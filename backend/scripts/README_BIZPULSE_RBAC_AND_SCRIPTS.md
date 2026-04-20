# Bizpulse RBAC and DB Copy Scripts

## Overview

- **bizpulse** = production MongoDB database. **Never modified** by these scripts (read-only when used as source).
- **bizpulse_rbac** = copy of bizpulse used for testing RBAC and Add User flows. All read/write for testing goes here.

## 1. Copy bizpulse → bizpulse_rbac (MongoDB)

**Script:** `copy_bizpulse_to_bizpulse_rbac.py`

- Reads **only** from `bizpulse`.
- Writes **only** to `bizpulse_rbac`.
- Copies **all** collections.

```bash
cd backend
python scripts/copy_bizpulse_to_bizpulse_rbac.py
```

## 2. Add RBAC fields to users (parameterized by target DB)

**Script:** `add_user_rbac_fields.py`

Adds to the **users** collection in the **target** database:

- `role`: `"admin"` or `"user"`
- `access`: object with:
  - `businesses`: e.g. `["Food"]` or `["*"]` for all
  - `channels`: e.g. `["Grocery"]` or `["*"]`
  - `brands`: e.g. `["Cali Cali", "Bensons"]` or `["*"]`
  - `categories`: `"all"` or list
  - `sub_categories`: `"all"` or list
  - `customers`: `"all"` or list
  - `allowed_metrics`: e.g. `["gsales", "fgp"]` or `["*"]` for all

**For testing (bizpulse_rbac):**

```bash
python scripts/add_user_rbac_fields.py --target-db bizpulse_rbac
```

**Dry run (no writes):**

```bash
python scripts/add_user_rbac_fields.py --target-db bizpulse_rbac --dry-run
```

**For production (bizpulse) – run when ready:**

```bash
python scripts/add_user_rbac_fields.py --target-db bizpulse
# Or use the wrapper:
python scripts/apply_rbac_to_main_db_bizpulse.py
```

## 3. One-shot setup for bizpulse_rbac

**Script:** `run_setup_bizpulse_rbac.py`

Runs in order:

1. Copy all collections from bizpulse → bizpulse_rbac
2. Add RBAC fields to users in bizpulse_rbac

```bash
cd backend
python scripts/run_setup_bizpulse_rbac.py
```

Then set in `.env`:

```env
DB_NAME=bizpulse_rbac
```

Use only bizpulse_rbac for read/write during testing.

## 4. Copy MongoDB bizpulse → ClickHouse

**Script:** `copy_bizpulse_mongo_to_clickhouse.py`

- **business_data** → ClickHouse `bizpulse.sales_analytics` (via existing migration script).
- **All other collections** → ClickHouse `bizpulse.mongodb_sync` (table with `collection`, `id`, `doc` JSON).

Reads only from MongoDB `bizpulse`. Does not modify MongoDB.

```bash
cd backend
# Ensure .env has CLICKHOUSE_* and MONGO_URL
python scripts/copy_bizpulse_mongo_to_clickhouse.py
```

## 5. Apply RBAC to main DB later

When you are ready to add the same RBAC fields to production users:

```bash
python scripts/apply_rbac_to_main_db_bizpulse.py
```

This runs `add_user_rbac_fields.py --target-db bizpulse` only. No copy, no other changes.

## Dynamic filters (Add User screen)

Existing app behaviour:

- **Filter options API:** `GET /api/filters/options` with query params `years`, `months`, `businesses`, `channels`, `brands`, `categories`, `customers`, `sub_categories`.
- **Logic:** Implemented in `FilterService.get_filter_options()` – options are **cascading** (e.g. selecting Business "Food" restricts years/brands/channels to those that exist for Food).
- **Data source:** Uses `db.business_data` (so with `DB_NAME=bizpulse_rbac` it uses bizpulse_rbac data).

For the **Add User** screen (admin only), use the same `/api/filters/options` (or equivalent) so that Business, Channel, Brand, Category, Customer, Sub-category (and if needed Years/Months) are dynamic and consistent with the rest of the app.

## Summary

| Script | Purpose | Touches bizpulse? |
|--------|---------|-------------------|
| `copy_bizpulse_to_bizpulse_rbac.py` | Copy all collections to bizpulse_rbac | Read-only |
| `add_user_rbac_fields.py --target-db bizpulse_rbac` | Add RBAC to users in bizpulse_rbac | No |
| `add_user_rbac_fields.py --target-db bizpulse` | Add RBAC to users in bizpulse | Yes (only users) |
| `run_setup_bizpulse_rbac.py` | Copy + RBAC for bizpulse_rbac | Read-only from bizpulse |
| `copy_bizpulse_mongo_to_clickhouse.py` | Sync bizpulse to ClickHouse | Read-only |
| `apply_rbac_to_main_db_bizpulse.py` | Apply RBAC to bizpulse users | Yes (only users) |
