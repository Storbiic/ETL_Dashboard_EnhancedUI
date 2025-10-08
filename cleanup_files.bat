@echo off
echo ===============================================
echo ETL Dashboard - File Cleanup Utility
echo ===============================================
echo.
echo This will remove:
echo - Old uploaded files (older than 7 days)
echo - All processed files (to free up space)
echo.
set /p confirm="Do you want to continue? (y/N): "
if /i "%confirm%" neq "y" goto :cancel

echo.
echo Running cleanup...
python cleanup_uploads.py

echo.
echo Cleanup completed!
pause
goto :end

:cancel
echo Cleanup cancelled.
pause

:end