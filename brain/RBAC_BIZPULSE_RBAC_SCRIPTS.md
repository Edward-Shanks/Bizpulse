# RBAC and bizpulse_rbac Scripts

## Purpose

- **bizpulse**: Production MongoDB DB. Not modified by scripts (only read when used as source).
- **bizpulse_rbac**: Copy of bizpulse for testing RBAC and Add User. All testing read/write uses this DB.

## Scripts (backend/scripts/)

| Script | What it does |
|--------|----------------|
| `copy_bizpulse_to_bizpulse_rbac.py` | Copy all MongoDB collections from bizpulse → bizpulse_rbac (read-only from bizpulse) |
| `add_user_rbac_fields.py` | Add `role` and `access` to users in target DB. Use `--target-db bizpulse_rbac` or `bizpulse` |
| `run_setup_bizpulse_rbac.py` | One-shot: copy then add RBAC to bizpulse_rbac |
| `copy_bizpulse_mongo_to_clickhouse.py` | Copy bizpulse MongoDB to ClickHouse (business_data → sales_analytics; others → mongodb_sync) |
| `apply_rbac_to_main_db_bizpulse.py` | Apply RBAC to bizpulse.users (run when ready for production) |

## User access schema (in users collection)

- `role`: `"admin"` | `"user"`
- `access`: `{ businesses, channels, brands, categories, sub_categories, customers, allowed_metrics }`
  - Example: business "Food", brands ["Cali Cali","Bensons"], categories "all", channel "Grocery", allowed_metrics ["gsales","fgp"]
- Dynamic filters for Add User screen use same logic as other screens: `FilterService.get_filter_options()` (cascading by business, year, etc.).

## Commands

```bash
# Setup testing DB (copy + RBAC)
cd backend && python scripts/run_setup_bizpulse_rbac.py

# Then set .env: DB_NAME=bizpulse_rbac

# Later: apply RBAC to production users
python scripts/apply_rbac_to_main_db_bizpulse.py
```

Full details: `backend/scripts/README_BIZPULSE_RBAC_AND_SCRIPTS.md`
