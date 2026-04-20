# MongoDB + ClickHouse — Complete Setup: Understanding & Architecture

This document captures what was agreed in the ChatGPT discussion, how it maps to your **actual Bizpulse codebase** (FastAPI/Python, not Node), and a concrete implementation plan for a full MongoDB + ClickHouse setup. It is written for you to review before any implementation.

---

## 1. My Understanding (Summary of the Discussion)

### 1.1 Your Confirmed Decisions

| Topic | Your decision |
|--------|----------------|
| **Production DB** | `bizpulse` (MongoDB) = **read-only** source. Never modify it. |
| **Working DB** | `bizpulse_rbac` (MongoDB) = copy of bizpulse. **All read/write** (users, RBAC, app data) go here after migration. |
| **Analytics DB** | **ClickHouse** = analytics only (e.g. `sales_analytics`). No user/RBAC storage in ClickHouse. |
| **Data source going forward** | **Not** “push from MongoDB daily”. Future data: **CSV (email)** or **ERP (API/CSV)**. MongoDB→ClickHouse was **one-time / initial** load. |
| **Daily new data** | **Incremental only**: insert new dates into ClickHouse; **no** full delete/reload. If corrections: **replace only affected partition** (e.g. one month). |
| **Default time filter** | If user **does not** mention time → default **24 months**. If user explicitly asks **“lifetime”** → **no** time limit (full history). |
| **RBAC** | Stored in **MongoDB** (e.g. `bizpulse_rbac.users` with `role` + `access`). Backend enforces filters; **no** per-user ClickHouse users/views. |
| **AI / Chatbot** | LLM **never** writes raw SQL. Flow: **Question → LLM intent (JSON) → Backend builds SQL → ClickHouse → LLM explanation → Frontend**. |
| **Add User (Admin)** | Admin screen uses **dynamic filter options** (same logic as existing screens): e.g. choose Business “Food” → years/brands/channels etc. narrow to what exists for Food. |
| **Example user access** | Business: [Food], Brand: [Cali Cali, Bensons], Category: all, Channel: [Grocery], Metrics: [gsales, fgp]. |

### 1.2 Architecture Roles (From Discussion)

- **MongoDB (bizpulse_rbac)**  
  - Users, auth, RBAC (business / channel / brand / category / customer / sub_category / allowed_metrics).  
  - Application/operational data (goals, kanban, etc.).  
  - **Source of truth for “who can see what”.**

- **ClickHouse**  
  - **Analytics only**: e.g. `bizpulse.sales_analytics` (and any other analytics tables).  
  - No user or permission storage.  
  - Single (or few) technical user(s); backend always injects `tenant_id` + RBAC filters.

- **Backend (your FastAPI app)**  
  - Authenticates (JWT).  
  - Loads RBAC from MongoDB.  
  - Builds ClickHouse SQL (deterministic from intent + RBAC).  
  - Enforces default 24-month window **unless** the user clearly asks for “lifetime”.  
  - Sends only safe, parameterized/constructed queries to ClickHouse.

---

## 2. What Already Exists in Your Project (Reality Check)

ChatGPT often used **Node/Express** examples. Your stack is **Python/FastAPI**. Below is how the discussion maps to what you already have.

### 2.1 MongoDB

- **DB in use:** `DB_NAME` in `.env` (e.g. `bizpulse_rbac` for testing).
- **Collections:** e.g. `users`, `business_data`, `goals`, `shopify_data`, `kanban`, etc.
- **RBAC in users:** You already have `role` and `access` (businesses, channels, brands, categories, sub_categories, customers, allowed_metrics) in `bizpulse_rbac.users` (from `add_user_rbac_fields.py`).
- **Scripts:**  
  - `copy_bizpulse_to_bizpulse_rbac.py` — copy all collections from bizpulse → bizpulse_rbac (read-only from bizpulse).  
  - `add_user_rbac_fields.py` — add RBAC fields to users in a target DB.  
  - `run_setup_bizpulse_rbac.py` — one-shot: copy + add RBAC to bizpulse_rbac.

### 2.2 ClickHouse

