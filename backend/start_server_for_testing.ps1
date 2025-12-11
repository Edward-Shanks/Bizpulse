# PowerShell script to start server for testing
# Run this in a separate terminal window

Write-Host "Starting server for testing..." -ForegroundColor Cyan
Write-Host "Keep this window open while testing" -ForegroundColor Yellow
Write-Host ""

# Activate venv
& .\venv\Scripts\Activate.ps1

# Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

