"""
Data context utilities for generating comprehensive data summaries
Used by Insights Chat to provide context to AI
"""
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.helpers import safe_float, format_currency, format_units
import logging
import re

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
        
        # CRITICAL FIX #1: Explicitly label Q1/Q2/Q3/Q4 when detected (as per ChatGPT recommendation)
        # This prevents LLM from thinking "Q1 data not available" when it actually exists
        quarter_label = ""
        if "q1" in user_msg_lower or "quarter 1" in user_msg_lower:
            if 'Month_Name' in query:
                month_filter = query.get('Month_Name', {}).get('$in', [])
                if any(m in ['January', 'February', 'March'] for m in month_filter):
                    quarter_label = "📌 Quarter Interpretation: Q1 = January, February, March. All figures below reflect only these months (Q1 data).\n\n"
                    logger.info("📌 Added Q1 label to data context")
        elif "q2" in user_msg_lower or "quarter 2" in user_msg_lower:
            if 'Month_Name' in query:
                month_filter = query.get('Month_Name', {}).get('$in', [])
                if any(m in ['April', 'May', 'June'] for m in month_filter):
                    quarter_label = "📌 Quarter Interpretation: Q2 = April, May, June. All figures below reflect only these months (Q2 data).\n\n"
                    logger.info("📌 Added Q2 label to data context")
        elif "q3" in user_msg_lower or "quarter 3" in user_msg_lower:
            if 'Month_Name' in query:
                month_filter = query.get('Month_Name', {}).get('$in', [])
                if any(m in ['July', 'August', 'September'] for m in month_filter):
                    quarter_label = "📌 Quarter Interpretation: Q3 = July, August, September. All figures below reflect only these months (Q3 data).\n\n"
                    logger.info("📌 Added Q3 label to data context")
        elif "q4" in user_msg_lower or "quarter 4" in user_msg_lower:
            if 'Month_Name' in query:
                month_filter = query.get('Month_Name', {}).get('$in', [])
                if any(m in ['October', 'November', 'December'] for m in month_filter):
                    quarter_label = "📌 Quarter Interpretation: Q4 = October, November, December. All figures below reflect only these months (Q4 data).\n\n"
                    logger.info("📌 Added Q4 label to data context")
        
        # Add quarter label at the beginning if detected
        if quarter_label:
            context_parts.append(quarter_label)
        
        # Get overall totals
        # CRITICAL: Include Gross_Sales in aggregation (as per ChatGPT recommendation - default metric)
        pipeline_totals = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_gross_sales": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Sales", "$Revenue", 0]}}},  # Gross_Sales with fallback to Revenue
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            }
        ]
        totals_result = await db.business_data.aggregate(pipeline_totals).to_list(1)
        totals = totals_result[0] if totals_result else {}
        
        total_revenue = safe_float(totals.get('total_revenue', 0))
        total_gross_sales = safe_float(totals.get('total_gross_sales', total_revenue))  # Fallback to revenue if not available
        total_profit = safe_float(totals.get('total_profit', 0))
        total_units = safe_float(totals.get('total_units', 0))
        
        # CRITICAL FIX #3: Label totals based on what filters are applied
        totals_label = "Overall Totals"
        if 'Month_Name' in query:
            month_filter = query.get('Month_Name', {}).get('$in', [])
            if len(month_filter) == 3 and set(month_filter) == {'January', 'February', 'March'}:
                totals_label = "Q1 Totals (January-March)"
            elif len(month_filter) == 3 and set(month_filter) == {'April', 'May', 'June'}:
                totals_label = "Q2 Totals (April-June)"
            elif len(month_filter) == 3 and set(month_filter) == {'July', 'August', 'September'}:
                totals_label = "Q3 Totals (July-September)"
            elif len(month_filter) == 3 and set(month_filter) == {'October', 'November', 'December'}:
                totals_label = "Q4 Totals (October-December)"
            elif month_filter:
                month_list = ', '.join(sorted(month_filter))
                totals_label = f"Totals for {month_list}"
        
        context_parts.append(f"{totals_label}:")
        context_parts.append(f"  Total Revenue: {format_currency(total_revenue)}")
        context_parts.append(f"  Total Gross Sales: {format_currency(total_gross_sales)}")  # CRITICAL: Include Gross Sales (default metric)
        context_parts.append(f"  Total Gross Profit: {format_currency(total_profit)}")
        context_parts.append(f"  Total Units: {format_units(total_units)}")
        if total_revenue > 0:
            margin = (total_profit / total_revenue) * 100
            context_parts.append(f"  Profit Margin: {margin:.2f}%")
        
        # If no data found, add a note
        # CRITICAL: Only add this note if ALL metrics are truly zero (not just missing)
        # Do NOT add misleading notes that the LLM might interpret as "data not available"
        if total_revenue == 0 and total_profit == 0 and total_units == 0:
            context_parts.append("\n⚠️ Note: No data found matching the specified filters. Please check your filter criteria.")
            # CRITICAL: This is the ONLY case where we should say "no data"
            # The LLM should NOT interpret aggregated data (even if broader) as "not available"
        
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
        # CRITICAL: Always show Q1/Q2/Q3/Q4 breakdown when quarter is mentioned in question
        # CRITICAL FIX: Database stores abbreviated months (Jan, Feb, Mar), not full names
        if is_quarterly or "quarter" in user_msg_lower or "q1" in user_msg_lower or "q2" in user_msg_lower or "q3" in user_msg_lower or "q4" in user_msg_lower:
            quarter_months = {
                'Q1': ['Jan', 'Feb', 'Mar'],
                'Q2': ['Apr', 'May', 'Jun'],
                'Q3': ['Jul', 'Aug', 'Sep'],
                'Q4': ['Oct', 'Nov', 'Dec']
            }
            
            # CRITICAL FIX #2: Determine which quarter(s) are requested
            requested_quarters = []
            if "q1" in user_msg_lower or "quarter 1" in user_msg_lower:
                requested_quarters.append('Q1')
            if "q2" in user_msg_lower or "quarter 2" in user_msg_lower:
                requested_quarters.append('Q2')
            if "q3" in user_msg_lower or "quarter 3" in user_msg_lower:
                requested_quarters.append('Q3')
            if "q4" in user_msg_lower or "quarter 4" in user_msg_lower:
                requested_quarters.append('Q4')
            
            # If no specific quarter mentioned, show all quarters
            if not requested_quarters:
                requested_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
            
            # CRITICAL FIX: For comparison queries, show quarter breakdown by year (e.g., Q1 2023 vs Q1 2024)
            # Check if this is a comparison query (has multiple years or "compare" in message)
            is_comparison_query = (
                is_comparison or 
                "compare" in user_msg_lower or 
                "across years" in user_msg_lower or
                (query.get('Year') and isinstance(query.get('Year', {}).get('$in'), list) and len(query.get('Year', {}).get('$in', [])) > 1)
            )
            
            # CRITICAL: Detect which dimensions are requested in the query for multi-dimensional breakdowns
            # This allows handling questions like "Compare Q1 for Food and KOKA brand" or "Compare Q1 for Food, KOKA brand, and Grocery channel"
            # The key insight: If a dimension filter exists in the query AND the user mentions it in the question, 
            # we should break down by that dimension for comparison queries
            requested_dimensions = []
            dimension_labels = []
            
            # CRITICAL: For comparison queries, detect ALL dimensions that are:
            # 1. Present in the query as filters, AND
            # 2. Mentioned in the user message (indicating user wants breakdown by that dimension)
            # This enables questions like:
            # - "Compare Q1 for Food and KOKA brand" → Break down by Year + Brand
            # - "Compare Q1 for Food, KOKA brand, and Grocery channel" → Break down by Year + Brand + Channel
            # - "Compare Q1 for Food in 2023 and 2024" → Break down by Year only
            
            # Check for Brand dimension
            # CRITICAL: If Brand filter exists in query, include it in breakdown (user wants brand-level comparison)
            # This works even if Brand filter was removed from data_context_query for listing purposes
            # We check the original query structure to detect dimensions
            if 'Brand' in query:
                # Check if user is asking FOR brands (listing) vs filtering BY brand (comparing specific brand)
                is_asking_for_brands_list = any(phrase in user_msg_lower for phrase in [
                    'top brands', 'all brands', 'list brands', 'show brands', 'which brands', 'what brands'
                ])
                # CRITICAL: If user mentions a specific brand name or "brand" in context of filtering/comparison, include it
                # Pattern: "Food and KOKA brand" or "compare ... brand" = filtering BY brand
                is_filtering_by_brand = (
                    re.search(r'and\s+[A-Z][a-zA-Z\s]+\s+brand', user_msg_lower) or  # "and KOKA brand"
                    re.search(r'business\s+[^,]+\s+and\s+[A-Z][a-zA-Z\s]+\s+brand', user_msg_lower) or  # "business Food and KOKA brand"
                    ('brand' in user_msg_lower and 'and' in user_msg_lower and not any(phrase in user_msg_lower for phrase in ['other brands', 'other brand', 'vs other', 'versus other']))
                )
                if not is_asking_for_brands_list and (is_filtering_by_brand or "brand" in user_msg_lower or query.get('Brand')):
                    requested_dimensions.append("$Brand")
                    dimension_labels.append("Brand")
                    logger.info(f"📊 Multi-dimensional breakdown: Added Brand dimension (filter: {query.get('Brand')})")
            
            # Check for Channel dimension
            # CRITICAL: If Channel filter exists in query, include it in breakdown (user wants channel-level comparison)
            if 'Channel' in query:
                is_asking_for_channels_list = any(phrase in user_msg_lower for phrase in [
                    'top channels', 'all channels', 'list channels', 'show channels'
                ])
                # CRITICAL: Detect patterns like "and grocery channel" OR "and channel grocery" or "Food and grocery channel"
                is_filtering_by_channel = (
                    re.search(r'and\s+[a-z][a-zA-Z\s]+\s+channel', user_msg_lower) or  # "and grocery channel" (case-insensitive)
                    re.search(r'and\s+channel\s+[a-z][a-zA-Z\s]+', user_msg_lower) or  # "and channel grocery" (case-insensitive)
                    re.search(r'business\s+[^,]+\s+and\s+[a-z][a-zA-Z\s]+\s+channel', user_msg_lower) or  # "business Food and grocery channel"
                    re.search(r'business\s+[^,]+\s+and\s+channel\s+[a-z][a-zA-Z\s]+', user_msg_lower) or  # "business Food and channel grocery"
                    ('channel' in user_msg_lower and 'and' in user_msg_lower and not any(phrase in user_msg_lower for phrase in ['other channels', 'other channel', 'vs other', 'versus other']))
                )
                # CRITICAL: Include Channel dimension if:
                # 1. Not asking for all channels (listing), AND
                # 2. Either filtering by specific channel OR channel mentioned in message OR Channel filter exists
                if not is_asking_for_channels_list and (is_filtering_by_channel or "channel" in user_msg_lower or query.get('Channel')):
                    requested_dimensions.append("$Channel")
                    dimension_labels.append("Channel")
                    logger.info(f"📊 Multi-dimensional breakdown: Added Channel dimension (filter: {query.get('Channel')})")
            
            # Check for Category dimension
            if 'Category' in query:
                is_asking_for_categories_list = any(phrase in user_msg_lower for phrase in [
                    'top categories', 'all categories', 'list categories', 'show categories'
                ])
                is_filtering_by_category = (
                    re.search(r'and\s+[A-Z][a-zA-Z\s]+\s+category', user_msg_lower) or
                    ('category' in user_msg_lower and 'and' in user_msg_lower)
                )
                if not is_asking_for_categories_list and (is_filtering_by_category or "category" in user_msg_lower or query.get('Category')):
                    requested_dimensions.append("$Category")
                    dimension_labels.append("Category")
                    logger.info(f"📊 Multi-dimensional breakdown: Added Category dimension (filter: {query.get('Category')})")
            
            # Check for Customer dimension
            if 'Customer' in query:
                is_asking_for_customers_list = any(phrase in user_msg_lower for phrase in [
                    'top customers', 'all customers', 'list customers', 'show customers'
                ])
                is_filtering_by_customer = (
                    re.search(r'and\s+[A-Z][a-zA-Z\s]+\s+customer', user_msg_lower) or
                    ('customer' in user_msg_lower and 'and' in user_msg_lower)
                )
                if not is_asking_for_customers_list and (is_filtering_by_customer or "customer" in user_msg_lower or query.get('Customer')):
                    requested_dimensions.append("$Customer")
                    dimension_labels.append("Customer")
                    logger.info(f"📊 Multi-dimensional breakdown: Added Customer dimension (filter: {query.get('Customer')})")
            
            # Always include Year for comparison queries (for year-over-year comparison)
            if is_comparison_query:
                # Only add Year if not already added (shouldn't happen, but safety check)
                if "$Year" not in requested_dimensions:
                    requested_dimensions.insert(0, "$Year")  # Year first for sorting
                    dimension_labels.insert(0, "Year")
                logger.info(f"📊 Multi-dimensional breakdown: Dimensions detected: {dimension_labels}")
            
            for quarter in requested_quarters:
                months = quarter_months[quarter]
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
                
                # CRITICAL: For comparison queries with multiple dimensions, create multi-dimensional breakdown
                if is_comparison_query and len(requested_dimensions) > 1:
                    # Multi-dimensional grouping (e.g., Year + Brand, or Year + Brand + Channel)
                    group_id = {}
                    for dim in requested_dimensions:
                        field_name = dim.replace("$", "")
                        group_id[field_name] = f"${field_name}"
                    
                    pipeline_quarter = [
                        quarter_match,
                        {
                            "$group": {
                                "_id": group_id,
                                "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                                "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                                "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                                "Gross_Sales": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Sales", "$Revenue", 0]}}},
                            }
                        }
                    ]
                    # Build sort stage - sort by Year first (if present), then other dimensions
                    sort_dict = {}
                    if "$Year" in requested_dimensions:
                        sort_dict["_id.Year"] = 1
                    for dim in requested_dimensions:
                        if dim != "$Year":
                            field_name = dim.replace("$", "")
                            sort_dict[f"_id.{field_name}"] = 1
                    if sort_dict:
                        pipeline_quarter.append({"$sort": sort_dict})
                    quarter_results = await db.business_data.aggregate(pipeline_quarter).to_list(100)
                    if quarter_results:
                        dim_label_str = " by " + " and ".join(dimension_labels)
                        context_parts.append(f"\n{quarter} Performance{dim_label_str} ({', '.join(months)}):")
                        for q_item in quarter_results:
                            item_id = q_item.get("_id", {})
                            # Build label from all dimensions
                            label_parts = []
                            for dim_label in dimension_labels:
                                dim_value = item_id.get(dim_label, "Unknown")
                                label_parts.append(f"{dim_label}: {dim_value}")
                            label = ", ".join(label_parts)
                            
                            revenue = safe_float(q_item.get("Revenue", 0))
                            profit = safe_float(q_item.get("Gross_Profit", 0))
                            gross_sales = safe_float(q_item.get("Gross_Sales", revenue))
                            units = safe_float(q_item.get("Units", 0))
                            if revenue > 0:
                                margin = (profit / revenue) * 100
                                context_parts.append(f"  {label}: Revenue {format_currency(revenue)}, Gross Sales {format_currency(gross_sales)}, Profit {format_currency(profit)} ({margin:.1f}% margin), Cases {format_units(units)}")
                            else:
                                context_parts.append(f"  {label}: Revenue {format_currency(revenue)}, Gross Sales {format_currency(gross_sales)}, Profit {format_currency(profit)}, Cases {format_units(units)}")
                        if quarter == 'Q1' and ("q1" in user_msg_lower or "quarter 1" in user_msg_lower):
                            context_parts.append(f"  ✅ Confirmed: Q1 data broken down by {', '.join(dimension_labels)} for comparison.")
                elif is_comparison_query:
                    # Single dimension: Year only
                    pipeline_quarter = [
                        quarter_match,
                        {
                            "$group": {
                                "_id": "$Year",  # Group by Year for comparison
                                "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                                "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                                "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                                # CRITICAL: Include Gross_Sales (default metric)
                                "Gross_Sales": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Sales", "$Revenue", 0]}}},
                            }
                        },
                        {"$sort": {"_id": 1}}  # Sort by year
                    ]
                    quarter_results = await db.business_data.aggregate(pipeline_quarter).to_list(10)
                    if quarter_results:
                        context_parts.append(f"\n{quarter} Performance by Year ({', '.join(months)}):")
                        for q_item in quarter_results:
                            year = int(q_item.get("_id", 0))
                            revenue = safe_float(q_item.get("Revenue", 0))
                            profit = safe_float(q_item.get("Gross_Profit", 0))
                            gross_sales = safe_float(q_item.get("Gross_Sales", revenue))  # Fallback to revenue
                            units = safe_float(q_item.get("Units", 0))
                            if revenue > 0:
                                margin = (profit / revenue) * 100
                                context_parts.append(f"  {year}: Revenue {format_currency(revenue)}, Gross Sales {format_currency(gross_sales)}, Profit {format_currency(profit)} ({margin:.1f}% margin), Cases {format_units(units)}")
                            else:
                                context_parts.append(f"  {year}: Revenue {format_currency(revenue)}, Gross Sales {format_currency(gross_sales)}, Profit {format_currency(profit)}, Cases {format_units(units)}")
                        # CRITICAL: Add confirmation that Q1 data exists
                        if quarter == 'Q1' and ("q1" in user_msg_lower or "quarter 1" in user_msg_lower):
                            context_parts.append(f"  ✅ Confirmed: Q1 data (January-March) broken down by year for comparison.")
                    else:
                        # CRITICAL: Even if no data, show that Q1 filter was applied
                        if quarter == 'Q1' and ("q1" in user_msg_lower or "quarter 1" in user_msg_lower):
                            context_parts.append(f"\n{quarter} Performance by Year ({', '.join(months)}):")
                            context_parts.append(f"  Note: Q1 filter (January-March) was applied, but no data found for the specified filters.")
                else:
                    # For non-comparison queries, show overall totals
                    pipeline_quarter = [
                        quarter_match,
                        {
                            "$group": {
                                "_id": None,
                                "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                                "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                                "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                                # CRITICAL: Include Gross_Sales (default metric)
                                "Gross_Sales": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Sales", "$Revenue", 0]}}},
                            }
                        }
                    ]
                    quarter_result = await db.business_data.aggregate(pipeline_quarter).to_list(1)
                    if quarter_result and quarter_result[0]:
                        q_data = quarter_result[0]
                        revenue = safe_float(q_data.get('Revenue', 0))
                        profit = safe_float(q_data.get('Gross_Profit', 0))
                        gross_sales = safe_float(q_data.get('Gross_Sales', revenue))  # Fallback to revenue
                        # CRITICAL FIX #2: Always show Q1 data, even if zero (proves it exists)
                        context_parts.append(f"\n{quarter} Performance ({', '.join(months)}):")
                        context_parts.append(f"  Revenue: {format_currency(revenue)}")
                        context_parts.append(f"  Gross Sales: {format_currency(gross_sales)}")  # CRITICAL: Include Gross Sales
                        context_parts.append(f"  Gross Profit: {format_currency(profit)}")
                        if revenue > 0:
                            margin = (profit / revenue) * 100
                            context_parts.append(f"  Margin: {margin:.2f}%")
                        context_parts.append(f"  Cases: {format_units(safe_float(q_data.get('Units', 0)))}")
                        # CRITICAL: Add confirmation that Q1 data exists
                        if quarter == 'Q1' and ("q1" in user_msg_lower or "quarter 1" in user_msg_lower):
                            context_parts.append(f"  ✅ Confirmed: Q1 data (January-March) exists and has been aggregated above.")
                    else:
                        # CRITICAL: Even if no data, show that Q1 filter was applied
                        if quarter == 'Q1' and ("q1" in user_msg_lower or "quarter 1" in user_msg_lower):
                            context_parts.append(f"\n{quarter} Performance ({', '.join(months)}):")
                            context_parts.append(f"  Revenue: €0")
                            context_parts.append(f"  Gross Sales: €0")
                            context_parts.append(f"  Note: Q1 filter (January-March) was applied, but no data found for the specified filters.")
        
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
        
        # Yearly breakdown (for comparisons) - CRITICAL: But skip for Q1-only questions (as per ChatGPT recommendation)
        # FIX #3: Do NOT show yearly totals for Q1-only questions to avoid diluting Q1 intent
        is_q1_only = (
            ("q1" in user_msg_lower or "quarter 1" in user_msg_lower) and 
            not any(k in user_msg_lower for k in ["full year", "yearly", "annual", "all year", "entire year"])
        )
        
        # Show yearly breakdown only if:
        # 1. Not a Q1-only question, OR
        # 2. User explicitly asks for yearly comparison
        should_show_yearly = not is_q1_only and (is_yearly or is_comparison or "year" in user_msg_lower or "compare" in user_msg_lower or "across years" in user_msg_lower)
        
        if should_show_yearly:
            pipeline_yearly = [
                match_stage,
                {
                    "$group": {
                        "_id": "$Year",
                        "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                        "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                        "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                        # CRITICAL: Also include Gross_Sales if available (as per ChatGPT recommendation)
                        "Gross_Sales": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Sales", "$Revenue", 0]}}},
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            yearly_results = await db.business_data.aggregate(pipeline_yearly).to_list(10)
            if yearly_results:
                context_parts.append("\nYearly Breakdown (for comparison):")
                # Sort by year
                sorted_years = sorted(yearly_results, key=lambda x: int(x.get("_id", 0)))
                for item in sorted_years:
                    year = int(item.get("_id", 0))
                    revenue = safe_float(item.get("Revenue", 0))
                    profit = safe_float(item.get("Gross_Profit", 0))
                    units = safe_float(item.get("Units", 0))
                    # CRITICAL: Include Gross_Sales if available (as per ChatGPT recommendation)
                    gross_sales = safe_float(item.get("Gross_Sales", revenue))  # Fallback to Revenue if Gross_Sales not available
                    if revenue > 0:
                        margin = (profit / revenue) * 100
                        context_parts.append(f"  {year}: Revenue {format_currency(revenue)}, Gross Sales {format_currency(gross_sales)}, Profit {format_currency(profit)} ({margin:.1f}% margin), Units {format_units(units)}")
                    else:
                        context_parts.append(f"  {year}: Revenue {format_currency(revenue)}, Gross Sales {format_currency(gross_sales)}, Profit {format_currency(profit)}, Units {format_units(units)}")
        
        # Brand breakdown (if brand mentioned or comparison)
        # CRITICAL: Show brand breakdown when:
        # 1. User mentions "brand" in message, OR
        # 2. It's a comparison query, OR
        # 3. User is comparing brands (e.g., "compare brand X with other brands")
        is_comparing_brands = any(phrase in user_msg_lower for phrase in [
            'compare brand', 'compare brands', 'brand vs', 'brands vs', 'brand versus', 'brands versus',
            'vs other brands', 'versus other brands', 'with other brands', 'compared to other brands',
            'compared with other brands'
        ]) and ('brand' in user_msg_lower or 'brands' in user_msg_lower)
        
        if "brand" in user_msg_lower or is_comparison or is_comparing_brands:
            # Use modified query without Brand filter when asking FOR brands or comparing brands
            brand_query = query.copy() if query else {}
            is_asking_for_brands = (
                any(phrase in user_msg_lower for phrase in [
                    'top brands', 'top 15 brands', 'top 10 brands', 'top 5 brands', 'top 20 brands',
                    'brands by revenue', 'brands by profit', 'brands by', 'all brands',
                    'list brands', 'show brands', 'which brands', 'what brands',
                    'tell me about brands', 'tell me about brand', 'show me brands', 'show me brand',
                    'brand performance', 'brand rankings', 'brand revenue', 'brand profit',
                    'compare brand', 'compare brands', 'brand comparison', 'brands comparison'
                ]) or 
                re.search(r'top\s+\d+\s+brand', user_msg_lower) or
                is_comparing_brands
            )
            # CRITICAL: Remove Brand filter when asking FOR brands or comparing brands (to show all brands)
            if is_asking_for_brands and 'Brand' in brand_query:
                logger.info(f"🔍 Removing Brand filter from brand breakdown (user is asking FOR brands or comparing brands)")
                brand_query = {k: v for k, v in brand_query.items() if k != 'Brand'}
            
            logger.info(f"🔍 Data context - Fetching brand breakdown with query: {brand_query}")
            brand_match_stage = {"$match": brand_query} if brand_query else {"$match": {}}
            # Determine limit from query (e.g., "top 10" = 10, "top 15" = 15, default = 20)
            import re
            top_match = re.search(r'top\s+(\d+)', user_msg_lower)
            brand_limit = int(top_match.group(1)) if top_match else 20
            
            pipeline_brand = [
                brand_match_stage,
                {
                    "$group": {
                        "_id": "$Brand",
                        "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                        "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                        "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                        # CRITICAL: Include Gross_Sales (default metric for comparisons)
                        "Gross_Sales": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Sales", "$Revenue", 0]}}},
                    }
                },
                {"$match": {"_id": {"$nin": [None, "", "Unknown", "null", "None"]}}},
                {"$sort": {"Gross_Sales": -1}},  # Sort by Gross_Sales (default metric) instead of Revenue
                {"$limit": brand_limit}
            ]
            brand_results = await db.business_data.aggregate(pipeline_brand).to_list(brand_limit)
            logger.info(f"📊 Data context - Brand results count: {len(brand_results)}")
            if brand_results:
                # CRITICAL: For brand comparisons, show all brands with clear labeling
                if is_comparing_brands:
                    context_parts.append("\nBrand Comparison (All Brands):")
                else:
                    context_parts.append("\nBrand Performance:")
                for idx, item in enumerate(brand_results, 1):
                    brand = str(item.get("_id", ""))
                    if brand and brand.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        profit = safe_float(item.get("Gross_Profit", 0))
                        gross_sales = safe_float(item.get("Gross_Sales", revenue))  # Fallback to revenue
                        units = safe_float(item.get("Units", 0))
                        if revenue > 0:
                            margin = (profit / revenue) * 100
                            context_parts.append(f"  {idx}. {brand}: Gross Sales {format_currency(gross_sales)}, Revenue {format_currency(revenue)}, Profit {format_currency(profit)} ({margin:.1f}% margin), Units {format_units(units)}")
                            logger.info(f"  Brand {idx}: {brand} - Gross Sales: {gross_sales}, Revenue: {revenue}")
                        else:
                            context_parts.append(f"  {idx}. {brand}: Gross Sales {format_currency(gross_sales)}, Revenue {format_currency(revenue)}, Profit {format_currency(profit)}, Units {format_units(units)}")
            else:
                logger.warning(f"⚠️ Data context - No brand results found with query: {brand_query}")
        
        # Business breakdown (if business mentioned, comparison, or asking for top/all businesses)
        is_asking_for_businesses = (
            "business" in user_msg_lower or 
            is_comparison or 
            "top" in user_msg_lower and "business" in user_msg_lower or
            "all business" in user_msg_lower or
            "all businesses" in user_msg_lower
        )
        if is_asking_for_businesses:
            # Determine limit from query (e.g., "top 10" = 10, "top 15" = 15, default = 20)
            import re
            top_match = re.search(r'top\s+(\d+)', user_msg_lower)
            business_limit = int(top_match.group(1)) if top_match else 20
            
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
            business_results = await db.business_data.aggregate(pipeline_business).to_list(business_limit)
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