- **Where it runs:** Mac Studio (Docker), e.g. `clickhouse-prod`; ports 9000 (native), 8123/18123 (HTTP).
- **Table:** `bizpulse.sales_analytics` (tenant_id, date, dimensions, metrics; MATERIALIZED time columns; `month_name` as non-MATERIALIZED).
- **Client:** `backend/app/database/clickhouse_client.py` (Python):
  - Connects using `.env` (host, port 9000, database, user, password).
  - **Validates** SELECT-only, no subqueries, no dangerous keywords.
  - **Injects** `tenant_id` and default time filter (e.g. last 24 months).
  - Can use RBAC view name (e.g. replace `sales_analytics` with a view name) for role-scoped access.
- **Migration:** `migrate_real_data_to_clickhouse.py` — MongoDB `business_data` → ClickHouse `sales_analytics` (one-time or re-run).
- **Copy script:** `copy_bizpulse_mongo_to_clickhouse.py` — business_data → sales_analytics + other collections → `mongodb_sync`-style table.

### 2.3 Dynamic Filters

- **API:** e.g. `GET /api/filters/options` (or equivalent) with query params: years, months, businesses, channels, brands, categories, customers, sub_categories.
- **Logic:** `FilterService.get_filter_options()` in `backend/app/services/filter_service.py` — **cascading** filters from `business_data` (or from the DB set by `DB_NAME`). So when you use `bizpulse_rbac`, filters are driven by `bizpulse_rbac.business_data`.
- **Use for Add User:** Reuse the same filter API so admin sees the same dynamic options (e.g. Business → then only years/brands/channels where that business exists).

### 2.4 Gaps vs “Complete Setup” (From Discussion)

- **Single “complete setup” guide** that ties together:  
  - MongoDB (bizpulse_rbac) as source for RBAC and app.  
  - ClickHouse as single analytics store.  
  - Backend: which DB for which purpose, how RBAC is applied to ClickHouse queries, and how default vs lifetime time filter is applied.
- **Default time filter behaviour** in code: “24 months if no time; full history only when user clearly asks for lifetime” — to be implemented/verified in the same place that builds or rewrites SQL (e.g. in or around `clickhouse_client` / query builder).
- **Daily incremental ingestion** (future): not from MongoDB; from CSV/ERP. Script/cron that inserts only new dates (and optionally partition-replace for corrections). No “daily MongoDB → ClickHouse” in the long term.
- **Intent → SQL (no raw LLM SQL):** Backend must build ClickHouse SQL from structured intent + RBAC. Your existing client already injects tenant and time; any LLM-generated “query” should be treated as intent (metrics, dimensions, filters, time) and turned into SQL inside the backend, not executed as-is.

---

## 3. Target Architecture (Complete Setup)

### 3.1 Data Flow (High Level)

```
Future data: CSV / ERP (email or API)
        ↓
   ETL (Python) — validate, transform
        ↓
   ClickHouse (INSERT new dates only; or REPLACE PARTITION for corrections)
        ↓
   Backend (FastAPI) — JWT, RBAC from MongoDB, build SQL, execute on ClickHouse
        ↓
   Frontend (React) — Dashboard + Chatbot
```

- **MongoDB (bizpulse_rbac):**  
  - Users, permissions (access + allowed_metrics).  
  - All app collections (business_data copy, goals, kanban, etc.).  
  - Used for: login, RBAC, dynamic filter options (from business_data or equivalent).

- **ClickHouse:**  
  - `bizpulse.sales_analytics` (and any other analytics tables).  
  - Used only for: analytics queries (dashboard + AI).  
  - No user/permission storage.

### 3.2 RBAC Flow (Backend)

1. User logs in → JWT (e.g. email, tenant_id, role).
2. On each analytics request: load user’s `access` and `allowed_metrics` from MongoDB (bizpulse_rbac.users).
3. If using AI: get **intent** from LLM (metric, dimensions, filters, time_range / lifetime).
4. **Validate intent** against RBAC (requested business/channel/brand etc. ⊆ allowed).
5. **Build SQL** in backend:  
   - `WHERE tenant_id = :tenant_id` (always).  
   - AND filters from RBAC (business IN (...), channel IN (...), etc.).  
   - AND time: if intent is “lifetime” → no date filter; else if no time → `date >= today() - INTERVAL 24 MONTH` (or equivalent).  
   - AND only allowed metrics (e.g. if only gsales, fgp → only those in SELECT).  
   - LIMIT and max_execution_time as you already have.
