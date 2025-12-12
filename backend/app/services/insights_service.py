"""
Service for Insights Chat functionality
MongoDB-based View Insights Chatbot for all screens
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.insights import InsightsChatRequest, InsightsChatResponse
from app.utils.query_builder import build_mongodb_query_from_context, parse_query_from_natural_language
from app.utils.data_context import get_comprehensive_data_context
from app.utils.ai_service import query_perplexity
from app.utils.helpers import safe_float
from datetime import datetime
import logging
import re
import json

logger = logging.getLogger(__name__)

class InsightsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def process_chat(self, request: InsightsChatRequest) -> InsightsChatResponse:
        """
        MongoDB-based View Insights Chatbot for all screens
        Supports: Business Compass, Brands, Customers, Categories, Sales Analysis
        """
        try:
            logger.info(f"📊 View Insights Chat Request - Chart: {request.chart_title}, Message: {request.message[:100]}")
            
            # Extract year from user message if mentioned (e.g., "2025", "sales trend for 2025")
            user_message = request.message or ""
            year_pattern = r'\b(20\d{2})\b'  # Match years like 2023, 2024, 2025
            years_in_message = re.findall(year_pattern, user_message)
            # Convert extracted years to integers and filter valid years (2000-2100)
            requested_years = [int(y) for y in years_in_message if 2000 <= int(y) <= 2100]
            
            # Extract months from user message if mentioned (e.g., "January", "Jan", "March", "Mar")
            month_mapping = {
                'january': 'January', 'jan': 'January',
                'february': 'February', 'feb': 'February',
                'march': 'March', 'mar': 'March',
                'april': 'April', 'apr': 'April',
                'may': 'May',
                'june': 'June', 'jun': 'June',
                'july': 'July', 'jul': 'July',
                'august': 'August', 'aug': 'August',
                'september': 'September', 'sep': 'September', 'sept': 'September',
                'october': 'October', 'oct': 'October',
                'november': 'November', 'nov': 'November',
                'december': 'December', 'dec': 'December'
            }
            user_msg_lower_for_months = user_message.lower()
            requested_months = []
            for month_key, month_full in month_mapping.items():
                # Match whole words only to avoid false positives (e.g., "march" in "marching")
                # Since user_msg_lower_for_months is already lowercase, we don't need IGNORECASE flag
                pattern = r'\b' + re.escape(month_key) + r'\b'
                if re.search(pattern, user_msg_lower_for_months):
                    if month_full not in requested_months:
                        requested_months.append(month_full)
            logger.info(f"📅 Extracted months from message: {requested_months if requested_months else 'None'}")
            
            # Build MongoDB query from context
            context_query = await build_mongodb_query_from_context(request.context or {}, self.db)
            
            # Parse query from natural language message
            parsed_query = await parse_query_from_natural_language(user_message, self.db)
            
            # Merge context query with parsed query (parsed query takes precedence for filters it specifies)
            query = context_query.copy()
            for key, value in parsed_query.items():
                if key in query:
                    # Merge filters (intersect for $in queries)
                    if isinstance(query[key], dict) and '$in' in query[key] and isinstance(value, dict) and '$in' in value:
                        existing_values = query[key]['$in']
                        new_values = value['$in']
                        # Intersect the lists
                        merged_values = [v for v in existing_values if v in new_values] or new_values
                        query[key] = {'$in': merged_values}
                    else:
                        query[key] = value
                else:
                    query[key] = value
            
            # CRITICAL FIX: If both context_query and parsed_query are empty, ensure query is empty
            # This ensures "Top 15 Brands" without filters gets ALL brands
            if not context_query and not parsed_query:
                query = {}
                logger.info("✅ No filters detected - using empty query to get all data")
            
            logger.info(f"🔍 Final MongoDB Query (merged): {query}")
            logger.info(f"📋 Context query: {context_query}")
            logger.info(f"📋 Parsed query: {parsed_query}")
            
            # Verify query will return data
            if query:
                test_count = await self.db.business_data.count_documents(query)
                logger.info(f"📊 Documents matching final query: {test_count}")
                if test_count == 0:
                    logger.warning(f"⚠️ WARNING: Final query returns 0 documents! Query: {query}")
            else:
                test_count = await self.db.business_data.count_documents({})
                logger.info(f"📊 Total documents in database (no filters): {test_count}")
            
            # Verify query doesn't have any unexpected filters
            if query:
                logger.info(f"📊 Query has {len(query)} filter(s): {list(query.keys())}")
            else:
                logger.info(f"📊 Query is empty - will fetch all data (no filters applied)")
            
            # Log query details for debugging
            if query:
                logger.info(f"📊 Query filters: {list(query.keys())}")
                for key, value in query.items():
                    if isinstance(value, dict) and '$in' in value:
                        logger.info(f"  {key}: {len(value['$in'])} values - {value['$in'][:5]}...")
                    else:
                        logger.info(f"  {key}: {value}")
            
            # Get comprehensive data context based on the query
            # Check what type of analysis is requested
            user_msg_lower = user_message.lower()
            chart_title_lower = (request.chart_title or "").lower()
            
            # CRITICAL FIX: If asking FOR brands (not filtering BY brand), remove Brand filter from query
            # This ensures data context shows all brands, not just one
            is_asking_for_brands = any(phrase in user_msg_lower for phrase in [
                'top brands', 'top 15 brands', 'top 10 brands', 'top 5 brands',
                'brands by revenue', 'brands by profit', 'brands by', 'all brands',
                'list brands', 'show brands', 'which brands', 'what brands', 'tell me brands'
            ]) or "brand" in chart_title_lower
            
            # Use a modified query for data context that excludes Brand filter when asking FOR brands
            data_context_query = query.copy() if query else {}
            if is_asking_for_brands and 'Brand' in data_context_query:
                logger.info(f"🔍 Removing Brand filter from data context query (user is asking FOR brands)")
                logger.info(f"🔍 Original query had Brand filter: {data_context_query.get('Brand')}")
                data_context_query = {k: v for k, v in data_context_query.items() if k != 'Brand'}
                logger.info(f"🔍 Data context query after removing Brand filter: {data_context_query}")
            
            # Determine analysis type
            is_comparison = any(word in user_msg_lower for word in ['compare', 'comparison', 'vs', 'versus', 'against'])
            is_quarterly = any(word in user_msg_lower for word in ['quarterly', 'q1', 'q2', 'q3', 'q4', 'quarter'])
            is_monthly = any(word in user_msg_lower for word in ['monthly', 'month', 'by month'])
            is_yearly = any(word in user_msg_lower for word in ['yearly', 'year', 'yoy', 'year over year'])
            is_metrics = any(word in user_msg_lower for word in ['metrics', 'details', 'show me', 'tell me'])
            
            # Get comprehensive data context using the modified query
            # IMPORTANT: Use the modified query (without Brand filter) for data context when asking FOR brands
            logger.info(f"🔍 Query being passed to data context: {data_context_query}")
            try:
                data_context = await get_comprehensive_data_context(
                    data_context_query,  # Use modified query without Brand filter when asking FOR brands
                    user_message,
                    self.db,
                    is_comparison=is_comparison,
                    is_quarterly=is_quarterly,
                    is_monthly=is_monthly,
                    is_yearly=is_yearly,
                    is_metrics=is_metrics
                )
                logger.info(f"📈 Data context length: {len(data_context)} characters")
                logger.info(f"📈 Data context preview: {data_context[:500]}...")
                
                # If data context shows very little data, log a warning
                if "Overall Totals" in data_context:
                    # Extract total revenue from context
                    revenue_match = re.search(r'Total Revenue: (€[\d.]+[kM]?)', data_context)
                    if revenue_match:
                        logger.info(f"📊 Total revenue in data context: {revenue_match.group(1)}")
                    else:
                        logger.warning(f"⚠️ Could not extract total revenue from data context")
            except Exception as e:
                logger.error(f"❌ Error getting data context: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                data_context = f"Error retrieving data: {str(e)}"
            
            # Build conversation history for Perplexity
            conversation_history = []
            if request.conversation_history:
                for msg in request.conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role in ["user", "assistant"]:
                        conversation_history.append({"role": role, "content": content})
            
            # Build comprehensive prompt
            chart_context = f"Chart: {request.chart_title}\n" if request.chart_title else ""
            
            # Check if user asked for a specific year
            year_context = ""
            if years_in_message and requested_years:
                year_context = f"CRITICAL: The user specifically asked about year(s) {', '.join(map(str, requested_years))}. You MUST focus your analysis ONLY on data from these year(s). Do NOT include data from other years unless explicitly requested. "
            
            # Check if user asked for a specific month
            month_context = ""
            if requested_months:
                month_list_str = ', '.join(requested_months)
                month_context = f"CRITICAL: The user specifically asked about month(s) {month_list_str}. You MUST focus your analysis ONLY on data from these month(s). Do NOT include data from other months unless explicitly requested. "
            
            # Enhanced system context for comprehensive queries
            email_context = ""
            if "email" in user_msg_lower or ("write" in user_msg_lower and "email" in user_msg_lower):
                email_context = "CRITICAL: The user is asking for an email. Format your response as a professional business email with: (1) Clear subject line, (2) Professional greeting, (3) Executive summary of key findings, (4) Detailed insights with specific numbers, (5) Actionable recommendations, (6) Professional closing. Keep it concise (around 250 words if specified). "
            
            comparison_context = ""
            if is_comparison:
                comparison_context = "CRITICAL: The user is asking for a comparison. Provide side-by-side analysis with specific numbers, highlight differences, calculate growth rates or changes, and explain what the comparison reveals. "
            
            quarterly_context = ""
            if is_quarterly:
                quarterly_context = "CRITICAL: The user is asking for quarterly data. Break down performance by Q1, Q2, Q3, Q4. Highlight seasonal patterns, quarter-over-quarter changes, and identify which quarters performed best/worst. "
            
            monthly_context = ""
            if is_monthly:
                monthly_context = "CRITICAL: The user is asking for monthly data. Provide month-by-month breakdown, identify peaks and dips, discuss seasonality patterns, and explain what drove monthly variations. "
            
            system_context = (
                "You are Vector AI, a strategic business intelligence analyst for ThriveBrands. "
                "You provide business insights and recommendations to non-technical executives and managers. "
                "CRITICAL: NEVER mention technical terms like 'MongoDB', 'database', 'query', 'aggregation', 'pipeline', 'API', 'system', or any other technical implementation details. "
                "Speak ONLY in business language. Focus on business outcomes, strategies, and actionable insights. "
                "When suggesting data analysis, say 'analyze your sales data' or 'review your performance metrics', NOT 'query the database' or 'use MongoDB'. "
                "When suggesting automation, say 'automate your reporting' or 'set up automated alerts', NOT 'deploy MongoDB-powered analytics' or 'use aggregation framework'. "
                f"{year_context}"
                f"{month_context}"
                f"{email_context}"
                f"{comparison_context}"
                f"{quarterly_context}"
                f"{monthly_context}"
                "CRITICAL: You MUST provide comprehensive analysis for EVERY question, including: "
                "(1) Key insights and patterns you observe in the data, "
                "(2) What these numbers mean for the business, "
                "(3) Specific, actionable recommendations (at least 3-5) with clear 'why' and 'how' for each, "
                "(4) Potential risks or opportunities identified, "
                "(5) Next steps the user should take. "
                "Do NOT just list the data - analyze it, interpret it, and provide strategic guidance. "
                "IMPORTANT: If the user asks for a specific number (e.g., 'top 15 brands', '15 brands'), you MUST provide exactly that number of items in your response. "
                "CRITICAL: Use the EXACT numbers from the data provided to you. Do NOT round, estimate, or modify the numbers. The data contains precise values - use them exactly as shown. "
                "Format monetary values in millions (M) or thousands (k) where appropriate, e.g., €59.0M or €1.6k, and cases as whole numbers. "
                "CRITICAL: Analyze EACH question independently. Do NOT reuse data or insights from previous questions unless the user explicitly asks for a comparison or follow-up. "
                "For every new question, generate fresh analysis based on the current question and the data provided. "
                "IMPORTANT: If the user asks about a specific brand, category, customer, or entity, and that entity only exists in certain years or has limited data availability, you should: "
                "(1) Mention this limitation clearly in your response (e.g., 'Cali Cali brand data is only available for 2023 and 2024'), "
                "(2) Provide analysis based on the available data for those years, and "
                "(3) If relevant, suggest asking about other time periods or entities. "
                "All monetary values are in Euros (€). Be specific, data-driven, and actionable. "
                "Include trends, growth rates (%), and percentage of total revenue where relevant. "
                "For underperformers, identify the lowest performers with specific numbers. "
                "When comparing years, quarters, or periods, calculate and highlight the percentage change or growth rate. "
                "When analyzing trends, identify patterns, seasonality, peaks, dips, and explain potential drivers. "
                "Always provide 3-5 specific, actionable recommendations with clear 'why' and 'how' for each. "
                "Use conversation history for context in follow-ups. "
                "Keep it engaging and provide comprehensive analysis in plain business language that any executive can understand."
            )
            
            # Build user prompt with data context
            user_prompt = f"{chart_context}\n\nBusiness Data:\n{data_context}\n\nUser Question: {request.message}"
            
            logger.info(f"🤖 Sending to AI - Prompt length: {len(user_prompt)} characters")
            logger.info(f"🤖 System context length: {len(system_context)} characters")
            
            # Query Perplexity API with custom system message to ensure non-technical language
            try:
                ai_response = await query_perplexity(user_prompt, conversation_history, custom_system_message=system_context)
                logger.info(f"✅ AI Response received - Length: {len(ai_response)} characters")
            except Exception as e:
                logger.error(f"❌ Error querying Perplexity: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                ai_response = f"I apologize, but I encountered an error while processing your request. Please try rephrasing your question or contact support if the issue persists. Error: {str(e)}"
            
            # Get pivot table data for visualization - make it relevant to the question
            pivot_table = await self._generate_pivot_table(request, query, user_msg_lower, chart_title_lower)
            
            # Get total row count
            total_rows = await self.db.business_data.count_documents(query) if query else await self.db.business_data.count_documents({})
            
            # Generate dynamic follow-up questions based on the question asked
            follow_up_questions = self._generate_follow_up_questions(user_msg_lower, chart_title_lower)
            
            # Format timestamp
            timestamp = datetime.now().strftime("%I:%M %p IST on %B %d, %Y")
            
            return InsightsChatResponse(
                response=ai_response,
                timestamp=timestamp,
                context=data_context,
                data={
                    "pivot_table": pivot_table,
                    "columns": ["Revenue", "Gross_Profit", "Units"],
                    "filters": query,
                    "is_trend_query": "trend" in (request.message or "").lower(),
                    "is_loser_query": any(word in (request.message or "").lower() for word in ["worst", "lowest", "loser", "least"]),
                    "total_rows": total_rows,
                    "follow_up_questions": follow_up_questions
                }
            )
            
        except Exception as e:
            logger.error(f"View Insights Chat error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Error processing view insights chat: {str(e)}")
    
    async def _generate_pivot_table(
        self,
        request: InsightsChatRequest,
        query: dict,
        user_msg_lower: str,
        chart_title_lower: str
    ) -> list:
        """Generate pivot table data based on the question type"""
        pivot_table = []
        try:
            # Log for debugging
            logger.info(f"Pivot table generation - Message: {request.message}, Chart Title: {request.chart_title}")
            
            # Determine what data to show based on the question
            # Check for brand questions FIRST (most common case)
            if "brand" in user_msg_lower or "brand" in chart_title_lower:
                logger.info("Detected BRAND question - generating brand-level pivot table")
                logger.info(f"🔍 Query being used for brand pivot: {query}")
                
                # Build match stage - ensure we're not accidentally filtering out data
                # CRITICAL: When asking "Top 15 Brands", don't filter by Brand unless explicitly requested
                match_conditions = {}
                if query:
                    # Only copy non-Brand filters (Year, Month, Business, Channel, Category, Customer)
                    # Don't copy Brand filter unless the user explicitly asked for a specific brand
                    for key, value in query.items():
                        if key != 'Brand':  # Don't filter by Brand when asking FOR brands
                            match_conditions[key] = value
                
                # Filter out null brands (but don't restrict to specific brands unless explicitly requested)
                if 'Brand' not in match_conditions:
                    match_conditions["Brand"] = {"$exists": True, "$nin": [None, "", "Unknown", "null", "None"]}
                
                match_stage = {"$match": match_conditions}
                logger.info(f"🔍 Match stage for brand pivot: {match_stage}")
                logger.info(f"🔍 Original query had Brand filter: {'Brand' in (query or {})}")
                
                # Test query first to see how many documents match
                test_count = await self.db.business_data.count_documents(match_conditions)
                logger.info(f"📊 Documents matching brand query: {test_count}")
                
                # If count is suspiciously low, log a warning
                if test_count < 1000:
                    logger.warning(f"⚠️ WARNING: Only {test_count} documents match brand query. This might be too restrictive!")
                    # Test with empty query to see total documents
                    total_docs = await self.db.business_data.count_documents({})
                    logger.info(f"📊 Total documents in database: {total_docs}")
                
                # Detect how many brands requested - CRITICAL: Prioritize user message over chart title
                # CRITICAL: Check user message FIRST, then chart title as fallback
                # This ensures "Top 10" in message overrides "Top 15" in chart title
                current_message = (request.message or "").lower()
                chart_title_lower = (request.chart_title or "").lower()
                
                brand_limit = 20  # Default
                
                # First, try to find number in user message
                message_numbers = re.findall(r'\b(\d+)\b', current_message)
                if message_numbers:
                    try:
                        valid_message_numbers = [int(num) for num in message_numbers if 1 <= int(num) <= 50]
                        if valid_message_numbers:
                            brand_limit = max(valid_message_numbers)
                            logger.info(f"✅ Detected brand limit from USER MESSAGE: {brand_limit} (message: '{request.message}')")
                    except:
                        pass
                
                # If no number in message, check chart title
                if brand_limit == 20:  # Still default, check chart title
                    chart_numbers = re.findall(r'\b(\d+)\b', chart_title_lower)
                    if chart_numbers:
                        try:
                            valid_chart_numbers = [int(num) for num in chart_numbers if 1 <= int(num) <= 50]
                            if valid_chart_numbers:
                                brand_limit = max(valid_chart_numbers)
                                logger.info(f"✅ Detected brand limit from CHART TITLE: {brand_limit} (chart: '{request.chart_title}')")
                        except:
                            pass
                
                if brand_limit == 20:
                    logger.info(f"ℹ️ No specific limit detected, using default: {brand_limit}")
                
                # Log the detected limit for debugging
                logger.info(f"Brand pivot table: Final limit = {brand_limit} for message: '{request.message}'")
                logger.info(f"🔍 This pivot table will show top {brand_limit} brands (regenerated for this question)")
                
                pipeline_pivot = [
                    match_stage,
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
                    {"$limit": brand_limit + 10}  # Get extra to ensure we have enough after filtering
                ]
                
                logger.info(f"📊 Brand pipeline: {json.dumps(pipeline_pivot, default=str)[:300]}...")
                
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(brand_limit + 10)  # Get extra to filter nulls
                logger.info(f"📊 Brand pivot results count: {len(pivot_results)} (will show top {brand_limit})")
                
                # CRITICAL: Reset pivot_table for this question to ensure fresh data
                # Only populate with the exact number requested (brand_limit)
                brands_added = 0
                for item in pivot_results:
                    if brands_added >= brand_limit:
                        logger.info(f"✅ Reached requested limit of {brand_limit} brands, stopping")
                        break
                    brand_name = str(item.get("_id", ""))
                    if brand_name and brand_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Brand": brand_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Units": safe_float(item.get("Units", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
                            brands_added += 1
                            logger.info(f"  Added brand {brands_added}/{brand_limit}: {brand_name} - Revenue: {revenue}")
                            # Stop when we reach the requested limit
                            if len(pivot_table) >= brand_limit:
                                logger.info(f"Brand pivot table: Reached limit of {brand_limit}, stopping")
                                break
                
                logger.info(f"📊 Final brand pivot table has {len(pivot_table)} brands")
            
            # Check for trend questions (must have explicit trend keywords)
            elif ("trend" in user_msg_lower or "monthly" in user_msg_lower or "yearly" in user_msg_lower or "over time" in user_msg_lower or 
                  "trend" in chart_title_lower or "monthly" in chart_title_lower or "yearly" in chart_title_lower or "ytd" in chart_title_lower):
                logger.info("Detected TREND question - generating time-based pivot table")
                # User asked about trends - show time-based data
                match_stage = {"$match": query} if query else {"$match": {}}
                
                # If user asked for a specific year, show monthly trend for that year
                # Otherwise, determine if monthly or yearly trend
                if "year" in query and "$in" in query.get("Year", {}):
                    # User specified a year - show monthly data for that year
                    logger.info(f"User specified year(s) {query['Year']['$in']} - showing monthly trend")
                    pipeline_pivot = [
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
                    pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(12)
                    for item in pivot_results:
                        month_name = str(item.get("_id", ""))
                        if month_name and month_name.lower() not in ["unknown", "none", "", "null"]:
                            revenue = safe_float(item.get("Revenue", 0))
                            if revenue > 0:
                                pivot_row = {
                                    "Month_Name": month_name,
                                    "Revenue": revenue,
                                    "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                    "Units": safe_float(item.get("Units", 0))
                                }
                                pivot_table.append(pivot_row)
                elif "month" in user_msg_lower or "monthly" in user_msg_lower:
                    pipeline_pivot = [
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
                    pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(12)
                    for item in pivot_results:
                        month_name = str(item.get("_id", ""))
                        if month_name and month_name.lower() not in ["unknown", "none", "", "null"]:
                            revenue = safe_float(item.get("Revenue", 0))
                            if revenue > 0:
                                pivot_row = {
                                    "Month_Name": month_name,
                                    "Revenue": revenue,
                                    "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                    "Units": safe_float(item.get("Units", 0))
                                }
                                pivot_table.append(pivot_row)
                else:
                    # Yearly trend - show only requested year(s) or all years if none specified
                    pipeline_pivot = [
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
                    pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(10)
                    for item in pivot_results:
                        year_value = item.get("_id", 0)
                        # Handle both int and float year values
                        if isinstance(year_value, float):
                            year = int(year_value) if year_value > 0 else 0
                        else:
                            year = int(year_value) if year_value else 0
                        
                        if year > 2000 and year < 2100:  # Valid year range
                            revenue = safe_float(item.get("Revenue", 0))
                            if revenue > 0:
                                pivot_row = {
                                    "Year": year,  # Store as integer, not formatted
                                    "Revenue": revenue,
                                    "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                    "Units": safe_float(item.get("Units", 0))
                                }
                                pivot_table.append(pivot_row)
            
            elif "customer" in user_msg_lower or "customer" in chart_title_lower:
                logger.info("Detected CUSTOMER question - generating customer-level pivot table")
                # User asked about customers - show customer-level aggregated data
                match_stage = {"$match": query} if query else {"$match": {}}
                pipeline_pivot = [
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
                    {"$limit": 15}
                ]
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(15)
                for item in pivot_results:
                    customer_name = str(item.get("_id", ""))
                    if customer_name and customer_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Customer": customer_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Units": safe_float(item.get("Units", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
            
            elif "category" in user_msg_lower or "category" in chart_title_lower:
                logger.info("Detected CATEGORY question - generating category-level pivot table")
                # User asked about categories - show category-level aggregated data
                match_stage = {"$match": query} if query else {"$match": {}}
                pipeline_pivot = [
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
                    {"$limit": 15}
                ]
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(15)
                for item in pivot_results:
                    category_name = str(item.get("_id", ""))
                    if category_name and category_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Category": category_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Units": safe_float(item.get("Units", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
            
            elif "channel" in user_msg_lower or "sales" in user_msg_lower or "channel" in chart_title_lower:
                logger.info("Detected CHANNEL question - generating channel-level pivot table")
                # User asked about channels or sales - show channel-level aggregated data
                match_stage = {"$match": query} if query else {"$match": {}}
                pipeline_pivot = [
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
                    {"$limit": 15}
                ]
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(15)
                for item in pivot_results:
                    channel_name = str(item.get("_id", ""))
                    if channel_name and channel_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Channel": channel_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Units": safe_float(item.get("Units", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
            
            elif "business" in user_msg_lower or "compass" in user_msg_lower:
                # User asked about business - show business-level aggregated data
                match_stage = {"$match": query} if query else {"$match": {}}
                pipeline_pivot = [
                    match_stage,
                    {
                        "$group": {
                            "_id": "$Business",
                            "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                            "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                            "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                        }
                    },
                    {"$sort": {"Revenue": -1}},
                    {"$limit": 15}
                ]
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(15)
                for item in pivot_results:
                    business_name = str(item.get("_id", ""))
                    if business_name and business_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Business": business_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Units": safe_float(item.get("Units", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
            
            else:
                # Default: show brand-level data (most common)
                # But check if chart_title gives us a hint
                logger.info(f"Using DEFAULT (brand) pivot table - Message: {request.message}, Chart: {request.chart_title}")
                match_stage = {"$match": query} if query else {"$match": {}}
                if 'Brand' not in match_stage["$match"]:
                    match_stage["$match"]["Brand"] = {"$exists": True, "$nin": [None, "", "Unknown", "null", "None"]}
                
                # Detect how many brands requested for pivot table
                numbers = re.findall(r'\b(\d+)\b', user_msg_lower + " " + chart_title_lower)
                pivot_limit = 15  # Default
                if numbers:
                    try:
                        valid_numbers = [int(num) for num in numbers if 1 <= int(num) <= 50]
                        if valid_numbers:
                            pivot_limit = max(valid_numbers)
                    except:
                        pass
                
                pipeline_pivot = [
                    match_stage,
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
                    {"$limit": pivot_limit + 5}  # Get extra to filter nulls
                ]
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(pivot_limit + 5)
                for item in pivot_results:
                    brand_name = str(item.get("_id", ""))
                    if brand_name and brand_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Brand": brand_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Units": safe_float(item.get("Units", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
                            # Stop when we reach the requested limit
                            if len(pivot_table) >= pivot_limit:
                                break
        except Exception as e:
            logger.error(f"Error building pivot table: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return pivot_table
    
    def _generate_follow_up_questions(self, user_msg_lower: str, chart_title_lower: str) -> list:
        """Generate dynamic follow-up questions based on the question asked"""
        follow_up_questions = []
        
        # Brand-related questions
        if "brand" in user_msg_lower or "brand" in chart_title_lower:
            if "top" in user_msg_lower and any(str(i) in user_msg_lower for i in range(1, 21)):
                # User asked for top N brands
                follow_up_questions = [
                    "Show me the profit margins for these brands",
                    "Which brands have the highest profit margins?",
                    "Compare revenue vs profit for top brands",
                    "What are the cases sold for each brand?",
                    "Show me brand performance trends"
                ]
            elif "margin" in user_msg_lower or "profit" in user_msg_lower:
                follow_up_questions = [
                    "Which brands have the highest revenue?",
                    "Show me total cases sold by brand",
                    "Compare brand performance across channels",
                    "What are the top performing brands?",
                    "Show brand revenue trends"
                ]
            else:
                follow_up_questions = [
                    "Which brands have the highest profit margins?",
                    "Show me revenue vs profit comparison",
                    "What are the cases sold for each brand?",
                    "Compare top brands performance",
                    "Show brand trends over time"
                ]
        
        # Customer-related questions
        elif "customer" in user_msg_lower or "customer" in chart_title_lower:
            follow_up_questions = [
                "Which customers generate the most revenue?",
                "Show customer profit margins",
                "Compare customer performance",
                "What are the top customers by units?",
                "Show customer trends"
            ]
        
        # Category-related questions
        elif "category" in user_msg_lower or "category" in chart_title_lower:
            follow_up_questions = [
                "Which categories have the highest revenue?",
                "Show category profit margins",
                "Compare category performance",
                "What are the top categories by units?",
                "Show category trends"
            ]
        
        # Channel/Sales questions
        elif "channel" in user_msg_lower or "sales" in user_msg_lower or "channel" in chart_title_lower:
            follow_up_questions = [
                "Which channels generate the most revenue?",
                "Show channel profit margins",
                "Compare channel performance",
                "What are the sales trends by channel?",
                "Show channel distribution"
            ]
        
        # Trend questions
        elif "trend" in user_msg_lower or "monthly" in user_msg_lower or "yearly" in user_msg_lower:
            follow_up_questions = [
                "Show me the top performers",
                "What are the profit margins?",
                "Compare this period to previous periods",
                "Show me the breakdown by category",
                "What are the key insights?"
            ]
        
        # Business/Compass questions
        elif "business" in user_msg_lower or "compass" in user_msg_lower:
            follow_up_questions = [
                "Show me top brands",
                "What are the customer insights?",
                "Show channel performance",
                "Compare business segments",
                "What are the key trends?"
            ]
        
        # Default follow-up questions
        else:
            follow_up_questions = [
                "Show me top brands by revenue",
                "Analyze profit margins",
                "Show customer performance",
                "Compare channel performance",
                "What are the key trends?"
            ]
        
        return follow_up_questions

