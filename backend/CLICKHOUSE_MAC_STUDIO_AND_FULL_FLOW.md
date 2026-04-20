# My Understanding + Steps: Connect Project to Mac Studio ClickHouse & Complete Flow

I’ve read **MONGODB_CLICKHOUSE_SETUP_UNDERSTANDING_AND_ARCHITECTURE.md**, **IMPLEMENTATION_COMPLETE.md**, and **CLICKHOUSE_SALES_ANALYTICS_ARCHITECT_FINAL.md**. Below is my understanding and the exact steps/commands so you can connect your Windows project to ClickHouse on Mac Studio and test the full flow.

---

## 1. My Understanding

### 1.1 Your Physical Setup

| Component | Where it runs | Purpose |
|-----------|----------------|---------|
| **Project (backend + frontend)** | **Windows laptop** | FastAPI backend + React frontend; you develop and run here. |
| **MongoDB Atlas** | **Cloud** | Login, auth, RBAC (users, `bizpulse_rbac`). Accessible from anywhere. |
| **ClickHouse** | **Mac Studio (local)** | Analytics only (`bizpulse.sales_analytics`). Runs in Docker (e.g. `clickhouse-prod`), port **9000** (native TCP). |
| **LLM (Qwen 32b)** | **Mac Studio (local)** | Ollama on ports 11434, 11435, 11436, 11437. Already reachable from laptop inside and outside office. |

So: **laptop** talks to **MongoDB Atlas** (cloud) and to **Mac Studio** (ClickHouse + LLM).

### 1.2 Network Access to Mac Studio

- **Inside office (same LAN):**  
  Mac Studio is at **192.168.50.29**.  
  You use this for Ollama and want the same for ClickHouse.

- **Outside office:**  
  You reach Mac Studio via **49.249.157.19** (static IP from ISP).  
  You SSH with `ssh thrivestudio@192.168.50.29` (in office) or `ssh thrivestudio@49.249.157.19` (outside).  
  LLM is already reachable from outside (so something—e.g. router port forwarding or VPN—exposes Ollama ports to 49.249.157.19).

- **Goal for ClickHouse:**  
  Use it the same way as the LLM:  
  - In office: backend uses **192.168.50.29** for ClickHouse.  
  - Outside: backend uses **49.249.157.19** for ClickHouse (so port **9000** must be reachable at 49.249.157.19:9000, similar to 11434 for Ollama).

### 1.3 Intended End-to-End Flow

1. **Login:** User logs in → backend uses **MongoDB Atlas** → JWT issued.
2. **RBAC:** All permission checks and user/role data come from **MongoDB Atlas** (`bizpulse_rbac`).
3. **Analytics / AI chatbot:**  
   - Backend (on Windows laptop) loads RBAC from MongoDB Atlas.  
   - Builds safe SQL from intent + RBAC.  
   - Sends query to **ClickHouse on Mac Studio** (192.168.50.29 or 49.249.157.19:9000).  
   - Optionally calls **LLM on Mac Studio** for intent/explanation.  
   - Returns response to frontend.

So: **MongoDB Atlas = auth + RBAC**; **ClickHouse on Mac Studio = analytics data**; **LLM on Mac Studio = AI**. Backend ties them together.

### 1.4 What “Connect project to Mac Studio ClickHouse” Means

- Backend (Python `clickhouse_client`) uses **CLICKHOUSE_HOST** and **CLICKHOUSE_PORT** from `.env`.
- When you’re in office: `CLICKHOUSE_HOST=192.168.50.29` (and port 9000) so the laptop can connect directly to Mac Studio.
- When you’re outside: `CLICKHOUSE_HOST=49.249.157.19` (and port 9000) so the laptop can connect via your static IP.  
So “connect” = correct `.env` + Mac Studio allowing remote connections on 9000 + (when outside) network allowing 49.249.157.19:9000 to reach Mac Studio.

### 1.5 What Must Be True on Mac Studio for ClickHouse

- ClickHouse server must **listen on 0.0.0.0** (or equivalent), not only 127.0.0.1, so that connections from the laptop (and via 49.249.157.19 when outside) are accepted.
- Port **9000** (native TCP, used by `clickhouse-driver`) must be open and forwarded when you’re outside (same idea as Ollama ports).
- User `bizpulse_admin` (or whatever is in `.env`) must exist and have rights on `bizpulse` DB / `sales_analytics` table.
- Database `bizpulse` and table `sales_analytics` must exist (schema as in CLICKHOUSE_SALES_ANALYTICS_ARCHITECT_FINAL / runbook).

### 1.6 Switching Between Office and Outside

