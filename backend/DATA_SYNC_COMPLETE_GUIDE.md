# Complete Data Sync Guide - Dev & Production

## 📋 Overview

This guide documents the complete data synchronization system for loading data from Azure Blob Storage (`Biz-Pulse/yearly_data1.csv`) into MongoDB databases. The system supports both development (`bizpulseDev`) and production (`bizpulse`) databases.

## 🎯 Purpose

- Load data from Azure Blob Storage CSV file into MongoDB
- Support both development and production environments
- Handle data normalization and cleaning
- Verify data after loading
- Update production database with new data (including 2025 months)

---

## 📁 Files Created

### Development Scripts

| File | Purpose | Database |
|------|---------|----------|
| `sync_azure_data_dev.py` | Load data into development database | `bizpulseDev` |
| `verify_dev_db.py` | Verify data in development database | `bizpulseDev` |
| `check_azure_file.py` | Check if Azure file exists and show structure | N/A |

### Production Scripts

| File | Purpose | Database |
|------|---------|----------|
| `sync_azure_data_production.py` | Load data into production database | `bizpulse` (from .env) |
| `verify_production_db.py` | Verify data in production database | `bizpulse` (from .env) |

### Helper Scripts

| File | Purpose |
|------|---------|
| `run_all.ps1` | PowerShell script to run all dev steps |
| `run_all.bat` | Batch file to run all dev steps |

### Documentation Files

| File | Purpose |
|------|---------|
| `DATA_LOADING_INSTRUCTIONS.md` | Detailed instructions for dev database |
| `UPDATE_PRODUCTION_DB.md` | Instructions for production database |
| `QUICK_START_DEV_DB.md` | Quick reference for dev database |
| `RUN_COMMANDS.md` | Command reference |
| `DATA_SYNC_COMPLETE_GUIDE.md` | **This file - Complete reference** |

---

## 🔧 Environment Variables Required

Create/update `.env` file in `backend/` directory:

```env
# MongoDB Connection
MONGO_URL=your_mongodb_connection_string
DB_NAME=bizpulse              # For production: 'bizpulse'
                              # For development: 'bizpulseDev'

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
AZURE_CONTAINER_NAME=your_container_name
AZURE_BLOB_PATH=Biz-Pulse/yearly_data1.csv        # Production file path
AZURE_BLOB_PATH_DEV=Biz-Pulse/yearly_data1.csv     # Dev file path (optional)
```

### Important Notes:
- `DB_NAME` is read from `.env` file (not hardcoded)
- Scripts default to `bizpulse` if `DB_NAME` is not set
- Azure file path defaults to `Biz-Pulse/yearly_data1.csv` if not specified

---

## 🚀 Development Database Workflow

### Step 1: Check Azure File (Optional but Recommended)

**Command:**
```powershell
cd backend
python check_azure_file.py
```

**What it does:**
- Verifies file `Biz-Pulse/yearly_data1.csv` exists in Azure
- Shows file size and properties
- Displays CSV structure (columns, data types)
- Shows year distribution (should include 2025)
- Lists available files if target file not found

**Expected Output:**
```
✅ File FOUND: Biz-Pulse/yearly_data1.csv
📊 File Properties: Size, Last Modified
📋 COLUMNS IN CSV: (list of columns)
📅 YEARS IN DATA: [2023, 2024, 2025]
✅ 2025 DATA FOUND: XXXX records
```

**When to use:**
- Before loading data (verify file exists)
- To check CSV structure
- To verify 2025 data is present

---

### Step 2: Load Data into Development Database

**Prerequisites:**
- Set `DB_NAME=bizpulseDev` in `.env` file
- Azure file exists and is accessible

**Command:**
```powershell
cd backend
python sync_azure_data_dev.py
```

**What it does:**
1. Connects to MongoDB using `bizpulseDev` database
2. Downloads `Biz-Pulse/yearly_data1.csv` from Azure Blob Storage
3. Normalizes column names (Month → Month_Name, gSales → Revenue, etc.)
4. Cleans numeric columns (removes commas, converts to numbers)
5. **Deletes all existing data** in `bizpulseDev.business_data` collection
6. Inserts all records in batches of 5000
7. Shows progress and statistics
8. Verifies 2025 data is loaded