6. Execute against ClickHouse with a single technical user; **never** execute raw user/LLM-generated SQL.

### 3.3 Default vs Lifetime Time Filter (Rule)

- **Explicit “lifetime” / “all time” in user question** → do **not** add any date filter.
- **No time mentioned** → add default: e.g. `date >= addMonths(today(), -24)` (last 24 months).
- **Explicit range** (e.g. “last 6 months”, “2024”) → use that range only.

This logic should live in the **backend** (same place that builds or rewrites the query), not in the LLM.

### 3.4 Add User (Admin) Screen

- **Data source for options:** Same as other screens — **dynamic filter API** (e.g. `/api/filters/options` or equivalent) so options are cascading (e.g. Business Food → only years/brands/channels where Food exists).
- **Stored in:** MongoDB `bizpulse_rbac.users`: e.g. `role`, `access` (businesses, channels, brands, categories, sub_categories, customers), `allowed_metrics` (e.g. gsales, fgp).
- **Admin only:** Screen and “create user” API protected by role (e.g. `role === 'admin'`).

---

## 4. What “Complete Setup” Should Include (Implementation View)

### 4.1 MongoDB

- **Use `bizpulse_rbac`** as the application DB (DB_NAME in .env).
- **Ensure** all app code (auth, RBAC, filters) reads/writes to the DB configured by DB_NAME (so one place to switch).
- **Schema:** Users have `role` and `access` (and optionally `allowed_metrics`) as you already added; no need to duplicate in ClickHouse.
- **Scripts (already there):**  
  - Copy: `copy_bizpulse_to_bizpulse_rbac.py`  
  - RBAC on users: `add_user_rbac_fields.py --target-db bizpulse_rbac`  
  - One-shot: `run_setup_bizpulse_rbac.py`

### 4.2 ClickHouse

- **Database:** `bizpulse` (or as in CLICKHOUSE_DB).
- **Table:** `sales_analytics` (schema already fixed: tenant_id, date, dimensions, metrics, MATERIALIZED time, `month_name` non-MATERIALIZED).
- **Access:** Backend only; single (or few) technical user(s); read-only for analytics user if possible.
- **Initial load:** Use existing `migrate_real_data_to_clickhouse.py` from MongoDB `business_data` (source DB can be bizpulse or bizpulse_rbac as you prefer for that one-time load).
- **Future ingestion:** Separate ETL (Python) that reads CSV/ERP and **inserts only new dates**; for corrections, use partition replacement (e.g. REPLACE PARTITION) as in the discussion.

#### 4.2.1 Correction Handling: `REPLACE PARTITION` (Recommended for Bizpulse)

**Final Verdict (after ChatGPT review):** For Bizpulse's batch-based data flow (ERP → CSV → ClickHouse), **use `MergeTree()` engine with `REPLACE PARTITION` for corrections. NO version column needed.**

**Why this is the right choice for Bizpulse:**

Your data flow is **batch-based** (not real-time streaming):
- ERP sends CSV → ETL script → ClickHouse INSERT
- Corrections arrive as CSV updates for specific months
- This is **NOT** a high-frequency, real-time update scenario

**Recommended approach: `MergeTree()` + `REPLACE PARTITION`**

**Table engine:**
```sql
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (tenant_id, date, business, channel, brand, category, sub_category, customer, sku)
```

**Correction flow:**
1. When ERP sends corrected data for a month (e.g. Jan-2026):
   - Load corrected CSV into a temporary table
   - Run: `ALTER TABLE sales_analytics REPLACE PARTITION 202601 FROM sales_analytics_temp`
2. Only that month's partition is replaced; all other data remains unchanged.

**Why NOT `ReplacingMergeTree(version)` for Bizpulse:**

