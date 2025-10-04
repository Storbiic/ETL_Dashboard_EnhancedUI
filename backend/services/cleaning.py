"""Data cleaning utilities and functions."""

import hashlib
import re
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd

from backend.core.logging import logger


def clean_id(s: str) -> str:
    """
    Clean ID column values by keeping only alphanumeric characters,
    collapsing spaces/underscores, and converting to uppercase.

    Args:
        s: Input string to clean

    Returns:
        Cleaned string
    """
    if pd.isna(s) or s is None:
        return ""

    # Convert to string and strip
    s = str(s).strip()

    # Keep only alphanumeric characters, spaces, hyphens, underscores
    s = re.sub(r"[^A-Za-z0-9\s\-_]", "", s)

    # Collapse multiple spaces/underscores into single space
    s = re.sub(r"[\s_]+", " ", s)

    # Convert to uppercase and strip again
    s = s.upper().strip()

    return s


def parse_date_column(series: pd.Series, col_name: str) -> pd.DataFrame:
    """
    Parse a date-like series -> datetime64[ns] and derive features.
    """
    out = pd.DataFrame()
    out[col_name] = series

    parsed = pd.to_datetime(series, errors="coerce")  # <— robust parse
    norm = parsed.dt.normalize()  # 00:00:00

    base = f"{col_name}_date"
    out[base] = norm  # datetime64[ns]
    out[f"{col_name}_year"] = norm.dt.year
    out[f"{col_name}_month"] = norm.dt.month
    out[f"{col_name}_day"] = norm.dt.day
    out[f"{col_name}_qtr"] = norm.dt.quarter
    out[f"{col_name}_week"] = norm.dt.isocalendar().week

    return out


