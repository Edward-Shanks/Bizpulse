## AI Chatbot & RBAC Architecture – Deep Dive

This document explains, end‑to‑end, how the **AI chatbot** works in the Bizpulse project – especially the **RBAC (role‑based access control)** logic, the **intent → SQL** pipeline, and how answers are generated.

The goal is that you can:

- Re‑implement this pattern in another project.
- Debug issues confidently (RBAC, time ranges, “top N” questions, etc.).
- Teach it to someone else without missing critical details.

---

### 1. High‑level system overview

- **Entry point (API):**
  - `POST /api/ai/chatbot/chat` → `AIService.process_question` (`backend/app/services/ai/ai_service.py`).
- **Data source:**
  - ClickHouse table `bizpulse.sales_analytics` (plus RBAC views such as `sales_*_view`).
- **Core AI components (`backend/app/services/ai/`):**
  - `ai_clarity_service.py` – detects off‑topic questions, suggests clarifications.
  - `ai_intent_service.py` – converts natural‑language question → structured **intent JSON**.
  - `ai_query_builder.py` – converts intent + RBAC access → **ClickHouse SQL**.
  - `ai_service.py` – orchestrates the full flow (RBAC load, cache, query, LLM, response).
  - `ai_response_service.py` – turns raw rows into business‑language answers (LLM + fallback).
  - `ai_cache_service.py` – caches results and LLM explanations.
- **RBAC source of truth:**
  - MongoDB `users` collection: each user document has an `access` field:
    - `businesses`, `channels`, `brands`, `categories`, `sub_categories`, `customers`, `allowed_metrics`, etc.

At a very high level, the flow is:

1. API receives a question + user email.
2. Load user + `access` from MongoDB.
3. Run **clarity service** to see if the question is in scope.
4. Extract **intent** (metric, dimensions, filters, time_range, limit).
5. Build SQL (applying **RBAC** as both **view‑level** and **WHERE filters**).
6. Execute on ClickHouse and get rows.
7. Use **LLM** (or deterministic fallback) to generate a business explanation.
8. Return answer + `pivot_table` data to the frontend.

RBAC is enforced **twice**:

- **At the ClickHouse view level** (via `clickhouse_client` replacing `sales_analytics` with a view).
- **Inside the query** via `_build_rbac_filters` (per‑dimension `IN (...)` and `1 = 0` when no access).

---

### 2. Request flow in detail (`AIService.process_question`)

File: `backend/app/services/ai/ai_service.py`.

When `process_question(question, user_email, ...)` is called:

1. **Load and validate RBAC:**
   - `_load_user_rbac(user_email)` fetches the user from MongoDB.
   - `access = user.get("access", {})` must be present; otherwise a `ValueError` is raised.
   - Example user (Barry):
     ```json
     "access": {
       "businesses": [],
       "channels": [],
       "brands": [],
       "categories": "all",
       "sub_categories": "all",
       "customers": "all",
       "allowed_metrics": []
     }
     ```

2. **Clarity / off‑topic routing (`AIClarityService`):**
   - For greetings or non‑business topics (e.g. world events, stock market), the clarity service decides whether to:
     - Answer directly (e.g. greeting), or
     - Return a **clarification message** with suggested business‑relevant questions.
   - If clarity suggests clarification, `process_question` returns that immediately.

3. **Intent extraction (`AIIntentService.extract_intent`):**
   - Uses LLM to produce an **intent JSON** (see Section 3).
   - If LLM fails, a deterministic `_get_default_intent` is used as fallback.

4. **Query + cache:**
   - A `query_function()` is defined:
     - Calls `AIQueryBuilder.build_query(intent, access, tenant_id)` to get `(sql, is_lifetime)`.
     - Executes the SQL via `ClickHouseClient.execute_dict`.
   - `AICacheService.get_or_set_cache(...)` wraps `query_function` so repeated queries reuse data.

