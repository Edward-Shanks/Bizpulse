@echo off
echo ========================================
echo Starting SSH Tunnel to Mac Studio
echo ========================================
echo.
echo IMPORTANT: This script must be run on your LAPTOP (Windows)
echo NOT on Mac Studio!
echo.

echo Step 1: Checking if port 11435 is already in use...
netstat -ano | findstr :11435 >nul
if %errorlevel% equ 0 (
    echo ⚠️  Port 11435 is already in use
    echo    Stopping existing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11435 ^| findstr LISTENING') do (
        echo Stopping PID %%a
        taskkill /PID %%a /F 2>nul
    )
    timeout /t 2 /nobreak >nul
)

echo.
echo Step 2: Creating SSH tunnel...
echo.
echo Command: ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
echo.
echo NOTE: 
echo - Replace rivemain@192.178.90.31 with your Mac Studio credentials
echo - You will be prompted for SSH password
echo.

set /p MAC_IP="Enter Mac Studio IP (e.g., 192.178.90.31): "
set /p MAC_USER="Enter Mac Studio username (e.g., rivemain): "

echo.
echo Creating tunnel: %MAC_USER%@%MAC_IP%
ssh -f -N -L 11435:localhost:11434 %MAC_USER%@%MAC_IP%

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ SSH tunnel created successfully!
    echo ========================================
    echo.
    echo Mac Studio Ollama accessible at: http://localhost:11435
    echo.
    echo Test with: curl http://localhost:11435/api/tags
    echo.
    echo Update your .env file:
    echo OLLAMA_BASE_URL=http://localhost:11435
) else (
    echo.
    echo ========================================
    echo ❌ SSH tunnel failed!
    echo ========================================
    echo.
    echo Please check:
    echo 1. Mac Studio IP is correct: %MAC_IP%
    echo 2. SSH username is correct: %MAC_USER%
    echo 3. Mac Studio is accessible
    echo 4. You can SSH manually: ssh %MAC_USER%@%MAC_IP%
    echo.
    echo Common issues:
    echo - Wrong IP address
    echo - SSH not enabled on Mac Studio
    echo - Firewall blocking connection
)

echo.
pause