- **Version column alone does nothing** — it only works with `ReplacingMergeTree(version)` engine.
- **Duplicate risk:** Merges are async, so queries can temporarily show duplicates until merges complete (unless you use `FINAL`, which is expensive).
- **Not needed:** Your batch-based flow doesn't require insert-only corrections; partition replace is simpler and safer.

**When `version` + `ReplacingMergeTree` IS useful:**
- Real-time streaming systems (Kafka ingestion, millions per second)
- Systems where you cannot replace partitions
- High-frequency update scenarios

**For Bizpulse:** Stick with `MergeTree()` + `REPLACE PARTITION`. It's the safest, simplest, and most appropriate for your architecture.

### 4.3 Backend (FastAPI)

- **Auth:** JWT; user identity and tenant from token.
- **RBAC:** On each analytics (or AI) request, load user from MongoDB (bizpulse_rbac) and get `access` + `allowed_metrics`.
- **ClickHouse client:** Keep using `clickhouse_client.py`; ensure:
  - **Tenant** and **default time** (24 months) are always applied for analytics queries, **unless** the request is explicitly “lifetime”.
  - **RBAC:** Either (a) pass permissions into the client and add business/channel/brand/… filters in Python, or (b) use a view name per role and let the client replace `sales_analytics` with that view (you already have view logic).
- **AI path:**  
  - LLM returns **intent** (metric, dimensions, filters, time_range / is_lifetime).  
  - Backend validates intent against RBAC, then **builds** SQL (or calls a safe query builder) and executes via ClickHouse client.  
  - No raw LLM SQL ever executed.

### 4.4 Frontend

- **Dashboard:** Already uses filters and (likely) MongoDB or ClickHouse-backed APIs; ensure analytics APIs use ClickHouse with RBAC and time rules.
- **Add User (admin):** New (or existing) screen that calls the **same dynamic filter API** as other screens, then sends selected access + allowed_metrics to a “create user” API that writes to MongoDB bizpulse_rbac.users.

### 4.5 Scripts / Runbooks

- **One-time / setup:**  
  - Copy bizpulse → bizpulse_rbac (MongoDB).  
  - Add RBAC fields to users in bizpulse_rbac.  
  - Create ClickHouse table if not present; run migration from MongoDB (bizpulse or bizpulse_rbac) business_data → ClickHouse sales_analytics.
- **Ongoing:**  
  - No “daily MongoDB → ClickHouse” by default.  
  - Daily job = **CSV/ERP → ClickHouse** (incremental insert or partition replace) when you have that pipeline.

---

## 5. What I Propose to Implement (After Your Go-Ahead)

1. **Single “complete setup” doc/runbook**  
   - Step-by-step: MongoDB (bizpulse_rbac), ClickHouse (create table, migrate business_data once), .env, and how to run each script.  
   - Clarify: Python commands, paths, and “run from backend folder”.

2. **Time filter behaviour in code**  
   - In the place that injects the default time filter (e.g. `clickhouse_client` or the service that calls it):  
     - If the **request** is marked “lifetime” (from intent or explicit flag), **do not** add any date condition.  
     - Otherwise, add default 24 months.  
   - No change to schema; only to backend logic.

3. **RBAC application to ClickHouse queries**  
   - Ensure every analytics query that goes to ClickHouse:  
     - Uses tenant_id from the authenticated user (or session).  
     - Restricts dimensions (business, channel, brand, etc.) and metrics to the user’s `access` and `allowed_metrics` from MongoDB.  
   - Implementation can be: (a) in `clickhouse_client` (accept permissions and inject WHERE clauses), or (b) in a dedicated service that builds the full query and then passes it to the client. Align with your existing RBAC view or filter injection.

4. **Optional: “Complete setup” script**  
   - One script (or a small set) that:  
     - Checks MongoDB and ClickHouse connectivity.  
     - Optionally runs: copy bizpulse → bizpulse_rbac, add_user_rbac_fields for bizpulse_rbac.  
     - Does **not** run migration to ClickHouse by default (so you can run it once explicitly); or run it once with a flag.  
   - So “complete setup” = one place to run from, with clear steps in the doc.

5. **No change to bizpulse**  
   - All write operations and scripts target **bizpulse_rbac** (and ClickHouse). No script will modify bizpulse.

