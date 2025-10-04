# 🔌 Backend-Frontend Connectivity Guide

## ✅ SOLUTION TO ERR_CONNECTION_RESET

### 🔴 Problem
```
POST http://127.0.0.1:5000/api/upload net::ERR_CONNECTION_RESET
Upload error: TypeError: Failed to fetch
```

### ✅ Root Cause
**The FastAPI backend server was not running!**

The Flask frontend (port 5000) was running, but it needs to proxy requests to the FastAPI backend (port 8000). When the backend is down, you get `ERR_CONNECTION_RESET` errors.

---

## 🚀 Quick Fix (Always Do This First!)

### Start Both Servers
```cmd
python run_dev.py
```

This single command starts:
- ✅ **FastAPI Backend** on http://127.0.0.1:8000
- ✅ **Flask Frontend** on http://127.0.0.1:5000

**Wait for these messages:**
```
✅ Servers started successfully!
📊 Frontend: http://127.0.0.1:5000
🔌 Backend API: http://127.0.0.1:8000
```

---

## 🏗️ Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Browser       │ ──────> │  Flask Frontend  │ ──────> │ FastAPI Backend │
│   :5000         │ <────── │  Port 5000       │ <────── │  Port 8000      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                    │                             │
                                    │                             │
                              Proxies API                   Handles Logic
                              Requests                      ETL Processing
                                                           File Operations
```

### Request Flow

1. **User uploads file in browser**
   ```javascript
   // frontend/static/js/app.js
   fetch('/api/upload', { method: 'POST', body: formData })
   ```

2. **Flask receives request** (port 5000)
   ```python
   # frontend/app.py
   @app.route("/api/upload", methods=["POST"])
   def api_upload():
       # Proxy to FastAPI backend
       response = requests.post(f"{FASTAPI_BASE_URL}/api/upload", ...)
   ```

3. **Flask proxies to FastAPI** (port 8000)
   ```python
   # Flask sends to: http://127.0.0.1:8000/api/upload
   ```

4. **FastAPI processes request**
   ```python
   # backend/api/routes_upload.py
   @router.post("/api/upload")
   async def upload_file(file: UploadFile):
       # Save file, return file_id
   ```

5. **Response flows back to browser**

---

## ⚙️ Configuration Details

### Environment Variables
```bash
# .env file (optional)
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
FLASK_DEBUG=true
```

### Flask Configuration
```python
# frontend/app.py
class Config:
    fastapi_host = os.getenv('FASTAPI_HOST', '127.0.0.1')
    fastapi_port = os.getenv('FASTAPI_PORT', '8000')
    FASTAPI_BASE_URL = f"http://{fastapi_host}:{fastapi_port}"
    FASTAPI_BROWSER_URL = f"http://localhost:{fastapi_port}"
```

### Why Two URLs?

- **FASTAPI_BASE_URL**: Used by Flask backend to talk to FastAPI
  - `http://127.0.0.1:8000` (server-to-server)
  
- **FASTAPI_BROWSER_URL**: Used by browser JavaScript
  - `http://localhost:8000` (browser-to-server)

---

## 🔍 Health Check Script

### Run Connectivity Test
```cmd
python health_check.py
```

### Expected Output (Healthy)
```
============================================================
🔧 BACKEND-FRONTEND CONNECTIVITY CHECK
============================================================

1️⃣ Configuration:
   FASTAPI_HOST: 127.0.0.1
   FASTAPI_PORT: 8000
   FASTAPI_BASE_URL: http://127.0.0.1:8000
   FASTAPI_BROWSER_URL: http://localhost:8000

2️⃣ Backend Health Check:
   Testing: http://127.0.0.1:8000/health
   ✅ SUCCESS: http://127.0.0.1:8000/health is reachable

3️⃣ API Endpoint Tests:
   Testing: GET http://127.0.0.1:8000/api/logs/recent
   ✅ 200: /api/logs/recent

4️⃣ Upload Endpoint Check:
   Testing: POST http://127.0.0.1:8000/api/upload
   ✅ Upload endpoint is accessible (got 400)

============================================================
✅ CONNECTIVITY CHECK COMPLETE
============================================================
```

---

## 🐛 Troubleshooting

### Issue: Backend Not Running

**Symptom:**
```
❌ CONNECTION REFUSED: http://127.0.0.1:8000/health
```

**Solution:**
```cmd
# Kill any stuck processes
taskkill /F /IM python.exe

# Restart servers
python run_dev.py
```

---

### Issue: Port Already in Use

**Symptom:**
```
[Errno 10048] Only one usage of each socket address is normally permitted
```

**Solution:**
```cmd
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /F /PID <PID>

# Or use different ports
set FASTAPI_PORT=8001
python run_dev.py
```

