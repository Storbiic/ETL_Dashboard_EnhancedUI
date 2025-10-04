#!/usr/bin/env python3
"""
Local development server for the ETL Dashboard.
This script provides a local development environment with hot reloading.
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

# Set environment variables for local development
os.environ['PYTHONPATH'] = str(Path(__file__).parent)
os.environ['FASTAPI_HOST'] = '127.0.0.1'
os.environ['FASTAPI_PORT'] = '8000'
os.environ['FLASK_ENV'] = 'development'

def run_command(cmd, description, background=False):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        if background:
            # Start process in background
            process = subprocess.Popen(cmd, shell=True)
            print(f"✅ {description} started (PID: {process.pid})")
            return process
        else:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ {description} completed")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main development server startup."""
    print("🚀 Starting ETL Dashboard Local Development Server")
    print("=" * 60)
    
    # Check if Python environment is ready
    print("📋 Checking environment...")
    
    # Install/update requirements if needed
    if Path("requirements-local.txt").exists():
        print("📦 Installing/updating dependencies...")
        run_command("pip install -r requirements-local.txt", "Installing dependencies")
    
    # Start FastAPI backend
    print("\n🔧 Starting Backend Services...")
    backend_process = run_command(
        "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload",
        "Starting FastAPI backend server",
        background=True
    )
    
    if not backend_process:
        print("❌ Failed to start backend server")
        return False
    
    # Wait for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(5)
    
    # Test backend health
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend health check passed")
        else:
            print("⚠️ Backend health check failed")
    except Exception as e:
        print(f"⚠️ Backend health check failed: {e}")
    
    # Display local URLs
    print("\n🌐 Local Development URLs:")
    print("=" * 40)
    print(f"🎨 Frontend (Modern UI):  http://localhost:8080")
    print(f"🔧 Backend API:           http://localhost:8000")
    print(f"📚 API Documentation:     http://localhost:8000/docs")
    print(f"💚 Health Check:          http://localhost:8000/health")
    print()
    
    # Start simple HTTP server for the frontend
    print("🔧 Starting Frontend Server...")
    frontend_process = run_command(
        f"python -m http.server 8080 --directory {Path(__file__).parent}",
        "Starting frontend HTTP server",
        background=True
    )
    
    if not frontend_process:
        print("❌ Failed to start frontend server")
        backend_process.terminate()
        return False
    
    # Wait for frontend to start
    time.sleep(2)
    
    print("\n🎉 Development server is ready!")
    print("=" * 40)
    print("📱 Open http://localhost:8080/index-local.html in your browser")
    print("🔄 Backend auto-reloads on code changes")
    print("🛑 Press Ctrl+C to stop all servers")
    print()
    
    # Auto-open browser
    try:
        webbrowser.open("http://localhost:8080/index-local.html")
        print("🌐 Browser opened automatically")
    except Exception as e:
        print(f"⚠️ Could not auto-open browser: {e}")
    
    try:
        # Keep the script running and monitor processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down development server...")
        
        # Terminate processes
        try:
            backend_process.terminate()
            frontend_process.terminate()
            
            # Wait for graceful shutdown
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
            
            print("✅ All servers stopped successfully")
        except Exception as e:
            print(f"⚠️ Error during shutdown: {e}")
            # Force kill if needed
            try:
                backend_process.kill()
                frontend_process.kill()
            except:
                pass
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)