"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response model for file upload."""

    file_id: str
    filename: str
    sheet_names: List[str]
    file_size: int
    upload_time: datetime


class PreviewRequest(BaseModel):
    """Request model for sheet preview."""

    file_id: str
    sheet: str
    n: int = Field(default=10, ge=1, le=100)


class PreviewResponse(BaseModel):
    """Response model for sheet preview."""

    sheet_name: str
    total_rows: int
    total_cols: int
    columns: List[str]
    head_data: List[Dict[str, Any]]
    tail_data: List[Dict[str, Any]]


class ProfileRequest(BaseModel):
    """Request model for data profiling."""

    file_id: str
    sheet: str


class ColumnProfile(BaseModel):
    """Profile information for a single column."""

    name: str
    dtype: str
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any]


class ProfileResponse(BaseModel):
    """Response model for data profiling."""

    sheet_name: str
    total_rows: int
    total_cols: int
    duplicate_rows: int
    columns: List[ColumnProfile]


class TransformOptions(BaseModel):
    """Options for ETL transformation."""

    date_cols: List[str] = Field(default_factory=list)
    excluded_date_cols: List[str] = Field(default_factory=list)
    id_col: str = Field(default="YAZAKI PN")
    master_sheet_name: Optional[str] = None
    status_sheet_name: Optional[str] = None


class TransformRequest(BaseModel):
    """Request model for ETL transformation."""

    file_id: str
    master_sheet: str
    status_sheet: str
    options: TransformOptions = Field(default_factory=TransformOptions)


class ArtifactInfo(BaseModel):
    """Information about generated artifacts."""

    name: str
    path: str
    format: str
    size_bytes: int
    row_count: Optional[int] = None


class TransformSummary(BaseModel):
    """Summary statistics from ETL transformation."""

    total_parts: int
    active_parts: int
    inactive_parts: int
    new_parts: int
    duplicate_parts: int
    plants_detected: int
    duplicates_removed: int
    date_columns_processed: List[str]
    processing_time_seconds: float


class TransformResponse(BaseModel):
    """Response model for ETL transformation."""

    success: bool
    artifacts: List[ArtifactInfo]
    summary: TransformSummary
    messages: List[Dict[str, Any]]
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str = "1.0.0"


# Status classification for parts
class PartStatus(BaseModel):
    """Part status information."""

    part_id_std: str
    part_id_raw: str
    project_plant: str
    raw_status: Optional[str]
    status_class: str
    is_duplicate: bool
    is_new: bool
    notes: Optional[str] = None


class PlantStats(BaseModel):
    """Statistics for a plant/project."""

    plant_name: str
    n_active: int
    n_inactive: int
    n_new: int
    n_duplicate: int
    total_parts: int