5. **Zero‑row safeguards:**
   - After `result_data` is obtained:
     - If **zero rows** and **query contains `1 = 0`** → RBAC denial (Section 7):
       - Response: “You don’t have permission to view [business‑level / brand‑level / etc.] data for this question…”
     - Else if **zero rows** and **question is off‑topic** → off‑topic clarification message.

6. **LLM explanation and caching:**
   - A `result_hash` and `question_hash` are computed.
   - If an explanation for `(tenant, permissions, intent, result, question)` is cached, re‑use it.
   - Otherwise call `AIResponseService.generate_response(question, data, intent)` (LLM) and cache result.

7. **Pivot table:**
   - `_data_to_pivot_table(rows)` maps DB column names to frontend keys:
     - `year` → `Year`
     - `revenue` → `Revenue`
     - `gross_profit` → `Gross_Profit`
     - `total_cases` → `Cases`
     - `margin_pct` → `Margin_%`
     - `business` → `Business`, etc.
   - Returned so the frontend can render charts/tables.

---

### 3. Intent model & extraction (`AIIntentService`)

File: `backend/app/services/ai/ai_intent_service.py`.

#### 3.1 Intent JSON schema

Example structure:

```json
{
  "metric": "gsales",
  "dimensions": ["business"],
  "filters": {
    "business": [],
    "channel": [],
    "brand": [],
    "category": [],
    "sub_category": [],
    "customer": [],
    "sku": [],
    "year": [2024],
    "quarter": [],
    "month_name": []
  },
  "time_range": {
    "type": "lifetime",        // or last_n_months, last_n_days, current_month, last_year, custom
    "value": null
  },
  "aggregation": "sum",
  "limit": 5
}
```

**Key fields:**

- **metric** – what to aggregate:
  - `"gsales"` (revenue), `"fgp"` (gross profit), `"cases"`, `"price_downs"`, `"perm_disc"`, `"transfer_cost"`, `"group_cost"`, `"lta"`.
- **dimensions** – group‑by fields (e.g. `["business"]`, `["brand"]`, `["channel"]`, `["year"]`, `["month_name"]`).
- **filters** – equality filters for each dimension (`IN (...)` semantics).
- **time_range** – shapes the date filter or instructs that only `year/quarter/month_name` filters apply.
- **aggregation** – SQL aggregation function: `"sum"` / `"avg"` / `"count"` / `"max"` / `"min"`.
- **limit** – how many rows to return; `top N` questions set a small limit.

#### 3.2 LLM prompt rules (high‑level)

The **intent extraction prompt** gives the LLM explicit rules, including:

- Map **words → metric** (revenue, profit, cases, etc.).
- Map **entities → dimensions/filters** (business, brand, category, channel, customer, sku).
- Time rules:
  - “last 6 months” → `time_range.type = "last_n_months", value = 6`.
  - “last 7 days” → `time_range.type = "last_n_days", value = 7`.
  - “current month” → `time_range.type = "current_month"`.
  - “lifetime / all time / all history” → `time_range.type = "lifetime"`.
- “top N” → set `limit = N`.
- Multi‑year / quarter comparisons (e.g. “Q1 2022, 2023, 2024”):
  - `filters.year = [2022, 2023, 2024]`,
  - `filters.quarter = [1]`,
  - include `"year"` in `dimensions`,
  - `time_range.type = "lifetime"` so only `year` + `quarter` filters apply.
- Special rules:
  - “Compare X with other brands” → `dimensions = ["brand"]`, `filters.brand = []`, `limit ≈ 20`.
  - “Compare brand A and B” → `dimensions = ["brand"]`, keep filters empty so all brands come back.
  - “Compare X performance in Convenience vs Grocery” → `dimensions = ["channel"]`, `filters.brand = ["X"]`, `filters.channel = ["Convenience", "Grocery"]`.
  - “Before and after January 2024” → `time_range = last_n_months (24)`, add `"month_name"` to `dimensions`.
  - Specific month / quarter (e.g. “January 2024”, “first month”, “Q1”, “quarter 1”) → `filters.month_name` / `filters.quarter` + `time_range.type = "lifetime"`.

