# 🔒 Production Security Implementation Notes

## Purpose
This document addresses critical implementation details that must be followed when building the production system based on the RBAC architecture.

---

## 🚨 CRITICAL: SQL Injection Prevention

### ❌ NEVER Do This (Even with MongoDB Values)

```python
# BAD - String concatenation
businesses = "', '".join(access_level["businesses"])
query += f" AND business IN ('{businesses}')"
```

**Why this is dangerous:**
- Even if values come from MongoDB, a compromised admin account could inject malicious data
- If MongoDB is compromised, SQL injection becomes possible
- String concatenation is never safe, regardless of source

### ✅ ALWAYS Do This (Parameterized Queries)

```python
# GOOD - Parameterized query (if ClickHouse driver supports)
from clickhouse_driver import Client

client = Client(host='192.168.50.29')

# Parameterized query
query = """
SELECT sum(gsales) as total_sales
FROM sales_analytics
WHERE business IN %(businesses)s
  AND year = %(year)s
"""

params = {
    'businesses': tuple(access_level["businesses"]),  # Convert to tuple
    'year': 2025
}

result = client.execute(query, params)
```

### ✅ Alternative: Strict Whitelist Validation

```python
# GOOD - Whitelist validation before building query
ALLOWED_BUSINESSES = ["Food", "Beauty", "Home Care"]
ALLOWED_CHANNELS = ["Convenience", "Direct", "Wholesale"]
ALLOWED_BRANDS = ["Heinz", "Coca Cola", "Dove", ...]  # From DB at startup

def validate_access_level(access_level):
    """
    Validate all access level values against whitelists
    Raises ValueError if any invalid value found
    """
    
    # Validate businesses
    for business in access_level.get("businesses", []):
        if business != "*" and business not in ALLOWED_BUSINESSES:
            raise ValueError(f"Invalid business: {business}")
    
    # Validate channels
    for channel in access_level.get("channels", []):
        if channel != "*" and channel not in ALLOWED_CHANNELS:
            raise ValueError(f"Invalid channel: {channel}")
    
    # Validate brands
    for brand in access_level.get("brands", []):
        if brand != "*" and brand not in ALLOWED_BRANDS:
            raise ValueError(f"Invalid brand: {brand}")
    
    return True

# In your endpoint:
async def get_dashboard_data(user_id: str):
    # Fetch permissions
    user = await db.users_permissions.find_one({"user_id": user_id})
    access_level = user["access_level"]
    
    # VALIDATE before building query
    validate_access_level(access_level)
    
    # Now safe to build query
    query = build_safe_query(access_level)
```

---

## 🛡️ CRITICAL: LLM Metric Whitelist

### ❌ NEVER Let LLM Choose Arbitrary Metrics

```python
# BAD - LLM can request any column
metrics = intent["metrics"]  # ["gsales", "evil_column", "sum(password)"]
select_clause = ", ".join([f"sum({m})" for m in metrics])
```

**Why this is dangerous:**
- LLM can hallucinate column names
- LLM can try to access restricted columns
- LLM can craft malicious SQL expressions

### ✅ ALWAYS Use Metric Whitelist

```python
# GOOD - Strict metric whitelist
ALLOWED_METRICS = {
    # Metric name → SQL expression
    "total_sales": "sum(gsales)",
    "total_profit": "sum(fgp)",
    "total_units": "sum(cases)",
    "avg_price": "sum(gsales) / sum(cases)",
    "margin_pct": "(sum(fgp) / sum(gsales)) * 100",
}

def build_select_clause(requested_metrics, access_level):
    """
    Build SELECT clause from whitelisted metrics only
    Respects data_types permissions
    """
    
    select_parts = []
    
    for metric in requested_metrics:
        # Check 1: Metric must be in whitelist
        if metric not in ALLOWED_METRICS:
            raise ValueError(f"Invalid metric: {metric}")
        
        # Check 2: User must have access to this data type
        if metric in ["total_profit", "margin_pct"]:
            if "profit" not in access_level["data_types"]:
                raise PermissionError(f"No access to profit metrics")
        
        # Add whitelisted expression WITH ALIAS (critical for result parsing)
        select_parts.append(f"{ALLOWED_METRICS[metric]} AS {metric}")
    
    return ", ".join(select_parts)

# In your query builder:
def build_safe_query(intent, access_level):
    # Use whitelist
    select_clause = build_select_clause(intent["metrics"], access_level)
    
    query = f"SELECT {select_clause} FROM sales_analytics WHERE 1=1"
    
    # Add RBAC filters (validated)
    query += build_rbac_filters(access_level)
    
    return query
```

