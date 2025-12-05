"""
Verify data in bizpulseDev database
This script checks the data loaded into the development database
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def verify_dev_database():
    """Verify data in bizpulseDev database"""
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulseDev')
    
    if not MONGO_URL:
        logger.error("❌ MONGO_URL not found in environment variables!")
        return
    
    logger.info(f"📊 Connecting to MongoDB database: {DB_NAME}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        await client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Check total records
    total_count = await db.business_data.count_documents({})
    logger.info(f"\n📊 Total Records: {total_count:,}")
    
    if total_count == 0:
        logger.warning("⚠️  Database is empty! Please run sync_azure_data_dev.py first.")
        return
    
    # Year distribution
    pipeline = [
        {
            '$group': {
                '_id': '$Year',
                'count': {'$sum': 1},
                'total_revenue': {'$sum': {'$toDouble': '$Revenue'}},
                'total_profit': {'$sum': {'$toDouble': '$Gross_Profit'}},
                'total_units': {'$sum': {'$toDouble': '$Units'}}
            }
        },
        {'$sort': {'_id': 1}}
    ]
    
    year_stats = await db.business_data.aggregate(pipeline).to_list(100)
    logger.info("\n📈 Year Distribution:")
    for stat in year_stats:
        year = stat.get('_id', 'Unknown')
        count = stat.get('count', 0)
        revenue = stat.get('total_revenue', 0)
        profit = stat.get('total_profit', 0)
        units = stat.get('total_units', 0)
        logger.info(f"   {year}: {count:,} records")
        logger.info(f"      Revenue: €{revenue:,.0f}, Profit: €{profit:,.0f}, Cases: {units:,.0f}")
    
    # Check 2025 data specifically
    count_2025 = await db.business_data.count_documents({'Year': 2025})
    logger.info(f"\n✅ 2025 Data: {count_2025:,} records")
    
    if count_2025 > 0:
        # Check months in 2025
        month_pipeline = [
            {'$match': {'Year': 2025}},
            {'$group': {'_id': '$Month_Name', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]
        month_stats = await db.business_data.aggregate(month_pipeline).to_list(100)
        months = [m['_id'] for m in month_stats if m.get('_id')]
        logger.info(f"   2025 Months: {months}")
        
        # Sample 2025 record
        sample_2025 = await db.business_data.find_one({'Year': 2025})
        if sample_2025:
            logger.info(f"\n📄 Sample 2025 Record:")
            logger.info(f"   Year: {sample_2025.get('Year')}")
            logger.info(f"   Month: {sample_2025.get('Month_Name')}")
            logger.info(f"   Business: {sample_2025.get('Business')}")
            logger.info(f"   Revenue: €{sample_2025.get('Revenue', 0):,.2f}")
            logger.info(f"   Cases: {sample_2025.get('Units', 0):,.0f}")
    
    # Check unique values
    businesses = await db.business_data.distinct('Business')
    channels = await db.business_data.distinct('Channel')
    brands = await db.business_data.distinct('Brand')
    categories = await db.business_data.distinct('Category')
    
    logger.info(f"\n📋 Unique Values:")
    logger.info(f"   Businesses: {len(businesses)}")
    logger.info(f"   Channels: {len(channels)}")
    logger.info(f"   Brands: {len(brands)}")
    logger.info(f"   Categories: {len(categories)}")
    
    # Check for 2025 months
    if count_2025 > 0:
        months_2025 = await db.business_data.distinct('Month_Name', {'Year': 2025})
        logger.info(f"   2025 Months: {sorted(months_2025)}")
    
    client.close()
    logger.info("\n✅ Verification completed!")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Verifying bizpulseDev Database")
    print("=" * 60)
    print()
    asyncio.run(verify_dev_database())

