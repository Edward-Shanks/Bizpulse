# Create sales_analytics Table - Commands

**Problem:** Views exist (`sales_food_view`, etc.) but base table `sales_analytics` is missing.

**Solution:** Create the table using the production schema, then views will work.

---

## 🖥️ On Mac Studio (via SSH)

### Step 1: Connect to ClickHouse

```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

### Step 2: Create the Table

Copy and paste this entire CREATE TABLE statement:

```sql
CREATE TABLE IF NOT EXISTS bizpulse.sales_analytics
(
    tenant_id LowCardinality(String),
    date Date,
    year UInt16 MATERIALIZED toYear(date),
    month UInt8 MATERIALIZED toMonth(date),
    quarter UInt8 MATERIALIZED toQuarter(date),
    year_month UInt32 MATERIALIZED toYYYYMM(date),
    month_name LowCardinality(String) MATERIALIZED formatDateTime(date, '%B'),
    business LowCardinality(String),
    channel LowCardinality(String),
    customer LowCardinality(String),
    brand LowCardinality(String),
    category LowCardinality(String),
    sub_category LowCardinality(String),
    sku LowCardinality(String),
    cases Decimal(15, 2),
    gsales Decimal(15, 2),
    price_downs Decimal(15, 2),
    perm_disc Decimal(15, 2),
    transfer_cost Decimal(15, 2),
    group_cost Decimal(15, 2),
    lta Decimal(15, 2),
    fgp Decimal(15, 2),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(date))
ORDER BY (tenant_id, date, business, channel, brand, customer)
SETTINGS index_granularity = 8192;
```

### Step 3: Verify Table Created

```sql
SHOW TABLES;
```

You should see `sales_analytics` in the list.

### Step 4: Verify Views Can Now Query It

```sql
SELECT count(*) FROM sales_food_view;
```

If this works → views are now functional.

### Step 5: Exit

```sql
exit
```

---

## 💻 On Windows Laptop

### Step 1: Update `.env` File

**CRITICAL:** Your Docker shows **9000:9000** for native TCP. Use **port 9000** (not 18123).

Edit `backend\.env`:

```env
CLICKHOUSE_HOST=192.168.50.29
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
TENANT_ID=client_001
```

**Note:** Port **9000** is for `clickhouse-driver` (native TCP). Port 18123 is HTTP (for curl/web UI).

### Step 2: Test Connection

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print('Connected:', ch.host, ch.port); print('Version:', ch.execute('SELECT version()')[0][0])"
```

Expected: `Connected: 192.168.50.29 9000` and version number.

### Step 3: Verify Table Exists from Python

```powershell
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); tables = ch.execute('SHOW TABLES FROM bizpulse'); print('Tables:', [t[0] for t in tables])"
```

Should show `sales_analytics` in the list.

### Step 4: Run Migration (Push MongoDB Data to ClickHouse)

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

This will:
- Read from MongoDB `business_data` collection
- Write to ClickHouse `sales_analytics` table
- Add `tenant_id = 'client_001'` to all rows

### Step 5: Verify Data Migrated

**On Mac Studio (SSH):**
```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

Then:
```sql
SELECT count(*) FROM sales_analytics;
SELECT count(*) FROM sales_food_view;
SELECT * FROM sales_analytics LIMIT 5;
```

### Step 6: Run Tests

**On Laptop:**
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\test_tenant_enforcement.py
C:\Python314\python.exe scripts\test_time_filter_injection.py
C:\Python314\python.exe scripts\test_ai_simulation_queries.py
```

---

## 🔍 Why This Happened

1. **Views were created** (probably from a script that ran `CREATE VIEW ...`)
2. **Base table was never created** in this Docker container
3. **Views reference** `FROM bizpulse.sales_analytics` → but table doesn't exist
4. **Result:** All queries fail with `UNKNOWN_TABLE`

**Fix:** Create the base table, then views will work automatically.

---

## 📋 Quick Reference

| Task | Command |
|------|---------|
| **SSH to Mac Studio** | `ssh thrivestudio@192.168.50.29` |
| **Connect to ClickHouse** | `docker exec -it clickhouse-prod clickhouse-client --database=bizpulse` |
| **Create table** | Paste CREATE TABLE SQL (see Step 2 above) |
| **Check tables** | `SHOW TABLES;` |
| **Check data** | `SELECT count(*) FROM sales_analytics;` |
| **Update .env** | Set `CLICKHOUSE_PORT=9000` |
| **Run migration** | `C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py` |

---

## ⚠️ Important Notes

1. **Port 9000 vs 18123:**
   - **9000** = Native TCP (for `clickhouse-driver` Python library) ✅ Use this
   - **18123** = HTTP (for curl/web UI) ❌ Don't use for Python

2. **Docker Port Mapping:**
   - Your container shows: `0.0.0.0:9000->9000/tcp` ✅ Perfect
   - This means port 9000 is exposed and accessible from your laptop

3. **Views vs Table:**
   - **Views** (`sales_food_view`) = Filtered queries on base table
   - **Base table** (`sales_analytics`) = Raw fact table (must exist first)

4. **After Creating Table:**
   - Views will automatically work
   - Migration script will populate the table
   - Tests will pass (once data exists)

---

**Next:** Create the table → Migrate data → Run tests → Everything should work! 🚀
