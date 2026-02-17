# ✅ Month Name Fix - Complete

## Problem
ClickHouse was throwing error: `Incorrect syntax '%B', symbol is not supported 'B' for function formatDateTime`

**Root Cause:** ClickHouse doesn't support the `%B` format specifier (full month name) in `formatDateTime()` function.

## Solution Applied
1. ✅ Removed `MATERIALIZED formatDateTime(date, '%B')` from `month_name` column
2. ✅ Changed `month_name` to a regular column (not MATERIALIZED)
3. ✅ Updated migration script to calculate `month_name` in Python
4. ✅ Updated INSERT statements to include `month_name`

## Files Fixed
- ✅ `CREATE_TABLE_ONLY.sql` - Schema updated
- ✅ `backend/scripts/create_schema.sql` - Schema updated  
- ✅ `backend/scripts/migrate_real_data_to_clickhouse.py` - Migration script updated

## Next Steps - Run These Commands

### Step 1: Drop and Recreate Table (Mac Studio)
```bash
ssh thrivestudio@192.168.50.29
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

Then in ClickHouse client:
```sql
DROP TABLE IF EXISTS bizpulse.sales_analytics;
```

Then copy-paste the entire contents of `CREATE_TABLE_ONLY.sql`:
```sql
CREATE TABLE IF NOT EXISTS bizpulse.sales_analytics
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
PARTITION BY (tenant_id, toYYYYMM(date))
ORDER BY (tenant_id, date, business, channel, brand, customer)
SETTINGS index_granularity = 8192;
```

Verify:
```sql
SHOW CREATE TABLE bizpulse.sales_analytics;
exit
```

### Step 2: Run Migration (Windows Laptop)
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

### Step 3: Verify Data (Mac Studio)
```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

```sql
SELECT count(*) FROM bizpulse.sales_analytics;
-- Should return: 107175

SELECT month_name, count(*) as cnt 
FROM bizpulse.sales_analytics 
GROUP BY month_name 
ORDER BY cnt DESC 
LIMIT 5;
-- Should show: January, February, March, etc.
```

## What Changed

### Before (❌ Broken)
```sql
month_name LowCardinality(String) MATERIALIZED formatDateTime(date, '%B')
```
- ClickHouse tried to compute this during INSERT
- Failed because `%B` is not supported

### After (✅ Fixed)
```sql
month_name LowCardinality(String)
```
- Python calculates month name during migration
- Inserts full month names: "January", "February", etc.
- No ClickHouse computation needed

## Migration Script Changes

**Before:** Did NOT insert `month_name` (thought it was MATERIALIZED)

**After:** 
- Extracts `month_name` from MongoDB
- Normalizes to full month name ("Jan" → "January")
- Inserts directly into ClickHouse

## Expected Result

After migration completes:
- ✅ 107,175 rows migrated
- ✅ `month_name` column populated with full month names
- ✅ No errors related to `formatDateTime`
- ✅ All queries work correctly

---

**Status:** ✅ All fixes applied and ready for migration!
