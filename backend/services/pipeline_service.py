"""Automated pipeline service for ETL processing."""

import shutil
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from backend.core.config import settings
from backend.core.logging import ETLLogger
from backend.models.schemas import ArtifactInfo


class PipelineService:
    """Service for automated ETL pipeline processing."""

    def __init__(self, logger: Optional[ETLLogger] = None):
        """Initialize pipeline service."""
        self.logger = logger or ETLLogger()

    def execute_post_etl_pipeline(
        self,
        artifacts: List[ArtifactInfo],
        dataframes: Dict[str, pd.DataFrame],
        file_id: str,
    ) -> Dict:
        """
        Execute the automated pipeline after ETL transformation.

        Args:
            artifacts: List of generated artifacts from ETL
            dataframes: Dictionary of processed dataframes
            file_id: ID of the processed file

        Returns:
            Pipeline execution results
        """
        pipeline_results = {
            "file_id": file_id,
            "pipeline_executed": True,
            "copied_files": [],
            "data_source_info": {},
            "errors": [],
        }

        try:
            self.logger.info(
                "Starting post-ETL pipeline",
                file_id=file_id,
                artifacts_count=len(artifacts),
            )

            # Step 1: Copy files to pipeline output folder
            if settings.auto_copy_to_pipeline:
                copied_files = self._copy_files_to_pipeline(artifacts)
                pipeline_results["copied_files"] = copied_files

                if copied_files:
                    self.logger.info(
                        "Files copied to pipeline folder", files_count=len(copied_files)
                    )
                else:
                    pipeline_results["errors"].append(
                        "Failed to copy files to pipeline folder"
                    )

            # Step 2: Create data source information
            data_source_info = self._create_data_source_info(
                pipeline_results["copied_files"]
            )
            pipeline_results["data_source_info"] = data_source_info

            # Step 4: Generate pipeline summary
            pipeline_results["summary"] = self._create_pipeline_summary(
                pipeline_results, dataframes
            )

            self.logger.info(
                "Post-ETL pipeline completed successfully",
                file_id=file_id,
                errors_count=len(pipeline_results["errors"]),
            )

            return pipeline_results

        except Exception as e:
            error_msg = f"Pipeline execution failed: {e}"
            self.logger.error(error_msg, file_id=file_id)
            pipeline_results["errors"].append(error_msg)
            pipeline_results["pipeline_executed"] = False
            return pipeline_results

    def _copy_files_to_pipeline(self, artifacts: List[ArtifactInfo]) -> List[str]:
        """Copy artifacts to pipeline output folder."""
        try:
            # Convert ArtifactInfo objects to dictionaries
            artifact_dicts = []
            for artifact in artifacts:
                if hasattr(artifact, "dict"):
                    artifact_dicts.append(artifact.dict())
                else:
                    # Handle case where artifact is already a dict
                    artifact_dicts.append(
                        {
                            "path": getattr(artifact, "path", str(artifact)),
                            "name": getattr(artifact, "name", Path(str(artifact)).name),
                            "size_bytes": getattr(artifact, "size_bytes", 0),
                        }
                    )

            # Copy files to pipeline output folder
            copied_files = []
            pipeline_folder = settings.pipeline_output_folder_path
            pipeline_folder.mkdir(parents=True, exist_ok=True)

            for artifact_dict in artifact_dicts:
                source_path = Path(artifact_dict["path"])
                if source_path.exists():
                    dest_path = pipeline_folder / artifact_dict["name"]
                    shutil.copy2(source_path, dest_path)
                    copied_files.append(str(dest_path))
                    self.logger.info(f"Copied file to pipeline: {dest_path}")

            return copied_files

        except Exception as e:
            self.logger.error(f"Failed to copy files to pipeline: {e}")
            return []

    def _create_data_source_info(self, copied_files: List[str]) -> Dict:
        """Create comprehensive data source information."""
        return {
            "files": copied_files,
            "count": len(copied_files),
            "pipeline_folder": str(settings.pipeline_output_folder_path.absolute()),
            "file_types": list(set(Path(f).suffix for f in copied_files)),
        }

    def _create_pipeline_summary(
        self, pipeline_results: Dict, dataframes: Dict[str, pd.DataFrame]
    ) -> Dict:
        """Create pipeline execution summary."""
        return {
            "pipeline_folder": str(settings.pipeline_output_folder_path.absolute()),
            "files_copied": len(pipeline_results["copied_files"]),
            "tables_processed": len(dataframes),
            "total_rows": sum(len(df) for df in dataframes.values()),
            "parquet_files": len(
                [f for f in pipeline_results["copied_files"] if f.endswith(".parquet")]
            ),
            "csv_files": len(
                [f for f in pipeline_results["copied_files"] if f.endswith(".csv")]
            ),
            "sqlite_files": len(
                [f for f in pipeline_results["copied_files"] if f.endswith(".sqlite")]
            ),
            "errors": pipeline_results["errors"],
        }

    def get_pipeline_status(self, file_id: str) -> Dict:
        """Get current pipeline status for a file."""
        try:
            pipeline_folder = settings.pipeline_output_folder_path

            # Check for files in pipeline folder
            pipeline_files = []
            if pipeline_folder.exists():
                pipeline_files = [
                    f.name for f in pipeline_folder.iterdir() if f.is_file()
                ]

            return {
                "file_id": file_id,
                "pipeline_folder_exists": pipeline_folder.exists(),
                "pipeline_files": pipeline_files,
                "pipeline_folder_path": str(pipeline_folder.absolute()),
                "files_count": len(pipeline_files),
            }

        except Exception as e:
            self.logger.error(f"Failed to get pipeline status: {e}")
            return {"file_id": file_id, "error": str(e)}
