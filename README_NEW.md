# 🔄 ETL Dashboard - Enhanced UI

A modern, dual-server ETL (Extract, Transform, Load) dashboard for auditable Excel-to-Power BI data processing with comprehensive data profiling and transformation capabilities.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#️-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Running the Application](#-running-the-application)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

### 🎯 Core Capabilities
- **📤 Excel Upload & Validation** - Upload multi-sheet Excel workbooks with real-time validation
- **🔍 Data Profiling** - Comprehensive data quality analysis with statistics, null counts, and type inference
- **🧹 ETL Processing** - Business-rule-driven data cleaning and transformation
- **💾 Multi-Format Output** - Export to CSV, Parquet, and SQLite formats
- **📊 Power BI Integration** - Auto-generated Power Query M scripts and DAX measures
- **📈 Progress Tracking** - Real-time pipeline progress with visual feedback
- **📝 Audit Logging** - Complete processing logs for compliance and debugging

### 🚀 Advanced Features
- Dual-server architecture (FastAPI backend + Flask frontend)
- Domain-specific business rules for MasterBOM and Status sheets
- Automatic data dictionary generation
- Cross-platform path handling (Docker & local development)
- Environment-aware configuration management
- Comprehensive test suite with integration tests

---

## 🏗️ Architecture

```
┌─────────────────┐      HTTP/REST      ┌──────────────────┐
│  Flask Frontend │ ◄─────────────────► │ FastAPI Backend  │
│   (Port 5000)   │                     │   (Port 8000)    │
└─────────────────┘                     └──────────────────┘
        │                                        │
        │                                        │
        ▼                                        ▼
┌─────────────────────────────────────────────────────────┐
│               Data Pipeline Services                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐           │
│  │  Excel   │→ │ Profiler │→ │ ETL Rules  │→ Outputs │
│  │  Reader  │  │          │  │ Processor  │           │
│  └──────────┘  └──────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Backend (FastAPI)**: API routes, ETL services, business logic
- **Frontend (Flask)**: Web UI, user interaction, API proxy
- **Services Layer**: Modular ETL processing (reader, profiler, cleaners, rules)
- **Data Flow**: Upload → Validation → Profiling → Transformation → Output

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** 0.104+ - High-performance API framework
- **[Pandas](https://pandas.pydata.org/)** 2.1+ - Data manipulation and analysis
- **[Pydantic](https://pydantic.dev/)** 2.5+ - Data validation and settings
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server

### Frontend
- **[Flask](https://flask.palletsprojects.com/)** 3.0+ - Web framework
- **Jinja2** - Template engine
- **Bootstrap 5** - UI components
- **Vanilla JavaScript** - Interactive features

### Data Processing
- **openpyxl** - Excel file parsing
- **pyarrow** - Parquet format support
- **sqlite3** - SQLite database generation

### Development & Deployment
- **pytest** - Testing framework
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **GCP Cloud Run** - Production deployment

---

## 📦 Prerequisites

### Required
- **Python** 3.11 or higher
- **pip** (Python package manager)
- **Git** for version control

### Optional (for development)
- **Docker** & **Docker Compose** (for containerized development)
- **Conda** (alternative to venv)
- **VS Code** (recommended IDE)

### System Requirements
- **RAM**: 4GB minimum (8GB recommended for large files)
- **Disk**: 500MB for application + space for data files
- **OS**: Windows, macOS, or Linux

---

## 🚀 Installation

### Option 1: Local Development (Recommended for Development)

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ETL_Dashboard_EnhancedUI.git
cd ETL_Dashboard_EnhancedUI
```

#### 2. Create Virtual Environment

**Using venv (Built-in):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**Using Conda:**
```bash
conda create -n etl_dashboard python=3.11 -y
conda activate etl_dashboard
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Create Data Directories
```bash
# Windows
mkdir data\uploads data\processed data\pipeline_output

# macOS/Linux
mkdir -p data/uploads data/processed data/pipeline_output
```

---

### Option 2: Docker Development

#### 1. Build and Run with Docker Compose
```bash
# Start both backend and frontend services
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

#### 2. Access the Application
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## ⚙️ Configuration

### 1. Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

### 2. Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FASTAPI_HOST` | Backend API URL | `http://127.0.0.1:8000` | Yes |
| `FLASK_ENV` | Flask environment | `development` | No |
| `PYTHONPATH` | Python module path | `/app` | Docker only |
| `UPLOADS_FOLDER` | Upload directory | `data/uploads` | Yes |
| `PROCESSED_FOLDER` | Output directory | `data/processed` | Yes |
| `PIPELINE_OUTPUT_FOLDER` | Power BI ready outputs | `data/pipeline_output` | Yes |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### 3. Example .env File

