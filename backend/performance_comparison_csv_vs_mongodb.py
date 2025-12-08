"""
Performance Comparison: CSV vs MongoDB
This script measures the time taken to load and process data from both CSV and MongoDB
to determine which is faster for the Customer Deep Intelligence screen.
"""
import asyncio
import os
import time
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import logging

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
    """Process data from CSV file (simulating current server.py logic)"""
    start_time = time.time()
    timings = {}
    
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
    logger.info(f"   ⏱️  Clean Numeric: {timings['clean_numeric']:.3f}s")
    
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
    logger.info(f"   ⏱️  Parse Dates: {timings['parse_dates']:.3f}s")
    
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
    logger.info(f"   ⏱️  Apply Filters: {timings['apply_filters']:.3f}s")
    
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
    logger.info(f"   ⏱️  Calculate Summary: {timings['calculate_summary']:.3f}s")
    
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
        # Apply month filter to monthly trend if specified
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
    logger.info(f"   ⏱️  Calculate Monthly Trend: {timings['calculate_monthly_trend']:.3f}s")
    
    total_time = time.time() - start_time
    timings['total'] = total_time
    
    return {
        "summary": summary,
        "monthlyTrend": monthly_trend_list,
        "totalRows": len(df),
        "timings": timings
    }

async def process_mongodb_data(years=None, months=None):
    """Process data from MongoDB (using aggregation pipelines)"""
    start_time = time.time()
    timings = {}
    
    # Step 1: Connect to MongoDB
    step_start = time.time()
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulse')
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    timings['connect'] = time.time() - step_start
    logger.info(f"   ⏱️  MongoDB Connect: {timings['connect']:.3f}s")
    
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
    logger.info(f"   ⏱️  Build Query: {timings['build_query']:.3f}s")
    
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
    logger.info(f"   ⏱️  Summary Aggregation: {timings['summary_aggregation']:.3f}s")
    
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
    
    # If month filter was applied, filter the results
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
    timings['monthly_trend_aggregation'] = time.time() - step_start
    logger.info(f"   ⏱️  Monthly Trend Aggregation: {timings['monthly_trend_aggregation']:.3f}s")
    
    # Step 5: Count total rows
    step_start = time.time()
    total_rows = await db.shopify_data.count_documents(match_query if match_query else {})
    timings['count_rows'] = time.time() - step_start
    logger.info(f"   ⏱️  Count Rows: {timings['count_rows']:.3f}s")
    
    total_time = time.time() - start_time
    timings['total'] = total_time
    
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
        "totalRows": total_rows,
        "timings": timings
    }

async def run_performance_comparison():
    """Run performance comparison tests"""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 Performance Comparison: CSV vs MongoDB")
    logger.info("=" * 70 + "\n")
    
    test_cases = [
        {"name": "No Filters (All Data)", "years": None, "months": None},
        {"name": "Year Filter (2025)", "years": "2025", "months": None},
        {"name": "Month Filter (January)", "years": None, "months": "January"},
        {"name": "Year + Month Filter (2025, November)", "years": "2025", "months": "November"},
    ]
    
    results = []
    
    for test_case in test_cases:
        logger.info("\n" + "=" * 70)
        logger.info(f"📊 Test Case: {test_case['name']}")
        logger.info("=" * 70)
        
        # Test CSV
        logger.info("\n📄 Processing from CSV...")
        try:
            csv_start = time.time()
            csv_result = process_csv_data(years=test_case['years'], months=test_case['months'])
            csv_total = time.time() - csv_start
            logger.info(f"✅ CSV Total Time: {csv_total:.3f}s")
        except Exception as e:
            logger.error(f"❌ CSV Error: {e}")
            csv_result = None
            csv_total = float('inf')
        
        # Test MongoDB
        logger.info("\n💾 Processing from MongoDB...")
        try:
            mongo_start = time.time()
            mongo_result = await process_mongodb_data(years=test_case['years'], months=test_case['months'])
            mongo_total = time.time() - mongo_start
            logger.info(f"✅ MongoDB Total Time: {mongo_total:.3f}s")
        except Exception as e:
            logger.error(f"❌ MongoDB Error: {e}")
            mongo_result = None
            mongo_total = float('inf')
        
        # Compare
        if csv_result and mongo_result:
            speedup = csv_total / mongo_total if mongo_total > 0 else 0
            faster = "MongoDB" if mongo_total < csv_total else "CSV"
            improvement = abs(csv_total - mongo_total)
            improvement_pct = (improvement / csv_total * 100) if csv_total > 0 else 0
            
            logger.info("\n" + "=" * 70)
            logger.info("⏱️  PERFORMANCE COMPARISON")
            logger.info("=" * 70)
            logger.info(f"   CSV Time:     {csv_total:.3f}s")
            logger.info(f"   MongoDB Time: {mongo_total:.3f}s")
            logger.info(f"   Difference:   {improvement:.3f}s ({improvement_pct:.1f}%)")
            logger.info(f"   Faster:       {faster}")
            if speedup > 1:
                logger.info(f"   Speedup:      {speedup:.2f}x faster")
            logger.info("=" * 70)
            
            results.append({
                "test": test_case['name'],
                "csv_time": csv_total,
                "mongo_time": mongo_total,
                "faster": faster,
                "speedup": speedup,
                "improvement_pct": improvement_pct,
                "csv_timings": csv_result.get('timings', {}),
                "mongo_timings": mongo_result.get('timings', {})
            })
        else:
            logger.error("❌ One or both methods failed - cannot compare")
    
    # Final Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 FINAL PERFORMANCE SUMMARY")
    logger.info("=" * 70)
    
    for result in results:
        logger.info(f"\n{result['test']}:")
        logger.info(f"   CSV:     {result['csv_time']:.3f}s")
        logger.info(f"   MongoDB: {result['mongo_time']:.3f}s")
        logger.info(f"   Winner:  {result['faster']} ({result['improvement_pct']:.1f}% faster)")
        if result['speedup'] > 1:
            logger.info(f"   Speedup:  {result['speedup']:.2f}x")
    
    # Overall winner
    avg_csv = sum(r['csv_time'] for r in results) / len(results)
    avg_mongo = sum(r['mongo_time'] for r in results) / len(results)
    overall_winner = "MongoDB" if avg_mongo < avg_csv else "CSV"
    overall_speedup = avg_csv / avg_mongo if avg_mongo > 0 else 1
    
    logger.info("\n" + "=" * 70)
    logger.info("🏆 OVERALL WINNER")
    logger.info("=" * 70)
    logger.info(f"   Average CSV Time:     {avg_csv:.3f}s")
    logger.info(f"   Average MongoDB Time: {avg_mongo:.3f}s")
    logger.info(f"   Overall Winner:       {overall_winner}")
    logger.info(f"   Average Speedup:      {overall_speedup:.2f}x")
    logger.info("=" * 70)
    
    if overall_winner == "MongoDB":
        logger.info("\n✅ RECOMMENDATION: MongoDB is faster - Ready to implement!")
    else:
        logger.info("\n⚠️  RECOMMENDATION: CSV is faster - Consider keeping CSV or optimizing MongoDB queries")
    
    logger.info("=" * 70 + "\n")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_performance_comparison())