**Expected Output:**
```
📊 Connecting to MongoDB database: bizpulseDev
✅ Successfully connected to MongoDB
📥 Downloading CSV from Azure...
✅ Downloaded XXXX records from Azure
🔄 Normalizing column names...
🔢 Cleaning numeric columns...
🗑️  Clearing existing data in bizpulseDev.business_data...
💾 Inserting XXXX new records...
   ✅ Inserted 5000/XXXX records...
   ✅ Inserted 10000/XXXX records...
🎉 Successfully loaded XXXX records into bizpulseDev database!
✅ Found XXXX records for year 2025 (new data)
   2025 Months: ['January', 'February', 'March', ...]
```

**Time:** Usually 1-5 minutes depending on data size

**Important:**
- ⚠️ This will DELETE all existing data in `bizpulseDev.business_data`
- Production database (`bizpulse`) is NOT affected

---

### Step 3: Verify Development Data

**Command:**
```powershell
cd backend
python verify_dev_db.py
```

**What it does:**
- Checks total record count
- Shows year distribution (2023, 2024, 2025)
- Displays 2025 months list
- Shows sample 2025 record
- Lists unique values (businesses, channels, brands, categories)

**Expected Output:**
```
📊 Total Records: XXXX
📈 Year Distribution:
   2023: XXXX records
   2024: XXXX records
   2025: XXXX records
✅ 2025 Data: XXXX records
   2025 Months: ['January', 'February', ...]
```

---

### Quick Dev Workflow (All Steps)

**Option 1: Run individually**
```powershell
cd backend
python check_azure_file.py
python sync_azure_data_dev.py
python verify_dev_db.py
```

**Option 2: Use helper script (PowerShell)**
```powershell
cd backend
.\run_all.ps1
```

**Option 3: Use helper script (CMD)**
```cmd
cd backend
run_all.bat
```

---

## 🏭 Production Database Workflow

### Step 1: Update Production Database

**Prerequisites:**
- ✅ Tested data loading in `bizpulseDev` first
- ✅ Verified data is correct
- ✅ Set `DB_NAME=bizpulse` in `.env` file
- ✅ Azure file exists and is accessible

**Command:**
```powershell
cd backend
python sync_azure_data_production.py
```

**What it does:**
1. Reads `DB_NAME` from `.env` file (defaults to `bizpulse` if not set)
2. Connects to MongoDB using the database from `.env`
3. Downloads `Biz-Pulse/yearly_data1.csv` from Azure Blob Storage
4. Normalizes column names (same as dev)
5. Cleans numeric columns
6. **⚠️ DELETES all existing data** in production database
7. Inserts all new records in batches
8. Shows progress and statistics
9. Verifies 2025 data is loaded

**Expected Output:**
```
======================================================================
🚀 Azure Data Sync to PRODUCTION Database (bizpulse)
======================================================================
⚠️  WARNING: This will update the PRODUCTION database!
   - Database: bizpulse (from .env file)
   - Source: Biz-Pulse/yearly_data1.csv (with 2025 data)
   - Action: DELETE all existing data and load new data
======================================================================

⚠️  PRODUCTION DATABASE UPDATE
======================================================================
📊 Target Database: bizpulse (from .env file)
⚠️  This will DELETE all existing data in bizpulse.business_data
======================================================================
📊 Connecting to MongoDB database: bizpulse
✅ Successfully connected to MongoDB
📥 Downloading CSV from Azure...
✅ Downloaded XXXX records from Azure
🔄 Normalizing column names...
🔢 Cleaning numeric columns...
🗑️  Clearing existing PRODUCTION data in bizpulse.business_data...
💾 Inserting XXXX new records into bizpulse PRODUCTION database...
   ✅ Inserted 5000/XXXX records...
🎉 Successfully loaded XXXX records into bizpulse PRODUCTION database!
✅ Found XXXX records for year 2025 (new data)
```

**Time:** Usually 1-5 minutes depending on data size

**⚠️ CRITICAL WARNINGS:**
- This will **DELETE all existing production data**
- Make sure you've tested in dev first
- Verify data is correct before running
- Consider running during low-traffic periods

---

### Step 2: Verify Production Data

**Command:**
```powershell
cd backend
python verify_production_db.py
```

