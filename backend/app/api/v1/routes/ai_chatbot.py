"""
AI Chatbot Routes
ClickHouse-based AI chatbot with RBAC, caching, and intent-based query generation
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.services.ai import AIService
from app.services.ai.ai_drill_service import AIDrillService
from app.core.config import settings
import logging
from typing import Dict, Any

try:
    from clickhouse_driver.errors import NetworkError as ClickHouseNetworkError
except ImportError:
    ClickHouseNetworkError = type("NeverMatch", (), {})  # sentinel so we only catch real driver errors

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ai/chatbot/chat")
async def ai_chatbot_chat(
    request: Dict[str, Any],
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    AI Chatbot endpoint with ClickHouse backend
    
    Complete flow:
    1. Extract intent from question (LLM)
    2. Load RBAC from MongoDB
    3. Check cache (permission-aware)
    4. Build SQL query (intent + RBAC)
    5. Execute on ClickHouse
    6. Generate explanation (LLM)
    7. Return response
    
    Request body:
    {
        "question": "Show revenue for Food business last 6 months"
    }
    
    Response:
    {
        "response": "Your Food business generated ₹4.58 crore...",
        "data": [...],  # Raw ClickHouse results
        "cached": false,
        "intent": {...}  # For debugging
    }
    """
    try:
        question = request.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Get tenant_id (from config or user)
        tenant_id = settings.TENANT_ID
        
        # Initialize AI service
        ai_service = AIService()
        
        # Process question
        result = await ai_service.process_question(
            question=question,
            user_email=email,
            tenant_id=tenant_id
        )
        
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClickHouseNetworkError as e:
        logger.warning("ClickHouse unreachable: %s", e)
        raise HTTPException(
            status_code=503,
            detail=(
                "Analytics data is temporarily unavailable. "
                "Please ensure ClickHouse is running at the configured host (e.g. start the server or wake the machine) and try again."
            ),
        )
    except Exception as e:
        err_msg = str(e).lower()
        if "connection" in err_msg and ("refused" in err_msg or "210" in str(e)):
            logger.warning("ClickHouse connection error: %s", e)
            raise HTTPException(
                status_code=503,
                detail=(
                    "Analytics data is temporarily unavailable. "
                    "Please ensure ClickHouse is running at the configured host and try again."
                ),
            )
        logger.error("AI chatbot error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing AI chatbot request: {str(e)}")


@router.post("/ai/chatbot/drill-down")
async def ai_chatbot_drill_down(
    request: Dict[str, Any],
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Dict[str, Any]:
    """
    "Why this number?" drill-down endpoint.

    Given a clicked pivot row (encoded as `filters`) and a `breakdown_by`
    dimension, returns the top-N contributors at that lower level with
    their share of the total. Identical RBAC rules as /ai/chatbot/chat.

    Request body:
    {
        "breakdown_by": "customer",
        "filters": {
            "brand": ["Brillo"],
            "year": [2024]
        },
        "measure": "gsales",   // optional, defaults to gsales (revenue)
        "limit": 10            // optional, max 50
    }

    Response:
    {
        "breakdown_by": "customer",
        "measure": "gsales",
        "filters_applied": {...},
        "total": 3950000.0,
        "rows": [
            {"Customer": "BWG", "Revenue": 2100000.0, "Gross_Profit": ..., "share_pct": 53.2},
            ...
        ],
        "denied": false,
        "message": null
    }
    """
    try:
        breakdown_by = request.get("breakdown_by")
        if not breakdown_by:
            raise HTTPException(status_code=400, detail="breakdown_by is required")
        filters = request.get("filters") or {}
        measure = request.get("measure")
        limit = request.get("limit")

        tenant_id = settings.TENANT_ID
        drill_service = AIDrillService()
        result = await drill_service.drill_down(
            breakdown_by=breakdown_by,
            filters=filters,
            measure=measure,
            limit=limit,
            user_email=email,
            tenant_id=tenant_id,
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClickHouseNetworkError as e:
        logger.warning("ClickHouse unreachable (drill-down): %s", e)
        raise HTTPException(
            status_code=503,
            detail=(
                "Analytics data is temporarily unavailable. "
                "Please ensure ClickHouse is running and try again."
            ),
        )
    except Exception as e:
        err_msg = str(e).lower()
        if "connection" in err_msg and ("refused" in err_msg or "210" in str(e)):
            logger.warning("ClickHouse connection error (drill-down): %s", e)
            raise HTTPException(
                status_code=503,
                detail=(
                    "Analytics data is temporarily unavailable. "
                    "Please ensure ClickHouse is running and try again."
                ),
            )
        logger.error("AI drill-down error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing drill-down request: {str(e)}")