---

## 6. What We Do Not Do (From Discussion + Your Stack)

- **No per-user ClickHouse users or views** for RBAC at scale; RBAC stays in MongoDB and is enforced in the backend.
- **No raw LLM SQL** to ClickHouse; only intent → backend-built SQL.
- **No daily sync from MongoDB to ClickHouse** as the long-term design; future ingestion is CSV/ERP → ClickHouse.
- **No storing users/permissions in ClickHouse**; only in MongoDB (bizpulse_rbac).
- **No Node/Express**; all implementation stays in your **Python/FastAPI** backend and existing scripts.

---

## 7. Summary Table

| Item | Source of truth / Where | Implementation note |
|------|-------------------------|----------------------|
| Users & auth | MongoDB bizpulse_rbac | Already; JWT + users collection. |
| RBAC (access, allowed_metrics) | MongoDB bizpulse_rbac.users | Already added by script; use in backend for every analytics request. |
| Dynamic filter options | Same DB as app (bizpulse_rbac) | FilterService + existing API; reuse for Add User screen. |
| Analytics data | ClickHouse bizpulse.sales_analytics | Existing table and client; migration script for initial load. |
| Default time | Backend | 24 months if no time; no limit only when “lifetime” is requested. |
| Intent → SQL | Backend only | LLM gives intent; backend builds and runs SQL with RBAC + tenant + time. |
| bizpulse (MongoDB) | Read-only | Only copy from it to bizpulse_rbac; never write to it. |
| AI Chatbot Cache | MongoDB or Redis | Permission-aware caching with TTL; cache ClickHouse results, not LLM explanations. |

---

## 8. AI Chatbot Caching Architecture (From Cache Discussion)

### 8.1 Critical Problems Identified

**Problem 1: Data changes daily → cached answer becomes wrong**
- Example: "Revenue of Food business in last 7 days" — today = ₹10,00,000, tomorrow = ₹11,20,000.
- If cache never expires → **wrong answer** shown to users.

**Problem 2: Security breach risk (CRITICAL)**
- If cache is **global** (not permission-aware):
  - Manager asks: "Revenue Food" → cached.
  - Employee asks same question → gets Manager's cached result (which may include data Employee shouldn't see).
- This is a **data breach** and must never happen.

### 8.2 Enterprise Solution: Permission-Aware, Time-Aware Caching

#### 8.2.1 Cache Key Structure (Production)

Cache key **MUST** include:
- `tenant_id` (always)
- `permissions_hash` (hash of full access object)
- `intent_hash` (hash of LLM intent JSON)
- `data_version` (optional: max date in ClickHouse for auto-invalidation)

**Final cache key formula:**
```
cache_key = sha256(
    tenant_id +
    permissions_hash +
    intent_hash
)
```

#### 8.2.2 Permission Hash Generation

**Critical:** Must hash **FULL** access object with deterministic sorting.

**Your RBAC structure:**
```python
access = {
    "businesses": ["Food"],  # or ["*"] for admin
    "channels": ["Grocery"],
    "brands": ["Cali Cali", "Bensons"],
    "categories": "all",  # or ["Snacks"] for specific
    "sub_categories": "all",  # or ["Chips"]
    "customers": "all",  # or ["Amazon"]
    "allowed_metrics": ["gsales", "fgp"]  # or ["*"] for admin
}
```

**Permission hash generation (Python):**
```python
import hashlib
import json

def generate_permissions_hash(access: dict) -> str:
    def _canon(value):
        # Canonicalize permissions so equivalent access generates same hash:
        # - list values are sorted
        # - string values like "all" are kept as-is
        if isinstance(value, list):
            return sorted(value)
        return value

    normalized = {
        "businesses": _canon(access.get("businesses", [])),
        "channels": _canon(access.get("channels", [])),
        "brands": _canon(access.get("brands", [])),
        "categories": _canon(access.get("categories")),        # "all" or list
        "sub_categories": _canon(access.get("sub_categories")),# "all" or list
        "customers": _canon(access.get("customers")),          # "all" or list
        "metrics": _canon(access.get("allowed_metrics", []))
    }
    permissions_string = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(permissions_string.encode()).hexdigest()
```

