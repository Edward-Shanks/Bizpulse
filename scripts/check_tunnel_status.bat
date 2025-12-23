@echo off
echo ========================================
echo Checking SSH Tunnel Status
echo ========================================
echo.

echo Checking if tunnel exists on port 11436...
netstat -ano | findstr :11436 >nul

if %errorlevel% equ 0 (
    echo ✅ SSH tunnel is ACTIVE on port 11436
    echo.
    echo Tunnel details:
    netstat -ano | findstr :11436 | findstr LISTENING
    echo.
    echo Testing Ollama connection...
    curl -s -m 5 http://localhost:11436/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Ollama is responding via tunnel
        echo.
        echo Quick test:
        curl -s http://localhost:11436/api/tags | findstr "models"
    ) else (
        echo ⚠️  Tunnel exists but Ollama is not responding
        echo    This might mean:
        echo    1. Mac Studio Ollama is not running
        echo    2. SSH tunnel is not forwarding correctly
        echo    3. Mac Studio is disconnected
    )
) else (
    echo ❌ SSH tunnel is NOT active on port 11436
    echo.
    echo To start tunnel, run:
    echo   ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29
    echo.
    echo OR use the script:
    echo   scripts\start_tunnel_background.bat
)

echo.
pause

