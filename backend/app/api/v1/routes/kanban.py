"""
Kanban routes
Handles kanban (campaigns and goals) endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Path
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.kanban import (
    StrategicRecommendationsResponse,
    GoalRequest, GoalResponse, GenerateGoalsRequest,
    AcceptCampaignRequest
)
from app.services.kanban_service import KanbanService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/kanban/annual-goal")
async def get_annual_goal(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get real annual goal metrics based on customer activation data"""
    try:
        service = KanbanService(db)
        return await service.get_annual_goal()
    except Exception as e:
        logger.error(f"Error calculating annual goal: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "current": 0,
            "target": 100,
            "metric": "% Activated Customers",
            "progress": 0
        }

@router.get("/kanban/recommendations", response_model=StrategicRecommendationsResponse)
async def get_kanban_recommendations(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Load kanban recommendations from MongoDB (does not generate new ones)"""
    try:
        service = KanbanService(db)
        return await service.get_recommendations()
    except Exception as e:
        logger.error(f"Error loading kanban recommendations: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error loading recommendations: {str(e)}")

@router.get("/analytics/strategic-recommendations", response_model=StrategicRecommendationsResponse)
async def generate_strategic_recommendations(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate NEW AI-powered strategic recommendations based on real business data"""
    try:
        service = KanbanService(db)
        return await service.generate_strategic_recommendations()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategic recommendations error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Strategic recommendations error: {str(e)}")

@router.post("/kanban/generate-goals", response_model=List[GoalResponse])
async def generate_goals_from_campaign(
    request: GenerateGoalsRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate AI-powered goals from a campaign"""
    try:
        service = KanbanService(db)
        return await service.generate_goals(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating goals: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating goals: {str(e)}")

@router.post("/kanban/goals", response_model=GoalResponse)
async def create_goal(
    request: GoalRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new goal linked to a campaign"""
    try:
        service = KanbanService(db)
        return await service.create_goal(request)
    except Exception as e:
        logger.error(f"Error creating goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating goal: {str(e)}")

@router.get("/kanban/campaigns/{campaignId}/goals", response_model=List[GoalResponse])
async def get_campaign_goals(
    campaignId: str = Path(..., description="Campaign ID"),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all goals for a specific campaign"""
    try:
        service = KanbanService(db)
        return await service.get_campaign_goals(campaignId)
    except Exception as e:
        logger.error(f"Error fetching campaign goals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")

@router.post("/kanban/accept")
async def accept_campaign(
    request: AcceptCampaignRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Move a campaign from recommended to live"""
    try:
        service = KanbanService(db)
        return await service.accept_campaign(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting campaign: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error accepting campaign: {str(e)}")

@router.post("/kanban/archive")
async def archive_campaign(
    request: AcceptCampaignRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Move a campaign from recommended or live to past (archived)"""
    try:
        service = KanbanService(db)
        return await service.archive_campaign(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving campaign: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error archiving campaign: {str(e)}")

@router.post("/kanban/move-to-live")
async def move_to_live(
    request: AcceptCampaignRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Move a campaign from past (archived) to live (active)"""
    try:
        service = KanbanService(db)
        return await service.move_to_live(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving campaign to live: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error moving campaign to live: {str(e)}")

