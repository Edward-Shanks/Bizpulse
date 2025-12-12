@echo off
REM Stop Server Script (Batch version)
REM Stops all Python/uvicorn processes and frees port 8000

echo 🛑 Stopping all server processes...

REM Find and stop processes using port 8000
echo.
echo 📊 Checking port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    echo   Stopping process %%a...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo   ⚠️  Could not stop process %%a
    ) else (
        echo   ✅ Stopped process %%a
    )
)

REM Find and stop Python processes
echo.
echo 🐍 Checking Python processes...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /V "INFO:"') do (
    echo   Stopping Python process %%a...
    taskkill /F /IM python.exe >nul 2>&1
)

for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV ^| findstr /V "INFO:"') do (
    echo   Stopping Pythonw process %%a...
    taskkill /F /IM pythonw.exe >nul 2>&1
)

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Verify port 8000
echo.
echo 🔍 Verifying port 8000 is free...
netstat -ano | findstr ":8000" >nul
if errorlevel 1 (
    echo   ✅ Port 8000 is now free
) else (
    echo   ⚠️  Port 8000 is still in use!
    echo   You may need to wait a few seconds
)

echo.
echo ✅ Done! All server processes have been stopped.
pause

