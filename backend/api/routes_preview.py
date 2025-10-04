"""Preview API routes for sheet data preview."""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from backend.core.config import settings
from backend.core.logging import logger
from backend.models.schemas import PreviewResponse
from backend.services.excel_reader import ExcelReader

router = APIRouter()


@router.get("/preview", response_model=PreviewResponse)
async def preview_sheet(
    file_id: str = Query(..., description="File ID from upload"),
    sheet: str = Query(..., description="Sheet name to preview"),
    n: int = Query(
        default=10, ge=1, le=100, description="Number of rows for head/tail"
    ),
):
    """
    Preview a sheet with head and tail samples.

    Args:
        file_id: ID of the uploaded file
        sheet: Name of the sheet to preview
        n: Number of rows to show in head/tail (1-100)

    Returns:
        PreviewResponse with sheet data samples
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
            "Starting sheet preview", file_id=file_id, sheet=sheet, preview_rows=n
        )

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

            # Get preview data
            preview_data = excel_reader.preview_sheet(sheet, n)

            logger.info(
                "Sheet preview completed",
                file_id=file_id,
                sheet=sheet,
                total_rows=preview_data["total_rows"],
                total_cols=preview_data["total_cols"],
            )

            return PreviewResponse(**preview_data)

        finally:
            excel_reader.close()

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Error during sheet preview", file_id=file_id, sheet=sheet, error=str(e)
        )

        raise HTTPException(
            status_code=500, detail=f"Internal server error during preview: {str(e)}"
        )


@router.get("/preview/{file_id}/sheets")
async def list_sheets(file_id: str):
    """
    List all available sheets in the uploaded file.

    Args:
        file_id: ID of the uploaded file

    Returns:
        List of sheet names with basic info
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

        # Create Excel reader
        excel_reader = ExcelReader(upload_path)

        try:
            # Get sheet names
            sheet_names = excel_reader.get_sheet_names()

            # Get basic info for each sheet
            sheets_info = []
            for sheet_name in sheet_names:
                try:
                    sheet_info = excel_reader.get_sheet_info(sheet_name)
                    sheets_info.append(sheet_info)
                except Exception as e:
                    logger.warning(f"Failed to get info for sheet '{sheet_name}': {e}")
                    sheets_info.append(
                        {
                            "name": sheet_name,
                            "total_rows": 0,
                            "total_cols": 0,
                            "columns": [],
                            "error": str(e),
                        }
                    )

            logger.info("Listed sheets", file_id=file_id, sheet_count=len(sheets_info))

            return {
                "file_id": file_id,
                "sheet_count": len(sheets_info),
                "sheets": sheets_info,
            }

        finally:
            excel_reader.close()

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Error listing sheets", file_id=file_id, error=str(e))

        raise HTTPException(
            status_code=500, detail=f"Internal server error listing sheets: {str(e)}"
        )


@router.get("/preview/{file_id}/{sheet}/columns")
async def get_sheet_columns(file_id: str, sheet: str):
    """
    Get column information for a specific sheet.

    Args:
        file_id: ID of the uploaded file
        sheet: Name of the sheet

    Returns:
        Column information including names and sample data
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

        # Create Excel reader
        excel_reader = ExcelReader(upload_path)

        try:
            # Check if sheet exists
            available_sheets = excel_reader.get_sheet_names()
            if sheet not in available_sheets:
                raise HTTPException(
                    status_code=400, detail=f"Sheet '{sheet}' not found"
                )

            # Read sheet header and sample data
            df = excel_reader.read_sheet(sheet, nrows=5)  # Just first 5 rows

            columns_info = []
            for col in df.columns:
                # Get sample values (non-null)
                sample_values = df[col].dropna().head(3).tolist()

                columns_info.append(
                    {
                        "name": str(col),
                        "index": df.columns.get_loc(col),
                        "sample_values": [str(val) for val in sample_values],
                    }
                )

            logger.info(
                "Retrieved column info",
                file_id=file_id,
                sheet=sheet,
                column_count=len(columns_info),
            )

            return {
                "file_id": file_id,
                "sheet": sheet,
                "column_count": len(columns_info),
                "columns": columns_info,
            }

        finally:
            excel_reader.close()

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Error getting column info", file_id=file_id, sheet=sheet, error=str(e)
        )

        raise HTTPException(
            status_code=500, detail=f"Internal server error getting columns: {str(e)}"
        )
