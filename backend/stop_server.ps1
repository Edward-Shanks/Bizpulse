# Stop Server Script
# Stops all Python/uvicorn processes and frees port 8000

Write-Host "[STOP] Stopping all server processes..." -ForegroundColor Yellow

# Find processes using port 8000
Write-Host "`n[CHECK] Checking port 8000..." -ForegroundColor Cyan
$portProcesses = netstat -ano | Select-String ":8000" | ForEach-Object {
    if ($_ -match '\s+(\d+)\s*$') {
        $matches[1]
    }
} | Select-Object -Unique

if ($portProcesses) {
    Write-Host "Found processes using port 8000: $($portProcesses -join ', ')" -ForegroundColor Yellow
    foreach ($pid in $portProcesses) {
        try {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "  Stopping process $pid ($($process.ProcessName))..." -ForegroundColor Yellow
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "  [OK] Stopped process $pid" -ForegroundColor Green
            }
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Host "  [WARN] Could not stop process $pid : $errorMsg" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  [INFO] No processes found using port 8000" -ForegroundColor Gray
}

# Find all Python processes
Write-Host "`n[CHECK] Checking Python processes..." -ForegroundColor Cyan
$pythonProcesses = Get-Process | Where-Object {
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*uvicorn*" -or
    $_.Path -like "*Bizpulse*backend*"
} | Select-Object Id, ProcessName, Path

if ($pythonProcesses) {
    Write-Host "Found Python processes:" -ForegroundColor Yellow
    $pythonProcesses | Format-Table -AutoSize
    foreach ($proc in $pythonProcesses) {
        try {
            Write-Host "  Stopping process $($proc.Id) ($($proc.ProcessName))..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Stopped process $($proc.Id)" -ForegroundColor Green
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Host "  [WARN] Could not stop process $($proc.Id) : $errorMsg" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  [INFO] No Python processes found" -ForegroundColor Gray
}

# Wait a moment for ports to be released
Start-Sleep -Seconds 2

# Verify port 8000 is free
Write-Host "`n[VERIFY] Verifying port 8000 is free..." -ForegroundColor Cyan
$stillInUse = netstat -ano | Select-String ":8000"
if ($stillInUse) {
    Write-Host "  [WARN] Port 8000 is still in use!" -ForegroundColor Red
    Write-Host "  You may need to wait a few seconds or restart your computer" -ForegroundColor Yellow
} else {
    Write-Host "  [OK] Port 8000 is now free" -ForegroundColor Green
}

Write-Host "`n[OK] Done! All server processes have been stopped." -ForegroundColor Green

