"""
Insights and AI chat related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

class AIConversation(BaseModel):
    """AI conversation model"""
    model_config = {"extra": "ignore"}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_message: str
    ai_response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AIChatRequest(BaseModel):
    """AI chat request model"""
    message: str
    session_id: Optional[str] = "default-session"

class AIChatResponse(BaseModel):
    """AI chat response model"""
    response: str
    session_id: str

class InsightsChatRequest(BaseModel):
    """View Insights Chatbot request model"""
    message: str = Field(..., description="User's question or message")
    chart_title: Optional[str] = Field(None, description="Title of the chart being viewed")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Filter context including selectedYears, selectedMonths, etc."
    )
    session_id: Optional[str] = Field(None, description="Session identifier")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Previous conversation messages for context"
    )

class InsightsChatResponse(BaseModel):
    """View Insights Chatbot response model"""
    response: str = Field(..., description="AI-generated response")
    timestamp: Optional[str] = Field(None, description="Response timestamp")
    context: Optional[str] = Field(None, description="Data context used for generating the response")
    data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional data including pivot_table, recommendations, etc."
    )

