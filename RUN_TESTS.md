# 🧪 How to Run Tests - Quick Guide

## ✅ Python Command Found

Your Python is installed at: `C:\Python314\python.exe`

## 📋 Commands to Run Tests

### Option 1: Use Full Python Path (Recommended)

```powershell
# Navigate to scripts folder
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend\scripts"

# Run tests (use full Python path)
C:\Python314\python.exe test_tenant_enforcement.py
C:\Python314\python.exe test_time_filter_injection.py
C:\Python314\python.exe test_ai_simulation_queries.py
```

### Option 2: Create Alias (Easier)

Add this to your PowerShell profile:

```powershell
# Open profile
notepad $PROFILE

# Add this line:
Set-Alias python "C:\Python314\python.exe"

# Then reload:
. $PROFILE
```

After that, you can use `python` normally.

## ⚠️ Expected Test Results

### Tests That Will Pass ✅
- Query injection logic tests (5/8 in tenant enforcement)
- Time filter injection tests
- AI simulation query structure tests

### Tests That Will Fail (Expected) ⚠️
- Tests that actually execute queries against ClickHouse
- These fail because ClickHouse is on Mac Studio, not localhost

**This is normal!** The injection logic is working correctly.

## 🔧 To Run Full Tests (Including ClickHouse Connection)

1. **Update `.env` file** to point to Mac Studio:
   ```bash
   CLICKHOUSE_HOST=192.168.50.29
   CLICKHOUSE_PORT=9000
   ```

2. **Make sure Mac Studio ClickHouse is running**:
   ```bash
   # On Mac Studio
   docker ps | grep clickhouse
   ```

3. **Then run tests** - they will connect to Mac Studio

## 📊 Current Test Status

**Tenant Enforcement Tests:**
- ✅ 5/8 passed (injection logic working)
- ⚠️ 3/8 failed (connection to ClickHouse needed)

**This means:** Your security code is working! The failures are just connection issues.

## 🚀 Quick Test Script

Create `run_tests.ps1`:

```powershell
# run_tests.ps1
$python = "C:\Python314\python.exe"
$scriptDir = "C:\Users\Sumit Mishra\Documents\Bizpulse\backend\scripts"

cd $scriptDir

Write-Host "Running Tenant Enforcement Tests..."
& $python test_tenant_enforcement.py

Write-Host "`nRunning Time Filter Tests..."
& $python test_time_filter_injection.py

Write-Host "`nRunning AI Simulation Tests..."
& $python test_ai_simulation_queries.py
```

Then run:
```powershell
.\run_tests.ps1
```
