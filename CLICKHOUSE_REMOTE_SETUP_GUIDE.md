# ClickHouse Remote Setup Guide
## Laptop (Windows) → Mac Studio (ClickHouse)

---

## 🖥️ Your Setup

```
┌─────────────────────────────────────────────────────────┐
│  LAPTOP (Windows)                                       │
│  ├── Code: C:\Users\Sumit Mishra\Documents\Bizpulse    │
│  ├── Backend: FastAPI                                   │
│  ├── Frontend: React                                    │
│  └── MongoDB: Local                                     │
└─────────────────────────────────────────────────────────┘
                        │
                        │ SSH Connection
                        ↓
┌─────────────────────────────────────────────────────────┐
│  MAC STUDIO (512GB RAM)                                 │
│  ├── ClickHouse: Docker (clickhouse-prod)              │
│  ├── Port 9000: Native protocol                         │
│  ├── Port 18123: HTTP API                               │
│  └── Qwen:32b LLM                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 What Runs Where

### On Mac Studio (via SSH)
✅ ClickHouse Docker container  
✅ SQL schema creation  
✅ RBAC setup  
✅ Database operations  

### On Laptop (Windows)
✅ Your code (Bizpulse)  
✅ Python migration script (connects remotely)  
✅ FastAPI backend (connects remotely)  
✅ MongoDB  

---

## 🚀 Step-by-Step Setup

### STEP 1: Transfer SQL Files to Mac Studio (5 minutes)

#### Option A: Using SCP (Recommended)

```bash
# From your Windows laptop PowerShell/Terminal
# Replace 'macstudio' with your Mac Studio's IP or hostname

# Transfer schema file
scp backend/scripts/create_schema.sql user@macstudio:/tmp/

# Transfer RBAC file
scp backend/scripts/setup_rbac.sql user@macstudio:/tmp/
```

#### Option B: Copy-Paste via SSH

```bash
# SSH into Mac Studio
ssh user@macstudio

# Create the SQL files manually
nano /tmp/create_schema.sql
# Paste the contents of create_schema.sql
# Save: Ctrl+O, Enter, Ctrl+X

nano /tmp/setup_rbac.sql
# Paste the contents of setup_rbac.sql
# Save: Ctrl+O, Enter, Ctrl+X
```

---

### STEP 2: Create Database on Mac Studio (2 minutes)

```bash
# SSH into Mac Studio
ssh user@macstudio

# Run schema creation
docker exec -i clickhouse-prod clickhouse-client < /tmp/create_schema.sql

# Verify database created
docker exec -it clickhouse-prod clickhouse-client --query="SHOW DATABASES"

# Verify table created
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse --query="SHOW TABLES"
```

**Expected Output:**
```
┌─name────────────────┐
│ sales_analytics     │
└─────────────────────┘
```

---

### STEP 3: Set Up RBAC on Mac Studio (2 minutes)

```bash
# Still on Mac Studio via SSH
docker exec -i clickhouse-prod clickhouse-client < /tmp/setup_rbac.sql

# Verify users created
docker exec -it clickhouse-prod clickhouse-client --query="SHOW USERS"

# Verify views created
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse --query="SHOW TABLES"
```

**Expected Output:**
```
┌─name────────────────────────────┐
│ sales_analytics                 │
│ sales_food_view                 │
│ manager_multi_business_view     │
│ sales_convenience_view          │
│ sales_heinz_view                │
└─────────────────────────────────┘
```

---

### STEP 4: Configure Remote Connection on Laptop (5 minutes)

#### Update `.env` on Your Laptop

```bash
# File: C:\Users\Sumit Mishra\Documents\Bizpulse\.env

