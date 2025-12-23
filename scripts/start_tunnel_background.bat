@echo off
echo ========================================
echo Starting SSH Tunnel to Mac Studio
echo ========================================
echo.

echo Checking if tunnel already exists...
netstat -ano | findstr :11436 >nul
if %errorlevel% equ 0 (
    echo ⚠️  Tunnel already exists on port 11436
    echo    Stopping existing tunnel...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11436 ^| findstr LISTENING') do (
        taskkill /PID %%a /F 2>nul
    )
    timeout /t 2 /nobreak >nul
)

echo.
echo Creating SSH tunnel in background...
echo Command: ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29
echo.

ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29

if %errorlevel% equ 0 (
    timeout /t 2 /nobreak >nul
    
    echo Testing tunnel...
    curl -s http://localhost:11436/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo.
        echo ========================================
        echo ✅ SSH tunnel created and working!
        echo ========================================
        echo.
        echo Mac Studio Ollama accessible at: http://localhost:11436
        echo.
        echo Test: curl http://localhost:11436/api/tags
        echo.
        echo Tunnel is running in background.
        echo You can close this window.
    ) else (
        echo.
        echo ⚠️  Tunnel created but test failed
        echo    Wait a few seconds and try: curl http://localhost:11436/api/tags
    )
) else (
    echo.
    echo ❌ SSH tunnel creation failed!
    echo.
    echo Please check:
    echo 1. Mac Studio IP: 192.168.50.29
    echo 2. Username: thrivestudio
    echo 3. SSH is accessible
)

echo.
pause

