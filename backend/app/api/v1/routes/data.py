"""
Data management routes
Handles data sync and data source endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.analytics import SyncStatusResponse
from app.services.data_service import DataService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/data/sync", response_model=SyncStatusResponse)
async def trigger_sync(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Trigger data sync from Azure Blob Storage"""
    try:
        data_service = DataService(db)
        result = await data_service.sync_from_azure()
        return SyncStatusResponse(**result)
    except Exception as e:
        logger.error(f"Error syncing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/source")
async def get_data_source(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Returns metadata about the current data source and sample records"""
    try:
        from app.repositories.business_data_repository import BusinessDataRepository
        import math
        
        repo = BusinessDataRepository(db)
        count = await repo.count_documents({})
        
        if count == 0:
            return {
                "source": "none",
                "message": "No data in MongoDB",
                "records_count": 0,
                "sample_records": []
            }
        
        # Get a sample record to show data structure
        sample = await db.business_data.find_one({}, {"_id": 0})
        
        # Convert NaN/Inf values to None for JSON serialization
        if sample:
            sample = {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v) 
                     for k, v in sample.items()}
        
        # Get database name from config (db.name might not work)
        from app.core.config import settings
        
        return {
            "source": "MongoDB",
            "database": settings.DB_NAME,
            "collection": "business_data",
            "record_count": count,
            "sample_records": [sample] if sample else []
        }
    except Exception as e:
        logger.error(f"Error getting data source: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



