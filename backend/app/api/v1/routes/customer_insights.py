"""
Routes for Customer Insights Chat
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.customer_insights import CustomerInsightsChatRequest, CustomerInsightsChatResponse
from app.services.customer_insights_service import CustomerInsightsService
from mongodb_customer_insights import get_customer_insights_mongodb
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/analytics/customer-insights/filters")
async def get_customer_insights_filters(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get filter options for customer insights based on actual Shopify data from MongoDB.
    
    Returns only years and months that exist in the Shopify data, ensuring filters are accurate.
    """
    try:
        logger.info("📊 Fetching customer insights filter options from MongoDB")
        
        # Get distinct years from shopify_data collection
        years_pipeline = [
            {"$match": {"Year": {"$exists": True, "$ne": None, "$type": "number"}}},
            {"$group": {"_id": "$Year"}},
            {"$sort": {"_id": 1}}
        ]
        years_result = await db.shopify_data.aggregate(years_pipeline).to_list(100)
        years = sorted([int(item['_id']) for item in years_result if item.get('_id') is not None])
        
        # Get distinct months - try Month (number) first, then convert to names
        months_pipeline = [
            {"$match": {"Month": {"$exists": True, "$ne": None, "$type": "number"}}},
            {"$group": {"_id": "$Month"}},
            {"$sort": {"_id": 1}}
        ]
        months_result = await db.shopify_data.aggregate(months_pipeline).to_list(12)
        
        # Convert month numbers to names
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        months = []
        for item in months_result:
            month_num = item.get('_id')
            if month_num and month_num in month_names:
                months.append(month_names[month_num])
        
        # If no months found, try Month_Name field as fallback
        if not months:
            months_pipeline_name = [
                {"$match": {"Month_Name": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$Month_Name"}},
                {"$sort": {"_id": 1}}
            ]
            months_result_name = await db.shopify_data.aggregate(months_pipeline_name).to_list(12)
            months = [item['_id'] for item in months_result_name if item.get('_id')]
            
            # Sort months properly
            month_order = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            months = sorted(months, key=lambda x: month_order.get(x, 999))
        
        logger.info(f"✅ Customer insights filters - Years: {years}, Months: {len(months)}")
        
        return {
            "years": years,
            "months": months
        }
    except Exception as e:
        logger.error(f"Error getting customer insights filters: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error getting filter options: {str(e)}")

@router.get("/analytics/customer-insights")
async def get_customer_insights(
    years: str = Query(None, description="Comma-separated list of years (e.g., '2023,2024')"),
    months: str = Query(None, description="Comma-separated list of months (e.g., 'January,February')"),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get comprehensive customer insights data with optional year and month filters.
    
    Uses MongoDB with caching for optimal performance.
    Returns aggregated customer data including:
    - New vs Returning customers
    - Channel performance
    - Geographic distribution
    - Traffic sources
    - Customer lifetime value
    - Monthly trends
    - And more...
    """
    try:
        logger.info(f"📊 Fetching customer insights from MongoDB (years: {years}, months: {months})")
        result = await get_customer_insights_mongodb(
            db=db,
            years=years,
            months=months,
            use_cache=True
        )
        return result
    except Exception as e:
        logger.error(f"Error processing customer insights: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing customer insights: {str(e)}")

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

@router.post("/analytics/customer-insights/view-insights/chat", response_model=CustomerInsightsChatResponse, name="customer_view_insights_chat")
async def customer_view_insights_chat(
    request: CustomerInsightsChatRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Enhanced AI Chat Assistant for Customer Deep Intelligence view insights modal using MongoDB.
    
    Processes user questions about Shopify customer data and returns AI-generated insights with data context.
    This endpoint is specifically for the "View Insight" modal on Customer Deep Intelligence charts.
    """
    logger.info(f"🔵 Customer view insights chat endpoint called by {email}")
    logger.info(f"🔵 Request message: {request.message[:100] if request.message else 'None'}")
    
    try:
        # Import the FastAPI function
        from customer_insights_fastapi import process_customer_insights_chat
        
        # Process the chat request using MongoDB (async)
        result = await process_customer_insights_chat(
            db=db,
            message=request.message or "",
            context=request.context or {},
            conversation_history=request.conversation_history or [],
            chart_title=request.chart_title
        )
        
        # Convert result to response model
        from datetime import datetime
        return CustomerInsightsChatResponse(
            response=result.get("response", "I apologize, but I couldn't process your request."),
            timestamp=result.get("timestamp", datetime.now().strftime("%I:%M %p IST on %B %d, %Y")),
            context=result.get("context", ""),
            data=result.get("data", {})
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail="Shopify data collection not found")
    except ImportError as e:
        logger.error(f"Failed to import customer_insights_fastapi: {str(e)}")
        import traceback
        logger.error(f"Import traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to load customer insights FastAPI module: {str(e)}")
    except Exception as e:
        logger.error(f"Customer view insights chat error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing customer view insights chat: {str(e)}")

