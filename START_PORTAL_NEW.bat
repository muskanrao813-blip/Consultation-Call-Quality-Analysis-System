@echo off
REM Dietician QA Portal — FastAPI Startup

echo.
echo ===============================================
echo Dietician QA Portal — FastAPI Server
echo ===============================================
echo.

cd /d "C:\Users\muskan.rao\Documents\claude\dietician-qa"

echo Checking dependencies...
pip show celery > nul
if errorlevel 1 (
    echo ERROR: Dependencies not installed
    echo Run this first:
    echo   pip install -r requirements-minimal.txt
    pause
    exit /b 1
)

echo.
echo Setting up database...
if not exist ".env" (
    echo DATABASE_URL=sqlite:///./test.db > .env
    echo REDIS_URL=redis://localhost:6379/0 >> .env
    echo GOOGLE_APPLICATION_CREDENTIALS= >> .env
    echo GCS_BUCKET_NAME=dietician-qa-audio >> .env
    echo GEMINI_API_KEY= >> .env
    echo CELERY_CONCURRENCY=2 >> .env
    echo Created .env file
)

echo.
echo ===============================================
echo Starting FastAPI Server on port 8001...
echo ===============================================
echo.
echo Portal URL: http://localhost:8001
echo API Docs:  http://localhost:8001/docs
echo Health:    http://localhost:8001/health
echo.
echo Keep this terminal open. Press Ctrl+C to stop.
echo.

python -m uvicorn app.main:app --reload --port 8001

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start FastAPI
    echo.
    echo Troubleshooting:
    echo 1. Check dependencies: pip install -r requirements-minimal.txt
    echo 2. Check port 8001 is free: netstat -ano ^| findstr :8001
    echo 3. Check .env file exists
    echo.
    pause
    exit /b 1
)
