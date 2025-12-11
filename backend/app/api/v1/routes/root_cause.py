"""
Root Cause Analysis routes
Handles root cause analysis endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.root_cause import RootCauseAnalysisResponse
from app.services.root_cause_service import RootCauseService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/root-cause-analysis/issues", response_model=RootCauseAnalysisResponse, name="get_root_cause_issues")
async def get_root_cause_issues(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Load root cause analysis issues from MongoDB"""
    logger.info(f"🔍🔍🔍 GET /root-cause-analysis/issues called by {email}")
    try:
        service = RootCauseService(db)
        return await service.get_issues()
    except Exception as e:
        logger.error(f"Error loading root cause issues: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error loading root cause issues: {str(e)}")

@router.post("/root-cause-analysis/generate", response_model=RootCauseAnalysisResponse, name="generate_root_cause_issues")
async def generate_root_cause_issues(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate NEW AI-powered root cause analysis issues based on real business data"""
    logger.info(f"🔍🔍🔍 POST /root-cause-analysis/generate called by {email}")
    try:
        service = RootCauseService(db)
        return await service.generate_issues()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Root cause analysis error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Root cause analysis error: {str(e)}")

