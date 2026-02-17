# Commands: Laptop + Mac Studio (ClickHouse & migration)

**Reference:** See project root **`COMMANDS_LAPTOP_AND_MAC_STUDIO.md`** for full step-by-step commands.

## Summary

- **Connection error (8123):** App was using HTTP port 8123; `clickhouse-driver` needs **native TCP port 9000**. Set `CLICKHOUSE_PORT=9000` in `backend\.env`.
- **Dashboard data:** MongoDB collection **`business_data`** (DB: `bizpulse`). Loaded by `sync_azure_data.py` (Azure CSV) or `load_cleaned_data.py` (local CSV).
- **Push to ClickHouse:** Run **`backend/scripts/migrate_real_data_to_clickhouse.py`** from laptop. It reads MongoDB `business_data` and writes to ClickHouse `sales_analytics`. No need to re-push from CSV.
- **Mac Studio (SSH):** Start/check ClickHouse with `docker ps | grep clickhouse`, `docker start clickhouse-prod`; create container if missing (see main doc). Port **9000** must be exposed.
- **Laptop:** Set `.env` → run schema if needed → run `migrate_real_data_to_clickhouse.py` → run test scripts.