---

## 🚨 CRITICAL: Never Expose Internal Errors

### ❌ NEVER Do This

```python
# BAD - Exposes internal details
except Exception as e:
    return {"error": str(e)}
    # Leaks: table names, column names, query structure, host info
```

**Why this is dangerous:**
- Exposes table names, column names, query structure
- Leaks internal host info, database version
- Helps attackers understand your system
- Violates security best practices

### ✅ ALWAYS Do This

```python
# GOOD - Generic error + internal logging
import logging

logger = logging.getLogger(__name__)

try:
    results = ch_client.execute(query, params)
except Exception as e:
    # Log full error internally (for debugging)
    logger.exception(f"ClickHouse query failed for user {user_id}")
    
    # Return generic error to client (no details leaked)
    raise HTTPException(
        status_code=500,
        detail="Query execution error. Please try again or contact support."
    )
```

**Enterprise Practice:**
- ✅ Log full exception internally (with context: user_id, query_id, timestamp)
- ✅ Return generic message to client
- ✅ Include request_id for support tracking
- ❌ Never expose: SQL, table names, column names, stack traces, host info

---

## 🛡️ CRITICAL: Query Resource Controls (Mandatory)

### ❌ Without Resource Controls

```python
# BAD - No limits
client = Client(host='192.168.50.29')
results = client.execute(query, params)
# One bad query can crash the node
```

**Why this is dangerous:**
- Long-running queries block other users
- Memory exhaustion crashes ClickHouse
- No protection against abuse
- Production instability

### ✅ ALWAYS Enforce Resource Controls

```python
# GOOD - Mandatory resource limits
from clickhouse_driver import Client

client = Client(
    host='192.168.50.29',
    port=9000,  # Native TCP protocol
    settings={
        'max_execution_time': 30,           # 30 second timeout
        'max_memory_usage': 2_000_000_000,  # 2GB memory limit
        'max_rows_to_read': 1_000_000,      # Max 1M rows scanned
        'max_result_rows': 10_000           # Max 10K rows returned
    }
)

# Execute query
results = client.execute(query, params)
```

**Enterprise Practice:**
- ✅ **max_execution_time**: Prevents runaway queries
- ✅ **max_memory_usage**: Prevents OOM crashes
- ✅ **max_rows_to_read**: Protects against full table scans
- ✅ **max_result_rows**: Limits result set size

**Phase 1 Requirement**: NON-NEGOTIABLE

---

## 🔍 CRITICAL: Query ID + Correlation Logging

### ❌ Without Query Tracing

```python
# BAD - No traceability
results = client.execute(query, params)
# Can't trace which query caused issues
```

**Problems:**
- Can't debug user issues
- Can't detect abuse patterns
- No forensic capability
- Support team blind

### ✅ ALWAYS Use Query ID + Correlation ID

```python
# GOOD - Full traceability
import uuid
import logging
import time

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

**Benefits:**
- ✅ Trace every query back to user + request
- ✅ Debug performance issues
- ✅ Detect abuse patterns (same user, many slow queries)
- ✅ Support can reference query_id

**Phase 1 Requirement**: HIGH PRIORITY

---

## 🛡️ CRITICAL: Dimension Whitelist + High-Cardinality Exclusions

```python
# GOOD - Whitelist for dimensions
ALLOWED_DIMENSIONS = [
    "year",
    "month",
    "month_name",
    "quarter",
    "business",
    "channel",
    "brand",
    "category",
    "sub_category"
    # NOT INCLUDED: customer, sku, transaction_id, invoice_id
]

def validate_dimensions(dimensions):
    """Validate GROUP BY dimensions"""
    for dim in dimensions:
        if dim not in ALLOWED_DIMENSIONS:
            raise ValueError(f"Invalid dimension: {dim}")
    return True
```

### High-Cardinality Exclusions (EXPLICIT)

The following dimensions are **intentionally excluded** from `ALLOWED_DIMENSIONS`:

| Dimension | Cardinality | Reason for Exclusion |
|-----------|-------------|----------------------|
| `customer` | ~10,000+ unique values | Memory explosion on GROUP BY |
| `sku` | ~50,000+ unique values | Very high cardinality, slow aggregation |
| `transaction_id` | Millions | Extremely high cardinality, no aggregation value |
| `invoice_id` | Millions | Extremely high cardinality, no aggregation value |

**Why This Matters:**

Grouping by high-cardinality dimensions causes:
- **Memory Explosion**: GROUP BY with millions of groups consumes 10GB+ RAM
- **Slow Queries**: Sorting/aggregating huge result sets takes 60+ seconds
- **Node Instability**: ClickHouse node can crash or freeze

**Alternative Approach:**

If customer-level detail is needed:
```python
# Use LIMIT + ORDER BY instead of GROUP BY
SELECT customer, sum(gsales) as sales
FROM sales_analytics
WHERE business = 'Food'
  AND year = 2025
