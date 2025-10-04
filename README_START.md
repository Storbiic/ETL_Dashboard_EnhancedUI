# 🚀 START HERE - ETL Dashboard

## ⚡ Quick Start (DO THIS FIRST!)

### 1. Start Both Servers
```cmd
python run_dev.py
```

**Wait for:**
```
✅ Servers started successfully!
📊 Frontend: http://127.0.0.1:5000
🔌 Backend API: http://127.0.0.1:8000
```

### 2. Open Browser
```
http://127.0.0.1:5000
```

---

## ⚠️ CRITICAL: Both Servers Must Run!

The application requires **TWO servers**:

1. **FastAPI Backend** (Port 8000)
   - Handles ETL processing
   - File uploads and transformations
   - Database operations

2. **Flask Frontend** (Port 5000)
   - Serves web interface
   - Proxies requests to backend

**If backend is not running, you'll get:**
```
❌ ERR_CONNECTION_RESET
❌ Failed to fetch
❌ Upload errors
```

---

## 🔧 Common Issues & Solutions

### Issue: "ERR_CONNECTION_RESET"

**Cause**: Backend server not running

**Fix**:
```cmd
python run_dev.py
```

---

### Issue: "Port already in use"

**Cause**: Previous Python process still running

**Fix**:
```cmd
# Kill all Python processes
taskkill /F /IM python.exe

# Restart servers
python run_dev.py
```

---

### Issue: "Upload not working"

**Cause**: Backend unreachable

**Fix**:
```cmd
# Check connectivity
python health_check.py

# If backend down, restart
python run_dev.py
```

---

## 📁 Project Files Reference

| File | Purpose |
|------|---------|
| `START_HERE.bat` | Windows quick start script |
| `run_dev.py` | Starts both servers |
| `health_check.py` | Tests backend connectivity |
| `CONNECTIVITY_GUIDE.md` | Full troubleshooting guide |

---

## 🎯 Workflow

```
1. Start Servers
   └─> python run_dev.py

2. Verify Running
   └─> Check terminal for ✅ messages

3. Open Browser
   └─> http://127.0.0.1:5000

4. Upload File
   └─> Drag & drop Excel file

5. If Errors
   └─> Check: Is backend running?
   └─> Fix: python run_dev.py
```

---

## 📞 Need Help?

1. **Check if servers are running**
   - Look for "Servers started successfully" in terminal

2. **Run health check**
   ```cmd
   python health_check.py
   ```

3. **Read full guide**
   - See `CONNECTIVITY_GUIDE.md`

4. **Restart from scratch**
   ```cmd
   taskkill /F /IM python.exe
   python run_dev.py
   ```

---

**Remember**: Always run `python run_dev.py` before using the app! 🚀
