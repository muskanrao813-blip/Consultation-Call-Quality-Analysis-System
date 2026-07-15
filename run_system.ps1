# Dietician QA Portal - Complete System Startup Script
# Run this script to start backend, frontend, and open the portal

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Dietician QA Portal - System Startup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Set working directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if database exists
$dbPath = "$scriptPath\test.db"
if (Test-Path $dbPath) {
    Write-Host "`n[INFO] Found existing database" -ForegroundColor Yellow
    $clearDB = Read-Host "Clear database and start fresh? (y/n)"
    if ($clearDB -eq 'y') {
        Remove-Item $dbPath -Force
        Write-Host "[OK] Database cleared" -ForegroundColor Green
    }
} else {
    Write-Host "`n[INFO] No existing database found - will create fresh" -ForegroundColor Yellow
}

# Kill any existing Python processes
Write-Host "`n[INFO] Cleaning up any existing processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start Backend
Write-Host "`n[STARTING] Backend Server on port 8000..." -ForegroundColor Cyan
Start-Process -NoNewWindow -FilePath python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 5

# Check backend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Backend running on http://localhost:8000" -ForegroundColor Green
        Write-Host "     API Docs: http://localhost:8000/docs" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] Backend may still be starting..." -ForegroundColor Yellow
}

# Start Frontend
Write-Host "`n[STARTING] Frontend on port 3000..." -ForegroundColor Cyan
cd "$scriptPath\clinical-intelligence-system"
Start-Process -NoNewWindow -FilePath npm -ArgumentList "run dev"
Start-Sleep -Seconds 5

Write-Host "`n================================" -ForegroundColor Green
Write-Host "System Ready!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "`nBackend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Go to Upload tab" -ForegroundColor White
Write-Host "3. Upload Excel file with recording URLs" -ForegroundColor White
Write-Host "4. View results in Transcriptions tab" -ForegroundColor White

Write-Host "`nTo stop the system, press Ctrl+C" -ForegroundColor Yellow
Write-Host "`nWaiting for system to be ready..." -ForegroundColor Gray

# Keep terminal open
Read-Host "`nPress Enter to close this window"
