# Update Production Database (bizpulse)

## ⚠️ IMPORTANT WARNING

This script will **DELETE all existing data** in the `bizpulse` production database and replace it with data from `Biz-Pulse/yearly_data1.csv`.

**Make sure you:**
- ✅ Have tested the data loading in `bizpulseDev` first
- ✅ Verified the data is correct
- ✅ Have a backup if needed
- ✅ Are ready to update production

## What This Does

1. Connects to **bizpulse** database (PRODUCTION)
2. Downloads `Biz-Pulse/yearly_data1.csv` from Azure (includes 2025 data)
3. **Deletes all existing data** in `bizpulse.business_data` collection
4. Loads all new data from the CSV file
5. Verifies the data was loaded correctly

## Prerequisites

1. **Environment Variables** - Your `.env` file should have:
   ```env
   DB_NAME=bizpulse  # Or leave it, script uses 'bizpulse' by default
   MONGO_URL=your_mongodb_connection_string
   AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
   AZURE_CONTAINER_NAME=your_container_name
   AZURE_BLOB_PATH=Biz-Pulse/yearly_data1.csv  # Optional, defaults to this
   ```

2. **Azure File** - File `Biz-Pulse/yearly_data1.csv` must exist in Azure

## Command to Run

```powershell
cd backend
python sync_azure_data_production.py
```

## Expected Output

```
======================================================================
🚀 Azure Data Sync to PRODUCTION Database (bizpulse)
======================================================================
⚠️  WARNING: This will update the PRODUCTION database!
   - Database: bizpulse (PRODUCTION)
   - Source: Biz-Pulse/yearly_data1.csv (with 2025 data)
   - Action: DELETE all existing data and load new data
======================================================================

⚠️  PRODUCTION DATABASE UPDATE
======================================================================
📊 Target Database: bizpulse (PRODUCTION)
⚠️  This will DELETE all existing data in bizpulse.business_data
======================================================================
📊 Connecting to MongoDB database: bizpulse
✅ Successfully connected to MongoDB
📥 Downloading CSV from Azure...
   Container: your-container
   Blob Path: Biz-Pulse/yearly_data1.csv
✅ Downloaded XXXX records from Azure
🔄 Normalizing column names...
🔢 Cleaning numeric columns...
🗑️  Clearing existing PRODUCTION data in bizpulse.business_data...
   Deleted X existing records
💾 Inserting XXXX new records into PRODUCTION database...
   ✅ Inserted 5000/XXXX records...
   ✅ Inserted 10000/XXXX records...
   ...

🎉 Successfully loaded XXXX records into bizpulse PRODUCTION database!

📊 Verifying data...
   Total records in database: XXXX

📈 Year Distribution:
   2023: XXXX records, Revenue: €XXX, Cases: XXX
   2024: XXXX records, Revenue: €XXX, Cases: XXX
   2025: XXXX records, Revenue: €XXX, Cases: XXX

✅ Found XXXX records for year 2025 (new data)
   2025 Months: ['January', 'February', 'March', ...]

✅ Production database update completed successfully!
======================================================================
⚠️  PRODUCTION DATABASE HAS BEEN UPDATED
======================================================================
```

## Verification After Update

After running the script, verify the production database:

```powershell
cd backend
python verify_production_db.py
```

Or manually check:
- Total record count
- 2025 data is present
- All years are correct
- Application works with new data

## Differences from Dev Script

| Feature | Dev Script | Production Script |
|---------|-----------|-------------------|
| Database | `bizpulseDev` | `bizpulse` (hardcoded) |
| Warnings | Standard | Extra warnings for production |
| File Path | `Biz-Pulse/yearly_data1.csv` | `Biz-Pulse/yearly_data1.csv` |
| Data Processing | Same | Same |

## Safety Notes

1. **Backup First** (if needed):
   - The script deletes all existing data
   - If you need a backup, export data before running

2. **Test First**:
   - Always test in `bizpulseDev` first
   - Verify data is correct before updating production

3. **Timing**:
   - Run during low-traffic periods if possible
   - The update takes 1-5 minutes depending on data size

4. **Verification**:
   - Always verify data after update
   - Check application works correctly
   - Verify 2025 data appears in filters

## Troubleshooting

**Connection errors?**
- Check MongoDB connection string
- Verify network connectivity
- Check database permissions

**File not found?**
- Verify `Biz-Pulse/yearly_data1.csv` exists in Azure
- Check Azure connection string
- Verify container name

**Data issues?**
- Check CSV file structure
- Verify column names match expected format
- Review error messages in output

## Rollback (if needed)

If something goes wrong:
1. Check error messages
2. Re-run the script (it will reload data)
3. Or restore from backup if you created one

---

**Ready to update production?** Run: `python sync_azure_data_production.py`