#### 3.3 Normalization (`_normalize_intent`)

After the LLM returns raw JSON, `_normalize_intent`:

1. **Ensures required keys:**
   - Adds missing keys for all filters (`business`, `brand`, `category`, etc.) with empty lists.
   - Default `time_range` to `{"type": "custom", "value": None}` if missing.

2. **Normalizes metric:**
   - `raw_metric = intent.get("metric") or "gsales"`.
   - Only allow known metrics; otherwise default to `"gsales"`:
     ```python
     allowed_metrics = {"gsales", "fgp", "cases", "price_downs", "perm_disc", "transfer_cost", "group_cost", "lta"}
     metric = raw_metric if raw_metric in allowed_metrics else "gsales"
     ```
   - This avoids invalid SQL like `COUNT(gsales) AS ` (blank alias).

3. **Time normalization:**
   - If multiple years in `filters.year` → add `"year"` to `dimensions`.
   - If a specific year is present and `time_range.type == "custom"` → change to `time_range = {"type": "lifetime"}` so the query uses only `year` filters.
   - “Before and after [month] [year]” → ensure `last_n_months` and `"month_name"` in `dimensions`.
   - Quarter/month detection via helper parsers:
     - `_parse_quarter_from_question(question)` handles `Q1`, `quarter 1`, `quarter one`, etc.
     - `_parse_month_from_question(question)` handles `January`, `Jan`, `first month`, `month 1`, etc. and normalizes to abbreviated `month_name` values (Jan, Feb, …).

4. **`top N` dimension detection (default intent path):**
   - If `dimensions` is empty and the question says “top N”:
     - “top 5 business(es)” → `dimensions = ["business"]`.
     - “top 6 brands” → `["brand"]`.
     - Similar for `categories`, `channels`, `customers`, `sub_categories`, `sku`.

5. **Brand/business/category comparison helpers:**
   - `_parse_multiple_brands_from_question`, `_parse_multiple_entities_from_question` extract lists like “Koka, Killeen, McDonnells” to set filters and adjust limits when comparing multiple named entities.

6. **Month name normalization (`_normalize_month_name_filter`)**
   - Converts full month names and variations to ClickHouse’s abbreviated `month_name` format (Jan, Feb, …).

---

### 4. Building SQL (`AIQueryBuilder.build_query`)

File: `backend/app/services/ai/ai_query_builder.py`.

Given `intent` and `access`, `build_query` outputs `(sql, is_lifetime)`.

#### 4.1 Metric / dimensions / filters

- **Metric:**
  - `metric = intent.get("metric") or "gsales"`; if not in `METRIC_COLUMNS`, default to `"gsales"`.
  - `METRIC_COLUMNS` maps each metric key to a column: `gsales`, `fgp`, `cases`, etc.

- **Dimensions:**
  - `dimensions = intent.get("dimensions", [])`.
  - `DIMENSION_COLUMNS` maps each dimension key to a column:
    - `business`, `channel`, `brand`, `category`, `sub_category`, `customer`, `sku`,
    - `year`, `month`, `quarter`, `year_month`, `month_name`.

- **Filters:**
  - `filters = intent.get("filters", {})` (string keys).
  - Two kinds of filters are built:
    1. **RBAC filters** (`_build_rbac_filters`): business/channel/brand/category/sub_category/customer/sku.
    2. **Direct filters** (`_build_direct_filters`): `year`, `quarter`, `month_name` (not part of RBAC lists).

#### 4.2 SELECT clause

- Starts with all dimension columns, then adds metric aggregations.
- For **revenue** (`metric == "gsales"` and `aggregation == "sum"`):
  - Adds derived columns to match the live dashboard:
    - `SUM(gsales) AS revenue`
    - `SUM(fgp) AS gross_profit`
    - `SUM(cases) AS total_cases`
    - `round((SUM(fgp) / nullIf(SUM(gsales), 0)) * 100, 2) AS margin_pct`
  - Orders by `revenue` by default.
