# Commands: Windows Laptop + Mac Studio (ClickHouse & Migration)

**Your setup:** Windows laptop ↔ SSH → Mac Studio (192.168.50.29).  
**Goal:** Fix connection errors, run ClickHouse on Mac Studio, push MongoDB `business_data` to ClickHouse from your laptop.

---

## 1. What the error means

```
ConnectionRefusedError: No connection could be made because the target machine actively refused it (192.168.50.29:8123)
```

This means one or both of:

1. **Wrong port** – The app uses **8123** (HTTP). The Python driver `clickhouse-driver` uses **9000** (native TCP). You must use port **9000** in `.env`.
2. **ClickHouse not running** – On Mac Studio, the ClickHouse container may be stopped or not created.

**Fix:** Use port **9000** in `.env` and ensure ClickHouse is running on Mac Studio (see below).

**Docker port mapping (from your screenshot):** Your container shows **`0.0.0.0:9000->9000/tcp`** ✅ This is correct! The `clickhouse-driver` Python library uses **native TCP port 9000**, not HTTP. So:
- ✅ **Port 9000** = Native TCP (for Python `clickhouse-driver`) → **Use this in `.env`**
- ⚠️ **Port 18123** = HTTP (for curl/web UI) → Don't use for Python

**Important:** Set `CLICKHOUSE_PORT=9000` in your `.env` file (not 18123, not 8123).

---

## 2. Where your dashboard data lives

| What | Where |
|------|--------|
| **Dashboard source** | MongoDB collection **`business_data`** (DB: `bizpulse`) |
| **Loaded from CSV by** | `sync_azure_data.py` (Azure blob CSV) or `load_cleaned_data.py` (local `yearly_data_cleaned.csv`) |
| **Migration to ClickHouse** | `backend/scripts/migrate_real_data_to_clickhouse.py` reads **MongoDB `business_data`** and writes to **ClickHouse `sales_analytics`** |

You do **not** need to push CSV again. You only need:

1. MongoDB `business_data` to have data (it already does for the dashboard).
2. ClickHouse running on Mac Studio.
3. Run the migration script from your laptop (with correct `.env`).

---

## 3. Commands on Mac Studio (after SSH)

SSH from your Windows terminal:

```powershell
ssh thrivestudio@192.168.50.29
```

Then on **Mac Studio** run:

### 3.1 Check if ClickHouse is running

```bash
docker ps | grep clickhouse
```

- If you see `clickhouse-prod` (or similar) and status **Up** → ClickHouse is running.  
- If nothing or status **Exited** → start or create the container (next steps).

### 3.2 Start existing ClickHouse container

```bash
docker start clickhouse-prod
```

### 3.3 If the container does not exist – create it

```bash
# Create directories for data and logs
mkdir -p ~/clickhouse/data ~/clickhouse/logs

# Run ClickHouse (port 9000 = native TCP for Python driver)
docker run -d \
  --name clickhouse-prod \
  --platform=linux/amd64 \
  --ulimit nofile=262144:262144 \
  -p 0.0.0.0:9000:9000 \
  -p 0.0.0.0:18123:8123 \
  -v ~/clickhouse/data:/var/lib/clickhouse \
  -v ~/clickhouse/logs:/var/log/clickhouse-server \
  --restart unless-stopped \
  clickhouse/clickhouse-server:24.3
```

### 3.4 Check that port 9000 is listening

```bash
netstat -an | grep 9000
# Or:
docker port clickhouse-prod
```

You should see `9000/tcp` (and optionally `8123`).

### 3.5 (Optional) Create database and schema from Mac Studio

If you prefer to run SQL from Mac Studio (e.g. after copying the script):

```bash
# Copy schema file into container (run from Mac Studio; adjust path if needed)
docker cp /path/to/create_schema.sql clickhouse-prod:/tmp/

# Apply schema (creates DB bizpulse and table sales_analytics)
docker exec -i clickhouse-prod clickhouse-client --multiquery < /tmp/create_schema.sql
```

If the schema file is only on your laptop, use the “From laptop” method in section 5 instead.

### 3.6 Create Missing `sales_analytics` Table (CRITICAL)

**Problem:** Views exist but base table `sales_analytics` is missing. Views reference `FROM bizpulse.sales_analytics` but table doesn't exist.

**Solution:** Create the table using the production schema.

**Option A: Copy-paste SQL directly**

```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

Then paste this entire CREATE TABLE (from `CREATE_TABLE_ONLY.sql`):

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

**Option B: Copy file into container and run**

```bash
# From Mac Studio, copy file from laptop (adjust path)
scp thrivestudio@192.168.50.29:/path/to/CREATE_TABLE_ONLY.sql /tmp/

# Or if file is already on Mac Studio:
docker cp /path/to/CREATE_TABLE_ONLY.sql clickhouse-prod:/tmp/

