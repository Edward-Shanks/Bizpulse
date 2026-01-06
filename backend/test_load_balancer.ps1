# PowerShell script to test Ollama load balancing
# Usage: .\test_load_balancer.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OLLAMA LOAD BALANCER TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if we're in the backend directory
if (-not (Test-Path "app\core\config.py")) {
    Write-Host "Error: Must run from backend directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Try to find Python
$pythonCmd = $null

# Check for venv first
if (Test-Path "venv\Scripts\python.exe") {
    $pythonCmd = "venv\Scripts\python.exe"
    Write-Host "Found Python in venv: $pythonCmd" -ForegroundColor Green
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    Write-Host "Found Python: $pythonCmd" -ForegroundColor Green
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
    Write-Host "Found Python3: $pythonCmd" -ForegroundColor Green
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
    Write-Host "Found Python launcher: $pythonCmd" -ForegroundColor Green
}
else {
    Write-Host "Error: Python not found!" -ForegroundColor Red
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Activate your virtual environment, OR" -ForegroundColor Yellow
    Write-Host "  2. Install Python and add it to PATH" -ForegroundColor Yellow
    exit 1
}

# Run the test
Write-Host "`nRunning test..." -ForegroundColor Cyan
& $pythonCmd test_load_balancer_simple.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nTest completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nTest failed with exit code: $LASTEXITCODE" -ForegroundColor Red
}


