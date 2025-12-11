"""
Customer Deep Intelligence related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CustomerInsightsChatRequest(BaseModel):
    """Request model for Customer Deep Intelligence chatbot"""
    message: str = Field(..., description="User's question or message", example="What is the total gross sales?")
    chart_title: Optional[str] = Field(None, description="Title of the chart being viewed", example="Sales Channel Performance")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Filter context including selectedYears, selectedMonths, selectedChannels, etc.",
        example={"selectedYears": [2025], "selectedMonths": ["January"]}
    )
    session_id: Optional[str] = Field(None, description="Session identifier for tracking conversations", example="session_123")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Previous conversation messages for context",
        example=[{"role": "user", "content": "What is the total sales?"}, {"role": "assistant", "content": "The total sales is..."}]
    )

class CustomerInsightsChatResponse(BaseModel):
    """Response model for Customer Deep Intelligence chatbot"""
    response: str = Field(..., description="AI-generated response to the user's question", example="Based on the Shopify customer data, the total gross sales is €299,132,414.31...")
    timestamp: Optional[str] = Field(None, description="Response timestamp", example="01:30 PM IST on November 29, 2025")
    context: Optional[str] = Field(None, description="Data context used for generating the response", example="Shopify Customer Data Analysis...")
    data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional data including pivot_table, filters, columns, etc.",
        example={
            "pivot_table": [{"Total sales": 299132414.31, "Orders": 15000}],
            "columns": ["Total sales"],
            "filters": {},
            "is_trend_query": False,
            "total_rows": 15972
        }
    )



