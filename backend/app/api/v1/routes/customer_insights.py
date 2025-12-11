"""
Routes for Customer Insights Chat
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.customer_insights import CustomerInsightsChatRequest, CustomerInsightsChatResponse
from app.services.customer_insights_service import CustomerInsightsService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/analytics/customer-insights/chat", response_model=CustomerInsightsChatResponse, name="customer_insights_chat")
async def customer_insights_chat(
    request: CustomerInsightsChatRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """AI Chat Assistant for Customer Deep Intelligence insights using Shopify customer data from MongoDB"""
    logger.info(f"🔵 Customer insights chat endpoint called")
    logger.info(f"🔵 Request received: {request.message[:100] if request.message else 'None'}")
    
    try:
        service = CustomerInsightsService(db)
        return await service.process_chat(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Customer insights chat error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing customer insights chat: {str(e)}")

