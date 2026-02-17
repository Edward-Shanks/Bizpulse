# 🎯 Phase 1 Implementation Guide - Production-Ready BizPulse

## Critical Decision: MongoDB vs ClickHouse

### ✅ **RECOMMENDATION: Use ClickHouse Cloud for Analytics**

**Why ClickHouse is PERFECT for your use case:**

| Factor | Your Requirement | MongoDB | ClickHouse | Winner |
|--------|-----------------|---------|-----------|---------|
| **Current Data** | 1 lakh rows | ✅ Good | ✅ Excellent | ⚖️ Tie |
| **Future Data** | 50-60 CRORE rows | ❌ Struggles | ✅ Perfect | 🏆 ClickHouse |
| **Columns** | 30-40 columns | ⚠️ Slow aggregations | ✅ Columnar = Fast | 🏆 ClickHouse |
| **Query Type** | Aggregations, GROUP BY | ⚠️ Slow | ✅ Native support | 🏆 ClickHouse |
| **Response Time** | <500ms required | ❌ 2-5 seconds at scale | ✅ 50-200ms | 🏆 ClickHouse |
| **Cost at Scale** | Must be reasonable | ❌ Expensive | ✅ Cheap (10x compression) | 🏆 ClickHouse |
| **Concurrent Users** | 50-100+ users | ❌ Degrades | ✅ No degradation | 🏆 ClickHouse |

### 📊 Performance at Your Scale

#### Current (1 Lakh Rows)
```
MongoDB:     100-300ms ✅ (acceptable)
ClickHouse:  20-50ms   ✅ (faster but overkill)
```

#### Future (50-60 Crore Rows) - **THIS IS CRITICAL**
```
MongoDB:     5-30 seconds    ❌ UNACCEPTABLE
ClickHouse:  100-500ms       ✅ PERFECT
```

**Verdict**: At 50-60 crore rows, MongoDB becomes unusable. ClickHouse is essential.

---

## 🏗️ **RECOMMENDED ARCHITECTURE**

### Hybrid Approach (Best of Both Worlds)

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                             │
│               (React Dashboard + AI Chat)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                      │
└────┬──────────────────────────────────────────┬─────────┘
     │                                          │
     ↓                                          ↓
┌─────────────────┐                   ┌──────────────────┐
│   MongoDB       │                   │  ClickHouse      │
│                 │                   │  Cloud           │
│ • Users         │                   │                  │
│ • Permissions   │                   │ • Analytics Data │
│ • RBAC Rules    │                   │ • 50-60 CR rows  │
│ • Auth/Session  │                   │ • 30-40 columns  │
│ • Chat History  │                   │ • Fast queries   │
│ • Audit Logs    │                   │ • Aggregations   │
└─────────────────┘                   └──────────────────┘
  (Transactional)                       (Analytical)
