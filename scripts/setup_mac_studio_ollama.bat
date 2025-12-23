@echo off
echo ========================================
echo Setting up Mac Studio Ollama connection
echo ========================================
echo.

echo Step 1: Stopping Ollama service...
net stop Ollama 2>nul
sc config Ollama start= disabled 2>nul
if %errorlevel% equ 0 (
    echo ✅ Ollama service disabled.
) else (
    echo ⚠️  Could not disable service (may need admin rights)
)

echo.
echo Step 2: Killing Ollama processes...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul
echo ✅ Ollama processes stopped.

echo.
echo Step 3: Checking port 11434...
netstat -ano | findstr :11434 >nul
if %errorlevel% equ 0 (
    echo ⚠️  WARNING: Port 11434 still in use!
    echo    You may need to restart your computer or use port 11435.
    echo.
    set USE_PORT=11435
) else (
    echo ✅ Port 11434 is free!
    set USE_PORT=11434
)

echo.
echo Step 4: Creating SSH tunnel on port %USE_PORT%...
echo Command: ssh -f -N -L %USE_PORT%:localhost:11434 rivemain@192.178.90.31
echo.
echo NOTE: You will be prompted for SSH password
echo.

ssh -f -N -L %USE_PORT%:localhost:11434 rivemain@192.178.90.31

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ Setup complete!
    echo ========================================
    echo.
    echo SSH tunnel created on port %USE_PORT%
    echo.
    echo Test with: curl http://localhost:%USE_PORT%/api/tags
    echo.
    echo Update your .env file:
    echo OLLAMA_BASE_URL=http://localhost:%USE_PORT%
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

