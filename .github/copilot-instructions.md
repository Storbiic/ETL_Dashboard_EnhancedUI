# ETL Dashboard AI Coding Instructions

## Architecture Overview

This is a **dual-server ETL Dashboard** with FastAPI backend + Flask frontend for auditable Excel-to-PowerBI ETL processing:

- **Backend (`backend/`)**: FastAPI server (port 8000) handling API routes and ETL services
- **Frontend (`frontend/`)**: Flask web app (port 5000/8080) serving UI and proxying API calls
- **Data Flow**: Excel upload → sheet validation → profiling → ETL transformation → multi-format output (CSV/Parquet/SQLite)

## Critical Architectural Patterns

### Dual-Server Communication
- Frontend makes HTTP requests to backend via `FASTAPI_BASE_URL` configuration
- Cross-platform path handling: Docker uses `/app/data/*`, local uses `data/*`
- Environment-aware URL construction in `frontend/app.py` Config class

### Service-Oriented ETL Pipeline
Key service classes in `backend/services/`:
- `PipelineService`: Orchestrates post-ETL automation (file copying, metadata generation)
- `ExcelReader`: Handles Excel file parsing with sheet validation
- `MasterBOMRules`/`StatusRules`: Domain-specific business logic for data transformation
- `PowerBIIntegration`: Generates Power Query M scripts and DAX measures

### Configuration Management
- Pydantic-based settings in `backend/core/config.py` with environment variable fallbacks
- Multi-environment support: local development, Docker, GCP Cloud Run
- Critical environment variables: `FASTAPI_HOST`, `PROCESSED_FOLDER`, `PIPELINE_OUTPUT_FOLDER`

## Essential Developer Workflows

### Development Setup
```bash
# Start both servers with auto-reload
python run_dev.py

# Alternative: Manual dual-terminal setup
# Terminal 1: uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
# Terminal 2: FLASK_APP=frontend.app flask run --host 127.0.0.1 --port 5000
```

### Testing Strategy
- **Unit tests**: `pytest tests/test_*.py -v` (cleaning, profiler, rules)
- **Integration tests**: `pytest tests/test_api_integration.py -v -m integration`
- **Test markers**: Use `-m "not slow"` to skip performance tests
- **Fixtures**: `conftest.py` provides sample Excel data and temp directories

### Docker Development
```bash
# Full stack with networking
docker-compose up --build

# Backend only
docker-compose up backend
```

## Project-Specific Conventions

### File ID Pattern
All operations use UUID-based file tracking:
```python
# Generated on upload, used throughout pipeline
file_id = str(uuid.uuid4())
file_path = settings.uploads_folder_path / f"{file_id}.xlsx"
```

### ETL Schema Assumptions
- **Primary Key**: Default ID column is `"YAZAKI PN"` (configurable)
- **Date Columns**: Auto-detected by pattern matching in column names
- **Sheet Requirements**: Exactly 2 sheets (MasterBOM + Status) must be selected
- **Output Naming**: Follows pattern `{table_name}_clean.{format}` in `data/processed/`

### Error Handling Pattern
All services use structured logging via `ETLLogger`:
```python
from backend.core.logging import ETLLogger
logger = ETLLogger()
logger.info("Operation started", file_id=file_id, extra_context=value)
logger.error("Operation failed", error=str(e), file_id=file_id)
```

### Data Processing Pipeline
1. **Upload** (`routes_upload.py`): File validation, UUID assignment, sheet enumeration
2. **Preview** (`routes_preview.py`): Sample data display with head/tail views
3. **Profile** (`routes_profile.py`): Data quality analysis, null counts, type inference
4. **Transform** (`routes_transform.py`): ETL execution via service classes
5. **Pipeline** (`PipelineService`): Auto-copy to output folder, metadata generation

## Integration Points

### Power BI Automation
- Auto-generates `.pqx` Power Query files in `powerbi/` folder
- Creates DAX measures for calculated columns
- Produces data dictionary with column mappings

### Cross-Platform File Handling
Critical pattern for Docker vs local paths:
```python
# In frontend/app.py
if os.getenv("PROCESSED_FOLDER", "").startswith("/app/"):
    # Docker environment
    PROCESSED_FOLDER = Path(os.getenv("PROCESSED_FOLDER"))
else:
    # Local development
    PROCESSED_FOLDER = PROJECT_ROOT / "data/processed"
```

### API Request/Response Models
All API endpoints use Pydantic schemas from `backend/models/schemas.py`:
- `TransformRequest`: ETL job configuration
- `ArtifactInfo`: Generated file metadata
- `ColumnProfile`: Data profiling results

## Key File Locations

- **API Routes**: `backend/api/routes_*.py` (upload, preview, profile, transform)
- **Business Logic**: `backend/services/` (all ETL processing logic)
- **Configuration**: `backend/core/config.py` (environment-aware settings)
- **Data Outputs**: `data/processed/` (user downloads), `data/pipeline_output/` (Power BI ready)
- **Frontend Templates**: `frontend/templates/` (Jinja2), `frontend/static/` (CSS/JS)

When modifying ETL logic, always update corresponding tests in `tests/` and ensure both CSV and Parquet outputs are generated.