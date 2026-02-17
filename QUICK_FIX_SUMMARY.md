# 🚀 Quick Fix Summary - Create Table & Fix Port

**Current Status:**
- ✅ ClickHouse running on Mac Studio (port 9000 exposed)
- ✅ Database `bizpulse` exists
- ✅ Views exist (`sales_food_view`, etc.)
- ❌ **Base table `sales_analytics` is MISSING** (views reference it but it doesn't exist)
- ❌ `.env` has wrong port (8123 instead of 9000)

---

## 🔧 Fix #1: Create Missing Table (On Mac Studio)

**SSH to Mac Studio:**
```bash
ssh thrivestudio@192.168.50.29
```

**Connect to ClickHouse:**
```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

**Copy-paste this CREATE TABLE:**

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

**Verify:**
```sql
SHOW TABLES;
-- Should show: sales_analytics

exit
```

---

## 🔧 Fix #2: Update `.env` Port (On Laptop)

**Edit `backend\.env`:**

Change:
```env
CLICKHOUSE_PORT=8123
```

To:
```env
CLICKHOUSE_PORT=9000
```

**Why:** Your Docker shows `0.0.0.0:9000->9000/tcp`. Python `clickhouse-driver` uses **native TCP port 9000**, not HTTP 8123/18123.

---

## 🚀 After Fixes: Migrate Data

**On Laptop:**
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

This pushes MongoDB `business_data` → ClickHouse `sales_analytics`.

---

## ✅ Verify Everything Works

**On Mac Studio:**
```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
SELECT count(*) FROM sales_analytics;
SELECT count(*) FROM sales_food_view;
exit
```

**On Laptop:**
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
C:\Python314\python.exe scripts\test_tenant_enforcement.py
```

---

**That's it!** After these 2 fixes, everything should work. 🎉
