@echo off
echo ========================================
echo Fix SSH Tunnel to Mac Studio
echo ========================================
echo.

echo Step 1: Stopping existing tunnels...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11435 ^| findstr LISTENING') do (
    echo Stopping PID %%a
    taskkill /PID %%a /F 2>nul
)
timeout /t 2 /nobreak >nul

echo.
echo Step 2: Verifying port is free...
netstat -ano | findstr :11435 >nul
if %errorlevel% equ 0 (
    echo ⚠️  Port still in use, trying again...
    timeout /t 2 /nobreak >nul
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11435 ^| findstr LISTENING') do (
        taskkill /PID %%a /F 2>nul
    )
) else (
    echo ✅ Port 11435 is free
)

echo.
echo Step 3: Testing SSH connection to Mac Studio...
echo.
set /p MAC_IP="Enter Mac Studio IP (e.g., 192.178.90.31): "
set /p MAC_USER="Enter Mac Studio username (e.g., rivemain): "

echo.
echo Testing SSH connection...
ssh -o ConnectTimeout=5 %MAC_USER%@%MAC_IP% "echo 'SSH connection successful'" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ❌ SSH connection failed!
    echo.
    echo Please check:
    echo 1. Mac Studio IP: %MAC_IP%
    echo 2. Username: %MAC_USER%
    echo 3. Mac Studio is accessible
    echo 4. SSH is enabled on Mac Studio
    echo.
    pause
    exit /b 1
)

echo ✅ SSH connection successful
echo.

echo Step 4: Testing Ollama on Mac Studio...
ssh %MAC_USER%@%MAC_IP% "curl -s http://localhost:11434/api/tags" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama is running on Mac Studio
) else (
    echo ⚠️  Could not verify Ollama on Mac Studio
    echo    (This might be okay, continuing...)
)

echo.
echo Step 5: Creating SSH tunnel...
echo Command: ssh -f -N -L 11435:localhost:11434 %MAC_USER%@%MAC_IP%
echo.

ssh -f -N -L 11435:localhost:11434 %MAC_USER%@%MAC_IP%

if %errorlevel% equ 0 (
    echo.
    echo ✅ SSH tunnel created
    echo.
    timeout /t 2 /nobreak >nul
    
    echo Step 6: Testing tunnel...
    curl -s http://localhost:11435/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Tunnel is working!
        echo.
        echo Test result:
        curl http://localhost:11435/api/tags
    ) else (
        echo ⚠️  Tunnel created but test failed
        echo.
        echo Try manually: curl http://localhost:11435/api/tags
        echo.
        echo If it still fails, check:
        echo 1. Mac Studio Ollama is running: ssh %MAC_USER%@%MAC_IP% "curl http://localhost:11434/api/tags"
        echo 2. SSH tunnel process: netstat -ano ^| findstr :11435
    )
) else (
    echo.
    echo ❌ SSH tunnel creation failed!
    echo.
    echo Please check your SSH credentials and Mac Studio accessibility.
)

echo.
pause