```

**Why Hybrid?**
- ✅ MongoDB: Perfect for users, auth, RBAC (transactional data)
- ✅ ClickHouse: Perfect for analytics (fast aggregations at scale)
- ✅ Best of both worlds

---

## 🚀 Phase 1 Implementation Roadmap

### Timeline: 12 Weeks to Production

```
Week 1-2:  Setup & Infrastructure
Week 3-5:  RBAC Foundation
Week 6-8:  AI Chatbot with RBAC
Week 9-10: Dashboard with RBAC
Week 11-12: Testing & Production Deploy
```

---

## 📅 WEEK 1-2: Setup & Infrastructure

### Task 1.1: ClickHouse Cloud Setup

**Why ClickHouse Cloud?**
- ✅ Managed service (no DevOps overhead)
- ✅ Auto-scaling (handles 50-60 crore rows easily)
- ✅ Built-in backups
- ✅ 99.9% uptime SLA
- ✅ Pay per usage (cost-effective)

**Steps**:

1. **Sign up for ClickHouse Cloud**
   - Go to: https://clickhouse.cloud
   - Create account
   - Choose region (closest to your users)
   - Start with "Development" tier for testing

2. **Create Your First Service**
   ```
   Service Name: bizpulse-analytics-prod
   Region: AWS Asia Pacific (Mumbai) or closest
   Tier: Development (upgrade to Production later)
   ```

3. **Get Connection Details**
   ```
   Host: abc123.clickhouse.cloud
   Port: 8443 (HTTPS)
   User: default
   Password: [secure password]
   Database: bizpulse
   ```

### Task 1.2: Create ClickHouse Schema

**File: `backend/database/clickhouse_schema.sql`**

```sql
-- Main analytics table (DENORMALIZED for Phase 1)
-- Using LowCardinality for 80-90% compression benefit!
CREATE TABLE IF NOT EXISTS sales_analytics
(
    -- Time dimensions
    date Date,
    year UInt16,
    month UInt8,
    month_name LowCardinality(String),  -- LowCardinality for repeated values
    quarter UInt8,
    
    -- Business dimensions (LowCardinality for repeated values)
    business LowCardinality(String),      -- ✅ LowCardinality = internal compression
    channel LowCardinality(String),       -- ✅ Only ~10-20 unique values
    brand LowCardinality(String),         -- ✅ Only ~100-500 unique values
    category LowCardinality(String),      -- ✅ Only ~50-100 unique values
    sub_category LowCardinality(String),  -- ✅ Only ~200-500 unique values
    
    -- Customer: DON'T use LowCardinality (too many unique values)
    customer String,                      -- ⚠️ Thousands of unique customers
    
    -- SKU: DON'T use LowCardinality (too many unique values)
    sku String,                           -- ⚠️ Thousands of unique SKUs
    
    -- Metrics (your 30-40 columns)
    gsales Decimal(15, 2),      -- Gross Sales
    cases Decimal(15, 2),       -- Units/Cases
    fgp Decimal(15, 2),         -- Final Gross Profit
    price_downs Decimal(15, 2),
    perm_disc Decimal(15, 2),
    group_cost Decimal(15, 2),
    lta Decimal(15, 2),
    transfer_cost Decimal(15, 2),
    
    -- Add your other 22-32 columns here
    -- metric1 Decimal(15, 2),
    -- metric2 Decimal(15, 2),
    -- ...
    
    -- Metadata
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)  -- Partition by month for fast queries
ORDER BY (business, channel, customer, brand, date)  -- Optimized for your queries
SETTINGS index_granularity = 8192;

-- 🎯 KEY INSIGHT: LowCardinality gives you 80-90% of Star Schema benefits
-- without the complexity! Perfect for Phase 1.

-- Create materialized view for faster aggregations (optional but recommended)
CREATE MATERIALIZED VIEW IF NOT EXISTS sales_monthly_summary
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (business, channel, year, month)
AS SELECT
    toYYYYMM(date) as month_key,
    business,
    channel,
    year,
    month,
    sum(gsales) as total_gsales,
    sum(cases) as total_cases,
    sum(fgp) as total_profit,
    count() as record_count
FROM sales_analytics
GROUP BY month_key, business, channel, year, month;
```

**Why This Schema?**
- ✅ **Partitioned by month**: Queries only scan relevant months (fast!)
- ✅ **Ordered by business dimensions**: Your most common filters
- ✅ **LowCardinality**: For columns with few unique values (saves memory)
- ✅ **Materialized view**: Pre-aggregated data for common queries

### Task 1.3: MongoDB Setup (Keep Existing)

**You already have MongoDB - just add RBAC tables**

**File: `backend/database/mongodb_rbac_schema.js`**

```javascript
// Users collection (keep existing, add fields)
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });

// NEW: User Data Access (RBAC rules)
db.user_data_access.createIndex({ "user_id": 1 });
db.user_data_access.createIndex({ "dimension_type": 1 });
db.user_data_access.createIndex({ "user_id": 1, "dimension_type": 1 });

// Example document structure
db.user_data_access.insertOne({
  user_id: "user123",
  dimension_type: "business",
  dimension_value: "Food",
  granted_by: "admin@company.com",
  granted_at: new Date(),
  valid_from: new Date(),
  valid_until: null  // null = no expiry
});

// NEW: RBAC Roles
db.rbac_roles.createIndex({ "role_name": 1 }, { unique: true });

