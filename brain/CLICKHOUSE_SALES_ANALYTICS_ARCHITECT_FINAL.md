# ClickHouse sales_analytics — Architect-Level Final Design

This document captures the **agreed production schema and design decisions** from the Cursor + ChatGPT + product discussion. Use this as the single source of truth for implementation.

---

## 1. What Was Resolved

### 1.1 Inconsistencies That Were Fixed

- **Placeholder columns (metric_1, metric_2, metric_3)**  
  **Decision:** Remove. They create technical debt and confuse AI. Add real columns later with `ALTER TABLE sales_analytics ADD COLUMN <name> Decimal(15,2);`.

- **ORDER BY**  
  **Decision:** Date must come early (after tenant_id) because ~70% of queries are time-based ("last 30 days", "Q1", "YoY", monthly).  
  **Correct:** `ORDER BY (tenant_id, date, business, channel, brand, customer)`  
  **Wrong:** `ORDER BY (tenant_id, business, channel, brand, category, date)` (date last).

- **Audit columns**  
  **Decision:** Remove `updated_at`. In ClickHouse it is only set at INSERT time, not on UPDATE, so it is misleading. Keep only `created_at DateTime DEFAULT now()`.

- **customer column type**  
  **Decision:** `LowCardinality(String)`. Even with 20k–100k+ unique customers, values repeat across dates/brands/channels, so dictionary encoding is beneficial. Use plain `String` only if you have millions of rarely repeating values.

- **PARTITION BY**  
  **Decision:** `PARTITION BY (tenant_id, toYYYYMM(date))` for multi-tenant isolation and monthly partitions (sweet spot for daily data).

---

## 2. Workload and Scale (Product Context)

- **Queries:** ~70% time-based; rest are hierarchy, lifetime, top-N, comparisons.
- **Scale:** Crores of rows; 20k+ customers (possibly millions later); 30–40 columns when full data is available.
- **Users:** CEO, CFO, sales, finance, marketing, etc., with **RBAC** (filter by business, channel, brand, customer).
- **Backend rule:** If the user does **not** provide a time filter, default to last 24 months (or ask) to avoid accidental full scans.

---

## 3. Final Production Schema (Architect-Approved)

Column naming in the discussion used **semantic names** (gross_sales, final_gp, permanent_discount). The current codebase uses **short names** (gsales, fgp, perm_disc). Implementation can either:

- **Option 1:** Keep short names (gsales, fgp, perm_disc) in ClickHouse and update only **structure** (tenant_id, ORDER BY, MATERIALIZED, etc.) so existing migration and backend keep working.
- **Option 2:** Use semantic names (gross_sales, final_gp, permanent_discount) in the new schema and update migration + all backend/SQL references.

**FINAL IMPLEMENTED SCHEMA** (Option A - existing column names):

```sql
CREATE TABLE sales_analytics
(
    -- Multi-tenant
    tenant_id LowCardinality(String),

    -- Time (daily grain)
    date Date,
    year UInt16 MATERIALIZED toYear(date),
    month UInt8 MATERIALIZED toMonth(date),
    quarter UInt8 MATERIALIZED toQuarter(date),
    year_month UInt32 MATERIALIZED toYYYYMM(date),
    month_name LowCardinality(String) MATERIALIZED formatDateTime(date, '%B'),

    -- Business dimensions
    business LowCardinality(String),
    channel LowCardinality(String),
    customer LowCardinality(String),
    brand LowCardinality(String),
    category LowCardinality(String),
    sub_category LowCardinality(String),
    sku LowCardinality(String),

    -- Core metrics (existing names kept)
    cases Decimal(15,2),
    gsales Decimal(15,2),
    price_downs Decimal(15,2),
    perm_disc Decimal(15,2),
    transfer_cost Decimal(15,2),
    group_cost Decimal(15,2),
    lta Decimal(15,2),
    fgp Decimal(15,2),

    -- Audit
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(date))
ORDER BY (tenant_id, date, business, channel, brand, customer)
SETTINGS index_granularity = 8192;
```

**Status:** ✅ Implemented in `backend/scripts/create_schema.sql`

---

## 4. Why This ORDER BY

- **tenant_id first:** Multi-tenant isolation; always in WHERE.
- **date second:** Most queries filter by time → best pruning and scan efficiency.
- **business, channel, brand, customer:** Common filters and group-bys; order reflects typical question flow (business → channel → brand → customer).
- **customer last:** High cardinality; putting it earlier would hurt time-based and business-level queries.

---

## 5. Query Simulation (Validated)

Representative patterns that align with this design:

- Top 10 customers by revenue in last 30 days  
- Customer X performance over last 12 months  
- Q1 2023 vs Q1 2024 for Business Food  
- Monthly metrics for a full hierarchy slice (business → channel → customer → brand → category) for a given year  
- Which channel had most sales in 2024 for Business Food  
- Lifetime performance of Business Food (no date filter; acceptable for low frequency)  
- Full hierarchy growth/risk (group by business, channel, customer, brand, category, sub_category)  
- RBAC: all queries get `WHERE tenant_id = ? AND business IN (...) AND brand IN (...) ...`

---

## 6. RBAC

RBAC does **not** change table design. It only adds filters to the WHERE clause (tenant_id + allowed businesses, channels, brands, customers). The ORDER BY above supports these filters.

---

## 7. Final Implementation Decision (CONFIRMED)

**Decision Date:** Based on ChatGPT + Product Owner discussion

**Column Naming:** ✅ **Option A - Keep existing names**
- Keep `gsales`, `fgp`, `perm_disc` (already used throughout backend/migration/RBAC)
- No renaming needed - maintains backward compatibility

**Optional Columns:** ✅ **Keep sku and transfer_cost**
- Already in schema and migration
- Useful for SKU drilldowns and costing analysis
- Extra columns are cheap in ClickHouse

**Final Schema Implemented:**
- ✅ tenant_id LowCardinality(String) - Multi-tenant isolation
- ✅ date Date - Daily grain
- ✅ MATERIALIZED time columns (year, month, quarter, year_month, month_name)
- ✅ customer LowCardinality(String) - Even with 20k+ customers
- ✅ sku LowCardinality(String) - Kept
- ✅ All existing metric names (gsales, fgp, perm_disc, etc.)
- ✅ transfer_cost - Kept
- ✅ No updated_at - Removed
- ✅ PARTITION BY (tenant_id, toYYYYMM(date))
- ✅ ORDER BY (tenant_id, date, business, channel, brand, customer)
- ✅ No placeholder metrics
- ✅ No category in ORDER BY

## 8. Implementation Checklist

- [x] ✅ Create new `create_schema.sql` with: tenant_id, MATERIALIZED time columns, no updated_at, customer LowCardinality, correct PARTITION BY and ORDER BY.
- [x] ✅ Decision: Keep gsales/fgp/perm_disc and sku/transfer_cost (Option A).
- [x] ✅ Update migration script: include tenant_id (default `client_001` from env), match column order; MATERIALIZED columns not inserted.
- [ ] Backend: default time filter (e.g. last 24 months) when user does not specify a date range.
- [ ] RBAC: ensure all ClickHouse queries use tenant_id + role-based filters.
- [ ] (Optional) Materialized views for monthly/brand/customer rollups later.

---

## 9. References

- Cursor: Option A (clean schema, date early in ORDER BY, no placeholders).
- ChatGPT: Same final position; remove updated_at; customer as LowCardinality; ORDER BY (tenant_id, date, business, channel, brand, customer).
- Product: 70% time-based queries; 20k+ customers; crores of rows; RBAC; multi-tenant.
