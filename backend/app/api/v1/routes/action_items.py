"""
Action Items routes
Handles action items endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.action_items import ActionItemsResponse
from app.services.action_items_service import ActionItemsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/cockpit/action-items", response_model=ActionItemsResponse)
async def get_action_items(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get action items directly from MongoDB"""
    try:
        service = ActionItemsService(db)
        return await service.get_action_items()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Action items error: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Action items error: {str(e)}")

@router.post("/cockpit/action-items/seed")
async def seed_action_items(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Seed action items in MongoDB if collection is empty"""
    try:
        service = ActionItemsService(db)
        return await service.seed_action_items()
    except Exception as e:
        logger.error(f"❌ Error seeding action items: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error seeding action items: {str(e)}")

