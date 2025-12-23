@echo off
echo ========================================
echo Starting Mac Studio Ollama Tunnel
echo ========================================
echo.

echo Checking if tunnel already exists...
netstat -ano | findstr :11435 >nul
if %errorlevel% equ 0 (
    echo ⚠️  Tunnel already exists on port 11435
    echo    Stopping existing tunnel...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11435 ^| findstr LISTENING') do (
        taskkill /PID %%a /F 2>nul
    )
    timeout /t 1 /nobreak >nul
)

echo.
echo Creating SSH tunnel...
echo Port mapping: localhost:11435 → Mac Studio:11434
echo.
echo Command: ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
echo.
echo NOTE: You will be prompted for SSH password
echo.

ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ SSH tunnel created successfully!
    echo ========================================
    echo.
    echo Mac Studio Ollama accessible at: http://localhost:11435
    echo Laptop Ollama still running at: http://localhost:11434
    echo.
    echo Test Mac Studio: curl http://localhost:11435/api/tags
    echo Test Laptop: curl http://localhost:11434/api/tags
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
    echo 1. Mac Studio IP: 192.178.90.31
    echo 2. SSH user: rivemain
    echo 3. Mac Studio is accessible
    echo 4. You can SSH manually: ssh rivemain@192.178.90.31
)

echo.
pause