// NEW: Audit Logs (for compliance)
db.rbac_audit_logs.createIndex({ "user_id": 1, "timestamp": -1 });
db.rbac_audit_logs.createIndex({ "timestamp": -1 });
```

### Task 1.4: Data Migration Script

**File: `backend/scripts/migrate_to_clickhouse.py`**

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import clickhouse_driver
import pandas as pd
from datetime import datetime

async def migrate_data():
    """Migrate data from MongoDB to ClickHouse"""
    
    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
    mongo_db = mongo_client["bizpulse"]
    
    # Connect to ClickHouse Cloud
    ch_client = clickhouse_driver.Client(
        host='abc123.clickhouse.cloud',
        port=9440,
        user='default',
        password='your_password',
        secure=True,
        database='bizpulse'
    )
    
    print("🚀 Starting migration...")
    
    # Fetch all business data from MongoDB
    cursor = mongo_db.business_data.find({})
    batch = []
    batch_size = 10000
    total_migrated = 0
    
    async for doc in cursor:
        # Transform document to ClickHouse format
        row = (
            doc.get('date') or datetime.now().date(),
            doc.get('Year'),
            doc.get('Month'),
            doc.get('Month_Name'),
            (doc.get('Month') - 1) // 3 + 1,  # Calculate quarter
            doc.get('Business'),
            doc.get('Channel'),
            doc.get('Customer'),
            doc.get('Brand'),
            doc.get('Category'),
            doc.get('Sub_Category'),
            doc.get('SKU'),
            float(doc.get('Revenue', 0) or 0),
            float(doc.get('Units', 0) or 0),
            float(doc.get('Gross_Profit', 0) or 0),
            float(doc.get('Price_Downs', 0) or 0),
            float(doc.get('Perm_Disc', 0) or 0),
            float(doc.get('Group_Cost', 0) or 0),
            float(doc.get('LTA', 0) or 0),
            float(doc.get('Transfer_Cost', 0) or 0),
            datetime.now(),
            datetime.now()
        )
        batch.append(row)
        
        # Insert in batches
        if len(batch) >= batch_size:
            ch_client.execute(
                'INSERT INTO sales_analytics VALUES',
                batch
            )
            total_migrated += len(batch)
            print(f"✅ Migrated {total_migrated:,} rows...")
            batch = []
    
    # Insert remaining
    if batch:
        ch_client.execute('INSERT INTO sales_analytics VALUES', batch)
        total_migrated += len(batch)
    
    print(f"✅ Migration complete! Total rows: {total_migrated:,}")
    
    # Verify
    count = ch_client.execute('SELECT count() FROM sales_analytics')[0][0]
    print(f"✅ ClickHouse row count: {count:,}")

if __name__ == "__main__":
    asyncio.run(migrate_data())
```

**Run Migration**:
```bash
cd backend
python scripts/migrate_to_clickhouse.py
```

---

## 📅 WEEK 3-5: RBAC Foundation

### Task 2.1: Define User Permission Model

**File: `backend/app/models/rbac.py`**

```python
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
from datetime import datetime

class DataAccess(BaseModel):
    """What data types user can access"""
    revenue: bool = True
    profit: bool = False
    cost: bool = False
    finance: bool = False  # LTA, Price Downs, etc.

class UserPermissions(BaseModel):
    """Complete user permissions"""
    user_id: str
    email: str
    role: str
    
    # Dimension access
    businesses: List[str] | Literal["*"]  # "*" = all
    channels: List[str] | Literal["*"]
    customers: List[str] | Literal["*"]
    brands: List[str] | Literal["*"]
    categories: List[str] | Literal["*"]
    
    # Data type access
    data_access: DataAccess
    
    # Time range access (optional)
    allowed_years: List[int] | Literal["*"] = "*"
    
    # Metadata
    granted_by: str
    granted_at: datetime
    active: bool = True

class RBACRule(BaseModel):
    """Single RBAC rule"""
    user_id: str
    dimension_type: Literal["business", "channel", "customer", "brand", "category"]
    dimension_value: str
    granted_by: str
    granted_at: datetime
```