---

### Issue: CORS Errors

**Symptom:**
```
Access to fetch at 'http://127.0.0.1:8000/api/upload' has been blocked by CORS policy
```

**Check Backend CORS:**
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should allow all origins in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Issue: Proxy Not Working

**Symptom:**
```
Flask returns 500, logs show connection error to backend
```

**Verify Configuration:**
```python
# frontend/app.py
print(f"FASTAPI_BASE_URL: {FASTAPI_BASE_URL}")
# Should print: http://127.0.0.1:8000
```

**Test Backend Directly:**
```bash
# In browser, visit:
http://127.0.0.1:8000/docs

# Should show FastAPI Swagger UI
```

---

## 📊 Monitoring Connectivity

### Check Both Servers are Running

**Terminal Output Should Show:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000  ← Backend
 * Running on http://127.0.0.1:5000                ← Frontend
```

### Browser Console (No Errors)
```
Template set FASTAPI_URL to: http://localhost:8000  ✅
[GlobalProgressTracker] Initializing...             ✅
```

### Network Tab (Successful Request)
```
Request:  POST http://127.0.0.1:5000/api/upload
Status:   200 OK
Response: { "file_id": "abc-123", "sheets": [...] }
```

---

## 🔄 API Proxy Routes

All these Flask routes proxy to FastAPI:

| Flask Route               | FastAPI Route             | Purpose              |
|---------------------------|---------------------------|----------------------|
| `/api/upload`             | `/api/upload`             | File upload          |
| `/api/preview`            | `/api/preview`            | Sheet preview        |
| `/api/profile`            | `/api/profile`            | Data profiling       |
| `/api/transform`          | `/api/transform`          | ETL transformation   |
| `/api/logs/recent`        | `/api/logs/recent`        | Backend logs         |
| `/api/progress/status`    | `/api/progress/status`    | Progress tracking    |

### Example: Upload Proxy
```python
# frontend/app.py
@app.route("/api/upload", methods=["POST"])
def api_upload():
    try:
        # Get file from browser request
        file = request.files["file"]
        
        # Forward to FastAPI backend
        files = {"file": (file.filename, file_content, file.content_type)}
        response = requests.post(
            f"{FASTAPI_BASE_URL}/api/upload",  # http://127.0.0.1:8000/api/upload
            files=files,
            timeout=30
        )
        
        # Return FastAPI response to browser
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Backend connection failed: {str(e)}"}), 500
```

---

## 🎯 Best Practices

### 1. Always Start Both Servers
```cmd
# ✅ CORRECT
python run_dev.py

# ❌ WRONG - Only starts Flask
python run_frontend.py

# ❌ WRONG - Only starts FastAPI
uvicorn backend.main:app
```

### 2. Check Health Before Debugging
```cmd
# First, verify backend is reachable
python health_check.py

# If backend is down, start it first
python run_dev.py
```

### 3. Monitor Terminal Output
```
# Look for errors like:
requests.exceptions.ConnectionError  ← Backend down
Timeout                              ← Backend slow/stuck
500 Internal Server Error            ← Backend crashed
```

### 4. Use Browser DevTools
```
Network Tab:
  - Check request URL (should be :5000, not :8000)
  - Check status code (should be 200, not ERR_CONNECTION_RESET)
  - Check response (should have JSON data)

Console Tab:
  - Check for fetch errors
  - Check FASTAPI_URL is set correctly
```

---

## 🆘 Emergency Recovery

### If Everything Fails:

1. **Stop all Python processes**
   ```cmd
   taskkill /F /IM python.exe
   ```

2. **Clear ports**
   ```cmd
   netstat -ano | findstr :5000
   netstat -ano | findstr :8000
   # Kill any processes using these ports
   ```

3. **Restart fresh**
   ```cmd
   python run_dev.py
   ```

4. **Verify connectivity**
   ```cmd
   python health_check.py
   ```

5. **Hard refresh browser**
   ```
   Ctrl + Shift + R
   ```

---

## 📝 Summary Checklist

Before reporting connectivity issues, verify:

- [ ] Both servers are running (`python run_dev.py`)
- [ ] Backend responds to health check (`python health_check.py`)
- [ ] No port conflicts (check `netstat`)
- [ ] Browser shows correct FASTAPI_URL in console
- [ ] Network tab shows requests to `:5000` (not `:8000`)
- [ ] No CORS errors in browser console
- [ ] Backend terminal shows no crashes

---

**Last Updated**: October 3, 2025  
**Status**: ✅ Servers Running and Connected  
**Backend**: http://127.0.0.1:8000  
**Frontend**: http://127.0.0.1:5000
