"""
AI Chatbot Routes
ClickHouse-based AI chatbot with RBAC, caching, and intent-based query generation
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.services.ai import AIService
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
