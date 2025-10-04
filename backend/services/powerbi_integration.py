"""PowerBI integration service for automated pipeline."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from backend.core.config import settings
from backend.core.logging import ETLLogger


class PowerBIIntegration:
    """Service for PowerBI template creation and integration."""

    def __init__(self, logger: Optional[ETLLogger] = None):
        """Initialize PowerBI integration service."""
        self.logger = logger or ETLLogger()
        self.pipeline_folder = settings.pipeline_output_folder_path
        self.templates_folder = settings.powerbi_templates_folder_path
        self.processed_folder = settings.processed_folder_path

        # Ensure directories exist
        self.pipeline_folder.mkdir(parents=True, exist_ok=True)
        self.templates_folder.mkdir(parents=True, exist_ok=True)

    def copy_files_to_pipeline(self, artifacts: List[Dict]) -> List[str]:
        """
        Copy processed files to pipeline output folder.

        Args:
            artifacts: List of artifact information from ETL processing

        Returns:
            List of copied file paths
        """
        copied_files = []

        try:
            self.logger.info(
                "Copying files to pipeline output folder",
                destination=str(self.pipeline_folder),
            )

            for artifact in artifacts:
                source_path = Path(artifact["path"])
                if not source_path.exists():
                    self.logger.warning(f"Source file not found: {source_path}")
                    continue

                # Copy to pipeline folder
                dest_path = self.pipeline_folder / source_path.name
                shutil.copy2(source_path, dest_path)
                copied_files.append(str(dest_path))

                self.logger.info(
                    f"Copied file: {source_path.name}",
                    size_bytes=artifact.get("size_bytes", 0),
                )

            self.logger.info("File copy completed", files_copied=len(copied_files))

            return copied_files

        except Exception as e:
            self.logger.error(f"Failed to copy files to pipeline: {e}")
            return []

    def create_powerbi_template(
        self, dataframes: Dict[str, pd.DataFrame]
    ) -> Optional[str]:
        """
        Create PowerBI template file (.pbit) with data connections.

        Args:
            dataframes: Dictionary of processed dataframes

        Returns:
            Path to created template file or None if failed
        """
        try:
            template_name = "ETL_Dashboard_Template.pbit"
            template_path = self.templates_folder / template_name

            # Create template metadata
            template_metadata = self._create_template_metadata(dataframes)

            # Create Power Query connections
            power_queries = self._create_power_queries(dataframes)

            # Create basic template structure
            template_content = {
                "version": "1.0",
                "name": "ETL Dashboard Template",
                "description": "Automated ETL Dashboard PowerBI Template",
                "dataModel": {
                    "tables": list(dataframes.keys()),
                    "relationships": self._create_relationships(dataframes),
                },
                "queries": power_queries,
                "metadata": template_metadata,
            }

            # Save template configuration
            config_path = self.templates_folder / "template_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(template_content, f, indent=2, ensure_ascii=False)

            # Create PowerBI template file (simplified version)
            self._create_pbit_file(template_path, template_content)

            self.logger.info(
                "PowerBI template created", template_path=str(template_path)
            )

            return str(template_path)

        except Exception as e:
            self.logger.error(f"Failed to create PowerBI template: {e}")
            return None

    def _create_template_metadata(self, dataframes: Dict[str, pd.DataFrame]) -> Dict:
        """Create template metadata."""
        return {
            "created_by": "ETL Dashboard",
            "tables_count": len(dataframes),
            "total_rows": sum(len(df) for df in dataframes.values()),
            "data_source": "Parquet Files",
            "refresh_method": "Manual/Scheduled",
        }

    def _create_power_queries(self, dataframes: Dict[str, pd.DataFrame]) -> Dict:
        """Create Power Query M scripts for each table."""
        queries = {}

        for table_name, df in dataframes.items():
            # Create M script for Parquet file connection
            parquet_file = f"{table_name}.parquet"

            m_script = f"""let
    Source = Parquet.Document(File.Contents("{self.pipeline_folder.absolute()}/{parquet_file}")),
    PromoteHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangeTypes = {self._generate_column_types(df)}
in
    ChangeTypes"""

            queries[table_name] = {
                "script": m_script,
                "description": f"Load {table_name} from Parquet file",
            }

        return queries

    def _generate_column_types(self, df: pd.DataFrame) -> str:
        """Generate Power Query column type transformations."""
        type_mappings = {
            "object": "type text",
            "int64": "Int64.Type",
            "float64": "type number",
            "bool": "type logical",
            "datetime64[ns]": "type datetime",
        }

        column_types = []
        for col, dtype in df.dtypes.items():
            pbi_type = type_mappings.get(str(dtype), "type text")
            column_types.append(f'{{"{col}", {pbi_type}}}')

        return (
            f"Table.TransformColumnTypes(PromoteHeaders,{{{', '.join(column_types)}}})"
        )

    def _create_relationships(self, dataframes: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Create suggested relationships between tables."""
        relationships = []

        # Common relationship patterns
        if "masterbom_clean" in dataframes and "plant_item_status" in dataframes:
            relationships.append(
                {
                    "from_table": "masterbom_clean",
                    "from_column": "part_id_std",
                    "to_table": "plant_item_status",
                    "to_column": "part_id_std",
                    "cardinality": "one_to_many",
                }
            )

        if "fact_parts" in dataframes and "dim_dates" in dataframes:
            relationships.append(
                {
                    "from_table": "fact_parts",
                    "from_column": "Approved Date_date",
                    "to_table": "dim_dates",
                    "to_column": "date",
                    "cardinality": "many_to_one",
                }
            )

        return relationships

    def _create_pbit_file(self, template_path: Path, content: Dict):
        """Create a PowerBI template file (simplified)."""
        # For now, create a JSON file with template configuration
        # In a full implementation, this would create a proper .pbit file
        with open(template_path.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        # Create a simple .pbit placeholder
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("PowerBI Template - Use template_config.json for configuration")

    def get_powerbi_desktop_path(self) -> str:
        """Find PowerBI Desktop installation path."""
        common_paths = [
            r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
            r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
            r"C:\Users\{}\AppData\Local\Microsoft\WindowsApps\PBIDesktop.exe".format(
                Path.home().name
            ),
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    def open_powerbi_template(self, template_path: str) -> bool:
        """
        Open PowerBI template in PowerBI Desktop.

        Args:
            template_path: Path to the template file

        Returns:
            True if successfully opened, False otherwise
        """
        try:
            pbi_path = self.get_powerbi_desktop_path()
            if not pbi_path:
                self.logger.warning("PowerBI Desktop not found")
                return False

            # Open template in PowerBI Desktop
            subprocess.Popen([pbi_path, template_path])

            self.logger.info("PowerBI template opened", template_path=template_path)
            return True

        except Exception as e:
            self.logger.error(f"Failed to open PowerBI template: {e}")
            return False

    def create_data_source_info(self, copied_files: List[str]) -> Dict:
        """Create data source information for PowerBI."""
        return {
            "data_folder": str(self.pipeline_folder.absolute()),
            "files": [Path(f).name for f in copied_files],
            "parquet_files": [f for f in copied_files if f.endswith(".parquet")],
            "csv_files": [f for f in copied_files if f.endswith(".csv")],
            "sqlite_files": [f for f in copied_files if f.endswith(".sqlite")],
            "connection_string": f'Folder.Files("{self.pipeline_folder.absolute()}")',
        }