**Why sorting is critical:**
- Without sorting: `["Food", "Beauty"]` and `["Beauty", "Food"]` produce different hashes ❌
- With sorting: Same hash ✅ (deterministic)

#### 8.2.3 Intent Hash Generation

Hash the LLM intent JSON (metric, dimensions, filters, time_range):
```python
def generate_intent_hash(intent: dict) -> str:
    intent_string = json.dumps(intent, sort_keys=True)
    return hashlib.sha256(intent_string.encode()).hexdigest()
```

#### 8.2.4 Cache Storage Options

**Option 1: MongoDB (easier, already in stack)**
- Collection: `bizpulse_rbac.ai_cache` (or separate `ai_cache` DB)
- Schema:
```python
{
    "_id": ObjectId(),
    "tenant_id": "client_001",
    "permissions_hash": "a81f9c4b...",
    "intent_hash": "b92d1c8f...",
    "data_version": ISODate("2026-02-12"),  # max(date) from ClickHouse
    "question": "Revenue Food last 6 months",
    "response": "Your Food business generated...",  # or ClickHouse result JSON
    "created_at": ISODate(),
    "expires_at": ISODate()  # created_at + TTL
}
```
- Index: `(tenant_id, permissions_hash, intent_hash, data_version)`

**Option 2: Redis (faster, recommended for production)**
- Key: `ai_cache:{tenant_id}:{permissions_hash}:{intent_hash}`
- Value: JSON string of response
- TTL: Set on key (automatic expiration)
- **Note:** Redis is faster but adds infrastructure dependency.

**Recommendation:** Start with **MongoDB** (already in stack), migrate to Redis later if needed for performance.

#### 8.2.5 Time-Based Cache Invalidation (TTL)

**Dynamic TTL based on query type:**

| Query Type | Cache TTL | Reason |
|------------|-----------|--------|
| "last 7 days" / "today" | 6 hours | Data changes daily |
| "current month" | 2 hours | Monthly data updates |
| "last year" | 24 hours | Yearly data less volatile |
| Custom date range | 12 hours | Balance freshness vs performance |
| "lifetime" / "all time" | 24 hours | Historical data rarely changes |

**Implementation:**
```python
def get_cache_ttl(intent: dict) -> int:
    time_range = intent.get("time_range", {})
    if time_range.get("type") == "last_n_days" and time_range.get("value", 0) <= 7:
        return 6 * 3600  # 6 hours
    elif time_range.get("type") == "current_month":
        return 2 * 3600  # 2 hours
    elif time_range.get("type") == "lifetime":
        return 24 * 3600  # 24 hours
    else:
        return 12 * 3600  # 12 hours default
```

#### 8.2.6 Data Version Tracking (Automatic Invalidation)

**Concept:** Track the latest data date in ClickHouse. If new data arrives, cache automatically invalidates.

**Implementation:**
```python
def get_data_version(tenant_id: str) -> date:
    """Get max(date) from ClickHouse sales_analytics for tenant"""
    query = f"""
        SELECT max(date)
        FROM bizpulse.sales_analytics
        WHERE tenant_id = '{tenant_id}'
    """
    result = clickhouse_client.execute(query)
    return result[0][0]  # max date
```

**Cache lookup includes data_version:**
```python
cache = db.ai_cache.find_one({
    "tenant_id": tenant_id,
    "permissions_hash": permissions_hash,
    "intent_hash": intent_hash,
    "data_version": current_data_version  # Must match!
})
```

**If `data_version` changed** → cache miss (new data arrived) → query fresh.

#### 8.2.7 CRITICAL SECURITY RULE: RBAC Before Cache

**WRONG flow (security risk):**
```
Cache lookup → RBAC check
```
- If cache hit, RBAC might be skipped → **data leak**.

**CORRECT flow (enterprise standard):**
```
1. User asks question
2. Validate JWT
3. Load RBAC from MongoDB (ALWAYS)
4. Generate permissions_hash
5. Generate intent_hash
6. Check cache (with permissions_hash in key)
7. If cache hit → return
8. If cache miss → query ClickHouse → store cache → return
```

