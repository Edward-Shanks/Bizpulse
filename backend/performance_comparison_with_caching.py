"""
Performance Comparison: CSV vs MongoDB (With Caching)
This script compares CSV and MongoDB performance, including caching for both
"""
import asyncio
import os
import time
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import logging
from functools import lru_cache
import hashlib
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ROOT_DIR = Path(__file__).parent

# Cache storage
_csv_cache = {}
_mongodb_cache = {}

def get_cache_key(years=None, months=None):
    """Generate cache key from filter parameters"""
    key_parts = []
    if years:
        key_parts.append(f"year:{years}")
    if months:
        key_parts.append(f"month:{months}")
    return ":".join(key_parts) if key_parts else "all"

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

def process_csv_data(years=None, months=None, use_cache=True):
    """Process data from CSV file with caching"""
    start_time = time.time()
    timings = {}
    cache_key = f"csv:{get_cache_key(years, months)}"
    
    # Check cache
    if use_cache and cache_key in _csv_cache:
        logger.info(f"   💾 Using CSV cache (key: {cache_key})")
        cached_result = _csv_cache[cache_key]
        timings['cache_hit'] = True
        timings['total'] = time.time() - start_time
        return {**cached_result, 'timings': timings}
    
    timings['cache_hit'] = False
    
    # Step 1: Load CSV
    step_start = time.time()
    csv_path = ROOT_DIR / 'Shopify_customer_df_new2.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    timings['load_csv'] = time.time() - step_start
    logger.info(f"   ⏱️  CSV Load: {timings['load_csv']:.3f}s")
    
    # Step 2: Clean numeric columns
    step_start = time.time()
    numeric_cols = ['Net sales', 'Gross sales', 'Total sales', 'Orders', 'Orders (first-time)', 
                   'Orders (returning)', 'Quantity ordered', 'Customer number of orders']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric_value)
    timings['clean_numeric'] = time.time() - step_start
    
    # Step 3: Parse dates
    step_start = time.time()
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
    timings['parse_dates'] = time.time() - step_start
    
    # Step 4: Apply filters
    step_start = time.time()
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
    timings['apply_filters'] = time.time() - step_start
    
    # Step 5: Calculate summary
    step_start = time.time()
    summary = {
        "totalCustomers": int(df['Customer email'].nunique()) if 'Customer email' in df.columns else 0,
        "totalOrders": int(df['Orders'].sum()) if 'Orders' in df.columns else 0,
        "totalSales": float(df['Total sales'].sum()) if 'Total sales' in df.columns else 0,
        "avgOrderValue": float(df['Total sales'].sum() / df['Orders'].sum() if df['Orders'].sum() > 0 else 0) if 'Total sales' in df.columns and 'Orders' in df.columns else 0,
        "newCustomers": int((df['New or returning customer'] == 'New').sum()) if 'New or returning customer' in df.columns else 0,
        "returningCustomers": int((df['New or returning customer'] == 'Returning').sum()) if 'New or returning customer' in df.columns else 0
    }
    timings['calculate_summary'] = time.time() - step_start
    
    # Step 6: Calculate monthly trend
    step_start = time.time()
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
    timings['calculate_monthly_trend'] = time.time() - step_start
    
    total_time = time.time() - start_time
    timings['total'] = total_time
    
    result = {
        "summary": summary,
        "monthlyTrend": monthly_trend_list,
        "totalRows": len(df),
        "timings": timings
    }
    
    # Cache the result
    if use_cache:
        _csv_cache[cache_key] = result
        logger.info(f"   💾 Cached CSV result (key: {cache_key})")
    
    return result

