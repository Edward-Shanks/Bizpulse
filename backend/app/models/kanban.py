"""
Kanban and Goals related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class StrategicRecommendation(BaseModel):
    """Strategic recommendation/campaign model"""
    id: Optional[int] = None
    title: str
    description: str
    type: str = "system"
    category: str
    startDate: str
    endDate: Optional[str] = None
    budget: float
    impact: Dict[str, Any]
    reasoning: str
    channels: List[str]
    aiScore: int
    acceptedAt: Optional[str] = None  # When it was accepted to live
    status: Optional[str] = "recommended"  # recommended, live, past

class StrategicRecommendationsResponse(BaseModel):
    """Response model for strategic recommendations"""
    recommended: List[StrategicRecommendation]
    live: List[StrategicRecommendation]
    past: List[StrategicRecommendation] = []

class AcceptCampaignRequest(BaseModel):
    """Request model for accepting a campaign"""
    campaignId: int
    fromCollection: str  # "recommended"

class GoalRequest(BaseModel):
    """Request model for creating a goal"""
    campaignId: str
    title: str
    description: str
    department: str
    owners: List[str]  # List of user IDs
    teamMembers: Optional[List[str]] = []
    dependencies: Optional[List[str]] = []
    metrics: Optional[List[str]] = []
    keyResults: Optional[List[Dict]] = []
    status: str = "on-track"
    progress: int = 0

class GenerateGoalsRequest(BaseModel):
    """Request model for generating goals"""
    campaignId: str
    autoAssign: bool = False  # If True, AI assigns departments and owners

class GoalResponse(BaseModel):
    """Response model for a goal"""
    id: str
    campaignId: str
    title: str
    description: str
    department: str
    owners: List[str]
    teamMembers: List[str]
    dependencies: List[str]
    metrics: List[str]
    keyResults: List[Dict]
    status: str
    progress: int

class UpdateGoalRequest(BaseModel):
    """Request model for updating a goal"""
    progress: Optional[int] = None
    status: Optional[str] = None
    keyResults: Optional[List[Dict]] = None
    tasks: Optional[List[Dict]] = None  # New field for user tasks

