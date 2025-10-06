@echo off
REM ETL Dashboard - Automated Cleanup Script for Windows
REM Run this before publishing to GitHub

echo =========================================
echo   ETL Dashboard - GitHub Cleanup Script
echo =========================================
echo.

REM Create backup branch first
echo [STEP 1] Creating backup branch...
git checkout -b pre-cleanup-backup
git checkout main
echo Backup branch created: pre-cleanup-backup
echo.

REM Phase 1: Remove development markdown files
echo [STEP 2] Removing development markdown files...
del /F /Q 3_STEP_VS_4_STEP_COMPARISON.md 2>nul
del /F /Q 4_STEP_WORKFLOW_UPDATE.md 2>nul
del /F /Q CONNECTIVITY_GUIDE.md 2>nul
del /F /Q CONNECTIVITY_RESOLVED.md 2>nul
del /F /Q DEBUGGING_GUIDE.md 2>nul
del /F /Q FIXES_APPLIED.md 2>nul
del /F /Q GREEN_COLOR_SCHEME_UPDATE.md 2>nul
del /F /Q IMPLEMENTATION_COMPLETE.md 2>nul
del /F /Q IMPLEMENTATION_SUMMARY.md 2>nul
del /F /Q LOADING_MODAL_AND_LOGS_FIX.md 2>nul
del /F /Q LOGS_PAGE_FIX.md 2>nul
del /F /Q PROGRESS_RESULTS_FIX.md 2>nul
del /F /Q PROGRESS_TRACKER_FIX.md 2>nul
del /F /Q PROGRESS_TRACKER_RESET_FIX.md 2>nul
del /F /Q PROGRESS_TRACKER_VISUAL_COMPARISON.md 2>nul
del /F /Q QUICK_REFERENCE_PROGRESS_FIX.md 2>nul
del /F /Q README_START.md 2>nul
del /F /Q REMOVAL_SUMMARY.md 2>nul
del /F /Q RESULTS_PAGE_FINAL_FIX.md 2>nul
del /F /Q STARTUP_REMINDER.txt 2>nul
del /F /Q STICKY_PROGRESS_TRACKER.md 2>nul
del /F /Q UPLOAD_DOUBLE_CLICK_FIX.md 2>nul
del /F /Q VISUAL_BREAKDOWN.md 2>nul
del /F /Q reset_progress.js 2>nul
echo Development docs removed
echo.

REM Phase 2: Organize deployment scripts
echo [STEP 3] Organizing deployment scripts...
if not exist "scripts\deployment" mkdir scripts\deployment
move /Y deploy-backend-only.ps1 scripts\deployment\ 2>nul
move /Y deploy-frontend-only.ps1 scripts\deployment\ 2>nul
move /Y deploy-frontend-gcp.ps1 scripts\deployment\ 2>nul
move /Y deploy-frontend-gcp.sh scripts\deployment\ 2>nul
move /Y deploy-gcp.ps1 scripts\deployment\ 2>nul
move /Y docker_build.sh scripts\deployment\ 2>nul
move /Y docker_cleanup.sh scripts\deployment\ 2>nul
move /Y docker_deploy.sh scripts\deployment\ 2>nul
echo Deployment scripts organized
echo.

REM Phase 3: Organize documentation
echo [STEP 4] Organizing documentation...
if not exist "docs" mkdir docs
move /Y ETL_WORKFLOW_DOCUMENTATION.md docs\ 2>nul
echo Documentation organized
echo.

REM Phase 4: Clean Python cache and artifacts
echo [STEP 5] Cleaning Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
del /s /q *.pyd 2>nul
echo Python cache cleaned
echo.

REM Phase 5: Clean log files
echo [STEP 6] Cleaning log files...
if exist "logs\*.log" del /F /Q logs\*.log 2>nul
echo Log files cleaned
echo.

REM Phase 6: Check for sensitive data
echo [STEP 7] Checking for potential sensitive data...
echo WARNING: Please manually review the following files:
echo   - .env (should NOT be committed)
echo   - .env.production (should NOT be committed)
echo   - .env.example (should have NO real values)
echo.
echo Press any key to continue after reviewing...
pause >nul
echo.

REM Phase 7: Format code (if black and isort are installed)
echo [STEP 8] Formatting code...
where black >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Running black formatter...
    black backend\ tests\ frontend\
) else (
    echo WARNING: black not installed. Install with: pip install black
)

where isort >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Running isort...
    isort backend\ tests\ frontend\
) else (
    echo WARNING: isort not installed. Install with: pip install isort
)
echo.

REM Phase 8: Run tests
echo [STEP 9] Running tests...
where pytest >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    pytest tests\ -v
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Tests failed! Please fix before continuing.
        pause
        exit /b 1
    )
) else (
    echo WARNING: pytest not installed. Skipping tests.
)
echo.

REM Phase 9: Git status
echo [STEP 10] Checking git status...
git status
echo.

REM Final confirmation
echo =========================================
echo   Cleanup Complete!
echo =========================================
echo.
echo Next steps:
echo   1. Review git status above
echo   2. Review README.md and update if needed
echo   3. Test the application locally
echo   4. Commit changes:
echo      git add -A
echo      git commit -m "chore: clean project for GitHub publication"
echo   5. Push to GitHub:
echo      git push origin main
echo.
echo If something went wrong, restore from backup:
echo   git checkout pre-cleanup-backup
echo.
pause