**For Local Development:**
```env
# Backend Configuration
FASTAPI_HOST=http://127.0.0.1:8000

# Flask Configuration
FLASK_ENV=development
FLASK_APP=frontend.app

# Paths (Local)
UPLOADS_FOLDER=data/uploads
PROCESSED_FOLDER=data/processed
PIPELINE_OUTPUT_FOLDER=data/pipeline_output

# Logging
LOG_LEVEL=INFO
```

**For Docker:**
```env
# Backend Configuration
FASTAPI_HOST=http://backend:8000

# Flask Configuration
FLASK_ENV=production
PYTHONPATH=/app

# Paths (Docker)
UPLOADS_FOLDER=/app/data/uploads
PROCESSED_FOLDER=/app/data/processed
PIPELINE_OUTPUT_FOLDER=/app/data/pipeline_output

# Logging
LOG_LEVEL=INFO
```

---

## 🏃 Running the Application

### Development Mode (Both Servers)

**Quick Start:**
```bash
python run_dev.py
```

This script automatically:
1. Starts FastAPI backend on port 8000
2. Starts Flask frontend on port 5000
3. Opens your browser to http://localhost:5000

**Manual Start (Separate Terminals):**

**Terminal 1 - Backend:**
```bash
cd ETL_Dashboard_EnhancedUI
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd ETL_Dashboard_EnhancedUI
set FLASK_APP=frontend.app
flask run --host 127.0.0.1 --port 5000
```

---

### Docker Mode

```bash
# Start services
docker-compose up

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

### Production Mode

See [Deployment Documentation](docs/deployment/gcp.md) for production deployment instructions.

---

## 📖 Usage Guide

### 1. Upload Excel File
1. Navigate to http://localhost:5000
2. Click "Upload Excel File" or drag & drop
3. Select your Excel workbook
4. Wait for upload confirmation

### 2. Select Sheets
1. Review detected sheets
2. Select exactly 2 sheets:
   - **MasterBOM Sheet** (product/parts data)
   - **Status Sheet** (plant/status data)
3. Click "Next"

### 3. Preview Data
1. Review data samples (head/tail views)
2. Verify column names and data types
3. Click "Profile Data" to continue

### 4. Data Profiling
1. Review data quality metrics:
   - Null counts per column
   - Data type distributions
   - Unique value counts
   - Statistical summaries
2. Identify potential issues
3. Click "Transform Data"

### 5. ETL Processing
1. Configure transformation settings:
   - Select primary key column (default: "YAZAKI PN")
   - Choose output formats (CSV/Parquet/SQLite)
2. Click "Start ETL"
3. Monitor real-time progress

### 6. Download Results
1. Review transformation summary
2. Download output files:
   - **Cleaned data** (CSV/Parquet)
   - **Power BI connectors** (.pqx files)
   - **DAX measures** (measures_dax.md)
   - **Data dictionary** (data_dictionary.md)

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Upload
```http
POST /api/v1/upload
Content-Type: multipart/form-data

Body:
- file: Excel file (.xlsx)

Response: {
  "file_id": "uuid-string",
  "sheets": ["Sheet1", "Sheet2"],
  "message": "File uploaded successfully"
}
```

#### Preview
```http
POST /api/v1/preview
Content-Type: application/json

Body: {
  "file_id": "uuid-string",
  "sheet_names": ["MasterBOM", "Status"]
}

Response: {
  "previews": {
    "MasterBOM": { "head": [...], "tail": [...] },
    "Status": { "head": [...], "tail": [...] }
  }
}
```

#### Profile
```http
POST /api/v1/profile
Content-Type: application/json

Body: {
  "file_id": "uuid-string",
  "sheet_names": ["MasterBOM", "Status"]
}

Response: {
  "profiles": {
    "MasterBOM": { "columns": [...], "stats": {...} },
    "Status": { "columns": [...], "stats": {...} }
  }
}
```

#### Transform (ETL)
```http
POST /api/v1/transform
Content-Type: application/json

Body: {
  "file_id": "uuid-string",
  "sheet_names": ["MasterBOM", "Status"],
  "output_formats": ["csv", "parquet"],
  "primary_key": "YAZAKI PN"
}

