@echo off
REM Batch script to start the backend server on Windows

echo Stopping existing server processes on port 8000...

REM Find and stop processes using port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

REM Wait a moment
timeout /t 2 /nobreak >nul

echo Starting backend server...

REM Change to backend directory
cd /d "%~dp0"

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo Warning: Virtual environment not found. Make sure dependencies are installed.
)

REM Start the server
echo Starting uvicorn server:app on port 8000...
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

pause

