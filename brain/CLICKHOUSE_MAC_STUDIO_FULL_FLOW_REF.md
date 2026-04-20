# ClickHouse on Mac Studio — Full flow and access from laptop

**Main doc:** `backend/CLICKHOUSE_MAC_STUDIO_AND_FULL_FLOW.md`

## In one sentence

- **MongoDB Atlas:** login + RBAC (bizpulse_rbac); used from anywhere.
- **ClickHouse:** on Mac Studio (Docker, port 9000); laptop connects with **192.168.50.29** (office) or **49.249.157.19** (outside); switch `CLICKHOUSE_HOST` in `.env` when changing network.
- **LLM:** same Mac Studio; same IPs for OLLAMA_*.

## Commands quick ref

- **SSH Mac Studio:** office `ssh thrivestudio@192.168.50.29`; outside `ssh thrivestudio@49.249.157.19`.
- **ClickHouse:** ensure listening on 0.0.0.0, port 9000; create `bizpulse`, user, `sales_analytics` table (see main doc).
- **Laptop .env:** office `CLICKHOUSE_HOST=192.168.50.29`; outside `CLICKHOUSE_HOST=49.249.157.19`; `CLICKHOUSE_PORT=9000`.
- **Full flow:** run RBAC/cache scripts → migrate `business_data` → `verify_complete_setup.py` → start backend → test `POST /api/ai/chatbot/chat`.

Do not delete this folder. See main doc for full steps and troubleshooting.
