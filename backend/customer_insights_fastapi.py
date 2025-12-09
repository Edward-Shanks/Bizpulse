"""
MongoDB-based Customer Insights Chatbot with LLM-powered query understanding
Uses LLM to understand questions, generate MongoDB queries, and analyze results
"""
import requests
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API key from environment
PPLX_API_KEY1 = os.getenv("PPLX_API_KEY1")
if not PPLX_API_KEY1:
    logger.warning("PPLX_API_KEY1 not found in environment. Some features may not work.")

def convert_to_native_types(obj):
    """Recursively convert numpy/pandas types to native Python types for JSON serialization"""
    # Handle numpy scalar types
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_to_native_types(item) for item in obj.tolist()]
    elif isinstance(obj, pd.Series):
        return [convert_to_native_types(item) for item in obj.tolist()]
    elif isinstance(obj, pd.DataFrame):
        records = obj.to_dict('records')
        return [convert_to_native_types(record) for record in records]
    elif isinstance(obj, dict):
        return {str(k): convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native_types(item) for item in obj]
    elif pd.isna(obj) or obj is None:
        return None
    elif hasattr(obj, 'item'):
        return obj.item()
    else:
        if isinstance(obj, (str, int, float, bool)):
            return obj
        else:
            return str(obj)

def query_perplexity(prompt, conversation_history=None):
    """Query Perplexity API"""
    if not PPLX_API_KEY1:
        return "API key not configured. Please set PPLX_API_KEY1 environment variable."
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {PPLX_API_KEY1}", "Content-Type": "application/json"}
    
    messages = [{
        "role": "system",
        "content": (
            "You are Vector AI, a friendly customer intelligence analyst for ThriveBrands, "
            "assisting with actionable insights from Shopify customer data. "
            "Analyze the provided data and deliver a detailed, confident answer in a conversational tone. "
            "All monetary values are in Euros (€) or the currency shown in the data. "
            "State results definitively, e.g., 'After analyzing the customer data, [answer].' "
            "Include trends, growth rates (%), and percentages where relevant. "
            "For customer behavior questions, identify patterns with specific numbers. "
            "Always provide 3-5 specific, actionable recommendations with clear 'why' and 'how' for each. "
            "Use conversation history for context in follow-ups. "
            "Keep it engaging and provide comprehensive analysis. "
            "At the end of your response, include a section with 3-5 numbered recommendations, each on a new line starting with a number."
        )
    }]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": prompt})
    payload = {"model": "sonar-pro", "messages": messages, "max_tokens": 2000}
    
    try:
        logger.info("Sending request to Perplexity API")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        logger.info("Received response from Perplexity API")
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Perplexity API error: {e}")
        return f"Error querying AI: {str(e)}"

