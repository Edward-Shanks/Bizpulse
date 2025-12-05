# Quick Reference Card - Data Sync Commands

## 🚀 Quick Commands

### Development Database (bizpulseDev)

```powershell
cd backend

# Check Azure file
python check_azure_file.py

# Load data
python sync_azure_data_dev.py

# Verify data
python verify_dev_db.py

# Or run all at once
.\run_all.ps1
```

### Production Database (bizpulse)

```powershell
cd backend

# Load data
python sync_azure_data_production.py

# Verify data
python verify_production_db.py
```

---

## 📋 Environment Variables (.env file)

```env
MONGO_URL=your_mongodb_connection_string
DB_NAME=bizpulse              # or bizpulseDev
AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
AZURE_CONTAINER_NAME=your_container_name
AZURE_BLOB_PATH=Biz-Pulse/yearly_data1.csv
```

---

## 📁 Script Files

| Script | Purpose | Database |
|--------|---------|----------|
| `check_azure_file.py` | Check if Azure file exists | N/A |
| `sync_azure_data_dev.py` | Load data to dev | `bizpulseDev` (from .env) |
| `verify_dev_db.py` | Verify dev data | `bizpulseDev` (from .env) |
| `sync_azure_data_production.py` | Load data to production | `bizpulse` (from .env) |
| `verify_production_db.py` | Verify production data | `bizpulse` (from .env) |

---

## ⚠️ Important Notes

- **All scripts read `DB_NAME` from `.env` file**
- **Scripts DELETE existing data before inserting new**
- **Test in dev first before updating production**
- **Production update takes 1-5 minutes**

---

## 🔄 Switch Database

Change `DB_NAME` in `.env`:
- `DB_NAME=bizpulseDev` → Development
- `DB_NAME=bizpulse` → Production

---

## 📚 Full Documentation

See `DATA_SYNC_COMPLETE_GUIDE.md` for complete details.

