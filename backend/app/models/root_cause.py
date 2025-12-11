"""
Root Cause Analysis related Pydantic models
"""
from pydantic import BaseModel
from typing import List, Dict, Optional

class RootCauseIssue(BaseModel):
    """Root cause issue model"""
    id: int
    title: str
    severity: str  # high, medium, low
    rootCause: str
    impact: str
    recommendation: str
    status: str  # investigating, resolved, monitoring
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class RootCauseAnalysisResponse(BaseModel):
    """Response model for root cause analysis"""
    issues: List[RootCauseIssue]
    summary: Dict[str, int]  # critical, investigating, resolved counts



