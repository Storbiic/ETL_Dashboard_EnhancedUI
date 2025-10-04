"""
Backend-Frontend Connectivity Health Check
Ensures FastAPI backend is accessible from Flask frontend
"""

import os
import sys
import requests
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.app import Config, FASTAPI_BASE_URL

def check_backend_health():
    """Comprehensive backend health check."""
    print("=" * 60)
    print("🔧 BACKEND-FRONTEND CONNECTIVITY CHECK")
    print("=" * 60)
    
    # 1. Configuration Check
    print("\n1️⃣ Configuration:")
    print(f"   FASTAPI_HOST: {os.getenv('FASTAPI_HOST', '127.0.0.1')}")
    print(f"   FASTAPI_PORT: {os.getenv('FASTAPI_PORT', '8000')}")
    print(f"   FASTAPI_BASE_URL: {FASTAPI_BASE_URL}")
    print(f"   FASTAPI_BROWSER_URL: {Config.FASTAPI_BROWSER_URL}")
    
    # 2. Backend Ping Test
    print("\n2️⃣ Backend Health Check:")
    backend_urls = [
        f"{FASTAPI_BASE_URL}/health",
        f"{FASTAPI_BASE_URL}/",
        "http://127.0.0.1:8000/health",
        "http://localhost:8000/health",
    ]
    
    backend_alive = False
    for url in backend_urls:
        try:
            print(f"   Testing: {url}")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: {url} is reachable")
                backend_alive = True
                break
            else:
                print(f"   ⚠️  Response {response.status_code}: {url}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION REFUSED: {url}")
        except requests.exceptions.Timeout:
            print(f"   ⏱️  TIMEOUT: {url}")
        except Exception as e:
            print(f"   ❌ ERROR: {url} - {type(e).__name__}")
    
    if not backend_alive:
        print("\n   ⚠️  WARNING: Backend not reachable!")
        print("   💡 Solution: Start backend with: python run_dev.py")
        return False
    
    # 3. API Endpoint Tests
    print("\n3️⃣ API Endpoint Tests:")
    endpoints = [
        ("/api/logs/recent", "GET"),
        ("/api/progress/status", "GET"),
    ]
    
    for endpoint, method in endpoints:
        try:
            url = f"{FASTAPI_BASE_URL}{endpoint}"
            print(f"   Testing: {method} {url}")
            if method == "GET":
                response = requests.get(url, timeout=5)
            
            if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                print(f"   ✅ {response.status_code}: {endpoint}")
            else:
                print(f"   ⚠️  {response.status_code}: {endpoint}")
        except Exception as e:
            print(f"   ❌ FAILED: {endpoint} - {str(e)}")
    
    # 4. Upload Endpoint Test (critical)
    print("\n4️⃣ Upload Endpoint Check:")
    try:
        url = f"{FASTAPI_BASE_URL}/api/upload"
        print(f"   Testing: POST {url}")
        # Don't send actual file, just check if endpoint exists
        response = requests.post(url, files={}, timeout=5)
        # We expect 400 (no file), not connection error
        if response.status_code in [400, 422]:
            print(f"   ✅ Upload endpoint is accessible (got {response.status_code})")
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ CONNECTION ERROR: Upload endpoint not reachable")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    
    # 5. CORS Check
    print("\n5️⃣ CORS Configuration:")
    try:
        response = requests.options(f"{FASTAPI_BASE_URL}/api/upload", timeout=5)
        cors_headers = response.headers.get('Access-Control-Allow-Origin', 'Not set')
        print(f"   CORS Header: {cors_headers}")
    except Exception as e:
        print(f"   Could not check CORS: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ CONNECTIVITY CHECK COMPLETE")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = check_backend_health()
    
    if not success:
        print("\n🔴 BACKEND NOT RUNNING!")
        print("\n📋 To fix:")
        print("   1. Open a new terminal")
        print("   2. Run: python run_dev.py")
        print("   3. Wait for both servers to start")
        print("   4. Re-run this health check")
        sys.exit(1)
    else:
        print("\n✅ Backend is healthy and reachable!")
        sys.exit(0)
