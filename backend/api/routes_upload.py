"""Upload API routes for file handling."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.logging import logger
from backend.models.schemas import ErrorResponse, UploadResponse
from backend.services.excel_reader import ExcelReader

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload an Excel workbook and return file info with sheet names.

    Args:
        file: Uploaded Excel file

    Returns:
        UploadResponse with file_id, filename, sheet_names, etc.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=400, detail="Only Excel files (.xlsx, .xls) are supported"
            )

        # Check file size
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_upload_size}",
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Save file to uploads directory
        upload_path = settings.upload_folder_path / f"{file_id}.xlsx"

        with open(upload_path, "wb") as f:
            f.write(file_content)

        logger.info(
            "File uploaded successfully",
            file_id=file_id,
            filename=file.filename,
            size_bytes=file_size,
        )

        # Read sheet names using ExcelReader
        try:
            excel_reader = ExcelReader(upload_path)
            sheet_names = excel_reader.get_sheet_names()
            excel_reader.close()

        except Exception as e:
            # Clean up uploaded file if Excel reading fails
            if upload_path.exists():
                upload_path.unlink()

            logger.error("Failed to read Excel file", file_id=file_id, error=str(e))

            raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")

        # Validate minimum requirements
        if len(sheet_names) < 2:
            # Clean up uploaded file
            if upload_path.exists():
                upload_path.unlink()

            raise HTTPException(
                status_code=400, detail="Excel file must contain at least 2 sheets"
            )

        # Auto-detect MasterBOM and Status sheets
        detected_sheets = _auto_detect_sheets(sheet_names)

        logger.info(
            "Excel file processed successfully",
            file_id=file_id,
            sheet_count=len(sheet_names),
            sheets=sheet_names,
            detected_sheets=detected_sheets,
        )

        # Create enhanced response with detected sheets
        response_data = UploadResponse(
            file_id=file_id,
            filename=file.filename,
            sheet_names=sheet_names,
            file_size=file_size,
            upload_time=datetime.now(),
        )

        # Add detected sheets to response
        response_dict = response_data.model_dump()
        response_dict["detected_sheets"] = detected_sheets

        return response_dict

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error("Unexpected error during file upload", error=str(e))

        raise HTTPException(
            status_code=500, detail="Internal server error during file upload"
        )


@router.delete("/upload/{file_id}")
async def delete_uploaded_file(file_id: str):
    """
    Delete an uploaded file.

    Args:
        file_id: ID of the file to delete

    Returns:
        Success message
    """
    try:
        # Validate file_id format
        try:
            uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        # Find and delete file
        upload_path = settings.upload_folder_path / f"{file_id}.xlsx"

        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        upload_path.unlink()

        logger.info("File deleted successfully", file_id=file_id)

        return {"message": "File deleted successfully", "file_id": file_id}

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Error deleting file", file_id=file_id, error=str(e))

        raise HTTPException(
            status_code=500, detail="Internal server error during file deletion"
        )


@router.get("/upload/{file_id}/info")
async def get_file_info(file_id: str):
    """
    Get information about an uploaded file.

    Args:
        file_id: ID of the uploaded file

    Returns:
        File information including sheet names
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

        # Get file info
        file_stat = upload_path.stat()

        # Read sheet names
        excel_reader = ExcelReader(upload_path)
        sheet_names = excel_reader.get_sheet_names()
        excel_reader.close()

        return {
            "file_id": file_id,
            "file_size": file_stat.st_size,
            "upload_time": datetime.fromtimestamp(file_stat.st_ctime),
            "sheet_names": sheet_names,
            "sheet_count": len(sheet_names),
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Error getting file info", file_id=file_id, error=str(e))

        raise HTTPException(
            status_code=500, detail="Internal server error getting file info"
        )


def _auto_detect_sheets(sheet_names: list[str]) -> dict:
    """
    Auto-detect MasterBOM and Status sheets from available sheet names.

    Args:
        sheet_names: List of available sheet names

    Returns:
        Dictionary with detected sheet mappings and confidence scores
    """
    detected = {"masterbom": None, "status": None, "confidence": {}, "suggestions": []}

    # Define detection patterns with confidence scores
    masterbom_patterns = [
        ("masterbom", 1.0),
        ("master_bom", 0.9),
        ("master bom", 0.9),
        ("bom", 0.7),
        ("bill of materials", 0.8),
        ("parts", 0.6),
        ("components", 0.5),
        ("items", 0.4),
    ]

    status_patterns = [
        ("status", 1.0),
        ("project status", 0.9),
        ("plant status", 0.9),
        ("summary", 0.6),
        ("overview", 0.5),
        ("dashboard", 0.4),
    ]

    # Find best matches for MasterBOM
    best_masterbom_score = 0
    masterbom_candidates = []

    for sheet in sheet_names:
        sheet_lower = sheet.lower().strip()
        max_score = 0

        for pattern, score in masterbom_patterns:
            if pattern in sheet_lower:
                max_score = max(max_score, score)

        if max_score > 0:
            masterbom_candidates.append((sheet, max_score))
            if max_score > best_masterbom_score:
                detected["masterbom"] = sheet
                detected["confidence"]["masterbom"] = max_score
                best_masterbom_score = max_score

    # Find best matches for Status
    best_status_score = 0
    status_candidates = []

    for sheet in sheet_names:
        sheet_lower = sheet.lower().strip()
        max_score = 0

        for pattern, score in status_patterns:
            if pattern in sheet_lower:
                max_score = max(max_score, score)

        if max_score > 0:
            status_candidates.append((sheet, max_score))
            if max_score > best_status_score:
                detected["status"] = sheet
                detected["confidence"]["status"] = max_score
                best_status_score = max_score

    # Add suggestions for manual selection
    detected["suggestions"] = {
        "masterbom_candidates": sorted(
            masterbom_candidates, key=lambda x: x[1], reverse=True
        ),
        "status_candidates": sorted(
            status_candidates, key=lambda x: x[1], reverse=True
        ),
    }

    logger.info(
        "Auto-detection completed",
        masterbom_detected=detected["masterbom"],
        status_detected=detected["status"],
        masterbom_confidence=detected["confidence"].get("masterbom", 0),
        status_confidence=detected["confidence"].get("status", 0),
    )

    return detected