# ClickHouse Configuration (REMOTE)
CLICKHOUSE_HOST=<MAC_STUDIO_IP_ADDRESS>  # e.g., 192.168.1.100
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=bizpulse
CLICKHOUSE_USER=bizpulse_admin
CLICKHOUSE_PASSWORD=Admin@123!Secure
CLICKHOUSE_HTTP_PORT=18123
```

**Replace `<MAC_STUDIO_IP_ADDRESS>` with actual IP:**

```bash
# Find Mac Studio IP (run this on Mac Studio via SSH)
ifconfig | grep "inet " | grep -v 127.0.0.1
```

---

### STEP 5: Test Remote Connection from Laptop (2 minutes)

Create a test script on your laptop:

**File: `backend/test_clickhouse_connection.py`**

```python
#!/usr/bin/env python3
"""Test ClickHouse connection from Windows laptop to Mac Studio"""

from clickhouse_driver import Client
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("Testing ClickHouse Connection (Laptop → Mac Studio)")
print("=" * 70)

# Get config from .env
host = os.getenv('CLICKHOUSE_HOST')
port = int(os.getenv('CLICKHOUSE_PORT', 9000))
database = os.getenv('CLICKHOUSE_DB', 'bizpulse')
user = os.getenv('CLICKHOUSE_USER', 'bizpulse_admin')
password = os.getenv('CLICKHOUSE_PASSWORD')

print(f"\nConnecting to:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Database: {database}")
print(f"  User: {user}")

try:
    # Connect
    client = Client(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    # Test query
    version = client.execute('SELECT version()')[0][0]
    print(f"\n✅ SUCCESS! Connected to ClickHouse {version}")
    
    # Count rows
    count = client.execute('SELECT count() FROM sales_analytics')[0][0]
    print(f"✅ Table exists with {count:,} rows")
    
    # List databases
    databases = client.execute('SHOW DATABASES')
    print(f"\n📊 Databases:")
    for db in databases:
        print(f"   - {db[0]}")
    
    # List tables
    tables = client.execute('SHOW TABLES FROM bizpulse')
    print(f"\n📋 Tables in bizpulse:")
    for table in tables:
        print(f"   - {table[0]}")
    
    print("\n" + "=" * 70)
    print("🎉 Remote connection working perfectly!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check Mac Studio IP is correct in .env")
    print("2. Check ClickHouse is running: ssh user@macstudio 'docker ps'")
    print("3. Check firewall allows port 9000 on Mac Studio")
    print("4. Try: ssh user@macstudio 'docker exec -it clickhouse-prod clickhouse-client --query=\"SELECT 1\"'")
```

**Run from your Windows laptop:**

```bash
# Install dependency if needed
pip install clickhouse-driver python-dotenv

# Run test
python backend/test_clickhouse_connection.py
```

---

### STEP 6: Migrate Data from Laptop to Mac Studio (10-15 minutes)

**Update Migration Script** to connect remotely:

**File: `backend/scripts/migrate_to_clickhouse.py`**

Update the configuration section:

```python
# ==================== CONFIGURATION ====================
# MongoDB (LOCAL on Laptop)
MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DB = "bizpulse"
MONGODB_COLLECTION = "business_data"

# ClickHouse (REMOTE on Mac Studio)
# Will read from .env file
import os
from dotenv import load_dotenv

load_dotenv()

CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST')  # Mac Studio IP
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', 9000))
CLICKHOUSE_DB = os.getenv('CLICKHOUSE_DB', 'bizpulse')
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'bizpulse_admin')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')

BATCH_SIZE = 10000  # Insert 10K rows at a time
```

**Run Migration from Your Laptop:**

```bash
cd C:\Users\Sumit Mishra\Documents\Bizpulse\backend
python scripts/migrate_to_clickhouse.py
```

**What Happens:**
1. Reads data from MongoDB (local on laptop)
2. Sends data to ClickHouse (remote on Mac Studio)
3. Data travels over your network

---

### STEP 7: Test RBAC (5 minutes)

You have **TWO options**:

#### Option A: Test from Mac Studio (via SSH)

```bash
# SSH into Mac Studio
ssh user@macstudio

# Test sales user
docker exec -it clickhouse-prod clickhouse-client \
    --user=sales_user \
    --password=Sales@123 \
    --database=bizpulse

# Should work
SELECT business, sum(gsales) FROM sales_food_view GROUP BY business;

