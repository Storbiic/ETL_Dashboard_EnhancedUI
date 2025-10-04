"""Flask frontend application for ETL Dashboard."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file, session

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")


# Configuration for different deployment environments
class Config:
    # Check if we're in GCP Cloud Run (FASTAPI_HOST will be the full backend URL)
    fastapi_host = os.getenv('FASTAPI_HOST', '127.0.0.1')
    fastapi_port = os.getenv('FASTAPI_PORT', '8000')
    
    # If FASTAPI_HOST is a full URL (starts with http), use it directly
    if fastapi_host.startswith('http'):
        FASTAPI_BASE_URL = fastapi_host
        FASTAPI_BROWSER_URL = fastapi_host
    else:
        # For Docker/local, construct URLs
        FASTAPI_BASE_URL = f"http://{fastapi_host}:{fastapi_port}"
        # Always use localhost for browser requests (not docker service names)
        FASTAPI_BROWSER_URL = f"http://localhost:{fastapi_port}"

    PORT = int(os.getenv("PORT", 8080))  # Changed default from 5000 to 8080 for GCP Cloud Run
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"


# Apply configuration
FASTAPI_BASE_URL = Config.FASTAPI_BASE_URL
FASTAPI_BROWSER_URL = Config.FASTAPI_BROWSER_URL

# Get the project root directory (parent of frontend directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Use Docker environment variables if available, otherwise fall back to local paths
if os.getenv("PROCESSED_FOLDER") and os.getenv("PROCESSED_FOLDER").startswith("/app/"):
    # Running in Docker - use absolute paths from environment
    PROCESSED_FOLDER = Path(os.getenv("PROCESSED_FOLDER", "/app/data/processed"))
    PIPELINE_OUTPUT_FOLDER = Path(os.getenv("PIPELINE_OUTPUT_FOLDER", "/app/data/pipeline_output"))
else:
    # Running locally - use relative paths
    PROCESSED_FOLDER = PROJECT_ROOT / os.getenv("PROCESSED_FOLDER", "data/processed")
    PIPELINE_OUTPUT_FOLDER = PROJECT_ROOT / os.getenv(
        "PIPELINE_OUTPUT_FOLDER", "data/pipeline_output"
    )


def ensure_directory_exists(directory_path):
    """Ensure directory exists with proper cross-platform handling."""
    try:
        directory_path = Path(directory_path)
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False


def find_parquet_files(search_paths):
    """Find parquet files in multiple potential locations."""
    parquet_files = []
    
    for search_path in search_paths:
        try:
            if search_path.exists() and search_path.is_dir():
                files = [f for f in search_path.iterdir() 
                        if f.is_file() and f.suffix.lower() == ".parquet"]
                if files:
                    print(f"Found {len(files)} parquet files in {search_path}")
                    parquet_files.extend(files)
                    break  # Use first location with files
        except Exception as e:
            print(f"Error accessing {search_path}: {e}")
            continue
    
    return parquet_files


@app.context_processor
def inject_progress():
    """Inject progress tracking data into all templates."""
    # Initialize session progress if not exists
    if 'etl_progress' not in session:
        session['etl_progress'] = {
            'current_step': 1,
            'steps': {
                1: {'name': 'Upload File', 'status': 'pending', 'percentage': 0},
                2: {'name': 'Select Sheets', 'status': 'pending', 'percentage': 0},
                3: {'name': 'Preview Data', 'status': 'pending', 'percentage': 0},
                4: {'name': 'Transform Data', 'status': 'pending', 'percentage': 0}
            }
        }
    
    return {
        'etl_progress': session.get('etl_progress', {}),
        'current_step': session.get('etl_progress', {}).get('current_step', 1)
    }


@app.route("/debug/paths")
def debug_paths():
    """Debug endpoint to check path resolution across platforms."""
    import platform
    
    debug_info = {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "current_working_directory": str(Path.cwd()),
        "project_root": str(PROJECT_ROOT),
        "processed_folder": str(PROCESSED_FOLDER),
        "pipeline_output_folder": str(PIPELINE_OUTPUT_FOLDER),
        "environment_variables": {
            "PROCESSED_FOLDER": os.getenv("PROCESSED_FOLDER", "Not set"),
            "PIPELINE_OUTPUT_FOLDER": os.getenv("PIPELINE_OUTPUT_FOLDER", "Not set"),
            "UPLOAD_FOLDER": os.getenv("UPLOAD_FOLDER", "Not set"),
        },
        "path_checks": {}
    }
    
    # Check various paths
    paths_to_check = {
        "processed_folder": PROCESSED_FOLDER,
        "pipeline_output_folder": PIPELINE_OUTPUT_FOLDER,
        "project_root": PROJECT_ROOT,
        "docker_data": Path("/app/data"),
        "docker_processed": Path("/app/data/processed"),
        "docker_pipeline": Path("/app/data/pipeline_output"),
        "relative_data": Path("./data"),
        "relative_processed": Path("./data/processed"),
    }
    
    for name, path in paths_to_check.items():
        try:
            info = {
                "path": str(path),
                "exists": path.exists() if path else False,
                "is_dir": path.is_dir() if path and path.exists() else False,
                "is_absolute": path.is_absolute() if path else False,
            }
            
            if info["exists"] and info["is_dir"]:
                try:
                    files = list(path.iterdir())
                    info["file_count"] = len(files)
                    info["parquet_count"] = len([f for f in files if f.suffix.lower() == ".parquet"])
                    info["files"] = [f.name for f in files[:10]]  # First 10 files
                except Exception as e:
                    info["read_error"] = str(e)
            
            debug_info["path_checks"][name] = info
        except Exception as e:
            debug_info["path_checks"][name] = {"error": str(e)}
    
    return jsonify(debug_info)


@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors."""
    # Return a 204 No Content response to avoid errors
    from flask import Response
    return Response(status=204)


