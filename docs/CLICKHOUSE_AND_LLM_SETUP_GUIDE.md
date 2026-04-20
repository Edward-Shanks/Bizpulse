## ClickHouse & Local LLM Setup Guide (for Re‑use in Other Projects)

This guide explains **all the moving parts** used in this project to:

- Create and manage the **ClickHouse** analytics table (`bizpulse.sales_analytics`).
- **Migrate data** from MongoDB (`business_data`) → ClickHouse.
- Wire ClickHouse into the **AI chatbot** (intent → query → RBAC → response).
- Configure and use a **local LLM** via **Ollama** (or other providers).

You can copy these files and steps into another project to reuse the same architecture.

---

### 1. Key files for ClickHouse

**Schema & table creation**

- `CREATE_TABLE_ONLY.sql`  
  - Contains minimal `CREATE TABLE IF NOT EXISTS bizpulse.sales_analytics (...)` for base table.

- `backend/scripts/create_schema.sql`  
  - More complete schema definition and helper commands:
    - Create DB `bizpulse` if not exists.
    - Create `sales_analytics` table with:
      - `tenant_id`,
      - `date`,
      - MATERIALIZED time columns: `year`, `month`, `quarter`, `year_month`,
      - `month_name` (string),
      - dimensions: `business`, `channel`, `customer`, `brand`, `category`, `sub_category`, `sku`,
      - metrics: `cases`, `gsales`, `price_downs`, `perm_disc`, `transfer_cost`, `group_cost`, `lta`, `fgp`,
      - `created_at`.

- `COMMANDS_LAPTOP_AND_MAC_STUDIO.md`  
- `CREATE_TABLE_COMMANDS.md`  
- `CLICKHOUSE_MAC_STUDIO_AND_FULL_FLOW.md`  
- `MONGODB_CLICKHOUSE_SETUP_UNDERSTANDING_AND_ARCHITECTURE.md`  
  - Documentation describing:
    - How to run ClickHouse in Docker (e.g. `clickhouse-prod`).
    - DB and table names: `bizpulse.sales_analytics`.
    - Why analytics lives in ClickHouse (not Mongo).
    - How to verify the table exists and is populated.

**ClickHouse client & RBAC**

