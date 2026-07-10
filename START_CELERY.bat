@echo off
REM Dietician QA Portal — Celery Worker Startup

echo.
echo ===============================================
echo Dietician QA Portal — Celery Worker
echo ===============================================
echo.

cd /d "C:\Users\muskan.rao\Documents\claude\dietician-qa"

echo Starting Celery Worker...
echo This terminal will stay open - Celery is running
echo Keep this terminal open. Press Ctrl+C to stop the worker.
echo.

REM Start Celery worker
celery -A app.worker.celery_app worker -c 2 -l info

REM If celery fails
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Celery
    echo Make sure Redis is running and dependencies are installed
    echo.
    echo To check if Redis is running:
    echo   redis-cli ping
    echo   (should return PONG)
    pause
    exit /b 1
)