async def llm_understand_question_and_generate_queries(
    question: str,
    chart_title: Optional[str] = None,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Use LLM to understand the question and determine what MongoDB queries to run.
    Returns a structured query plan with filters and aggregation requirements.
    """
    # Build context about available data fields
    available_fields = """
    Available fields in shopify_data collection:
    - Year (number): e.g., 2023, 2024, 2025
    - Month (number): 1-12
    - MonthName (string): "January", "February", etc.
    - Total sales (number): Sales amount in Euros
    - Orders (number): Number of orders
    - Customer email (string): Customer identifier
    - New or returning customer (string): "New" or "Returning"
    - Referring channel (string): Traffic source channel
    - Shipping country (string): Customer country
    - Day (date): Order date
    - Hour of day (number): 0-23
    """
    
    # Build prompt for LLM to understand the question
    prompt = f"""You are a MongoDB query planner for a Shopify customer analytics system.

User Question: "{question}"
Chart Context: {chart_title if chart_title else "General customer insights"}
Available Filters: {json.dumps(context or {})}

{available_fields}

Analyze the user's question and determine:
1. What filters should be applied (Year, Month, Customer Type, Channel, Country, etc.)
2. What aggregations are needed (group by, sum, count, etc.)
3. What breakdowns are requested (by month, by channel, by customer type, etc.)
4. What metrics to calculate (total sales, average order value, customer count, etc.)

Return a JSON object with this structure:
{{
    "filters": {{
        "Year": [2023, 2024] or null,
        "Month": [1, 2, 3] or null,
        "MonthName": ["January", "February"] or null,
        "New or returning customer": "New" or "Returning" or null,
        "Referring channel": "Direct" or null,
        "Shipping country": "United Kingdom" or null
    }},
    "group_by": ["Year", "Month"] or ["New or returning customer"] or null,
    "metrics": ["Total sales", "Orders", "Customers"],
    "breakdowns": ["monthly", "by_channel", "by_customer_type", "by_country"],
    "analysis_type": "summary" or "trend" or "comparison" or "breakdown",
    "needs_customer_breakdown": true or false,
    "needs_channel_breakdown": true or false,
    "needs_geographic_breakdown": true or false,
    "needs_monthly_breakdown": true or false
}}

Important:
- If question mentions "new vs returning" or "new and returning", set needs_customer_breakdown: true and DON'T filter by customer type
- If question asks about trends over time, set needs_monthly_breakdown: true
- If question asks to compare, set analysis_type: "comparison"
- Only include filters that are explicitly mentioned or can be inferred from context
- Return ONLY valid JSON, no additional text"""

    try:
        response = query_perplexity(prompt, None)
        # Extract JSON from response (might have markdown code blocks)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            query_plan = json.loads(json_match.group())
        else:
            # Fallback: try to parse entire response as JSON
            query_plan = json.loads(response)
        
        logger.info(f"📋 LLM Query Plan: {json.dumps(query_plan, indent=2)}")
        return query_plan
    except Exception as e:
        logger.error(f"Error parsing LLM query plan: {e}")
        logger.error(f"LLM Response: {response[:500] if 'response' in locals() else 'No response'}")
        # Return default query plan
        return {
            "filters": {},
            "group_by": None,
            "metrics": ["Total sales", "Orders", "Customers"],
            "breakdowns": [],
            "analysis_type": "summary",
            "needs_customer_breakdown": "customer" in question.lower() or "new vs returning" in question.lower(),
            "needs_channel_breakdown": "channel" in question.lower(),
            "needs_geographic_breakdown": "country" in question.lower() or "region" in question.lower(),
            "needs_monthly_breakdown": "month" in question.lower() or "trend" in question.lower()
        }

async def execute_mongodb_queries(
    db: AsyncIOMotorDatabase,
    query_plan: Dict[str, Any],
    preset_filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute MongoDB queries based on the LLM-generated query plan.
    Returns comprehensive data for analysis.
    """
    results = {
        "summary": {},
        "customer_breakdown": [],
        "channel_breakdown": [],
        "geographic_breakdown": [],
        "monthly_breakdown": [],
        "raw_data": []
    }
    
    # Build base match query from filters
    match_query = {}
    
    # Apply LLM-suggested filters
    if query_plan.get("filters"):
        filters = query_plan["filters"]
        if filters.get("Year"):
            match_query["Year"] = {"$in": filters["Year"]} if isinstance(filters["Year"], list) else filters["Year"]
        if filters.get("Month"):
            match_query["Month"] = {"$in": filters["Month"]} if isinstance(filters["Month"], list) else filters["Month"]
        if filters.get("MonthName"):
            match_query["MonthName"] = {"$in": filters["MonthName"]} if isinstance(filters["MonthName"], list) else filters["MonthName"]
        if filters.get("New or returning customer"):
            match_query["New or returning customer"] = filters["New or returning customer"]
        if filters.get("Referring channel"):
            match_query["Referring channel"] = filters["Referring channel"]
        if filters.get("Shipping country"):
            match_query["Shipping country"] = filters["Shipping country"]
    
    # Merge with preset filters (preset filters take precedence)
    if preset_filters:
        if 'year' in preset_filters:
            match_query["Year"] = {"$in": [int(preset_filters['year'])]}
        if 'month' in preset_filters:
            month_map = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            month_num = month_map.get(preset_filters['month'], None)
            if month_num:
                match_query["Month"] = {"$in": [month_num]}
    
    match_stage = {"$match": match_query} if match_query else {"$match": {}}
    
    # 1. Get summary statistics
    summary_pipeline = [
        match_stage,
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": {"$toDouble": {"$ifNull": ["$Total sales", 0]}}},
                "total_orders": {"$sum": {"$toDouble": {"$ifNull": ["$Orders", 0]}}},
                "unique_customers": {"$addToSet": "$Customer email"}
            }
        },
        {
            "$project": {
                "total_sales": 1,
                "total_orders": 1,
                "total_customers": {"$size": "$unique_customers"},
                "avg_order_value": {"$divide": ["$total_sales", {"$cond": [{"$eq": ["$total_orders", 0]}, 1, "$total_orders"]}]}
            }
        }
    ]
    
    summary_result = await db.shopify_data.aggregate(summary_pipeline).to_list(1)
    results["summary"] = summary_result[0] if summary_result else {
        "total_sales": 0,
        "total_orders": 0,
        "total_customers": 0,
        "avg_order_value": 0
    }
    
    # 2. Customer type breakdown (if needed)
    if query_plan.get("needs_customer_breakdown", False):
        customer_pipeline = [
            match_stage,
            {
                "$group": {
                    "_id": "$New or returning customer",
                    "sales": {"$sum": {"$toDouble": {"$ifNull": ["$Total sales", 0]}}},
                    "orders": {"$sum": {"$toDouble": {"$ifNull": ["$Orders", 0]}}},
                    "customers": {"$addToSet": "$Customer email"}
                }
            },
            {
                "$project": {
                    "type": "$_id",
                    "sales": 1,
                    "orders": 1,
                    "customers": {"$size": "$customers"}
                }
            }
        ]
        customer_results = await db.shopify_data.aggregate(customer_pipeline).to_list(10)
        results["customer_breakdown"] = customer_results
    
    # 3. Channel breakdown (if needed)
    if query_plan.get("needs_channel_breakdown", False):
        channel_pipeline = [
            match_stage,
            {"$match": {"Referring channel": {"$ne": None, "$exists": True}}},
            {
                "$group": {
                    "_id": "$Referring channel",
                    "sales": {"$sum": {"$toDouble": {"$ifNull": ["$Total sales", 0]}}},
                    "orders": {"$sum": {"$toDouble": {"$ifNull": ["$Orders", 0]}}}
                }
            },
            {"$sort": {"sales": -1}},
            {"$limit": 10}
        ]
        channel_results = await db.shopify_data.aggregate(channel_pipeline).to_list(10)
        results["channel_breakdown"] = channel_results
    
    # 4. Geographic breakdown (if needed)
    if query_plan.get("needs_geographic_breakdown", False):
        country_pipeline = [
            match_stage,
            {
                "$group": {
                    "_id": "$Shipping country",
                    "sales": {"$sum": {"$toDouble": {"$ifNull": ["$Total sales", 0]}}},
                    "orders": {"$sum": {"$toDouble": {"$ifNull": ["$Orders", 0]}}}
                }
            },
            {"$sort": {"sales": -1}},
            {"$limit": 10}
        ]
        country_results = await db.shopify_data.aggregate(country_pipeline).to_list(10)
        results["geographic_breakdown"] = country_results
    
    # 5. Monthly breakdown (if needed)
    if query_plan.get("needs_monthly_breakdown", False):
        monthly_pipeline = [
            match_stage,
            {
                "$match": {
                    "Year": {"$ne": None, "$exists": True, "$type": "number"},
                    "Month": {"$ne": None, "$exists": True, "$type": "number"}
                }
            },
            {
                "$group": {
                    "_id": {"Year": "$Year", "Month": "$Month", "MonthName": "$MonthName"},
                    "sales": {"$sum": {"$toDouble": {"$ifNull": ["$Total sales", 0]}}},
                    "orders": {"$sum": {"$toDouble": {"$ifNull": ["$Orders", 0]}}},
                    "customers": {"$addToSet": "$Customer email"}
                }
            },
            {
                "$project": {
                    "Year": "$_id.Year",
                    "Month": "$_id.Month",
                    "MonthName": "$_id.MonthName",
                    "sales": 1,
                    "orders": 1,
                    "customers": {"$size": "$customers"}
                }
            },
            {"$sort": {"Year": 1, "Month": 1}}
        ]
        monthly_results = await db.shopify_data.aggregate(monthly_pipeline).to_list(100)
        results["monthly_breakdown"] = monthly_results
    
    return results

