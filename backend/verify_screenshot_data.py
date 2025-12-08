"""
Verify Screenshot Data Against MongoDB
Compare the values shown in the Customer Deep Intelligence screenshot with MongoDB data
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def verify_screenshot_data():
    """Verify the KPI values shown in the screenshot match MongoDB data"""
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulse')
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    logger.info("=" * 70)
    logger.info("Verifying Screenshot Data Against MongoDB")
    logger.info("=" * 70)
    
    # Screenshot values (from the image description)
    screenshot_values = {
        "totalCustomers": 5600,  # 5.6k
        "totalOrders": 16900,    # 16.9k
        "totalSales": 592600,    # €592,600
        "avgOrderValue": 35      # €35
    }
    
    logger.info("\n📊 SCREENSHOT VALUES:")
    logger.info(f"   Total Customers: {screenshot_values['totalCustomers']:,} (5.6k)")
    logger.info(f"   Total Orders: {screenshot_values['totalOrders']:,} (16.9k)")
    logger.info(f"   Total Sales: €{screenshot_values['totalSales']:,}")
    logger.info(f"   Avg Order Value: €{screenshot_values['avgOrderValue']}")
    
    # Query MongoDB (no filters - all data)
    summary_pipeline = [
        {'$match': {}},
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
    mongo_data = summary_result[0] if summary_result else {}
    
    logger.info("\n📊 MONGODB VALUES:")
    logger.info(f"   Total Customers: {int(mongo_data.get('totalCustomers', 0)):,}")
    logger.info(f"   Total Orders: {int(mongo_data.get('totalOrders', 0)):,}")
    logger.info(f"   Total Sales: €{float(mongo_data.get('totalSales', 0)):,.2f}")
    logger.info(f"   Avg Order Value: €{float(mongo_data.get('avgOrderValue', 0)):.2f}")
    
    # Compare values
    logger.info("\n" + "=" * 70)
    logger.info("COMPARISON RESULTS")
    logger.info("=" * 70)
    
    all_match = True
    
    # Total Customers
    mongo_customers = int(mongo_data.get('totalCustomers', 0))
    screenshot_customers = screenshot_values['totalCustomers']
    diff_customers = abs(mongo_customers - screenshot_customers)
    match_customers = diff_customers <= 100  # Allow 100 difference for rounding (5.6k = 5600, actual = 5631)
    status = "✅" if match_customers else "❌"
    logger.info(f"\n{status} Total Customers:")
    logger.info(f"   Screenshot: {screenshot_customers:,} (5.6k)")
    logger.info(f"   MongoDB:    {mongo_customers:,}")
    logger.info(f"   Difference: {diff_customers:,}")
    if not match_customers:
        all_match = False
    
    # Total Orders
    mongo_orders = int(mongo_data.get('totalOrders', 0))
    screenshot_orders = screenshot_values['totalOrders']
    diff_orders = abs(mongo_orders - screenshot_orders)
    match_orders = diff_orders <= 100  # Allow 100 difference for rounding (16.9k = 16900, actual = 16864)
    status = "✅" if match_orders else "❌"
    logger.info(f"\n{status} Total Orders:")
    logger.info(f"   Screenshot: {screenshot_orders:,} (16.9k)")
    logger.info(f"   MongoDB:    {mongo_orders:,}")
    logger.info(f"   Difference: {diff_orders:,}")
    if not match_orders:
        all_match = False
    
    # Total Sales
    mongo_sales = float(mongo_data.get('totalSales', 0))
    screenshot_sales = screenshot_values['totalSales']
    diff_sales = abs(mongo_sales - screenshot_sales)
    match_sales = diff_sales <= 1  # Allow €1 difference for rounding
    status = "✅" if match_sales else "❌"
    logger.info(f"\n{status} Total Sales:")
    logger.info(f"   Screenshot: €{screenshot_sales:,}")
    logger.info(f"   MongoDB:    €{mongo_sales:,.2f}")
    logger.info(f"   Difference: €{diff_sales:,.2f}")
    if not match_sales:
        all_match = False
    
    # Avg Order Value
    mongo_avg = float(mongo_data.get('avgOrderValue', 0))
    screenshot_avg = screenshot_values['avgOrderValue']
    diff_avg = abs(mongo_avg - screenshot_avg)
    match_avg = diff_avg <= 1  # Allow €1 difference for rounding
    status = "✅" if match_avg else "❌"
    logger.info(f"\n{status} Avg Order Value:")
    logger.info(f"   Screenshot: €{screenshot_avg}")
    logger.info(f"   MongoDB:    €{mongo_avg:.2f}")
    logger.info(f"   Difference: €{diff_avg:.2f}")
    if not match_avg:
        all_match = False
    
    # Additional verification - check New vs Returning
    mongo_new = int(mongo_data.get('newCustomers', 0))
    mongo_returning = int(mongo_data.get('returningCustomers', 0))
    logger.info(f"\n📊 Additional Data from MongoDB:")
    logger.info(f"   New Customers: {mongo_new:,}")
    logger.info(f"   Returning Customers: {mongo_returning:,}")
    
    logger.info("\n" + "=" * 70)
    if all_match:
        logger.info("✅ ALL VALUES MATCH (within rounding tolerance)")
        logger.info("   The screenshot values are consistent with MongoDB data!")
    else:
        logger.warning("⚠️  SOME VALUES DIFFER")
        logger.warning("   Please check the differences above")
    logger.info("=" * 70)
    
    # Check if frontend might be using CSV still
    logger.info("\n💡 NOTE:")
    logger.info("   If values don't match exactly, the frontend might still be")
    logger.info("   reading from CSV file instead of MongoDB.")
    logger.info("   The backend needs to be updated to query MongoDB instead.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(verify_screenshot_data())

