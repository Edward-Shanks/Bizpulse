"""
Routes for Insights Chat
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.insights import InsightsChatRequest, InsightsChatResponse
from app.services.insights_service import InsightsService
from app.core.config import settings
from app.utils.llm_providers.ollama import get_ollama_endpoint, _initialize_ollama_endpoints
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test/load-balancer")
async def test_load_balancer():
    """
    Test endpoint to verify Ollama load balancing
    Returns which endpoint would be selected for the next request
    No authentication required for testing
    """
    try:
        # Initialize if not already done
        _initialize_ollama_endpoints()
        
        # Get next endpoint
        selected_endpoint = get_ollama_endpoint()
        
        # Get configuration info
        config_info = {
            "ollama_base_url": settings.OLLAMA_BASE_URL,
            "ollama_endpoints": settings.OLLAMA_ENDPOINTS,
            "num_endpoints": len(settings.OLLAMA_ENDPOINTS) if settings.OLLAMA_ENDPOINTS else 0,
            "selected_endpoint": selected_endpoint,
            "port": selected_endpoint.split(':')[-1] if ':' in selected_endpoint else 'unknown'
        }
        
        return {
            "status": "success",
            "message": "Load balancer test endpoint",
            "config": config_info,
            "note": "Call this endpoint multiple times to see round-robin distribution"
        }
    except Exception as e:
        logger.error(f"Load balancer test error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/insights/chat", response_model=InsightsChatResponse)
async def insights_chat(
    request: InsightsChatRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    MongoDB-based View Insights Chatbot for all screens
    Supports: Business Compass, Brands, Customers, Categories, Sales Analysis
    
    CRITICAL: This endpoint is fully async and should handle parallel requests.
    If responses are sequential, check Ollama server configuration for concurrent request handling.
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

@router.post("/insights/chat/stream")
async def insights_chat_stream(
    request: InsightsChatRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    think: bool = Query(False, description="Enable thinking mode for supported models")
):
    """
    Streaming version of insights chat
    Returns Server-Sent Events (SSE) stream
    """
    try:
        service = InsightsService(db)
        
        async def generate_stream():
            try:
                # Process chat and get streaming response
                async for chunk in service.process_chat_stream(request, think=think):
                    # Format as SSE and yield immediately (no buffering)
                    chunk_json = json.dumps(chunk)
                    # Yield immediately to ensure streaming
                    yield f"data: {chunk_json}\n\n"
                    # Force flush (though FastAPI should handle this)
                    import sys
                    if hasattr(sys.stdout, 'flush'):
                        sys.stdout.flush()
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                error_chunk = {
                    "type": "error",
                    "data": f"Error: {str(e)}"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
            finally:
                # Send done signal
                yield f"data: {json.dumps({'type': 'done', 'data': ''})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering in Nginx
                "Content-Type": "text/event-stream; charset=utf-8"
            }
        )
    except Exception as e:
        logger.error(f"View Insights Chat Stream error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing stream: {str(e)}")

