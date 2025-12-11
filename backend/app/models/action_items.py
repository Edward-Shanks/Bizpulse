"""
Action Items related Pydantic models
"""
from pydantic import BaseModel
from typing import List, Optional

class ActionItem(BaseModel):
    """Action item model"""
    id: int
    title: str
    dueDate: str
    priority: str  # high, medium, low
    category: str  # critical, impact
    status: str = "pending"  # pending, in_progress, completed
    assignedTo: Optional[str] = None
    description: Optional[str] = None

class ActionItemsResponse(BaseModel):
    """Response model for action items"""
    critical: List[ActionItem]
    impact: List[ActionItem]

