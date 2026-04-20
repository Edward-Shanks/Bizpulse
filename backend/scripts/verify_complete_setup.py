"""
Verify Complete Setup
Checks MongoDB, ClickHouse, RBAC, and AI cache setup
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.database.clickhouse_client import ClickHouseClient
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_mongodb():
    """Verify MongoDB connection and RBAC setup"""
    try:
        client = AsyncIOMotorClient(settings.MONGO_URL)
        db = client[settings.DB_NAME]
        
        # Test connection
        await client.admin.command('ping')
        logger.info(f"✅ MongoDB: Connected to {settings.DB_NAME}")
        
        # Check users have RBAC fields
        users_collection = db.users
        total_users = await users_collection.count_documents({})
        users_with_role = await users_collection.count_documents({"role": {"$exists": True}})
        users_with_access = await users_collection.count_documents({"access": {"$exists": True}})
        
        logger.info(f"✅ RBAC: {users_with_role}/{total_users} users have 'role' field")
        logger.info(f"✅ RBAC: {users_with_access}/{total_users} users have 'access' field")
        
        if users_with_role == 0 or users_with_access == 0:
            logger.warning("⚠️  RBAC fields missing - run: add_user_rbac_fields.py --target-db bizpulse_rbac")
            return False
        
        # Check AI cache collection
        collections = await db.list_collection_names()
        if "ai_cache" in collections:
            cache_collection = db.ai_cache
            indexes = await cache_collection.list_indexes().to_list(length=10)
            index_names = [idx.get("name") for idx in indexes]
            
            if "lookup_index" in index_names and "ttl_index" in index_names:
                logger.info("✅ AI Cache: Collection exists with required indexes")
            else:
                logger.warning("⚠️  AI Cache: Collection exists but indexes missing - run: setup_ai_cache_collection.py")
                return False
        else:
            logger.warning("⚠️  AI Cache: Collection missing - run: setup_ai_cache_collection.py")
            return False
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ MongoDB verification failed: {e}")
        return False


def verify_clickhouse():
    """Verify ClickHouse connection and table"""
    try:
        client = ClickHouseClient()
        
        # Test query
        result = client.execute(
            "SELECT count() FROM bizpulse.sales_analytics LIMIT 1",
            tenant_id=settings.TENANT_ID,
            enforce_time_filter=False
        )
        
        logger.info(f"✅ ClickHouse: Connected to {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}")
        logger.info(f"✅ ClickHouse: sales_analytics table exists")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ClickHouse verification failed: {e}")
        return False


def verify_config():
    """Verify configuration"""
    try:
        logger.info(f"✅ Config: DB_NAME = {settings.DB_NAME}")
        logger.info(f"✅ Config: DEFAULT_TIME_MONTHS = {settings.DEFAULT_TIME_MONTHS}")
        logger.info(f"✅ Config: TENANT_ID = {settings.TENANT_ID}")
        logger.info(f"✅ Config: CLICKHOUSE_DB = {settings.CLICKHOUSE_DB}")
        return True
    except Exception as e:
        logger.error(f"❌ Config verification failed: {e}")
        return False


async def main():
    """Run all verification checks"""
    logger.info("=" * 60)
    logger.info("Verifying Complete Setup...")
    logger.info("=" * 60)
    
    results = []
    
    # Verify config
    results.append(("Config", verify_config()))
    
    # Verify MongoDB
    results.append(("MongoDB", await verify_mongodb()))
    
    # Verify ClickHouse
    results.append(("ClickHouse", verify_clickhouse()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("Verification Summary:")
    logger.info("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("✅ Setup complete! All checks passed.")
    else:
        logger.info("⚠️  Some checks failed. Please review the errors above.")
    logger.info("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
