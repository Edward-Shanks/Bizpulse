# 🚀 Run Migration NOW - Quick Commands

**Status:** ✅ Everything fixed, ready to migrate MongoDB → ClickHouse

---

## ⚡ Quick Commands (Copy-Paste Ready)

### 1️⃣ Verify Everything is Ready

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"

# Check MongoDB has data
C:\Python314\python.exe -c "import asyncio; from motor.motor_asyncio import AsyncIOMotorClient; from dotenv import load_dotenv; import os; load_dotenv(); async def c(): client = AsyncIOMotorClient(os.getenv('MONGO_URL')); db = client[os.getenv('DB_NAME', 'bizpulse')]; count = await db.business_data.count_documents({}); print(f'MongoDB documents: {count:,}'); await client.close(); asyncio.run(c())"

# Check ClickHouse connection
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print('✅ Connected:', ch.host, ch.port); print('✅ Table exists:', 'sales_analytics' in [t[0] for t in ch.execute('SHOW TABLES FROM bizpulse')])"
```

**Expected:**
- MongoDB documents: > 0
- ✅ Connected: 192.168.50.29 9000
- ✅ Table exists: True

---

### 2️⃣ Run Migration Script

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

**What to expect:**
- Progress bar showing migration progress
- If table has data, it will ask: "Clear and reload? (yes/no)" → Type `yes`
- Final statistics showing rows migrated

---

### 3️⃣ Verify Migration Success

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"

# Check row count
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); count = ch.execute('SELECT count(*) FROM sales_analytics')[0][0]; print(f'✅ ClickHouse rows: {count:,}')"

# Check sample data
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); rows = ch.execute('SELECT business, count(*) as cnt FROM sales_analytics GROUP BY business ORDER BY cnt DESC LIMIT 5'); print('Top businesses:'); [print(f'  {r[0]}: {r[1]:,} rows') for r in rows]"
```

---

### 4️⃣ Run All Tests

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"

C:\Python314\python.exe scripts\test_tenant_enforcement.py
C:\Python314\python.exe scripts\test_time_filter_injection.py
C:\Python314\python.exe scripts\test_ai_simulation_queries.py
```

**Expected:** All tests should pass (or only fail on connection if ClickHouse is down).

---

## 📋 Pre-Flight Checklist

Before running migration, ensure:

- [ ] ✅ Table `sales_analytics` created on Mac Studio (see `CREATE_TABLE_COMMANDS.md`)
- [ ] ✅ `.env` has `CLICKHOUSE_HOST=192.168.50.29` and `CLICKHOUSE_PORT=9000`
- [ ] ✅ MongoDB `business_data` collection has data
- [ ] ✅ ClickHouse connection works (tested above)

---

## 🎯 Migration Script Details

**File:** `backend/scripts/migrate_real_data_to_clickhouse.py`

**What it does:**
- ✅ Reads from MongoDB `business_data`
- ✅ Maps columns (Year+Month_Name → date, Business → business, etc.)
- ✅ Adds `tenant_id = 'client_001'` to every row
- ✅ Uses explicit column names (safe for schema evolution)
- ✅ Batch inserts (10K rows at a time)
- ✅ Shows progress and statistics

**Column mapping:**
- `Year` + `Month_Name` → `date` (parsed)
- `Business` → `business`
- `Channel` → `channel`
- `Customer` → `customer`
- `Brand` → `brand`
- `Revenue` / `gSales` → `gsales`
- `Gross_Profit` / `fGP` → `fgp`
- And all other metrics...

---

## ⚠️ If Migration Fails

### Error: "Authentication failed"
**Fix:** Check `.env` has correct `CLICKHOUSE_USER` and `CLICKHOUSE_PASSWORD`

### Error: "Unknown table sales_analytics"
**Fix:** Create table first (see `CREATE_TABLE_COMMANDS.md`)

### Error: "No documents found"
**Fix:** Ensure MongoDB `business_data` has data

---

**Ready?** Run Step 2 above! 🚀