- For other metrics, uses `AGG(metric_col) AS metric` and orders by that alias.

#### 4.3 FROM, WHERE, GROUP BY, ORDER BY, LIMIT

- **FROM:**
  - `FROM bizpulse.sales_analytics` (later rewritten to view name for RBAC in `ClickHouseClient`).

- **WHERE:**
  - Always includes `tenant_id = '{tenant_id}'`.
  - Adds RBAC filters (Section 5).
  - Adds direct filters for `year`, `quarter`, `month_name`.
  - Adds a time filter based on `time_range` unless `is_lifetime` is True.

- **GROUP BY:**
  - All dimension columns.

- **ORDER BY:**
  - `ORDER BY <order_metric_alias> DESC`, where `order_metric_alias` is typically `revenue` or `metric`.

- **LIMIT:**
  - Based on `intent["limit"]`, bounded by 5000 for safety.

---

### 5. RBAC model – access + SQL filters

RBAC is defined in MongoDB user documents and enforced in two places:

1. **At the ClickHouse level** via views and `ClickHouseClient` table name replacement.
2. **Inside the query** via `_build_rbac_filters` on dimensions like `business`, `brand`, etc.

#### 5.1 User access document

Example (Barry):

```json
{
  "email": "Barry@thrivebrands.ai",
  "access": {
    "businesses": [],
    "channels": [],
    "brands": [],
    "categories": "all",
    "sub_categories": "all",
    "customers": "all",
    "allowed_metrics": []
  }
}
```

- Lists or strings:
  - `"all"` or `"*"` → full access for that dimension.
  - `[]` or `null` → **no access**.

#### 5.2 View‑level RBAC (`ClickHouseClient`)

File: `backend/app/database/clickhouse_client.py`.

- For calls that use **RBAC views** (e.g. `execute_with_rbac`, `execute_dict_with_rbac`):
  - Determine a view name based on permissions (`_get_user_view(user_permissions)`):
    - Admin / finance → `sales_analytics` (full access).
    - Single brand → `sales_<brand>_view`.
    - Single channel → `sales_<channel>_view`.
    - Etc.
  - Replace `sales_analytics` with this view name using a regex with word boundaries.

For the AI chatbot flow, we rely primarily on **Python‑side RBAC filters** (`_build_rbac_filters`) in conjunction with views (if configured).

#### 5.3 In‑query RBAC (`_build_rbac_filters`)

File: `ai_query_builder.py`.

Key behavior:

- Input: `access` (from MongoDB), `intent_filters`, `dimensions`.
- `access_key_map` links dimensions → access fields:
  - `"business"` → `"businesses"`
  - `"channel"` → `"channels"`
  - `"brand"` → `"brands"`
  - `"category"` → `"categories"`
  - `"sub_category"` → `"sub_categories"`
  - `"customer"` → `"customers"`
  - `"sku"` → `"sku"`

Two helper functions:

- `_normalize_allowed(allowed_values)`:
  - `None` → `[]`
  - List → unchanged
  - `"*"` / `"all"` → `["*"]`

- `_has_full_access(allowed_values)`:
  - True for `"*"`, `"all"`, `["*"]`, or lists containing `"all"`.
  - **Empty list** is **not** full access.

Then:

1. **Detect restricted dimensions:**
   - `restricted_dims = set(dimensions) ∪ {d for d in intent_filters if d in access_key_map and intent_filters[d]}`.

2. **“No access” shortcut:**
   - For each `dimension` in `restricted_dims`:
     - Get `allowed = _normalize_allowed(access[access_key_map[dimension]])`.
     - If `_has_full_access(allowed)` → do nothing.
     - If `allowed` is empty (no access):
       - Log: `RBAC: user has no access to <dimension> (empty list); denying query.`
       - Append `"1 = 0"` to `filters` and **return** immediately.
       - This ensures the SQL always returns **zero rows** when the user has no access for a dimension that the query needs.

