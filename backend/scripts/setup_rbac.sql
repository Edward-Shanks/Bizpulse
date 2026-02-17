-- ===================================================================
-- BIZPULSE - RBAC (Role-Based Access Control) Setup
-- ===================================================================
-- This script creates users, roles, and views for database-level
-- access control in ClickHouse
-- ===================================================================

USE bizpulse;

-- ===================================================================
-- STEP 1: CREATE ADMIN USER
-- ===================================================================

-- Admin user has full access to everything
CREATE USER IF NOT EXISTS bizpulse_admin
    IDENTIFIED WITH plaintext_password BY 'Admin@123!Secure'
    SETTINGS readonly = 0;

-- Grant all privileges
GRANT ALL ON bizpulse.* TO bizpulse_admin;

-- Verify
SHOW GRANTS FOR bizpulse_admin;

-- ===================================================================
-- STEP 2: CREATE MANAGER USER
-- ===================================================================

-- Manager can see multiple businesses, revenue + profit
CREATE USER IF NOT EXISTS manager_user
    IDENTIFIED WITH plaintext_password BY 'Manager@123'
    SETTINGS readonly = 1;  -- Read-only

-- Grant select on main table
GRANT SELECT ON bizpulse.sales_analytics TO manager_user;

-- ===================================================================
-- STEP 3: CREATE SALES USER
-- ===================================================================

-- Sales user - restricted to specific business and columns
CREATE USER IF NOT EXISTS sales_user
    IDENTIFIED WITH plaintext_password BY 'Sales@123'
    SETTINGS readonly = 1;

-- Access granted via VIEW (see Step 6)

-- ===================================================================
-- STEP 4: CREATE FINANCE USER
-- ===================================================================

-- Finance user can see all financial data
CREATE USER IF NOT EXISTS finance_user
    IDENTIFIED WITH plaintext_password BY 'Finance@123'
    SETTINGS readonly = 1;

-- Grant full select access
GRANT SELECT ON bizpulse.sales_analytics TO finance_user;

-- ===================================================================
-- STEP 5: CREATE CHANNEL MANAGER USER
-- ===================================================================

-- Channel manager - restricted to specific channel
CREATE USER IF NOT EXISTS convenience_user
    IDENTIFIED WITH plaintext_password BY 'Conv@123'
    SETTINGS readonly = 1;

-- ===================================================================
-- STEP 6: CREATE RBAC VIEWS (DATABASE-LEVEL SECURITY)
-- ===================================================================

-- ============= VIEW 1: SALES - FOOD BUSINESS ONLY =============
-- Sales team can only see:
--   - Food business
--   - Revenue and units (NO profit, NO costs)
CREATE VIEW IF NOT EXISTS bizpulse.sales_food_view AS
SELECT
    date,
    year,
    month,
    month_name,
    quarter,
    business,
    channel,
    customer,
    brand,
    category,
    sub_category,
    gsales,          -- ✅ Can see revenue
    cases            -- ✅ Can see units
    -- ❌ No profit columns (fgp)
    -- ❌ No cost columns (group_cost, lta, transfer_cost)
FROM bizpulse.sales_analytics
WHERE business = 'Food';  -- ✅ Only Food business

-- Grant access to sales user
GRANT SELECT ON bizpulse.sales_food_view TO sales_user;

-- ============= VIEW 2: MANAGER - MULTI-BUSINESS =============
-- Manager can see:
--   - Food + Beauty businesses
--   - Revenue, units, and profit (NO costs)
CREATE VIEW IF NOT EXISTS bizpulse.manager_multi_business_view AS
SELECT
    date,
    year,
    month,
    month_name,
    quarter,
    business,
    channel,
    customer,
    brand,
    category,
    sub_category,
    gsales,          -- ✅ Revenue
    cases,           -- ✅ Units
    fgp              -- ✅ Profit
    -- ❌ No cost columns (group_cost, lta, transfer_cost)
FROM bizpulse.sales_analytics
WHERE business IN ('Food', 'Beauty');  -- ✅ Food and Beauty only

-- Grant access to manager
GRANT SELECT ON bizpulse.manager_multi_business_view TO manager_user;

-- ============= VIEW 3: CHANNEL - CONVENIENCE ONLY =============
-- Convenience channel manager can see:
--   - Only Convenience channel
--   - All businesses in that channel
--   - Revenue and profit
CREATE VIEW IF NOT EXISTS bizpulse.sales_convenience_view AS
SELECT
    date,
    year,
    month,
    month_name,
    quarter,
    business,
    channel,
    customer,
    brand,
    category,
    sub_category,
    gsales,
    cases,
    fgp