### Task 2.2: RBAC Service Implementation

**File: `backend/app/services/rbac_service.py`**

```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.rbac import UserPermissions, DataAccess, RBACRule
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class RBACService:
    """Service for managing RBAC"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.cache = {}  # Simple in-memory cache
    
    async def get_user_permissions(self, user_id: str) -> UserPermissions:
        """Get all permissions for a user"""
        
        # Check cache first
        cache_key = f"permissions:{user_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Get user
        user = await self.db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check if superadmin
        if user.get("is_superadmin", False):
            permissions = UserPermissions(
                user_id=user_id,
                email=user["email"],
                role=user.get("role", "admin"),
                businesses="*",
                channels="*",
                customers="*",
                brands="*",
                categories="*",
                data_access=DataAccess(
                    revenue=True,
                    profit=True,
                    cost=True,
                    finance=True
                ),
                granted_by="system",
                granted_at=user.get("created_at"),
                active=True
            )
            self.cache[cache_key] = permissions
            return permissions
        
        # Get access rules from user_data_access collection
        rules = await self.db.user_data_access.find({
            "user_id": user_id,
            "active": True
        }).to_list(1000)
        
        # Organize by dimension
        permissions_dict = {
            "businesses": [],
            "channels": [],
            "customers": [],
            "brands": [],
            "categories": []
        }
        
        for rule in rules:
            dim_type = rule["dimension_type"]
            dim_value = rule["dimension_value"]
            if dim_type in permissions_dict:
                permissions_dict[dim_type].append(dim_value)
        
        # Get data access from user role
        data_access = await self._get_role_data_access(user.get("role", "user"))
        
        permissions = UserPermissions(
            user_id=user_id,
            email=user["email"],
            role=user.get("role", "user"),
            businesses=permissions_dict["businesses"] or "*",
            channels=permissions_dict["channels"] or "*",
            customers=permissions_dict["customers"] or "*",
            brands=permissions_dict["brands"] or "*",
            categories=permissions_dict["categories"] or "*",
            data_access=data_access,
            granted_by=user.get("created_by", "system"),
            granted_at=user.get("created_at"),
            active=True
        )
        
        # Cache for 5 minutes
        self.cache[cache_key] = permissions
        return permissions
    
    async def _get_role_data_access(self, role: str) -> DataAccess:
        """Get data access permissions based on role"""
        
        role_access = {
            "ceo": DataAccess(revenue=True, profit=True, cost=True, finance=True),
            "cfo": DataAccess(revenue=True, profit=True, cost=True, finance=True),
            "manager": DataAccess(revenue=True, profit=True, cost=False, finance=False),
            "sales": DataAccess(revenue=True, profit=False, cost=False, finance=False),
            "user": DataAccess(revenue=True, profit=False, cost=False, finance=False),
        }
        
        return role_access.get(role.lower(), DataAccess())
    
    async def grant_access(
        self,
        user_id: str,
        dimension_type: str,
        dimension_value: str,
        granted_by: str
    ):
        """Grant access to a user"""
        
        rule = {
            "user_id": user_id,
            "dimension_type": dimension_type,
            "dimension_value": dimension_value,
            "granted_by": granted_by,
            "granted_at": datetime.utcnow(),
            "active": True
        }
        
        await self.db.user_data_access.insert_one(rule)
        
        # Clear cache
        cache_key = f"permissions:{user_id}"
        if cache_key in self.cache:
            del self.cache[cache_key]
        
        logger.info(f"✅ Granted {dimension_type}={dimension_value} to user {user_id}")
    
    async def revoke_access(
        self,
        user_id: str,
        dimension_type: str,
        dimension_value: str
    ):
        """Revoke access from a user"""
        
        await self.db.user_data_access.update_many(
            {
                "user_id": user_id,
                "dimension_type": dimension_type,
                "dimension_value": dimension_value
            },
            {"$set": {"active": False}}
        )
        
        # Clear cache
        cache_key = f"permissions:{user_id}"
        if cache_key in self.cache:
            del self.cache[cache_key]
        
        logger.info(f"✅ Revoked {dimension_type}={dimension_value} from user {user_id}")
```