# Should FAIL
SELECT * FROM sales_analytics LIMIT 1;
```

#### Option B: Test from Laptop (Remote)

Update `backend/scripts/test_rbac.py` configuration:

```python
# Configuration
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST')  # Mac Studio IP
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', 9000))
CLICKHOUSE_DB = "bizpulse"
```

Then run from laptop:

```bash
python backend/scripts/test_rbac.py
```

---

## 🔧 Network Configuration

### Mac Studio Firewall (Important!)

**On Mac Studio, allow ClickHouse ports:**

```bash
# SSH into Mac Studio
ssh user@macstudio

# Check if ports are listening
netstat -an | grep 9000
netstat -an | grep 18123

# If using macOS firewall, allow Docker
# System Preferences → Security & Privacy → Firewall → Firewall Options
# Add Docker to allowed applications
```

### Docker Port Mapping

**Verify Docker ports are exposed:**

```bash
# On Mac Studio
docker ps | grep clickhouse

# Should show:
# 0.0.0.0:9000->9000/tcp
# 0.0.0.0:18123->8123/tcp
```

If not exposed, recreate container:

```bash
# Stop and remove old container
docker stop clickhouse-prod
docker rm clickhouse-prod

# Recreate with proper port mapping
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

---

## 🐍 Python Client Configuration

**Update `backend/app/database/clickhouse_client.py`:**

```python
def __init__(
    self,
    host: str = None,
    port: int = None,
    database: str = None,
    user: str = None,
    password: str = None
):
    """
    Initialize ClickHouse client
    Reads from .env by default (supports remote Mac Studio)
    """
    self.host = host or os.getenv('CLICKHOUSE_HOST', 'localhost')
    self.port = int(port or os.getenv('CLICKHOUSE_PORT', 9000))
    self.database = database or os.getenv('CLICKHOUSE_DB', 'bizpulse')
    self.user = user or os.getenv('CLICKHOUSE_USER', 'bizpulse_admin')
    self.password = password or os.getenv('CLICKHOUSE_PASSWORD', 'Admin@123!Secure')
    
    # ... rest of code
```

**This will automatically connect to Mac Studio when running from laptop!**

---

## 📊 FastAPI Backend Configuration

**Your FastAPI will run on laptop and connect to Mac Studio:**

```python
# backend/app/main.py or wherever you initialize

from app.database.clickhouse_client import ClickHouseClient
from dotenv import load_dotenv

load_dotenv()

# This will automatically use Mac Studio IP from .env
ch_client = ClickHouseClient()

@app.get("/analytics/test")
async def test_connection():
    """Test ClickHouse connection"""
    try:
        version = ch_client.execute('SELECT version()')[0][0]
        count = ch_client.execute('SELECT count() FROM sales_analytics')[0][0]
        
        return {
            "status": "success",
            "clickhouse_version": version,
            "total_rows": count,
            "connection": "remote",
            "host": ch_client.host
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

---

## 🔍 Quick Commands Reference

### On Your Laptop (Windows)

```bash
# Test connection
python backend/test_clickhouse_connection.py

# Run migration
python backend/scripts/migrate_to_clickhouse.py

# Test RBAC
python backend/scripts/test_rbac.py

# Start FastAPI (connects to remote ClickHouse)
cd backend
uvicorn app.main:app --reload
```

### On Mac Studio (via SSH)

```bash
# SSH into Mac Studio
ssh user@macstudio

# Check ClickHouse status
docker ps | grep clickhouse

# Access ClickHouse CLI
docker exec -it clickhouse-prod clickhouse-client --database=bizpulse

# Check logs
docker logs clickhouse-prod --tail 50

# Restart ClickHouse
docker restart clickhouse-prod
```

---

## 🐛 Troubleshooting

### Issue 1: Can't Connect from Laptop

**Symptoms:**
```
Connection refused / Timeout
```

**Fix:**

1. **Check Mac Studio IP:**
```bash
# On Mac Studio
ifconfig | grep "inet "
```

2. **Test network connectivity:**
```bash
# From laptop
ping <MAC_STUDIO_IP>
```

3. **Check ClickHouse is running:**
```bash
# On Mac Studio
docker ps | grep clickhouse
```

4. **Check firewall:**
```bash
# On Mac Studio - test if port is accessible
nc -zv localhost 9000
```

### Issue 2: Port Not Accessible

**Fix:**

```bash
# On Mac Studio - verify port binding
docker ps | grep clickhouse
# Should show: 0.0.0.0:9000->9000/tcp

