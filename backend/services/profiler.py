"""Data profiling service for analyzing DataFrame quality and statistics."""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backend.core.logging import logger
from backend.models.schemas import ColumnProfile, ProfileResponse


class DataProfiler:
    """Service for profiling DataFrame data quality and statistics."""

    def __init__(self, df: pd.DataFrame, sheet_name: str):
        """Initialize with DataFrame and sheet name."""
        self.df = df
        self.sheet_name = sheet_name
        self.total_rows = len(df)
        self.total_cols = len(df.columns)

    def profile_column(self, col_name: str, max_samples: int = 10) -> ColumnProfile:
        """Profile a single column."""
        series = self.df[col_name]

        # Basic counts
        non_null_count = series.notna().sum()
        null_count = series.isna().sum()
        null_percentage = (
            (null_count / self.total_rows) * 100 if self.total_rows > 0 else 0
        )

        # Unique values
        unique_count = series.nunique()

        # Sample values (non-null, unique)
        sample_values = []
        try:
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                unique_values = non_null_series.unique()
                sample_count = min(max_samples, len(unique_values))
                sample_values = unique_values[:sample_count].tolist()

                # Convert numpy types to Python types for JSON serialization
                sample_values = [
                    item.item() if hasattr(item, "item") else item
                    for item in sample_values
                ]
        except Exception as e:
            logger.warning(f"Failed to get sample values for column '{col_name}': {e}")
            sample_values = []

        # Infer data type
        dtype_str = self._infer_dtype(series)

        return ColumnProfile(
            name=col_name,
            dtype=dtype_str,
            non_null_count=int(non_null_count),
            null_count=int(null_count),
            null_percentage=round(null_percentage, 2),
            unique_count=int(unique_count),
            sample_values=sample_values,
        )

    def _infer_dtype(self, series: pd.Series) -> str:
        """Infer the most appropriate data type for a series."""
        # Remove null values for type inference
        non_null = series.dropna()

        if len(non_null) == 0:
            return "empty"

        # Check if all values are numeric
        try:
            pd.to_numeric(non_null)
            # Check if integers
            if all(
                str(val).replace(".", "").replace("-", "").isdigit()
                for val in non_null
                if str(val).strip()
            ):
                return "integer"
            else:
                return "numeric"
        except (ValueError, TypeError):
            pass

        # Check if date-like
        date_patterns = [
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",
            r"\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
        ]

        sample_str = str(non_null.iloc[0]).lower()
        for pattern in date_patterns:
            import re

            if re.search(pattern, sample_str):
                return "date"

        # Check if boolean-like
        bool_values = {"true", "false", "yes", "no", "1", "0", "x", "d"}
        unique_lower = {str(val).strip().lower() for val in non_null.unique()}
        if unique_lower.issubset(bool_values):
            return "boolean"

        # Default to text
        return "text"

    def count_duplicate_rows(self) -> int:
        """Count duplicate rows in the DataFrame."""
        try:
            # Consider only non-null columns for duplicate detection
            non_null_cols = [
                col for col in self.df.columns if self.df[col].notna().any()
            ]

            if not non_null_cols:
                return 0

            duplicate_count = self.df[non_null_cols].duplicated().sum()
            return int(duplicate_count)

        except Exception as e:
            logger.warning(f"Failed to count duplicates: {e}")
            return 0

    def profile_sheet(self) -> ProfileResponse:
        """Profile the entire sheet."""
        logger.info(
            f"Profiling sheet '{self.sheet_name}'",
            rows=self.total_rows,
            cols=self.total_cols,
        )

        # Profile each column
        column_profiles = []
        for col_name in self.df.columns:
            try:
                profile = self.profile_column(str(col_name))
                column_profiles.append(profile)
            except Exception as e:
                logger.error(f"Failed to profile column '{col_name}': {e}")
                # Create minimal profile for failed column
                column_profiles.append(
                    ColumnProfile(
                        name=str(col_name),
                        dtype="error",
                        non_null_count=0,
                        null_count=self.total_rows,
                        null_percentage=100.0,
                        unique_count=0,
                        sample_values=[],
                    )
                )

        # Count duplicate rows
        duplicate_rows = self.count_duplicate_rows()

        logger.info(
            f"Profiling complete for '{self.sheet_name}'",
            duplicate_rows=duplicate_rows,
            columns_profiled=len(column_profiles),
        )

        return ProfileResponse(
            sheet_name=self.sheet_name,
            total_rows=self.total_rows,
            total_cols=self.total_cols,
            duplicate_rows=duplicate_rows,
            columns=column_profiles,
        )
