# PowerShell script to run all data loading steps
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Loading Data into bizpulseDev Database" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Azure file
Write-Host "Step 1: Checking Azure file..." -ForegroundColor Yellow
python check_azure_file.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Azure file check failed!" -ForegroundColor Red
    Write-Host "Please verify the file exists in Azure." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 2: Load data
Write-Host "Step 2: Loading data into bizpulseDev database..." -ForegroundColor Yellow
python sync_azure_data_dev.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Data loading failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 3: Verify data
Write-Host "Step 3: Verifying data..." -ForegroundColor Yellow
python verify_dev_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Verification had issues, but data may still be loaded." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "All steps completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Read-Host "Press Enter to exit"

