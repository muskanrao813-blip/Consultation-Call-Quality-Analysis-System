@echo off
REM Dietician QA Portal - Complete Startup Script
REM This script starts the FastAPI portal on port 8001

cd /d "C:\Users\muskan.rao\Documents\claude\dietician-qa"

echo.
echo ===============================================
echo   DIETICIAN QA PORTAL - STARTING
echo ===============================================
echo.
echo Portal URL: http://localhost:8001
echo API Docs:   http://localhost:8001/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --reload --port 8001