**What it does:**
- Checks total record count in production
- Shows year distribution
- Verifies 2025 data is present
- Displays 2025 months
- Shows sample records and statistics

**Expected Output:**
```
🔍 Verifying bizpulse PRODUCTION Database
📊 Total Records: XXXX
📈 Year Distribution:
   2023: XXXX records
   2024: XXXX records
   2025: XXXX records
✅ 2025 Data: XXXX records
   2025 Months: ['January', 'February', ...]
```

---

### Quick Production Workflow

```powershell
cd backend
python sync_azure_data_production.py
python verify_production_db.py
```

---

## 📊 Data Processing Details

### Column Normalization

The scripts normalize column names to match the expected schema:

| Original Column | Normalized Column |
|----------------|-------------------|
| `Month` / `Month Name` / `MonthName` | `Month_Name` |
| `Sub-Cat` / `Sub_Category` / `SubCat` | `Sub_Cat` |
| `Brand Type Name` / `Brand_Type` | `Brand_Type_Name` |
| `P+L Brand` / `PL Brand` | `PL_Brand` |
| `P+L Category` / `PL Category` | `PL_Category` |
| `P+L Cust. Grp` / `PL Cust Grp` | `PL_Cust_Grp` |
| `gSales` | `Revenue` |
| `fGP` | `Gross_Profit` |
| `Cases` | `Units` |

### Numeric Cleaning

- Removes commas from numbers (e.g., "1,000" → 1000)
- Converts to proper numeric types
- Handles missing values (fills with 0)
- Processes: `Revenue`, `Gross_Profit`, `Units`, `Year`

### Batch Processing

- Inserts data in batches of 5000 records
- Shows progress after each batch
- Handles errors gracefully
- Continues even if one batch fails (with error logging)

---

## 🔄 Switching Between Dev and Production

### To Work with Development Database

1. **Update `.env` file:**
   ```env
   DB_NAME=bizpulseDev
   ```

2. **Run dev scripts:**
   ```powershell
   python sync_azure_data_dev.py
   python verify_dev_db.py
   ```

### To Work with Production Database

1. **Update `.env` file:**
   ```env
   DB_NAME=bizpulse
   ```

2. **Run production scripts:**
   ```powershell
   python sync_azure_data_production.py
   python verify_production_db.py
   ```

**Note:** Both scripts read `DB_NAME` from `.env`, so you can use either script with any database by changing `.env`.

---

## 📝 Complete Command Reference

### Development Commands

```powershell
# Check Azure file
cd backend
python check_azure_file.py

# Load dev data
python sync_azure_data_dev.py

# Verify dev data
python verify_dev_db.py

# Or run all at once
.\run_all.ps1
```

### Production Commands

```powershell
# Load production data
cd backend
python sync_azure_data_production.py

# Verify production data
python verify_production_db.py
```

### Quick Reference Table

| Task | Command | Database |
|------|---------|----------|
| Check Azure file | `python check_azure_file.py` | N/A |
| Load dev data | `python sync_azure_data_dev.py` | `bizpulseDev` |
| Verify dev data | `python verify_dev_db.py` | `bizpulseDev` |
| Load production data | `python sync_azure_data_production.py` | `bizpulse` (from .env) |
| Verify production data | `python verify_production_db.py` | `bizpulse` (from .env) |

---

## 🐛 Troubleshooting

### Error: "MONGO_URL not found"
**Solution:**
- Check `.env` file exists in `backend/` directory
- Verify `MONGO_URL` is set correctly
- Ensure `.env` file is not corrupted

### Error: "Azure Storage configuration not found"
**Solution:**
- Check `AZURE_STORAGE_CONNECTION_STRING` is set
- Verify `AZURE_CONTAINER_NAME` is set
- Ensure Azure credentials are correct

### Error: "Blob not found: Biz-Pulse/yearly_data1.csv"
**Solution:**
- Run `python check_azure_file.py` to see available files
- Verify file path in Azure Portal
- Check file name is correct (case-sensitive)
- Verify you have read permissions

### Error: "ModuleNotFoundError: No module named 'pandas'"
**Solution:**
```powershell
cd backend
python -m pip install pandas motor azure-storage-blob python-dotenv
```

### Error: "Required column missing"
**Solution:**
- Check CSV file structure
- Verify column names match expected format
- Run `python check_azure_file.py` to see actual columns
- Update column mapping if needed

