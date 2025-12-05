@echo off
echo ========================================
echo Loading Data into bizpulseDev Database
echo ========================================
echo.

echo Step 1: Checking Azure file...
python check_azure_file.py
if errorlevel 1 (
    echo.
    echo ERROR: Azure file check failed!
    echo Please verify the file exists in Azure.
    pause
    exit /b 1
)
echo.

echo Step 2: Loading data into bizpulseDev database...
python sync_azure_data_dev.py
if errorlevel 1 (
    echo.
    echo ERROR: Data loading failed!
    pause
    exit /b 1
)
echo.

echo Step 3: Verifying data...
python verify_dev_db.py
if errorlevel 1 (
    echo.
    echo WARNING: Verification had issues, but data may still be loaded.
)
echo.

echo ========================================
echo All steps completed!
echo ========================================
pause