def format_data_for_llm(data: Dict[str, Any]) -> str:
    """Format MongoDB query results into a readable string for LLM analysis"""
    context_parts = []
    
    # Summary
    summary = data.get("summary", {})
    if summary:
        context_parts.append("=== SUMMARY STATISTICS ===")
        context_parts.append(f"Total Sales: €{summary.get('total_sales', 0):,.2f}")
        context_parts.append(f"Total Orders: {summary.get('total_orders', 0):,}")
        context_parts.append(f"Total Customers: {summary.get('total_customers', 0):,}")
        context_parts.append(f"Average Order Value: €{summary.get('avg_order_value', 0):,.2f}")
        context_parts.append("")
    
    # Customer breakdown
    if data.get("customer_breakdown"):
        context_parts.append("=== NEW VS RETURNING CUSTOMERS ===")
        total_cust_sales = sum(item.get("sales", 0) for item in data["customer_breakdown"])
        for item in data["customer_breakdown"]:
            cust_type = item.get("type", "Unknown")
            sales = item.get("sales", 0)
            orders = item.get("orders", 0)
            customers = item.get("customers", 0)
            percentage = (sales / total_cust_sales * 100) if total_cust_sales > 0 else 0
            context_parts.append(f"{cust_type}: €{sales:,.2f} ({percentage:.1f}% of sales), {orders:,} orders, {customers:,} customers")
        context_parts.append("")
    
    # Channel breakdown
    if data.get("channel_breakdown"):
        context_parts.append("=== SALES BY CHANNEL ===")
        for item in data["channel_breakdown"]:
            channel = item.get("_id", "Unknown")
            sales = item.get("sales", 0)
            orders = item.get("orders", 0)
            context_parts.append(f"{channel}: €{sales:,.2f} ({orders:,} orders)")
        context_parts.append("")
    
    # Geographic breakdown
    if data.get("geographic_breakdown"):
        context_parts.append("=== SALES BY COUNTRY ===")
        for item in data["geographic_breakdown"]:
            country = item.get("_id", "Unknown")
            sales = item.get("sales", 0)
            orders = item.get("orders", 0)
            context_parts.append(f"{country}: €{sales:,.2f} ({orders:,} orders)")
        context_parts.append("")
    
    # Monthly breakdown
    if data.get("monthly_breakdown"):
        context_parts.append("=== MONTHLY TRENDS ===")
        for item in data["monthly_breakdown"]:
            year = item.get("Year", 0)
            month = item.get("MonthName", "")
            sales = item.get("sales", 0)
            orders = item.get("orders", 0)
            customers = item.get("customers", 0)
            context_parts.append(f"{year}-{month}: €{sales:,.2f} ({orders:,} orders, {customers:,} customers)")
        context_parts.append("")
    
    return "\n".join(context_parts)

