#!/usr/bin/env python3
"""Run just the Flask frontend."""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the Flask frontend."""
    print("🌐 Starting Flask Frontend...")
    
    # Ensure data directories exist
    Path('data/uploads').mkdir(parents=True, exist_ok=True)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = 'frontend.app'
    env['FLASK_DEBUG'] = 'true'
    env['FASTAPI_HOST'] = '127.0.0.1'
    env['FASTAPI_PORT'] = '8000'
    env['FLASK_HOST'] = '127.0.0.1'
    env['FLASK_PORT'] = '5000'
    
    cmd = [
        sys.executable, '-m', 'flask', 'run',
        '--host', '127.0.0.1',
        '--port', '5000'
    ]
    
    print("✅ Frontend starting...")
    print("🌐 Frontend: http://127.0.0.1:5000")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped")

if __name__ == '__main__':
    main()