### Task 2.3: ClickHouse RBAC Views

**File: `backend/scripts/create_rbac_views.py`**

```python
import clickhouse_driver

def create_user_view(user_id: str, permissions: UserPermissions):
    """Create ClickHouse view for user based on permissions"""
    
    ch_client = clickhouse_driver.Client(
        host='abc123.clickhouse.cloud',
        port=9440,
        secure=True
    )
    
    view_name = f"sales_user_{user_id}_view"
    
    # Build WHERE clause from permissions
    conditions = []
    
    if permissions.businesses != "*":
        business_list = "', '".join(permissions.businesses)
        conditions.append(f"business IN ('{business_list}')")
    
    if permissions.channels != "*":
        channel_list = "', '".join(permissions.channels)
        conditions.append(f"channel IN ('{channel_list}')")
    
    if permissions.customers != "*":
        customer_list = "', '".join(permissions.customers[:100])  # Limit for SQL
        conditions.append(f"customer IN ('{customer_list}')")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Select only allowed columns
    allowed_columns = ["date", "year", "month", "business", "channel", "customer", "brand"]
    
    if permissions.data_access.revenue:
        allowed_columns.append("gsales")
    if permissions.data_access.profit:
        allowed_columns.append("fgp")
    if permissions.data_access.cost:
        allowed_columns.extend(["group_cost", "transfer_cost"])
    if permissions.data_access.finance:
        allowed_columns.extend(["lta", "price_downs", "perm_disc"])
    
    columns_str = ", ".join(allowed_columns)
    
    # Create view
    create_view_sql = f"""
    CREATE OR REPLACE VIEW {view_name} AS
    SELECT {columns_str}
    FROM sales_analytics
    WHERE {where_clause}
    """
    
    ch_client.execute(create_view_sql)
    print(f"✅ Created view: {view_name}")
    
    return view_name
```

---

## 📅 WEEK 6-8: AI Chatbot with RBAC

### Task 3.1: Intent-Based Query System

**File: `backend/app/services/query_intent.py`**

```python
from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import date

class QueryIntent(BaseModel):
    """Structured intent from user question"""
    intent_type: Literal["compare", "trend", "breakdown", "summary", "rank"]
    requested_businesses: List[str] | Literal["all"]
    requested_channels: List[str] | Literal["all"]
    requested_metrics: List[str]
    requested_data_types: List[Literal["revenue", "profit", "cost", "finance"]]
    time_period: dict
    aggregation: Literal["sum", "avg", "count", "min", "max"]
    group_by: List[str]
    sort_by: Optional[str] = None
    limit: int = 100

class IntentExtractor:
    """Extract structured intent from natural language"""
    
    async def extract(self, question: str, model: str = "qwen:32b") -> QueryIntent:
        """Use LLM to extract intent"""
        
        prompt = f"""Extract intent from this business question.

Question: "{question}"

Return ONLY valid JSON:
{{
  "intent_type": "compare|trend|breakdown|summary|rank",
  "requested_businesses": ["Food", "Beauty"] or "all",
  "requested_metrics": ["gsales", "cases", "fgp"],
  "requested_data_types": ["revenue", "profit"],
  "time_period": {{"years": [2024], "months": [1,2,3]}},
  "aggregation": "sum",
  "group_by": ["business"],
  "limit": 10
}}"""
        
        # Call your local LLM (Qwen:32b)
        response = await self.call_llm(prompt, model)
        intent = QueryIntent(**json.loads(response))
        return intent
```

### Task 3.2: Query Builder with RBAC

**File: `backend/app/services/query_builder.py`**

