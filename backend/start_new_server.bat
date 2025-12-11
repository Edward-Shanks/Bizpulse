@echo off
REM Batch script to start the new backend server
REM Run this script from the backend directory

echo ========================================
echo Starting BizPulse Backend Server
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create venv first: python -m venv venv
    pause
    exit /b 1
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

echo Virtual environment activated!
echo.

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Server may not start correctly without environment variables.
    echo.
)

REM Start server
echo Starting server on http://0.0.0.0:8000...
echo Press CTRL+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause



