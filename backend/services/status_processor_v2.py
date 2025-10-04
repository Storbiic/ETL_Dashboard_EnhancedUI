"""
Status sheet processor following exact specification requirements.
"""

import re
from typing import Dict, Optional

import numpy as np
import pandas as pd

from backend.core.logging import ETLLogger


class StatusProcessorV2:
    """Process Status sheet according to exact specification requirements."""

    def __init__(self, df: pd.DataFrame, logger: ETLLogger):
        """Initialize with DataFrame and logger."""
        self.df = df.copy()
        self.logger = logger

        # Column mapping specification
        self.column_mapping = {
            "project": "plant_id",
            "oem": "oem",
            "managed by": "sqe",
            "1st ppap milestone": "milestone_date",
            "total part numbers": "total_parts",
            "psw available": "psw_available",
            "% psw": "psw_completion_pct",
            "drawing available": "drawing_available",
            "%.1 drawing": "drawing_completion_pct",
            "imds": "imds_total",
            "% imds": "imds_completion_pct",
            "m2 parts": "m2_parts",
            "m2 parts psw ok": "m2_parts_psw_ok",
            "project status": "completion_status",
            "bom file date": "bom_file_date",
        }

        # Required output columns
        self.required_columns = [
            "plant_id",
            "oem",
            "sqe",
            "milestone_date",
            "total_parts",
            "psw_available",
            "psw_completion_pct",
            "drawing_available",
            "drawing_completion_pct",
            "imds_total",
            "imds_completion_pct",
            "m2_parts",
            "m2_parts_psw_ok",
            "ppap_completion_pct",
            "overall_completion_pct",
            "completion_status",
            "bom_file_date",
        ]

    def process(self) -> Dict[str, pd.DataFrame]:
        """
        Process Status sheet according to specification requirements.

        Returns:
            Dictionary containing processed Status DataFrame
        """
        try:
            self.logger.info(
                "Starting Status sheet processing (V2)",
                input_rows=len(self.df),
                input_cols=len(self.df.columns),
            )

            # Step 1: Clean and prepare data
            self._clean_and_prepare_data()

            # Step 2: Normalize headers and map schema
            self._normalize_headers_and_map_schema()

            # Step 3: Apply type coercion and create derived fields
            self._apply_type_coercion_and_derived_fields()

            # Step 4: Validate and finalize output
            self._validate_and_finalize_output()

            self.logger.info(
                "Status sheet processing complete (V2)",
                output_rows=len(self.df),
                output_cols=len(self.df.columns),
            )

            return {
                "status_clean": self.df,
                "project_completion_by_plant": self.df.copy(),  # Same data, different name for compatibility
            }

        except Exception as e:
            self.logger.error(
                f"Error in status processing (V2): {str(e)}",
                step="status_processing_v2",
                error_type=type(e).__name__,
            )
            raise

    def _clean_and_prepare_data(self):
        """Clean and prepare data according to specification."""
        # Use row 0 as headers (already done by pandas read)

        # Drop entirely blank columns (Unnamed columns)
        unnamed_cols = [
            col for col in self.df.columns if str(col).startswith("Unnamed:")
        ]
        if unnamed_cols:
            self.df = self.df.drop(columns=unnamed_cols)
            self.logger.info(f"Dropped {len(unnamed_cols)} unnamed columns")

        # Drop columns that are entirely blank
        blank_cols = []
        for col in self.df.columns:
            if (
                self.df[col].isna().all()
                or (self.df[col].astype(str).str.strip() == "").all()
            ):
                blank_cols.append(col)

        if blank_cols:
            self.df = self.df.drop(columns=blank_cols)
            self.logger.info(f"Dropped {len(blank_cols)} entirely blank columns")

        # Find first fully empty row and truncate there
        fully_empty_rows = self.df.isna().all(axis=1)
        if fully_empty_rows.any():
            first_empty_idx = fully_empty_rows.idxmax()
            if first_empty_idx > 0:  # Keep at least some data
                self.df = self.df.iloc[:first_empty_idx]
                self.logger.info(
                    f"Truncated at first fully empty row: {first_empty_idx}"
                )

        # Drop rows that are fully NaN
        self.df = self.df.dropna(how="all")

        self.logger.info(
            "Data cleaning complete",
            final_rows=len(self.df),
            final_cols=len(self.df.columns),
        )

    def _normalize_headers_and_map_schema(self):
        """Normalize headers and map to canonical schema."""
        # Normalize headers: lower(), trim spaces, collapse multiple spaces
        normalized_headers = {}
        for col in self.df.columns:
            normalized = str(col).lower().strip()
            normalized = re.sub(r"\s+", " ", normalized)  # Collapse multiple spaces
            normalized_headers[col] = normalized

        # Map to target schema - avoid duplicate mappings
        column_renames = {}
        used_targets = set()

        for original_col, normalized_header in normalized_headers.items():
            # Find best match in column mapping
            for source_pattern, target_name in self.column_mapping.items():
                if target_name not in used_targets and self._header_matches(
                    normalized_header, source_pattern
                ):
                    column_renames[original_col] = target_name
                    used_targets.add(target_name)
                    break

        # Apply renames
        self.df = self.df.rename(columns=column_renames)

        # Handle any remaining duplicate columns by dropping them
        if self.df.columns.duplicated().any():
            self.df = self.df.loc[:, ~self.df.columns.duplicated()]
            self.logger.info("Removed duplicate columns after mapping")

        self.logger.info(
            "Header normalization complete",
            mapped_columns=len(column_renames),
            mappings=column_renames,
        )

    def _header_matches(self, normalized_header: str, pattern: str) -> bool:
        """Check if normalized header matches pattern (exact or close variant)."""
        # Handle percentage patterns specially
        if pattern == "% psw":
            return ("psw" in normalized_header and "%" in normalized_header) or (
                "psw" in normalized_header and "percent" in normalized_header
            )

        if pattern == "%.1 drawing":
            return ("drawing" in normalized_header and "%" in normalized_header) or (
                "drawing" in normalized_header and "percent" in normalized_header
            )

        if pattern == "% imds":
            return ("imds" in normalized_header and "%" in normalized_header) or (
                "imds" in normalized_header and "percent" in normalized_header
            )

        # Exact match first
        if normalized_header == pattern:
            return True

        # For other patterns, check if all words in pattern are in header
        pattern_words = pattern.split()
        return all(word in normalized_header for word in pattern_words)

    def _apply_type_coercion_and_derived_fields(self):
        """Apply type coercion and create derived fields."""
        # Date columns
        date_columns = ["milestone_date", "bom_file_date"]
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(
                    self.df[col], errors="coerce"
                ).dt.normalize()

        # Numeric count columns - handle duplicate column names
        count_columns = [
            "total_parts",
            "psw_available",
            "drawing_available",
            "imds_total",
            "m2_parts",
            "m2_parts_psw_ok",
        ]
        for col in count_columns:
            if col in self.df.columns:
                # Check if column exists and is not duplicated
                col_data = self.df[col]
                if hasattr(col_data, "iloc"):  # It's a Series
                    self.df[col] = pd.to_numeric(col_data, errors="coerce").astype(
                        "Int64"
                    )
                else:
                    # Handle potential duplicate columns by taking first
                    self.df[col] = pd.to_numeric(
                        (
                            self.df[col].iloc[:, 0]
                            if len(self.df[col].shape) > 1
                            else self.df[col]
                        ),
                        errors="coerce",
                    ).astype("Int64")

        # Percentage columns
        pct_columns = [
            "psw_completion_pct",
            "drawing_completion_pct",
            "imds_completion_pct",
        ]
        for col in pct_columns:
            if col in self.df.columns:
                col_data = self.df[col]
                if hasattr(col_data, "iloc"):  # It's a Series
                    self.df[col] = self._parse_percentage_column(col_data)
                else:
                    # Handle potential duplicate columns
                    self.df[col] = self._parse_percentage_column(
                        self.df[col].iloc[:, 0]
                        if len(self.df[col].shape) > 1
                        else self.df[col]
                    )

        # Create derived fields
        self._create_derived_fields()

        self.logger.info("Type coercion and derived fields complete")

    def _parse_percentage_column(self, series: pd.Series) -> pd.Series:
        """Parse percentage values according to specification."""

        def parse_pct(val):
            if pd.isna(val):
                return np.nan

            val_str = str(val).strip()
            if not val_str:
                return np.nan

            # Handle comma decimal separators
            val_str = val_str.replace(",", ".")

            # Remove % sign
            val_str = val_str.replace("%", "")

            try:
                num_val = float(val_str)

                # If value > 1 and ≤ 100, divide by 100
                if num_val > 1 and num_val <= 100:
                    num_val = num_val / 100.0

                # Clip to [0, 1]
                return max(0.0, min(1.0, num_val))

            except ValueError:
                return np.nan

        return series.apply(parse_pct)

    def _create_derived_fields(self):
        """Create derived fields according to specification."""
        # Calculate psw_completion_pct = psw_available / total_parts
        if "psw_available" in self.df.columns and "total_parts" in self.df.columns:
            self.df["psw_completion_pct"] = np.where(
                (self.df["total_parts"] > 0) & self.df["total_parts"].notna(),
                self.df["psw_available"] / self.df["total_parts"],
                np.nan,
            )

        # Calculate drawing_completion_pct = drawing_available / total_parts
        if "drawing_available" in self.df.columns and "total_parts" in self.df.columns:
            self.df["drawing_completion_pct"] = np.where(
                (self.df["total_parts"] > 0) & self.df["total_parts"].notna(),
                self.df["drawing_available"] / self.df["total_parts"],
                np.nan,
            )

        # Calculate imds_completion_pct = imds_total / total_parts
        if "imds_total" in self.df.columns and "total_parts" in self.df.columns:
            self.df["imds_completion_pct"] = np.where(
                (self.df["total_parts"] > 0) & self.df["total_parts"].notna(),
                self.df["imds_total"] / self.df["total_parts"],
                np.nan,
            )

        # ppap_completion_pct = m2_parts_psw_ok / m2_parts
        if "m2_parts_psw_ok" in self.df.columns and "m2_parts" in self.df.columns:
            self.df["ppap_completion_pct"] = np.where(
                (self.df["m2_parts"] > 0) & self.df["m2_parts"].notna(),
                self.df["m2_parts_psw_ok"] / self.df["m2_parts"],
                np.nan,
            )
        else:
            self.df["ppap_completion_pct"] = np.nan

        # overall_completion_pct = mean of available completion percentages
        pct_cols = [
            "psw_completion_pct",
            "drawing_completion_pct",
            "imds_completion_pct",
            "ppap_completion_pct",
        ]

        available_pct_cols = [col for col in pct_cols if col in self.df.columns]

        if available_pct_cols:
            self.df["overall_completion_pct"] = self.df[available_pct_cols].mean(
                axis=1, skipna=True
            )
        else:
            self.df["overall_completion_pct"] = np.nan

    def _validate_and_finalize_output(self):
        """Validate and finalize output according to specification."""
        # Ensure all required columns exist
        for col in self.required_columns:
            if col not in self.df.columns:
                # Add missing columns with appropriate default values
                if col.endswith("_pct"):
                    self.df[col] = np.nan
                elif col.endswith("_date"):
                    self.df[col] = pd.NaT
                elif col in [
                    "total_parts",
                    "psw_available",
                    "drawing_available",
                    "imds_total",
                    "m2_parts",
                    "m2_parts_psw_ok",
                ]:
                    self.df[col] = pd.NA
                else:
                    self.df[col] = None

        # Reorder columns to match specification
        self.df = self.df[self.required_columns]

        # Ensure percentage columns are explicitly cast to float
        pct_cols = [
            "psw_completion_pct",
            "drawing_completion_pct",
            "imds_completion_pct",
            "ppap_completion_pct",
            "overall_completion_pct",
        ]
        for col in pct_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(float)

        self.logger.info(
            "Output validation complete",
            final_columns=list(self.df.columns),
            final_shape=self.df.shape,
        )
