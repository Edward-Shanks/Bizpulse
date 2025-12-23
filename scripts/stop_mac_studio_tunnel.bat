@echo off
echo ========================================
echo Stopping Mac Studio Ollama Tunnel
echo ========================================
echo.

echo Finding SSH tunnel on port 11435...
netstat -ano | findstr :11435 >nul

if %errorlevel% equ 0 (
    echo Found tunnel, stopping...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11435 ^| findstr LISTENING') do (
        echo Stopping PID %%a
        taskkill /PID %%a /F 2>nul
    )
    timeout /t 1 /nobreak >nul
    
    netstat -ano | findstr :11435 >nul
    if %errorlevel% equ 0 (
        echo ⚠️  Tunnel still active, may need manual cleanup
    ) else (
        echo ✅ Tunnel stopped successfully
    )
) else (
    echo ℹ️  No tunnel found on port 11435
)

echo.
pause

