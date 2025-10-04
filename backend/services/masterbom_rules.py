"""Business rules and transformations for MasterBOM sheet processing."""

from typing import Dict, List, Tuple

import pandas as pd

from backend.core.logging import ETLLogger
from backend.services.cleaning import (
    clean_id,
    detect_date_columns,
    flag_duplicate_rows,
    parse_date_column,
    standardize_text,
)


class MasterBOMProcessor:
    """Processor for MasterBOM sheet with business rules."""

    def __init__(self, df: pd.DataFrame, logger: ETLLogger):
        """Initialize with DataFrame and logger."""
        self.df = df.copy()
        self.logger = logger
        self.project_columns = []
        self.id_column = None

    def process(
        self, id_col: str = "YAZAKI PN", date_cols: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Process MasterBOM sheet according to business rules.

        Args:
            id_col: Name of the ID column
            date_cols: List of date column names to process

        Returns:
            Dictionary with processed DataFrames
        """
        self.logger.info(
            "Starting MasterBOM processing",
            input_rows=len(self.df),
            input_cols=len(self.df.columns),
        )

        # Step 1: Detect and fix multi-row headers
        self._detect_and_fix_headers()

        # Step 2: Clean column names
        self._clean_column_names()

        # Step 3: Identify ID column and project columns
        self._identify_columns(id_col)

        # Step 3: Clean ID column
        self._clean_id_column()

        # Step 4: Process date columns
        preferred_date_cols = [
            "Approved Date",  # approval of part into MBOM
            "PSW Date",  # PSW approval date (if present)
            "FAR Date",  # FAR closed/ok date (if present)
        ]
        auto_detected = detect_date_columns(self.df)
        date_cols = [
            c for c in preferred_date_cols if c in self.df.columns
        ] or auto_detected
        self._process_date_columns(date_cols)

        # Step 5: Standardize text columns
        self._standardize_text_columns()

        # Step 6: Create normalized plant-item-status table
        plant_item_status = self._create_plant_item_status()

        # Step 7: Create fact parts table
        fact_parts = self._create_fact_parts()

        # Step 8: Clean main DataFrame
        masterbom_clean = self._finalize_masterbom()

        self.logger.info(
            "MasterBOM processing complete",
            output_tables=3,
            masterbom_rows=len(masterbom_clean),
            plant_status_rows=len(plant_item_status),
            fact_parts_rows=len(fact_parts),
        )

        return {
            "masterbom_clean": masterbom_clean,
            "plant_item_status": plant_item_status,
            "fact_parts": fact_parts,
        }

    def _detect_and_fix_headers(self):
        """Detect and fix multi-row headers in Excel data."""
        self.logger.info("Detecting multi-row headers")

        # Look for the actual data start by finding the first row with the ID column pattern
        id_patterns = ["YAZAKI PN", "yazaki pn", "part number", "part_number", "id"]
        data_start_row = None

        # Check first 10 rows for potential header rows
        for i in range(min(10, len(self.df))):
            row_values = [
                str(val).strip().lower()
                for val in self.df.iloc[i].values
                if pd.notna(val)
            ]

            # Look for ID column patterns in this row
            for pattern in id_patterns:
                if any(pattern in val for val in row_values):
                    # Check if this row looks like headers (contains text, not numbers)
                    non_numeric_count = sum(
                        1
                        for val in row_values
                        if not val.replace(".", "").replace("-", "").isdigit()
                    )
                    if (
                        non_numeric_count > len(row_values) * 0.7
                    ):  # 70% non-numeric suggests headers
                        data_start_row = i
                        break

            if data_start_row is not None:
                break

        if data_start_row is not None and data_start_row > 0:
            self.logger.info(
                f"Found multi-row headers, data starts at row {data_start_row}"
            )

            # Use the detected row as new headers
            new_headers = []
            header_row = self.df.iloc[data_start_row]

            for i, val in enumerate(header_row):
                if pd.notna(val) and str(val).strip():
                    new_headers.append(str(val).strip())
                else:
                    # Use original column name if header is empty
                    new_headers.append(f"Column_{i}")

            # Remove header rows and reset
            self.df = self.df.iloc[data_start_row + 1 :].reset_index(drop=True)
            self.df.columns = new_headers

            self.logger.info(
                f"Fixed headers, removed {data_start_row + 1} header rows",
                new_shape=self.df.shape,
                sample_headers=new_headers[:5],
            )
        else:
            self.logger.info("No multi-row headers detected, using original structure")

    def _clean_column_names(self):
        """Clean and standardize column names."""
        original_cols = self.df.columns.tolist()

        # Strip whitespace and standardize
        self.df.columns = [str(col).strip() for col in self.df.columns]

        self.logger.info("Cleaned column names", original_count=len(original_cols))

    def _identify_columns(self, id_col: str):
        """Identify ID column and project columns."""
        columns = self.df.columns.tolist()

        # Find ID column
        self.id_column = None
        for col in columns:
            if str(col).strip().upper() == id_col.upper():
                self.id_column = col
                break

        if self.id_column is None:
            self.logger.warning(f"ID column '{id_col}' not found, using first column")
            self.id_column = columns[0]

        # Find project columns (between ID and Item Description)
        id_idx = columns.index(self.id_column)
        desc_idx = None

        for i, col in enumerate(columns[id_idx + 1 :], start=id_idx + 1):
            col_lower = str(col).lower()
            if "item" in col_lower and "desc" in col_lower:
                desc_idx = i
                break

        if desc_idx is None:
            # Assume all remaining columns are projects if no description found
            desc_idx = len(columns)

        self.project_columns = columns[id_idx + 1 : desc_idx]

        self.logger.info(
            "Identified columns",
            id_column=self.id_column,
            project_columns_count=len(self.project_columns),
            project_columns=self.project_columns[:5],
        )  # Log first 5

    def _clean_id_column(self):
        """Clean the ID column values."""
        if self.id_column not in self.df.columns:
            return

        # Create standardized ID column
        self.df["part_id_raw"] = self.df[self.id_column].astype(str)
        self.df["part_id_std"] = self.df[self.id_column].apply(clean_id)

        # Count cleaning results
        non_empty = self.df["part_id_std"].str.len() > 0

        self.logger.info(
            "Cleaned ID column",
            total_parts=len(self.df),
            valid_ids=int(non_empty.sum()),
            empty_ids=int((~non_empty).sum()),
        )

    def _process_date_columns(self, date_cols: List[str]):
        """Process date columns and create derived features."""
        processed_cols = []

        for col in date_cols:
            if col in self.df.columns:
                try:
                    date_df = parse_date_column(self.df[col], col)

                    # Add new columns to main DataFrame
                    for new_col in date_df.columns:
                        if new_col != col:  # Don't overwrite original
                            self.df[new_col] = date_df[new_col]

                    processed_cols.append(col)

                except Exception as e:
                    self.logger.error(f"Failed to process date column '{col}': {e}")

        self.logger.info(
            "Processed date columns",
            requested=len(date_cols),
            processed=len(processed_cols),
            columns=processed_cols,
        )

    def _standardize_text_columns(self):
        """Standardize text columns like supplier names."""
        text_columns = [
            "Supplier Name",
            "Original Supplier Name",
            "Item Description",
            "Part Specification",
        ]

        standardized = 0
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = standardize_text(self.df[col])
                standardized += 1

        self.logger.info("Standardized text columns", count=standardized)

    def _create_plant_item_status(self) -> pd.DataFrame:
        """
        Create normalized plant-item-status long table with enhanced duplicate handling.

        Implements:
        - Proper status handling: 'X' (Active), 'D' (Discontinued), Blank/NULL (Not in Project)
        - Morocco supplier prioritization for duplicates
        - Enhanced duplicate resolution logic
        """
        if not self.project_columns:
            self.logger.warning("No project columns found for normalization")
            return pd.DataFrame()

        self.logger.info(
            "Starting enhanced plant-item-status processing",
            project_columns=len(self.project_columns),
            total_parts=len(self.df),
        )

        # Step 1: Handle duplicates in source data BEFORE melting
        deduplicated_df = self._handle_source_duplicates()

        # Step 2: Prepare base data with additional columns for duplicate resolution
        base_cols = ["part_id_std", "part_id_raw"]
        if self.id_column:
            base_cols.append(self.id_column)

        # Add supplier and FAR status columns if available for duplicate resolution
        additional_cols = []
        if "Supplier Name" in deduplicated_df.columns:
            additional_cols.append("Supplier Name")
        if "FAR Status" in deduplicated_df.columns:
            additional_cols.append("FAR Status")

        # Step 3: Melt project columns into long format
        id_vars = [
            col for col in base_cols + additional_cols if col in deduplicated_df.columns
        ]

        melted = pd.melt(
            deduplicated_df,
            id_vars=id_vars,
            value_vars=self.project_columns,
            var_name="project_plant",
            value_name="raw_status",
        )

        # Step 4: Apply enhanced status classification rules
        melted["status_class"] = melted.apply(self._classify_status_enhanced, axis=1)
        melted["is_duplicate"] = False  # Will be updated in duplicate detection
        melted["is_new"] = melted["status_class"] == "not_in_project"
        melted["notes"] = None

        # Step 5: Detect and resolve remaining duplicates in melted data
        melted = self._resolve_melted_duplicates(melted)

        # Step 6: Calculate plant counts per part
        plant_counts = self._calculate_plant_counts(melted)
        melted = melted.merge(plant_counts, on="part_id_std", how="left")

        # Step 7: Clean up columns (remove helper columns if they exist)
        final_columns = [
            "part_id_std",
            "part_id_raw",
            self.id_column,
            "project_plant",
            "raw_status",
            "status_class",
            "is_duplicate",
            "is_new",
            "notes",
            "n_active",
            "n_inactive",
            "n_new",
            "n_duplicate",
        ]
        final_columns = [
            col for col in final_columns if col in melted.columns and col is not None
        ]
        melted = melted[final_columns]

        self.logger.info(
            "Enhanced plant-item-status processing complete",
            total_records=len(melted),
            unique_parts=melted["part_id_std"].nunique(),
            unique_plants=melted["project_plant"].nunique(),
            active_records=len(melted[melted["status_class"] == "active"]),
            discontinued_records=len(melted[melted["status_class"] == "discontinued"]),
            not_in_project_records=len(
                melted[melted["status_class"] == "not_in_project"]
            ),
        )

        return melted

    def _classify_status_enhanced(self, row) -> str:
        """
        Enhanced status classification based on raw_status value.

        Status Logic:
        - 'X': Active - Part is currently active and still included in the project plant
        - 'D': Discontinued - Part has been deleted/discontinued from the project plant
        - Blank/NULL: Not in Project - Part is not present in the current project
        """
        raw_status = str(row["raw_status"]).strip().upper()

        if raw_status == "X":
            return "active"
        elif raw_status == "D":
            return "discontinued"
        elif raw_status in ["", "NAN", "NONE", "NULL"]:
            return "not_in_project"
        elif raw_status == "0":
            # Legacy duplicate marker - treat as not in project for now
            return "not_in_project"
        else:
            # Any other value - treat as not in project
            return "not_in_project"

    def _classify_status(self, row) -> str:
        """Legacy status classification - kept for backward compatibility."""
        return self._classify_status_enhanced(row)

    def _handle_source_duplicates(self) -> pd.DataFrame:
        """
        Handle duplicates in source data with Morocco supplier prioritization.

        Duplicate Handling Logic:
        1. Identify duplicated Yazaki PNs with different FAR Status values
        2. Check Supplier Name field for Morocco-related suppliers
        3. Prioritize Morocco suppliers when duplicates exist
        4. Keep only the Morocco supplier record when choosing between duplicates
        """
        df_work = self.df.copy()

        if "part_id_std" not in df_work.columns:
            self.logger.warning("No part_id_std column found for duplicate handling")
            return df_work

        # Find duplicated part IDs
        duplicated_parts = df_work[
            df_work.duplicated(subset=["part_id_std"], keep=False)
        ]

        if duplicated_parts.empty:
            self.logger.info("No duplicates found in source data")
            return df_work

        self.logger.info(
            "Processing duplicates in source data",
            total_duplicates=len(duplicated_parts),
            unique_duplicated_parts=duplicated_parts["part_id_std"].nunique(),
        )

        # Process each duplicated part
        resolved_records = []
        non_duplicated = df_work[
            ~df_work.duplicated(subset=["part_id_std"], keep=False)
        ]

        for part_id in duplicated_parts["part_id_std"].unique():
            part_records = df_work[df_work["part_id_std"] == part_id].copy()

            # Apply Morocco supplier prioritization
            resolved_record = self._resolve_duplicate_with_morocco_priority(
                part_id, part_records
            )
            resolved_records.append(resolved_record)

        # Combine resolved records with non-duplicated records
        if resolved_records:
            resolved_df = pd.concat(resolved_records, ignore_index=True)
            final_df = pd.concat([non_duplicated, resolved_df], ignore_index=True)
        else:
            final_df = non_duplicated

        duplicates_removed = len(df_work) - len(final_df)
        self.logger.info(
            "Source duplicate resolution complete",
            original_records=len(df_work),
            final_records=len(final_df),
            duplicates_removed=duplicates_removed,
        )

        return final_df

    def _resolve_duplicate_with_morocco_priority(
        self, part_id: str, part_records: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Resolve duplicates for a specific part ID using Morocco supplier priority.

        Args:
            part_id: The part ID being processed
            part_records: All records for this part ID

        Returns:
            Single record (highest priority) for this part ID
        """
        if len(part_records) == 1:
            return part_records

        # Check if we have Supplier Name column
        if "Supplier Name" not in part_records.columns:
            self.logger.warning(
                f"No Supplier Name column for duplicate resolution of {part_id}"
            )
            return part_records.iloc[[0]]  # Return first record

        # Define Morocco supplier patterns (case-insensitive)
        morocco_patterns = ["MA", "MAROC", "MOROCCO", "MAROC"]

        # Find Morocco suppliers
        morocco_records = pd.DataFrame()
        for pattern in morocco_patterns:
            mask = part_records["Supplier Name"].str.contains(
                pattern, case=False, na=False
            )
            if mask.any():
                morocco_records = pd.concat(
                    [morocco_records, part_records[mask]], ignore_index=True
                )

        # Remove duplicates in morocco_records if any
        if not morocco_records.empty:
            morocco_records = morocco_records.drop_duplicates()

        # Decision logic
        if len(morocco_records) == 1:
            # Single Morocco supplier found - use it
            selected_record = morocco_records
            self.logger.info(
                f"Morocco supplier prioritized for part {part_id}",
                supplier=morocco_records.iloc[0].get("Supplier Name", "Unknown"),
                total_duplicates=len(part_records),
            )
        elif len(morocco_records) > 1:
            # Multiple Morocco suppliers - use first one
            selected_record = morocco_records.iloc[[0]]
            self.logger.info(
                f"Multiple Morocco suppliers found for part {part_id}, using first",
                supplier=selected_record.iloc[0].get("Supplier Name", "Unknown"),
                total_morocco_records=len(morocco_records),
            )
        else:
            # No Morocco suppliers found - use first record
            selected_record = part_records.iloc[[0]]
            self.logger.info(
                f"No Morocco supplier found for part {part_id}, using first record",
                supplier=selected_record.iloc[0].get("Supplier Name", "Unknown"),
                total_duplicates=len(part_records),
            )

        return selected_record

    def _check_duplicate(self, row) -> bool:
        """Legacy duplicate check - kept for backward compatibility."""
        return False  # Duplicates are now handled in preprocessing

    def _resolve_melted_duplicates(self, melted_df: pd.DataFrame) -> pd.DataFrame:
        """
        Resolve any remaining duplicates in the melted data.

        This handles edge cases where duplicates might still exist after source processing.
        """
        # Check for duplicates in melted data (same part + same project_plant)
        duplicate_mask = melted_df.duplicated(
            subset=["part_id_std", "project_plant"], keep=False
        )

        if not duplicate_mask.any():
            self.logger.info("No duplicates found in melted data")
            return melted_df

        duplicated_melted = melted_df[duplicate_mask]
        self.logger.info(
            "Processing duplicates in melted data",
            duplicate_records=len(duplicated_melted),
        )

        # For melted duplicates, keep the first occurrence
        # (since source duplicates should already be resolved)
        cleaned_melted = melted_df.drop_duplicates(
            subset=["part_id_std", "project_plant"], keep="first"
        )

        duplicates_removed = len(melted_df) - len(cleaned_melted)
        if duplicates_removed > 0:
            self.logger.info(
                "Removed duplicates from melted data",
                duplicates_removed=duplicates_removed,
            )

        return cleaned_melted

    def _calculate_plant_counts(self, melted_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate counts by status for each part with updated status names."""
        counts = (
            melted_df.groupby("part_id_std")["status_class"]
            .value_counts()
            .unstack(fill_value=0)
        )

        # Ensure all status columns exist with new naming
        status_mapping = {
            "active": "n_active",
            "discontinued": "n_inactive",  # Map discontinued to n_inactive for compatibility
            "not_in_project": "n_new",  # Map not_in_project to n_new for compatibility
            "duplicate": "n_duplicate",
        }

        # Create columns for all possible statuses
        for old_status, new_col in status_mapping.items():
            if old_status not in counts.columns:
                counts[old_status] = 0

        # Rename columns according to mapping
        counts = counts.rename(columns=status_mapping)

        # Ensure all expected columns exist
        expected_cols = ["n_active", "n_inactive", "n_new", "n_duplicate"]
        for col in expected_cols:
            if col not in counts.columns:
                counts[col] = 0

        return counts.reset_index()

    def _create_fact_parts(self) -> pd.DataFrame:
        if "part_id_std" not in self.df.columns:
            return pd.DataFrame()

        # Prepare date columns for aggregation
        self._prepare_date_columns_for_aggregation()
        # One row per part with “first non-null” aggregation
        agg_map = {
            "part_id_raw": "first",
            "Item Description": "first",
            "Supplier Name": "first",
            "Supplier PN": "first",
            "PSW": "first",
            "PSW Type": "first",
            "PSW Sub Type": "first",
            "YPN Status": "first",
            "Handling Manual": "first",
            "IMDS STATUS (Yes, No, N/A)": "first",
            "FAR Status": "first",
            "PPAP Details": "first",
            # Enhanced date aggregation logic
            "Approved Date_date": "max",  # Latest approved date
            "PSW Date_date": "first",  # First PSW date
            "FAR Date_date": "max",  # Latest FAR closure date
            "Promised Date_date": "min",  # Earliest promised date
            "FAR Promised date_date": "min",  # Earliest FAR promised date
        }
        present = {k: v for k, v in agg_map.items() if k in self.df.columns}
        fact_parts = (
            self.df.groupby("part_id_std", dropna=False).agg(present).reset_index()
        )
        # Rename to clean names and ensure datetime64[ns]
        rename_map = {
            "part_id_std": "item_id",  # Use item_id as requested
        }

        # Map date columns to requested names
        if "Approved Date_date" in fact_parts.columns:
            rename_map["Approved Date_date"] = "latest_approved_date"
        if "PSW Date_date" in fact_parts.columns:
            rename_map["PSW Date_date"] = "psw_date"
        if "FAR Date_date" in fact_parts.columns:
            rename_map["FAR Date_date"] = "far_date"
        if "Promised Date_date" in fact_parts.columns:
            rename_map["Promised Date_date"] = "earliest_promised_date"
        if "FAR Promised date_date" in fact_parts.columns:
            rename_map["FAR Promised date_date"] = "earliest_far_promised_date"

        fact_parts = fact_parts.rename(columns=rename_map)

        # Ensure all date columns are datetime64[ns] and normalized
        date_columns = [
            "latest_approved_date",
            "psw_date",
            "far_date",
            "earliest_promised_date",
            "earliest_far_promised_date",
        ]

        for col in date_columns:
            if col in fact_parts.columns:
                fact_parts[col] = pd.to_datetime(
                    fact_parts[col], errors="coerce"
                ).dt.normalize()

        # Derived flags
        if "PSW" in fact_parts.columns:
            fact_parts["psw_ok"] = fact_parts["PSW"].notna() & (fact_parts["PSW"] != "")
        if "Handling Manual" in fact_parts.columns:
            fact_parts["has_handling_manual"] = fact_parts["Handling Manual"].notna()
        if "FAR Status" in fact_parts.columns:
            fact_parts["far_ok"] = fact_parts["FAR Status"].str.contains(
                "OK", case=False, na=False
            )
        if "IMDS STATUS (Yes, No, N/A)" in fact_parts.columns:
            fact_parts["imds_ok"] = fact_parts[
                "IMDS STATUS (Yes, No, N/A)"
            ].str.contains("Yes", case=False, na=False)

        self.logger.info(
            "Created fact_parts table with enhanced date fields",
            total_parts=len(fact_parts),
            date_columns=[col for col in date_columns if col in fact_parts.columns],
        )

        return fact_parts

    def _prepare_date_columns_for_aggregation(self):
        """Prepare additional date columns for fact_parts aggregation."""
        # Ensure we have processed date columns for Promised Date and FAR Promised date
        additional_date_cols = ["Promised Date", "FAR Promised date"]

        for col in additional_date_cols:
            if col in self.df.columns and f"{col}_date" not in self.df.columns:
                try:
                    # Parse the date column if not already processed
                    from backend.services.cleaning import parse_date_column

                    date_df = parse_date_column(self.df[col], col)

                    # Add new date columns to main DataFrame
                    for new_col in date_df.columns:
                        if new_col != col:  # Don't overwrite original
                            self.df[new_col] = date_df[new_col]

                    self.logger.info(f"Processed additional date column: {col}")

                except Exception as e:
                    self.logger.warning(
                        f"Failed to process additional date column '{col}': {e}"
                    )

    def _finalize_masterbom(self) -> pd.DataFrame:
        """Finalize the cleaned MasterBOM DataFrame with duplicate flagging."""
        self.logger.info("Step 8: Finalizing MasterBOM with duplicate detection")

        # Flag duplicate rows instead of removing them
        cleaned_df, duplicate_count = flag_duplicate_rows(self.df)

        if duplicate_count > 0:
            self.logger.info(
                "Duplicate handling complete: Flagged duplicate rows (preserved in dataset)",
                count=duplicate_count,
                total_rows=len(cleaned_df),
                unique_rows=len(cleaned_df) - duplicate_count,
            )
        else:
            self.logger.info("No duplicate rows found", total_rows=len(cleaned_df))

        # Verify the is_duplicate_entry column exists
        if "is_duplicate_entry" in cleaned_df.columns:
            duplicate_flagged = cleaned_df["is_duplicate_entry"].sum()
            self.logger.info(
                f"Verification: {duplicate_flagged} rows flagged as duplicates in final dataset"
            )
        else:
            self.logger.warning("is_duplicate_entry column not found in final dataset")

        return cleaned_df