```python
class QueryBuilder:
    """Build ClickHouse SQL from intent + RBAC"""
    
    def build(self, intent: QueryIntent, permissions: UserPermissions) -> str:
        """Generate SQL with RBAC filters"""
        
        # Build SELECT
        select_cols = []
        for dim in intent.group_by:
            select_cols.append(dim)
        
        for metric in intent.requested_metrics:
            agg = intent.aggregation.upper()
            select_cols.append(f"{agg}({metric}) as total_{metric}")
        
        select_clause = ", ".join(select_cols)
        
        # Use RBAC view (Database-level security!)
        from_clause = f"sales_user_{permissions.user_id}_view"
        
        # Build WHERE with RBAC
        conditions = []
        
        # Application-level RBAC filters
        if permissions.businesses != "*":
            business_list = "', '".join(permissions.businesses)
            conditions.append(f"business IN ('{business_list}')")
        
        # Intent filters (already validated against RBAC)
        if intent.requested_businesses != "all":
            business_list = "', '".join(intent.requested_businesses)
            conditions.append(f"business IN ('{business_list}')")
        
        # Time filters
        if "years" in intent.time_period:
            years = ", ".join(str(y) for y in intent.time_period["years"])
            conditions.append(f"year IN ({years})")
        
        where_clause = " AND ".join(conditions)
        
        # Build GROUP BY
        group_by = f"GROUP BY {', '.join(intent.group_by)}" if intent.group_by else ""
        
        # Build ORDER BY
        order_by = f"ORDER BY {intent.sort_by} DESC" if intent.sort_by else ""
        
        # Build final SQL with safety limits
        sql = f"""
        SELECT {select_clause}
        FROM {from_clause}
        WHERE {where_clause}
        {group_by}
        {order_by}
        LIMIT {min(intent.limit, 1000000)}
        SETTINGS max_execution_time = 30
        """
        
        return sql.strip()
```

### Task 3.3: Complete Chat Endpoint

**File: `backend/app/api/v1/routes/chat.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.rbac_service import RBACService
from app.services.query_intent import IntentExtractor
from app.services.query_builder import QueryBuilder
import time

router = APIRouter()

@router.post("/api/v2/chat")
async def chat_with_rbac(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """AI Chat with RBAC enforcement"""
    start_time = time.time()
    
    # STEP 1: Get user permissions
    rbac_service = RBACService(db)
    permissions = await rbac_service.get_user_permissions(user_id)
    
    # STEP 2: Extract intent with LLM
    intent_extractor = IntentExtractor()
    intent = await intent_extractor.extract(request.message)
    
    # STEP 3: Validate intent against RBAC
    filtered_intent, warnings = await validate_intent(intent, permissions)
    
    if not filtered_intent:
        return {"response": "⛔ You don't have access to this data"}
    
    # STEP 4: Build SQL with RBAC
    query_builder = QueryBuilder()
    sql = query_builder.build(filtered_intent, permissions)
    
    # STEP 5: Execute on ClickHouse
    result = await execute_clickhouse(sql)
    
    # STEP 6: Format response with LLM
    response = await format_response(result, request.message, warnings)
    
    # Log metrics
    latency = time.time() - start_time
    logger.info(f"✅ Chat response: {latency*1000:.0f}ms, user={user_id}")
    
    return {
        "response": response,
        "warnings": warnings,
        "latency_ms": int(latency * 1000)
    }
```

---

## 📅 WEEK 9-10: Dashboard with RBAC

### Task 4.1: Apply RBAC to All Dashboard Endpoints

**Example: Executive Dashboard**

**File: `backend/app/api/v1/routes/analytics.py`**

```python
@router.get("/analytics/executive-dashboard")
async def get_executive_dashboard(
    years: Optional[str] = None,
    months: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Executive dashboard with RBAC"""
    
    # Get user permissions
    rbac_service = RBACService(db)
    permissions = await rbac_service.get_user_permissions(user_id)
    
    # Build RBAC-filtered query
    base_query = {}
    if years:
        base_query["year"] = {"$in": parse_years(years)}
    
    # Apply RBAC filters
    if permissions.businesses != "*":
        base_query["business"] = {"$in": permissions.businesses}
    
    if permissions.channels != "*":
        base_query["channel"] = {"$in": permissions.channels}
    
    # Execute on ClickHouse (using user's view)
    result = await clickhouse.execute(f"""
        SELECT
            business,
            SUM(gsales) as total_sales,
            SUM(fgp) as total_profit
        FROM sales_user_{user_id}_view
        WHERE {build_where_clause(base_query)}
        GROUP BY business
    """)
    
    return format_dashboard_data(result)
```