@app.route("/")
def index():
    """Main dashboard page with stepper interface."""
    return render_template(
        "index.html", fastapi_url=Config.FASTAPI_BROWSER_URL, page_title="ETL Dashboard"
    )


@app.route("/preview")
def preview():
    """Preview page for sheet data."""
    file_id = request.args.get("file_id")
    sheet = request.args.get("sheet")

    if not file_id or not sheet:
        return render_template("index.html", error="Missing file_id or sheet parameter")

    return render_template(
        "preview.html",
        file_id=file_id,
        sheet=sheet,
        fastapi_url=Config.FASTAPI_BROWSER_URL,
        page_title="Sheet Preview",
    )


@app.route("/profile")
def profile():
    """Profile page for data quality analysis."""
    file_id = request.args.get("file_id")
    master_sheet = request.args.get("master_sheet")
    status_sheet = request.args.get("status_sheet")

    if not all([file_id, master_sheet, status_sheet]):
        return render_template("index.html", error="Missing required parameters")

    return render_template(
        "profile.html",
        file_id=file_id,
        master_sheet=master_sheet,
        status_sheet=status_sheet,
        fastapi_url=Config.FASTAPI_BROWSER_URL,
        page_title="Data Profile",
    )


@app.route("/results")
def results():
    """Results page showing ETL outputs."""
    file_id = request.args.get("file_id")

    if not file_id:
        return render_template("index.html", error="Missing file_id parameter")

    return render_template(
        "results.html",
        file_id=file_id,
        fastapi_url=Config.FASTAPI_BROWSER_URL,
        page_title="ETL Results",
    )


@app.route("/logs")
def logs():
    """Logs page for monitoring system activity."""
    return render_template(
        "logs.html", fastapi_url=Config.FASTAPI_BROWSER_URL, page_title="System Logs"
    )


@app.route("/api/logs/backend")
def get_backend_logs():
    """Get recent backend logs via API proxy."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/api/logs/recent", timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch backend logs: {str(e)}"}), 500


@app.route("/api/progress/status")
def get_progress_status():
    """Get current ETL progress status via API proxy."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/api/progress/status", timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch progress status: {str(e)}"}), 500


# Pipeline status endpoint removed - manual ETL only