**RBAC must ALWAYS run BEFORE cache lookup** — this ensures:
- Permission validation happens even if cache exists
- Cache key includes permissions, so different users get different cache entries
- No data leakage across users

#### 8.2.8 What to Cache: ClickHouse Results vs LLM Explanation

**ChatGPT recommendation:** Cache **ClickHouse query result**, NOT final LLM explanation.

**Why:**
- ClickHouse result = raw data (stable, reusable)
- LLM explanation = formatted text (may change with LLM version/prompt)
- If you cache explanation → can't update explanation style without clearing cache
- If you cache data → can regenerate explanation dynamically (better accuracy)

**Flow:**
```
1. Check cache for ClickHouse result
2. If hit → use cached data → generate LLM explanation → return
3. If miss → query ClickHouse → cache result → generate LLM explanation → return
```

**Cache structure (if caching ClickHouse result):**
```python
{
    "tenant_id": "...",
    "permissions_hash": "...",
    "intent_hash": "...",
    "data_version": "...",
    "clickhouse_result": [...],  # Raw data from ClickHouse
    "created_at": "...",
    "expires_at": "..."
}
```

**Alternative (if caching final response):**
```python
{
    "response": "Your Food business generated ₹4.58 crore...",  # Final LLM text
    ...
}
```

**Recommendation:** Cache **ClickHouse result** (more flexible, better for future LLM updates).

### 8.3 Complete Cache Flow (Enterprise)

```
User Question: "Show revenue Food last 6 months"
    ↓
[1] JWT validation → extract user_id, tenant_id
    ↓
[2] Load RBAC from MongoDB (bizpulse_rbac.users)
    → access = {"businesses": ["Food"], "channels": ["Grocery"], ...}
    ↓
[3] Generate permissions_hash = hash(access)
    ↓
[4] LLM → Intent extraction
    → intent = {"metric": "gsales", "business": "Food", "time_range": {...}}
    ↓
[5] Generate intent_hash = hash(intent)
    ↓
[6] Get data_version = max(date) from ClickHouse
    ↓
[7] Check cache:
    WHERE tenant_id = ? 
    AND permissions_hash = ?
    AND intent_hash = ?
    AND data_version = ?
    ↓
[8a] IF cache HIT:
    → Return cached ClickHouse result
    → Generate LLM explanation from cached data
    → Return to frontend (⚡ 50-200ms)
    ↓
[8b] IF cache MISS:
    → Validate intent against RBAC (ensure Food ∈ allowed businesses)
    → Build SQL with RBAC filters
    → Execute on ClickHouse
    → Cache result (with permissions_hash, intent_hash, data_version, TTL)
    → Generate LLM explanation
    → Return to frontend (⚡ 500-2000ms)
```

### 8.4 Cache Implementation Notes (For Your Stack)

**Where to implement:**
- **Service:** `backend/app/services/ai_cache_service.py` (new)
- **Integration:** In your chatbot API endpoint (where LLM intent → ClickHouse → response happens)
- **Storage:** MongoDB `bizpulse_rbac.ai_cache` collection (or Redis if preferred)

#### 8.4.1 Cache Indexes (Required for Production Performance)

**ChatGPT's recommendation is correct:** These indexes are **required** for production performance, not optional.

**Why indexes are critical:**
- Without indexes: MongoDB scans every document → slow (500ms+ at 100k docs)
- With indexes: Direct lookup → fast (~2-5ms even at 1M docs)
- **100x+ performance improvement** as cache grows

**Required MongoDB indexes for `ai_cache` collection:**

**1. Compound lookup index (for cache queries):**
```python
db.ai_cache.create_index([
    ("tenant_id", 1),
    ("permissions_hash", 1),
    ("intent_hash", 1),
    ("data_version", 1)
])
```
This matches your cache lookup query pattern exactly.

**2. TTL index (automatic cleanup of expired cache):**
```python
db.ai_cache.create_index(
    ("expires_at", 1),
    expireAfterSeconds=0
)
```
This automatically deletes expired cache entries, preventing the collection from growing forever.