# Run SQL
docker exec -i clickhouse-prod clickhouse-client --database=bizpulse < /tmp/CREATE_TABLE_ONLY.sql
```

**Verify table created:**

```sql
SHOW TABLES;
-- Should show: sales_analytics

SELECT count(*) FROM sales_analytics;
-- Should return: 0 (empty table, ready for data)

SELECT count(*) FROM sales_food_view;
-- Should now work (views can query the base table)
```

### 3.7 Quick test on Mac Studio

```bash
docker exec -it clickhouse-prod clickhouse-client --query="SELECT version()"
docker exec -it clickhouse-prod clickhouse-client --query="SHOW DATABASES"
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse --query="SHOW TABLES"
```

Then type `exit` or press Ctrl+D to leave the client.

---

## 4. Commands on Windows Laptop

All of these are from a terminal on your **Windows laptop** (PowerShell or CMD).

### 4.1 Fix `.env` for ClickHouse port

Edit `backend\.env` and set:

```env
CLICKHOUSE_HOST=192.168.50.29
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
TENANT_ID=client_001
```

Important: use **9000**, not 8123.

### 4.2 Go to backend and (optional) activate venv

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
# If you use a venv:
# .\venv\Scripts\Activate.ps1
```

### 4.3 Test ClickHouse connection from laptop

```powershell
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print('OK', ch.host, ch.port); print(ch.execute('SELECT version()'))"
```

If this prints `OK 192.168.50.29 9000` and a version, the connection is fine.

### 4.4 Create schema from laptop (if not done on Mac Studio)

Schema is in `backend\scripts\create_schema.sql`. You can run it via Python:

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe -c "
import os
from dotenv import load_dotenv
load_dotenv()
import clickhouse_driver
p = os.getenv
client = clickhouse_driver.Client(host=p('CLICKHOUSE_HOST','192.168.50.29'), port=int(p('CLICKHOUSE_PORT',9000)), database='default', user=p('CLICKHOUSE_USER','bizpulse_admin'), password=p('CLICKHOUSE_PASSWORD','Admin@123!Secure'))
with open('scripts/create_schema.sql','r') as f:
    sql = f.read()
for stmt in sql.split(';'):
    s = stmt.strip()
    if s and not s.startswith('--'):
        try: client.execute(s); print('OK:', s[:60])
        except Exception as e: print('Skip/Err:', e)
print('Done.')
"
```

Or run the SQL manually once inside the container (see 3.5).

### 4.5 Run migration (MongoDB → ClickHouse)

Ensure MongoDB is running and has data in `bizpulse.business_data`. Then:

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

- For full reload it may ask: “Clear and reload? (yes/no)” – type `yes` if you want to replace all ClickHouse data.
- Migration reads from **MongoDB `business_data`** and writes to **ClickHouse `sales_analytics`**.

### 4.6 Run tests (after migration)

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\test_tenant_enforcement.py
C:\Python314\python.exe scripts\test_time_filter_injection.py
C:\Python314\python.exe scripts\test_ai_simulation_queries.py
```

---

## 5. Quick reference

| Step | Where | Command |
|------|--------|--------|
| SSH to Mac Studio | Laptop | `ssh thrivestudio@192.168.50.29` |
| Check ClickHouse | Mac Studio | `docker ps \| grep clickhouse` |
| Start ClickHouse | Mac Studio | `docker start clickhouse-prod` |
| Create ClickHouse (if missing) | Mac Studio | See 3.3 block above |
| Set port 9000 | Laptop | Edit `backend\.env` → `CLICKHOUSE_PORT=9000` |
| Test connection | Laptop | See 4.3 |
| Create schema | Laptop or Mac Studio | See 4.4 or 3.5 |
| Migrate MongoDB → ClickHouse | Laptop | `C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py` |
| Run tests | Laptop | See 4.6 |

---

## 6. Files involved

| File | Purpose |
|------|--------|
| `backend/load_shopify_data_to_mongodb.py` | Loads **Shopify** CSV → `shopify_data` (not used for dashboard analytics). |
| `backend/sync_azure_data.py` | Loads Azure CSV → `business_data` (dashboard source). |
| `backend/load_cleaned_data.py` | Loads `yearly_data_cleaned.csv` → `business_data`. |
| `backend/scripts/migrate_real_data_to_clickhouse.py` | **MongoDB `business_data` → ClickHouse `sales_analytics`** (this is what you run to “push data to ClickHouse”). |
| `backend/scripts/create_schema.sql` | Creates DB `bizpulse` and table `sales_analytics` in ClickHouse. |

Your dashboard already uses **MongoDB `business_data`**. The migration script reuses that same collection to fill ClickHouse; no need to re-load from CSV for this step.