@app.route("/api/powerbi/templates")
def get_powerbi_templates():
    """Get available PowerBI templates via API proxy."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/api/powerbi/templates", timeout=10)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return (
                jsonify(
                    {
                        "templates": [],
                        "count": 0,
                        "error": f"Backend returned status {response.status_code}",
                        "details": response.text,
                    }
                ),
                response.status_code,
            )

    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {
                    "templates": [],
                    "count": 0,
                    "error": f"Failed to fetch PowerBI templates: {str(e)}",
                }
            ),
            500,
        )
    except Exception as e:
        return (
            jsonify(
                {"templates": [], "count": 0, "error": f"Unexpected error: {str(e)}"}
            ),
            500,
        )


@app.route("/download/<filename>")
def download_file(filename):
    """Download processed files."""
    try:
        # Use processed folder only
        file_path = PROCESSED_FOLDER / filename

        if not file_path.exists():
            return jsonify({"error": f"File not found: {filename}"}), 404

        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/bulk/<file_id>")
def download_bulk_files(file_id):
    """Download all files for a specific processing session as a ZIP."""
    import tempfile
    import zipfile
    from datetime import datetime

    try:
        # Create a temporary ZIP file
        temp_dir = tempfile.mkdtemp()
        zip_filename = (
            f"etl_results_{file_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )
        zip_path = Path(temp_dir) / zip_filename

        # Find all files related to this processing session
        files_to_zip = []

        # Check processed folder only
        if PROCESSED_FOLDER.exists():
            for file_path in PROCESSED_FOLDER.iterdir():
                if file_path.is_file():
                    files_to_zip.append((file_path, file_path.name))

        if not files_to_zip:
            return jsonify({"error": "No files found to download"}), 404

        # Create ZIP file
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path, archive_name in files_to_zip:
                zipf.write(file_path, archive_name)

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype="application/zip",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/powerbi/<file_id>")
def download_powerbi_package(file_id):
    """Download organized Power BI package with Parquet files and DAX measures."""
    import tempfile
    import zipfile
    from datetime import datetime

    try:
        # Import DAX generator with error handling
        try:
            from backend.services.dax_generator import DAXGenerator
        except ImportError as e:
            print(f"Warning: Could not import DAXGenerator: {e}")
            # Continue without DAX file
            DAXGenerator = None

        # Get Parquet files from processed folder
        parquet_files = []

        # Get Parquet files from multiple potential locations
        search_paths = [
            PROCESSED_FOLDER,
            PIPELINE_OUTPUT_FOLDER,
            Path("/app/data/processed"),  # Docker absolute path
            Path("/app/data/pipeline_output"),  # Docker absolute path  
            PROJECT_ROOT / "data" / "processed",  # Local relative path
            PROJECT_ROOT / "data" / "pipeline_output"  # Local relative path
        ]
        
        # Ensure processed folder exists
        ensure_directory_exists(PROCESSED_FOLDER)
        
        print(f"Searching for parquet files in {len(search_paths)} locations:")
        for path in search_paths:
            print(f"  - {path} (exists: {path.exists() if path else False})")
        
        parquet_files = find_parquet_files(search_paths)

        if not parquet_files:
            # Last attempt: try listing all accessible directories
            print("No parquet files found in standard locations. Checking current working directory...")
            cwd = Path.cwd()
            print(f"Current working directory: {cwd}")
            
            potential_data_dirs = [
                cwd / "data" / "processed",
                cwd / "data" / "pipeline_output",
                Path("/app") / "data" / "processed",
                Path("/app") / "data" / "pipeline_output"
            ]
            
            for potential_dir in potential_data_dirs:
                if potential_dir.exists():
                    files = list(potential_dir.glob("*.parquet"))
                    if files:
                        print(f"Found {len(files)} parquet files in fallback location: {potential_dir}")
                        parquet_files = files
                        break
                        
            if not parquet_files:
                error_msg = f"No Parquet files found for Power BI package. Searched in: {[str(p) for p in search_paths]}"
                print(error_msg)
                return jsonify({"error": error_msg}), 404

        print(f"Found {len(parquet_files)} parquet files")

        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            with zipfile.ZipFile(tmp_file.name, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add Parquet files to DATA_BI folder
                for file_path in parquet_files:
                    zipf.write(file_path, f"DATA_BI/{file_path.name}")
                    print(f"Added to zip: DATA_BI/{file_path.name}")

                # Try to add DAX measures file if DAXGenerator is available
                if DAXGenerator:
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            dax_generator = DAXGenerator()
                            dax_file_path = dax_generator.generate_dax_file(temp_dir)
                            zipf.write(
                                dax_file_path, "DATA_BI/ETL_Dashboard_Measures.dax"
                            )
                            print("Added DAX measures file to zip")
                    except Exception as dax_error:
                        print(f"Warning: Could not generate DAX file: {dax_error}")
                        # Continue without DAX file
                else:
                    print("Skipping DAX file generation (DAXGenerator not available)")

            # Generate download filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_filename = f"DATA_BI_{timestamp}.zip"

            print(f"Sending zip file: {download_filename}")
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=download_filename,
                mimetype="application/zip",
            )

    except Exception as e:
        print(f"Error in download_powerbi_package: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/download/csv/<file_id>")
def download_csv_package(file_id):
    """Download organized CSV package."""
    import tempfile
    import zipfile
    from datetime import datetime

    try:
        # Get CSV files from processed folder
        csv_files = []

        if PROCESSED_FOLDER.exists():
            for file_path in PROCESSED_FOLDER.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == ".csv":
                    csv_files.append(file_path)

        if not csv_files:
            return jsonify({"error": "No CSV files found for CSV package"}), 404

        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            with zipfile.ZipFile(tmp_file.name, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add CSV files to DATA_CSV folder
                for file_path in csv_files:
                    zipf.write(file_path, f"DATA_CSV/{file_path.name}")

            # Generate download filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_filename = f"DATA_CSV_{timestamp}.zip"

            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=download_filename,
                mimetype="application/zip",
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/dax/<file_id>")
def download_dax_measures(file_id):
    """Download DAX measures file."""
    import tempfile
    import os
    import shutil
    from datetime import datetime

    from backend.services.dax_generator import DAXGenerator

    try:
        # Create a temporary file that we can control
        temp_fd, temp_path = tempfile.mkstemp(suffix='.dax', text=True)
        
        try:
            # Generate DAX measures file in a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                dax_generator = DAXGenerator()
                dax_file_path = dax_generator.generate_dax_file(temp_dir)
                
                # Close the temp file descriptor and copy the DAX content
                os.close(temp_fd)
                shutil.copy2(dax_file_path, temp_path)

            # Generate download filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_filename = f"ETL_Dashboard_Measures_{timestamp}.dax"

            def remove_file(response):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                return response

            return send_file(
                temp_path,
                as_attachment=True,
                download_name=download_filename,
                mimetype="text/plain",
            )

        except Exception as e:
            # Clean up temp file on error
            try:
                os.close(temp_fd)
            except:
                pass
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise e

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/open-folder/<folder_type>")
def open_local_folder(folder_type):
    """Open local folder in file explorer."""
    import platform
    import subprocess

    try:
        if folder_type == "pipeline":
            folder_path = PIPELINE_OUTPUT_FOLDER
        elif folder_type == "processed":
            folder_path = PROCESSED_FOLDER
        else:
            return jsonify({"error": "Invalid folder type"}), 400

        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)

        # Open folder based on operating system
        system = platform.system()
        if system == "Windows":
            subprocess.run(["explorer", str(folder_path.absolute())], check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path.absolute())], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(folder_path.absolute())], check=True)
        else:
            return jsonify({"error": f"Unsupported operating system: {system}"}), 400

        return jsonify(
            {
                "success": True,
                "message": f"Opened {folder_type} folder",
                "path": str(folder_path.absolute()),
            }
        )

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to open folder: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/files/list")
def list_available_files():
    """List all available files for download."""
    try:
        files = []

        # Pipeline output folder removed - using processed folder only

        # Check processed folder
        if PROCESSED_FOLDER.exists():
            for file_path in PROCESSED_FOLDER.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append(
                        {
                            "name": file_path.name,
                            "path": f"processed/{file_path.name}",
                            "size_bytes": stat.st_size,
                            "size_human": format_file_size(stat.st_size),
                            "modified": stat.st_mtime,
                            "type": "processed",
                            "download_url": f"/download/{file_path.name}",
                        }
                    )

        # Sort by modification time (newest first)
        files.sort(key=lambda f: f["modified"], reverse=True)

        return jsonify(
            {
                "files": files,
                "count": len(files),
                "pipeline_folder": str(PIPELINE_OUTPUT_FOLDER.absolute()),
                "processed_folder": str(PROCESSED_FOLDER.absolute()),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "frontend": "Flask",
            "fastapi_url": FASTAPI_BASE_URL,
            "pipeline_folder": str(PIPELINE_OUTPUT_FOLDER.absolute()),
            "processed_folder": str(PROCESSED_FOLDER.absolute()),
        }
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template("index.html", error="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template("index.html", error="Internal server error"), 500


# Template filters
@app.template_filter("filesize")
def filesize_filter(size_bytes):
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


@app.template_filter("percentage")
def percentage_filter(value):
    """Format decimal as percentage."""
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return "N/A"


@app.route("/api/health")
def api_health():
    """Proxy health check to FastAPI backend."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/api/health")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Proxy file upload to FastAPI backend."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Read the file content to avoid stream issues
        file_content = file.read()
        file.seek(0)  # Reset stream position

        # Forward the file to FastAPI backend
        files = {"file": (file.filename, file_content, file.content_type)}
        response = requests.post(
            f"{FASTAPI_BASE_URL}/api/upload", files=files, timeout=30
        )

        if response.status_code == 200:
            return jsonify(response.json()), response.status_code
        else:
            return (
                jsonify({"error": f"Backend error: {response.text}"}),
                response.status_code,
            )

    except requests.exceptions.Timeout:
        return jsonify({"error": "Upload timeout - file may be too large"}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route("/api/logs/recent", methods=["GET"])
def api_logs_recent():
    """Proxy logs request to FastAPI backend."""
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/api/logs/recent", timeout=10
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout", "logs": [], "count": 0}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}", "logs": [], "count": 0}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to fetch logs: {str(e)}", "logs": [], "count": 0}), 500