def generate_recommendations_and_followups(query, ai_response, context_data=None):
    """Generate dynamic recommendations and follow-up questions based on query and response"""
    query_lower = query.lower()
    
    # Extract recommendations from AI response
    recommendations = []
    lines = ai_response.split('\n')
    in_recommendations_section = False
    
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        
        if re.match(r'^\d+[\.\)]\s+', line) or line.startswith('-') or line.startswith('•'):
            in_recommendations_section = True
            rec_text = re.sub(r'^\d+[\.\)]\s*', '', line)
            rec_text = re.sub(r'^[-•]\s*', '', rec_text)
            rec_text = rec_text.strip()
            
            if rec_text and len(rec_text) > 10:
                recommendations.insert(0, rec_text)
                if len(recommendations) >= 5:
                    break
        elif in_recommendations_section and ('recommendation' in line.lower() or 'suggestion' in line.lower()):
            break
    
    if len(recommendations) == 0:
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+[\.\)]\s+', line):
                rec_text = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if rec_text and len(rec_text) > 10:
                    recommendations.append(rec_text)
                    if len(recommendations) >= 5:
                        break
    
    if len(recommendations) == 0:
        recommendations = [
            "Focus on retention programs to increase returning customer rate",
            "Improve new customer onboarding to enhance first-time purchase experience",
            "Create loyalty incentives to boost customer lifetime value"
        ]
    
    # Generate follow-up questions
    if "sales" in query_lower or "revenue" in query_lower:
        follow_up_questions = [
            "Show me sales trends by month",
            "Which channels drive the most sales?",
            "Compare sales performance across regions",
            "What is the average order value trend?"
        ]
    elif "customer" in query_lower or "retention" in query_lower:
        follow_up_questions = [
            "What is the customer lifetime value?",
            "Show me new vs returning customer breakdown",
            "Which customer segments are most valuable?",
            "What is the customer acquisition cost?"
        ]
    elif "channel" in query_lower or "traffic" in query_lower:
        follow_up_questions = [
            "Which channels have the best conversion rates?",
            "Show me channel performance by month",
            "What is the ROI by marketing channel?",
            "Compare channel customer acquisition costs"
        ]
    elif "month" in query_lower or "trend" in query_lower:
        follow_up_questions = [
            "Show me month-over-month growth",
            "What are the seasonal trends?",
            "Compare this month to last month",
            "Which months perform best?"
        ]
    else:
        follow_up_questions = [
            "Show sales overview",
            "Analyze profitability",
            "Customer insights",
            "Channel performance"
        ]
    
    return recommendations[:5], follow_up_questions[:4]