# If shows 127.0.0.1:9000, recreate container with 0.0.0.0
docker stop clickhouse-prod
docker rm clickhouse-prod
# Run docker run with -p 0.0.0.0:9000:9000
```

### Issue 3: Slow Migration

**Cause:** Network latency between laptop and Mac Studio

**Fix:**

1. **Increase batch size in migration script:**
```python
BATCH_SIZE = 50000  # Larger batches = fewer network trips
```

2. **Use Mac Studio's network (if possible):**
   - Copy migration script to Mac Studio
   - Run MongoDB export on laptop
   - Transfer CSV to Mac Studio
   - Import directly on Mac Studio

### Issue 4: SSH Connection Lost During Migration

**Fix:**

Use `screen` or `tmux` on Mac Studio:

```bash
# SSH into Mac Studio
ssh user@macstudio

# Start screen session
screen -S migration

# Run migration
python migrate_to_clickhouse.py

# Detach: Ctrl+A, then D
# Reattach later: screen -r migration
```

---

## 📁 File Locations

### On Your Laptop (Windows)
```
C:\Users\Sumit Mishra\Documents\Bizpulse\
├── .env                                    ← Configure Mac Studio IP here
├── backend\
│   ├── scripts\
│   │   ├── create_schema.sql              ← Transfer to Mac Studio
│   │   ├── setup_rbac.sql                 ← Transfer to Mac Studio
│   │   ├── migrate_to_clickhouse.py       ← Run from laptop
│   │   └── test_rbac.py                   ← Run from laptop
│   └── app\
│       └── database\
│           └── clickhouse_client.py        ← Uses .env config
└── test_clickhouse_connection.py          ← Test remote connection
```

### On Mac Studio
```
/tmp/
├── create_schema.sql                       ← Copied from laptop
└── setup_rbac.sql                          ← Copied from laptop

~/clickhouse/
├── data/                                   ← ClickHouse data
└── logs/                                   ← ClickHouse logs
```

---

## ✅ Setup Checklist

### Mac Studio Setup
- [ ] ClickHouse Docker running
- [ ] Ports 9000 and 18123 accessible
- [ ] SQL files transferred
- [ ] Database created (`bizpulse`)
- [ ] Table created (`sales_analytics`)
- [ ] RBAC users and views created

### Laptop Setup
- [ ] `.env` configured with Mac Studio IP
- [ ] Python dependencies installed
- [ ] Remote connection tested
- [ ] Migration script updated
- [ ] Python client configured

### Verification
- [ ] Test connection script passes
- [ ] Can query from laptop
- [ ] Migration runs successfully
- [ ] RBAC tests pass
- [ ] FastAPI connects to remote ClickHouse

---

## 🎯 Summary

**Your Architecture:**
```
Laptop (Windows)
├── Your code
├── MongoDB (local)
├── FastAPI backend → connects to Mac Studio ClickHouse
└── React frontend
        ↓ (network)
Mac Studio (512GB RAM)
├── ClickHouse (Docker)
├── Qwen:32b LLM
└── Handles all analytics queries
```

**Key Points:**
1. ✅ SQL commands run on Mac Studio (via SSH)
2. ✅ Python scripts run on laptop (connect remotely)
3. ✅ Code stays on laptop
4. ✅ Data migrates: Laptop MongoDB → Mac Studio ClickHouse
5. ✅ FastAPI on laptop queries ClickHouse on Mac Studio

---

**Next:** Once setup complete, continue with `PHASE1_IMPLEMENTATION_README.md`

**Version**: 1.0  
**Last Updated**: February 10, 2026  
**Status**: ✅ Ready for Remote Setup