FROM bizpulse.sales_analytics
WHERE channel = 'Convenience';  -- ✅ Only Convenience channel

-- Grant access
GRANT SELECT ON bizpulse.sales_convenience_view TO convenience_user;

-- ============= VIEW 4: BRAND SPECIFIC =============
-- Brand manager - can only see specific brands
CREATE VIEW IF NOT EXISTS bizpulse.sales_heinz_view AS
SELECT
    date,
    year,
    month,
    month_name,
    quarter,
    business,
    channel,
    customer,
    brand,
    category,
    sub_category,
    gsales,
    cases,
    fgp
FROM bizpulse.sales_analytics
WHERE brand = 'Heinz';  -- ✅ Only Heinz brand

-- Create brand manager user
CREATE USER IF NOT EXISTS brand_heinz_user
    IDENTIFIED WITH plaintext_password BY 'Heinz@123'
    SETTINGS readonly = 1;

-- Grant access
GRANT SELECT ON bizpulse.sales_heinz_view TO brand_heinz_user;

-- ===================================================================
-- STEP 7: VERIFY RBAC SETUP
-- ===================================================================

-- List all users
SHOW USERS;

-- List all tables and views
SHOW TABLES FROM bizpulse;

-- Check grants for each user
SHOW GRANTS FOR bizpulse_admin;
SHOW GRANTS FOR manager_user;
SHOW GRANTS FOR sales_user;
SHOW GRANTS FOR finance_user;
SHOW GRANTS FOR convenience_user;
SHOW GRANTS FOR brand_heinz_user;

-- ===================================================================
-- STEP 8: TEST RBAC (RUN THESE SEPARATELY)
-- ===================================================================

-- Test 1: Sales user should only see Food business
-- Exit and reconnect:
-- docker exec -it clickhouse-prod clickhouse-client --user=sales_user --password=Sales@123 --database=bizpulse

-- Should work:
-- SELECT business, sum(gsales) FROM sales_food_view GROUP BY business;

-- Should FAIL:
-- SELECT * FROM sales_analytics LIMIT 1;
-- Error: "Not enough privileges"

-- ===================================================================
-- STEP 9: CREATE DYNAMIC VIEWS (TEMPLATE)
-- ===================================================================

-- Use this template to create views for your actual users
-- Replace BUSINESS_NAME and USER_NAME with actual values

/*
CREATE VIEW IF NOT EXISTS bizpulse.sales_{BUSINESS_NAME}_view AS
SELECT
    date,
    year,
    month,
    business,
    channel,
    customer,
    brand,
    gsales,
    cases,
    fgp
FROM bizpulse.sales_analytics
WHERE business = '{BUSINESS_NAME}';

CREATE USER IF NOT EXISTS {USER_NAME}
    IDENTIFIED WITH plaintext_password BY '{PASSWORD}'
    SETTINGS readonly = 1;

GRANT SELECT ON bizpulse.sales_{BUSINESS_NAME}_view TO {USER_NAME};
*/

-- ===================================================================
-- SECURITY NOTES:
-- ===================================================================
-- 1. Views enforce security at DATABASE level
--    Even if your application has bugs, users can't bypass these views
--
-- 2. Views are FAST - ClickHouse optimizes them like regular queries
--    No performance penalty
--
-- 3. Use WHERE clause in views for:
--    - Business filtering
--    - Channel filtering
--    - Brand filtering
--    - Customer filtering
--    - Date range filtering
--
-- 4. Use SELECT clause to hide sensitive columns:
--    - Hide profit from sales team
--    - Hide costs from non-finance users
--    - Hide customer details from external users
--
-- 5. Always use readonly=1 for non-admin users
--    This prevents INSERT, UPDATE, DELETE
--
-- 6. Change default passwords immediately!
--    Use strong passwords in production
--
-- 7. For production, consider:
--    - Using SHA256_password instead of plaintext_password
--    - Setting up SSL/TLS
--    - Using LDAP/AD integration
--    - Setting up audit logs
-- ===================================================================

-- ===================================================================
-- QUICK REFERENCE: USER PERMISSIONS
-- ===================================================================
-- bizpulse_admin      → Full access to everything
-- manager_user        → Food + Beauty, Revenue + Profit
-- sales_user          → Food only, Revenue only
-- finance_user        → All data, all columns
-- convenience_user    → Convenience channel only
-- brand_heinz_user    → Heinz brand only
-- ===================================================================