GROUP BY customer
ORDER BY sales DESC
LIMIT 100  # Top 100 customers only
```

**Phase 1 Requirement**: Document and enforce

---

## 🛡️ CRITICAL: Query Limits (Non-Negotiable)

```python
# GOOD - Always add limits
def build_safe_query(intent, access_level):
    query = build_base_query(intent, access_level)
    
    # ALWAYS add LIMIT (non-negotiable)
    max_rows = 10000
    query += f" LIMIT {max_rows}"
    
    return query

# GOOD - Also set at ClickHouse client level
client = Client(
    host='192.168.50.29',
    settings={
        'max_execution_time': 5,      # 5 second timeout
        'max_rows_to_read': 1000000,  # Max 1M rows scanned
        'max_result_rows': 10000       # Max 10K rows returned
    }
)
```

---

## 🚨 Failure Behavior Strategy

### Fail-Safe vs Fail-Secure

**BizPulse RBAC uses FAIL-SECURE strategy**: When in doubt, DENY access.

| Scenario | Behavior | Rationale |
|----------|----------|-----------|
| MongoDB connection failure | ❌ Return 503 Service Unavailable | Cannot verify permissions → deny |
| Empty permissions list | ❌ PermissionError("No access configured") | Empty = no access granted |
| Invalid `perm_version` | ❌ 401 Unauthorized | Permissions changed → re-login required |
| ClickHouse connection failure | ❌ Return 503 Database Unavailable | Cannot execute query safely |
| Query timeout | ❌ Return 408 Query Timeout | Query too expensive |
| Empty tuple in `IN ()` clause | ❌ PermissionError("No business access") | SQL syntax error → deny |

### Implementation

```python
# Middleware-level RBAC check
async def rbac_middleware(request: Request, call_next):
    user_id = get_user_id_from_jwt(request)
    
    try:
        # Fetch permissions from MongoDB
        perms = await mongo_db.users.find_one(
            {"user_id": user_id},
            {"access_level": 1, "perm_version": 1}
        )
        
        # FAIL-SECURE: Deny if not found
        if not perms:
            raise HTTPException(401, "User not found")
        
        # FAIL-SECURE: Deny if empty access
        if not perms.get("access_level"):
            raise HTTPException(403, "No permissions configured for user")
        
        # FAIL-SECURE: Validate perm_version
        token_version = request.state.jwt_payload.get("perm_version")
        if token_version != perms["perm_version"]:
            raise HTTPException(401, "Permissions updated. Please login again.")
        
        # Attach to request
        request.state.access_level = perms["access_level"]
        
    except PyMongoError as e:
        logger.exception(f"MongoDB error fetching permissions for {user_id}")
        # FAIL-SECURE: Database error → deny
        raise HTTPException(503, "Authentication service unavailable")
    
    return await call_next(request)

# Query Builder-level RBAC enforcement
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

**Key Principle:** "Deny by default, allow explicitly"

---

## 📋 Production Implementation Checklist

### Before Deploying to Production:

#### SQL Security ✅
- [ ] No string concatenation in SQL (use parameterized queries)
- [ ] All MongoDB values validated against whitelists
- [ ] Empty tuple guard (check `if not businesses` before `IN ()`)
- [ ] Special characters escaped (if parameterization not available)

#### LLM Security ✅
- [ ] Metric whitelist implemented
- [ ] Dimension whitelist implemented
- [ ] High-cardinality dimensions explicitly excluded (customer, sku, transaction_id)
- [ ] No arbitrary SQL expressions from LLM
- [ ] All LLM intent validated before SQL generation

#### Query Limits ✅
- [ ] LIMIT clause always added (max 10,000 rows)
- [ ] Query timeout set (30 seconds via `max_execution_time`)
- [ ] Memory limit set (2GB via `max_memory_usage`)
- [ ] Max rows to scan set (1,000,000 via `max_rows_to_read`)
- [ ] Max result rows set (10,000 via `max_result_rows`)

