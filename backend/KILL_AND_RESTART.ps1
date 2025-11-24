# Force kill all Python processes and restart server
Write-Host "Stopping ALL Python processes..." -ForegroundColor Red
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 3

Write-Host "Checking port 8000..." -ForegroundColor Yellow
$ports = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($ports) {
    Write-Host "Port 8000 still in use by:" -ForegroundColor Red
    $ports | ForEach-Object { 
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  PID $($_.OwningProcess): $($proc.ProcessName)" -ForegroundColor Red
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host "Clearing Python cache..." -ForegroundColor Yellow
Remove-Item "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Starting fresh server..." -ForegroundColor Green
Set-Location $PSScriptRoot

if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Start server in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; if (Test-Path 'venv\Scripts\Activate.ps1') { & 'venv\Scripts\Activate.ps1'; Write-Host 'Virtual environment activated' -ForegroundColor Green }; Write-Host 'Starting uvicorn server:app...' -ForegroundColor Green; uvicorn server:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "Server starting in new window. Wait 5 seconds and check http://localhost:8000/docs" -ForegroundColor Green

