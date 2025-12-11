"""
Data context utilities for generating comprehensive data summaries
Used by Insights Chat to provide context to AI
"""
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.helpers import safe_float, format_currency, format_units
import logging

logger = logging.getLogger(__name__)

async def get_comprehensive_data_context(
    query: Dict[str, Any],
    user_message: str,
    db: AsyncIOMotorDatabase,
    is_comparison: bool = False,
    is_quarterly: bool = False,
    is_monthly: bool = False,
    is_yearly: bool = False,
    is_metrics: bool = False
) -> str:
    """Get comprehensive data context for complex queries"""
    context_parts = []
    user_msg_lower = user_message.lower()
    
    try:
        # CRITICAL: If query is empty, use empty match to get ALL data
        # If query has filters, use those filters
        match_stage = {"$match": query} if query else {"$match": {}}
        logger.info(f"🔍 Data context - Query: {query}, Match stage: {match_stage}")
        
        # Get overall totals
        pipeline_totals = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            }
        ]
        totals_result = await db.business_data.aggregate(pipeline_totals).to_list(1)
        totals = totals_result[0] if totals_result else {}
        
        total_revenue = safe_float(totals.get('total_revenue', 0))
        total_profit = safe_float(totals.get('total_profit', 0))
        total_units = safe_float(totals.get('total_units', 0))
        
        context_parts.append("Overall Totals:")
        context_parts.append(f"  Total Revenue: {format_currency(total_revenue)}")
        context_parts.append(f"  Total Gross Profit: {format_currency(total_profit)}")
        context_parts.append(f"  Total Units: {format_units(total_units)}")
        if total_revenue > 0:
            margin = (total_profit / total_revenue) * 100
            context_parts.append(f"  Profit Margin: {margin:.2f}%")
        
        # If no data found, add a note
        if total_revenue == 0 and total_profit == 0 and total_units == 0:
            context_parts.append("\n⚠️ Note: No data found matching the specified filters. Please check your filter criteria.")
        
        # If metrics requested, get all available metrics
        if is_metrics or "all metrics" in user_msg_lower or "cases" in user_msg_lower or "gsales" in user_msg_lower:
            # Get additional metrics if available in the data
            pipeline_metrics = [
                match_stage,
                {
                    "$group": {
                        "_id": None,
                        "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                        "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                        "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                    }
                }
            ]
            metrics_result = await db.business_data.aggregate(pipeline_metrics).to_list(1)
            if metrics_result:
                metrics = metrics_result[0]
                context_parts.append("\nDetailed Metrics:")
                context_parts.append(f"  Revenue: {format_currency(safe_float(metrics.get('total_revenue', 0)))}")
                context_parts.append(f"  Gross Profit: {format_currency(safe_float(metrics.get('total_profit', 0)))}")
                context_parts.append(f"  Cases: {format_units(safe_float(metrics.get('total_units', 0)))}")
                if safe_float(metrics.get('total_revenue', 0)) > 0:
                    margin = (safe_float(metrics.get('total_profit', 0)) / safe_float(metrics.get('total_revenue', 0))) * 100
                    context_parts.append(f"  Margin: {margin:.2f}%")
        
        # Quarterly breakdown
        if is_quarterly or "quarter" in user_msg_lower or "q1" in user_msg_lower or "q2" in user_msg_lower:
            quarter_months = {
                'Q1': ['January', 'February', 'March'],
                'Q2': ['April', 'May', 'June'],
                'Q3': ['July', 'August', 'September'],
                'Q4': ['October', 'November', 'December']
            }
            
            for quarter, months in quarter_months.items():
                # Merge quarter months with existing month filter if present
                quarter_query = query.copy()
                if 'Month_Name' in query:
                    # Intersect existing months with quarter months
                    existing_months = query['Month_Name'].get('$in', [])
                    if isinstance(existing_months, list):
                        quarter_months_list = [m for m in existing_months if m in months]
                        if quarter_months_list:
                            quarter_query['Month_Name'] = {'$in': quarter_months_list}
                        else:
                            continue  # Skip this quarter if no overlap
                    else:
                        quarter_query['Month_Name'] = {'$in': months}
                else:
                    quarter_query['Month_Name'] = {'$in': months}
                quarter_match = {"$match": quarter_query}
                pipeline_quarter = [
                    quarter_match,
                    {
                        "$group": {
                            "_id": None,
                            "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                            "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                            "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                        }
                    }
                ]
                quarter_result = await db.business_data.aggregate(pipeline_quarter).to_list(1)
                if quarter_result and quarter_result[0]:
                    q_data = quarter_result[0]
                    revenue = safe_float(q_data.get('Revenue', 0))
                    profit = safe_float(q_data.get('Gross_Profit', 0))
                    if revenue > 0:
                        margin = (profit / revenue) * 100
                        context_parts.append(f"\n{quarter} Performance:")
                        context_parts.append(f"  Revenue: {format_currency(revenue)}")
                        context_parts.append(f"  Gross Profit: {format_currency(profit)}")
                        context_parts.append(f"  Margin: {margin:.2f}%")
                        context_parts.append(f"  Cases: {format_units(safe_float(q_data.get('Units', 0)))}")
        
        # Monthly breakdown
        if is_monthly or "monthly" in user_msg_lower or "by month" in user_msg_lower:
            pipeline_monthly = [
                match_stage,
                {
                    "$group": {
                        "_id": "$Month_Name",
                        "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                        "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                        "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            monthly_results = await db.business_data.aggregate(pipeline_monthly).to_list(12)
            if monthly_results:
                context_parts.append("\nMonthly Breakdown:")
                month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                # Sort by month order
                sorted_months = sorted(monthly_results, key=lambda x: (
                    month_order.index(str(x['_id'])) if str(x['_id']) in month_order else 999
                ))
                for item in sorted_months:
                    month = str(item.get("_id", ""))
                    revenue = safe_float(item.get("Revenue", 0))
                    profit = safe_float(item.get("Gross_Profit", 0))
                    if revenue > 0:
                        margin = (profit / revenue) * 100
                        context_parts.append(f"  {month}: Revenue {format_currency(revenue)}, Profit {format_currency(profit)} ({margin:.1f}% margin)")
        
        # Yearly breakdown (for comparisons)
        if is_yearly or is_comparison or "year" in user_msg_lower:
            pipeline_yearly = [
                match_stage,
                {
                    "$group": {
                        "_id": "$Year",
                        "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                        "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                        "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            yearly_results = await db.business_data.aggregate(pipeline_yearly).to_list(10)
            if yearly_results:
                context_parts.append("\nYearly Performance:")
                for item in yearly_results:
                    year = int(item.get("_id", 0))
                    revenue = safe_float(item.get("Revenue", 0))
                    profit = safe_float(item.get("Gross_Profit", 0))
                    if revenue > 0:
                        margin = (profit / revenue) * 100
                        context_parts.append(f"  {year}: Revenue {format_currency(revenue)}, Profit {format_currency(profit)} ({margin:.1f}% margin), Cases {format_units(safe_float(item.get('Units', 0)))}")
        
        # Brand breakdown (if brand mentioned or comparison)
        # CRITICAL: Exclude Brand filter when asking FOR brands
        if "brand" in user_msg_lower or is_comparison:
            # Use modified query without Brand filter when asking FOR brands
            brand_query = query.copy() if query else {}
            is_asking_for_brands = any(phrase in user_msg_lower for phrase in [
                'top brands', 'top 15 brands', 'top 10 brands', 'top 5 brands',
                'brands by revenue', 'brands by profit', 'brands by', 'all brands',
                'list brands', 'show brands', 'which brands', 'what brands'
            ])
            if is_asking_for_brands and 'Brand' in brand_query:
                logger.info(f"🔍 Removing Brand filter from brand breakdown (user is asking FOR brands)")
                brand_query = {k: v for k, v in brand_query.items() if k != 'Brand'}
            
            logger.info(f"🔍 Data context - Fetching brand breakdown with query: {brand_query}")
            brand_match_stage = {"$match": brand_query} if brand_query else {"$match": {}}
            pipeline_brand = [
                brand_match_stage,
                {
                    "$group": {
                        "_id": "$Brand",
                        "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                        "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                        "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                    }
                },
                {"$match": {"_id": {"$nin": [None, "", "Unknown", "null", "None"]}}},
                {"$sort": {"Revenue": -1}},
                {"$limit": 20}
            ]
            brand_results = await db.business_data.aggregate(pipeline_brand).to_list(20)
            logger.info(f"📊 Data context - Brand results count: {len(brand_results)}")
            if brand_results:
                context_parts.append("\nBrand Performance:")
                for idx, item in enumerate(brand_results, 1):
                    brand = str(item.get("_id", ""))
                    if brand and brand.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        profit = safe_float(item.get("Gross_Profit", 0))
                        if revenue > 0:
                            margin = (profit / revenue) * 100
                            context_parts.append(f"  {idx}. {brand}: Revenue {format_currency(revenue)}, Profit {format_currency(profit)} ({margin:.1f}% margin)")
                            logger.info(f"  Brand {idx}: {brand} - Revenue: {revenue}")
            else:
                logger.warning(f"⚠️ Data context - No brand results found with query: {brand_query}")
        
        # Business breakdown (if business mentioned or comparison)
        if "business" in user_msg_lower or is_comparison:
            pipeline_business = [
                match_stage,
                {
                    "$group": {
                        "_id": "$Business",
                        "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                        "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                        "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                    }
                },
                {"$sort": {"Revenue": -1}}
            ]
            business_results = await db.business_data.aggregate(pipeline_business).to_list(20)
            if business_results:
                context_parts.append("\nBusiness Performance:")
                for item in business_results:
                    business = str(item.get("_id", ""))
                    if business and business.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        profit = safe_float(item.get("Gross_Profit", 0))
                        if revenue > 0:
                            margin = (profit / revenue) * 100
                            context_parts.append(f"  {business}: Revenue {format_currency(revenue)}, Profit {format_currency(profit)} ({margin:.1f}% margin)")
        
        # Channel breakdown
        if "channel" in user_msg_lower:
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
                {"$sort": {"Revenue": -1}}
            ]
            channel_results = await db.business_data.aggregate(pipeline_channel).to_list(20)
            if channel_results:
                context_parts.append("\nChannel Performance:")
                for item in channel_results:
                    channel = str(item.get("_id", ""))
                    if channel and channel.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        profit = safe_float(item.get("Gross_Profit", 0))
                        if revenue > 0:
                            margin = (profit / revenue) * 100
                            context_parts.append(f"  {channel}: Revenue {format_currency(revenue)}, Profit {format_currency(profit)} ({margin:.1f}% margin)")
        
        # Category breakdown
        if "category" in user_msg_lower:
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
                {"$sort": {"Revenue": -1}}
            ]
            category_results = await db.business_data.aggregate(pipeline_category).to_list(20)
            if category_results:
                context_parts.append("\nCategory Performance:")
                for item in category_results:
                    category = str(item.get("_id", ""))
                    if category and category.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        profit = safe_float(item.get("Gross_Profit", 0))
                        if revenue > 0:
                            margin = (profit / revenue) * 100
                            context_parts.append(f"  {category}: Revenue {format_currency(revenue)}, Profit {format_currency(profit)} ({margin:.1f}% margin)")
        
    except Exception as e:
        logger.error(f"Error building comprehensive data context: {str(e)}")
        context_parts.append(f"\nError retrieving data: {str(e)}")
    
    return "\n".join(context_parts)

