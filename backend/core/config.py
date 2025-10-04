"""Configuration management for the ETL Dashboard application."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # FastAPI Configuration
    fastapi_host: str = Field(default="127.0.0.1", alias="FASTAPI_HOST")
    fastapi_port: int = Field(default=8000, alias="FASTAPI_PORT")
    fastapi_reload: bool = Field(default=True, alias="FASTAPI_RELOAD")

    # Flask Configuration
    flask_host: str = Field(default="127.0.0.1", alias="FLASK_HOST")
    flask_port: int = Field(default=5000, alias="FLASK_PORT")
    flask_debug: bool = Field(default=True, alias="FLASK_DEBUG")
    flask_secret_key: str = Field(default="dev-secret-key", alias="FLASK_SECRET_KEY")

    # File Upload Configuration
    max_upload_size: str = Field(default="50MB", alias="MAX_UPLOAD_SIZE")
    upload_folder: str = Field(default="data/uploads", alias="UPLOAD_FOLDER")
    processed_folder: str = Field(default="data/processed", alias="PROCESSED_FOLDER")

    # Pipeline Configuration
    pipeline_output_folder: str = Field(
        default="data/pipeline_output", alias="PIPELINE_OUTPUT_FOLDER"
    )
    powerbi_templates_folder: str = Field(
        default="powerbi/templates", alias="POWERBI_TEMPLATES_FOLDER"
    )
    auto_copy_to_pipeline: bool = Field(default=True, alias="AUTO_COPY_TO_PIPELINE")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///data/processed/etl.sqlite", alias="DATABASE_URL"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # ETL Configuration
    default_id_column: str = Field(default="YAZAKI PN", alias="DEFAULT_ID_COLUMN")
    max_preview_rows: int = Field(default=10, alias="MAX_PREVIEW_ROWS")
    chunk_size: int = Field(default=10000, alias="CHUNK_SIZE")
    enable_performance_optimizations: bool = Field(
        default=True, alias="ENABLE_PERFORMANCE_OPTIMIZATIONS"
    )
    large_dataset_threshold: int = Field(default=50000, alias="LARGE_DATASET_THRESHOLD")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def upload_folder_path(self) -> Path:
        """Get upload folder as Path object."""
        return Path(self.upload_folder)

    @property
    def processed_folder_path(self) -> Path:
        """Get processed folder as Path object."""
        return Path(self.processed_folder)

    @property
    def pipeline_output_folder_path(self) -> Path:
        """Get pipeline output folder as Path object."""
        return Path(self.pipeline_output_folder)

    @property
    def powerbi_templates_folder_path(self) -> Path:
        """Get PowerBI templates folder as Path object."""
        return Path(self.powerbi_templates_folder)

    @property
    def max_upload_bytes(self) -> int:
        """Convert max upload size to bytes."""
        size_str = self.max_upload_size.upper()
        if size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.upload_folder_path.mkdir(parents=True, exist_ok=True)
settings.processed_folder_path.mkdir(parents=True, exist_ok=True)
