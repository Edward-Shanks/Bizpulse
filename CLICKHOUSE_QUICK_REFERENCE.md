# ClickHouse Quick Reference Card

## 🚀 Quick Start Commands

### Access ClickHouse CLI
```bash
# As admin
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse

# As specific user
docker exec -it clickhouse-prod clickhouse-client \
    --user=sales_user --password=Sales@123 --database=bizpulse
```

### One-Line Status Check
```bash
docker exec -it clickhouse-prod clickhouse-client --query="SELECT count() FROM bizpulse.sales_analytics"
```

---

## 📊 Essential Queries

### Data Overview
```sql
-- Total rows
SELECT count() FROM sales_analytics;

-- Date range
SELECT min(date), max(date) FROM sales_analytics;

-- Distinct values
SELECT DISTINCT business FROM sales_analytics;
SELECT DISTINCT channel FROM sales_analytics;
```

### Business Metrics
```sql
-- Sales by business
SELECT business, sum(gsales) as total_sales
FROM sales_analytics
GROUP BY business
ORDER BY total_sales DESC;

-- Monthly trend
SELECT year, month, month_name, sum(gsales) as total_sales
FROM sales_analytics
WHERE year = 2024
GROUP BY year, month, month_name
ORDER BY month;

-- Top 10 customers
SELECT customer, sum(gsales) as total_sales
FROM sales_analytics
GROUP BY customer
ORDER BY total_sales DESC
LIMIT 10;
```

### Performance Monitoring
```sql
-- Query execution time
SELECT query, query_duration_ms, read_rows
FROM system.query_log
WHERE type = 'QueryFinish'
ORDER BY event_time DESC
LIMIT 10;

-- Table size
SELECT formatReadableSize(sum(bytes)) as size
FROM system.parts
WHERE database = 'bizpulse' AND table = 'sales_analytics';

-- Compression ratio
SELECT 
    formatReadableSize(sum(data_compressed_bytes)) as compressed,
    formatReadableSize(sum(data_uncompressed_bytes)) as uncompressed,
    round(sum(data_compressed_bytes) / sum(data_uncompressed_bytes) * 100, 2) as ratio_pct
FROM system.parts
WHERE database = 'bizpulse' AND table = 'sales_analytics';
```

---

## 🔐 RBAC Quick Reference

### Users & Their Access

| User | Password | Access |
|------|----------|--------|
| `bizpulse_admin` | `Admin@123!Secure` | Full access |
| `manager_user` | `Manager@123` | Food + Beauty, Revenue + Profit |
| `sales_user` | `Sales@123` | Food only, Revenue only |
| `finance_user` | `Finance@123` | All data |
| `convenience_user` | `Conv@123` | Convenience channel only |
| `brand_heinz_user` | `Heinz@123` | Heinz brand only |

### Views & Their Purpose

| View | Purpose |
|------|---------|
| `sales_analytics` | Main table (admin only) |
| `sales_food_view` | Food business, no profit |
| `manager_multi_business_view` | Food + Beauty with profit |
| `sales_convenience_view` | Convenience channel |
| `sales_heinz_view` | Heinz brand |

### RBAC Commands
```sql
-- List users
SHOW USERS;

-- Check user permissions
SHOW GRANTS FOR sales_user;

-- List views
SHOW TABLES FROM bizpulse;

-- Test user access
-- (connect as user, then try queries)
```

---

## 🛠️ Docker Commands

### Container Management
```bash
# Check status
docker ps | grep clickhouse

# Start/Stop/Restart
docker start clickhouse-prod
docker stop clickhouse-prod
docker restart clickhouse-prod

# View logs
docker logs clickhouse-prod --tail 50
docker logs clickhouse-prod -f  # Follow logs

# Container stats
docker stats clickhouse-prod
```

### Data Operations
```bash
# Backup table
docker exec clickhouse-prod clickhouse-client \
    --database=bizpulse \
    --query="SELECT * FROM sales_analytics FORMAT Native" > backup.native

# Restore table
cat backup.native | docker exec -i clickhouse-prod clickhouse-client \
    --database=bizpulse \
    --query="INSERT INTO sales_analytics FORMAT Native"

# Export to CSV
docker exec clickhouse-prod clickhouse-client \
    --database=bizpulse \
    --query="SELECT * FROM sales_analytics FORMAT CSV" > data.csv
```

---

## 🔧 Maintenance Commands

### Optimize Table
```sql
-- Merge partitions for better performance
OPTIMIZE TABLE bizpulse.sales_analytics FINAL;
```

### Clear Cache
```sql
-- Clear query cache
SYSTEM DROP MARK CACHE;
SYSTEM DROP UNCOMPRESSED CACHE;
```

