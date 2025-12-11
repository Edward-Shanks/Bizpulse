"""
Data service - Handles data synchronization from Azure Blob Storage
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.business_data_repository import BusinessDataRepository
from app.utils.azure_storage import load_data_from_azure_blob
import logging

logger = logging.getLogger(__name__)

class DataService:
    """Service for data operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.business_data_repo = BusinessDataRepository(db)
    
    async def sync_from_azure(self) -> dict:
        """Sync data from Azure Blob Storage"""
        try:
            records = await load_data_from_azure_blob()
            if records == 0:
                count = await self.business_data_repo.count_documents({})
                return {
                    "status": "success",
                    "message": "Azure load skipped/failed; collection unchanged",
                    "records_count": count
                }
            
            # Clean collection then insert
            await self.business_data_repo.delete_many({})
            
            # Insert in batches to avoid large payloads
            batch_size = 5000
            total = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                await self.business_data_repo.insert_many(batch)
                total += len(batch)
            
            logger.info(f"Loaded {total} records from Azure CSV into MongoDB")
            count = await self.business_data_repo.count_documents({})
            
            return {
                "status": "success",
                "message": "Loaded from Azure",
                "records_count": count
            }
        except Exception as e:
            logger.error(f"Error syncing from Azure: {str(e)}")
            raise
    
    async def verify_and_sync_data(self) -> None:
        """Verify data exists, sync from Azure if needed"""
        count = await self.business_data_repo.count_documents({})
        if count == 0:
            logger.info("No data in MongoDB. Attempting Azure CSV load...")
            result = await self.sync_from_azure()
            count = await self.business_data_repo.count_documents({})
            if result.get("records_count", 0) > 0:
                logger.info(f"Data loaded from Azure. Records now available: {count}")
            else:
                logger.warning("⚠️ Azure load skipped/failed. You can run /api/data/sync after fixing config")
        else:
            logger.info(f"MongoDB already has data: {count} records")

# Factory function
def get_data_service(db: AsyncIOMotorDatabase) -> DataService:
    """Get data service instance"""
    return DataService(db)

# Standalone function for startup
async def verify_and_sync_data(db: AsyncIOMotorDatabase) -> None:
    """Verify and sync data (standalone function for startup)"""
    service = DataService(db)
    await service.verify_and_sync_data()