- Today you already switch Ollama: in office you use 192.168.50.29 in OLLAMA_* and outside you use 49.249.157.19 (commented in `.env`).
- For ClickHouse we do the same: **one .env for office** (CLICKHOUSE_HOST=192.168.50.29) and **when outside**, change to CLICKHOUSE_HOST=49.249.157.19 (or use a second .env and swap).

I’ve captured this in the “Steps” section below.

---

## 2. Steps and Commands to Complete Setup and Test Full Flow

### Phase A: On Mac Studio (ClickHouse reachable from laptop)

Do these once (or after Mac Studio / Docker / network changes).

**A.1 – SSH into Mac Studio**

- In office:  
  `ssh thrivestudio@192.168.50.29`
- Outside:  
  `ssh thrivestudio@49.249.157.19`

**A.2 – Ensure ClickHouse is running and listening on all interfaces**

- Check container (example name `clickhouse-prod`):  
  `docker ps | grep clickhouse`  
  If not running:  
  `docker start clickhouse-prod`
- If you need to (re)create the container so port 9000 is bound to 0.0.0.0 (same as in your existing docs):

  ```bash
  docker run -d --name clickhouse-prod \
    -p 0.0.0.0:9000:9000 \
    -p 0.0.0.0:18123:8123 \
    clickhouse/clickhouse-server
  ```

- Confirm port 9000 is listening:  
  `ss -tlnp | grep 9000` or `netstat -an | grep 9000`

**A.3 – Allow ClickHouse to accept remote connections (config)**

- Edit server config (path can vary; common one):  
  `sudo nano /etc/clickhouse-server/config.xml`  
  or, if run from Docker, the config might be in the container or a mounted volume.
- Ensure you have (or add):  
  `<listen_host>0.0.0.0</listen_host>`  
  so it’s not only `127.0.0.1`.
- Restart ClickHouse (e.g. restart the container):  
  `docker restart clickhouse-prod`

**A.4 – Create DB, user, and table (if not already done)**

- Attach to ClickHouse (e.g. inside container):  
  `docker exec -it clickhouse-prod clickhouse-client`
- Then run (adjust user/password to match your `.env`):

  ```sql
  CREATE DATABASE IF NOT EXISTS bizpulse;

  CREATE USER IF NOT EXISTS bizpulse_admin IDENTIFIED BY 'Admin@123!Secure';
  GRANT ALL ON bizpulse.* TO bizpulse_admin;

  -- Create sales_analytics if not exists (schema from CLICKHOUSE_SALES_ANALYTICS_ARCHITECT_FINAL / runbook)
  CREATE TABLE IF NOT EXISTS bizpulse.sales_analytics (
    tenant_id LowCardinality(String),
    date Date,
    year UInt16 MATERIALIZED toYear(date),
    month UInt8 MATERIALIZED toMonth(date),
    quarter UInt8 MATERIALIZED toQuarter(date),
    year_month UInt32 MATERIALIZED toYYYYMM(date),
    month_name LowCardinality(String),
    business LowCardinality(String),
    channel LowCardinality(String),
    customer LowCardinality(String),
    brand LowCardinality(String),
    category LowCardinality(String),
    sub_category LowCardinality(String),
    sku LowCardinality(String),
    cases Decimal(15,2),
    gsales Decimal(15,2),
    price_downs Decimal(15,2),
    perm_disc Decimal(15,2),
    transfer_cost Decimal(15,2),
    group_cost Decimal(15,2),
    lta Decimal(15,2),
    fgp Decimal(15,2),
    created_at DateTime DEFAULT now()
  )
  ENGINE = MergeTree()
  PARTITION BY toYYYYMM(date)
  ORDER BY (tenant_id, date, business, channel, brand, category, sub_category, customer, sku);
  ```

**A.5 – (When outside office) Expose port 9000 to the internet**

- Your static IP 49.249.157.19 already reaches Mac Studio for Ollama, so the router likely forwards a range or specific ports to Mac Studio.
- Ensure **port 9000** is forwarded to Mac Studio’s IP (192.168.50.29) on the router, same idea as 11434 for Ollama.
- If you use a firewall on Mac Studio, allow inbound TCP 9000.

---

### Phase B: On Windows Laptop (project and .env)

**B.1 – Use the right host in `.env` for where you are**

- **When in office:**  
  In `backend\.env`:  
  `CLICKHOUSE_HOST=192.168.50.29`  
  `CLICKHOUSE_PORT=9000`
- **When outside office:**  
  In `backend\.env`:  
  `CLICKHOUSE_HOST=49.249.157.19`  
  `CLICKHOUSE_PORT=9000`