### Check Partitions
```sql
-- List partitions
SELECT partition, count(), formatReadableSize(sum(bytes)) as size
FROM system.parts
WHERE database = 'bizpulse' AND table = 'sales_analytics'
GROUP BY partition
ORDER BY partition DESC;

-- Drop old partition (example)
ALTER TABLE bizpulse.sales_analytics DROP PARTITION '202301';
```

---

## 🐛 Troubleshooting

### Connection Issues
```bash
# Test if ClickHouse is responding
docker exec clickhouse-prod clickhouse-client --query="SELECT 1"

# Check if port is listening
netstat -an | grep 9000
netstat -an | grep 18123

# Check container health
docker inspect clickhouse-prod | grep -A 10 State
```

### Data Issues
```sql
-- Verify data integrity
SELECT count() FROM sales_analytics;
SELECT count(DISTINCT date) FROM sales_analytics;

-- Check for NULL values
SELECT 
    countIf(business IS NULL) as null_business,
    countIf(gsales IS NULL) as null_sales,
    countIf(date IS NULL) as null_date
FROM sales_analytics;

-- Find duplicate rows
SELECT date, business, customer, count() as cnt
FROM sales_analytics
GROUP BY date, business, customer
HAVING cnt > 1;
```

### Performance Issues
```sql
-- Find slow queries
SELECT 
    query,
    query_duration_ms,
    read_rows,
    read_bytes
FROM system.query_log
WHERE type = 'QueryFinish' AND query_duration_ms > 1000
ORDER BY query_duration_ms DESC
LIMIT 10;

-- Check active queries
SELECT query, elapsed, read_rows
FROM system.processes
WHERE user != 'default';
```

---

## 📦 Python Client Usage

### Basic Connection
```python
from app.database.clickhouse_client import ClickHouseClient

ch = ClickHouseClient()

# Simple query
results = ch.execute("SELECT count() FROM sales_analytics")
print(f"Total rows: {results[0][0]}")

# Query with results as dicts
results = ch.execute_dict("""
    SELECT business, sum(gsales) as total
    FROM sales_analytics
    GROUP BY business
""")

for row in results:
    print(f"{row['business']}: €{row['total']:,.2f}")
```

### With RBAC
```python
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
```

---

## 🗂️ File Locations

### SQL Scripts
- `backend/scripts/create_schema.sql` - Database schema
- `backend/scripts/setup_rbac.sql` - RBAC configuration

### Python Scripts
- `backend/scripts/migrate_to_clickhouse.py` - Data migration
- `backend/scripts/test_rbac.py` - RBAC testing
- `backend/app/database/clickhouse_client.py` - Python client

### Documentation
- `CLICKHOUSE_SETUP_README.md` - Main setup guide
- `brain/CLICKHOUSE_DATABASE_SETUP_COMPLETE.md` - Detailed guide
- `brain/CLICKHOUSE_SETUP_SUMMARY.md` - Summary report

---

## ⚡ Performance Expectations

| Rows | Aggregation | Filter | Join |
|------|------------|--------|------|
| 1 lakh | < 100ms | < 50ms | < 200ms |
| 1 crore | < 500ms | < 200ms | < 1s |
| 10 crore | < 2s | < 1s | < 5s |
| 50 crore | < 5s | < 3s | < 10s |

---

## 🆘 Emergency Procedures

### Container Won't Start
```bash
# Check logs
docker logs clickhouse-prod

# Remove and recreate
docker stop clickhouse-prod
docker rm clickhouse-prod

# Re-run docker run command from setup doc
```

### Data Corruption
```bash
# Stop container
docker stop clickhouse-prod

# Backup data
tar -czf clickhouse-backup-$(date +%Y%m%d).tar.gz ~/clickhouse/data

# Start container
docker start clickhouse-prod

# Verify data
docker exec clickhouse-prod clickhouse-client --query="SELECT count() FROM bizpulse.sales_analytics"
```

### RBAC Broken
```sql
-- Reconnect as admin
-- docker exec -it clickhouse-prod clickhouse-client

-- Drop and recreate users
DROP USER IF EXISTS sales_user;
DROP VIEW IF EXISTS sales_food_view;

-- Re-run setup_rbac.sql
```

---

## 📞 Get Help

1. **Documentation**: Check `CLICKHOUSE_SETUP_README.md`
2. **Logs**: `docker logs clickhouse-prod`
3. **Official Docs**: https://clickhouse.com/docs
4. **Community**: https://clickhouse.com/slack

---

**Keep this card handy for daily operations!**

**Version**: 1.0  
**Last Updated**: February 10, 2026
