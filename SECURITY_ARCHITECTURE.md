# BizPulse Security Architecture
## Centralized Security Policy & Implementation Guide

**Document Purpose**: Centralized reference for all security policies, patterns, and requirements across BizPulse's analytics platform.

**Last Updated**: February 11, 2026  
**Status**: Production-Grade Implementation  
**Scope**: Phase 1 mandatory requirements

---

## 🎯 Security Architecture Overview

### Core Security Principles

1. **Fail-Secure**: When in doubt, deny access
2. **Defense in Depth**: Multiple security layers (JWT → MongoDB → Query Builder → ClickHouse)
3. **Zero Trust**: Never trust client input or LLM output
4. **Least Privilege**: Users see only data they're explicitly granted access to
5. **Audit Everything**: Every query logged with full context

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Authentication (JWT)                               │
│  ├─ Validates user identity                                 │
│  ├─ Contains: user_id, role, perm_version                   │
│  └─ Does NOT contain full permissions                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Authorization (MongoDB)                            │
│  ├─ Fetches fresh permissions on EVERY request              │
│  ├─ Single source of truth for access control               │
│  └─ Validates perm_version for cache invalidation           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: LLM Intent Parsing (Structured Output)             │
│  ├─ LLM generates INTENT, not SQL                           │
│  ├─ Output: JSON with metrics, dimensions, filters          │
│  └─ NEVER trust LLM output directly                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Query Builder (Backend)                            │
│  ├─ Validates intent against whitelists                     │
│  ├─ Builds SQL with parameterization                        │
│  ├─ Injects RBAC WHERE clauses                              │
│  └─ Applies resource limits (timeout, memory, rows)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: ClickHouse Execution                               │
│  ├─ Executes parameterized query                            │
│  ├─ Enforces timeouts and memory limits                     │
│  └─ Returns results                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication & Authorization

### JWT Structure (Mandatory)

**✅ CORRECT:**
```json
{
  "user_id": "usr_123",
  "role": "sales",
  "perm_version": 5,
  "exp": "2026-02-11T..."
}
```

**❌ NEVER:**
```json
{
  "user_id": "usr_123",
  "access_level": {
    "businesses": ["Food"],
    "channels": ["Convenience"]
  }
}
```

**Why**: Permissions in JWT cannot be revoked until token expires. Always fetch from MongoDB.

### MongoDB Permission Structure

```python
{
    "user_id": "usr_123",
    "email": "sales@company.com",
    "role": "sales",
    "password_hash": "$2b$12$...",  # bcrypt hash
    "perm_version": 5,  # Increment when permissions change
    "access_level": {
        "businesses": ["Food", "Beauty"],
        "channels": ["Convenience", "Direct"],
        "brands": ["Heinz", "Dove"],
        "categories": ["*"],  # Wildcard = all
        "sub_categories": ["*"],
        "customers": ["*"],
        "data_types": ["revenue", "profit"]  # NOT "costs"
    }
}
```

### perm_version Enforcement (Mandatory)

```python
# Middleware-level check
async def rbac_middleware(request: Request, call_next):
    user_id = get_user_id_from_jwt(request)
    token_perm_version = request.state.jwt_payload.get("perm_version")
    
    try:
        # Fetch from MongoDB
        user = await mongo_db.users_permissions.find_one(
            {"user_id": user_id},
            {"access_level": 1, "perm_version": 1}
        )
        
        # FAIL-SECURE: Deny if not found
        if not user:
            raise HTTPException(401, "User not found")
        
        # FAIL-SECURE: Validate perm_version
        if token_perm_version != user["perm_version"]:
            raise HTTPException(
                401,
                "Permissions updated. Please login again."
            )
        
        # Attach to request
        request.state.access_level = user["access_level"]
        
    except PyMongoError as e:
        logger.exception(f"MongoDB error for user {user_id}")
        # FAIL-SECURE: Database error → deny
        raise HTTPException(503, "Authentication service unavailable")
    
    return await call_next(request)
```

---

## 🛡️ SQL Injection Prevention

