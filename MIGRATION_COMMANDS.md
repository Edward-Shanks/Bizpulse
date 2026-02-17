# 🚀 Migration Commands: MongoDB → ClickHouse

**Status:** ✅ All fixes applied, ready to migrate data  
**Source:** MongoDB `business_data` collection  
**Target:** ClickHouse `sales_analytics` table

---

## ✅ Pre-Migration Checklist

Before running migration, verify:

- [x] ✅ ClickHouse table `sales_analytics` created (on Mac Studio)
- [x] ✅ `.env` file has correct ClickHouse settings
- [x] ✅ MongoDB `business_data` has data
- [x] ✅ Python can connect to ClickHouse (tested)

---

## 📋 Step 1: Verify `.env` Configuration (On Laptop)

**File:** `backend\.env`

**Required settings:**

```env
# MongoDB (Local on Laptop)
MONGO_URL=mongodb://localhost:27017
DB_NAME=bizpulse

# ClickHouse (Remote on Mac Studio)
CLICKHOUSE_HOST=192.168.50.29
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
TENANT_ID=client_001
```

**Note:** If your ClickHouse uses `bizpulse_admin` user with password, set:
```env
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
```

---

## 📋 Step 2: Verify MongoDB Has Data (On Laptop)

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
load_dotenv()
async def check():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL'))
    db = client[os.getenv('DB_NAME', 'bizpulse')]
    count = await db.business_data.count_documents({})
    print(f'MongoDB business_data count: {count:,}')
    if count > 0:
        sample = await db.business_data.find_one({})
        print(f'Sample document keys: {list(sample.keys())[:10]}')
    await client.close()
asyncio.run(check())
"
```

**Expected:** Should show document count > 0.

---

## 📋 Step 3: Verify ClickHouse Connection (On Laptop)

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print('✅ Connected:', ch.host, ch.port); print('✅ Version:', ch.execute('SELECT version()')[0][0])"
```

**Expected:**
```
✅ Connected: 192.168.50.29 9000
✅ Version: 24.3.18.x
```

---

## 🚀 Step 4: Run Migration Script (On Laptop)

### Option A: Full Migration (Clear & Reload)

**Use this if:** Table is empty or you want to replace all data.

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

**What happens:**
1. Connects to MongoDB `business_data`
2. Reads all documents
3. Maps columns (Year → year, Month_Name → month_name, etc.)
4. Transforms to ClickHouse format
5. Inserts in batches of 10,000 rows
6. Shows progress bar
7. Displays statistics after completion

**When prompted:** Type `yes` to clear existing data (if any).

### Option B: Incremental Migration (Add New Data Only)

**Use this if:** Table already has data and you want to add more.

Edit `migrate_real_data_to_clickhouse.py` line ~429:
```python
mode = 'incremental'  # Change from 'full' to 'incremental'
```

Then run:
```powershell
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

**Note:** Incremental mode will **add** rows (may create duplicates if same data exists).

---

## 📊 Step 5: Verify Migration Success

### On Laptop (Python):

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe -c "
from app.database.clickhouse_client import ClickHouseClient
ch = ClickHouseClient()
count = ch.execute('SELECT count(*) FROM sales_analytics')[0][0]
print(f'✅ Total rows in ClickHouse: {count:,}')
businesses = ch.execute('SELECT countDistinct(business) FROM sales_analytics')[0][0]
print(f'✅ Unique businesses: {businesses}')
"
```

### On Mac Studio (SSH):

```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

Then:
```sql
SELECT count(*) FROM sales_analytics;
SELECT count(*) FROM sales_food_view;
SELECT business, count(*) as rows FROM sales_analytics GROUP BY business ORDER BY rows DESC LIMIT 5;
SELECT * FROM sales_analytics LIMIT 5;
exit
```

---

## 🧪 Step 6: Run Test Suites (On Laptop)

After migration, run all tests:

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"

# Test 1: Tenant enforcement
C:\Python314\python.exe scripts\test_tenant_enforcement.py

# Test 2: Time filter injection
C:\Python314\python.exe scripts\test_time_filter_injection.py

# Test 3: AI query simulation
C:\Python314\python.exe scripts\test_ai_simulation_queries.py
```

**Expected:** All tests should pass (or only fail on connection if ClickHouse is down).

---

## 📋 Migration Script Details

**File:** `backend/scripts/migrate_real_data_to_clickhouse.py`

**What it does:**
1. ✅ Reads from MongoDB `business_data` collection
2. ✅ Maps columns:
   - `Year` + `Month_Name` → `date` (parsed)
   - `Business` → `business`
   - `Channel` → `channel`
   - `Customer` → `customer`
   - `Brand` → `brand`
   - `Category` → `category`
   - `Sub_Cat` / `Sub_Category` → `sub_category`
   - `SKU` / `Product` → `sku`
   - `Units` / `Cases` → `cases`
   - `Revenue` / `gSales` → `gsales`
   - `Gross_Profit` / `fGP` → `fgp`
   - And other metrics...
3. ✅ Adds `tenant_id = 'client_001'` to every row
4. ✅ Uses **explicit column names** in INSERT (safe for schema evolution)
5. ✅ Skips MATERIALIZED columns (year, month, quarter, etc. - auto-calculated)
6. ✅ Batch inserts (10K rows at a time for performance)
7. ✅ Shows progress bar and statistics