3. **Limited access without explicit intent filter:**
   - For each `dimension` in **`dimensions`**:
     - If `intent_filters[dimension]` is empty but `allowed_values` is a non‑empty list:
       - Add `lowerUTF8(dimension) IN (<allowed_values>)` using a formatted `IN` clause.

4. **Intent‑specified filters:**
   - For each `(dimension, intent_values)` in `intent_filters` where `intent_values` is non‑empty:
     - If user has full access → use intent values as is.
     - If user has a limited set → only keep intent values that are in `allowed_values`.
     - If none are allowed → log a warning and add `"1 = 0"` so the query returns zero rows.

**Result:** for a user with `businesses: []`:

- Any question using the `business` dimension (“top 5 business”, “baking category belongs to which business”, etc.) produces:
  - A query with `... WHERE tenant_id = '...' AND 1 = 0 ...`.
  - Zero data rows returned.
  - `AIService` then returns an RBAC denial message (Section 7).

---

### 6. Response generation (`AIResponseService`)

File: `backend/app/services/ai/ai_response_service.py`.

#### 6.1 LLM prompt and formatting rules

- `generate_response(question, data, intent)` builds a prompt with:
  - Raw `data` as JSON (from ClickHouse).
  - A `data_intro` that tells the LLM:
    - This data is the **source of truth**.
    - Start by listing entities (`Business`/`Brand`/`Category`/`Channel` etc.) with **Revenue**, **Profit**, **margin**, and **Cases**.
    - Then write **Key Insights**, **Performance Analysis / What These Numbers Mean**, **Recommendations**, etc.
  - For **“top N”** questions, a helper `_top_n_header()` builds a header like:
    - `"Top 5 Businesses by Revenue in 2025:"`
  - The prompt tells the LLM:
    - Start the response with **exactly** that header line for top‑N queries.
    - Always show margins with **one decimal place** (e.g. `31.9%`, `41.0%`).

- After the LLM responds, small regex post‑processing normalizes integer `% margin` values to one decimal (e.g. `41% margin` → `41.0% margin`), without touching already‑decimal values (`31.9%`).

#### 6.2 Fallback response

If the LLM fails or throws, `_generate_fallback_response(question, data, intent)`:

- Parses each row to `(label, revenue, profit, cases, margin_pct)`:
  - `label` uses (in order): `channel`, `brand`, `business`, `category`, `year` fields from the row.
- Builds:
  - A header: **Top N …** (if applicable) or `**Data:**`.
  - A line per row: `"Label: Revenue €X.XXM, Profit €Y.YY M (Z.Z% margin), Cases N"`.
  - **Key Insights:** who leads in revenue, who has highest margin, etc.
  - **Recommendations:** generic optimization ideas.
- Uses one‑decimal margins in all bullet points.

This ensures the chatbot still gives a decent explanation when the LLM is down or returns invalid output.

---

### 7. How RBAC denial appears in responses

When `_build_rbac_filters` injects `1 = 0` (no access), the SQL will be valid and return **zero rows**.

In `AIService.process_question`:

```python
rows = result_data if isinstance(result_data, list) else []
query_str = str(debug_info.get("query", "") or "")
if len(rows) == 0 and "1 = 0" in query_str:
    # RBAC layer deliberately denied this query (no access to requested dimension)
    # Build RBAC message instead of “no data”
```

The service then:

1. Inspects `intent["dimensions"]` and `intent["filters"]` to see which dimension was used.
2. Inspects `access` to find which dimension had **no access** (empty list).
3. Maps the dimension → human text:
   - `"business"` → “business‑level data”
   - `"brand"` → “brand‑level data”
   - `"category"` → “category‑level data”
   - `"channel"` → “channel‑level data”
   - `"customer"` → “customer‑level data”
   - `"sku"` → “SKU‑level data”
4. Returns a message like:

> You don't currently have permission to view **business‑level data** for this question. Please contact your system administrator if you believe you should have access.

The frontend receives this as the `response` field, with `data: []` and `pivot_table: []`, and `needs_clarification = False` (this is an explicit RBAC result, not a clarification request).