### Database Connection Issues
**Solution:**
- Verify MongoDB connection string is correct
- Check network connectivity
- Verify database permissions
- Test connection with MongoDB Compass or CLI

### Data Not Loading
**Solution:**
- Check error messages in console output
- Verify CSV file is not corrupted
- Check MongoDB has enough storage
- Review batch insertion errors

---

## 🔄 Future Updates

### To Update Data in Future

1. **Upload new CSV file to Azure:**
   - Upload to: `Biz-Pulse/yearly_data1.csv` (or update path in `.env`)

2. **For Development:**
   ```powershell
   cd backend
   # Update .env: DB_NAME=bizpulseDev
   python sync_azure_data_dev.py
   python verify_dev_db.py
   ```

3. **For Production:**
   ```powershell
   cd backend
   # Update .env: DB_NAME=bizpulse
   python sync_azure_data_production.py
   python verify_production_db.py
   ```

### To Change Database Name

1. **Update `.env` file:**
   ```env
   DB_NAME=your_new_database_name
   ```

2. **Run scripts** (they will use the new database name)

### To Change Azure File Path

1. **Update `.env` file:**
   ```env
   AZURE_BLOB_PATH=Biz-Pulse/your_new_file.csv
   # Or for dev:
   AZURE_BLOB_PATH_DEV=Biz-Pulse/your_new_file.csv
   ```

2. **Run scripts** (they will use the new file path)

### To Add New Column Normalization

1. **Edit the script** (`sync_azure_data_dev.py` or `sync_azure_data_production.py`)

2. **Update `rename_map` dictionary:**
   ```python
   rename_map = {
       # ... existing mappings ...
       'New_Column': 'Normalized_Column',
   }
   ```

3. **Save and run the script**

---

## 📋 Checklist for Production Update

Before updating production, verify:

- [ ] Data tested in `bizpulseDev` database
- [ ] Data verified and correct
- [ ] `DB_NAME=bizpulse` in `.env` file
- [ ] Azure file exists and is accessible
- [ ] MongoDB connection is working
- [ ] Backup created (if needed)
- [ ] Low-traffic period (if applicable)
- [ ] Team notified (if applicable)

After updating production, verify:

- [ ] Script completed successfully
- [ ] Total record count is correct
- [ ] 2025 data is present
- [ ] Application works correctly
- [ ] Filters show 2025 and new months
- [ ] Charts display correctly
- [ ] No errors in application logs

---

## 📚 Additional Documentation

- **`DATA_LOADING_INSTRUCTIONS.md`** - Detailed dev database instructions
- **`UPDATE_PRODUCTION_DB.md`** - Production database update guide
- **`QUICK_START_DEV_DB.md`** - Quick reference for dev
- **`RUN_COMMANDS.md`** - Command reference

---

## 🔐 Security Notes

1. **Never commit `.env` file** to version control
2. **Protect Azure connection strings** - they provide access to your storage
3. **Use environment-specific credentials** for dev and production
4. **Limit database permissions** - scripts only need read/write to `business_data` collection
5. **Review logs** for any suspicious activity

---

## 📞 Support

If you encounter issues:

1. **Check error messages** in console output
2. **Review troubleshooting section** above
3. **Verify environment variables** are correct
4. **Check Azure file** exists and is accessible
5. **Test MongoDB connection** separately
6. **Review script logs** for detailed error information

---

## 📝 Summary

### Development Workflow
```powershell
# 1. Check file
python check_azure_file.py

# 2. Load data (DB_NAME=bizpulseDev in .env)
python sync_azure_data_dev.py

# 3. Verify
python verify_dev_db.py
```

### Production Workflow
```powershell
# 1. Load data (DB_NAME=bizpulse in .env)
python sync_azure_data_production.py

# 2. Verify
python verify_production_db.py
```

### Key Points
- ✅ All scripts read `DB_NAME` from `.env` file
- ✅ Same data processing for dev and production
- ✅ Scripts delete existing data before inserting new
- ✅ Batch processing (5000 records at a time)
- ✅ Comprehensive error handling and logging
- ✅ Verification scripts to confirm data loaded correctly

---

**Last Updated:** 2025
**Version:** 1.0
**Maintained By:** Development Team