async def process_customer_insights_chat(
    db: AsyncIOMotorDatabase,
    message: str,
    context: Optional[Dict] = None,
    conversation_history: Optional[List] = None,
    chart_title: Optional[str] = None
):
    """Main function to process customer insights chat requests using LLM-powered query understanding"""
    try:
        # Extract preset filters from context
        preset_filters = {}
        if context:
            if 'year' in context or 'selectedYears' in context:
                year_val = context.get('year') or (context.get('selectedYears') or [None])[0]
                if year_val:
                    preset_filters['year'] = int(year_val)
            
            if 'month' in context or 'selectedMonths' in context:
                month_val = context.get('month') or (context.get('selectedMonths') or [None])[0]
                if month_val:
                    month_str = str(month_val).capitalize()
                    month_map = {
                        'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
                        'Apr': 'April', 'May': 'May', 'Jun': 'June',
                        'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
                        'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
                    }
                    if month_str in month_map:
                        month_str = month_map[month_str]
                    preset_filters['month'] = month_str
        
        # Step 1: Use LLM to understand the question and generate query plan
        logger.info(f"🤖 Step 1: Understanding question with LLM...")
        query_plan = await llm_understand_question_and_generate_queries(message, chart_title, context)
        
        # Step 2: Execute MongoDB queries based on the plan
        logger.info(f"📊 Step 2: Executing MongoDB queries...")
        data = await execute_mongodb_queries(db, query_plan, preset_filters)
        
        # Step 3: Format data for LLM analysis
        logger.info(f"📝 Step 3: Formatting data for LLM...")
        data_context = format_data_for_llm(data)
        
        # Step 4: Use LLM to analyze data and generate comprehensive answer
        logger.info(f"💬 Step 4: Generating answer with LLM...")
        
        # Convert conversation history
        conv_history = []
        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, dict):
                    conv_history.append(msg)
                elif hasattr(msg, 'dict'):
                    conv_history.append(msg.dict())
                else:
                    conv_history.append({
                        "role": getattr(msg, 'role', 'user'),
                        "content": getattr(msg, 'content', '')
                    })
        
        # Build comprehensive prompt
        chart_context = f"\n\nChart Context: {chart_title}" if chart_title else ""
        
        full_prompt = f"""Based on the following Shopify customer data, provide a comprehensive analysis answering: "{message}"

{data_context}{chart_context}

Please provide:
1. A detailed analysis of the data
2. Key insights and patterns
3. Specific numbers and percentages
4. 3-5 actionable recommendations
5. Visual suggestions (what charts/tables would help visualize this data)

Be specific, use exact numbers from the data, and provide actionable insights."""

        # Query AI
        response_text = query_perplexity(full_prompt, conv_history if conv_history else None)
        
        # Generate recommendations and follow-up questions
        context_summary = {
            'total_sales': data.get("summary", {}).get("total_sales", 0),
            'total_orders': data.get("summary", {}).get("total_orders", 0),
            'total_customers': data.get("summary", {}).get("total_customers", 0)
        }
        
        recommendations, follow_up_questions = generate_recommendations_and_followups(
            message, response_text, context_summary
        )
        
        # Prepare response
        timestamp = datetime.now().strftime("%I:%M %p IST on %B %d, %Y")
        
        # Convert data to pivot table format for compatibility
        pivot_records = []
        if data.get("customer_breakdown"):
            for item in data["customer_breakdown"]:
                pivot_records.append({
                    "CustomerType": item.get("type", ""),
                    "Total sales": item.get("sales", 0),
                    "Orders": item.get("orders", 0),
                    "Customers": item.get("customers", 0)
                })
        
        return {
            "response": response_text,
            "timestamp": timestamp,
            "context": data_context[:500] + "..." if len(data_context) > 500 else data_context,
            "data": {
                "pivot_table": pivot_records,
                "columns": ["Total sales", "Orders", "Customers"],
                "filters": {},
                "is_trend_query": query_plan.get("analysis_type") == "trend",
                "total_rows": data.get("summary", {}).get("total_customers", 0),
                "chart_title": chart_title,
                "recommendations": recommendations,
                "follow_up_questions": follow_up_questions
            }
        }
    except Exception as e:
        logger.error(f"Error processing customer insights chat: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "response": f"I apologize, but I encountered an error: {str(e)}. Please try again.",
            "timestamp": datetime.now().strftime("%I:%M %p IST on %B %d, %Y"),
            "context": "",
            "data": {}
        }
