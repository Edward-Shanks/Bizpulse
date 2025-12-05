# Commands to Run Data Loading Scripts

## 📋 All Commands in Order

### Step 1: Navigate to Backend Directory
```powershell
cd backend
```

### Step 2: Check Azure File (Optional - Recommended First)
```powershell
python check_azure_file.py
```

**What it does:** Verifies the file `Biz-Pulse/yearly_data1.csv` exists in Azure and shows its structure.

**Expected output:**
- ✅ File FOUND message
- File size and properties
- Column list
- Sample data
- Year distribution (should show 2025)

---

### Step 3: Load Data into bizpulseDev Database
```powershell
python sync_azure_data_dev.py
```

**What it does:** Downloads CSV from Azure and loads all data into `bizpulseDev` database.

**Expected output:**
- Connection to MongoDB
- Download progress
- Data processing steps
- Insertion progress (batches of 5000)
- Final statistics with 2025 data

**Time:** Usually takes 1-5 minutes depending on data size.

---

### Step 4: Verify Data Loaded Correctly
```powershell
python verify_dev_db.py
```

**What it does:** Checks the data in `bizpulseDev` database and shows statistics.

**Expected output:**
- Total record count
- Year distribution (2023, 2024, 2025)
- 2025 months list
- Sample 2025 record
- Unique values count

---

## 🚀 Complete Command Sequence (Copy & Paste)

```powershell
# Navigate to backend directory
cd backend

# Step 1: Check Azure file exists
python check_azure_file.py

# Step 2: Load data into bizpulseDev
python sync_azure_data_dev.py

# Step 3: Verify data loaded
python verify_dev_db.py
```

---

## 🔄 If You Need to Re-run

If you need to reload the data (e.g., after updating the CSV file):

```powershell
cd backend
python sync_azure_data_dev.py
```

**Note:** This will delete existing data and reload everything.

---

## 🐛 Troubleshooting Commands

### Check Python is Available
```powershell
python --version
```

### Check if Required Packages are Installed
```powershell
python -c "import pandas; import motor; from azure.storage.blob import BlobServiceClient; print('All packages installed')"
```

### Check Environment Variables are Loaded
```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('MONGO_URL:', 'SET' if os.getenv('MONGO_URL') else 'NOT SET'); print('DB_NAME:', os.getenv('DB_NAME', 'NOT SET')); print('AZURE_CONTAINER_NAME:', 'SET' if os.getenv('AZURE_CONTAINER_NAME') else 'NOT SET')"
```

---

## 📝 Alternative: Run All in One Go

You can create a batch file to run all commands sequentially:

**Create `run_all.bat` in backend folder:**
```batch
@echo off
echo ========================================
echo Loading Data into bizpulseDev Database
echo ========================================
echo.

echo Step 1: Checking Azure file...
python check_azure_file.py
echo.

echo Step 2: Loading data...
python sync_azure_data_dev.py
echo.

echo Step 3: Verifying data...
python verify_dev_db.py
echo.

echo ========================================
echo All steps completed!
echo ========================================
pause
```

Then run:
```powershell
cd backend
.\run_all.bat
```

---

## ⚡ Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `python check_azure_file.py` | Check if Azure file exists | Before loading data |
| `python sync_azure_data_dev.py` | Load data into database | Main data loading step |
| `python verify_dev_db.py` | Verify data loaded | After loading to confirm |

---

## 💡 Tips

1. **Run in order:** Check → Load → Verify
2. **Check first:** Always run `check_azure_file.py` first to ensure file exists
3. **Wait for completion:** Don't interrupt the loading process
4. **Check output:** Look for ✅ success messages and error ❌ messages

---

## 📊 Expected Results

After running all commands successfully, you should see:

✅ **check_azure_file.py:**
- File found message
- 2025 data present
- File structure shown

✅ **sync_azure_data_dev.py:**
- "Successfully loaded XXXX records"
- "Found XXXX records for year 2025"
- Year distribution shown

✅ **verify_dev_db.py:**
- Total records count
- 2025 data confirmed
- 2025 months listed

