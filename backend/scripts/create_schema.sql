-- ===================================================================
-- BIZPULSE ANALYTICS DATABASE - SCHEMA DEFINITION
-- ===================================================================
-- Architect-Approved Production Schema (Final Version)
-- Multi-tenant, time-optimized for 70% time-based queries
-- Target: Crores of rows, 20k+ customers, scalable to millions
-- Hardware: Mac Studio with 512GB RAM
-- ===================================================================

-- Step 1: Create Database
CREATE DATABASE IF NOT EXISTS bizpulse;
USE bizpulse;

-- Step 2: Create Main Analytics Table
CREATE TABLE IF NOT EXISTS bizpulse.sales_analytics
(
    -- ============= MULTI-TENANT ISOLATION =============
    tenant_id LowCardinality(String),           -- Multi-tenant identifier (e.g., 'client_001')
    
    -- ============= TIME DIMENSIONS (Daily Grain) =============
    date Date,                                  -- Date of transaction (daily level)
    
    -- Auto-generated time columns (MATERIALIZED - computed from date, not stored)
    year UInt16 MATERIALIZED toYear(date),      -- Year (2024, 2025, etc.)
    month UInt8 MATERIALIZED toMonth(date),     -- Month (1-12)
    quarter UInt8 MATERIALIZED toQuarter(date), -- Quarter (1-4)
    year_month UInt32 MATERIALIZED toYYYYMM(date), -- Year-month (202401, 202402, etc.)
    month_name LowCardinality(String),          -- "January", "February", etc. (calculated in Python during migration)
    
    -- ============= BUSINESS DIMENSIONS =============
    -- LowCardinality: ClickHouse internally stores as dictionary-encoded IDs
    -- Provides 80-90% compression vs regular String
    -- Perfect for columns with repeated values across dates/brands/channels
    business LowCardinality(String),            -- Food, Beauty, etc. (~5-10 unique)
    channel LowCardinality(String),             -- Convenience, Direct, etc. (~10-20 unique)
    customer LowCardinality(String),            -- Customer names (20k+ unique, but repeated across dates/brands)
    brand LowCardinality(String),               -- Brand names (~100-500 unique)
    category LowCardinality(String),            -- Category (~50-100 unique)
    sub_category LowCardinality(String),        -- Sub-category (~200-500 unique)
    sku LowCardinality(String),                -- SKU codes (repeated across dates/customers)
    
    -- ============= METRICS (FINANCIAL DATA) =============
    -- All monetary values use Decimal(15,2) for precision
    cases Decimal(15, 2),                       -- Units/Cases sold
    gsales Decimal(15, 2),                      -- Gross Sales (Revenue)
    price_downs Decimal(15, 2),                 -- Price reductions
    perm_disc Decimal(15, 2),                   -- Permanent discounts
    transfer_cost Decimal(15, 2),               -- Transfer costs
    group_cost Decimal(15, 2),                   -- Group costs
    lta Decimal(15, 2),                         -- LTA (Long Term Agreement)
    fgp Decimal(15, 2),                         -- Final Gross Profit
    
    -- ============= METADATA =============
    created_at DateTime DEFAULT now()           -- When record was created
    -- Note: No updated_at - ClickHouse doesn't auto-update rows
)
ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(date))        -- Multi-tenant + monthly partitions
ORDER BY (
    tenant_id,                                  -- Multi-tenant isolation (always filtered)
    date,                                        -- Time-first for 70% time-based queries
    business,                                   -- Business-level analysis
    channel,                                    -- Channel analysis
    brand,                                      -- Brand-level queries
    customer                                    -- Customer analysis (high cardinality, but common filter)
)
SETTINGS index_granularity = 8192;

-- ===================================================================
-- ARCHITECTURAL DECISIONS EXPLAINED:
-- ===================================================================
-- ENGINE = MergeTree()
--   Best engine for analytics workloads
--   Supports partitioning, primary keys, and high compression
--
-- PARTITION BY (tenant_id, toYYYYMM(date))
--   Multi-tenant isolation: each tenant's data in separate partitions
--   Monthly partitions: sweet spot for daily grain data
--   Queries with date filters only scan relevant partitions
--   Makes data management easier (drop old partitions, optimize separately)
--
-- ORDER BY (tenant_id, date, business, channel, brand, customer)
--   tenant_id first: Multi-tenant isolation, always in WHERE clause
--   date second: Optimized for 70% time-based queries ("last 30 days", "Q1", "YoY")
--   business/channel/brand/customer: Common filters and group-by columns
--   customer last: High cardinality, but putting it earlier would hurt time queries
--   Creates primary index for fast lookups
--
-- MATERIALIZED columns (year, month, quarter, year_month)
--   Computed automatically from date column
--   Not stored separately (saves space)
--   Can be queried directly: SELECT year, month FROM sales_analytics
--   No need to insert these values - ClickHouse calculates them
--
-- month_name column (NOT MATERIALIZED)
--   ClickHouse doesn't support %B format specifier in formatDateTime()
--   Calculated in Python during migration and inserted directly
--   Full month names: "January", "February", etc.
--
-- LowCardinality(String) for customer
--   Even with 20k+ unique customers, values repeat across dates/brands/channels
--   Dictionary encoding provides compression and faster filtering
--   Only use plain String if you have millions of rarely-repeating values
--
-- No updated_at column
--   ClickHouse doesn't auto-update rows like MySQL
--   Analytics tables are append-heavy, rarely updated
--   updated_at would be misleading (only set at INSERT time)
--
-- SETTINGS index_granularity = 8192
--   How many rows between index marks
--   8192 is default and optimal for most cases
--   Larger = less memory, slower queries
--   Smaller = more memory, faster queries
-- ===================================================================

-- Verify table created
SHOW CREATE TABLE bizpulse.sales_analytics;
DESCRIBE TABLE bizpulse.sales_analytics;

-- ===================================================================
-- EXPECTED PERFORMANCE (with optimized ORDER BY):
-- ===================================================================
-- Time-based queries (70% of workload):
--   Last 30 days:        < 100ms (even with crores of rows)
--   Q1 comparison:        < 200ms
--   Monthly YoY:          < 300ms
--
-- Full table aggregations:
--   1 lakh rows:         < 100ms
--   1 crore rows:        < 500ms
--   10 crore rows:       < 2 seconds
--   50 crore rows:       < 5 seconds
-- ===================================================================
