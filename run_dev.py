#!/usr/bin/env python3
"""Development server runner for ETL Dashboard."""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_backend():
    """Run the FastAPI backend server."""
    print("🚀 Starting FastAPI backend...")
    
    env = os.environ.copy()
    env.update({
        'PYTHONPATH': str(Path.cwd()),
        'FASTAPI_RELOAD': 'true'
    })
    
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'backend.main:app',
        '--reload',
        '--host', os.getenv('FASTAPI_HOST', '127.0.0.1'),
        '--port', os.getenv('FASTAPI_PORT', '8000')
    ]
    
    return subprocess.Popen(cmd, env=env)

def run_frontend():
    """Run the Flask frontend server."""
    print("🌐 Starting Flask frontend...")
    
    env = os.environ.copy()
    env.update({
        'FLASK_APP': 'frontend.app',
        'FLASK_DEBUG': 'true',
        'PYTHONPATH': str(Path.cwd())
    })
    
    cmd = [
        sys.executable, '-m', 'flask', 'run',
        '--host', os.getenv('FLASK_HOST', '127.0.0.1'),
        '--port', os.getenv('FLASK_PORT', '5000')
    ]
    
    return subprocess.Popen(cmd, env=env)

def main():
    """Main function to run both servers."""
    print("🔧 ETL Dashboard Development Server")
    print("=" * 40)
    
    # Ensure data directories exist
    Path('data/uploads').mkdir(parents=True, exist_ok=True)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    
    # Start servers
    backend_process = run_backend()
    time.sleep(2)  # Give backend time to start
    frontend_process = run_frontend()
    
    print("\n✅ Servers started successfully!")
    print(f"📊 Frontend: http://{os.getenv('FLASK_HOST', '127.0.0.1')}:{os.getenv('FLASK_PORT', '5000')}")
    print(f"🔌 Backend API: http://{os.getenv('FASTAPI_HOST', '127.0.0.1')}:{os.getenv('FASTAPI_PORT', '8000')}")
    print(f"📚 API Docs: http://{os.getenv('FASTAPI_HOST', '127.0.0.1')}:{os.getenv('FASTAPI_PORT', '8000')}/docs")
    print("\n🛑 Press Ctrl+C to stop both servers")
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Wait for graceful shutdown
        try:
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
            frontend_process.kill()
        
        print("✅ Servers stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Wait for processes
        while True:
            if backend_process.poll() is not None:
                print("❌ Backend process died")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process died")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == '__main__':
    main()
