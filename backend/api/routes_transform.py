"""Transform API routes for ETL processing."""

import time
import uuid
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.core.config import settings
from backend.core.logging import ETLLogger, logger
from backend.models.schemas import (
    ArtifactInfo,
    TransformRequest,
    TransformResponse,
    TransformSummary,
)
from backend.services.cleaning import create_dim_dates, detect_date_columns
from backend.services.excel_reader import ExcelReader
from backend.services.masterbom_rules import MasterBOMProcessor
from backend.services.status_processor_v2 import StatusProcessorV2
from backend.services.storage import DataStorage

# Pipeline service removed - manual ETL only

router = APIRouter()


@router.post("/transform", response_model=TransformResponse)
async def transform_data(request: TransformRequest):
    """
    Run ETL transformation on uploaded Excel file.

    Args:
        request: Transform request with file_id, sheet selections, and options

    Returns:
        TransformResponse with artifacts, summary, and processing messages
    """
    start_time = time.time()
    etl_logger = ETLLogger()

    try:
        # Validate file_id format
        try:
            uuid.UUID(request.file_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        # Check if file exists
        upload_path = settings.upload_folder_path / f"{request.file_id}.xlsx"

        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        etl_logger.info(
            "Starting ETL transformation",
            file_id=request.file_id,
            master_sheet=request.master_sheet,
            status_sheet=request.status_sheet,
        )

        # Create Excel reader
        excel_reader = ExcelReader(upload_path)

        try:
            # Validate sheet names
            available_sheets = excel_reader.get_sheet_names()

            if request.master_sheet not in available_sheets:
                raise HTTPException(
                    status_code=400,
                    detail=f"Master sheet '{request.master_sheet}' not found",
                )

            if request.status_sheet not in available_sheets:
                raise HTTPException(
                    status_code=400,
                    detail=f"Status sheet '{request.status_sheet}' not found",
                )

            # Read sheets
            etl_logger.info("Reading Excel sheets")

            master_df = excel_reader.read_sheet(request.master_sheet)
            status_df = excel_reader.read_sheet(request.status_sheet)

            etl_logger.info(
                "Sheets loaded successfully",
                master_rows=len(master_df),
                master_cols=len(master_df.columns),
                status_rows=len(status_df),
                status_cols=len(status_df.columns),
            )

            # Process MasterBOM sheet
            etl_logger.info("=== STARTING MASTERBOM PROCESSING ===")
            etl_logger.info(
                "Processing MasterBOM sheet",
                input_rows=len(master_df),
                input_cols=len(master_df.columns),
                id_col=request.options.id_col,
                date_cols=request.options.date_cols,
            )

            master_processor = MasterBOMProcessor(master_df, etl_logger)
            master_results = master_processor.process(
                id_col=request.options.id_col, date_cols=request.options.date_cols
            )

            etl_logger.info(
                "=== MASTERBOM PROCESSING COMPLETE ===",
                output_tables=len(master_results),
                table_names=list(master_results.keys()),
            )

            # Process Status sheet
            etl_logger.info("=== STARTING STATUS SHEET PROCESSING ===")
            etl_logger.info(
                "Processing Status sheet",
                input_rows=len(status_df),
                input_cols=len(status_df.columns),
            )

            status_processor = StatusProcessorV2(status_df, etl_logger)
            status_results = status_processor.process()
            status_clean = status_results["status_clean"]
            project_completion = status_results["project_completion_by_plant"]

            etl_logger.info(
                "=== STATUS SHEET PROCESSING COMPLETE ===",
                status_clean_rows=len(status_clean),
                project_completion_rows=len(project_completion),
            )

            # Create date dimension from all date columns
            etl_logger.info("=== STARTING DATE DIMENSION CREATION ===")
            etl_logger.info("Creating date dimension")

            date_columns = []
            date_column_names = []

            # Collect date columns from MasterBOM
            etl_logger.info(
                "Collecting specified date columns",
                specified_cols=request.options.date_cols,
            )
            for col in request.options.date_cols:
                if col in master_df.columns:
                    date_columns.append(master_df[col])
                    date_column_names.append(col)
                    etl_logger.info(f"Added specified date column: {col}")

            # Auto-detect additional date columns
            etl_logger.info("Auto-detecting additional date columns")
            auto_date_cols = detect_date_columns(master_df)

            # Filter out excluded date columns
            if request.options.excluded_date_cols:
                etl_logger.info(
                    "Excluding specified date columns",
                    excluded=request.options.excluded_date_cols,
                )
                auto_date_cols = [
                    col
                    for col in auto_date_cols
                    if col not in request.options.excluded_date_cols
                ]

            etl_logger.info("Auto-detected date columns", detected_cols=auto_date_cols)

            for col in auto_date_cols:
                if col not in date_column_names and col in master_df.columns:
                    date_columns.append(master_df[col])
                    date_column_names.append(col)
                    etl_logger.info(f"Added auto-detected date column: {col}")

            etl_logger.info(
                "Final date columns for dimension",
                total_columns=len(date_column_names),
                column_names=date_column_names,
            )

            dim_dates, date_role_bridge = create_dim_dates(
                date_columns, date_column_names
            )

            etl_logger.info(
                "=== DATE DIMENSION CREATION COMPLETE ===",
                dim_dates_rows=len(dim_dates),
                date_bridge_rows=len(date_role_bridge),
            )

            # Prepare all DataFrames for storage
            all_dataframes = {
                "masterbom_clean": master_results["masterbom_clean"],
                "plant_item_status": master_results["plant_item_status"],
                "fact_parts": master_results["fact_parts"],
                "status_clean": status_clean,
                "project_completion_by_plant": project_completion,
                "dim_dates": dim_dates,
                "date_role_bridge": date_role_bridge,
            }

            # Save data in multiple formats
            etl_logger.info("Saving processed data")

            storage = DataStorage(etl_logger)
            artifacts = storage.save_all_formats(all_dataframes)

            # Create data dictionary
            dict_path = storage.create_data_dictionary(all_dataframes)
            if dict_path:
                dict_size = Path(dict_path).stat().st_size
                artifacts.append(
                    ArtifactInfo(
                        name="data_dictionary.md",
                        path=dict_path,
                        format="Markdown",
                        size_bytes=dict_size,
                    )
                )

            # Calculate summary statistics
            summary = _calculate_summary(all_dataframes, date_column_names, start_time)

            etl_logger.info(
                "ETL transformation completed successfully",
                processing_time=summary.processing_time_seconds,
                total_artifacts=len(artifacts),
            )

            response = TransformResponse(
                success=True,
                artifacts=artifacts,
                summary=summary,
                messages=etl_logger.get_messages(),
            )

            return response

        finally:
            excel_reader.close()

    except HTTPException:
        etl_logger.error("ETL transformation failed with HTTP error")
        raise

    except Exception as e:
        etl_logger.error(
            "ETL transformation failed with unexpected error", error=str(e)
        )

        logger.error(
            "Unexpected error during ETL transformation",
            file_id=request.file_id,
            error=str(e),
        )

        return TransformResponse(
            success=False,
            artifacts=[],
            summary=TransformSummary(
                total_parts=0,
                active_parts=0,
                inactive_parts=0,
                new_parts=0,
                duplicate_parts=0,
                plants_detected=0,
                duplicates_removed=0,
                date_columns_processed=[],
                processing_time_seconds=time.time() - start_time,
            ),
            messages=etl_logger.get_messages(),
            error=str(e),
        )


def _calculate_summary(
    dataframes: Dict[str, pd.DataFrame], date_columns: list, start_time: float
) -> TransformSummary:
    """Calculate summary statistics from processed DataFrames."""

    # Get plant-item-status for statistics
    plant_status = dataframes.get("plant_item_status", pd.DataFrame())

    if not plant_status.empty:
        # Count parts by status
        status_counts = plant_status["status_class"].value_counts()

        total_parts = int(plant_status["part_id_std"].nunique())
        active_parts = int(status_counts.get("active", 0))
        inactive_parts = int(status_counts.get("inactive", 0))
        new_parts = int(status_counts.get("new", 0))
        duplicate_parts = int(status_counts.get("duplicate", 0))

        plants_detected = int(plant_status["project_plant"].nunique())
    else:
        total_parts = active_parts = inactive_parts = new_parts = duplicate_parts = (
            plants_detected
        ) = 0

    # Count duplicates removed from MasterBOM
    masterbom = dataframes.get("masterbom_clean", pd.DataFrame())
    duplicates_removed = 0  # This would be calculated during processing

    processing_time = time.time() - start_time

    return TransformSummary(
        total_parts=total_parts,
        active_parts=active_parts,
        inactive_parts=inactive_parts,
        new_parts=new_parts,
        duplicate_parts=duplicate_parts,
        plants_detected=plants_detected,
        duplicates_removed=duplicates_removed,
        date_columns_processed=date_columns,
        processing_time_seconds=round(processing_time, 2),
    )


@router.get("/transform/{file_id}/status")
async def get_transform_status(file_id: str):
    """
    Get status of a transformation (for future async processing).

    Args:
        file_id: ID of the file being processed

    Returns:
        Status information
    """
    # This is a placeholder for future async processing implementation
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID format")

    # For now, return a simple status
    return {
        "file_id": file_id,
        "status": "not_implemented",
        "message": "Async processing not yet implemented",
    }


# Pipeline status endpoint removed - manual ETL only
