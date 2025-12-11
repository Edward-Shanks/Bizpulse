"""
Filter routes
Handles dynamic filter options endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.services.filter_service import FilterService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/filters/options")
async def get_filter_options(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    channels: Optional[str] = Query(None),
    brands: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get dynamic filter options based on current filter selections"""
    try:
        filter_service = FilterService(db)
        return await filter_service.get_filter_options(
            years=years,
            months=months,
            businesses=businesses,
            channels=channels,
            brands=brands,
            categories=categories
        )
    except Exception as e:
        logger.error(f"Filter options error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