---

## 📅 WEEK 11-12: Testing & Production

### Task 5.1: Testing Checklist

```bash
# Create test script
cat > backend/tests/test_rbac.py
```

**File: `backend/tests/test_rbac.py`**

```python
import pytest
from app.services.rbac_service import RBACService

class TestRBAC:
    """Test RBAC implementation"""
    
    async def test_superadmin_access(self):
        """Superadmin should see all data"""
        permissions = await rbac_service.get_user_permissions("superadmin_id")
        assert permissions.businesses == "*"
        assert permissions.data_access.finance == True
    
    async def test_manager_access(self):
        """Manager should see only assigned business"""
        permissions = await rbac_service.get_user_permissions("manager_id")
        assert permissions.businesses == ["Food"]
        assert permissions.data_access.profit == True
        assert permissions.data_access.finance == False
    
    async def test_sales_access(self):
        """Sales should see revenue only"""
        permissions = await rbac_service.get_user_permissions("sales_id")
        assert permissions.data_access.revenue == True
        assert permissions.data_access.profit == False
    
    async def test_query_with_rbac(self):
        """Query should respect RBAC"""
        intent = QueryIntent(requested_businesses=["Beauty"])
        permissions = UserPermissions(businesses=["Food"])
        
        # Should filter to only Food
        filtered_intent, warnings = await validate_intent(intent, permissions)
        assert filtered_intent.requested_businesses == []
        assert "Beauty" in warnings[0]
```

---

## 🎯 **FINAL RECOMMENDATION**

### ✅ **Use This Hybrid Architecture**:

```
MongoDB (Keep):
  • Users & RBAC rules
  • Auth & sessions
  • Current size: <1GB
  • Cost: ~$50-100/month

ClickHouse Cloud (Migrate):
  • All analytics data (50-60 crore rows)
  • Fast aggregations (<500ms even at scale)
  • Auto-scaling
  • Cost: ~$200-400/month (grows with usage)

Total Cost: ~$300-500/month
Performance: 10-50x faster than MongoDB alone
```

### 📊 Expected Performance at Scale

| Data Size | MongoDB Alone | Hybrid (MongoDB + ClickHouse) | Improvement |
|-----------|--------------|-------------------------------|-------------|
| 1 lakh rows | 200ms | 50ms | 4x faster |
| 1 crore rows | 2-5 sec | 100ms | **20-50x faster** |
| 50-60 crore rows | 30-60 sec ❌ | 200-500ms ✅ | **100x faster** |

---

## 🚀 **START HERE - Quick Start Commands**

```bash
# Week 1: Setup
# 1. Sign up for ClickHouse Cloud: https://clickhouse.cloud
# 2. Create service and get credentials

# 3. Install Python dependencies
cd backend
pip install clickhouse-driver motor pymongo redis pydantic

# 4. Create schema
python scripts/create_clickhouse_schema.py

# 5. Migrate current data
python scripts/migrate_to_clickhouse.py

# Week 3: RBAC Setup
# 6. Create RBAC tables in MongoDB
python scripts/setup_rbac_tables.py

# 7. Create test users
python scripts/create_test_users.py

# Week 6: Implement intent system
# 8. Test intent extraction
python tests/test_intent_extraction.py

# Week 11: Full testing
pytest tests/test_rbac.py -v
pytest tests/test_performance.py -v

# Week 12: Production deploy
# Deploy with confidence! 🚀
```

---

## 📝 **SUCCESS CRITERIA**

### ✅ Phase 1 Complete When:
- [ ] ClickHouse Cloud running with 1 lakh+ rows
- [ ] RBAC enforced in all endpoints (dashboard + chatbot)
- [ ] Response time <500ms for all queries
- [ ] Users see only authorized data
- [ ] Audit logs tracking all access
- [ ] Tests passing (RBAC + Performance)

---

**This is your production-ready roadmap. Follow it step-by-step for secure, fast, scalable BizPulse!** 🚀
