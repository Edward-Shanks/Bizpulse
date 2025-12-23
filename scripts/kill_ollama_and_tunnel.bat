@echo off
echo ========================================
echo Killing all processes on port 11434...
echo ========================================

:kill_loop
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11434 ^| findstr LISTENING') do (
    echo Killing PID %%a
    taskkill /PID %%a /F 2>nul
)
timeout /t 1 /nobreak >nul
netstat -ano | findstr :11434 >nul
if %errorlevel% equ 0 (
    echo Port still in use, retrying...
    goto kill_loop
)

echo.
echo ========================================
echo Port 11434 is now free!
echo ========================================
echo.
echo Starting SSH tunnel to Mac Studio...
echo Command: ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
echo.
echo NOTE: Replace rivemain@192.178.90.31 with your actual Mac Studio credentials
echo.

ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SSH tunnel created successfully!
    echo ========================================
    echo.
    echo Test with: curl http://localhost:11434/api/tags
) else (
    echo.
    echo ========================================
    echo SSH tunnel failed!
    echo ========================================
    echo.
    echo Please check:
    echo 1. Mac Studio IP address is correct
    echo 2. SSH credentials are correct
    echo 3. Mac Studio is accessible
)

pause

