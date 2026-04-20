# Complete Setup Runbook: MongoDB + ClickHouse + AI Chatbot

This runbook provides step-by-step instructions to set up the complete Bizpulse production architecture with MongoDB (bizpulse_rbac), ClickHouse (analytics), and AI chatbot caching.

---

## Prerequisites

- Python 3.10+ installed (use `C:\Python314\python.exe` on Windows)
- MongoDB Atlas connection string configured in `.env`
- ClickHouse running on Mac Studio (192.168.50.29:9000)
- Access to backend folder

---

## Step 1: Environment Configuration

### 1.1 Update `.env` file

Ensure these variables are set in `backend/.env`:

```env
# MongoDB
MONGO_URL=mongodb+srv://...
DB_NAME=bizpulse_rbac

# ClickHouse
CLICKHOUSE_HOST=192.168.50.29
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
TENANT_ID=client_001

# Default time filter (in months)
DEFAULT_TIME_MONTHS=24

# LLM (for AI chatbot)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.50.29:11434
OLLAMA_MODEL=qwen2.5:32b-instruct
```

**Note:** `DEFAULT_TIME_MONTHS` controls the default time window when users don't specify a time range. Change this value to adjust the default (e.g., 12 for 12 months, 36 for 36 months).

---

## Step 2: MongoDB Setup (bizpulse_rbac)

### 2.1 Copy bizpulse → bizpulse_rbac (One-time)

**Purpose:** Create a working copy of the production database for RBAC and app data.

**Command:**
```powershell
cd backend
C:\Python314\python.exe scripts\copy_bizpulse_to_bizpulse_rbac.py
```

**What it does:**
- Copies all collections from `bizpulse` → `bizpulse_rbac`
- Reads from `bizpulse` (read-only)
- Writes to `bizpulse_rbac` (new working DB)

**Expected output:**
```
Copying collection: users
Copying collection: business_data
...
✅ Copy complete: bizpulse → bizpulse_rbac
```

### 2.2 Add RBAC Fields to Users

**Purpose:** Add `role` and `access` fields to all users in bizpulse_rbac.

**Command:**
```powershell
C:\Python314\python.exe scripts\add_user_rbac_fields.py --target-db bizpulse_rbac
```

**What it does:**
- Adds `role` field (default: "user")
- Adds `access` field with structure:
  ```python
  {
    "businesses": ["*"],  # or specific list
    "channels": ["*"],
    "brands": ["*"],
    "categories": "all",
    "sub_categories": "all",
    "customers": "all",
    "allowed_metrics": ["*"]  # or ["gsales", "fgp", ...]
  }
  ```
- Admin users get `role: "admin"` and `access` with `["*"]` for all fields

**Expected output:**
```
✅ Added RBAC fields to 32 users in bizpulse_rbac
```

### 2.3 Verify RBAC Setup

**Command:**
```powershell
C:\Python314\python.exe scripts\verify_rbac_fields.py
```

**Expected output:**
```
✅ Admin user found:
   role = admin
   access = {'businesses': ['*'], ...}
📊 Users in bizpulse_rbac:
   Total: 32
   With 'role' field: 32
   With 'access' field: 32
```

### 2.4 Create AI Cache Collection with Indexes

**Purpose:** Create MongoDB collection for AI chatbot cache with required indexes.

**Command:**
```powershell
C:\Python314\python.exe scripts\setup_ai_cache_collection.py
```

**What it does:**
- Creates `bizpulse_rbac.ai_cache` collection
- Creates compound index: `(tenant_id, permissions_hash, intent_hash, data_version)`
- Creates TTL index: `(expires_at)` with `expireAfterSeconds=0`

**Expected output:**
```
✅ Created ai_cache collection
✅ Created compound index: (tenant_id, permissions_hash, intent_hash, data_version)
✅ Created TTL index: (expires_at)
```

---

## Step 3: ClickHouse Setup

### 3.1 Verify ClickHouse Connection

**Test connection from backend:**
```powershell
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; c = ClickHouseClient(); print('✅ Connected')"
```

**Expected output:**
```
✅ Connected
```

### 3.2 Create sales_analytics Table (if not exists)

**Note:** If you already ran `migrate_real_data_to_clickhouse.py`, the table should exist. Skip this if table exists.

**Verify table exists:**
```sql
-- Run in ClickHouse client
DESCRIBE TABLE bizpulse.sales_analytics;
```

