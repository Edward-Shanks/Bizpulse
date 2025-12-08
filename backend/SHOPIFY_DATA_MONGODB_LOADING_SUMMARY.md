# Shopify Customer Data - MongoDB Loading Summary

## Overview
Successfully loaded all Shopify customer data from `Shopify_customer_df_new2.csv` into MongoDB collection `shopify_data` in the `bizpulse` database.

## What Was Done

### 1. Data Loading Script
**File:** `backend/load_shopify_data_to_mongodb.py`

**Features:**
- Loads data from `Shopify_customer_df_new2.csv`
- Cleans and normalizes numeric columns
- Parses date columns (Year, Month, MonthName) from `Month_Column` field
- Handles NaN, None, and empty values
- Inserts data in batches of 1000 records
- Verifies data after loading

**Database Details:**
- **Database:** `bizpulse` (read from `.env` file)
- **Collection:** `shopify_data`
- **Total Records Loaded:** 17,104

### 2. Test Script
**File:** `backend/test_shopify_csv_vs_mongodb.py`

**Test Coverage:**
- Test 1: No filters (all data) ✅ PASS
- Test 2: Year filter (2025) ✅ PASS
- Test 3: Month filter (January) ✅ PASS
- Test 4: Year + Month filter (2025, November) ✅ PASS

**What It Tests:**
- Summary metrics (totalCustomers, totalOrders, totalSales, avgOrderValue, newCustomers, returningCustomers)
- Monthly trend data
- Total row counts
- Filter accuracy (Year, Month, Year+Month combinations)

## Test Results

### ✅ All Tests Passed

**Summary Metrics Match:**
- Total Customers: 5,631
- Total Orders: 16,864
- Total Sales: €592,599.71
- Average Order Value: €35.14
- New Customers: 6,226
- Returning Customers: 10,878

**Monthly Trend:**
- 11 months of data (January - November 2025)
- All monthly aggregations match between CSV and MongoDB

**Data Integrity:**
- All 17,104 records loaded successfully
- Year and Month fields parsed correctly
- All numeric values match between CSV and MongoDB

## Commands to Run

### Load Data to MongoDB
```bash
cd backend
python load_shopify_data_to_mongodb.py
```

### Run Tests (Compare CSV vs MongoDB)
```bash
cd backend
python test_shopify_csv_vs_mongodb.py
```

## Data Structure

### MongoDB Collection: `shopify_data`

**Key Fields:**
- `Year` (integer): Parsed from `Month_Column` (e.g., 2025)
- `Month` (integer): Parsed from `Month_Column` (e.g., 1-12)
- `MonthName` (string): Full month name (e.g., "January")
- `Customer email`: Customer email address
- `Total sales`: Total sales amount
- `Orders`: Number of orders
- `Orders (first-time)`: First-time orders
- `Orders (returning)`: Returning customer orders
- `New or returning customer`: Customer type
- Plus 25+ other fields from the original CSV

## Verification

All test cases confirm that:
1. ✅ Data loaded correctly into MongoDB
2. ✅ Summary calculations match CSV exactly
3. ✅ Monthly trend aggregations match CSV exactly
4. ✅ Filtering by Year works correctly
5. ✅ Filtering by Month works correctly
6. ✅ Filtering by Year + Month works correctly
7. ✅ Row counts match between CSV and MongoDB

## Next Steps

The data is now ready to be used in the Customer Deep Intelligence screen. The backend API can be updated to query from MongoDB instead of reading the CSV file, which will significantly improve performance.

## Files Created

1. `backend/load_shopify_data_to_mongodb.py` - Data loading script
2. `backend/test_shopify_csv_vs_mongodb.py` - Test comparison script
3. `backend/SHOPIFY_DATA_MONGODB_LOADING_SUMMARY.md` - This summary document

## Notes

- Database name is read from `.env` file (`DB_NAME`), not hardcoded
- All data is loaded into `bizpulse.shopify_data` collection
- Date parsing matches the logic used in `server.py` for consistency
- Numeric values are cleaned and normalized before insertion
- The script deletes existing data before loading new data (⚠️ be careful in production)