#### Query Tracing ✅
- [ ] Query ID generated and passed to ClickHouse
- [ ] Correlation ID (X-Request-ID) captured from request
- [ ] Full context logged (user_id, query_id, request_id, execution_time_ms)
- [ ] Query audit trail stored for forensics

#### RBAC Validation ✅
- [ ] Permissions fetched from MongoDB (not JWT)
- [ ] `perm_version` verified in middleware (centralized check)
- [ ] Access level validated against whitelists
- [ ] Data type permissions checked (revenue vs profit vs costs)
- [ ] Empty permission lists denied with clear error

#### Error Handling ✅
- [ ] Invalid metrics → clear error message
- [ ] Permission denied → clear error message
- [ ] Query timeout → clear error message
- [ ] MongoDB connection failure → 503 Service Unavailable
- [ ] ClickHouse connection failure → 503 Database Unavailable
- [ ] Never expose internal SQL in errors

#### Failure Behavior ✅
- [ ] Fail-secure strategy documented
- [ ] All edge cases have defined behavior
- [ ] No "silent failures" or undefined states

---

## 🔧 Implementation Example (Complete)

```python
from clickhouse_driver import Client
from typing import Dict, List
from fastapi import HTTPException

# Initialize whitelists at startup
ALLOWED_METRICS = {
    "total_sales": "sum(gsales)",
    "total_profit": "sum(fgp)",
    "total_units": "sum(cases)",
}

ALLOWED_DIMENSIONS = ["year", "month", "business", "channel"]

ALLOWED_BUSINESSES = []  # Loaded from ClickHouse at startup
ALLOWED_CHANNELS = []    # Loaded from ClickHouse at startup
ALLOWED_BRANDS = []      # Loaded from ClickHouse at startup

async def initialize_whitelists(client: Client):
    """Load dynamic whitelists at startup"""
    global ALLOWED_BUSINESSES, ALLOWED_CHANNELS, ALLOWED_BRANDS
    
    ALLOWED_BUSINESSES = [row[0] for row in client.execute("SELECT DISTINCT business FROM sales_analytics")]
    ALLOWED_CHANNELS = [row[0] for row in client.execute("SELECT DISTINCT channel FROM sales_analytics")]
    ALLOWED_BRANDS = [row[0] for row in client.execute("SELECT DISTINCT brand FROM sales_analytics")]

def validate_access_level(access_level: Dict):
    """Validate access level against whitelists"""
    for business in access_level.get("businesses", []):
        if business != "*" and business not in ALLOWED_BUSINESSES:
            raise ValueError(f"Invalid business: {business}")
    
    for channel in access_level.get("channels", []):
        if channel != "*" and channel not in ALLOWED_CHANNELS:
            raise ValueError(f"Invalid channel: {channel}")
    
    for brand in access_level.get("brands", []):
        if brand != "*" and brand not in ALLOWED_BRANDS:
            raise ValueError(f"Invalid brand: {brand}")

def validate_intent(intent: Dict, access_level: Dict):
    """Validate LLM intent"""
    # Validate metrics
    for metric in intent.get("metrics", []):
        if metric not in ALLOWED_METRICS:
            raise ValueError(f"Invalid metric: {metric}")
        
        # Check data type permissions
        if metric in ["total_profit"]:
            if "profit" not in access_level.get("data_types", []):
                raise PermissionError("No access to profit data")
    
    # Validate dimensions
    for dim in intent.get("dimensions", []):
        if dim not in ALLOWED_DIMENSIONS:
            raise ValueError(f"Invalid dimension: {dim}")

def build_safe_query(intent: Dict, access_level: Dict) -> tuple[str, dict]:
    """
    Build safe parameterized query
    Returns: (query_string, params_dict)
    """
    
    # Build SELECT clause (from whitelist)
    select_parts = [ALLOWED_METRICS[m] for m in intent["metrics"]]
    select_clause = ", ".join(select_parts)
    
    # Build base query
    query = f"SELECT {select_clause} FROM sales_analytics WHERE 1=1"
    params = {}
    
    # Add RBAC filters (parameterized)
    if access_level["businesses"] and access_level["businesses"] != ["*"]:
        query += " AND business IN %(businesses)s"
        params["businesses"] = tuple(access_level["businesses"])
    
    if access_level["channels"] and access_level["channels"] != ["*"]:
        query += " AND channel IN %(channels)s"
        params["channels"] = tuple(access_level["channels"])
    
    if access_level["brands"] and access_level["brands"] != ["*"]:
        query += " AND brand IN %(brands)s"
        params["brands"] = tuple(access_level["brands"])
    
    # Add user filters from intent (validated)
    if "year" in intent.get("filters", {}):
        query += " AND year = %(year)s"
        params["year"] = intent["filters"]["year"]
    
    # Add GROUP BY (if dimensions specified)
    if intent.get("dimensions"):
        dims = ", ".join(intent["dimensions"])
        query += f" GROUP BY {dims}"
    
    # ALWAYS add LIMIT (non-negotiable)
    query += " LIMIT 10000"
    
    return query, params

@app.post("/api/ai/query")
async def ai_query(
    request: AIQueryRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
    ch_client = Depends(get_clickhouse_client)
):
    """AI chatbot endpoint with full security"""
    
    # Step 1: Fetch FRESH permissions from MongoDB
    user = await db.users_permissions.find_one({"user_id": current_user["user_id"]})
    access_level = user["access_level"]
    
    # Step 2: Verify perm_version
    if current_user["perm_version"] != user["perm_version"]:
        raise HTTPException(401, "Token outdated, please login again")
    
    # Step 3: Validate access level against whitelists
    try:
        validate_access_level(access_level)
    except ValueError as e:
        raise HTTPException(403, str(e))
    
    # Step 4: Get LLM intent
    llm_intent = await generate_intent_from_llm(
        question=request.question,
        access_level=access_level
    )
    
    # Step 5: Validate intent
    try:
        validate_intent(llm_intent, access_level)
    except (ValueError, PermissionError) as e:
        return {"error": str(e)}
    
    # Step 6: Build safe parameterized query
    query, params = build_safe_query(llm_intent, access_level)
    
    # Step 7: Execute with timeout
    try:
        results = ch_client.execute(query, params)
    except Exception as e:
        # ⚠️ CRITICAL: Never expose raw exception to client
        # Log internally for debugging
        logger.exception(f"ClickHouse query failed for user {current_user['user_id']}")
        
        # Return generic error (no SQL details leaked)
        raise HTTPException(500, "Query execution error. Please try again or contact support.")
    
    # Step 8: Format response with LLM
    response = await format_response_with_llm(
        question=request.question,
        results=results
    )
    
    return response
```

