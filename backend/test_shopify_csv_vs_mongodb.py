"""
Test Script: Compare CSV vs MongoDB Data for Shopify Customer Insights
This script tests that data from CSV and MongoDB produce the same results
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ROOT_DIR = Path(__file__).parent

def clean_numeric_value(value):
    """Clean numeric values"""
    if pd.isna(value) or value is None or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return 0.0
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(',', '').replace('€', '').replace('$', '').replace('£', '').strip()
        if cleaned == '' or cleaned.lower() in ['nan', 'none', 'null', '-']:
            return 0.0
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    return 0.0

def process_csv_data(years=None, months=None):
    """Process data from CSV file (same logic as server.py)"""
    csv_path = ROOT_DIR / 'Shopify_customer_df_new2.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Clean numeric columns
    numeric_cols = ['Net sales', 'Gross sales', 'Total sales', 'Orders', 'Orders (first-time)', 
                   'Orders (returning)', 'Quantity ordered', 'Customer number of orders']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric_value)
    
    # Parse dates (simplified version)
    if 'Month' in df.columns:
        df['Month_Column'] = df['Month'].copy()
    
    if 'Month_Column' in df.columns:
        month_col = df['Month_Column'].astype(str)
        valid_mask = month_col.notna() & (month_col != 'nan') & month_col.str.contains('-', na=False)
        
        if valid_mask.any():
            split_parts = month_col[valid_mask].str.split('-', expand=True)
            if len(split_parts.columns) >= 2:
                try:
                    df.loc[valid_mask, 'Year'] = pd.to_numeric(split_parts[0], errors='coerce')
                    df.loc[valid_mask, 'Month'] = pd.to_numeric(split_parts[1], errors='coerce')
                    valid_dates = df.loc[valid_mask, ['Year', 'Month']].dropna()
                    if not valid_dates.empty:
                        date_series = pd.to_datetime(valid_dates.assign(Day=1), errors='coerce')
                        df.loc[valid_dates.index, 'MonthName'] = date_series.dt.strftime('%B')
                except Exception as e:
                    logger.warning(f"Error in date parsing: {str(e)}")
    
    # Apply filters
    if years:
        year_list = [int(y) for y in years.split(',') if y.strip()]
        if year_list:
            df = df[df['Year'].notna() & df['Year'].isin(year_list)]
    
    if months:
        month_list = [m.strip() for m in months.split(',') if m.strip()]
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9,
            'Oct': 10, 'Nov': 11, 'Dec': 12,
        }
        month_numbers = []
        for m in month_list:
            if m in month_map:
                month_numbers.append(month_map[m])
            else:
                m_lower = m.lower()
                for key, value in month_map.items():
                    if key.lower() == m_lower:
                        month_numbers.append(value)
                        break
        
        if month_numbers:
            df = df[df['Month'].notna() & df['Month'].isin(month_numbers)]
    
    # Calculate summary (same as server.py)
    summary = {
        "totalCustomers": int(df['Customer email'].nunique()) if 'Customer email' in df.columns else 0,
        "totalOrders": int(df['Orders'].sum()) if 'Orders' in df.columns else 0,
        "totalSales": float(df['Total sales'].sum()) if 'Total sales' in df.columns else 0,
        "avgOrderValue": float(df['Total sales'].sum() / df['Orders'].sum() if df['Orders'].sum() > 0 else 0) if 'Total sales' in df.columns and 'Orders' in df.columns else 0,
        "newCustomers": int((df['New or returning customer'] == 'New').sum()) if 'New or returning customer' in df.columns else 0,
        "returningCustomers": int((df['New or returning customer'] == 'Returning').sum()) if 'New or returning customer' in df.columns else 0
    }
    
    # Calculate monthly trend - apply same filters as summary
    df_valid_dates = df[(df['Year'].notna()) & (df['Month'].notna())]
    if not df_valid_dates.empty:
        monthly_trend = df_valid_dates.groupby(['Year', 'Month']).agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique',
            'Orders (first-time)': 'sum',
            'Orders (returning)': 'sum'
        }).reset_index()
        monthly_trend['MonthName'] = pd.to_datetime(monthly_trend[['Year', 'Month']].assign(Day=1)).dt.strftime('%B')
        monthly_trend = monthly_trend.sort_values(['Year', 'Month'])
        monthly_trend['month_label'] = monthly_trend['MonthName'] + ' ' + monthly_trend['Year'].astype(str)
        monthly_trend = monthly_trend.rename(columns={
            'Total sales': 'Total_sales',
            'Orders (first-time)': 'Orders_first_time',
            'Orders (returning)': 'Orders_returning',
            'Customer email': 'Customer_email'
        })
        # Apply month filter to monthly trend if specified (filter after aggregation)
        if months:
            month_list = [m.strip() for m in months.split(',') if m.strip()]
            month_map = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12,
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9,
                'Oct': 10, 'Nov': 11, 'Dec': 12,
            }
            month_numbers = []
            for m in month_list:
                if m in month_map:
                    month_numbers.append(month_map[m])
                else:
                    m_lower = m.lower()
                    for key, value in month_map.items():
                        if key.lower() == m_lower:
                            month_numbers.append(value)
                            break
            if month_numbers:
                monthly_trend = monthly_trend[monthly_trend['Month'].isin(month_numbers)]
        monthly_trend_list = monthly_trend.to_dict('records')
    else:
        monthly_trend_list = []
    
    return {
        "summary": summary,
        "monthlyTrend": monthly_trend_list,
        "totalRows": len(df)
    }

async def process_mongodb_data(years=None, months=None):
    """Process data from MongoDB (using aggregation pipelines)"""
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulse')
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Build match query
    match_query = {}
    
    if years:
        year_list = [int(y) for y in years.split(',') if y.strip()]
        if year_list:
            match_query['Year'] = {'$in': year_list}
    
    if months:
        month_list = [m.strip() for m in months.split(',') if m.strip()]
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9,
            'Oct': 10, 'Nov': 11, 'Dec': 12,
        }
        month_numbers = []
        for m in month_list:
            if m in month_map:
                month_numbers.append(month_map[m])
            else:
                m_lower = m.lower()
                for key, value in month_map.items():
                    if key.lower() == m_lower:
                        month_numbers.append(value)
                        break
        
        if month_numbers:
            match_query['Month'] = {'$in': month_numbers}
    
    # Summary aggregation - ensure we match valid records
    summary_match = match_query.copy() if match_query else {}
    
    summary_pipeline = [
        {'$match': summary_match},
        {'$group': {
            '_id': None,
            'totalCustomers': {'$addToSet': '$Customer email'},
            'totalOrders': {'$sum': {'$toDouble': '$Orders'}},
            'totalSales': {'$sum': {'$toDouble': '$Total sales'}},
            'newCustomers': {'$sum': {'$cond': [{'$eq': ['$New or returning customer', 'New']}, 1, 0]}},
            'returningCustomers': {'$sum': {'$cond': [{'$eq': ['$New or returning customer', 'Returning']}, 1, 0]}}
        }},
        {'$project': {
            'totalCustomers': {'$size': '$totalCustomers'},
            'totalOrders': 1,
            'totalSales': 1,
            'newCustomers': 1,
            'returningCustomers': 1,
            'avgOrderValue': {'$cond': [
                {'$gt': ['$totalOrders', 0]},
                {'$divide': ['$totalSales', '$totalOrders']},
                0
            ]}
        }}
    ]
    
    summary_result = await db.shopify_data.aggregate(summary_pipeline).to_list(1)
    summary = summary_result[0] if summary_result else {
        'totalCustomers': 0,
        'totalOrders': 0,
        'totalSales': 0,
        'avgOrderValue': 0,
        'newCustomers': 0,
        'returningCustomers': 0
    }
    
    # Monthly trend aggregation - only match records with valid Year and Month
    # Apply the same filters as summary, but ensure Year and Month are valid numbers
    monthly_match = match_query.copy() if match_query else {}
    monthly_match['Year'] = {'$ne': None, '$exists': True, '$type': 'number'}
    monthly_match['Month'] = {'$ne': None, '$exists': True, '$type': 'number'}
    
    monthly_pipeline = [
        {'$match': monthly_match},
        {'$group': {
            '_id': {'Year': '$Year', 'Month': '$Month'},
            'Total_sales': {'$sum': {'$toDouble': '$Total sales'}},
            'Orders': {'$sum': {'$toDouble': '$Orders'}},
            'Customer_email': {'$addToSet': '$Customer email'},
            'Orders_first_time': {'$sum': {'$toDouble': '$Orders (first-time)'}},
            'Orders_returning': {'$sum': {'$toDouble': '$Orders (returning)'}}
        }},
        {'$project': {
            'Year': '$_id.Year',
            'Month': '$_id.Month',
            'Total_sales': 1,
            'Orders': 1,
            'Customer_email': {'$size': '$Customer_email'},
            'Orders_first_time': 1,
            'Orders_returning': 1
        }},
        {'$sort': {'Year': 1, 'Month': 1}}
    ]
    
    monthly_results = await db.shopify_data.aggregate(monthly_pipeline).to_list(1000)
    
    # If month filter was applied, filter the results to only show matching months
    # (This matches CSV behavior where monthly trend only shows filtered months)
    if months:
        month_list = [m.strip() for m in months.split(',') if m.strip()]
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9,
            'Oct': 10, 'Nov': 11, 'Dec': 12,
        }
        month_numbers = []
        for m in month_list:
            if m in month_map:
                month_numbers.append(month_map[m])
            else:
                m_lower = m.lower()
                for key, value in month_map.items():
                    if key.lower() == m_lower:
                        month_numbers.append(value)
                        break
        if month_numbers:
            monthly_results = [r for r in monthly_results if r.get('Month') in month_numbers]
    
    # Format monthly trend
    monthly_trend_list = []
    for item in monthly_results:
        year = int(item.get('Year', 0))
        month = int(item.get('Month', 0))
        if year and month:
            month_name = pd.to_datetime(f"{year}-{month}-01").strftime('%B')
            monthly_trend_list.append({
                'Year': year,
                'Month': month,
                'MonthName': month_name,
                'month_label': f"{month_name} {year}",
                'Total_sales': float(item.get('Total_sales', 0)),
                'Orders': float(item.get('Orders', 0)),
                'Customer_email': int(item.get('Customer_email', 0)),
                'Orders_first_time': float(item.get('Orders_first_time', 0)),
                'Orders_returning': float(item.get('Orders_returning', 0))
            })
    
    # Count total rows
    total_rows = await db.shopify_data.count_documents(match_query if match_query else {})
    
    client.close()
    
    return {
        "summary": {
            "totalCustomers": int(summary.get('totalCustomers', 0)),
            "totalOrders": int(summary.get('totalOrders', 0)),
            "totalSales": float(summary.get('totalSales', 0)),
            "avgOrderValue": float(summary.get('avgOrderValue', 0)),
            "newCustomers": int(summary.get('newCustomers', 0)),
            "returningCustomers": int(summary.get('returningCustomers', 0))
        },
        "monthlyTrend": monthly_trend_list,
        "totalRows": total_rows
    }

def compare_results(csv_result, mongo_result, test_name=""):
    """Compare CSV and MongoDB results"""
    logger.info(f"\n{'='*70}")
    logger.info(f"📊 Test: {test_name}")
    logger.info(f"{'='*70}")
    
    # Compare summary
    csv_summary = csv_result.get('summary', {})
    mongo_summary = mongo_result.get('summary', {})
    
    logger.info("\n📈 SUMMARY COMPARISON:")
    all_match = True
    
    for key in ['totalCustomers', 'totalOrders', 'totalSales', 'avgOrderValue', 'newCustomers', 'returningCustomers']:
        csv_val = csv_summary.get(key, 0)
        mongo_val = mongo_summary.get(key, 0)
        match = abs(csv_val - mongo_val) < 0.01  # Allow small floating point differences
        status = "✅" if match else "❌"
        logger.info(f"   {status} {key}:")
        logger.info(f"      CSV:    {csv_val:,.2f}")
        logger.info(f"      MongoDB: {mongo_val:,.2f}")
        logger.info(f"      Diff:    {abs(csv_val - mongo_val):,.2f}")
        if not match:
            all_match = False
    
    # Compare monthly trend
    csv_trend = csv_result.get('monthlyTrend', [])
    mongo_trend = mongo_result.get('monthlyTrend', [])
    
    logger.info(f"\n📅 MONTHLY TREND COMPARISON:")
    logger.info(f"   CSV records:    {len(csv_trend)}")
    logger.info(f"   MongoDB records: {len(mongo_trend)}")
    
    if len(csv_trend) != len(mongo_trend):
        logger.warning(f"   ⚠️  Record count mismatch!")
        all_match = False
    else:
        logger.info(f"   ✅ Record count matches")
    
    # Compare each month
    csv_dict = {(r['Year'], r['Month']): r for r in csv_trend}
    mongo_dict = {(r['Year'], r['Month']): r for r in mongo_trend}
    
    trend_match = True
    for key in csv_dict.keys():
        if key not in mongo_dict:
            logger.warning(f"   ❌ Month {key[0]}-{key[1]:02d} missing in MongoDB")
            trend_match = False
            all_match = False
        else:
            csv_month = csv_dict[key]
            mongo_month = mongo_dict[key]
            for field in ['Total_sales', 'Orders', 'Customer_email']:
                csv_val = csv_month.get(field, 0)
                mongo_val = mongo_month.get(field, 0)
                if abs(csv_val - mongo_val) > 0.01:
                    logger.warning(f"   ❌ Month {key[0]}-{key[1]:02d} {field} mismatch:")
                    logger.warning(f"      CSV: {csv_val:,.2f}, MongoDB: {mongo_val:,.2f}")
                    trend_match = False
                    all_match = False
    
    if trend_match and len(csv_trend) == len(mongo_trend):
        logger.info(f"   ✅ All monthly trend data matches!")
    
    # Compare total rows
    csv_rows = csv_result.get('totalRows', 0)
    mongo_rows = mongo_result.get('totalRows', 0)
    logger.info(f"\n📊 TOTAL ROWS:")
    logger.info(f"   CSV:    {csv_rows:,}")
    logger.info(f"   MongoDB: {mongo_rows:,}")
    if csv_rows != mongo_rows:
        logger.warning(f"   ⚠️  Row count mismatch!")
        all_match = False
    else:
        logger.info(f"   ✅ Row count matches")
    
    logger.info(f"\n{'='*70}")
    if all_match:
        logger.info("✅ ALL TESTS PASSED - CSV and MongoDB results match!")
    else:
        logger.error("❌ TESTS FAILED - Differences found between CSV and MongoDB")
    logger.info(f"{'='*70}\n")
    
    return all_match

async def run_tests():
    """Run all comparison tests"""
    logger.info("\n" + "="*70)
    logger.info("🧪 Shopify Data: CSV vs MongoDB Comparison Tests")
    logger.info("="*70 + "\n")
    
    # Test 1: No filters
    logger.info("Test 1: No filters (all data)")
    try:
        csv_result = process_csv_data()
        mongo_result = await process_mongodb_data()
        test1_pass = compare_results(csv_result, mongo_result, "No Filters")
    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}")
        test1_pass = False
    
    # Test 2: Year filter
    logger.info("Test 2: Year filter (2025)")
    try:
        csv_result = process_csv_data(years="2025")
        mongo_result = await process_mongodb_data(years="2025")
        test2_pass = compare_results(csv_result, mongo_result, "Year Filter: 2025")
    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}")
        test2_pass = False
    
    # Test 3: Month filter
    logger.info("Test 3: Month filter (January)")
    try:
        csv_result = process_csv_data(months="January")
        mongo_result = await process_mongodb_data(months="January")
        test3_pass = compare_results(csv_result, mongo_result, "Month Filter: January")
    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}")
        test3_pass = False
    
    # Test 4: Year + Month filter
    logger.info("Test 4: Year + Month filter (2025, November)")
    try:
        csv_result = process_csv_data(years="2025", months="November")
        mongo_result = await process_mongodb_data(years="2025", months="November")
        test4_pass = compare_results(csv_result, mongo_result, "Year + Month Filter: 2025, November")
    except Exception as e:
        logger.error(f"❌ Test 4 failed: {e}")
        test4_pass = False
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*70)
    logger.info(f"Test 1 (No filters):        {'✅ PASS' if test1_pass else '❌ FAIL'}")
    logger.info(f"Test 2 (Year filter):       {'✅ PASS' if test2_pass else '❌ FAIL'}")
    logger.info(f"Test 3 (Month filter):      {'✅ PASS' if test3_pass else '❌ FAIL'}")
    logger.info(f"Test 4 (Year + Month):      {'✅ PASS' if test4_pass else '❌ FAIL'}")
    logger.info("="*70)
    
    all_pass = test1_pass and test2_pass and test3_pass and test4_pass
    if all_pass:
        logger.info("✅ ALL TESTS PASSED - CSV and MongoDB are in sync!")
    else:
        logger.error("❌ SOME TESTS FAILED - Please review differences above")
    logger.info("="*70 + "\n")
    
    return all_pass

if __name__ == "__main__":
    asyncio.run(run_tests())