async def process_mongodb_data(years=None, months=None, use_cache=True):
    """Process data from MongoDB with caching"""
    start_time = time.time()
    timings = {}
    cache_key = f"mongo:{get_cache_key(years, months)}"
    
    # Check cache
    if use_cache and cache_key in _mongodb_cache:
        logger.info(f"   💾 Using MongoDB cache (key: {cache_key})")
        cached_result = _mongodb_cache[cache_key]
        timings['cache_hit'] = True
        timings['total'] = time.time() - start_time
        return {**cached_result, 'timings': timings}
    
    timings['cache_hit'] = False
    
    # Step 1: Connect to MongoDB
    step_start = time.time()
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulse')
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    timings['connect'] = time.time() - step_start
    
    # Step 2: Build match query
    step_start = time.time()
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
    timings['build_query'] = time.time() - step_start
    
    # Step 3: Summary aggregation
    step_start = time.time()
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
    timings['summary_aggregation'] = time.time() - step_start
    
    # Step 4: Monthly trend aggregation
    step_start = time.time()
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
    timings['monthly_trend_aggregation'] = time.time() - step_start
    
    # Step 5: Count total rows
    step_start = time.time()
    total_rows = await db.shopify_data.count_documents(match_query if match_query else {})
    timings['count_rows'] = time.time() - step_start
    
    total_time = time.time() - start_time
    timings['total'] = total_time
    
    result = {
        "summary": {
            "totalCustomers": int(summary.get('totalCustomers', 0)),
            "totalOrders": int(summary.get('totalOrders', 0)),
            "totalSales": float(summary.get('totalSales', 0)),
            "avgOrderValue": float(summary.get('avgOrderValue', 0)),
            "newCustomers": int(summary.get('newCustomers', 0)),
            "returningCustomers": int(summary.get('returningCustomers', 0))
        },
        "monthlyTrend": monthly_trend_list,
        "totalRows": total_rows,
        "timings": timings
    }
    
    # Cache the result
    if use_cache:
        _mongodb_cache[cache_key] = result
        logger.info(f"   💾 Cached MongoDB result (key: {cache_key})")
    
    client.close()
    
    return result

