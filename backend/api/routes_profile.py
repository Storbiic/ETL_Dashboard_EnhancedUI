"""Profile API routes for data quality analysis."""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from backend.core.config import settings
from backend.core.logging import logger
from backend.models.schemas import ProfileResponse
from backend.services.excel_reader import ExcelReader
from backend.services.profiler import DataProfiler

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
async def profile_sheet(
    file_id: str = Query(..., description="File ID from upload"),
    sheet: str = Query(..., description="Sheet name to profile"),
):
    """
    Profile a sheet for data quality analysis.

    Args:
        file_id: ID of the uploaded file
        sheet: Name of the sheet to profile

    Returns:
        ProfileResponse with data quality metrics
    """
    try:
        # Validate file_id format
        try:
            uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        # Check if file exists
        upload_path = settings.upload_folder_path / f"{file_id}.xlsx"

        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        logger.info("Starting sheet profiling", file_id=file_id, sheet=sheet)

        # Create Excel reader
        excel_reader = ExcelReader(upload_path)

        try:
            # Get available sheet names
            available_sheets = excel_reader.get_sheet_names()

            if sheet not in available_sheets:
                raise HTTPException(
                    status_code=400,
                    detail=f"Sheet '{sheet}' not found. Available sheets: {available_sheets}",
                )

            # Read the sheet data
            df = excel_reader.read_sheet(sheet)

            # Create profiler and analyze
            profiler = DataProfiler(df, sheet)
            profile_result = profiler.profile_sheet()

            logger.info(
                "Sheet profiling completed",
                file_id=file_id,
                sheet=sheet,
                rows=profile_result.total_rows,
                cols=profile_result.total_cols,
                duplicates=profile_result.duplicate_rows,
            )

            return profile_result

        finally:
            excel_reader.close()

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Error during sheet profiling", file_id=file_id, sheet=sheet, error=str(e)
        )

        raise HTTPException(
            status_code=500, detail=f"Internal server error during profiling: {str(e)}"
        )


@router.get("/profile/{file_id}/compare")
async def compare_sheets(
    file_id: str,
    sheet1: str = Query(..., description="First sheet to compare"),
    sheet2: str = Query(..., description="Second sheet to compare"),
):
    """
    Compare two sheets for compatibility analysis.

    Args:
        file_id: ID of the uploaded file
        sheet1: Name of the first sheet
        sheet2: Name of the second sheet

    Returns:
        Comparison analysis between the two sheets
    """
    try:
        # Validate file_id format
        try:
            uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        # Check if file exists
        upload_path = settings.upload_folder_path / f"{file_id}.xlsx"

        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        logger.info(
            "Starting sheet comparison", file_id=file_id, sheet1=sheet1, sheet2=sheet2
        )

        # Create Excel reader
        excel_reader = ExcelReader(upload_path)

        try:
            # Get available sheet names
            available_sheets = excel_reader.get_sheet_names()

            for sheet in [sheet1, sheet2]:
                if sheet not in available_sheets:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Sheet '{sheet}' not found. Available sheets: {available_sheets}",
                    )

            # Profile both sheets
            df1 = excel_reader.read_sheet(sheet1)
            df2 = excel_reader.read_sheet(sheet2)

            profiler1 = DataProfiler(df1, sheet1)
            profiler2 = DataProfiler(df2, sheet2)

            profile1 = profiler1.profile_sheet()
            profile2 = profiler2.profile_sheet()

            # Compare profiles
            comparison = {
                "sheet1": {
                    "name": sheet1,
                    "rows": profile1.total_rows,
                    "cols": profile1.total_cols,
                    "duplicates": profile1.duplicate_rows,
                },
                "sheet2": {
                    "name": sheet2,
                    "rows": profile2.total_rows,
                    "cols": profile2.total_cols,
                    "duplicates": profile2.duplicate_rows,
                },
                "compatibility": {
                    "size_difference": abs(profile1.total_rows - profile2.total_rows),
                    "column_difference": abs(profile1.total_cols - profile2.total_cols),
                    "common_columns": [],
                    "sheet1_only_columns": [],
                    "sheet2_only_columns": [],
                },
            }

            # Find common and unique columns
            cols1 = {col.name for col in profile1.columns}
            cols2 = {col.name for col in profile2.columns}

            comparison["compatibility"]["common_columns"] = list(cols1 & cols2)
            comparison["compatibility"]["sheet1_only_columns"] = list(cols1 - cols2)
            comparison["compatibility"]["sheet2_only_columns"] = list(cols2 - cols1)

            # Add recommendations
            recommendations = []

            if len(comparison["compatibility"]["common_columns"]) < 3:
                recommendations.append(
                    "Sheets have very few common columns - verify sheet selection"
                )

            if comparison["compatibility"]["size_difference"] > 1000:
                recommendations.append("Large size difference between sheets")

            if profile1.duplicate_rows > profile1.total_rows * 0.1:
                recommendations.append(f"Sheet '{sheet1}' has high duplicate rate")

            if profile2.duplicate_rows > profile2.total_rows * 0.1:
                recommendations.append(f"Sheet '{sheet2}' has high duplicate rate")

            comparison["recommendations"] = recommendations

            logger.info(
                "Sheet comparison completed",
                file_id=file_id,
                common_columns=len(comparison["compatibility"]["common_columns"]),
                recommendations=len(recommendations),
            )

            return comparison

        finally:
            excel_reader.close()

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Error during sheet comparison",
            file_id=file_id,
            sheet1=sheet1,
            sheet2=sheet2,
            error=str(e),
        )

        raise HTTPException(
            status_code=500, detail=f"Internal server error during comparison: {str(e)}"
        )