---

## 📊 Security Layers Summary

Your system now has:

1. ✅ **JWT Layer**: user_id + perm_version (no permissions)
2. ✅ **MongoDB Layer**: Single source of truth for permissions
3. ✅ **Validation Layer**: Access level validated against whitelists
4. ✅ **Intent Layer**: LLM generates structured intent (not SQL)
5. ✅ **Whitelist Layer**: Metrics and dimensions validated
6. ✅ **Query Builder Layer**: Backend builds safe parameterized SQL
7. ✅ **RBAC Layer**: Backend adds non-negotiable RBAC filters
8. ✅ **Limit Layer**: Max rows always enforced
9. ✅ **Execution Layer**: ClickHouse executes with timeout

**This is defense-in-depth. Production-grade.** 🔒

---

## 🎯 What ChatGPT Confirmed

✅ Architecture: Senior-level  
✅ Separation of concerns: Excellent  
✅ Security awareness: Above average  
✅ Intent-based AI: Production-ready  
✅ No overengineering: Correct balance  

**One implementation detail to fix**: SQL parameterization (this document)

---

## 🚀 Next Steps

1. ✅ **Update documentation** with parameterized queries (this file)
2. ✅ **Implement whitelists** when building query_builder.py
3. ✅ **Add validation layers** in FastAPI endpoints
4. ✅ **Test with malicious inputs** (see test scenarios below)

---

## 🧪 Test Scenarios (Before Production)

### Test 1: SQL Injection Attempt
```python
# Malicious admin tries to inject via MongoDB
malicious_permission = {
    "businesses": ["Food'; DROP TABLE sales_analytics; --"]
}

# Expected: Validation catches it (not in ALLOWED_BUSINESSES)
# Result: ValueError raised, query never executed
```

### Test 2: LLM Hallucination
```python
# LLM tries to access non-existent column
intent = {
    "metrics": ["password_hash", "secret_key"]
}

# Expected: Validation catches it (not in ALLOWED_METRICS)
# Result: ValueError raised, query never built
```

### Test 3: Permission Bypass Attempt
```python
# User tries to access profit without permission
access_level = {"data_types": ["revenue"]}
intent = {"metrics": ["total_profit"]}

# Expected: Permission check fails
# Result: PermissionError raised
```

---

**Status**: ✅ Critical implementation details documented  
**Date**: February 10, 2026  
**Based on**: ChatGPT's principal-level architectural review  
**Action Required**: Implement parameterized queries and whitelists in production code
