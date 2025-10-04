"""Business rules and transformations for Status sheet processing."""

import re
from typing import Dict, List, Optional

import pandas as pd

from backend.core.logging import ETLLogger
from backend.services.cleaning import standardize_text


class StatusProcessor:
    """Processor for Status sheet with business rules."""

    def __init__(self, df: pd.DataFrame, logger: ETLLogger):
        """Initialize with DataFrame and logger."""
        self.df = df.copy()
        self.logger = logger

    def process(self) -> Dict[str, pd.DataFrame]:
        """
        Process Status sheet according to business rules.

        Returns:
            Dictionary containing cleaned Status DataFrame and project completion data
        """
        self.logger.info(
            "Starting Status sheet processing",
            input_rows=len(self.df),
            input_cols=len(self.df.columns),
        )

        try:
            # Step 1: Clean headers
            self.logger.info("Step 1: Cleaning headers")
            self._clean_headers()

            # Step 2: Standardize text columns
            self.logger.info("Step 2: Standardizing text columns")
            self._standardize_text_columns()

            # Step 3: Convert percentage columns
            self.logger.info("Step 3: Converting percentage columns")
            self._convert_percentage_columns()

            # Step 4: Clean project names
            self.logger.info("Step 4: Cleaning project names")
            self._clean_project_names()

            # Step 5: Remove empty rows
            self.logger.info("Step 5: Removing empty rows")
            self._remove_empty_rows()

            # Step 6: Extract project completion by plant
            self.logger.info("Step 6: Extracting project completion by plant")
            project_completion = self._extract_project_completion_by_plant()

            self.logger.info(
                "Status sheet processing complete",
                output_rows=len(self.df),
                output_cols=len(self.df.columns),
                completion_records=len(project_completion),
            )

            return {
                "status_clean": self.df,
                "project_completion_by_plant": project_completion,
            }

        except Exception as e:
            self.logger.error(
                f"Error in status processing: {str(e)}",
                step="status_processing",
                error_type=type(e).__name__,
            )
            raise

    def _clean_headers(self):
        """Clean and standardize column headers."""
        original_cols = self.df.columns.tolist()

        cleaned_cols = []
        for col in original_cols:
            # Convert to string and strip
            clean_col = str(col).strip()

            # Collapse multiple spaces
            clean_col = re.sub(r"\s+", " ", clean_col)

            # Standardize common header patterns
            clean_col = self._standardize_header_name(clean_col)

            cleaned_cols.append(clean_col)

        self.df.columns = cleaned_cols

        self.logger.info(
            "Cleaned column headers",
            original_count=len(original_cols),
            cleaned_count=len(cleaned_cols),
        )

    def _standardize_header_name(self, header: str) -> str:
        """Standardize individual header names."""
        header_lower = header.lower()

        # Common standardizations
        standardizations = {
            "oem": "OEM",
            "project": "Project",
            "ppap": "PPAP",
            "psw": "PSW",
            "total part numbers": "Total_Part_Numbers",
            "psw available": "PSW_Available",
            "drawing available": "Drawing_Available",
            "1st ppap milestone": "First_PPAP_Milestone",
            "managed by": "Managed_By",
        }

        for pattern, replacement in standardizations.items():
            if pattern in header_lower:
                return replacement

        # Default: title case with underscores
        return header.replace(" ", "_").title()

    def _standardize_text_columns(self):
        """Standardize text columns."""
        text_columns = ["OEM", "Project", "Managed_By"]

        standardized = 0
        for col in text_columns:
            try:
                if col in self.df.columns.tolist():
                    self.logger.info(f"Standardizing column: {col}")
                    self.df[col] = standardize_text(self.df[col])
                    standardized += 1
                    self.logger.info(f"Successfully standardized column: {col}")
            except Exception as e:
                self.logger.error(
                    f"Error standardizing column '{col}': {str(e)}",
                    column=col,
                    error_type=type(e).__name__,
                )
                raise

        self.logger.info("Standardized text columns", count=standardized)

    def _convert_percentage_columns(self):
        """Convert percentage columns to numeric values (0-1 range)."""
        try:
            percentage_patterns = [r"%", r"percent", r"available", r"complete"]

            converted = 0
            for col in self.df.columns:
                try:
                    col_lower = str(col).lower()

                    # Check if column name suggests percentages
                    is_percentage = any(
                        pattern in col_lower for pattern in percentage_patterns
                    )

                    if is_percentage:
                        self.logger.info(f"Converting percentage column: {col}")
                        # Convert percentage strings to numeric
                        self.df[col] = self._parse_percentage_values(self.df[col])
                        converted += 1

                        self.logger.info(f"Converted percentage column: {col}")

                except Exception as e:
                    self.logger.warning(
                        f"Failed to convert percentage column '{col}': {e}"
                    )

            self.logger.info("Converted percentage columns", count=converted)

        except Exception as e:
            self.logger.error(
                f"Error in percentage conversion: {str(e)}", error_type=type(e).__name__
            )
            raise

    def _parse_percentage_values(self, series: pd.Series) -> pd.Series:
        """Parse percentage values from various formats."""

        def parse_value(val):
            if pd.isna(val):
                return None

            val_str = str(val).strip()

            # Handle empty strings
            if not val_str:
                return None

            # Remove percentage sign
            val_str = val_str.replace("%", "")

            try:
                # Convert to float
                num_val = float(val_str)

                # If value is > 1, assume it's in percentage format (e.g., 85 = 85%)
                if num_val > 1:
                    return num_val / 100.0
                else:
                    return num_val

            except ValueError:
                # Handle text values like "Complete", "N/A", etc.
                val_lower = val_str.lower()
                if val_lower in ["complete", "done", "finished", "100"]:
                    return 1.0
                elif val_lower in ["none", "n/a", "na", "not available", "0"]:
                    return 0.0
                else:
                    return None

        return series.apply(parse_value)

    def _clean_project_names(self):
        """Clean and standardize project names."""
        try:
            # Check if Project column exists
            if "Project" in self.df.columns.tolist():
                # Remove common prefixes/suffixes
                def clean_project(name):
                    try:
                        if pd.isna(name):
                            return name

                        name = str(name).strip()

                        # Remove common patterns
                        patterns_to_remove = [
                            r"^Project\s*:?\s*",
                            r"\s*-\s*Project$",
                            r"\s*\(.*\)$",  # Remove parenthetical notes
                        ]

                        for pattern in patterns_to_remove:
                            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

                        return name.strip()
                    except Exception as e:
                        # If there's an error processing this name, return it as-is
                        return name

                self.df["Project"] = self.df["Project"].apply(clean_project)

                self.logger.info("Cleaned project names")
        except Exception as e:
            self.logger.warning(f"Failed to clean project names: {e}")

    def _remove_empty_rows(self):
        """Remove rows that are completely empty or contain only whitespace."""
        try:
            original_count = len(self.df)

            # Check for rows where all values are null or empty strings
            def is_row_not_empty(row):
                """Check if a row has any non-empty values."""
                # First check if any values are not null
                if not row.notna().any():
                    return False

                # Then check if any non-null values are not empty strings
                non_null_values = [val for val in row if pd.notna(val)]
                return any(str(val).strip() != "" for val in non_null_values)

            mask = self.df.apply(is_row_not_empty, axis=1)

            # Filter DataFrame using the boolean mask
            self.df = self.df.loc[mask]

            removed_count = original_count - len(self.df)

            if removed_count > 0:
                self.logger.info("Removed empty rows", count=removed_count)

        except Exception as e:
            self.logger.error(
                f"Error removing empty rows: {str(e)}", error_type=type(e).__name__
            )
            raise

    def get_project_summary(self) -> Dict[str, any]:
        """Get summary statistics for the status sheet."""
        summary = {
            "total_projects": 0,
            "total_parts": 0,
            "avg_psw_available": 0,
            "avg_drawing_available": 0,
            "projects_by_oem": {},
        }

        try:
            columns_list = self.df.columns.tolist()

            if "Project" in columns_list:
                summary["total_projects"] = self.df["Project"].nunique()

            if "Total_Part_Numbers" in columns_list:
                total_parts = pd.to_numeric(
                    self.df["Total_Part_Numbers"], errors="coerce"
                )
                summary["total_parts"] = (
                    int(total_parts.sum()) if total_parts.notna().any() else 0
                )

            if "PSW_Available" in columns_list:
                psw_avg = pd.to_numeric(
                    self.df["PSW_Available"], errors="coerce"
                ).mean()
                summary["avg_psw_available"] = (
                    round(psw_avg, 3) if pd.notna(psw_avg) else 0
                )

            if "Drawing_Available" in columns_list:
                drawing_avg = pd.to_numeric(
                    self.df["Drawing_Available"], errors="coerce"
                ).mean()
                summary["avg_drawing_available"] = (
                    round(drawing_avg, 3) if pd.notna(drawing_avg) else 0
                )

            if "OEM" in columns_list and "Project" in columns_list:
                oem_projects = self.df.groupby("OEM")["Project"].nunique().to_dict()
                summary["projects_by_oem"] = oem_projects

        except Exception as e:
            self.logger.warning(f"Failed to generate project summary: {e}")

        return summary

    def _extract_project_completion_by_plant(self) -> pd.DataFrame:
        """
        Extract project completion status by plant from the status sheet.

        Returns:
            DataFrame with normalized project completion data by plant
        """
        try:
            completion_records = []

            # Get column names for analysis
            columns = self.df.columns.tolist()

            # Identify key columns
            project_col = None
            oem_col = None
            milestone_cols = []
            completion_cols = []

            for col in columns:
                col_lower = str(col).lower()

                # Project identification
                if "project" in col_lower and project_col is None:
                    project_col = col

                # OEM identification
                if "oem" in col_lower and oem_col is None:
                    oem_col = col

                # Milestone date columns
                if any(
                    keyword in col_lower
                    for keyword in ["milestone", "ppap", "date", "deadline"]
                ):
                    milestone_cols.append(col)

                # Completion/percentage columns
                if any(
                    keyword in col_lower
                    for keyword in ["%", "percent", "complete", "available", "status"]
                ):
                    completion_cols.append(col)

            self.logger.info(
                "Identified completion analysis columns",
                project_col=project_col,
                oem_col=oem_col,
                milestone_cols=len(milestone_cols),
                completion_cols=len(completion_cols),
            )

            # Process each row to extract completion data
            for idx, row in self.df.iterrows():
                try:
                    # Extract base project information
                    project_name = (
                        str(row.get(project_col, "")).strip()
                        if project_col
                        else f"Project_{idx}"
                    )
                    oem_name = (
                        str(row.get(oem_col, "")).strip() if oem_col else "Unknown"
                    )

                    if not project_name or project_name.lower() in ["nan", "none", ""]:
                        continue

                    # Extract plant information from project name
                    plants = self._extract_plants_from_project(project_name)

                    # If no plants extracted, create a single record for the project
                    if not plants:
                        plants = [
                            {"plant_id": project_name, "plant_name": project_name}
                        ]

                    # Process completion data for each plant
                    for plant_info in plants:
                        completion_record = {
                            "project_name": project_name,
                            "oem": oem_name,
                            "plant_id": plant_info["plant_id"],
                            "plant_name": plant_info["plant_name"],
                            "overall_completion_pct": None,
                            "psw_completion_pct": None,
                            "drawing_completion_pct": None,
                            "imds_completion_pct": None,
                            "ppap_completion_pct": None,
                            "completion_status": "Unknown",
                            "milestone_date": None,
                            "total_parts": None,
                        }

                        # Extract completion percentages
                        for col in completion_cols:
                            col_lower = str(col).lower()

                            # Handle potential Series values from duplicate columns
                            try:
                                value = row[col]
                                # If value is a Series, take the first non-null value
                                if hasattr(value, "iloc"):
                                    value = value.iloc[0] if len(value) > 0 else None
                            except (KeyError, IndexError):
                                continue

                            # Special handling for drawing (may be referred to as '%.1 drawing')
                            if ".1" in col_lower and "drawing" in col_lower:
                                col_lower = "drawing"  # Normalize to 'drawing' for matching below

                            if pd.notna(value):
                                # Parse completion value
                                completion_pct = self._parse_completion_value(value)

                                # Categorize by column type
                                if "psw" in col_lower:
                                    completion_record["psw_completion_pct"] = (
                                        completion_pct
                                    )
                                elif "drawing" in col_lower:
                                    completion_record["drawing_completion_pct"] = (
                                        completion_pct
                                    )
                                elif "imds" in col_lower:
                                    completion_record["imds_completion_pct"] = (
                                        completion_pct
                                    )
                                elif "ppap" in col_lower:
                                    completion_record["ppap_completion_pct"] = (
                                        completion_pct
                                    )
                                elif any(
                                    keyword in col_lower
                                    for keyword in ["total", "overall", "complete"]
                                ):
                                    completion_record["overall_completion_pct"] = (
                                        completion_pct
                                    )

                        # Extract milestone dates
                        for col in milestone_cols:
                            try:
                                value = row[col]
                                # If value is a Series, take the first non-null value
                                if hasattr(value, "iloc"):
                                    value = value.iloc[0] if len(value) > 0 else None
                            except (KeyError, IndexError):
                                continue

                            if pd.notna(value):
                                try:
                                    milestone_date = pd.to_datetime(
                                        value, errors="coerce"
                                    )
                                    if pd.notna(milestone_date):
                                        completion_record["milestone_date"] = (
                                            milestone_date.date()
                                        )
                                        break  # Use first valid date found
                                except:
                                    continue

                        # Extract total parts if available
                        for col in columns:
                            if (
                                "total" in str(col).lower()
                                and "part" in str(col).lower()
                            ):
                                try:
                                    value = row[col]
                                    # If value is a Series, take the first non-null value
                                    if hasattr(value, "iloc"):
                                        value = (
                                            value.iloc[0] if len(value) > 0 else None
                                        )
                                except (KeyError, IndexError):
                                    continue

                                if pd.notna(value):
                                    try:
                                        completion_record["total_parts"] = int(
                                            float(str(value))
                                        )
                                        break
                                    except:
                                        continue

                        # Determine overall completion status
                        completion_record["completion_status"] = (
                            self._determine_completion_status(completion_record)
                        )

                        completion_records.append(completion_record)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to process completion data for row {idx}: {e}"
                    )
                    continue

            # Create DataFrame from records
            if completion_records:
                completion_df = pd.DataFrame(completion_records)

                # Remove duplicates (same project + plant combination)
                completion_df = completion_df.drop_duplicates(
                    subset=["project_name", "plant_id"], keep="first"
                )

                self.logger.info(
                    "Project completion extraction complete",
                    total_records=len(completion_df),
                    unique_projects=completion_df["project_name"].nunique(),
                    unique_plants=completion_df["plant_id"].nunique(),
                )

                return completion_df
            else:
                self.logger.warning("No completion records extracted")
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Failed to extract project completion data: {e}")
            return pd.DataFrame()

    def _extract_plants_from_project(self, project_name: str) -> List[Dict[str, str]]:
        """
        Extract plant information from project name.

        Args:
            project_name: Project name that may contain plant identifiers

        Returns:
            List of plant dictionaries with plant_id and plant_name
        """
        plants = []

        # Common plant/facility patterns
        plant_patterns = [
            r"_([A-Z]{2,4})$",  # Suffix like _YMOK, _YRL
            r"_([A-Z]{2,4})_",  # Middle like _YMOK_, _YRL_
            r"([A-Z]{2,4})\+",  # Before plus like YMOK+, YRL+
            r"Plant[_\s]*([A-Z0-9]+)",  # Plant identifier
            r"Facility[_\s]*([A-Z0-9]+)",  # Facility identifier
        ]

        for pattern in plant_patterns:
            matches = re.findall(pattern, project_name, re.IGNORECASE)
            for match in matches:
                plant_id = match.upper()
                plants.append({"plant_id": plant_id, "plant_name": f"Plant_{plant_id}"})

        # If no specific plants found, try to extract from the full project name
        if not plants:
            # Look for common separators that might indicate multiple plants/locations
            separators = ["_", "-", "+", "&"]
            for sep in separators:
                if sep in project_name:
                    parts = project_name.split(sep)
                    for i, part in enumerate(parts):
                        if len(part.strip()) >= 2:  # Reasonable plant identifier length
                            plant_id = part.strip().upper()
                            plants.append(
                                {
                                    "plant_id": plant_id,
                                    "plant_name": f"Plant_{plant_id}",
                                }
                            )
                    break

        return plants

    def _parse_completion_value(self, value) -> Optional[float]:
        """
        Parse completion value from various formats.

        Args:
            value: Raw completion value

        Returns:
            Completion percentage as float (0.0 to 1.0) or None
        """
        if pd.isna(value):
            return None

        value_str = str(value).strip().lower()

        # Handle text statuses
        if value_str in ["complete", "done", "finished", "100%", "100"]:
            return 1.0
        elif value_str in ["none", "n/a", "na", "not available", "0%", "0"]:
            return 0.0
        elif value_str in ["in progress", "ongoing", "partial"]:
            return 0.5  # Assume 50% for in-progress

        # Handle percentage strings
        if "%" in value_str:
            try:
                num_val = float(value_str.replace("%", ""))
                return num_val / 100.0 if num_val > 1 else num_val
            except:
                return None

        # Handle numeric values
        try:
            num_val = float(value_str)
            return num_val / 100.0 if num_val > 1 else num_val
        except:
            return None

    def _determine_completion_status(self, record: Dict) -> str:
        """
        Determine overall completion status based on available metrics.

        Args:
            record: Completion record dictionary

        Returns:
            Status string
        """
        # Collect all available completion percentages
        completion_values = []

        for key in [
            "overall_completion_pct",
            "psw_completion_pct",
            "drawing_completion_pct",
            "imds_completion_pct",
            "ppap_completion_pct",
        ]:
            value = record.get(key)
            if value is not None:
                completion_values.append(value)

        if not completion_values:
            return "Unknown"

        # Calculate average completion
        avg_completion = sum(completion_values) / len(completion_values)

        # Determine status based on average
        if avg_completion >= 1.0:
            return "Complete"
        elif avg_completion >= 0.8:
            return "Near Complete"
        elif avg_completion >= 0.5:
            return "In Progress"
        elif avg_completion > 0:
            return "Started"
        else:
            return "Not Started"
