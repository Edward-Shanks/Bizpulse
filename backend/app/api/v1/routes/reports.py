"""
Reports routes
Handles report generation and download endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.services.reports_service import ReportsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/reports/generate")
async def generate_custom_report(
    years: Optional[str] = Query(None, description="Comma-separated years"),
    months: Optional[str] = Query(None, description="Comma-separated months"),
    businesses: Optional[str] = Query(None, description="Comma-separated business names"),
    channels: Optional[str] = Query(None, description="Comma-separated channels"),
    brands: Optional[str] = Query(None, description="Comma-separated brands"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    format: str = Query("excel", description="Report format: excel or csv"),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate custom report based on filters"""
    try:
        reports_service = ReportsService(db)
        
        # Generate report
        file_data, filename, media_type = await reports_service.generate_custom_report(
            years=years,
            months=months,
            businesses=businesses,
            channels=channels,
            brands=brands,
            categories=categories,
            format=format
        )
        
        # Return file as download
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Custom report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/executive-summary")
async def generate_executive_summary_report(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate Executive Summary Report"""
    try:
        reports_service = ReportsService(db)
        file_data, filename, media_type = await reports_service.generate_executive_summary_report(
            years=years,
            months=months,
            businesses=businesses
        )
        
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Executive summary report error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/customer-performance")
async def generate_customer_performance_report(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    channels: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate Customer Performance Report"""
    try:
        reports_service = ReportsService(db)
        file_data, filename, media_type = await reports_service.generate_customer_performance_report(
            years=years,
            months=months,
            businesses=businesses,
            channels=channels
        )
        
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Customer performance report error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/brand-analysis")
async def generate_brand_analysis_report(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    brands: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate Brand Analysis Report"""
    try:
        reports_service = ReportsService(db)
        file_data, filename, media_type = await reports_service.generate_brand_analysis_report(
            years=years,
            months=months,
            businesses=businesses,
            brands=brands
        )
        
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Brand analysis report error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/category-insights")
async def generate_category_insights_report(
    years: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate Category Insights Report"""
    try:
        reports_service = ReportsService(db)
        file_data, filename, media_type = await reports_service.generate_category_insights_report(
            years=years,
            months=months,
            businesses=businesses,
            categories=categories
        )
        
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Category insights report error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/yoy-comparison")
async def generate_yoy_comparison_report(
    years: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate Year-over-Year Comparison Report"""
    try:
        reports_service = ReportsService(db)
        file_data, filename, media_type = await reports_service.generate_yoy_comparison_report(
            years=years,
            businesses=businesses
        )
        
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"YoY comparison report error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/monthly-trends")
async def generate_monthly_trends_report(
    years: Optional[str] = Query(None),
    businesses: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate Monthly Trends Report"""
    try:
        reports_service = ReportsService(db)
        file_data, filename, media_type = await reports_service.generate_monthly_trends_report(
            years=years,
            businesses=businesses
        )
        
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Monthly trends report error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
