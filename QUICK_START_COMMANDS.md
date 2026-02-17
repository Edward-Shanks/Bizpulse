# ⚡ Quick Start Commands - ClickHouse Setup

**Quick reference for common commands**

---

## 🖥️ Mac Studio Commands

### Check ClickHouse Status
```bash
docker ps | grep clickhouse
docker logs clickhouse-prod --tail 50
```

### Connect to ClickHouse
```bash
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
```

### Create Schema (if needed)
```bash
# Copy schema file to Mac Studio first, then:
docker exec -i clickhouse-prod clickhouse-client < create_schema.sql
```

### Check Data
```bash
docker exec clickhouse-prod clickhouse-client --database=bizpulse -q "SELECT count() FROM sales_analytics"
```

---

## 💻 Laptop Commands (From Project Root)

### Test Connection
```bash
cd backend
python -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print(ch.execute('SELECT version()'))"
```

### Create Schema (Python method)
```bash
cd backend/scripts
python -c "
import clickhouse_driver
import os
from dotenv import load_dotenv
load_dotenv()
client = clickhouse_driver.Client(host=os.getenv('CLICKHOUSE_HOST'), port=9000, database='default', user=os.getenv('CLICKHOUSE_USER'), password=os.getenv('CLICKHOUSE_PASSWORD'))
with open('create_schema.sql', 'r') as f:
    sql = f.read()
    for stmt in [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]:
        if stmt:
            try:
                client.execute(stmt)
                print(f'✅ {stmt[:50]}')
            except Exception as e:
                print(f'⚠️  {e}')
"
```

### Run Migration
```bash
cd backend/scripts
python migrate_real_data_to_clickhouse.py
```

### Run All Tests
```bash
cd backend/scripts
python test_tenant_enforcement.py
python test_time_filter_injection.py
python test_ai_simulation_queries.py
```

### Verify Migration
```bash
cd backend
python -c "
from app.database.clickhouse_client import ClickHouseClient
ch = ClickHouseClient()
count = ch.execute('SELECT count() FROM bizpulse.sales_analytics')[0][0]
print(f'Total rows: {count:,}')
tenants = ch.execute_dict('SELECT tenant_id, count() as cnt FROM bizpulse.sales_analytics GROUP BY tenant_id')
for t in tenants:
    print(f\"  {t['tenant_id']}: {t['cnt']:,}\")
"
```

---

## 🔧 Environment Setup

### Check .env File
```bash
# From project root
cat .env | grep CLICKHOUSE
```

### Required .env Variables
```bash
CLICKHOUSE_HOST=192.168.50.29
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
TENANT_ID=client_001
DEFAULT_TIME_MONTHS=24
```

---

## 🧪 Test Commands

### Single Test
```bash
cd backend/scripts
python test_tenant_enforcement.py
```

### All Tests
```bash
cd backend/scripts
for test in test_*.py; do echo "Running $test..."; python "$test"; echo ""; done
```

---

## 📊 Quick Verification Queries

### From Laptop (Python)
```python
from app.database.clickhouse_client import ClickHouseClient
ch = ClickHouseClient()

# Row count
print(ch.execute('SELECT count() FROM bizpulse.sales_analytics')[0][0])

# Tenant check
print(ch.execute_dict('SELECT tenant_id, count() FROM bizpulse.sales_analytics GROUP BY tenant_id'))

# Date range
print(ch.execute('SELECT min(date), max(date) FROM bizpulse.sales_analytics')[0])
```

### From Mac Studio (SQL)
```sql
SELECT count() FROM sales_analytics;
SELECT tenant_id, count() FROM sales_analytics GROUP BY tenant_id;
SELECT min(date), max(date) FROM sales_analytics;
SELECT business, sum(gsales) FROM sales_analytics GROUP BY business LIMIT 5;
```

---

## 🚨 Common Issues

### Connection Refused
```bash
# Check Mac Studio IP is correct in .env
# Check ClickHouse is running: docker ps | grep clickhouse
# Check port 9000 is open: telnet 192.168.50.29 9000
```

### Table Doesn't Exist
```bash
# Create schema first (see above)
# Verify: docker exec clickhouse-prod clickhouse-client -q "SHOW TABLES FROM bizpulse"
```

### Migration Fails
```bash
# Check MongoDB is running: mongosh --eval "db.adminCommand('ping')"
# Check MongoDB has data: mongosh bizpulse --eval "db.business_data.countDocuments()"
# Check ClickHouse connection: python -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print('OK')"
```
