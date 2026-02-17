# 🚨 PRODUCTION CRITICAL: Tenant ID & Time Filter Enforcement

**Status:** ⚠️ **NOT YET IMPLEMENTED** - Must be fixed before production deployment

**Priority:** 🔴 **CRITICAL** - Multi-tenant data isolation and performance protection

---

## 🔴 Critical Issue #1: tenant_id Not Enforced

### Problem
The current `ClickHouseClient` executes queries **without enforcing tenant_id**. This means:
- ❌ Queries can access data from other tenants
- ❌ Multi-tenant isolation is broken
- ❌ Security risk: data leakage between clients

### Current State
```python
# backend/app/database/clickhouse_client.py
def execute(self, query: str, params: tuple = None):
    # Just executes query as-is - NO tenant_id enforcement!
    return self.client.execute(query, params)
```

### Required Fix
**Every query MUST include `WHERE tenant_id = ?`** (or `IN (?)` for multi-tenant queries).

### Implementation Options

**Option A: Query Builder Wrapper (Recommended)**
```python
def execute_with_tenant(
    self,
    query: str,
    tenant_id: str,
    params: tuple = None
):
    """Automatically inject tenant_id into WHERE clause"""
    # Parse query and inject tenant_id filter
    # Ensure WHERE clause exists, add tenant_id filter
    # Execute modified query
```

**Option B: Hard Enforcement at Client Level**
```python
def execute(self, query: str, tenant_id: str, params: tuple = None):
    """Execute query with mandatory tenant_id"""
    # Always add tenant_id to WHERE clause
    # Raise error if tenant_id not provided
```

**Option C: Database-Level Views (Most Secure)**
- Create tenant-specific views: `sales_analytics_client_001`, `sales_analytics_client_002`
- RBAC views automatically filter by tenant_id
- Application uses view name based on tenant

### Recommendation
**Use Option A + Option C combination:**
- Create tenant-specific RBAC views (most secure)
- Query builder wrapper ensures tenant_id is always present (defense in depth)

---

## 🔴 Critical Issue #2: No Default Time Filter

### Problem
When users don't specify a date range, queries can scan **entire history**:
- ❌ "Show me top brands" → scans all time (slow, expensive)
- ❌ AI vague questions → accidental full-table scans
- ❌ Performance degradation at scale

### Current State
No default time filter implementation found in:
- `clickhouse_client.py`
- `query_builder.py`
- `insights_service.py`

### Required Fix
**Default to last 24 months** when no date filter is present.

### Implementation
```python
def add_default_time_filter(query: str, has_date_filter: bool) -> str:
    """
    Add default time filter if none exists
    
    Default: last 24 months
    """
    if not has_date_filter:
        # Add: AND date >= addMonths(today(), -24)
        # Or: AND year >= year(today()) - 2
        pass
```

### Where to Implement
1. **AI Query Layer** (`insights_service.py`, `server.py` AI endpoints)
   - Check if user message contains date/time keywords
   - If not, add default filter before building query

2. **Query Builder** (`query_builder.py`)
   - Check WHERE clause for date/year/month filters
   - If missing, inject default time filter

3. **ClickHouse Client** (as fallback)
   - Parse query before execution
   - Add default filter if missing

### Recommendation
**Implement at Query Builder level** - single point of enforcement.

---

## 🔴 Critical Issue #3: Direct INSERTs Without Column Names

### Problem
Current migration script uses:
```python
ch_client.execute(f'INSERT INTO {CLICKHOUSE_DB}.sales_analytics VALUES', batch)
```

This relies on **implicit column order**. If schema changes, INSERTs break.

### Required Fix
**Always use explicit column names:**
```python
INSERT INTO sales_analytics (
    tenant_id, date, business, channel, customer, brand, 
    category, sub_category, sku, cases, gsales, price_downs, 
    perm_disc, transfer_cost, group_cost, lta, fgp, created_at
) VALUES (...)
```

### Status
✅ **FIXED** - Migration script updated to match new schema order, but should still use explicit column names for safety.

---

## ✅ Implementation Checklist

### Phase 1: Tenant ID Enforcement (CRITICAL)
- [ ] Update `ClickHouseClient.execute()` to require `tenant_id` parameter
- [ ] Create `_inject_tenant_filter()` helper method
- [ ] Update all query execution methods to enforce tenant_id
- [ ] Add tenant_id to RBAC view creation scripts
- [ ] Test: Verify queries without tenant_id fail
- [ ] Test: Verify queries with wrong tenant_id return empty results

### Phase 2: Default Time Filter (CRITICAL)
- [ ] Create `_add_default_time_filter()` helper method
- [ ] Detect if query has date/year/month filters
- [ ] Inject `AND date >= addMonths(today(), -24)` if missing
- [ ] Add configuration option for default window (24 months)
- [ ] Test: Verify queries without date filter get default applied
- [ ] Test: Verify queries with date filter don't get modified

### Phase 3: Query Builder Safety (HIGH PRIORITY)
- [ ] Create `SafeQueryBuilder` class
- [ ] Enforce tenant_id injection
- [ ] Enforce default time filter
- [ ] Add query validation (no DROP, no DELETE, etc.)
- [ ] Add LIMIT enforcement (max 10K rows)
- [ ] Update all AI endpoints to use SafeQueryBuilder

### Phase 4: System-Level Protection (RECOMMENDED)
- [ ] Add `max_execution_time` to ClickHouse client settings (already done: 30s)
- [ ] Add `max_rows_to_read` limit
- [ ] Add `max_memory_usage` limit
- [ ] Add query logging/audit trail

---

## 🎯 Quick Win: Update ClickHouse Client

**Immediate action:** Update `clickhouse_client.py` to enforce tenant_id:

```python
def execute_with_tenant(
    self,
    query: str,
    tenant_id: str,
    params: tuple = None
) -> List[tuple]:
    """
    Execute query with mandatory tenant_id enforcement
    
    Args:
        query: SQL query (will have tenant_id injected)
        tenant_id: Tenant identifier (e.g., 'client_001')
        params: Query parameters
    """
    # Inject tenant_id into WHERE clause
    modified_query = self._inject_tenant_filter(query, tenant_id)
    
    # Add default time filter if missing
    modified_query = self._add_default_time_filter(modified_query)
    
    return self.execute(modified_query, params)
```

---

## 📊 Impact Assessment

### Without These Fixes:
- 🔴 **Security Risk:** Multi-tenant data leakage
- 🔴 **Performance Risk:** Full-table scans on vague queries
- 🔴 **Scalability Risk:** Queries become slower as data grows
- 🔴 **Cost Risk:** Unnecessary compute usage

### With These Fixes:
- ✅ **Secure:** Tenant isolation guaranteed
- ✅ **Performant:** Default time filters prevent full scans
- ✅ **Scalable:** Queries optimized for time-based access patterns
- ✅ **Cost-Effective:** Reduced unnecessary data scanning

---

## 🚀 Next Steps

1. **Immediate:** Implement tenant_id enforcement in ClickHouse client
2. **Immediate:** Add default time filter logic
3. **This Week:** Update all query execution points to use new methods
4. **This Week:** Add comprehensive tests
5. **Next Sprint:** Create tenant-specific RBAC views

---

**Last Updated:** Based on architect review of schema implementation
**Owner:** Backend Team
**Status:** 🔴 Critical - Must fix before production deployment