### Rule 1: ALWAYS Use Parameterized Queries

**✅ CORRECT:**
```python
query = "SELECT sum(gsales) FROM sales_analytics WHERE business = %(business)s"
params = {"business": "Food"}
results = client.execute(query, params)
```

**❌ NEVER:**
```python
business = "Food"
query = f"SELECT sum(gsales) FROM sales_analytics WHERE business = '{business}'"
```

### Rule 2: Whitelist Validation

**Metric Whitelist:**
```python
ALLOWED_METRICS = {
    "total_sales": "sum(gsales)",
    "total_profit": "sum(fgp)",
    "total_units": "sum(cases)",
    "avg_price": "sum(gsales) / sum(cases)",
    "margin_pct": "(sum(fgp) / sum(gsales)) * 100"
}

def validate_metric(metric):
    if metric not in ALLOWED_METRICS:
        raise ValueError(f"Unauthorized metric: {metric}")
    return ALLOWED_METRICS[metric]
```

**Dimension Whitelist:**
```python
ALLOWED_DIMENSIONS = [
    "year", "month", "month_name", "quarter",
    "business", "channel", "brand", "category", "sub_category"
]

# Explicitly EXCLUDED (high-cardinality):
# "customer", "sku", "transaction_id", "invoice_id"
```

### Rule 3: Empty Tuple Guard

```python
def build_rbac_filters(access_level):
    businesses = access_level.get("businesses", [])
    
    # FAIL-SECURE: Empty list → deny
    if not businesses:
        raise PermissionError("No business access configured for user.")
    
    # Safe parameterization
    params = {"businesses": tuple(businesses)}
    query = " AND business IN %(businesses)s"
    return query, params
```

---

## 🤖 LLM Security (Intent-Based Queries)

### LLM Never Generates SQL Directly

**✅ CORRECT Flow:**
```
User Question → LLM → Structured Intent (JSON) → Query Builder → Safe SQL
```

**❌ NEVER:**
```
User Question → LLM → Raw SQL → Execute
```

### Intent Structure

```json
{
  "metrics": ["total_sales", "total_profit"],
  "dimensions": ["business", "channel"],
  "filters": {
    "year": 2025,
    "month": 1
  },
  "sort": {"total_sales": "DESC"},
  "limit": 100
}
```

### Query Builder Validation

```python
def build_query_from_intent(intent, access_level):
    # 1. Validate metrics
    for metric in intent["metrics"]:
        if metric not in ALLOWED_METRICS:
            raise ValueError(f"Invalid metric: {metric}")
    
    # 2. Validate dimensions
    for dim in intent["dimensions"]:
        if dim not in ALLOWED_DIMENSIONS:
            raise ValueError(f"Invalid dimension: {dim}")
    
    # 3. Build SELECT clause
    select_parts = [
        f"{ALLOWED_METRICS[m]} AS {m}" 
        for m in intent["metrics"]
    ]
    
    # 4. Inject RBAC filters (parameterized)
    rbac_query, rbac_params = build_rbac_filters(access_level)
    
    # 5. Assemble query
    query = f"SELECT {', '.join(select_parts)} FROM sales_analytics WHERE 1=1{rbac_query}"
    
    return query, rbac_params
```

---

## ⏱️ Resource Controls (Mandatory)

### ClickHouse Client Configuration

```python
from clickhouse_driver import Client

client = Client(
    host='192.168.50.29',
    port=9000,  # Native TCP protocol (fastest)
    settings={
        'max_execution_time': 30,           # 30 second timeout
        'max_memory_usage': 2_000_000_000,  # 2GB memory limit
        'max_rows_to_read': 1_000_000,      # Max 1M rows scanned
        'max_result_rows': 10_000           # Max 10K rows returned
    }
)
```

### Query Limits

```python
def build_safe_query(intent, access_level):
    query = build_base_query(intent, access_level)
    
    # ALWAYS add LIMIT (non-negotiable)
    max_rows = 10000
    query += f" LIMIT {max_rows}"
    
    return query
```

---

## 🔍 Audit Logging (Mandatory)

