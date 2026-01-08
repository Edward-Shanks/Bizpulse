"""
User Questions models for storing and retrieving user questions
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class UserQuestion(BaseModel):
    """User question model for database"""
    model_config = {"extra": "ignore"}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str = Field(..., description="Email of the user who asked the question")
    question: str = Field(..., description="The question text")
    chatbot_type: str = Field(..., description="Type of chatbot: 'view_insights' or 'vector_deep_ai'")
    chart_title: Optional[str] = Field(None, description="Chart title if applicable")
    context: Optional[dict] = Field(default_factory=dict, description="Filter context when question was asked")
    response: Optional[str] = Field(None, description="AI response to the question")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    usage_count: int = Field(default=0, description="Number of times this question was reused")

class UserQuestionRequest(BaseModel):
    """Request to store a user question"""
    question: str
    chatbot_type: str = Field(..., description="Type of chatbot: 'view_insights' or 'vector_deep_ai'")
    chart_title: Optional[str] = None
    context: Optional[dict] = None
    response: Optional[str] = None

class UserQuestionResponse(BaseModel):
    """Response model for user questions"""
    id: str
    question: str
    chatbot_type: str
    chart_title: Optional[str] = None
    timestamp: str
    usage_count: int = 0

class PreviousQuestionsResponse(BaseModel):
    """Response for retrieving previous questions"""
    questions: List[UserQuestionResponse]

