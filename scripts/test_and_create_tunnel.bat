@echo off
echo ========================================
echo Test and Create SSH Tunnel to Mac Studio
echo ========================================
echo.

set /p MAC_IP="Enter Mac Studio IP (default: 192.178.90.31): "
if "%MAC_IP%"=="" set MAC_IP=192.178.90.31

set /p MAC_USER="Enter Mac Studio username (default: rivemain): "
if "%MAC_USER%"=="" set MAC_USER=rivemain

echo.
echo ========================================
echo Step 1: Testing SSH Connection
echo ========================================
echo Testing: ssh %MAC_USER%@%MAC_IP%
echo.

ssh -o ConnectTimeout=10 -o BatchMode=yes %MAC_USER%@%MAC_IP% "echo 'SSH OK'" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  SSH test failed (this is normal if using password auth)
    echo    Will proceed with tunnel creation...
) else (
    echo ✅ SSH connection successful
)

echo.
echo ========================================
echo Step 2: Testing Ollama on Mac Studio
echo ========================================
echo.

echo Testing: ssh %MAC_USER%@%MAC_IP% "curl -s http://localhost:11434/api/tags"
ssh %MAC_USER%@%MAC_IP% "curl -s http://localhost:11434/api/tags" 2>nul
if %errorlevel% equ 0 (
    echo.
    echo ✅ Ollama is accessible on Mac Studio!
) else (
    echo.
    echo ⚠️  Could not verify Ollama on Mac Studio
    echo    Make sure Ollama is running: ssh %MAC_USER%@%MAC_IP% "ollama serve"
)

echo.
echo ========================================
echo Step 3: Creating SSH Tunnel
echo ========================================
echo.

echo Waiting for port 11435 to be free...
:wait_loop
netstat -ano | findstr :11435 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo Port still in use, waiting...
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo Port 11435 is free.
echo.
echo Creating tunnel: localhost:11435 -> %MAC_USER%@%MAC_IP%:11434
echo Command: ssh -f -N -L 11435:localhost:11434 %MAC_USER%@%MAC_IP%
echo.

ssh -f -N -L 11435:localhost:11434 %MAC_USER%@%MAC_IP%

if %errorlevel% equ 0 (
    echo ✅ SSH tunnel command executed
    timeout /t 2 /nobreak >nul
    
    echo.
    echo ========================================
    echo Step 4: Testing Tunnel
    echo ========================================
    echo.
    
    echo Testing: curl http://localhost:11435/api/tags
    curl -s -m 10 http://localhost:11435/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo.
        echo ✅✅✅ TUNNEL IS WORKING! ✅✅✅
        echo.
        echo Full response:
        curl http://localhost:11435/api/tags
    ) else (
        echo.
        echo ❌ Tunnel test failed
        echo.
        echo Debugging info:
        echo.
        echo 1. Check tunnel process:
        netstat -ano ^| findstr :11435
        echo.
        echo 2. Test Mac Studio Ollama directly:
        echo    ssh %MAC_USER%@%MAC_IP% "curl http://localhost:11434/api/tags"
        echo.
        echo 3. Try manual tunnel (keep terminal open):
        echo    ssh -N -L 11435:localhost:11434 %MAC_USER%@%MAC_IP%
    )
) else (
    echo.
    echo ❌ SSH tunnel creation failed!
    echo.
    echo Please check:
    echo 1. Mac Studio IP: %MAC_IP%
    echo 2. Username: %MAC_USER%
    echo 3. SSH is accessible
)

echo.
pause