async def run_performance_comparison_with_caching():
    """Run performance comparison with caching"""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 Performance Comparison: CSV vs MongoDB (With Caching)")
    logger.info("=" * 70 + "\n")
    
    test_cases = [
        {"name": "No Filters (All Data)", "years": None, "months": None},
        {"name": "Year Filter (2025)", "years": "2025", "months": None},
        {"name": "Month Filter (January)", "years": None, "months": "January"},
        {"name": "Year + Month Filter (2025, November)", "years": "2025", "months": "November"},
    ]
    
    results_first = []  # First request (no cache)
    results_cached = []  # Cached requests
    
    # Clear caches
    _csv_cache.clear()
    _mongodb_cache.clear()
    
    # First run (no cache)
    logger.info("=" * 70)
    logger.info("📊 FIRST REQUEST (No Cache - Cold Start)")
    logger.info("=" * 70)
    
    for test_case in test_cases:
        logger.info(f"\n📊 Test: {test_case['name']} (First Request)")
        
        # Test CSV
        logger.info("\n📄 CSV (First Request):")
        csv_result = process_csv_data(years=test_case['years'], months=test_case['months'], use_cache=True)
        csv_total = csv_result['timings']['total']
        logger.info(f"   Total Time: {csv_total:.3f}s")
        
        # Test MongoDB
        logger.info("\n💾 MongoDB (First Request):")
        mongo_result = await process_mongodb_data(years=test_case['years'], months=test_case['months'], use_cache=True)
        mongo_total = mongo_result['timings']['total']
        logger.info(f"   Total Time: {mongo_total:.3f}s")
        
        results_first.append({
            "test": test_case['name'],
            "csv_time": csv_total,
            "mongo_time": mongo_total
        })
    
    # Second run (with cache)
    logger.info("\n" + "=" * 70)
    logger.info("📊 CACHED REQUESTS (Warm Cache)")
    logger.info("=" * 70)
    
    for test_case in test_cases:
        logger.info(f"\n📊 Test: {test_case['name']} (Cached)")
        
        # Test CSV
        logger.info("\n📄 CSV (Cached):")
        csv_result = process_csv_data(years=test_case['years'], months=test_case['months'], use_cache=True)
        csv_total = csv_result['timings']['total']
        cache_hit = csv_result['timings'].get('cache_hit', False)
        logger.info(f"   Total Time: {csv_total:.3f}s {'(CACHED)' if cache_hit else ''}")
        
        # Test MongoDB
        logger.info("\n💾 MongoDB (Cached):")
        mongo_result = await process_mongodb_data(years=test_case['years'], months=test_case['months'], use_cache=True)
        mongo_total = mongo_result['timings']['total']
        cache_hit = mongo_result['timings'].get('cache_hit', False)
        logger.info(f"   Total Time: {mongo_total:.3f}s {'(CACHED)' if cache_hit else ''}")
        
        results_cached.append({
            "test": test_case['name'],
            "csv_time": csv_total,
            "mongo_time": mongo_total
        })
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 PERFORMANCE SUMMARY")
    logger.info("=" * 70)
    
    logger.info("\n🔵 FIRST REQUEST (No Cache):")
    for r in results_first:
        logger.info(f"   {r['test']}:")
        logger.info(f"      CSV: {r['csv_time']:.3f}s | MongoDB: {r['mongo_time']:.3f}s")
    
    logger.info("\n🟢 CACHED REQUEST:")
    for r in results_cached:
        speedup_csv = results_first[results_cached.index(r)]['csv_time'] / r['csv_time'] if r['csv_time'] > 0 else 0
        speedup_mongo = results_first[results_cached.index(r)]['mongo_time'] / r['mongo_time'] if r['mongo_time'] > 0 else 0
        logger.info(f"   {r['test']}:")
        logger.info(f"      CSV: {r['csv_time']:.3f}s ({speedup_csv:.1f}x faster) | MongoDB: {r['mongo_time']:.3f}s ({speedup_mongo:.1f}x faster)")
    
    # Overall comparison
    avg_csv_first = sum(r['csv_time'] for r in results_first) / len(results_first)
    avg_mongo_first = sum(r['mongo_time'] for r in results_first) / len(results_first)
    avg_csv_cached = sum(r['csv_time'] for r in results_cached) / len(results_cached)
    avg_mongo_cached = sum(r['mongo_time'] for r in results_cached) / len(results_cached)
    
    logger.info("\n" + "=" * 70)
    logger.info("🏆 OVERALL WINNER")
    logger.info("=" * 70)
    logger.info(f"\nFirst Request (No Cache):")
    logger.info(f"   CSV Average:     {avg_csv_first:.3f}s")
    logger.info(f"   MongoDB Average: {avg_mongo_first:.3f}s")
    logger.info(f"   Winner: {'CSV' if avg_csv_first < avg_mongo_first else 'MongoDB'}")
    
    logger.info(f"\nCached Request:")
    logger.info(f"   CSV Average:     {avg_csv_cached:.3f}s")
    logger.info(f"   MongoDB Average: {avg_mongo_cached:.3f}s")
    logger.info(f"   Winner: {'CSV' if avg_csv_cached < avg_mongo_cached else 'MongoDB'}")
    
    csv_speedup = avg_csv_first / avg_csv_cached if avg_csv_cached > 0 else 0
    mongo_speedup = avg_mongo_first / avg_mongo_cached if avg_mongo_cached > 0 else 0
    
    logger.info(f"\nCache Speedup:")
    logger.info(f"   CSV:     {csv_speedup:.1f}x faster with cache")
    logger.info(f"   MongoDB: {mongo_speedup:.1f}x faster with cache")
    
    if avg_mongo_cached < avg_csv_cached:
        logger.info("\n✅ RECOMMENDATION: MongoDB with caching is faster - Ready to implement!")
    else:
        logger.info("\n✅ RECOMMENDATION: Both are fast with caching - MongoDB recommended for scalability")
    
    logger.info("=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(run_performance_comparison_with_caching())

