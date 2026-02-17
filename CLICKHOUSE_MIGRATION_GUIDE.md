# 🚀 ClickHouse Migration Guide - Complete Setup & Testing

**Status:** Production-ready schema + Security protections implemented  
**Purpose:** Migrate MongoDB data to ClickHouse and validate setup

---

## 📋 Files Created/Modified

### Schema & Migration Files
1. ✅ `backend/scripts/create_schema.sql` - Final architect-approved schema
2. ✅ `backend/scripts/migrate_real_data_to_clickhouse.py` - Updated migration script
3. ✅ `backend/app/database/clickhouse_client.py` - Added tenant_id & time filter enforcement

### Test Scripts (NEW - CRITICAL)
4. ✅ `backend/scripts/test_tenant_enforcement.py` - Tenant isolation tests
5. ✅ `backend/scripts/test_time_filter_injection.py` - Time filter tests
6. ✅ `backend/scripts/test_ai_simulation_queries.py` - AI query simulation tests

### Documentation
7. ✅ `brain/CLICKHOUSE_SALES_ANALYTICS_ARCHITECT_FINAL.md` - Architect decisions
8. ✅ `brain/PRODUCTION_CRITICAL_TENANT_AND_TIME_FILTERS.md` - Critical checklist
9. ✅ `brain/IMPLEMENTATION_COMPLETE_SUMMARY.md` - Implementation status
10. ✅ `CLICKHOUSE_MIGRATION_GUIDE.md` - This document

---

## 🖥️ Step 1: Mac Studio Setup (Run on Mac Studio)

### 1.1 Verify ClickHouse is Running

```bash
# SSH into Mac Studio (or run directly on Mac Studio)
ssh your_user@192.168.50.29

# Check if ClickHouse container is running
docker ps | grep clickhouse

# If not running, start it:
docker start clickhouse-prod

# Or if container doesn't exist, create it:
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

### 1.2 Verify Ports are Accessible

```bash
# On Mac Studio, verify ports are listening
netstat -an | grep -E '9000|18123'

# Should show:
# 0.0.0.0:9000
# 0.0.0.0:18123
```

### 1.3 Test Connection from Mac Studio

```bash
# Connect to ClickHouse
docker exec -it clickhouse-prod clickhouse-client

# Test basic query
SELECT version();

# Check if database exists
SHOW DATABASES;

# Exit
exit
```

---

## 💻 Step 2: Laptop Setup (Run from Your Laptop)

### 2.1 Verify Environment Variables

Create/update `.env` file in project root:

```bash
# MongoDB (Local on Laptop)
MONGO_URL=mongodb://localhost:27017
DB_NAME=bizpulse

# ClickHouse (Remote on Mac Studio)
CLICKHOUSE_HOST=192.168.50.29
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
CLICKHOUSE_HTTP_PORT=18123

# Multi-tenant
TENANT_ID=client_001

# Default time filter (months)
DEFAULT_TIME_MONTHS=24
```

### 2.2 Test Connection from Laptop

```bash
# From project root
cd backend

# Test ClickHouse connection
python -c "
from app.database.clickhouse_client import ClickHouseClient
ch = ClickHouseClient()
print('✅ Connected to ClickHouse:', ch.host, ch.port)
version = ch.execute('SELECT version()')
print('ClickHouse version:', version[0][0])
"
```

**Expected output:**
```
✅ Connected to ClickHouse: 192.168.50.29 9000
ClickHouse version: 24.3.x.x
```

---

## 🗄️ Step 3: Create Schema (Run from Laptop)

### 3.1 Create Database and Table

```bash
# From project root
cd backend/scripts

# Option A: Run SQL file directly (if you have clickhouse-client installed)
# This won't work from laptop, so use Option B

# Option B: Use Python script to create schema
python -c "
import clickhouse_driver
import os
from dotenv import load_dotenv

load_dotenv()

client = clickhouse_driver.Client(
    host=os.getenv('CLICKHOUSE_HOST', '192.168.50.29'),
    port=int(os.getenv('CLICKHOUSE_PORT', 9000)),
    database='default',
    user=os.getenv('CLICKHOUSE_USER', 'bizpulse_admin'),
    password=os.getenv('CLICKHOUSE_PASSWORD', 'Admin@123!Secure')
)

# Read and execute schema file
with open('create_schema.sql', 'r') as f:
    sql = f.read()
    # Split by semicolons and execute each statement
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    for stmt in statements:
        if stmt:
            try:
                client.execute(stmt)
                print(f'✅ Executed: {stmt[:50]}...')
            except Exception as e:
                print(f'⚠️  Error: {e}')
                print(f'   Statement: {stmt[:100]}')