@app.route("/api/progress/status", methods=["GET"])
def api_progress_status():
    """Proxy progress status request to FastAPI backend."""
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/api/progress/status", timeout=10
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout", "status": "unknown"}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}", "status": "error"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to fetch status: {str(e)}", "status": "error"}), 500


@app.route("/api/transform", methods=["POST"])
def api_transform():
    """Proxy ETL transform to FastAPI backend with debugging."""
    try:
        # Get JSON data from request
        transform_data = request.get_json()

        print("🔧 Transform request received:")
        print(f"   File ID: {transform_data.get('file_id', 'N/A')}")
        print(f"   Master Sheet: {transform_data.get('master_sheet', 'N/A')}")
        print(f"   Status Sheet: {transform_data.get('status_sheet', 'N/A')}")
        print(f"   Options: {transform_data.get('options', {})}")

        # Forward the request to FastAPI backend
        response = requests.post(
            f"{FASTAPI_BASE_URL}/api/transform",
            json=transform_data,
            headers={"Content-Type": "application/json"},
        )

        print(f"🔧 FastAPI response status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Transform error: {response.text}")
        else:
            result = response.json()
            print(f"✅ Transform success: {result.get('success', False)}")
            if result.get("artifacts"):
                print(f"   Artifacts created: {len(result['artifacts'])}")

        return jsonify(response.json()), response.status_code

    except Exception as e:
        print(f"❌ Transform proxy error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/test")
def test_page():
    """Test page for debugging frontend-backend communication."""
    return render_template(
        "test.html", fastapi_url=Config.FASTAPI_BROWSER_URL, page_title="Frontend-Backend Test"
    )


if __name__ == "__main__":
    # Development server - Use PORT environment variable for consistency with Cloud Run
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", "8080")))  # Priority: PORT -> FLASK_PORT -> 8080
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    app.run(host=host, port=port, debug=debug)
