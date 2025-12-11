"""
Routes for Insights Chat
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.insights import InsightsChatRequest, InsightsChatResponse
from app.services.insights_service import InsightsService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/insights/chat", response_model=InsightsChatResponse)
async def insights_chat(
    request: InsightsChatRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    MongoDB-based View Insights Chatbot for all screens
    Supports: Business Compass, Brands, Customers, Categories, Sales Analysis
    """
    try:
        service = InsightsService(db)
        return await service.process_chat(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"View Insights Chat error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing view insights chat: {str(e)}")

