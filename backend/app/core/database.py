"""
Database connection and setup
Handles MongoDB connection using Motor (async MongoDB driver)
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager"""
    
    client: AsyncIOMotorClient = None
    db = None

# Create global database instance
database = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        database.client = AsyncIOMotorClient(settings.MONGO_URL)
        database.db = database.client[settings.DB_NAME]
        # Test connection
        await database.client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {settings.DB_NAME}")
        return database
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        logger.info("MongoDB connection closed")

def get_database():
    """Get database instance (for dependency injection)"""
    if database.db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database.db

# For backward compatibility
def get_db():
    """Get database instance (alias for get_database)"""
    return get_database()