(Optional: keep two files, e.g. `.env.office` and `.env.remote`, and copy the right one to `.env` when you switch.)

**B.2 – Other .env settings (already aligned with architecture)**

- MongoDB Atlas (login + RBAC):  
  `MONGO_URL=...`  
  `DB_NAME=bizpulse_rbac`
- ClickHouse:  
  `CLICKHOUSE_DB=bizpulse`  
  `CLICKHOUSE_USER=bizpulse_admin`  
  `CLICKHOUSE_PASSWORD=Admin@123!Secure`  
  `TENANT_ID=client_001`
- LLM (Mac Studio):  
  In office: OLLAMA_BASE_URL / OLLAMA_ENDPOINTS with 192.168.50.29.  
  Outside: same but 49.249.157.19.

**B.3 – Test ClickHouse connection from laptop**

From `backend` folder:

```powershell
cd C:\Users\Sumit Mishra\Documents\Bizpulse\backend
C:\Python314\python.exe -c "from app.database.clickhouse_client import ClickHouseClient; c = ClickHouseClient(); print('OK:', c.execute('SELECT 1', enforce_time_filter=False))"
```

If you see `OK: [(1,)]` (or similar), the project is connected to Mac Studio ClickHouse.

---

### Phase C: Complete flow (MongoDB + ClickHouse + optional migration)

**C.1 – MongoDB (bizpulse_rbac) and RBAC**

Run from `backend` (if not already done):

```powershell
cd C:\Users\Sumit Mishra\Documents\Bizpulse\backend
C:\Python314\python.exe scripts\copy_bizpulse_to_bizpulse_rbac.py
C:\Python314\python.exe scripts\add_user_rbac_fields.py --target-db bizpulse_rbac
C:\Python314\python.exe scripts\setup_ai_cache_collection.py
```

**C.2 – Load data into ClickHouse (one-time)**

Migration reads from MongoDB `business_data` (DB from DB_NAME in .env, i.e. bizpulse_rbac) and writes to ClickHouse `sales_analytics`:

```powershell
C:\Python314\python.exe scripts\migrate_real_data_to_clickhouse.py
```

(If the script expects a different DB for the source, use that; the runbook says “source DB can be bizpulse or bizpulse_rbac”.)

**C.3 – Verify full setup**

```powershell
C:\Python314\python.exe scripts\verify_complete_setup.py
```

This checks MongoDB, ClickHouse, RBAC, and ai_cache.

**C.4 – Run backend and test AI chatbot**

- Start backend (from project root or backend, however you usually do).
- Call:  
  `POST /api/ai/chatbot/chat`  
  Headers: `Authorization: Bearer <JWT>`  
  Body: `{"question": "Show revenue for Food business last 6 months"}`  

Full flow: Login (MongoDB Atlas) → RBAC from MongoDB → intent (LLM on Mac Studio) → SQL build → query ClickHouse (Mac Studio) → cache (MongoDB) → explanation (LLM) → response.

---

## 3. Summary Table

| What | Where | How you connect |
|------|--------|------------------|
| Login + RBAC | MongoDB Atlas | MONGO_URL, DB_NAME=bizpulse_rbac (same from anywhere). |
| ClickHouse | Mac Studio | CLICKHOUSE_HOST=192.168.50.29 (office) or 49.249.157.19 (outside), port 9000. |
| LLM | Mac Studio | OLLAMA_* with 192.168.50.29 (office) or 49.249.157.19 (outside). |
| Backend | Windows laptop | Uses .env; switch CLICKHOUSE_HOST (and OLLAMA_* if needed) when changing network. |

---

## 4. If Something Fails

- **ClickHouse connection refused (office):**  
  Check Mac Studio IP (192.168.50.29), Docker container running, port 9000 listening, `listen_host=0.0.0.0`.
- **ClickHouse connection refused (outside):**  
  Check router forwards TCP 9000 to Mac Studio; firewall on Mac Studio allows 9000; .env has CLICKHOUSE_HOST=49.249.157.19.
- **Auth error to ClickHouse:**  
  Check CLICKHOUSE_USER / CLICKHOUSE_PASSWORD and that the user exists and has rights on `bizpulse`.
- **MongoDB/RBAC issues:**  
  Run the scripts in C.1 again; confirm DB_NAME=bizpulse_rbac and MONGO_URL is correct.

---

I’ve not changed any code in this step; this is only understanding and a concrete runbook. If this matches what you want, next we can (1) add a short “office vs remote” note to the runbook and (2) optionally add a small script or .env.example that shows both CLICKHOUSE_HOST options. If you want different IPs or a different way to switch (e.g. env files), say how you prefer it and we’ll align to that.