**Column mapping (MongoDB → ClickHouse):**
```
MongoDB Field          → ClickHouse Column
─────────────────────────────────────────────
Year + Month_Name      → date (parsed to Date)
Business               → business
Channel                → channel
Customer               → customer
Brand                  → brand
Category               → category
Sub_Cat / Sub_Category → sub_category
SKU / Product          → sku
Units / Cases          → cases
Revenue / gSales        → gsales
Price_Downs            → price_downs
Perm_Disc              → perm_disc
Transfer_Cost          → transfer_cost
Group_Cost             → group_cost
LTA                    → lta
Gross_Profit / fGP     → fgp
(created_at auto-added) → created_at
```

---

## ⚠️ Troubleshooting

### Error: "Authentication failed"

**Fix:** Check `.env` has correct `CLICKHOUSE_USER` and `CLICKHOUSE_PASSWORD`.

**Test:**
```powershell
C:\Python314\python.exe -c "from dotenv import load_dotenv; import os; load_dotenv(); print('User:', os.getenv('CLICKHOUSE_USER'), 'Password:', '***' if os.getenv('CLICKHOUSE_PASSWORD') else 'empty')"
```

### Error: "Unknown table sales_analytics"

**Fix:** Create table first (see `CREATE_TABLE_COMMANDS.md`).

### Error: "Connection refused"

**Fix:** 
1. Verify ClickHouse is running: `ssh thrivestudio@192.168.50.29 'docker ps | grep clickhouse'`
2. Check `.env` has `CLICKHOUSE_PORT=9000` (not 8123 or 18123)

### Error: "No documents found in MongoDB"

**Fix:** Ensure MongoDB is running and `business_data` collection has data.

**Check:**
```powershell
C:\Python314\python.exe -c "import asyncio; from motor.motor_asyncio import AsyncIOMotorClient; from dotenv import load_dotenv; import os; load_dotenv(); async def c(): client = AsyncIOMotorClient(os.getenv('MONGO_URL')); db = client[os.getenv('DB_NAME')]; print(await db.business_data.count_documents({})); asyncio.run(c())"
```

---

## 🎯 Expected Migration Output

When migration runs successfully, you'll see:

```
======================================================================
🚀 BIZPULSE - REAL DATA Migration (MongoDB → ClickHouse)
======================================================================
Mode: FULL
======================================================================

📊 Connecting to MongoDB...
✅ Found 1,234,567 documents in MongoDB.business_data

🗄️  Connecting to ClickHouse at 192.168.50.29:9000...
✅ Connected to ClickHouse 24.3.18.x
   Current rows in ClickHouse: 0

🔄 Starting full migration...
   Batch size: 10,000
   Source: MongoDB.bizpulse.business_data
   Target: ClickHouse.bizpulse.sales_analytics

📋 Column Mapping (MongoDB → ClickHouse):
   Year → year: 2024
   Month_Name → month_name: January
   Business → business: Food
   ...

Migrating: 100%|████████████| 1234567/1234567 [05:23<00:00, 3812.34docs/s]

======================================================================
✅ MIGRATION COMPLETE!
======================================================================
   MongoDB documents:  1,234,567
   Migrated rows:     1,234,567
   ClickHouse count:  1,234,567
   Errors encountered: 0
   Skipped (no date): 0

📊 Data Statistics:
   Total Rows:      1,234,567
   Businesses:      5
   Channels:        12
   Brands:          234
   Customers:       15,678
   Categories:      45
   Total Sales:     €12,345,678.90
   Total Profit:    €2,345,678.90

📊 Sample Data by Business:
   Food              :  456,789 rows, €5,678,901.23
   Beauty            :  234,567 rows, €2,345,678.90
   ...
```

---

## 🚀 Quick Command Reference

| Task | Command |
|------|---------|
| **Check MongoDB data** | See Step 2 above |
| **Test ClickHouse connection** | See Step 3 above |
| **Run migration** | `C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py` |
| **Verify data** | See Step 5 above |
| **Run tests** | See Step 6 above |

---

## 💡 ChatGPT's Suggestions Review

### ✅ Implemented:
1. ✅ **`.env` loading** - Fixed (added `load_dotenv()` at top of `clickhouse_client.py`)
2. ✅ **System queries** - Fixed (skip tenant injection if no FROM clause)
3. ✅ **SQL spacing** - Fixed (trailing spaces added)

### 📝 Documented (Future Enhancement):
1. **ClickHouse Row Policies** - Good suggestion for production, but current regex-based approach is acceptable for SaaS stage. Documented in `brain/FINAL_SECURITY_FIXES_COMPLETE.md`.

**When to consider Row Policies:**
- When you have 10+ tenants
- When you need database-level enforcement
- When you want to eliminate Python-level SQL rewriting

**Current approach is fine for:**
- Single tenant or few tenants
- Application-level control is acceptable
- Faster to implement and debug

---

## ✅ Final Checklist

Before migration:
- [x] Table `sales_analytics` created on Mac Studio
- [x] `.env` configured correctly
- [x] MongoDB has data
- [x] ClickHouse connection works

After migration:
- [ ] Verify row count matches MongoDB
- [ ] Check views work (`sales_food_view`, etc.)
- [ ] Run test suites
- [ ] Test API endpoints

---

**You're ready to migrate!** 🚀

Run the migration script and watch your data flow from MongoDB to ClickHouse.
