-- Copy-paste this entire block into ClickHouse client
-- Run from: docker exec -it clickhouse-prod clickhouse-client --database=bizpulse

CREATE TABLE IF NOT EXISTS bizpulse.sales_analytics
(
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
    cases Decimal(15, 2),
    gsales Decimal(15, 2),
    price_downs Decimal(15, 2),
    perm_disc Decimal(15, 2),
    transfer_cost Decimal(15, 2),
    group_cost Decimal(15, 2),
    lta Decimal(15, 2),
    fgp Decimal(15, 2),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(date))
ORDER BY (tenant_id, date, business, channel, brand, customer)
SETTINGS index_granularity = 8192;
