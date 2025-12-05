# Quick Start: Load Data into bizpulseDev Database

## 🎯 Goal
Load data from `Biz-Pulse/yearly_data1.csv` (Azure) into `bizpulseDev` MongoDB database.

## ✅ Prerequisites Check

1. **Environment Variables** - Your `.env` file should have:
   ```env
   DB_NAME=bizpulseDev
   MONGO_URL=your_mongodb_connection_string
   AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
   AZURE_CONTAINER_NAME=your_container_name
   ```

2. **Azure File** - Verify file exists:
   ```bash
   python check_azure_file.py
   ```

## 🚀 Quick Steps

### Step 1: Check Azure File (Optional but Recommended)
```bash
cd backend
python check_azure_file.py
```
This will verify the file exists and show its structure.

### Step 2: Load Data
```bash
cd backend
python sync_azure_data_dev.py
```

### Step 3: Verify Data
```bash
cd backend
python verify_dev_db.py
```

## 📋 What Each Script Does

| Script | Purpose |
|--------|---------|
| `check_azure_file.py` | Checks if `Biz-Pulse/yearly_data1.csv` exists in Azure and shows file structure |
| `sync_azure_data_dev.py` | **Main script** - Downloads CSV from Azure and loads into `bizpulseDev` database |
| `verify_dev_db.py` | Verifies data was loaded correctly, shows statistics |

## ⚠️ Important Notes

- **This will DELETE all existing data** in `bizpulseDev.business_data` collection
- **Production database (`bizpulse`) is NOT affected**
- The script uses the same data processing as production
- Database `bizpulseDev` will be created automatically if it doesn't exist

## 🔍 Expected Output

When successful, you'll see:
```
✅ Successfully loaded XXXX records into bizpulseDev database!
✅ Found XXXX records for year 2025 (new data)
   2025 Months: ['January', 'February', 'March', ...]
```

## 🐛 Troubleshooting

**File not found?**
- Run `python check_azure_file.py` to see available files
- Verify file path in Azure Portal

**Connection errors?**
- Check `.env` file has correct values
- Verify MongoDB connection string
- Verify Azure connection string

**Need more details?**
- See `DATA_LOADING_INSTRUCTIONS.md` for complete guide

