# Data Loading Instructions for bizpulseDev Database

## Overview
This guide explains how to load data from the new Azure CSV file (`Biz-Pulse/yearly_data1.csv`) into the new development database (`bizpulseDev`).

## Prerequisites

1. **Environment Variables Setup**
   - Ensure your `.env` file has:
     ```env
     MONGO_URL=your_mongodb_connection_string
     DB_NAME=bizpulseDev
     AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
     AZURE_CONTAINER_NAME=your_container_name
     AZURE_BLOB_PATH_DEV=Biz-Pulse/yearly_data1.csv
     ```
   
   **Note:** The script will use `AZURE_BLOB_PATH_DEV` if set, otherwise defaults to `Biz-Pulse/yearly_data1.csv`

2. **MongoDB Database**
   - The database `bizpulseDev` will be created automatically when you run the script
   - No need to create it manually in MongoDB Atlas

3. **Azure Blob Storage**
   - File must be uploaded to: `Biz-Pulse/yearly_data1.csv`
   - Verify the file exists in your Azure container

## Step-by-Step Instructions

### Step 1: Verify Environment Variables

Check your `.env` file in the `backend` directory:

```bash
cd backend
# Check if .env file has correct values
```

Required variables:
- `MONGO_URL` - MongoDB connection string
- `DB_NAME=bizpulseDev` - Development database name
- `AZURE_STORAGE_CONNECTION_STRING` - Azure storage connection
- `AZURE_CONTAINER_NAME` - Azure container name
- `AZURE_BLOB_PATH_DEV=Biz-Pulse/yearly_data1.csv` (optional, defaults to this)

### Step 2: Verify Azure File Exists

Run the verification script to check if the file exists:

```bash
cd backend
python verify_azure_data.py
```

Or manually check in Azure Portal that `Biz-Pulse/yearly_data1.csv` exists.

### Step 3: Load Data into Development Database

Run the sync script:

```bash
cd backend
python sync_azure_data_dev.py
```

**What this script does:**
1. ✅ Connects to MongoDB using `bizpulseDev` database
2. ✅ Downloads `Biz-Pulse/yearly_data1.csv` from Azure Blob Storage
3. ✅ Normalizes column names (same as production)
4. ✅ Cleans numeric columns (removes commas, converts to numbers)
5. ✅ Clears existing data in `bizpulseDev.business_data` collection
6. ✅ Inserts all records in batches of 5000
7. ✅ Verifies the data and shows statistics

### Step 4: Verify Data Loaded Correctly

Run the verification script:

```bash
cd backend
python verify_dev_db.py
```

This will show:
- Total record count
- Year distribution (including 2025)
- 2025 months data
- Sample records
- Unique values for businesses, channels, brands, categories

## Expected Output

When you run `sync_azure_data_dev.py`, you should see:

```
============================================================
🚀 Azure Data Sync to Development Database (bizpulseDev)
============================================================
This script will:
  1. Connect to MongoDB (bizpulseDev database)
  2. Download yearly_data1.csv from Azure Blob Storage
  3. Load all data into the development database
============================================================

📊 Connecting to MongoDB database: bizpulseDev
✅ Successfully connected to MongoDB
📥 Downloading CSV from Azure...
   Container: your-container
   Blob Path: Biz-Pulse/yearly_data1.csv
✅ Downloaded XXXX records from Azure
🔄 Normalizing column names...
🔢 Cleaning numeric columns...
🗑️  Clearing existing data in bizpulseDev.business_data...
   Deleted X existing records
💾 Inserting XXXX new records...
   ✅ Inserted 5000/XXXX records...
   ✅ Inserted 10000/XXXX records...
   ...

🎉 Successfully loaded XXXX records into bizpulseDev database!

📊 Verifying data...
   Total records in database: XXXX

📈 Year Distribution:
   2023: XXXX records, Revenue: €XXX, Cases: XXX
   2024: XXXX records, Revenue: €XXX, Cases: XXX
   2025: XXXX records, Revenue: €XXX, Cases: XXX

✅ Found XXXX records for year 2025 (new data)
   2025 Months: ['January', 'February', 'March', ...]

✅ Data sync completed successfully!
```

## Troubleshooting

### Error: "MONGO_URL not found"
- Check your `.env` file exists in `backend/` directory
- Verify `MONGO_URL` is set correctly

### Error: "Azure Storage configuration not found"
- Check `AZURE_STORAGE_CONNECTION_STRING` is set
- Check `AZURE_CONTAINER_NAME` is set

### Error: "Blob not found: Biz-Pulse/yearly_data1.csv"
- Verify the file exists in Azure Blob Storage
- Check the file path is correct (case-sensitive)
- Verify you have read permissions

### Error: "Required column missing"
- The CSV might have different column names
- Check the CSV file structure
- The script will show available columns if this error occurs

### Database Connection Issues
- Verify MongoDB connection string is correct
- Check network connectivity
- Verify database permissions

## Data Processing Details

The script performs the same data processing as production:

1. **Column Normalization:**
   - `Month` → `Month_Name`
   - `Sub-Cat` → `Sub_Cat`
   - `gSales` → `Revenue`
   - `fGP` → `Gross_Profit`
   - `Cases` → `Units`

2. **Numeric Cleaning:**
   - Removes commas from numbers
   - Converts to proper numeric types
   - Handles missing values (fills with 0)

3. **Batch Insertion:**
   - Inserts in batches of 5000 records
   - Shows progress during insertion
   - Handles errors gracefully

## Verification Checklist

After loading, verify:

- [ ] Total record count matches CSV row count
- [ ] 2025 data is present
- [ ] 2025 months are correct (should include new months)
- [ ] Revenue, Profit, and Cases totals are reasonable
- [ ] No duplicate records
- [ ] All required columns are present

## Next Steps

After data is loaded:

1. **Test the Application:**
   - Update your `.env` to use `DB_NAME=bizpulseDev`
   - Start the backend server
   - Test all screens with the new 2025 data

2. **Verify Filters:**
   - Check that 2025 appears in year filters
   - Verify new months appear in month filters
   - Test all filter combinations

3. **Check Data Accuracy:**
   - Compare totals with source data
   - Verify charts display correctly
   - Check that all screens load properly

## Important Notes

⚠️ **This script will DELETE all existing data in `bizpulseDev.business_data` collection before inserting new data.**

✅ **The production database (`bizpulse`) is NOT affected** - this only works with `bizpulseDev`.

✅ **The script uses the same data processing logic as production**, so data format will be consistent.

## Files Created

- `sync_azure_data_dev.py` - Main script to load data from Azure to bizpulseDev
- `verify_dev_db.py` - Script to verify data in bizpulseDev database

## Support

If you encounter issues:
1. Check the error messages in the console
2. Verify environment variables are correct
3. Check Azure file exists and is accessible
4. Verify MongoDB connection is working
5. Review the troubleshooting section above

