"""
Service for Customer Insights Chat functionality
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.customer_insights import CustomerInsightsChatRequest, CustomerInsightsChatResponse
from datetime import datetime
import logging
import sys
import os

# Add backend directory to path to import customer_insights_fastapi
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

class CustomerInsightsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def process_chat(self, request: CustomerInsightsChatRequest) -> CustomerInsightsChatResponse:
        """Process customer insights chat request"""
        try:
            # Import the FastAPI functions from customer_insights_fastapi
            from customer_insights_fastapi import process_customer_insights_chat
            
            # Process the chat request using MongoDB (async)
            result = await process_customer_insights_chat(
                db=self.db,
                message=request.message or "",
                context=request.context or {},
                conversation_history=request.conversation_history or [],
                chart_title=request.chart_title
            )
            
            # Convert result to response model
            return CustomerInsightsChatResponse(
                response=result.get("response", "I apologize, but I couldn't process your request."),
                timestamp=result.get("timestamp", datetime.now().strftime("%I:%M %p IST on %B %d, %Y")),
                context=result.get("context", ""),
                data=result.get("data", {})
            )
        except FileNotFoundError:
            logger.error("MongoDB shopify_data collection not found")
            raise ValueError("MongoDB shopify_data collection not found")
        except ImportError as e:
            logger.error(f"Failed to import customer_insights_fastapi: {str(e)}")
            raise ValueError(f"Failed to load customer insights module: {str(e)}")
        except Exception as e:
            logger.error(f"Customer insights chat error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Error processing customer insights chat: {str(e)}")

