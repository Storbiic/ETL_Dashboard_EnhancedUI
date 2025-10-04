@echo off
echo ================================================================
echo    ETL DASHBOARD - QUICK START GUIDE
echo ================================================================
echo.
echo IMPORTANT: You must run BOTH servers for the app to work!
echo.
echo ----------------------------------------------------------------
echo  STEP 1: Start Both Servers
echo ----------------------------------------------------------------
echo.
echo   Run this command:
echo   python run_dev.py
echo.
echo   Wait for these messages:
echo   ✅ Servers started successfully!
echo   📊 Frontend: http://127.0.0.1:5000
echo   🔌 Backend API: http://127.0.0.1:8000
echo.
echo ----------------------------------------------------------------
echo  STEP 2: Open Browser
echo ----------------------------------------------------------------
echo.
echo   Visit: http://127.0.0.1:5000
echo.
echo ----------------------------------------------------------------
echo  TROUBLESHOOTING
echo ----------------------------------------------------------------
echo.
echo   ❌ ERR_CONNECTION_RESET?
echo      → Backend not running. Run: python run_dev.py
echo.
echo   ❌ Port already in use?
echo      → Kill processes: taskkill /F /IM python.exe
echo      → Then restart: python run_dev.py
echo.
echo   ❌ Upload not working?
echo      → Check health: python health_check.py
echo      → Restart servers: python run_dev.py
echo.
echo ================================================================
echo.
pause
python run_dev.py