### Query ID + Correlation ID

```python
import uuid
import time
import logging

logger = logging.getLogger(__name__)

# Generate unique identifiers
query_id = str(uuid.uuid4())
request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

# Execute with query_id
start_time = time.time()
results = client.execute(query, params, query_id=query_id)
execution_time_ms = (time.time() - start_time) * 1000

# Log with full context
logger.info(
    "Query executed",
    extra={
        "user_id": user_id,
        "query_id": query_id,
        "request_id": request_id,
        "intent": intent,
        "execution_time_ms": execution_time_ms,
        "rows_returned": len(results),
        "status": "success"
    }
)
```

---

## 🚨 Error Handling

### Never Expose Internal Details

**✅ CORRECT:**
```python
try:
    results = client.execute(query, params)
except Exception as e:
    # Log full error internally
    logger.exception(f"ClickHouse query failed for user {user_id}")
    
    # Return generic error to client
    raise HTTPException(
        status_code=500,
        detail="Query execution error. Please try again or contact support."
    )
```

**❌ NEVER:**
```python
except Exception as e:
    return {"error": str(e)}  # Leaks SQL, table names, internals
```

---

## 🔄 Failure Behavior Strategy

**BizPulse uses FAIL-SECURE**: When in doubt, DENY access.

| Scenario | Behavior | HTTP Code |
|----------|----------|-----------|
| MongoDB connection failure | ❌ Deny | 503 Service Unavailable |
| Empty permissions list | ❌ Deny | 403 No Access Configured |
| Invalid `perm_version` | ❌ Deny | 401 Token Outdated |
| ClickHouse connection failure | ❌ Deny | 503 Database Unavailable |
| Query timeout | ❌ Deny | 408 Query Timeout |
| Empty tuple in `IN ()` clause | ❌ Deny | 403 No Access Configured |
| Invalid metric | ❌ Deny | 400 Invalid Metric |
| Invalid dimension | ❌ Deny | 400 Invalid Dimension |

---

## 📋 Production Deployment Checklist

### Pre-Deployment Security Audit

#### Authentication & Authorization
- [ ] JWT contains ONLY `user_id`, `role`, `perm_version`
- [ ] Permissions fetched from MongoDB on every request
- [ ] `perm_version` validated in centralized middleware
- [ ] Empty permission lists denied with clear error

#### SQL Injection Prevention
- [ ] All queries use parameterized format (`%(name)s`)
- [ ] No string concatenation or f-strings in SQL
- [ ] Metric whitelist enforced
- [ ] Dimension whitelist enforced
- [ ] Empty tuple guard implemented

#### LLM Security
- [ ] LLM generates intent (JSON), not SQL
- [ ] All intent fields validated against whitelists
- [ ] No arbitrary expressions from LLM
- [ ] Query Builder is sole SQL generator

#### Resource Controls
- [ ] Query timeout configured (30 seconds)
- [ ] Memory limit configured (2GB)
- [ ] Max rows to read configured (1M)
- [ ] Max result rows configured (10K)
- [ ] LIMIT clause always added to queries

#### Audit & Monitoring
- [ ] Query ID generated and logged
- [ ] Correlation ID (X-Request-ID) captured
- [ ] Full context logged (user, query, timing, status)
- [ ] Structured logging format (JSON)

#### Error Handling
- [ ] Generic errors returned to client
- [ ] Full exceptions logged internally
- [ ] No SQL or internal details exposed
- [ ] Fail-secure behavior for all edge cases

---

## 🔗 Related Documentation

- **RBAC_PRODUCTION_HARDENED_VERSION.md** - Detailed RBAC implementation
- **PRODUCTION_SECURITY_IMPLEMENTATION.md** - Code examples and patterns
- **START_HERE.md** - Architecture overview and setup guide
- **COMPLETE_SETUP_CHECKLIST.md** - Step-by-step deployment guide

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial centralized security architecture document |

---

**Document Status**: ✅ Production-Ready  
**Approval**: Architecture review completed  
**Next Review**: Before Phase 2 features