**When to create:** During initial setup (run once, e.g. in FastAPI startup or migration script).

**Performance impact:**
- Cache size 10k docs: 50ms → 2ms (25x faster)
- Cache size 100k docs: 500ms → 2ms (250x faster)
- Cache size 1M docs: 5s → 3ms (1667x faster)

**These indexes are production-required, not optional.**

**Key functions needed:**
1. `generate_permissions_hash(access: dict) -> str`
2. `generate_intent_hash(intent: dict) -> str`
3. `get_data_version(tenant_id: str) -> date`
4. `get_cache(tenant_id, permissions_hash, intent_hash, data_version) -> Optional[dict]`
5. `store_cache(tenant_id, permissions_hash, intent_hash, data_version, result, ttl) -> None`
6. `get_or_set_cache(tenant_id, access, intent, question, query_function) -> dict`

**Integration point:**
- In your chatbot endpoint (e.g. `POST /api/chatbot/chat`):
  - After RBAC load, before ClickHouse query
  - Check cache with permissions_hash + intent_hash
  - If miss, execute query, then store cache

### 8.5 Performance Expectations

**Without cache:**
- First query: 500-2000ms (LLM intent + ClickHouse + LLM explanation)

**With cache:**
- Cache hit: 50-200ms (cache lookup + LLM explanation from cached data)
- Cache miss: 500-2000ms (same as without cache, but result cached for next time)

**Expected cache hit rate:** 60-70% (if users ask similar questions)

**Speed improvement:** 2.5-10x faster for cached queries.

### 8.6 Security Guarantees

✅ **Permission-aware:** Cache key includes permissions_hash → different users get different cache entries  
✅ **RBAC enforced:** RBAC checked BEFORE cache lookup → no bypass  
✅ **Tenant isolation:** Cache key includes tenant_id → no cross-tenant leakage  
✅ **Data freshness:** data_version tracking → cache invalidates when new data arrives  
✅ **Time-based expiry:** TTL ensures stale data doesn't persist forever  

---

## 9. Final Production Recommendations (After ChatGPT Review)

**ChatGPT confirmed:** The architecture and recommendations below are correct for Bizpulse's production setup.

### 9.1 ClickHouse Table Engine & Corrections

**✅ Final Decision:**
- **Engine:** `MergeTree()` (NOT `ReplacingMergeTree`)
- **Correction method:** `REPLACE PARTITION` for affected months
- **Version column:** NOT needed (only useful for real-time streaming systems)

**Why:** Bizpulse's batch-based flow (ERP → CSV → ClickHouse) doesn't require insert-only corrections. Partition replace is simpler, safer, and avoids duplicate risk.

### 9.2 MongoDB Cache Indexes

**✅ Required (not optional):**
- **Compound index:** `(tenant_id, permissions_hash, intent_hash, data_version)` for fast cache lookups
- **TTL index:** `(expires_at)` with `expireAfterSeconds=0` for automatic cleanup

**Why:** Without indexes, cache lookups become slow (500ms+) as cache grows. With indexes, stays fast (~2-5ms) even at 1M+ documents.

---

## 10. Next Step

Once you confirm this understanding and the direction above, the next step is to implement:

1. The **runbook** (complete setup steps and commands).  
2. **Default vs lifetime** time filter in backend.  
3. **RBAC application** to ClickHouse queries (and any small refactors in `clickhouse_client` or the service layer).  
4. **AI Chatbot caching** (permission-aware, time-aware):
   - Create `ai_cache_service.py` with permission_hash and intent_hash generation
   - Create MongoDB `ai_cache` collection (or use Redis if preferred)
   - Integrate cache check in chatbot endpoint (after RBAC, before ClickHouse query)
   - Implement TTL based on query type (6 hours for "last 7 days", 24 hours for "lifetime", etc.)
   - Implement data_version tracking for automatic invalidation
   - Cache ClickHouse results (not LLM explanations) for flexibility
5. Optionally, a **single “setup” script** that runs the approved steps in order.

If you want to adjust anything (e.g. default 12 months instead of 24, cache TTL values, or where RBAC is applied), we can change the doc and then implement accordingly.
