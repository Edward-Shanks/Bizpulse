"""
Setup AI Cache Collection
Creates MongoDB ai_cache collection with required indexes for production performance
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_ai_cache_collection():
    """
    Create ai_cache collection with required indexes
    
    Indexes:
    1. Compound lookup index: (tenant_id, permissions_hash, intent_hash, data_version)
    2. TTL index: (expires_at) with expireAfterSeconds=0
    """
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGO_URL)
        db = client[settings.DB_NAME]
        collection = db.ai_cache
        
        logger.info(f"Connected to MongoDB: {settings.DB_NAME}")
        
        # Check if collection exists
        collections = await db.list_collection_names()
        if "ai_cache" in collections:
            logger.info("ai_cache collection already exists")
        else:
            logger.info("Creating ai_cache collection...")
            # Collection will be created automatically on first insert
        
        # Create compound lookup index
        logger.info("Creating compound lookup index...")
        await collection.create_index([
            ("tenant_id", 1),
            ("permissions_hash", 1),
            ("intent_hash", 1),
            ("data_version", 1)
        ], name="lookup_index")
        logger.info("✅ Created compound lookup index")
        
        # Create TTL index for automatic cleanup
        logger.info("Creating TTL index...")
        await collection.create_index(
            [("expires_at", 1)],  # Must be a list of tuples, not just a tuple
            expireAfterSeconds=0,
            name="ttl_index"
        )
        logger.info("✅ Created TTL index")
        
        # Verify indexes
        indexes = await collection.list_indexes().to_list(length=10)
        logger.info(f"✅ Collection indexes:")
        for idx in indexes:
            index_info = f"   - {idx.get('name')}: {idx.get('key')}"
            # Show TTL expiration setting if present
            if 'expireAfterSeconds' in idx:
                index_info += f" (TTL: {idx.get('expireAfterSeconds')}s)"
            logger.info(index_info)
        
        logger.info("✅ AI cache collection setup complete!")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        raise
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    asyncio.run(setup_ai_cache_collection())