print('✅ Schema creation complete!')
"
```

**OR** Run directly on Mac Studio:

```bash
# On Mac Studio
docker exec -i clickhouse-prod clickhouse-client < /path/to/create_schema.sql

# Or copy file to Mac Studio first, then:
docker exec -i clickhouse-prod clickhouse-client < create_schema.sql
```

### 3.2 Verify Schema Created

```bash
# From laptop
python -c "
from app.database.clickhouse_client import ClickHouseClient
ch = ClickHouseClient()

# Check table exists
tables = ch.execute('SHOW TABLES FROM bizpulse')
print('Tables:', tables)

# Describe table
columns = ch.execute_dict('DESCRIBE TABLE bizpulse.sales_analytics')
print('\nColumns:')
for col in columns:
    print(f\"  {col['name']:30s} {col['type']}\")
"
```

**Expected output:**
```
Tables: [('sales_analytics',)]
Columns:
  tenant_id                      LowCardinality(String)
  date                           Date
  year                           UInt16
  month                          UInt8
  ...
```

---

## 📊 Step 4: Migrate Data (Run from Laptop)

### 4.1 Run Migration Script

```bash
# From project root
cd backend/scripts

# Run migration (full mode - clears and reloads)
python migrate_real_data_to_clickhouse.py

# OR incremental mode (only adds new data)
# Edit script: mode = 'incremental'
```

**Expected output:**
```
======================================================================
🚀 BIZPULSE - REAL DATA Migration (MongoDB → ClickHouse)
======================================================================
Mode: FULL
======================================================================

📊 Connecting to MongoDB...
✅ Found X documents in MongoDB.bizpulse.business_data

🗄️  Connecting to ClickHouse at 192.168.50.29:9000...
✅ Connected to ClickHouse 24.3.x.x
   Current rows in ClickHouse: 0

🔄 Starting full migration...
   Batch size: 10,000
   Source: MongoDB.bizpulse.business_data
   Target: ClickHouse.bizpulse.sales_analytics

📋 Column Mapping (MongoDB → ClickHouse):
   Tenant ID: client_001 (from env/default)
   Year + Month_Name → date: 2024 January
   Note: year/month/quarter/year_month/month_name are MATERIALIZED (auto-calculated)
   ...

Migrating: 100%|████████████████████| X/X [00:XX<00:00]

✅ MIGRATION COMPLETE!
======================================================================
   MongoDB documents:  X
   Migrated rows:      X
   ClickHouse count:   X
   Errors encountered: 0
   Skipped (no date):  0

📊 Data Statistics:
   Total Rows:      X
   Businesses:      X
   Channels:        X
   Brands:          X
   Customers:       X
   Categories:      X
   Total Sales:     €X.XX
   Total Profit:    €X.XX
```

### 4.2 Verify Migration

```bash
# From laptop
python -c "
from app.database.clickhouse_client import ClickHouseClient
ch = ClickHouseClient()

# Count rows
count = ch.execute('SELECT count() FROM bizpulse.sales_analytics')[0][0]
print(f'Total rows: {count:,}')

# Check tenant_id distribution
tenants = ch.execute_dict('SELECT tenant_id, count() as cnt FROM bizpulse.sales_analytics GROUP BY tenant_id')
print('\nTenant distribution:')
for t in tenants:
    print(f\"  {t['tenant_id']}: {t['cnt']:,} rows\")

# Check date range
dates = ch.execute('SELECT min(date), max(date) FROM bizpulse.sales_analytics')[0]
print(f'\nDate range: {dates[0]} to {dates[1]}')

# Sample data
sample = ch.execute_dict('SELECT * FROM bizpulse.sales_analytics LIMIT 3')
print('\nSample rows:')
for row in sample:
    print(f\"  {row}\")
"
```

---

## 🧪 Step 5: Run Test Suites (Run from Laptop)

### 5.1 Test Tenant Enforcement

```bash
# From project root
cd backend/scripts

python test_tenant_enforcement.py
```

**Expected output:**
```
======================================================================
🚀 TENANT ID ENFORCEMENT TEST SUITE
======================================================================

TEST: No tenant → Default injected
======================================================================
✅ PASSED: No tenant → Default injected

TEST: Correct tenant → Returns data
======================================================================
✅ PASSED: Correct tenant → Returns data

...

======================================================================
📊 TEST SUMMARY
======================================================================
Total Tests: 8
✅ Passed: 8
❌ Failed: 0

🎉 ALL TESTS PASSED - Tenant enforcement is working!
```

### 5.2 Test Time Filter Injection

```bash
python test_time_filter_injection.py
```

**Expected output:**
```
======================================================================
🚀 DEFAULT TIME FILTER INJECTION TEST SUITE
======================================================================

TEST: No date filter → Default injected
======================================================================
✅ PASSED: No date filter → Default injected

...

🎉 ALL TESTS PASSED - Time filter injection is working!
```

### 5.3 Test AI Simulation

```bash
python test_ai_simulation_queries.py
```

**Expected output:**
```
======================================================================
🚀 AI QUERY SIMULATION TEST SUITE
======================================================================

TEST: AI Query 1: What was total sales last quarter?
======================================================================
✅ PASSED: AI Query 1: What was total sales last quarter?

...

🎉 ALL TESTS PASSED - AI query simulation is working!
```

### 5.4 Run All Tests Together

```bash
# Create a test runner script
cat > run_all_tests.sh << 'EOF'
#!/bin/bash
echo "Running all ClickHouse tests..."
echo ""

echo "1. Tenant Enforcement Tests"
python test_tenant_enforcement.py
echo ""

echo "2. Time Filter Injection Tests"
python test_time_filter_injection.py
echo ""

echo "3. AI Simulation Tests"
python test_ai_simulation_queries.py
echo ""

echo "✅ All tests complete!"
EOF

chmod +x run_all_tests.sh
./run_all_tests.sh
```

---

## 🔍 Step 6: Manual Verification (Run from Mac Studio)

### 6.1 Connect to ClickHouse

```bash
# On Mac Studio
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

### 6.2 Run Verification Queries

```sql
-- Check row count
SELECT count() FROM sales_analytics;

-- Check tenant distribution
SELECT tenant_id, count() as rows 
FROM sales_analytics 
GROUP BY tenant_id;

-- Check date range
SELECT 
    min(date) as earliest_date,
    max(date) as latest_date,
    count(DISTINCT date) as unique_dates
FROM sales_analytics;

-- Check business distribution
SELECT business, count() as rows, sum(gsales) as total_sales
FROM sales_analytics
GROUP BY business
ORDER BY total_sales DESC;

-- Test tenant isolation (should only see client_001 data)
SELECT count() FROM sales_analytics WHERE tenant_id = 'client_001';
SELECT count() FROM sales_analytics WHERE tenant_id = 'client_999';  -- Should be 0

-- Test time filter (should see data)
SELECT count() FROM sales_analytics 
WHERE date >= addMonths(today(), -24);

-- Test MATERIALIZED columns work
SELECT year, month, quarter, month_name, count() 
FROM sales_analytics 
GROUP BY year, month, quarter, month_name 
ORDER BY year, month 
LIMIT 10;

-- Exit
exit;
```

---

## 🚨 Troubleshooting

### Issue: Cannot connect to ClickHouse from laptop

**Solution:**
```bash
# On Mac Studio, check firewall
sudo ufw status

# Allow port 9000 if needed
sudo ufw allow 9000/tcp

# Check ClickHouse is listening on all interfaces
docker exec clickhouse-prod netstat -tlnp | grep 9000
```

### Issue: Migration fails with "Table doesn't exist"

**Solution:**
```bash
# Create schema first (Step 3)
# Then verify table exists:
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse -q "SHOW TABLES"
```

### Issue: Tests fail with "Connection refused"

**Solution:**
```bash
# Verify .env file has correct Mac Studio IP
# Test connection manually:
python -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print(ch.execute('SELECT 1'))"
```

### Issue: Migration is slow

**Solution:**
```bash
# Increase batch size in migrate_real_data_to_clickhouse.py:
BATCH_SIZE = 50000  # Increase from 10000

# Or run migration in parallel batches (advanced)
```

---

## ✅ Success Checklist

- [ ] ClickHouse running on Mac Studio
- [ ] Can connect from laptop
- [ ] Schema created successfully
- [ ] Data migrated (row count matches MongoDB)
- [ ] Tenant enforcement tests pass
- [ ] Time filter tests pass
- [ ] AI simulation tests pass
- [ ] Manual verification queries work
- [ ] MATERIALIZED columns working
- [ ] Date range correct

---

## 🎯 Next Steps After Migration

1. **Update Backend Endpoints**
   - Ensure all AI endpoints pass `tenant_id` from user session
   - Update query builders to use new `execute()` methods

2. **Monitor Performance**
   - Check query execution times
   - Monitor ClickHouse resource usage
   - Set up query logging

3. **Production Hardening**
   - Create tenant-specific RBAC views
   - Add query rate limiting
   - Set up backup strategy

---

**Last Updated:** Migration guide created  
**Status:** Ready for execution
