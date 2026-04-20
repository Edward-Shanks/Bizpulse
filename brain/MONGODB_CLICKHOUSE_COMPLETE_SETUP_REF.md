# MongoDB + ClickHouse Complete Setup — Reference

## Source document
**Location:** `backend/MONGODB_CLICKHOUSE_SETUP_UNDERSTANDING_AND_ARCHITECTURE.md`

That document is the single source of understanding and architecture for the “complete setup” of MongoDB and ClickHouse, derived from the ChatGPT discussion in `backend/discussion_file.md` and aligned with the actual Bizpulse codebase (FastAPI/Python).

## Summary
- **bizpulse** (MongoDB): read-only; never write after migration.
- **bizpulse_rbac** (MongoDB): all app read/write; users + RBAC (access, allowed_metrics).
- **ClickHouse**: analytics only (e.g. sales_analytics); no user storage.
- **Default time:** 24 months when time not specified; full history only when user asks “lifetime”.
- **RBAC:** Application-level only (MongoDB); backend injects tenant + filters into ClickHouse queries.
- **AI:** LLM returns intent; backend builds SQL (no raw LLM SQL).

Implementation plan and runbook are in the main doc. Do not delete this brain reference.
