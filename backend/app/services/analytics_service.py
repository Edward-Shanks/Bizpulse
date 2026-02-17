"""
Analytics service - Business logic for analytics endpoints
Handles data aggregation and calculations for executive overview, customer analysis, brand analysis, category analysis
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional
from app.repositories.business_data_repository import BusinessDataRepository
from app.utils.query_builder import build_analytics_query, apply_business_filter
from app.utils.helpers import safe_float, sort_by_year, sort_by_month, sort_by_metric
import logging
import math

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for analytics operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.business_data_repo = BusinessDataRepository(db)
        self.db = db
    
    async def get_executive_overview(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        brands: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get executive overview with yearly, business, monthly, and channel performance"""
        logger.info("🔍 Getting executive overview")
        
        # Build query
        query = build_analytics_query(years=years, months=months, channels=channels, brands=brands)
        
        if businesses:
            query = await apply_business_filter(query, businesses, self.db)
        
        match_stage = {"$match": query} if query else {"$match": {}}
        
        # Yearly performance aggregation
        pipeline_yearly = [
            match_stage,
            {
                "$group": {
                    "_id": "$Year",
                    "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                    "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                    "Cases": {"$sum": {"$toDouble": "$Units"}}
                }
            }
        ]
        yearly_results = await self.business_data_repo.aggregate(pipeline_yearly)
        
        yearly_list = []
        for item in yearly_results:
            yearly_list.append({
                "Year": int(item['_id']) if item['_id'] else 0,
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Cases": safe_float(item.get('Cases', 0))
            })
        # Sort by Year in ascending order (2023, 2024, 2025)
        yearly_list = sort_by_year(yearly_list, "Year")
        
        # Business performance aggregation
        pipeline_business = [
            match_stage,
            {
                "$group": {
                    "_id": "$Business",
                    "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                    "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                    "Cases": {"$sum": {"$toDouble": "$Units"}}
                }
            }
        ]
        business_results = await self.business_data_repo.aggregate(pipeline_business)
        
        business_list = []
        for item in business_results:
            business_list.append({
                "Business": str(item['_id']) if item['_id'] else "Unknown",
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Cases": safe_float(item.get('Cases', 0))
            })
        # Sort by Revenue in descending order (largest first)
        business_list = sort_by_metric(business_list, "Revenue", reverse=True)
        
        # Get current year for monthly trend
        pipeline_max_year = [
            match_stage,
            {"$group": {"_id": None, "maxYear": {"$max": {"$toDouble": "$Year"}}}}
        ]
        max_year_result = await self.business_data_repo.aggregate(pipeline_max_year)
        current_year = int(max_year_result[0]['maxYear']) if max_year_result and max_year_result[0].get('maxYear') else 2024
        
        # Monthly trend for current year
        monthly_query = {**query, "Year": current_year}
        pipeline_monthly = [
            {"$match": monthly_query},
            {
                "$group": {
                    "_id": "$Month_Name",
                    "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                    "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                    "Cases": {"$sum": {"$toDouble": "$Units"}}
                }
            }
        ]
        monthly_results = await self.business_data_repo.aggregate(pipeline_monthly)
        
        monthly_list = []
        for item in monthly_results:
            monthly_list.append({
                "Month_Name": str(item['_id']) if item['_id'] else "Unknown",
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Cases": safe_float(item.get('Cases', 0))
            })
        # Sort by Month_Name in chronological order (Jan, Feb, Mar, ...)
        monthly_list = sort_by_month(monthly_list, "Month_Name")
        
        # Channel performance aggregation
        pipeline_channel = [
            match_stage,
            {
                "$group": {
                    "_id": "$Channel",
                    "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                    "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                    "Cases": {"$sum": {"$toDouble": "$Units"}}
                }
            }
        ]
        channel_results = await self.business_data_repo.aggregate(pipeline_channel)
        
        channel_list = []
        for item in channel_results:
            channel_list.append({
                "Channel": str(item['_id']) if item['_id'] else "Unknown",
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Cases": safe_float(item.get('Cases', 0))
            })
        # Sort by Revenue in descending order (largest first)
        channel_list = sort_by_metric(channel_list, "Revenue", reverse=True)
        
        # Get totals
        pipeline_totals = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": "$Revenue"}},
                    "total_profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                    "total_units": {"$sum": {"$toDouble": "$Units"}}
                }
            }
        ]
        totals_result = await self.business_data_repo.aggregate(pipeline_totals, limit=1)
        totals = totals_result[0] if totals_result else {}
        
        logger.info(f"✅ Executive overview calculated: Revenue={totals.get('total_revenue', 0)}")
        
        return {
            "yearly_performance": yearly_list,
            "business_performance": business_list,
            "monthly_trend": monthly_list,
            "channel_performance": channel_list,
            "total_profit": safe_float(totals.get('total_profit', 0)),
            "total_revenue": safe_float(totals.get('total_revenue', 0)),
            "total_units": safe_float(totals.get('total_units', 0))
        }
    
    async def get_customer_analysis(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        customers: Optional[str] = None,
        brands: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customer analysis with channel and customer performance"""
        logger.info("🔍 Getting customer analysis")
        
        # Build query
        query = build_analytics_query(
            years=years, months=months, channels=channels,
            brands=brands, customers=customers
        )
        
        if businesses:
            query = await apply_business_filter(query, businesses, self.db)
        
        match_stage = {"$match": query} if query else {"$match": {}}
        
        # Channel performance aggregation
        pipeline_channel = [
            match_stage,
            {
                "$group": {
                    "_id": "$Channel",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        channel_results = await self.business_data_repo.aggregate(pipeline_channel)
        
        channel_performance = []
        for item in channel_results:
            channel_performance.append({
                "Channel": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })
        
        # Sort by Revenue in descending order (largest first) - already sorted in pipeline, but ensure it's correct
        channel_performance = sort_by_metric(channel_performance, "Revenue", reverse=True)
        
        # Calculate profit margin for channels
        for item in channel_performance:
            revenue = item.get("Revenue", 0)
            profit = item.get("Gross_Profit", 0)
            margin = (profit / revenue) * 100 if revenue else 0
            item["Profit_Margin"] = margin
        
        # Customer performance aggregation
        pipeline_customer = [
            match_stage,
            {
                "$group": {
                    "_id": "$Customer",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        customer_results = await self.business_data_repo.aggregate(pipeline_customer)
        
        customer_performance = []
        for item in customer_results:
            customer_performance.append({
                "Customer": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })
        
        # Sort by Revenue in descending order (largest first) - already sorted in pipeline, but ensure it's correct
        customer_performance = sort_by_metric(customer_performance, "Revenue", reverse=True)
        
        top_customers = customer_performance[:50]
        
        # Totals
        pipeline_totals = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
        ]
        totals_result = await self.business_data_repo.aggregate(pipeline_totals, limit=1)
        totals = totals_result[0] if totals_result else {}
        
        active_channels = sum(
            1 for item in channel_performance
            if item["Channel"] != "Unknown" and item["Revenue"] > 0
        )
        
        return {
            "channel_performance": channel_performance,
            "customer_performance": customer_performance,
            "top_customers": top_customers,
            "total_revenue": safe_float(totals.get("total_revenue", 0)),
            "total_profit": safe_float(totals.get("total_profit", 0)),
            "total_units": safe_float(totals.get("total_units", 0)),
            "active_channels": active_channels,
        }
    
    async def get_brand_analysis(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        categories: Optional[str] = None,
        brands: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get brand analysis with brand performance, brand by business, and YoY growth"""
        logger.info("🔍 Getting brand analysis")
        
        # Build query
        query = build_analytics_query(
            years=years, months=months, businesses=businesses,
            channels=channels, categories=categories, brands=brands
        )
        
        if businesses:
            query = await apply_business_filter(query, businesses, self.db)
        
        match_stage = {"$match": query} if query else {"$match": {}}
        
        # Brand performance aggregation
        pipeline_brand = [
            match_stage,
            {
                "$group": {
                    "_id": "$Brand",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        brand_results = await self.business_data_repo.aggregate(pipeline_brand)
        
        brand_performance = []
        for item in brand_results:
            brand_performance.append({
                "Brand": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })
        # Sort by Revenue in descending order (largest first) - already sorted in pipeline, but ensure it's correct
        brand_performance = sort_by_metric(brand_performance, "Revenue", reverse=True)
        
        # Brand by business aggregation
        pipeline_brand_business = [
            match_stage,
            {
                "$group": {
                    "_id": {
                        "Brand": "$Brand",
                        "Business": "$Business",
                    },
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        brand_business_results = await self.business_data_repo.aggregate(pipeline_brand_business)
        
        brand_by_business = []
        for item in brand_business_results:
            key = item.get("_id", {})
            brand_by_business.append({
                "Brand": str(key.get("Brand")) if key.get("Brand") else "Unknown",
                "Business": str(key.get("Business")) if key.get("Business") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
            })
        
        # Brand Year-over-Year aggregation
        pipeline_brand_yoy = [
            match_stage,
            {
                "$group": {
                    "_id": {
                        "Brand": "$Brand",
                        "Year": "$Year",
                    },
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                }
            },
            {"$sort": {"_id.Brand": 1, "_id.Year": 1}},
        ]
        brand_yoy_results = await self.business_data_repo.aggregate(pipeline_brand_yoy)
        
        brand_yoy_growth = []
        for item in brand_yoy_results:
            key = item.get("_id", {})
            brand_yoy_growth.append({
                "Brand": str(key.get("Brand")) if key.get("Brand") else "Unknown",
                "Year": int(key.get("Year")) if key.get("Year") else 0,
                "Revenue": safe_float(item.get("Revenue")),
            })
        # Sort by Brand first, then by Year ascending (already sorted in pipeline, but ensure it's correct)
        brand_yoy_growth = sorted(brand_yoy_growth, key=lambda x: (x.get("Brand", ""), int(x.get("Year", 0))))
        
        # Totals and active brands
        pipeline_totals = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
        ]
        totals_result = await self.business_data_repo.aggregate(pipeline_totals, limit=1)
        totals = totals_result[0] if totals_result else {}
        
        # Count all distinct brands that have data (not just revenue > 0)
        # This includes brands with 0 revenue but have units, profit, or other data
        # Exclude only "Unknown", null, empty, or invalid brand names
        active_brands = 0
        excluded_brands = []
        for item in brand_performance:
            brand = item.get("Brand")
            if brand:
                brand_str = str(brand).strip()
                if (brand_str and 
                    brand_str != "Unknown" and 
                    brand_str.lower() not in ["unknown", "none", "null", ""]):
                    active_brands += 1
                else:
                    excluded_brands.append(brand_str)
            else:
                excluded_brands.append("None/Null")
        
        # Log excluded brands for debugging
        if excluded_brands:
            logger.info(f"⚠️ Excluded {len(excluded_brands)} brand(s) from active_brands count: {excluded_brands}")
        
        return {
            "brand_performance": brand_performance,
            "brand_by_business": brand_by_business,
            "brand_yoy_growth": brand_yoy_growth,
            "total_revenue": safe_float(totals.get("total_revenue", 0)),
            "total_profit": safe_float(totals.get("total_profit", 0)),
            "total_units": safe_float(totals.get("total_units", 0)),
            "active_brands": active_brands,
        }
    
    async def get_category_analysis(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        categories: Optional[str] = None,
        sub_categories: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get category analysis with category performance and sub-category breakdown"""
        logger.info("🔍 Getting category analysis")
        
        # Build query
        query = build_analytics_query(
            years=years, months=months, channels=channels,
            categories=categories, sub_categories=sub_categories
        )
        
        if businesses:
            query = await apply_business_filter(query, businesses, self.db)
        
        match_stage = {"$match": query} if query else {"$match": {}}
        
        # Category performance aggregation
        pipeline_category = [
            match_stage,
            {
                "$group": {
                    "_id": "$Category",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        category_results = await self.business_data_repo.aggregate(pipeline_category)
        
        # Normalize and merge categories with same name (different case)
        from app.utils.helpers import normalize_category_name
        category_performance_dict = {}
        for item in category_results:
            cat_name = str(item.get("_id")) if item.get("_id") else "Unknown"
            normalized = normalize_category_name(cat_name)
            
            if normalized not in category_performance_dict:
                category_performance_dict[normalized] = {
                    "Category": normalized,
                    "Revenue": safe_float(item.get("Revenue")),
                    "Gross_Profit": safe_float(item.get("Gross_Profit")),
                    "Units": safe_float(item.get("Units")),
                }
            else:
                # Merge duplicate categories
                category_performance_dict[normalized]["Revenue"] += safe_float(item.get("Revenue"))
                category_performance_dict[normalized]["Gross_Profit"] += safe_float(item.get("Gross_Profit"))
                category_performance_dict[normalized]["Units"] += safe_float(item.get("Units"))
        
        category_performance = list(category_performance_dict.values())
        category_performance.sort(key=lambda x: x["Revenue"], reverse=True)
        
        # Sub-category performance aggregation
        pipeline_subcategory = [
            match_stage,
            {
                "$group": {
                    "_id": {
                        "$ifNull": ["$Sub_Cat", "$Sub_Category"]
                    },
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        subcategory_results = await self.business_data_repo.aggregate(pipeline_subcategory)
        
        subcategory_performance = []
        for item in subcategory_results:
            subcategory_performance.append({
                "Sub_Category": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })
        
        # Totals
        pipeline_totals = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
        ]
        totals_result = await self.business_data_repo.aggregate(pipeline_totals, limit=1)
        totals = totals_result[0] if totals_result else {}
        
        # Count active categories (excluding "Unknown")
        active_categories = sum(
            1 for item in category_performance
            if item["Category"] != "Unknown"
        )
        
        return {
            "category_performance": category_performance,
            "subcategory_performance": subcategory_performance,
            "total_revenue": safe_float(totals.get("total_revenue", 0)),
            "total_profit": safe_float(totals.get("total_profit", 0)),
            "total_units": safe_float(totals.get("total_units", 0)),
            "active_categories": active_categories,
        }
    
    async def get_sales_by_month(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        brands: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get gross sales data aggregated by month and year for time series chart"""
        logger.info("🔍 Getting sales by month")
        
        # Build query
        query = build_analytics_query(years=years, months=months, channels=channels, brands=brands)
        
        if businesses:
            query = await apply_business_filter(query, businesses, self.db)
        
        match_stage = {"$match": query} if query else {"$match": {}}
        
        # Aggregate by Year and Month_Name
        pipeline = [
            match_stage,
            {
                "$group": {
                    "_id": {
                        "year": "$Year",
                        "month": "$Month_Name"
                    },
                    "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "gross_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}}
                }
            },
            {
                "$sort": {
                    "_id.year": 1,
                    "_id.month": 1
                }
            }
        ]
        
        results = await self.business_data_repo.aggregate(pipeline)
        
        # Transform results
        data_list = []
        for item in results:
            year = item['_id']['year']
            month = item['_id']['month']
            
            data_list.append({
                "year": int(year) if year else 0,
                "month_name": str(month) if month else "Unknown",
                "revenue": safe_float(item.get('revenue', 0)),
                "gross_profit": safe_float(item.get('gross_profit', 0)),
                "units": safe_float(item.get('units', 0))
            })
        
        # Sort by year and then by month (chronological order)
        # Month order: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
        month_order = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        data_list.sort(key=lambda x: (x['year'], month_order.get(x['month_name'], 99)))
        
        return {
            "data": data_list,
            "count": len(data_list)
        }
    
    async def get_executive_dashboard(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        brands: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive executive dashboard data"""
        logger.info("🔍 Getting executive dashboard data")
        
        # Build query
        query = build_analytics_query(years=years, months=months, channels=channels, brands=brands)
        
        if businesses:
            query = await apply_business_filter(query, businesses, self.db)
        
        match_stage = {"$match": query} if query else {"$match": {}}
        
        # Get summary metrics (Gross Sales, Gross Profit, Margin%, Transfer Cost)
        pipeline_summary = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "gross_sales": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "gross_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "transfer_cost": {"$sum": {"$toDouble": {"$ifNull": ["$Cost_of_Goods", 0]}}},
                    "units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}}
                }
            }
        ]
        summary_result = await self.business_data_repo.aggregate(pipeline_summary)
        summary = summary_result[0] if summary_result else {}
        
        gross_sales = safe_float(summary.get('gross_sales', 0))
        gross_profit = safe_float(summary.get('gross_profit', 0))
        transfer_cost = safe_float(summary.get('transfer_cost', 0))
        units = safe_float(summary.get('units', 0))
        margin_pct = (gross_profit / gross_sales * 100) if gross_sales > 0 else 0
        
        # Get top 10 customers
        pipeline_customers = [
            match_stage,
            {
                "$group": {
                    "_id": "$Customer",
                    "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}}
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": 10}
        ]
        customers_result = await self.business_data_repo.aggregate(pipeline_customers)
        
        top_customers = []
        for item in customers_result:
            revenue = safe_float(item.get('revenue', 0))
            profit = safe_float(item.get('profit', 0))
            customer_margin = (profit / revenue * 100) if revenue > 0 else 0
            top_customers.append({
                "name": str(item['_id']) if item['_id'] else "Unknown",
                "revenue": revenue,
                "profit": profit,
                "margin_pct": round(customer_margin, 2),
                "units": safe_float(item.get('units', 0))
            })
        
        # Get top 10 brands
        pipeline_brands = [
            match_stage,
            {
                "$group": {
                    "_id": "$Brand",
                    "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}}
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": 10}
        ]
        brands_result = await self.business_data_repo.aggregate(pipeline_brands)
        
        top_brands = []
        for item in brands_result:
            revenue = safe_float(item.get('revenue', 0))
            profit = safe_float(item.get('profit', 0))
            brand_margin = (profit / revenue * 100) if revenue > 0 else 0
            top_brands.append({
                "name": str(item['_id']) if item['_id'] else "Unknown",
                "revenue": revenue,
                "profit": profit,
                "margin_pct": round(brand_margin, 2),
                "units": safe_float(item.get('units', 0))
            })
        
        # Get top 10 channels
        pipeline_channels = [
            match_stage,
            {
                "$group": {
                    "_id": "$Channel",
                    "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}}
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": 10}
        ]
        channels_result = await self.business_data_repo.aggregate(pipeline_channels)
        
        top_channels = []
        for item in channels_result:
            revenue = safe_float(item.get('revenue', 0))
            profit = safe_float(item.get('profit', 0))
            channel_margin = (profit / revenue * 100) if revenue > 0 else 0
            top_channels.append({
                "name": str(item['_id']) if item['_id'] else "Unknown",
                "revenue": revenue,
                "profit": profit,
                "margin_pct": round(channel_margin, 2),
                "units": safe_float(item.get('units', 0))
            })
        
        # Get top 10 categories
        pipeline_categories = [
            match_stage,
            {
                "$group": {
                    "_id": "$Category",
                    "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}}
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": 10}
        ]
        categories_result = await self.business_data_repo.aggregate(pipeline_categories)
        
        top_categories = []
        for item in categories_result:
            revenue = safe_float(item.get('revenue', 0))
            profit = safe_float(item.get('profit', 0))
            category_margin = (profit / revenue * 100) if revenue > 0 else 0
            top_categories.append({
                "name": str(item['_id']) if item['_id'] else "Unknown",
                "revenue": revenue,
                "profit": profit,
                "margin_pct": round(category_margin, 2),
                "units": safe_float(item.get('units', 0))
            })
        
        # Get top 10 businesses
        pipeline_businesses = [
            match_stage,
            {
                "$group": {
                    "_id": "$Business",
                    "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}}
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": 10}
        ]
        businesses_result = await self.business_data_repo.aggregate(pipeline_businesses)
        
        top_businesses = []
        for item in businesses_result:
            revenue = safe_float(item.get('revenue', 0))
            profit = safe_float(item.get('profit', 0))
            business_margin = (profit / revenue * 100) if revenue > 0 else 0
            top_businesses.append({
                "name": str(item['_id']) if item['_id'] else "Unknown",
                "revenue": revenue,
                "profit": profit,
                "margin_pct": round(business_margin, 2),
                "units": safe_float(item.get('units', 0))
            })
        
        # Get exception highlights (month-over-month comparisons)
        pipeline_monthly = [
            match_stage,
            {
                "$group": {
                    "_id": {
                        "year": "$Year",
                        "month": "$Month_Name"
                    },
                    "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}}
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
        monthly_result = await self.business_data_repo.aggregate(pipeline_monthly)
        
        # Sort and analyze exceptions
        month_order = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        monthly_data = []
        for item in monthly_result:
            year = item['_id']['year']
            month = item['_id']['month']
            revenue = safe_float(item.get('revenue', 0))
            profit = safe_float(item.get('profit', 0))
            monthly_data.append({
                "year": int(year) if year else 0,
                "month": str(month) if month else "Unknown",
                "month_order": month_order.get(str(month), 99),
                "revenue": revenue,
                "profit": profit,
                "margin_pct": (profit / revenue * 100) if revenue > 0 else 0
            })
        
        monthly_data.sort(key=lambda x: (x['year'], x['month_order']))
        
        # Find exceptions (significant changes > 15%)
        exceptions = []
        for i in range(1, len(monthly_data)):
            prev = monthly_data[i-1]
            curr = monthly_data[i]
            
            # Revenue change
            if prev['revenue'] > 0:
                rev_change = ((curr['revenue'] - prev['revenue']) / prev['revenue']) * 100
                if abs(rev_change) > 15:
                    exceptions.append({
                        "type": "revenue_change",
                        "severity": "high" if abs(rev_change) > 25 else "medium",
                        "period": f"{curr['month']} {curr['year']}",
                        "message": f"Revenue {'increased' if rev_change > 0 else 'decreased'} by {abs(rev_change):.1f}% vs previous month",
                        "value": rev_change
                    })
            
            # Margin change
            margin_change = curr['margin_pct'] - prev['margin_pct']
            if abs(margin_change) > 3:
                exceptions.append({
                    "type": "margin_change",
                    "severity": "high" if abs(margin_change) > 5 else "medium",
                    "period": f"{curr['month']} {curr['year']}",
                    "message": f"Margin {'improved' if margin_change > 0 else 'declined'} by {abs(margin_change):.1f} percentage points",
                    "value": margin_change
                })
        
        # Limit to top 5 most recent exceptions
        exceptions = sorted(exceptions, key=lambda x: x.get('value', 0), reverse=True)[:5]
        
        return {
            "summary": {
                "gross_sales": gross_sales,
                "gross_profit": gross_profit,
                "transfer_cost": transfer_cost,
                "margin_pct": round(margin_pct, 2),
                "units": units
            },
            "top_contributors": {
                "customers": top_customers,
                "brands": top_brands,
                "channels": top_channels,
                "categories": top_categories,
                "businesses": top_businesses
            },
            "exceptions": exceptions,
            "monthly_trend": monthly_data
        }

# Factory function
def get_analytics_service(db: AsyncIOMotorDatabase) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(db)

