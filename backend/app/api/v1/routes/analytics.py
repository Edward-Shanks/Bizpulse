"""
Analytics routes
Handles executive overview, customer analysis, brand analysis, category analysis endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/analytics/executive-overview")
async def get_executive_overview(
    years: Optional[str] = Query(None, description="Comma-separated years (e.g., '2023,2024')"),
    months: Optional[str] = Query(None, description="Comma-separated months (e.g., 'January,February')"),
    businesses: Optional[str] = Query(None, description="Comma-separated business names"),
    channels: Optional[str] = Query(None, description="Comma-separated channels"),
    brands: Optional[str] = Query(None, description="Comma-separated brands"),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Executive Overview - YoY comparison, KPIs with multi-select filters"""
    try:
        analytics_service = AnalyticsService(db)
        return await analytics_service.get_executive_overview(
            years=years,
            months=months,
            businesses=businesses,
            channels=channels,
            brands=brands
        )
    except Exception as e:
        logger.error(f"Executive overview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/customer-analysis")
async def get_customer_analysis(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    channels: Optional[str] = Query(None),
    customers: Optional[str] = Query(None),
    brands: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Customer Analysis - Channel and customer drilldowns with optional filters"""
    try:
        analytics_service = AnalyticsService(db)
        return await analytics_service.get_customer_analysis(
            years=years,
            months=months,
            businesses=businesses,
            channels=channels,
            customers=customers,
            brands=brands
        )
    except Exception as e:
        logger.error(f"Customer analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/brand-analysis")
async def get_brand_analysis(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    channels: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    brands: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Brand Analysis - Brand performance by category and channel with optional filters"""
    try:
        analytics_service = AnalyticsService(db)
        return await analytics_service.get_brand_analysis(
            years=years,
            months=months,
            businesses=businesses,
            channels=channels,
            categories=categories,
            brands=brands
        )
    except Exception as e:
        logger.error(f"Brand analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/category-analysis")
async def get_category_analysis(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    channels: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    sub_categories: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Category Analysis - Category and sub-category performance with optional filters"""
    try:
        analytics_service = AnalyticsService(db)
        return await analytics_service.get_category_analysis(
            years=years,
            months=months,
            businesses=businesses,
            channels=channels,
            categories=categories,
            sub_categories=sub_categories
        )
    except Exception as e:
        logger.error(f"Category analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