**If table doesn't exist, create it:**
```sql
CREATE TABLE bizpulse.sales_analytics
(
    tenant_id LowCardinality(String),
    date Date,
    year UInt16 MATERIALIZED toYear(date),
    month UInt8 MATERIALIZED toMonth(date),
    quarter UInt8 MATERIALIZED toQuarter(date),
    year_month UInt32 MATERIALIZED toYYYYMM(date),
    month_name LowCardinality(String),
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
PARTITION BY toYYYYMM(date)
ORDER BY (tenant_id, date, business, channel, brand, category, sub_category, customer, sku);
```

### 3.3 Initial Data Migration (One-time)

**Purpose:** Copy historical data from MongoDB `business_data` → ClickHouse `sales_analytics`.

**Command:**
```powershell
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

**What it does:**
- Reads from MongoDB `business_data` collection (from DB_NAME in .env)
- Transforms data to match ClickHouse schema
- Inserts into ClickHouse `sales_analytics` table
- Sets `month_name` in Python (ClickHouse doesn't support `%B` format)

**Expected output:**
```
✅ Migrated 107,175 rows to ClickHouse
```

**Note:** This is a one-time operation. Future data comes from CSV/ERP, not MongoDB.

---

## Step 4: Backend Configuration

### 4.1 Verify Config Loads Correctly

**Test:**
```powershell
C:\Python314\python.exe -c "from app.core.config import settings; print(f'DB: {settings.DB_NAME}, Default Time: {settings.DEFAULT_TIME_MONTHS} months')"
```

**Expected output:**
```
DB: bizpulse_rbac, Default Time: 24 months
```

---

## Step 5: Verify Complete Setup

### 5.1 Run Setup Verification Script

**Command:**
```powershell
C:\Python314\python.exe scripts\verify_complete_setup.py
```

**What it checks:**
- ✅ MongoDB connection (bizpulse_rbac)
- ✅ ClickHouse connection
- ✅ Users have RBAC fields
- ✅ AI cache collection exists with indexes
- ✅ sales_analytics table exists
- ✅ Config loads correctly

**Expected output:**
```
✅ MongoDB: Connected to bizpulse_rbac
✅ ClickHouse: Connected to bizpulse
✅ RBAC: 32 users have role and access fields
✅ AI Cache: Collection exists with indexes
✅ ClickHouse Table: sales_analytics exists
✅ Config: DEFAULT_TIME_MONTHS = 24
✅ Setup complete!
```

---

## Step 6: Daily Operations (Future)

### 6.1 Incremental Data Ingestion

**When new CSV/ERP data arrives:**

1. **Load new data** (only dates not already in ClickHouse):
   ```python
   # Example ETL script (to be created)
   latest_date = clickhouse.execute("SELECT max(date) FROM sales_analytics WHERE tenant_id = 'client_001'")
   new_data = load_csv()
   new_data = new_data[new_data["date"] > latest_date]
   clickhouse.insert("sales_analytics", new_data)
   ```

2. **For corrections** (if a month needs to be corrected):
   ```sql
   -- Load corrected data into temp table
   -- Then replace partition:
   ALTER TABLE sales_analytics REPLACE PARTITION 202601 FROM sales_analytics_temp
   ```

---

## Troubleshooting

### MongoDB Connection Issues
- Verify `MONGO_URL` in `.env` is correct
- Check MongoDB Atlas IP whitelist
- Test connection: `mongosh "<MONGO_URL>"`

### ClickHouse Connection Issues
- Verify Mac Studio IP (192.168.50.29) is accessible
- Check ClickHouse is running: `docker ps | grep clickhouse`
- Test port 9000: `telnet 192.168.50.29 9000`

### RBAC Fields Missing
- Re-run: `add_user_rbac_fields.py --target-db bizpulse_rbac`
- Check MongoDB: `db.users.findOne({role: {$exists: true}})`

### Cache Indexes Missing
- Re-run: `setup_ai_cache_collection.py`
- Verify: `db.ai_cache.getIndexes()`

---

## Quick Reference Commands

```powershell
# Full setup (run once)
cd backend
C:\Python314\python.exe scripts\copy_bizpulse_to_bizpulse_rbac.py
C:\Python314\python.exe scripts\add_user_rbac_fields.py --target-db bizpulse_rbac
C:\Python314\python.exe scripts\setup_ai_cache_collection.py
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py

# Verify setup
C:\Python314\python.exe scripts\verify_complete_setup.py
```

---

## Next Steps

After setup is complete:
1. ✅ Backend services are ready (AI cache, intent, query builder, etc.)
2. ✅ Chatbot endpoint will use caching automatically
3. ✅ RBAC filters are applied to all ClickHouse queries
4. ✅ Default time filter (24 months) is applied unless user asks for "lifetime"

**Your system is now production-ready!**
