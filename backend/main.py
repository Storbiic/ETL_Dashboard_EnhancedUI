"""FastAPI main application for ETL Dashboard."""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import routes_preview, routes_profile, routes_transform, routes_upload
from backend.core.config import settings
from backend.core.logging import logger
from backend.models.schemas import ErrorResponse, HealthResponse

# Create FastAPI application
app = FastAPI(
    title="ETL Dashboard API",
    description="FastAPI backend for Excel ETL processing with Power BI outputs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error("Unhandled exception", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=(
                str(exc) if settings.fastapi_reload else "An unexpected error occurred"
            ),
        ).dict(),
    )


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic health check."""
    return HealthResponse(status="healthy", timestamp=datetime.now())


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint."""
    # Check if required directories exist
    upload_dir = settings.upload_folder_path
    processed_dir = settings.processed_folder_path

    if not upload_dir.exists():
        raise HTTPException(
            status_code=503, detail=f"Upload directory not found: {upload_dir}"
        )

    if not processed_dir.exists():
        raise HTTPException(
            status_code=503, detail=f"Processed directory not found: {processed_dir}"
        )

    return HealthResponse(status="healthy", timestamp=datetime.now())


@app.get("/api/debug/paths")
async def debug_paths():
    """Debug endpoint to check path configuration."""
    return {
        "upload_folder": str(settings.upload_folder_path),
        "processed_folder": str(settings.processed_folder_path), 
        "pipeline_output_folder": str(settings.pipeline_output_folder_path),
        "paths_exist": {
            "upload": settings.upload_folder_path.exists(),
            "processed": settings.processed_folder_path.exists(),
            "pipeline_output": settings.pipeline_output_folder_path.exists(),
        },
        "environment_vars": {
            "UPLOAD_FOLDER": settings.upload_folder,
            "PROCESSED_FOLDER": settings.processed_folder,
            "PIPELINE_OUTPUT_FOLDER": settings.pipeline_output_folder,
        },
        "working_directory": str(Path.cwd()),
    }


# Include API routers
app.include_router(routes_upload.router, prefix="/api", tags=["upload"])

app.include_router(routes_preview.router, prefix="/api", tags=["preview"])

app.include_router(routes_profile.router, prefix="/api", tags=["profile"])

app.include_router(routes_transform.router, prefix="/api", tags=["transform"])


@app.get("/api/logs/recent")
async def get_recent_logs():
    """Get recent log entries for monitoring."""
    import json
    import os
    from datetime import datetime

    try:
        logs = []
        log_file = os.path.join(os.path.dirname(__file__), "..", "logs", "etl.log")

        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                lines = f.readlines()
                # Get last 50 lines
                recent_lines = lines[-50:] if len(lines) > 50 else lines

                for line in recent_lines:
                    if line.strip():
                        try:
                            # Try to parse as JSON log
                            log_data = json.loads(line.strip())
                            logs.append(log_data)
                        except json.JSONDecodeError:
                            # Plain text log
                            logs.append(
                                {
                                    "message": line.strip(),
                                    "timestamp": datetime.now().isoformat(),
                                    "level": "info",
                                }
                            )

        return {"logs": logs, "count": len(logs)}

    except Exception as e:
        return {"error": f"Failed to read logs: {str(e)}", "logs": [], "count": 0}


@app.get("/api/progress/status")
async def get_progress_status():
    """Get current ETL progress status."""
    import json
    import os
    from datetime import datetime, timedelta

    try:
        # Read recent logs to determine current status
        log_file = os.path.join(os.path.dirname(__file__), "..", "logs", "etl.log")

        if not os.path.exists(log_file):
            return {
                "progress": 0,
                "status": "idle",
                "operation": "System Ready",
                "description": "Waiting for ETL operations...",
                "last_activity": None,
            }

        # Get recent logs (last 5 minutes)
        recent_logs = []
        cutoff_time = datetime.now() - timedelta(minutes=5)

        with open(log_file, "r") as f:
            lines = f.readlines()
            recent_lines = lines[-20:] if len(lines) > 20 else lines

            for line in recent_lines:
                if line.strip():
                    try:
                        log_data = json.loads(line.strip())
                        log_time = datetime.fromisoformat(
                            log_data.get("timestamp", "").replace("Z", "+00:00")
                        )
                        if log_time > cutoff_time:
                            recent_logs.append(log_data)
                    except (json.JSONDecodeError, ValueError):
                        continue

        # Analyze logs to determine current status
        progress = 0
        status = "idle"
        operation = "System Ready"
        description = "Waiting for ETL operations..."
        last_activity = None

        if recent_logs:
            latest_log = recent_logs[-1]
            last_activity = latest_log.get("timestamp")

            # Check for errors
            has_error = any(
                (log.get("level") or log.get("severity") or "").upper() == "ERROR"
                for log in recent_logs
            )

            if has_error:
                status = "error"
                operation = "Error Occurred"
                description = (
                    "An error occurred during processing. Check logs for details."
                )
                progress = 0
            else:
                # Determine progress based on recent log messages
                for log in reversed(recent_logs):
                    message = (log.get("message") or log.get("event") or "").lower()

                    if "file uploaded" in message:
                        progress = 10
                        status = "upload"
                        operation = "File Upload"
                        description = "Excel file uploaded successfully"
                        break
                    elif "reading excel" in message or (
                        "found" in message and "sheets" in message
                    ):
                        progress = 20
                        status = "reading"
                        operation = "Reading Sheets"
                        description = "Loading Excel sheets..."
                        break
                    elif (
                        "masterbom processing" in message
                        or "processing masterbom" in message
                    ):
                        progress = 40
                        status = "masterbom_processing"
                        operation = "Processing MasterBOM"
                        description = "Cleaning and transforming master data..."
                        break
                    elif (
                        "status sheet processing" in message
                        or "processing status" in message
                    ):
                        progress = 70
                        status = "status_processing"
                        operation = "Processing Status"
                        description = "Processing status sheet data..."
                        break
                    elif "etl transformation" in message:
                        progress = 85
                        status = "transformation"
                        operation = "ETL Transformation"
                        description = "Applying business rules and transformations..."
                        break
                    elif "complete" in message and (
                        "processing" in message or "transformation" in message
                    ):
                        progress = 100
                        status = "complete"
                        operation = "Complete"
                        description = "ETL process completed successfully!"
                        break

        return {
            "progress": progress,
            "status": status,
            "operation": operation,
            "description": description,
            "last_activity": last_activity,
            "recent_logs_count": len(recent_logs),
        }

    except Exception as e:
        return {
            "progress": 0,
            "status": "error",
            "operation": "System Error",
            "description": f"Failed to get progress status: {str(e)}",
            "last_activity": None,
        }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting ETL Dashboard API", version="1.0.0")

    # Ensure required directories exist
    settings.upload_folder_path.mkdir(parents=True, exist_ok=True)
    settings.processed_folder_path.mkdir(parents=True, exist_ok=True)

    logger.info("ETL Dashboard API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down ETL Dashboard API")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.fastapi_reload,
        log_level=settings.log_level.lower(),
    )