---

### 8. Examples and mental models

#### 8.1 “Tell me top 5 business”

- User: has `businesses = []` (no business access).
- Question: `"tell me top 5 business"`.

Intent (simplified):

```json
{
  "metric": "gsales",
  "dimensions": ["business"],
  "filters": {
    "business": [],
    "year": [],
    ...
  },
  "time_range": { "type": "custom", "value": null },
  "aggregation": "sum",
  "limit": 5
}
```

Normalization:

- Metric stays `"gsales"`.
- `time_range` remains `"custom"` (no year or specific time).

RBAC:

- `dimensions = ["business"]`.
- `access["businesses"] = []` → no access.
- `_build_rbac_filters` detects **no access** for a used dimension and returns:
  - Filters: `["1 = 0"]`.

SQL (conceptually):

```sql
SELECT business, SUM(gsales) AS revenue, ...
FROM bizpulse.sales_analytics
WHERE tenant_id = '...' AND 1 = 0
GROUP BY business
ORDER BY revenue DESC
LIMIT 5;
```

Result: zero rows.

`AIService` sees `1 = 0` in the query and returns an RBAC message: no business‑level permission.

#### 8.2 “baking category belongs to which business”

- User: no business access; categories = "all".

Intent (from log):

```json
{
  "metric": "gsales",           // normalized from empty
  "dimensions": ["business"],
  "filters": {
    "category": ["baking"],
    "business": [],
    "year": [],
    ...
  },
  "time_range": { "type": "lifetime", "value": null },
  "aggregation": "count",
  "limit": 1000
}
```

RBAC:

- Dimension used: `business`.
- `access.businesses = []` → RBAC denies with `1 = 0`.

SQL returns zero rows; `AIService` returns a **business‑level RBAC message**.

#### 8.3 “Tell me revenue of Kinetica business”

- If user has `businesses = ["Kinetica"]` and question is `"tell me revenue of Kinetica business"`:
  - Intent sets `filters.business = ["Kinetica"]`, `dimensions = ["year"]` or none (depending on question).
  - `_build_rbac_filters` allows `business = 'Kinetica'` (in allowed list).
  - Query returns real Kinetica data; `AIResponseService` generates a normal business explanation.

---

### 9. How to reuse this design in another project

If you want to port this architecture to another system:

1. **Define your dimensions and metrics clearly.**
   - Decide which columns are “dimensions” (group‑by) and which are “metrics” (aggregates).
   - Create `METRIC_COLUMNS` and `DIMENSION_COLUMNS` mappings.

2. **Design the user access model:**
   - For each dimension you want to restrict (business, brand, category, region, etc.), add a list or `"all"` to the user’s `access` object.
   - Decide the semantics:
     - `[]` → no access.
     - `"all"` / `"*"` → full access.

3. **Implement `_build_rbac_filters`:**
   - Mirror the pattern described above:
     - If a dimension is used and `allowed_values` is empty → append `1 = 0` and return.
     - If the dimension is used and `allowed_values` is limited → restrict to those values with an `IN (...)` clause.
     - If the dimension is used and user has full access → don’t add an extra filter.

4. **Implement an intent model similar to this repo:**
   - Use LLM + normalization, or a pure rules‑based parser, but keep the same **shape**:
     - `metric`, `dimensions`, `filters`, `time_range`, `aggregation`, `limit`.

5. **Add a clear RBAC‑denied branch in your service layer:**
   - Recognize when your query has been deliberately neutralized (`1 = 0` or similar).
   - Return a **permission message**, not “no data” and not a 500.

6. **Keep fallback + formatting separate from business logic:**
   - `AIResponseService` is a good pattern: one place for text formatting, LLM prompts, and fallbacks.

Using this document as a guide, you should be able to:

- Explain exactly how RBAC and intents work in this chatbot.
- Debug any “no data” vs “no access” issues.
- Recreate the same layered architecture (clarity → intent → query builder with RBAC → LLM/fallback) in a different codebase without losing important behavior.

