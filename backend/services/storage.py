"""Data storage service for saving processed data in multiple formats."""

import sqlite3
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sqlalchemy import create_engine

from backend.core.config import settings
from backend.core.logging import ETLLogger
from backend.models.schemas import ArtifactInfo


class DataStorage:
    """Service for storing processed data in multiple formats."""

    def __init__(self, logger: ETLLogger):
        """Initialize with logger."""
        self.logger = logger
        self.processed_folder = settings.processed_folder_path
        self.processed_folder.mkdir(parents=True, exist_ok=True)

    def save_all_formats(
        self, dataframes: Dict[str, pd.DataFrame]
    ) -> List[ArtifactInfo]:
        """
        Save all DataFrames in CSV, Parquet, and SQLite formats.

        Args:
            dataframes: Dictionary of {table_name: DataFrame}

        Returns:
            List of artifact information
        """
        artifacts = []

        self.logger.info(
            "Starting data storage",
            tables=list(dataframes.keys()),
            total_tables=len(dataframes),
        )

        # Save individual formats
        for table_name, df in dataframes.items():
            if df.empty:
                self.logger.warning(f"Skipping empty table: {table_name}")
                continue

            # Save CSV
            csv_artifacts = self._save_csv(table_name, df)
            artifacts.extend(csv_artifacts)

            # Save Parquet
            parquet_artifacts = self._save_parquet(table_name, df)
            artifacts.extend(parquet_artifacts)

        # Save SQLite database with all tables
        sqlite_artifacts = self._save_sqlite(dataframes)
        artifacts.extend(sqlite_artifacts)

        self.logger.info("Data storage complete", total_artifacts=len(artifacts))

        return artifacts

    def _save_csv(self, table_name: str, df: pd.DataFrame) -> List[ArtifactInfo]:
        """Save DataFrame as CSV with optimized settings."""
        try:
            csv_path = self.processed_folder / f"{table_name}.csv"

            # Convert datetime columns to strings for CSV compatibility (optimized)
            df_csv = df.copy()
            for col in df_csv.columns:
                if pd.api.types.is_datetime64_any_dtype(df_csv[col]):
                    # Use vectorized string conversion for better performance
                    df_csv[col] = df_csv[col].dt.strftime("%Y-%m-%d")
                elif "datetime" in str(df_csv[col].dtype).lower():
                    df_csv[col] = df_csv[col].astype(str)

            # Save with optimized settings for large files
            df_csv.to_csv(
                csv_path,
                index=False,
                encoding="utf-8",
                chunksize=(
                    10000 if len(df_csv) > 50000 else None
                ),  # Chunk large datasets
                compression=None,  # No compression for CSV (faster)
            )

            file_size = csv_path.stat().st_size

            self.logger.info(
                f"Saved CSV: {table_name}", path=str(csv_path), size_bytes=file_size
            )

            return [
                ArtifactInfo(
                    name=f"{table_name}.csv",
                    path=str(csv_path),
                    format="CSV",
                    size_bytes=file_size,
                    row_count=len(df),
                )
            ]

        except Exception as e:
            self.logger.error(f"Failed to save CSV for {table_name}: {e}")
            return []

    def _save_parquet(self, table_name: str, df: pd.DataFrame) -> List[ArtifactInfo]:
        """Save DataFrame as Parquet with optimized data type handling."""
        try:
            parquet_path = self.processed_folder / f"{table_name}.parquet"
            df_parquet = df.copy()

            # Common date formats to try (most common first for performance)
            date_formats = [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
            ]

            # Known date column patterns (case-insensitive)
            date_column_patterns = [
                "date",
                "created",
                "updated",
                "modified",
                "due",
                "start",
                "end",
                "delivery",
                "required",
                "planned",
                "actual",
                "forecast",
            ]

            # Performance optimization: Log processing start for large datasets
            if len(df_parquet) > 50000:
                self.logger.info(
                    f"Processing large dataset: {table_name}",
                    rows=len(df_parquet),
                    columns=len(df_parquet.columns),
                )

            for col in df_parquet.columns:
                # Special handling for percentage columns
                if col.endswith("_pct"):
                    df_parquet[col] = pd.to_numeric(df_parquet[col], errors="coerce")
                    continue

                # Skip if already datetime or numeric
                if pd.api.types.is_datetime64_any_dtype(
                    df_parquet[col]
                ) or pd.api.types.is_numeric_dtype(df_parquet[col]):
                    continue

                # Only process object columns that might be dates
                if pd.api.types.is_object_dtype(df_parquet[col]):
                    col_lower = col.lower()

                    # Check if column name suggests it's a date
                    is_likely_date = any(
                        pattern in col_lower for pattern in date_column_patterns
                    )

                    if is_likely_date:
                        # Try optimized datetime parsing with specific formats
                        parsed_date = None
                        sample_values = (
                            df_parquet[col].dropna().head(100)
                        )  # Sample for format detection

                        if len(sample_values) > 0:
                            for date_format in date_formats:
                                try:
                                    # Test format on sample
                                    test_parse = pd.to_datetime(
                                        sample_values.iloc[0], format=date_format
                                    )
                                    # If successful, apply to whole column
                                    parsed_date = pd.to_datetime(
                                        df_parquet[col],
                                        format=date_format,
                                        errors="coerce",
                                    )
                                    break
                                except (ValueError, TypeError):
                                    continue

                            # If no specific format worked, try general parsing but with cache
                            if parsed_date is None or parsed_date.isna().all():
                                parsed_date = pd.to_datetime(
                                    df_parquet[col], errors="coerce", cache=True
                                )

                            # Only replace if we got valid dates (>10% success rate)
                            if parsed_date.notna().sum() > len(df_parquet) * 0.1:
                                df_parquet[col] = parsed_date.dt.normalize()
                            else:
                                # Not a date column, convert to string efficiently
                                df_parquet[col] = (
                                    df_parquet[col]
                                    .astype("string")
                                    .replace("<NA>", None)
                                )
                    else:
                        # Non-date object column - convert to string efficiently
                        df_parquet[col] = (
                            df_parquet[col].astype("string").replace("<NA>", None)
                        )

            # Save with optimized settings
            df_parquet.to_parquet(
                parquet_path,
                index=False,
                engine="pyarrow",
                compression="snappy",  # Fast compression
                use_deprecated_int96_timestamps=False,
            )

            file_size = parquet_path.stat().st_size

            self.logger.info(
                f"Saved Parquet: {table_name}",
                path=str(parquet_path),
                size_bytes=file_size,
            )

            return [
                ArtifactInfo(
                    name=f"{table_name}.parquet",
                    path=str(parquet_path),
                    format="Parquet",
                    size_bytes=file_size,
                    row_count=len(df),
                )
            ]

        except Exception as e:
            self.logger.error(f"Failed to save Parquet for {table_name}: {e}")
            return []

    def _save_sqlite(self, dataframes: Dict[str, pd.DataFrame]) -> List[ArtifactInfo]:
        """Save all DataFrames to SQLite database."""
        try:
            sqlite_path = self.processed_folder / "etl.sqlite"

            # Remove existing database
            if sqlite_path.exists():
                sqlite_path.unlink()

            # Create SQLAlchemy engine
            engine = create_engine(f"sqlite:///{sqlite_path}")

            # Save each DataFrame as a table
            tables_saved = 0
            for table_name, df in dataframes.items():
                if df.empty:
                    continue

                # Prepare DataFrame for SQLite
                df_sqlite = df.copy()

                # Handle data types for SQLite
                for col in df_sqlite.columns:
                    if df_sqlite[col].dtype == "datetime64[ns]":
                        df_sqlite[col] = df_sqlite[col].dt.strftime("%Y-%m-%d")
                    elif "date" in str(df_sqlite[col].dtype):
                        df_sqlite[col] = df_sqlite[col].astype(str)
                    elif df_sqlite[col].dtype == "object":
                        df_sqlite[col] = df_sqlite[col].astype(str)
                        df_sqlite[col] = df_sqlite[col].replace("nan", None)

                # Save to SQLite
                df_sqlite.to_sql(table_name, engine, if_exists="replace", index=False)
                tables_saved += 1

                self.logger.info(
                    f"Saved table to SQLite: {table_name}", rows=len(df_sqlite)
                )

            engine.dispose()

            file_size = sqlite_path.stat().st_size

            self.logger.info(
                "Saved SQLite database",
                path=str(sqlite_path),
                tables=tables_saved,
                size_bytes=file_size,
            )

            return [
                ArtifactInfo(
                    name="etl.sqlite",
                    path=str(sqlite_path),
                    format="SQLite",
                    size_bytes=file_size,
                    row_count=sum(len(df) for df in dataframes.values()),
                )
            ]

        except Exception as e:
            self.logger.error(f"Failed to save SQLite database: {e}")
            return []

    def create_data_dictionary(self, dataframes: Dict[str, pd.DataFrame]) -> str:
        """Create a data dictionary file describing all tables and columns."""
        try:
            dict_path = self.processed_folder / "data_dictionary.md"

            with open(dict_path, "w", encoding="utf-8") as f:
                f.write("# Data Dictionary\n\n")
                f.write("Generated data dictionary for ETL processed tables.\n\n")

                for table_name, df in dataframes.items():
                    if df.empty:
                        continue

                    f.write(f"## {table_name}\n\n")
                    f.write(f"**Rows:** {len(df)}\n")
                    f.write(f"**Columns:** {len(df.columns)}\n\n")

                    f.write("| Column | Type | Description |\n")
                    f.write("|--------|------|-------------|\n")

                    for col in df.columns:
                        dtype = str(df[col].dtype)
                        description = self._get_column_description(table_name, col)
                        f.write(f"| {col} | {dtype} | {description} |\n")

                    f.write("\n")

            self.logger.info("Created data dictionary", path=str(dict_path))
            return str(dict_path)

        except Exception as e:
            self.logger.error(f"Failed to create data dictionary: {e}")
            return ""

    def _get_column_description(self, table_name: str, column_name: str) -> str:
        """Get description for a column based on table and column name."""
        descriptions = {
            "masterbom_clean": {
                "part_id_std": "Standardized part ID (cleaned)",
                "part_id_raw": "Original part ID from source",
                "Item Description": "Part description",
                "Supplier Name": "Primary supplier name",
                "PSW": "Part Submission Warrant status",
                "FAR Status": "First Article Report status",
                "PPAP Details": "Production Part Approval Process details",
            },
            "plant_item_status": {
                "part_id_std": "Standardized part ID",
                "project_plant": "Project/plant identifier",
                "raw_status": "Original status value (X/D/0/blank)",
                "status_class": "Classified status (active/inactive/new/duplicate)",
                "is_duplicate": "Whether part is marked as duplicate",
                "is_new": "Whether part is new to project/plant",
                "n_active": "Count of active plants for this part",
                "n_inactive": "Count of inactive plants for this part",
            },
            "fact_parts": {
                "part_id_std": "Standardized part ID (primary key)",
                "psw_ok": "Whether PSW is available and OK",
                "far_ok": "Whether FAR status is OK",
                "imds_ok": "Whether IMDS status is OK",
                "has_handling_manual": "Whether handling manual exists",
            },
            "status_clean": {
                "OEM": "Original Equipment Manufacturer",
                "Project": "Project name",
                "Total_Part_Numbers": "Total number of parts in project",
                "PSW_Available": "Percentage of PSW available (0-1)",
                "Drawing_Available": "Percentage of drawings available (0-1)",
            },
            "dim_dates": {
                "date": "Date value",
                "role": "Source column name for this date",
                "year": "Year component",
                "month": "Month component (1-12)",
                "quarter": "Quarter component (1-4)",
                "week": "ISO week number",
            },
        }

        table_desc = descriptions.get(table_name, {})
        return table_desc.get(column_name, "Data column")

    def clear_processed_files(self):
        """Clear all processed files to ensure fresh ETL run."""
        try:
            files_removed = 0
            # Remove all files except .gitkeep
            for file_path in self.processed_folder.iterdir():
                if file_path.is_file() and file_path.name != ".gitkeep":
                    file_path.unlink()
                    files_removed += 1

            self.logger.info("Cleared processed folder", files_removed=files_removed)

        except Exception as e:
            self.logger.warning(f"Failed to clear processed files: {e}")

    def cleanup_old_files(self, keep_latest: int = 5):
        """Clean up old processed files, keeping only the latest N versions."""
        try:
            # This is a simple implementation - in production you might want
            # more sophisticated cleanup based on timestamps
            all_files = list(self.processed_folder.glob("*"))

            if len(all_files) > keep_latest * 6:  # Rough estimate for file types
                # Sort by modification time and remove oldest
                all_files.sort(key=lambda x: x.stat().st_mtime)

                files_to_remove = all_files[: -keep_latest * 6]
                for file_path in files_to_remove:
                    if file_path.is_file():
                        file_path.unlink()

                self.logger.info("Cleaned up old files", removed=len(files_to_remove))

        except Exception as e:
            self.logger.warning(f"Failed to cleanup old files: {e}")
