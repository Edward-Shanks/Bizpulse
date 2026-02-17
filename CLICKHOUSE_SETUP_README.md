# ClickHouse Setup & Migration Guide - Complete Step-by-Step

---

## ⚠️ IMPORTANT: Remote Setup

**If you're running ClickHouse on Mac Studio and your code is on Windows laptop:**

👉 **READ THIS FIRST:** [`CLICKHOUSE_REMOTE_SETUP_GUIDE.md`](CLICKHOUSE_REMOTE_SETUP_GUIDE.md)

**Also see:** [`SETUP_ARCHITECTURE.txt`](SETUP_ARCHITECTURE.txt) for a visual diagram

This document below assumes ClickHouse and code are on the same machine. For remote setup, follow the guide above.

---

## 📚 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Steps)](#quick-start)
3. [Detailed Setup Guide](#detailed-setup-guide)
4. [RBAC Configuration](#rbac-configuration)
5. [Testing & Verification](#testing--verification)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Prerequisites

### ✅ What You Need

1. **ClickHouse Running** (Already completed ✅)
   - Docker container: `clickhouse-prod`
   - Port 9000: Native protocol
   - Port 18123: HTTP API

2. **MongoDB with Data**
   - Database: `bizpulse`
   - Collection: `business_data`
   - At least some test data

3. **Python Environment**
   ```bash
   pip install motor clickhouse-driver pandas tqdm python-dotenv
   ```

---

## Quick Start (5 Steps)

### Step 1: Create Database & Tables (2 minutes)

```bash
# Copy SQL file to container
docker cp backend/scripts/create_schema.sql clickhouse-prod:/tmp/

# Execute SQL
docker exec -i clickhouse-prod clickhouse-client --database=default < backend/scripts/create_schema.sql
```

Or manually:
```bash
docker exec -it clickhouse-prod clickhouse-client --database=default
```

Then paste the contents of `backend/scripts/create_schema.sql`.

### Step 2: Set Up RBAC (2 minutes)

```bash
# Copy RBAC SQL to container
docker cp backend/scripts/setup_rbac.sql clickhouse-prod:/tmp/

# Execute RBAC setup
docker exec -i clickhouse-prod clickhouse-client --database=bizpulse < backend/scripts/setup_rbac.sql
```

### Step 3: Configure Environment (1 minute)

Add to your `.env` file:

```bash
# ClickHouse Configuration
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
CLICKHOUSE_HTTP_PORT=18123
```

### Step 4: Migrate Data (5-10 minutes)

```bash
cd backend
python scripts/migrate_to_clickhouse.py
```

You should see:
```
🚀 BIZPULSE - MongoDB to ClickHouse Migration
======================================================================
📊 Connecting to MongoDB...
✅ Found 100,000 documents in MongoDB

🗄️  Connecting to ClickHouse...
✅ Connected to ClickHouse 24.3.1.2672

🔄 Starting migration...
Migrating: 100%|████████████████████| 100000/100000 [00:15<00:00]

✅ MIGRATION COMPLETE!
```

### Step 5: Verify Setup (2 minutes)

```bash
# Connect to ClickHouse
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse

# Run test queries
SELECT count() FROM sales_analytics;
SELECT DISTINCT business FROM sales_analytics;
SELECT business, sum(gsales) FROM sales_analytics GROUP BY business;
```

**✅ If all queries work, you're done!**

---

## Detailed Setup Guide

### 1. Database Schema

The schema is defined in `backend/scripts/create_schema.sql`.

**Key Features:**
- **Denormalized** for Phase 1 (simpler, faster to implement)
- **LowCardinality** for repeated values (80-90% compression)
- **Partitioned** by month for fast queries
- **Optimized** ORDER BY for your common filters

**Columns:**
- Time: `date`, `year`, `month`, `month_name`, `quarter`
- Dimensions: `business`, `channel`, `brand`, `category`, `sub_category`, `customer`, `sku`
- Metrics: `gsales`, `cases`, `fgp`, `price_downs`, `perm_disc`, `group_cost`, `lta`, `transfer_cost`

**To add more columns:**
1. Edit `backend/scripts/create_schema.sql`
2. Add column definitions before `created_at`
3. Update `migrate_to_clickhouse.py` to include the new columns
4. Re-run migration

### 2. RBAC (Role-Based Access Control)

RBAC is implemented at **three levels**:

#### Level 1: Users
- `bizpulse_admin` - Full access
- `manager_user` - Multiple businesses, revenue + profit
- `sales_user` - Single business, revenue only
- `finance_user` - All data
- `convenience_user` - Single channel
- `brand_heinz_user` - Single brand

#### Level 2: Views (Database-Level Security)
- `sales_food_view` - Only Food business, no profit/costs
- `manager_multi_business_view` - Food + Beauty, with profit
- `sales_convenience_view` - Convenience channel only
- `sales_heinz_view` - Heinz brand only

#### Level 3: Application-Level RBAC
Your FastAPI application uses `ClickHouseClient` to:
1. Read user permissions from MongoDB
2. Map permissions to appropriate ClickHouse view
3. Execute queries against that view

**Why Three Levels?**
- **Defense in depth**: Even if app has bugs, database enforces security
- **Performance**: Views are optimized by ClickHouse
- **Auditability**: All access is logged

### 3. Data Migration

The migration script `migrate_to_clickhouse.py`:

**What it does:**
1. Connects to MongoDB `bizpulse.business_data`
2. Reads all documents
3. Transforms to ClickHouse format
4. Inserts in batches of 10,000
5. Verifies data integrity

**Important:**
- Migration is **additive** by default (doesn't delete existing data)
- If you need to re-migrate, truncate table first:
  ```sql
  TRUNCATE TABLE bizpulse.sales_analytics;
  ```

**Customizing Migration:**
1. Edit field mappings in `migrate_to_clickhouse.py`
2. Update the `row` tuple to match your MongoDB schema
3. Ensure order matches `create_schema.sql`

### 4. Python Client

The `ClickHouseClient` class in `backend/app/database/clickhouse_client.py`:

**Features:**
- Connection management
- RBAC view mapping
- Query execution
- Error handling
- Type conversion

**Usage Example:**

```python
from app.database.clickhouse_client import ClickHouseClient

# Initialize
ch = ClickHouseClient()

# Query without RBAC (admin)
results = ch.execute_dict("""
    SELECT business, sum(gsales) as total
    FROM sales_analytics
    GROUP BY business
""")

# Query with RBAC
user_permissions = {
    'role': 'sales',
    'businesses': ['Food'],
    'data_types': ['revenue']
}

results = ch.execute_dict_with_rbac("""
    SELECT business, sum(gsales) as total
    FROM sales_analytics
    GROUP BY business
""", user_permissions)

# User will only see Food business data
```

---

## RBAC Configuration

### Creating New RBAC Views

**Example: Create view for "Beauty" business**

```sql
-- Create view
CREATE VIEW bizpulse.sales_beauty_view AS
SELECT
    date, year, month, month_name, quarter,
    business, channel, customer, brand,
    gsales, cases, fgp
FROM bizpulse.sales_analytics
WHERE business = 'Beauty';

-- Create user
CREATE USER IF NOT EXISTS beauty_user
    IDENTIFIED WITH plaintext_password BY 'Beauty@123'
    SETTINGS readonly = 1;

-- Grant access
GRANT SELECT ON bizpulse.sales_beauty_view TO beauty_user;
```

### Testing RBAC

```bash
# Connect as specific user
docker exec -it clickhouse-prod clickhouse-client \
    --user=sales_user \
    --password=Sales@123 \
    --database=bizpulse

# Try to access their view (should work)
SELECT * FROM sales_food_view LIMIT 5;

# Try to access main table (should fail)
SELECT * FROM sales_analytics LIMIT 5;
# Error: "Not enough privileges"
```

### Application-Level RBAC

Your FastAPI endpoints should:

1. **Get user from JWT token**
2. **Fetch permissions from MongoDB**
3. **Pass to ClickHouse client**

```python
from fastapi import Depends
from app.database.clickhouse_client import ClickHouseClient

async def get_sales_data(
    current_user: dict = Depends(get_current_user),
    ch: ClickHouseClient = Depends(get_clickhouse)
):
    # Get user permissions from MongoDB
    user_permissions = await get_user_permissions(current_user['id'])
    
    # Execute query with RBAC
    query = """
        SELECT business, sum(gsales) as total
        FROM sales_analytics
        WHERE year = 2024
        GROUP BY business
    """
    
    results = ch.execute_dict_with_rbac(query, user_permissions)
    return results
```

---

## Testing & Verification

### 1. Basic Connectivity

```bash
# Test connection
docker exec -it clickhouse-prod clickhouse-client --query "SELECT 1"

# Check databases
docker exec -it clickhouse-prod clickhouse-client --query "SHOW DATABASES"

# Check tables
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse --query "SHOW TABLES"
```

### 2. Data Verification

```sql
-- Count rows
SELECT count() FROM bizpulse.sales_analytics;

-- Check distinct values
SELECT DISTINCT business FROM bizpulse.sales_analytics;
SELECT DISTINCT channel FROM bizpulse.sales_analytics;

-- Check date range
SELECT min(date), max(date) FROM bizpulse.sales_analytics;

-- Sample data
SELECT * FROM bizpulse.sales_analytics LIMIT 10;
```

### 3. Performance Testing

```sql
-- Measure query time
SELECT 
    business,
    sum(gsales) as total_sales,
    sum(fgp) as total_profit
FROM bizpulse.sales_analytics
GROUP BY business;

-- Check query log
SELECT 
    query,
    type,
    query_duration_ms,
    read_rows,
    memory_usage
FROM system.query_log
WHERE type = 'QueryFinish'
ORDER BY event_time DESC
LIMIT 10;
```

**Expected Performance:**
- 1 lakh rows: < 100ms
- 1 crore rows: < 500ms
- 10 crore rows: < 2 seconds

### 4. RBAC Testing

Run the RBAC test script:

```bash
cd backend
python scripts/test_rbac.py
```

Or manually:

```bash
# Test each user
for user in sales_user manager_user finance_user; do
    echo "Testing $user..."
    docker exec -it clickhouse-prod clickhouse-client \
        --user=$user \
        --password=${user//_/}@123 \
        --database=bizpulse \
        --query="SELECT count() FROM sales_analytics" || echo "Failed as expected"
done
```

---

## Troubleshooting

### Issue 1: Can't Connect to ClickHouse

**Symptoms:**
```
Connection refused
```

**Fix:**
```bash
# Check if container is running
docker ps | grep clickhouse

# If not running, start it
docker start clickhouse-prod

# Check logs
docker logs clickhouse-prod --tail 50
```

### Issue 2: Table Not Found

**Symptoms:**
```
Table bizpulse.sales_analytics doesn't exist
```

**Fix:**
```bash
# Check if table exists
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse --query="SHOW TABLES"

# If not exists, create it
docker exec -i clickhouse-prod clickhouse-client --database=default < backend/scripts/create_schema.sql
```

### Issue 3: Migration Fails

**Symptoms:**
```
Error inserting batch: ...
```

**Fix:**
1. Check MongoDB connection:
   ```bash
   mongosh --eval "db.adminCommand('ping')"
   ```

2. Check MongoDB has data:
   ```bash
   mongosh bizpulse --eval "db.business_data.count()"
   ```

3. Check ClickHouse schema matches migration script:
   ```sql
   DESCRIBE TABLE bizpulse.sales_analytics;
   ```

4. Run migration with verbose logging:
   ```bash
   python scripts/migrate_to_clickhouse.py --verbose
   ```

### Issue 4: Slow Queries

**Symptoms:**
Queries taking > 5 seconds

**Fix:**
1. Check if data is partitioned:
   ```sql
   SELECT partition, count() 
   FROM system.parts 
   WHERE database = 'bizpulse' AND table = 'sales_analytics'
   GROUP BY partition;
   ```

2. Optimize table:
   ```sql
   OPTIMIZE TABLE bizpulse.sales_analytics FINAL;
   ```

3. Check query is using ORDER BY columns:
   ```sql
   -- Good (uses ORDER BY columns)
   SELECT * FROM sales_analytics WHERE business = 'Food';
   
   -- Bad (doesn't use ORDER BY columns)
   SELECT * FROM sales_analytics WHERE sku = '12345';
   ```

### Issue 5: RBAC Not Working

**Symptoms:**
User can see data they shouldn't

**Fix:**
1. Check user exists:
   ```sql
   SHOW USERS;
   ```

2. Check grants:
   ```sql
   SHOW GRANTS FOR sales_user;
   ```

3. Verify view exists:
   ```sql
   SHOW TABLES FROM bizpulse;
   ```

4. Test view directly:
   ```bash
   docker exec -it clickhouse-prod clickhouse-client \
       --user=sales_user \
       --password=Sales@123 \
       --database=bizpulse \
       --query="SELECT DISTINCT business FROM sales_food_view"
   ```

---

## Next Steps

### Immediate (This Week)
- [ ] Verify all data migrated correctly
- [ ] Test RBAC with different users
- [ ] Create views for your actual users
- [ ] Update `.env` with production passwords

### Short-term (Next 2 Weeks)
- [ ] Update FastAPI backend to use ClickHouse
- [ ] Implement AI chatbot query generation
- [ ] Update dashboard endpoints
- [ ] Set up backup strategy

### Medium-term (Month 2-3)
- [ ] Monitor query performance
- [ ] Add materialized views for common queries
- [ ] Implement data retention policies
- [ ] Consider Star Schema migration (Phase 2)

---

## Useful Commands

### ClickHouse CLI

```bash
# Admin access
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse

# Specific user
docker exec -it clickhouse-prod clickhouse-client \
    --user=sales_user \
    --password=Sales@123 \
    --database=bizpulse

# Run single query
docker exec -it clickhouse-prod clickhouse-client \
    --database=bizpulse \
    --query="SELECT count() FROM sales_analytics"
```

### Common Queries

```sql
-- Show databases
SHOW DATABASES;

-- Show tables
SHOW TABLES FROM bizpulse;

-- Show users
SHOW USERS;

-- Show grants
SHOW GRANTS FOR sales_user;

-- Table info
DESCRIBE TABLE bizpulse.sales_analytics;

-- Count rows
SELECT count() FROM bizpulse.sales_analytics;

-- Table size
SELECT formatReadableSize(sum(bytes)) as size
FROM system.parts
WHERE database = 'bizpulse' AND table = 'sales_analytics';

-- Query performance
SELECT query, query_duration_ms
FROM system.query_log
WHERE type = 'QueryFinish'
ORDER BY event_time DESC
LIMIT 10;
```

### Docker Commands

```bash
# Check if running
docker ps | grep clickhouse

# Start/stop/restart
docker start clickhouse-prod
docker stop clickhouse-prod
docker restart clickhouse-prod

# View logs
docker logs clickhouse-prod --tail 50
docker logs clickhouse-prod -f  # Follow

# Remove container (WARNING: Deletes data if not backed up!)
docker stop clickhouse-prod
docker rm clickhouse-prod
```

---

## Related Documentation

- `brain/CLICKHOUSE_DATABASE_SETUP_COMPLETE.md` - Full detailed guide
- `brain/PHASE1_IMPLEMENTATION_README.md` - 12-week implementation plan
- `brain/FINAL_ENHANCED_ARCHITECTURE_V2.md` - Complete architecture
- `brain/MONGODB_VS_CLICKHOUSE_DECISION.md` - Why ClickHouse?

---

## Support & Resources

### Official Documentation
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [ClickHouse SQL Reference](https://clickhouse.com/docs/en/sql-reference/)
- [RBAC in ClickHouse](https://clickhouse.com/docs/en/operations/access-rights)

### Internal Resources
- Migration script: `backend/scripts/migrate_to_clickhouse.py`
- Schema definition: `backend/scripts/create_schema.sql`
- RBAC setup: `backend/scripts/setup_rbac.sql`
- Python client: `backend/app/database/clickhouse_client.py`

---

**Status**: ✅ Ready for Production  
**Last Updated**: February 10, 2026  
**Version**: 1.0  
**Author**: BizPulse Development Team