Response: {
  "success": true,
  "artifacts": [
    { "name": "masterbom_clean.csv", "path": "..." },
    { "name": "status_clean.parquet", "path": "..." }
  ]
}
```

---

## 📁 Project Structure

```
ETL_Dashboard_EnhancedUI/
├── backend/                    # FastAPI backend application
│   ├── api/                    # API route handlers
│   │   ├── routes_upload.py    # File upload endpoint
│   │   ├── routes_preview.py   # Data preview endpoint
│   │   ├── routes_profile.py   # Data profiling endpoint
│   │   └── routes_transform.py # ETL transformation endpoint
│   ├── core/                   # Core configurations
│   │   ├── config.py           # Environment-aware settings
│   │   ├── logging.py          # ETL logger setup
│   │   └── performance.py      # Performance monitoring
│   ├── models/                 # Pydantic schemas
│   │   └── schemas.py          # API request/response models
│   ├── services/               # Business logic layer
│   │   ├── cleaning.py         # Data cleaning utilities
│   │   ├── excel_reader.py     # Excel file parsing
│   │   ├── profiler.py         # Data profiling engine
│   │   ├── masterbom_rules.py  # MasterBOM transformation rules
│   │   ├── status_rules.py     # Status transformation rules
│   │   ├── pipeline_service.py # Post-ETL automation
│   │   ├── powerbi_integration.py # Power BI artifact generation
│   │   └── storage.py          # File management
│   └── main.py                 # FastAPI application entry point
│
├── frontend/                   # Flask frontend application
│   ├── static/                 # Static assets
│   │   ├── css/                # Stylesheets
│   │   └── js/                 # JavaScript files
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html           # Base template
│   │   ├── index.html          # Landing page
│   │   ├── upload.html         # Upload interface
│   │   ├── preview.html        # Data preview
│   │   ├── profile.html        # Profiling results
│   │   ├── transform.html      # ETL configuration
│   │   └── results.html        # Download page
│   └── app.py                  # Flask application entry point
│
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures
│   ├── test_cleaning.py        # Cleaning tests
│   ├── test_profiler.py        # Profiler tests
│   ├── test_masterbom_rules.py # MasterBOM rules tests
│   └── test_api_integration.py # Integration tests
│
├── data/                       # Data directories (gitignored)
│   ├── uploads/                # Uploaded Excel files
│   ├── processed/              # User download outputs
│   └── pipeline_output/        # Power BI ready outputs
│
├── powerbi/                    # Power BI artifacts
│   ├── power_query_connectors.md
│   ├── measures_dax.md
│   └── data_dictionary.md
│
├── docs/                       # Documentation
│   └── deployment/             # Deployment guides
│
├── scripts/                    # Utility scripts
│   └── deployment/             # Deployment scripts
│
├── docker-compose.yml          # Local development orchestration
├── docker-compose.prod.yml     # Production orchestration
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── run_dev.py                  # Development server launcher
└── README.md                   # This file
```

---

## 🚀 Deployment

### Docker Deployment

**1. Build Images:**
```bash
docker-compose -f docker-compose.prod.yml build
```

**2. Run in Production:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Google Cloud Platform (GCP)

**Prerequisites:**
- GCP account with billing enabled
- gcloud CLI installed and configured

**Deploy to Cloud Run:**
```bash
# Make script executable (Linux/Mac)
chmod +x deploy-gcp.sh

# Run deployment
./deploy-gcp.sh
```

**Manual GCP Deployment:**
See [GCP Deployment Guide](docs/deployment/gcp.md)

### Other Platforms

- **AWS**: See [AWS Deployment Guide](docs/deployment/aws.md)
- **Azure**: See [Azure Deployment Guide](docs/deployment/azure.md)
- **Heroku**: See [Heroku Deployment Guide](docs/deployment/heroku.md)

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/test_cleaning.py tests/test_profiler.py -v

# Integration tests
pytest tests/test_api_integration.py -v -m integration

# Skip slow tests
pytest tests/ -v -m "not slow"
```

### Test with Coverage
```bash
pytest tests/ --cov=backend --cov-report=html
```

View coverage report: `htmlcov/index.html`

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Run tests (`pytest tests/`)
5. Format code (`black . && isort .`)
6. Commit changes (`git commit -m 'Add AmazingFeature'`)
7. Push to branch (`git push origin feature/AmazingFeature`)
8. Open a Pull Request

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Module not found" errors
```bash
# Ensure virtual environment is activated
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Port already in use
```bash
# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

#### 3. Docker permission errors
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

#### 4. FastAPI backend not accessible from frontend
- Verify `FASTAPI_HOST` in `.env` matches backend URL
- Check backend is running: `curl http://localhost:8000/health`
- Review CORS settings in `backend/main.py`

#### 5. Excel file upload fails
- Ensure file is `.xlsx` format (not `.xls`)
- Check file size < 100MB
- Verify `data/uploads/` directory exists and is writable

### Getting Help

- 📖 Check [Documentation](docs/)
- 🐛 Report bugs via [GitHub Issues](https://github.com/yourusername/ETL_Dashboard_EnhancedUI/issues)
- 💬 Ask questions in [Discussions](https://github.com/yourusername/ETL_Dashboard_EnhancedUI/discussions)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [@yourusername](https://github.com/yourusername)

See also the list of [contributors](https://github.com/yourusername/ETL_Dashboard_EnhancedUI/contributors) who participated in this project.

---

## 🙏 Acknowledgments

- **FastAPI** for the amazing API framework
- **Flask** for the web framework
- **Pandas** for data manipulation capabilities
- All open-source contributors

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/ETL_Dashboard_EnhancedUI?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/ETL_Dashboard_EnhancedUI?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/ETL_Dashboard_EnhancedUI)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/ETL_Dashboard_EnhancedUI)

---

**Made with ❤️ for better ETL workflows**