def create_dim_dates(
    date_columns: List[pd.Series], column_names: List[str], fy_end_month: int = 12
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build a contiguous daily calendar (dim_dates) and a role bridge (date_role_bridge).
    """
    all_valid = []
    bridge_records = []

    for s, role in zip(date_columns, column_names):
        parsed = pd.to_datetime(s, errors="coerce").dropna().dt.normalize()
        if not parsed.empty:
            all_valid.append(parsed)
            # Bridge (unique dates per role)
            bridge_records.append(pd.DataFrame({"Date": parsed.unique(), "Role": role}))

    if not all_valid:
        return pd.DataFrame(), pd.DataFrame()

    min_d = min(x.min() for x in all_valid)
    max_d = max(x.max() for x in all_valid)

    # CONTIGUOUS daily calendar
    rng = pd.date_range(min_d, max_d, freq="D")
    dim_dates = pd.DataFrame({"Date": rng})
    dim_dates["Year"] = dim_dates["Date"].dt.year
    dim_dates["Month"] = dim_dates["Date"].dt.month
    dim_dates["MonthName"] = dim_dates["Date"].dt.strftime("%b")
    dim_dates["MonthYear"] = dim_dates["Date"].dt.strftime("%b %Y")
    dim_dates["MonthYearSort"] = dim_dates["Year"] * 12 + dim_dates["Month"]
    dim_dates["Quarter"] = "Q" + dim_dates["Date"].dt.quarter.astype(str)
    dim_dates["Week"] = dim_dates["Date"].dt.isocalendar().week.astype(int)

    date_role_bridge = pd.concat(bridge_records, ignore_index=True).drop_duplicates()

    return dim_dates, date_role_bridge


def standardize_text(series: pd.Series) -> pd.Series:
    """
    Standardize text values by stripping whitespace and converting to title case.

    Args:
        series: Pandas series with text values

    Returns:
        Cleaned series
    """
    try:
        # Ensure we're working with a proper Series
        if not isinstance(series, pd.Series):
            series = pd.Series(series)

        # Create a copy to avoid modifying the original
        result_series = series.copy()

        # Process each value individually to avoid Series ambiguity
        for idx in result_series.index:
            try:
                val = result_series.iloc[idx]

                # Handle null/None values
                if pd.isna(val) or val is None:
                    continue

                # Convert to string and strip
                text = str(val).strip()

                # Skip empty strings
                if not text:
                    continue

                # Unescape newlines and normalize whitespace
                text = re.sub(r"\\n", "\n", text)
                text = re.sub(r"\s+", " ", text)

                # Convert to title case for names
                if len(text) > 0:
                    text = text.title()

                result_series.iloc[idx] = text

            except Exception as e:
                # If there's an error processing this specific value, leave it as-is
                continue

        return result_series

    except Exception as e:
        # If there's a fundamental error, return the original series
        print(f"Error in standardize_text: {e}")
        return series


def create_row_hash(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.Series:
    """
    Create a hash for each row based on significant columns.

    Args:
        df: DataFrame to hash
        columns: Specific columns to include in hash (default: all)

    Returns:
        Series with row hashes
    """
    if columns is None:
        columns = df.columns.tolist()

    def hash_row(row):
        # Convert row values to string and concatenate
        row_str = "|".join(str(row[col]) for col in columns if col in row.index)

        # Create MD5 hash
        return hashlib.md5(row_str.encode()).hexdigest()

    return df.apply(hash_row, axis=1)


def flag_duplicate_rows(
    df: pd.DataFrame, subset: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Flag duplicate rows instead of removing them and return DataFrame with duplicate flag.

    Args:
        df: DataFrame to process
        subset: Columns to consider for duplicates (default: all)

    Returns:
        Tuple of (df_with_flag, duplicate_count)
    """
    original_count = len(df)

    # Add duplicate flag column
    df_with_flag = df.copy()
    df_with_flag["is_duplicate_entry"] = df.duplicated(subset=subset, keep="first")

    duplicate_count = int(df_with_flag["is_duplicate_entry"].sum())

    if duplicate_count > 0:
        logger.info(
            f"Flagged {duplicate_count} duplicate rows (preserved in dataset)",
            original_rows=original_count,
            flagged_duplicates=duplicate_count,
        )

    return df_with_flag, duplicate_count


def remove_duplicate_rows(
    df: pd.DataFrame, subset: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Remove duplicate rows and return cleaned DataFrame with count.

    Args:
        df: DataFrame to deduplicate
        subset: Columns to consider for duplicates (default: all)

    Returns:
        Tuple of (cleaned_df, duplicate_count)
    """
    original_count = len(df)

    # Remove duplicates, keeping first occurrence
    cleaned_df = df.drop_duplicates(subset=subset, keep="first")

    duplicate_count = original_count - len(cleaned_df)

    if duplicate_count > 0:
        logger.info(
            f"Removed {duplicate_count} duplicate rows",
            original_rows=original_count,
            final_rows=len(cleaned_df),
        )

    return cleaned_df, duplicate_count


def detect_date_columns(df: pd.DataFrame) -> List[str]:
    """
    Auto-detect date columns based on column names and content.

    Args:
        df: DataFrame to analyze

    Returns:
        List of column names that appear to contain dates
    """
    date_columns = []

    # Common date column name patterns
    date_patterns = [
        r"date",
        r"time",
        r"approved",
        r"promised",
        r"created",
        r"updated",
        r"modified",
        r"sop",
        r"milestone",
    ]

    # Patterns to exclude (part numbers, IDs, etc.)
    exclude_patterns = [
        r"supplier.*pn",
        r"original.*supplier.*pn",
        r"supplier pn",
        r"original supplier pn",
        r"part.*number",
        r"pn$",
        r"id$",
        r"code$",
        r"number$",
    ]

    for col in df.columns:
        col_lower = str(col).lower()

        # Skip columns that match exclusion patterns
        is_excluded = any(re.search(pattern, col_lower) for pattern in exclude_patterns)
        if is_excluded:
            continue

        # Check column name patterns
        is_date_name = any(re.search(pattern, col_lower) for pattern in date_patterns)

        if is_date_name:
            # Verify content looks like dates
            sample = df[col].dropna().head(10)
            if len(sample) > 0:
                try:
                    parsed = pd.to_datetime(sample, errors="coerce")
                    valid_ratio = parsed.notna().sum() / len(sample)

                    if valid_ratio > 0.5:  # At least 50% valid dates
                        date_columns.append(col)
                        logger.info(
                            f"Auto-detected date column: '{col}'",
                            valid_ratio=valid_ratio,
                        )
                except Exception:
                    pass

    return date_columns
