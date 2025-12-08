"""
Add MongoDB Indexes for Shopify Data
This script creates indexes on frequently queried fields to improve query performance
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

async def add_indexes():
    """Add indexes to shopify_data collection"""
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulse')
    
    logger.info("=" * 70)
    logger.info("Adding MongoDB Indexes for Shopify Data")
    logger.info("=" * 70)
    logger.info(f"Database: {DB_NAME}")
    logger.info(f"Collection: shopify_data")
    logger.info("=" * 70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db.shopify_data
    
    # Test connection
    try:
        await client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Check existing indexes
    logger.info("\n📋 Checking existing indexes...")
    existing_indexes = await collection.list_indexes().to_list(100)
    logger.info(f"   Found {len(existing_indexes)} existing indexes")
    for idx in existing_indexes:
        logger.info(f"   - {idx.get('name', 'unnamed')}: {idx.get('key', {})}")
    
    # Indexes to create
    indexes_to_create = [
        {
            "name": "Year index",
            "keys": [("Year", 1)],
            "description": "Index on Year field for filtering by year"
        },
        {
            "name": "Month index",
            "keys": [("Month", 1)],
            "description": "Index on Month field for filtering by month"
        },
        {
            "name": "Year_Month compound index",
            "keys": [("Year", 1), ("Month", 1)],
            "description": "Compound index for Year + Month filters"
        },
        {
            "name": "Customer email index",
            "keys": [("Customer email", 1)],
            "description": "Index on Customer email for unique customer counting"
        },
        {
            "name": "Year_Month_Customer compound index",
            "keys": [("Year", 1), ("Month", 1), ("Customer email", 1)],
            "description": "Compound index for efficient aggregations"
        }
    ]
    
    logger.info("\n🔨 Creating indexes...")
    created_count = 0
    skipped_count = 0
    
    for idx_config in indexes_to_create:
        idx_name = idx_config["name"]
        idx_keys = idx_config["keys"]
        
        # Check if index already exists
        index_exists = False
        for existing_idx in existing_indexes:
            existing_keys = list(existing_idx.get('key', {}).items())
            if existing_keys == idx_keys:
                index_exists = True
                break
        
        if index_exists:
            logger.info(f"   ⏭️  Skipping {idx_name} (already exists)")
            skipped_count += 1
        else:
            try:
                # Convert list of tuples to dict for create_index
                keys_dict = {key: direction for key, direction in idx_keys}
                result = await collection.create_index(list(keys_dict.items()), name=idx_name)
                logger.info(f"   ✅ Created {idx_name}")
                created_count += 1
            except Exception as e:
                logger.error(f"   ❌ Failed to create {idx_name}: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"📊 Index Creation Summary")
    logger.info("=" * 70)
    logger.info(f"   Created: {created_count} new indexes")
    logger.info(f"   Skipped: {skipped_count} existing indexes")
    logger.info(f"   Total: {len(indexes_to_create)} indexes")
    logger.info("=" * 70)
    
    # Show final index list
    logger.info("\n📋 Final index list:")
    final_indexes = await collection.list_indexes().to_list(100)
    for idx in final_indexes:
        idx_name = idx.get('name', 'unnamed')
        idx_keys = idx.get('key', {})
        idx_size = idx.get('size', 0)
        logger.info(f"   - {idx_name}: {idx_keys} (size: {idx_size} bytes)")
    
    # Get collection stats
    stats = await db.command("collStats", "shopify_data")
    logger.info("\n📊 Collection Statistics:")
    logger.info(f"   Total documents: {stats.get('count', 0):,}")
    logger.info(f"   Total size: {stats.get('size', 0):,} bytes ({stats.get('size', 0) / 1024 / 1024:.2f} MB)")
    logger.info(f"   Index size: {stats.get('totalIndexSize', 0):,} bytes ({stats.get('totalIndexSize', 0) / 1024 / 1024:.2f} MB)")
    
    client.close()
    logger.info("\n✅ Index creation complete!")

if __name__ == "__main__":
    asyncio.run(add_indexes())