- `backend/app/database/clickhouse_client.py`
  - Central wrapper around the Python `clickhouse_driver` client.
  - Responsibilities:
    - Manage host/port/DB/user/password from env (`CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, etc.).
    - Inject `tenant_id` filters into every query (`_inject_tenant_filter`).
    - Optionally inject **default time filters** when `enforce_time_filter=True` (`_add_default_time_filter`).
    - Replace `sales_analytics` base table name with **RBAC views** for certain calls:
      - `execute_with_rbac`, `execute_dict_with_rbac`:
        - Uses `_get_user_view(user_permissions)` to pick a view (e.g. `sales_food_view`, `sales_kinetica_view`, `sales_grocery_view`).
        - Replaces `sales_analytics` with the view via a regex with word boundaries.
    - Convenience helpers:
      - `execute`, `execute_dict` – run arbitrary SQL and return rows / dicts.
      - `get_table_info('sales_analytics')` – check schema and row counts.

**Migration scripts (MongoDB → ClickHouse)**

- `backend/scripts/migrate_real_data_to_clickhouse.py`
  - Main **one‑time or repeatable migration** script.
  - Reads from MongoDB `business_data` and writes to `CLICKHOUSE_DB.sales_analytics`.
  - Key behaviors:
    - Validates that `sales_analytics` exists; if not, prints instructions.
    - Can truncate the table before insert (for full reload).
    - Inserts using explicit column lists to avoid mismatches:
      ```sql
      INSERT INTO {CLICKHOUSE_DB}.sales_analytics (
          tenant_id,
          date,
          month_name,
          business,
          channel,
          customer,
          brand,
          category,
          sub_category,
          sku,
          cases,
          gsales,
          price_downs,
          perm_disc,
          transfer_cost,
          group_cost,
          lta,
          fgp
      ) VALUES ...
      ```
    - Batches inserts to avoid huge payloads.
    - Prints total row count from ClickHouse after migration.

- `backend/scripts/copy_bizpulse_mongo_to_clickhouse.py`
  - Wrapper script for:
    - Running the existing migration pipeline (business_data → sales_analytics).
    - Copying other Mongo collections to a `mongodb_sync` table if needed.

- `COLUMN_MISMATCH_FIX.md`, `MONTH_NAME_FIX_COMPLETE.md`  
  - Notes about fixing schema mismatches (e.g. `Cases` → `cases`, `fGP` → `fgp`, `Month_Name` vs `month_name`).

**Verification & quick checks**

- `RUN_MIGRATION_NOW.md`
- `MIGRATION_COMMANDS.md`
- `FINAL_STATUS_AND_COMMANDS.md`
  - Provide example commands like:
    - `SELECT count(*) FROM sales_analytics;`
    - `SELECT business, count(*) FROM sales_analytics GROUP BY business ...;`
    - Python one‑liners using `ClickHouseClient` to print row counts and sample data.

---

### 2. Key files for the AI chatbot + ClickHouse

These files build the pipeline from **user question → ClickHouse SQL → data → explanation** with RBAC:

- `backend/app/services/ai/ai_intent_service.py`
  - LLM‑driven intent extraction.
  - Produces JSON with fields:
    - `metric` (gsales, fgp, cases, etc.).
    - `dimensions` (business, brand, channel, category, customer, sku, year, quarter, month_name).
    - `filters` (per dimension).
    - `time_range` (lifetime, last_n_months, last_n_days, current_month, custom).
    - `aggregation` (sum, avg, count, ...).
    - `limit` (for top N).
  - Also includes deterministic fallback parsing and normalization for:
    - Top N questions.
    - Before/after January 2024.
    - Convenience vs Grocery channel comparisons.
    - Multi‑brand comparisons.

- `backend/app/services/ai/ai_query_builder.py`
  - Converts **intent + RBAC access** into **ClickHouse SQL**.
  - Uses `METRIC_COLUMNS` and `DIMENSION_COLUMNS` mappings to build `SELECT`, `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`.
  - Calls `_build_rbac_filters(access, filters, dimensions)` to apply per‑dimension RBAC (business, channel, brand, category, sub_category, customer, sku).
  - Calls `_build_direct_filters(filters)` for `year`, `quarter`, `month_name`.
  - Works directly with `sales_analytics` (ClickHouse client later rewrites to views if using RBAC views).

- `backend/app/services/ai/ai_service.py`
  - Main orchestration service for `POST /api/ai/chatbot/chat`.
  - Steps:
    1. Load user RBAC (`access`) from Mongo.
    2. Run clarity/off‑topic checks.
    3. Extract intent via `AIIntentService`.
    4. Call `AIQueryBuilder.build_query(intent, access, tenant_id)` to get `(sql, is_lifetime)`.
    5. Execute SQL via `ClickHouseClient.execute_dict(...)`.
    6. If query has `1 = 0` (RBAC denial) → return explicit **“you don’t have permission”** message.
    7. Otherwise call `AIResponseService.generate_response(...)` to build explanation, and cache it.
    8. Build a `pivot_table` for charts and return data + explanation.

- `backend/app/services/ai/ai_response_service.py`
  - Calls the LLM with the raw ClickHouse rows to generate human‑friendly output.
  - Has a deterministic fallback `_generate_fallback_response` that formats:
    - Entity list (businesses, brands, channels, etc.).
    - “Key Insights” and “Recommendations” sections.
  - Normalizes margin formatting (e.g. `41%` → `41.0%`).
  - Adds top‑N headings (`Top 5 Brands by Revenue in 2025:`) based on intent and/or question text.

- `backend/app/services/ai/ai_cache_service.py`
  - Caches ClickHouse results and LLM explanations by:
    - `tenant_id`, `permissions_hash`, `intent_hash`, `result_hash`, `question_hash`.
  - Also queries ClickHouse for latest data date (`max(date)` from `sales_analytics`) to invalidate cache when data changes.

- `backend/app/utils/ai_service.py`
  - Generic utility to call the configured LLM provider (`LLM_PROVIDER` env var):
    - Orchestrates Ollama / Perplexity / vLLM client based on configuration.
    - Creates prompts, logs request/response sizes, and handles provider failures.

---

### 3. Local LLM (Ollama) integration

**Configuration**

- `backend/app/core/config.py`
  - LLM‑related fields:
    - `LLM_PROVIDER` – which provider to use (e.g. `"ollama"`, `"perplexity"`, `"vllm"`).
    - `OLLAMA_BASE_URL` – main Ollama instance URI (e.g. `http://localhost:11436`).
    - `OLLAMA_ENDPOINTS` – optional **comma‑separated list** of Ollama endpoints for load balancing:
      - Example: `OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.29:11435`.
    - `OLLAMA_MODEL` – primary local model (e.g. `qwen2.5:32b-instruct`).
    - `OLLAMA_FALLBACK_MODEL` – fallback model (e.g. `llama3:70b`).
    - `OLLAMA_TIMEOUT` – seconds (or ms) before giving up on a call.

- `.env` (backend)
  - Typical entries:
    ```env
    LLM_PROVIDER=ollama
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=qwen2.5:32b-instruct
    OLLAMA_FALLBACK_MODEL=llama3:70b
    OLLAMA_TIMEOUT=120
    # Optional for multi-endpoint load balancing:
    # OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.29:11435
    ```

**Provider implementation**

- `backend/app/utils/llm_providers/ollama.py`
  - Implements a client class that:
    - Uses `settings.OLLAMA_ENDPOINTS` if configured, otherwise falls back to `OLLAMA_BASE_URL`.
    - Provides methods for:
      - Health check (GET `/api/tags`).
      - Chat/completion (POST `/api/chat`).
  - Handles:
    - Timeouts using `OLLAMA_TIMEOUT`.
    - Failover between endpoints if one is down.

- `backend/app/utils/llm_providers/factory.py`
  - Chooses provider (Ollama, Perplexity, vLLM, etc.) based on:
    - Parameter `provider_name`, or
    - `LLM_PROVIDER` env var.

- `backend/app/api/debug.py`
  - Has **debug endpoints** to show current LLM settings and test Ollama connectivity:
    - Current `LLM_PROVIDER`.
    - `OLLAMA_BASE_URL`, `OLLAMA_ENDPOINTS`.

---

### 4. End‑to‑end ClickHouse data flow (for a new project)

To reuse this setup in a different project, follow these steps.

#### 4.1. Prepare ClickHouse

1. **Run ClickHouse** (e.g. Docker):
   - See `CLICKHOUSE_MAC_STUDIO_AND_FULL_FLOW.md` or `COMMANDS_LAPTOP_AND_MAC_STUDIO.md` for example docker commands.
   - Ensure ClickHouse is reachable from your backend (host + port).

2. **Create DB + table**:
   - Use `create_schema.sql` or `CREATE_TABLE_ONLY.sql`:
     - Either connect via `clickhouse-client` inside the container:
       ```bash
       docker exec -it clickhouse-prod clickhouse-client --database=bizpulse
       ```
     - Then run:
       ```sql
       CREATE TABLE IF NOT EXISTS bizpulse.sales_analytics (...);
       ```
   - Or run the commands from `CREATE_TABLE_COMMANDS.md`.

3. **Check table exists**:
   - Inside ClickHouse:
     ```sql
     SHOW TABLES FROM bizpulse;
     DESCRIBE TABLE bizpulse.sales_analytics;
     ```

#### 4.2. Prepare MongoDB source

1. Ensure you have a MongoDB collection with your analytics/fact data (equivalent to `business_data`):
   - Must have:
     - `Year`, `Month_Name`, `Business`, `Channel`, `Customer`, `Brand`, `Category`, `Sub_Cat`, etc.
     - Metrics: units/cases, revenue (gSales), fGP, etc.

2. Adjust `migrate_real_data_to_clickhouse.py` if your schema naming differs:
   - Map Mongo field names → ClickHouse columns (`sales_analytics` schema).
   - Re‑use the explicit `INSERT INTO ... (columns) VALUES` pattern to avoid confusion.

#### 4.3. Run the migration

1. Configure env in `backend/.env`:
   - `MONGO_URL`, `DB_NAME` to point to your Mongo.
   - `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_DB`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`.

2. Run migration script:
   ```bash
   cd backend
   python scripts/migrate_real_data_to_clickhouse.py
   ```

3. Verify row count:
   - Using ClickHouse CLI or the Python one‑liner from `FINAL_STATUS_AND_COMMANDS.md`:
     ```bash
     python -c "from app.database.clickhouse_client import ClickHouseClient; ch = ClickHouseClient(); print(ch.execute('SELECT count(*) FROM sales_analytics')[0][0])"
     ```

#### 4.4. Wire into AI chatbot (optional, if you want the same AI layer)

If your new project also needs an AI chatbot over ClickHouse:

1. Copy these modules (and their deps):
   - `backend/app/database/clickhouse_client.py`
   - `backend/app/services/ai/ai_intent_service.py`
   - `backend/app/services/ai/ai_query_builder.py`
   - `backend/app/services/ai/ai_response_service.py`
   - `backend/app/services/ai/ai_cache_service.py`
   - `backend/app/services/ai/ai_service.py`
   - `backend/app/utils/ai_service.py`
   - `backend/app/utils/llm_providers/ollama.py`
   - `backend/app/utils/llm_providers/factory.py`
   - `backend/app/core/config.py` (or at least the LLM + ClickHouse parts).

2. Expose an endpoint similar to `POST /api/ai/chatbot/chat`:
   - See `backend/app/api/v1/routes/ai_chatbot.py` in this project.

3. Update any **dimension/metric names** in:
   - `METRIC_COLUMNS` / `DIMENSION_COLUMNS` in `ai_query_builder.py`.
   - Intent prompt rules in `ai_intent_service.py`.

4. For RBAC, reuse the same `access` structure:
   - User documents in Mongo with:
     ```json
     "access": {
       "businesses": "all" | ["Food", "Kinetica"] | [],
       "channels": "all" | ["Grocery"] | [],
       "brands": "all" | ["Koka"] | [],
       "categories": "all" | ["Curry"] | [],
       "sub_categories": "all" | ["BCAA"] | [],
       "customers": "all" | ["Tesco ROI"] | []
     }
     ```
   - `_build_rbac_filters` in `ai_query_builder.py` already knows how to interpret `"all"` vs list vs empty.

#### 4.5. Configure local LLM

1. Install and run **Ollama** on your machine:
   - Install Ollama from their site.
   - Pull the model you want, e.g. `qwen2.5:32b-instruct`:
     ```bash
     ollama pull qwen2.5:32b-instruct
     ```
   - Ensure it's listening at the URL you specify (e.g. `http://localhost:11434`). For multiple instances, run them on different ports.

2. Update backend `.env`:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=qwen2.5:32b-instruct
   OLLAMA_TIMEOUT=120
   ```
   - Optionally set `OLLAMA_ENDPOINTS` if using multiple endpoints.

3. Start the FastAPI app (`uvicorn app.main:app --reload ...`) and test:
   - Use `/api/debug/llm` (if present) to verify provider and endpoints.
   - Hit the AI chatbot route with a known question and verify it returns, with logs showing Ollama usage.

---

### 5. Minimal file list to copy for another project

If you just want the **essentials** to reuse in another project, start with this list:

**ClickHouse core**

- `backend/app/database/clickhouse_client.py`
- `backend/scripts/create_schema.sql` (or `CREATE_TABLE_ONLY.sql`)
- `backend/scripts/migrate_real_data_to_clickhouse.py`
- `.env` entries for `CLICKHOUSE_*` and `TENANT_ID`

**AI chatbot + ClickHouse**

- `backend/app/services/ai/ai_intent_service.py`
- `backend/app/services/ai/ai_query_builder.py`
- `backend/app/services/ai/ai_response_service.py`
- `backend/app/services/ai/ai_cache_service.py`
- `backend/app/services/ai/ai_service.py`
- `backend/app/api/v1/routes/ai_chatbot.py`

**LLM integration (local Ollama by default)**

- `backend/app/utils/ai_service.py`
- `backend/app/utils/llm_providers/ollama.py`
- `backend/app/utils/llm_providers/factory.py`
- `backend/app/core/config.py` (or at least the `Settings` fields related to `LLM_PROVIDER`, `OLLAMA_*`)
- `.env` entries for `LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, etc.

Copying these files + adjusting environment variables and schema names is usually enough to:

- Run ClickHouse locally.
- Migrate your own analytics data into `sales_analytics` (or a similarly structured table).
- Expose an AI chatbot over that data using a local LLM via Ollama, with RBAC and intent‑driven SQL generation.

