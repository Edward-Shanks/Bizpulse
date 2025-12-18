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
from typing import Optional, List
import logging
import re
import json

logger = logging.getLogger(__name__)

class InsightsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def _check_question_clarity(self, user_message: str, chart_title: Optional[str] = None) -> tuple[bool, List[str]]:
        """
        Check if a question is clear or needs clarification.
        Returns (is_clear: bool, suggested_questions: List[str])
        """
        # Pre-check: Skip LLM check for obviously clear questions
        user_msg_lower = user_message.lower().strip()
        
        # Patterns that indicate a CLEAR question (skip LLM check)
        # Also include patterns for suggested questions (which are always well-formed)
        clear_patterns = [
            r'top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers|channel|channels)',
            r'show\s+me\s+top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers)',
            r'tell\s+me\s+top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers)',
            r'compare\s+(brand|brands|business|businesses|category|categories)\s+',
            r'all\s+(brand|brands|business|businesses|category|categories|customer|customers)',
            r'tell\s+me\s+about\s+all\s+(brand|brands|business|businesses|category|categories)',
            r'show\s+me\s+all\s+(brand|brands|business|businesses|category|categories)',
            # Board summary and report questions are always clear
            r'write\s+(me\s+)?(the\s+)?(a\s+)?(comprehensive\s+)?(board\s+)?summary',
            r'write\s+(me\s+)?(the\s+)?(a\s+)?(comprehensive\s+)?(board\s+)?summary\s+for',
            r'write\s+(me\s+)?(the\s+)?(a\s+)?(comprehensive\s+)?(board\s+)?summary\s+for\s+the\s+month',
            r'board\s+summary\s+for',
            r'board\s+summary\s+for\s+the\s+month',
            r'provide\s+(a\s+)?(board\s+)?summary',
            r'create\s+(a\s+)?(comprehensive\s+)?(board\s+)?summary',
            r'summarize\s+key',
            r'draft\s+(a\s+)?(board\s+)?(level\s+)?summary',
            r'generate\s+(a\s+)?(board\s+)?summary',
            r'board\s+summary',
            r'executive\s+summary',
            r'monthly\s+summary',
            # Email and report generation questions are clear if they mention business data context
            r'draft\s+(an\s+)?(a\s+)?email',
            r'write\s+(me\s+)?(an\s+)?(a\s+)?email',
            r'create\s+(an\s+)?(a\s+)?email',
            r'generate\s+(an\s+)?(a\s+)?email',
            r'focusing\s+on\s+key',
            r'highlighting\s+(top\s+)?(kpis?|business|performance)',
            r'covering\s+(sales|customer|operational|marketing)',
            r'including\s+(year|comparisons|achievements)',
            r'with\s+(highlights|insights|recommendations)',
            r'emphasizing\s+(hr|employee|metrics)',
        ]
        
        for pattern in clear_patterns:
            if re.search(pattern, user_msg_lower):
                logger.info(f"✅ Question matches clear pattern: '{user_message}' - skipping clarification check")
                return True, []  # Question is clear, no suggestions needed
        
        try:
            # System prompt for question clarity analysis
            clarity_system_prompt = (
                "You are a question clarity analyzer for a BUSINESS INTELLIGENCE chatbot. "
                "This chatbot ONLY answers questions about BUSINESS DATA: revenue, profit, units, margins, brands, businesses, categories, customers, channels, SKUs, sub-categories. "
                "It does NOT answer questions about: global news, world events, politics, elections, wars, conflicts, natural disasters, economics, international relations, or any non-business topics. "
                "Your job is to determine if a user's question is clear and unambiguous, or if it needs clarification. "
                ""
                "A question is UNCLEAR if it has: "
                "- Poor grammar or sentence structure that makes intent ambiguous "
                "- Missing key information (e.g., 'tell me business' without specifying what about business) "
                "- Ambiguous phrasing (e.g., 'top business' could mean top 10, top 5, or all businesses) "
                "- Typos or misspellings that make the question unclear "
                "- Vague requests without specific entity or metric "
                "- Too short or incomplete (e.g., 'tell me brands' - needs clarification: all brands? top brands? compare brands?) "
                "- Lacks specificity about what information is needed (e.g., 'brands' alone doesn't specify if user wants all, top, comparison, performance, etc.) "
                ""
                "A question is CLEAR if it: "
                "- Has proper grammar and clear intent "
                "- Specifies what entity (business, brand, category, etc.) "
                "- Specifies what information is needed (revenue, profit, comparison, etc.) "
                "- Is well-formed and unambiguous "
                "- Contains specific requests like 'top 10', 'top 5', 'all', 'compare', 'show me', 'tell me about' "
                "- Examples of CLEAR questions: 'tell me top 10 brands', 'show me all businesses', 'compare brands', 'tell me about brand performance', 'draft an email about November 2025 business performance' "
                ""
                "CRITICAL: Questions like 'tell me top 10 brands', 'show me top 10 brands by revenue', 'draft an email about November 2025', 'write me the board summary for November 2025' are CLEAR and should NOT need clarification. "
                "Only mark as unclear if the question is truly ambiguous or missing critical information about BUSINESS DATA."
                ""
                "If the question is UNCLEAR, you MUST generate EXACTLY 5-6 clarified versions that cover different possible interpretations. "
                "Each suggested question MUST: "
                "- Be about BUSINESS DATA ONLY (revenue, profit, units, margins, brands, businesses, categories, customers, channels) "
                "- Reference business entities (brands, businesses, categories, customers, channels) "
                "- Reference business metrics (revenue, profit, units, margins, sales, performance) "
                "- Reference business time periods (years: 2023, 2024, 2025; months: January through December) "
                "- NEVER suggest questions about: global news, world events, politics, elections, wars, conflicts, natural disasters, economics, international relations "
                "- Be actionable and specific (e.g., 'Tell me about all brands by revenue and profit', 'Show me top 10 brands by revenue', 'Compare all brands by margin', 'Draft an email summarizing November 2025 business performance') "
                ""
                "CRITICAL: If is_clear is false, you MUST provide 5-6 suggested questions. Never return an empty array."
                ""
                "Respond ONLY with a JSON object in this exact format: "
                '{"is_clear": true/false, "suggested_questions": ["question1", "question2", "question3", "question4", "question5", "question6"]}'
                ""
                "If is_clear is true, suggested_questions should be an empty array []. "
                "If is_clear is false, suggested_questions MUST contain exactly 5-6 clarified questions - NEVER return an empty array."
            )
            
            # Build the prompt
            chart_context = f"Chart context: {chart_title}\n" if chart_title else ""
            clarity_prompt = (
                f"{chart_context}"
                f"User question: {user_message}\n\n"
                f"Analyze this question and determine if it needs clarification. "
                f"If unclear, suggest 5-6 well-formed clarified versions."
            )
            
            # Call LLM for clarity check
            clarity_response = await query_perplexity(
                clarity_prompt,
                conversation_history=None,
                custom_system_message=clarity_system_prompt
            )
            
            # Parse JSON response
            try:
                # Extract JSON from response (might have markdown code blocks)
                import json
                # Try to find JSON in the response
                json_start = clarity_response.find('{')
                json_end = clarity_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = clarity_response[json_start:json_end]
                    clarity_data = json.loads(json_str)
                    
                    is_clear = clarity_data.get('is_clear', True)
                    suggested_questions = clarity_data.get('suggested_questions', [])
                    
                    # Ensure suggested_questions is a list
                    if not isinstance(suggested_questions, list):
                        suggested_questions = []
                    
                    # If marked as unclear but no suggestions, log warning
                    if not is_clear and len(suggested_questions) == 0:
                        logger.warning(f"⚠️ LLM marked question as unclear but returned empty suggestions. Question: '{user_message}'")
                    
                    logger.info(f"🔍 Question clarity check: is_clear={is_clear}, suggestions={len(suggested_questions)}")
                    if suggested_questions:
                        logger.info(f"🔍 Suggested questions from LLM: {suggested_questions}")
                    return is_clear, suggested_questions
                else:
                    # If no JSON found, assume question is clear
                    logger.warning(f"⚠️ Could not parse clarity response as JSON, assuming clear: {clarity_response[:100]}")
                    return True, []
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error parsing clarity JSON: {e}, response: {clarity_response[:200]}")
                # If parsing fails, assume question is clear to avoid blocking
                return True, []
                
        except Exception as e:
            logger.error(f"❌ Error checking question clarity: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # On error, assume question is clear to avoid blocking
            return True, []

    async def process_chat(self, request: InsightsChatRequest) -> InsightsChatResponse:
        """
        MongoDB-based View Insights Chatbot for all screens
        Supports: Business Compass, Brands, Customers, Categories, Sales Analysis
        """
        try:
            logger.info(f"📊 View Insights Chat Request - Chart: {request.chart_title}, Message: {request.message[:100]}")
            
            user_message = request.message or ""
            
            # STEP 1: Check if question needs clarification
            is_clear, suggested_questions = await self._check_question_clarity(user_message, request.chart_title)
            
            # If question is unclear but no suggestions were generated, create fallback suggestions
            if not is_clear and not suggested_questions:
                logger.warning(f"⚠️ Question marked as unclear but no suggestions generated. Creating fallback suggestions.")
                # Generate fallback suggestions based on common patterns
                user_msg_lower = user_message.lower()
                fallback_suggestions = []
                
                # Detect entity type - ALL suggestions MUST be about business data only
                if 'brand' in user_msg_lower or 'brands' in user_msg_lower:
                    fallback_suggestions = [
                        "Tell me about all brands by revenue and profit",
                        "Show me the top 10 brands by revenue",
                        "Compare all brands by revenue and margin",
                        "Tell me about brand performance by revenue and profit margin",
                        "Show me brand rankings by revenue",
                        "Tell me about brand revenue, profit, and units"
                    ]
                elif 'business' in user_msg_lower or 'businesses' in user_msg_lower:
                    fallback_suggestions = [
                        "Tell me about all businesses by revenue and profit",
                        "Show me the top 10 businesses by revenue",
                        "Compare all businesses by revenue and margin",
                        "Tell me about business performance by revenue and profit margin",
                        "Show me business rankings by revenue",
                        "Tell me about business revenue, profit, and units"
                    ]
                elif 'category' in user_msg_lower or 'categories' in user_msg_lower:
                    fallback_suggestions = [
                        "Tell me about all categories by revenue and profit",
                        "Show me the top 10 categories by revenue",
                        "Compare all categories by revenue and margin",
                        "Tell me about category performance by revenue and profit margin",
                        "Show me category rankings by revenue",
                        "Tell me about category revenue, profit, and units"
                    ]
                elif 'customer' in user_msg_lower or 'customers' in user_msg_lower:
                    fallback_suggestions = [
                        "Tell me about all customers by revenue and profit",
                        "Show me the top 10 customers by revenue",
                        "Compare all customers by revenue and margin",
                        "Tell me about customer performance by revenue and profit margin",
                        "Show me customer rankings by revenue",
                        "Tell me about customer revenue, profit, and units"
                    ]
                elif 'email' in user_msg_lower or 'draft' in user_msg_lower:
                    # Email-related questions should be about business data
                    fallback_suggestions = [
                        "Draft an email summarizing November 2025 business performance",
                        "Write an email about business revenue and profit for November 2025",
                        "Create an email highlighting key business metrics for November 2025",
                        "Generate an email with business performance summary for November 2025",
                        "Draft a business performance email for November 2025",
                        "Write an email about top business KPIs for November 2025"
                    ]
                else:
                    # Generic fallback - ensure all are business-related
                    fallback_suggestions = [
                        f"Tell me about all {user_message} by revenue and profit",
                        f"Show me the top 10 {user_message} by revenue",
                        f"Compare all {user_message} by revenue and margin",
                        f"Tell me about {user_message} performance by revenue and profit margin",
                        f"Show me {user_message} rankings by revenue",
                        f"Tell me about {user_message} revenue, profit, and units"
                    ]
                
                suggested_questions = fallback_suggestions[:6]  # Limit to 6
                logger.info(f"✅ Generated {len(suggested_questions)} fallback suggestions: {suggested_questions}")
            
            # Return clarification response if question is unclear (with or without suggestions)
            if not is_clear:
                # Safety check: if still no suggestions, generate basic ones
                if not suggested_questions or len(suggested_questions) == 0:
                    logger.error(f"❌ CRITICAL: Question marked unclear but no suggestions available! Generating emergency suggestions. Question: '{user_message}'")
                    user_msg_lower = user_message.lower()
                    if 'brand' in user_msg_lower or 'brands' in user_msg_lower:
                        suggested_questions = [
                            "Tell me about all brands by revenue and profit",
                            "Show me the top 10 brands by revenue",
                            "Compare all brands by revenue and margin",
                            "Tell me about brand performance by revenue and profit margin",
                            "Show me brand rankings by revenue",
                            "Tell me about brand revenue, profit, and units"
                        ]
                    elif 'business' in user_msg_lower or 'businesses' in user_msg_lower:
                        suggested_questions = [
                            "Tell me about all businesses by revenue and profit",
                            "Show me the top 10 businesses by revenue",
                            "Compare all businesses by revenue and margin",
                            "Tell me about business performance by revenue and profit margin",
                            "Show me business rankings by revenue",
                            "Tell me about business revenue, profit, and units"
                        ]
                    elif 'email' in user_msg_lower or 'draft' in user_msg_lower:
                        suggested_questions = [
                            "Draft an email summarizing November 2025 business performance",
                            "Write an email about business revenue and profit for November 2025",
                            "Create an email highlighting key business metrics for November 2025",
                            "Generate an email with business performance summary for November 2025",
                            "Draft a business performance email for November 2025",
                            "Write an email about top business KPIs for November 2025"
                        ]
                    else:
                        suggested_questions = [
                            f"Tell me about all {user_message} by revenue and profit",
                            f"Show me the top 10 {user_message} by revenue",
                            f"Compare all {user_message} by revenue and margin",
                            f"Tell me about {user_message} performance by revenue and profit margin",
                            f"Show me {user_message} rankings by revenue",
                            f"Tell me about {user_message} revenue, profit, and units"
                        ]
                    logger.info(f"✅ Generated emergency suggestions: {suggested_questions}")
                
                # Always return clarification when unclear
                logger.info(f"❓ Question needs clarification. Returning {len(suggested_questions)} suggestions: {suggested_questions}")
                return InsightsChatResponse(
                    response=(
                        "I want to make sure I understand your question correctly. "
                        "Could you please select one of these clarified versions, or rewrite your question?"
                    ),
                    needs_clarification=True,
                    suggested_questions=suggested_questions,
                    data={}
                )
            
            # STEP 2: Process the question normally if it's clear
            # CRITICAL: Check for "across years" BEFORE extracting years
            # If user wants "across years", we should NOT filter by specific years
            user_msg_lower_for_years = user_message.lower()
            is_across_years = (
                any(phrase in user_msg_lower_for_years for phrase in [
                    'across years', 'across all years', 'all years', 'year over year', 'yoy'
                ]) or
                re.search(r'compare.*across\s+years?', user_msg_lower_for_years) is not None
            )
            
            # Extract year from user message if mentioned (e.g., "2025", "sales trend for 2025")
            # BUT skip if "across years" is mentioned (user wants all years)
            requested_years = []
            if not is_across_years:
                year_pattern = r'\b(20\d{2})\b'  # Match years like 2023, 2024, 2025
                years_in_message = re.findall(year_pattern, user_message)
                # Convert extracted years to integers and filter valid years (2000-2100)
                requested_years = [int(y) for y in years_in_message if 2000 <= int(y) <= 2100]
            else:
                logger.info("📅 User asked for 'across years' - will NOT filter by specific years")
                years_in_message = []  # Don't extract years if comparing across years
            
            # Extract months from user message if mentioned (e.g., "January", "Jan", "March", "Mar")
            # CRITICAL: Database stores months as full names (January, February, etc.) AND abbreviations (Jan, Feb, etc.)
            # We need to check both formats to ensure we match the data
            month_mapping = {
                'january': ['January', 'Jan'], 'jan': ['January', 'Jan'],
                'february': ['February', 'Feb'], 'feb': ['February', 'Feb'],
                'march': ['March', 'Mar'], 'mar': ['March', 'Mar'],
                'april': ['April', 'Apr'], 'apr': ['April', 'Apr'],
                'may': ['May'],
                'june': ['June', 'Jun'], 'jun': ['June', 'Jun'],
                'july': ['July', 'Jul'], 'jul': ['July', 'Jul'],
                'august': ['August', 'Aug'], 'aug': ['August', 'Aug'],
                'september': ['September', 'Sep', 'Sept'], 'sep': ['September', 'Sep', 'Sept'], 'sept': ['September', 'Sep', 'Sept'],
                'october': ['October', 'Oct'], 'oct': ['October', 'Oct'],
                'november': ['November', 'Nov'], 'nov': ['November', 'Nov'],
                'december': ['December', 'Dec'], 'dec': ['December', 'Dec']
            }
            user_msg_lower_for_months = user_message.lower()
            requested_months = []
            for month_key, month_variants in month_mapping.items():
                # Match whole words only to avoid false positives (e.g., "march" in "marching")
                pattern = r'\b' + re.escape(month_key) + r'\b'
                if re.search(pattern, user_msg_lower_for_months):
                    # Add all possible month formats to ensure we match database
                    for month_variant in month_variants:
                        if month_variant not in requested_months:
                            requested_months.append(month_variant)
            logger.info(f"📅 Extracted months from message (with all variants): {requested_months if requested_months else 'None'}")
            
            # CRITICAL: Detect "all business" queries BEFORE building queries
            # This ensures we don't add Business filter from context when user wants all businesses
            user_msg_lower = user_message.lower()
            # Detect "all business" or "top X business" queries - these should show all businesses
            is_asking_for_all_businesses = any(phrase in user_msg_lower for phrase in [
                'all business', 'all businesses', 'every business', 'every businesses',
                'show all business', 'show all businesses', 'list all business', 'list all businesses',
                'all business in', 'all businesses in', 'all business data', 'all businesses data',
                'tell me about all business', 'tell me about all businesses', 'details about all business',
                'details about all businesses', 'information about all business', 'information about all businesses',
                'top business', 'top businesses', 'top 10 business', 'top 10 businesses', 'top 15 business', 'top 15 businesses',
                'top 5 business', 'top 5 businesses', 'top 20 business', 'top 20 businesses',
                'best business', 'best businesses', 'leading business', 'leading businesses',
                'top business by', 'top businesses by', 'rank business', 'rank businesses',
                'business ranking', 'businesses ranking', 'top performing business', 'top performing businesses'
            ]) or re.search(r'top\s+\d+\s+business', user_msg_lower) or re.search(r'top\s+\d+\s+businesses', user_msg_lower)
            
            # Build MongoDB query from context
            # If asking for all businesses, remove Business filter from context BEFORE building query
            context_for_query = request.context.copy() if request.context else {}
            if is_asking_for_all_businesses:
                logger.info(f"🔍✅ DETECTED: User asked for all/top businesses - is_asking_for_all_businesses=True")
                logger.info(f"🔍 User message: {user_message}")
                logger.info(f"🔍 Removing Business filter from context before building query")
                if 'selectedBusinesses' in context_for_query:
                    logger.info(f"🔍 Removed selectedBusinesses from context: {context_for_query.get('selectedBusinesses')}")
                    del context_for_query['selectedBusinesses']
                if 'business' in context_for_query:
                    logger.info(f"🔍 Removed business from context: {context_for_query.get('business')}")
                    del context_for_query['business']
            else:
                logger.info(f"🔍❌ NOT DETECTED: is_asking_for_all_businesses=False for message: {user_message}")
            
            context_query = await build_mongodb_query_from_context(context_for_query, self.db)
            
            # Parse query from natural language message
            parsed_query = await parse_query_from_natural_language(user_message, self.db)
            
            # Add extracted months to parsed query if they were found in the message
            # This ensures months mentioned in the message are actually used in the MongoDB query
            if requested_months:
                logger.info(f"📅 Adding extracted months to query: {requested_months}")
                if 'Month_Name' in parsed_query:
                    # Merge with existing month filter
                    existing_months = parsed_query['Month_Name'].get('$in', [])
                    if isinstance(existing_months, list):
                        # Combine and deduplicate
                        combined_months = list(set(existing_months + requested_months))
                        parsed_query['Month_Name'] = {'$in': combined_months}
                        logger.info(f"📅 Merged months: {combined_months}")
                    else:
                        parsed_query['Month_Name'] = {'$in': requested_months}
                else:
                    parsed_query['Month_Name'] = {'$in': requested_months}
                    logger.info(f"📅 Added months to query: {requested_months}")
            
            # Add extracted years to parsed query if they were found in the message
            # BUT skip if "across years" is detected (user wants all years)
            if requested_years and not is_across_years:
                logger.info(f"📅 Adding extracted years to query: {requested_years}")
                if 'Year' in parsed_query:
                    # Merge with existing year filter
                    existing_years = parsed_query['Year'].get('$in', [])
                    if isinstance(existing_years, list):
                        # Combine and deduplicate, convert to int
                        combined_years = list(set([int(y) for y in existing_years] + requested_years))
                        parsed_query['Year'] = {'$in': combined_years}
                        logger.info(f"📅 Merged years: {combined_years}")
                    else:
                        parsed_query['Year'] = {'$in': requested_years}
                else:
                    parsed_query['Year'] = {'$in': requested_years}
                    logger.info(f"📅 Added years to query: {requested_years}")
            elif is_across_years and 'Year' in parsed_query:
                # Remove Year filter from parsed_query if "across years" is detected
                logger.info("📅 Removing Year filter from parsed_query for cross-year comparison")
                parsed_query = {k: v for k, v in parsed_query.items() if k != 'Year'}
            
            # Merge context query with parsed query (parsed query takes precedence for filters it specifies)
            query = context_query.copy()
            
            # CRITICAL: Ensure extracted months and years are in the final query
            # If they were extracted from the message, they MUST be in the query
            if requested_months:
                if 'Month_Name' in query:
                    existing_months = query['Month_Name'].get('$in', [])
                    if isinstance(existing_months, list):
                        merged_months = list(set(existing_months + requested_months))
                        query['Month_Name'] = {'$in': merged_months}
                        logger.info(f"📅 Final query - Merged months: {merged_months}")
                    else:
                        query['Month_Name'] = {'$in': requested_months}
                        logger.info(f"📅 Final query - Added months: {requested_months}")
                else:
                    query['Month_Name'] = {'$in': requested_months}
                    logger.info(f"📅 Final query - Added months: {requested_months}")
            
            if requested_years:
                if 'Year' in query:
                    existing_years = query['Year'].get('$in', [])
                    if isinstance(existing_years, list):
                        merged_years = list(set([int(y) for y in existing_years] + requested_years))
                        query['Year'] = {'$in': merged_years}
                        logger.info(f"📅 Final query - Merged years: {merged_years}")
                    else:
                        query['Year'] = {'$in': requested_years}
                        logger.info(f"📅 Final query - Added years: {requested_years}")
                else:
                    query['Year'] = {'$in': requested_years}
                    logger.info(f"📅 Final query - Added years: {requested_years}")
            
            # Now merge other parsed_query filters
            for key, value in parsed_query.items():
                if key in query:
                    # Skip if we already handled Month_Name or Year above
                    if key in ['Month_Name', 'Year']:
                        continue
                    # Merge filters (intersect for $in queries)
                    if isinstance(query[key], dict) and '$in' in query[key] and isinstance(value, dict) and '$in' in value:
                        existing_values = query[key]['$in']
                        new_values = value['$in']
                        # Intersect the lists for other filters
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
            
            # CRITICAL: Check if Month_Name format might be wrong (e.g., "Nov" vs "November")
            # If query has Month_Name but returns 0, try alternative formats
            if query and 'Month_Name' in query and 'Year' in query:
                month_filter = query['Month_Name'].get('$in', [])
                year_filter = query['Year'].get('$in', [])
                
                # Check what month formats actually exist in database
                year_query_for_months = {'Year': year_filter}
                distinct_months = await self.db.business_data.distinct('Month_Name', year_query_for_months)
                logger.info(f"📅 Available month formats in database for year {year_filter}: {distinct_months}")
                
                # If our months don't match, try to find the correct format
                if month_filter:
                    month_mapping_full_to_abbr = {
                        'January': 'Jan', 'February': 'Feb', 'March': 'Mar', 'April': 'Apr',
                        'May': 'May', 'June': 'Jun', 'July': 'Jul', 'August': 'Aug',
                        'September': 'Sep', 'October': 'Oct', 'November': 'Nov', 'December': 'Dec'
                    }
                    
                    # Try to match our months with database months
                    corrected_months = []
                    for our_month in month_filter:
                        # Check if exact match exists
                        if our_month in distinct_months:
                            corrected_months.append(our_month)
                        else:
                            # Try abbreviation
                            abbr = month_mapping_full_to_abbr.get(our_month)
                            if abbr and abbr in distinct_months:
                                corrected_months.append(abbr)
                                logger.info(f"📅 Corrected month format: {our_month} -> {abbr}")
                            else:
                                # Try reverse (abbr to full)
                                for db_month in distinct_months:
                                    if our_month.lower() in db_month.lower() or db_month.lower() in our_month.lower():
                                        corrected_months.append(db_month)
                                        logger.info(f"📅 Corrected month format: {our_month} -> {db_month}")
                    
                    if corrected_months and set(corrected_months) != set(month_filter):
                        logger.warning(f"⚠️ Month format mismatch! Original: {month_filter}, Corrected: {corrected_months}")
                        query['Month_Name'] = {'$in': list(set(corrected_months))}
                        logger.info(f"📅 Updated query with corrected months: {query['Month_Name']}")
            
            # Verify query will return data
            if query:
                test_count = await self.db.business_data.count_documents(query)
                logger.info(f"📊 Documents matching final query: {test_count}")
                logger.info(f"📊 Final query after corrections: {query}")
                
                if test_count == 0:
                    logger.warning(f"⚠️ WARNING: Final query returns 0 documents! Query: {query}")
                    
                    # Additional diagnostics
                    if 'Month_Name' in query:
                        month_filter = query['Month_Name']
                        logger.warning(f"⚠️ Month_Name filter: {month_filter}")
                        query_without_month = {k: v for k, v in query.items() if k != 'Month_Name'}
                        count_without_month = await self.db.business_data.count_documents(query_without_month)
                        logger.warning(f"⚠️ Documents without Month_Name filter: {count_without_month}")
                    
                    if 'Year' in query:
                        year_filter = query['Year']
                        logger.warning(f"⚠️ Year filter: {year_filter}")
                        query_without_year = {k: v for k, v in query.items() if k != 'Year'}
                        count_without_year = await self.db.business_data.count_documents(query_without_year)
                        logger.warning(f"⚠️ Documents without Year filter: {count_without_year}")
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
            # Also detect "compare brand X" queries - these should show all brands for comparison
            # Check for various phrasings: "compare brand X", "compare X with other brands", "X vs other brands", etc.
            is_comparing_brand = any(phrase in user_msg_lower for phrase in [
                'compare brand', 'compare brands', 'brand vs', 'brands vs', 'brand versus', 'brands versus',
                'compare x with', 'compare x to', 'compare x against', 'x compared to', 'x compared with',
                'x vs other', 'x versus other', 'x against other', 'x and other brands', 'x with other brands',
                'with other brands', 'versus other brands', 'against other brands', 'to other brands',
                'how does', 'how do', 'how is', 'how are', 'compared to other', 'compared with other',
                'relative to other brands', 'among other brands', 'alongside other brands'
            ]) and ('brand' in user_msg_lower or 'brands' in user_msg_lower)
            
            # Detect "compare business X" queries - these should show all businesses for comparison
            # Check for various phrasings: "compare business X", "compare X with other businesses", "X vs other businesses", etc.
            # Also check for "with other business in the group" which is a common phrasing
            is_comparing_business = (
                any(phrase in user_msg_lower for phrase in [
                    'compare business', 'compare businesses', 'business vs', 'businesses vs', 'business versus', 'businesses versus',
                    'compare x with', 'compare x to', 'compare x against', 'x compared to', 'x compared with',
                    'x vs other', 'x versus other', 'x against other', 'x and other businesses', 'x with other businesses',
                    'with other businesses', 'versus other businesses', 'against other businesses', 'to other businesses',
                    'with other business', 'versus other business', 'against other business', 'to other business',
                    'compared to other', 'compared with other', 'in the group', 'with other business in the group',
                    'with other businesses in the group', 'relative to other businesses', 'among other businesses', 
                    'alongside other businesses', 'other business in the group', 'other businesses in the group'
                ]) and ('business' in user_msg_lower or 'businesses' in user_msg_lower)
            ) or 'with other business' in user_msg_lower or 'with other businesses' in user_msg_lower
            
            # Note: is_asking_for_all_businesses is already defined earlier (line 66)
            # This check is just for reference - the variable is already set above
            
            is_asking_for_brands = (
                any(phrase in user_msg_lower for phrase in [
                    'top brands', 'top 15 brands', 'top 10 brands', 'top 5 brands', 'top 20 brands',
                    'brands by revenue', 'brands by profit', 'brands by', 'all brands',
                    'list brands', 'show brands', 'which brands', 'what brands', 'tell me brands',
                    'tell me about brands', 'tell me about brand', 'show me brands', 'show me brand',
                    'show me the top', 'brand performance', 'brand rankings', 'brand revenue', 'brand profit',
                    'compare brand', 'compare brands', 'brand comparison', 'brands comparison'
                ]) or 
                re.search(r'top\s+\d+\s+brand', user_msg_lower) or
                re.search(r'show\s+me\s+(the\s+)?top\s+\d+\s+brand', user_msg_lower) or
                re.search(r'tell\s+me\s+about\s+(all\s+)?brand', user_msg_lower) or
                "brand" in chart_title_lower or 
                is_comparing_brand
            )
            
            # Remove Brand filter from main query when comparing brands (so pivot table shows all brands)
            if is_comparing_brand and 'Brand' in query:
                logger.info(f"🔍 Removing Brand filter from main query (user is comparing brands)")
                logger.info(f"🔍 Original query had Brand filter: {query.get('Brand')}")
                query = {k: v for k, v in query.items() if k != 'Brand'}
                logger.info(f"🔍 Main query after removing Brand filter: {query}")
            
            # Remove Business filter from main query when comparing businesses or asking for all businesses
            # Note: is_asking_for_all_businesses is defined earlier (line 67-78)
            if (is_comparing_business or is_asking_for_all_businesses) and 'Business' in query:
                logger.info(f"🔍✅ Removing Business filter from main query (user is comparing businesses or asking for all businesses)")
                logger.info(f"🔍 Original query had Business filter: {query.get('Business')}")
                logger.info(f"🔍 is_comparing_business: {is_comparing_business}, is_asking_for_all_businesses: {is_asking_for_all_businesses}")
                query = {k: v for k, v in query.items() if k != 'Business'}
                logger.info(f"🔍 Main query after removing Business filter: {query}")
            elif 'Business' in query and not is_comparing_business:
                logger.info(f"🔍⚠️ Business filter still present in query but not removed!")
                logger.info(f"🔍 Business filter value: {query.get('Business')}")
                logger.info(f"🔍 is_comparing_business: {is_comparing_business}, is_asking_for_all_businesses: {is_asking_for_all_businesses}")
                logger.info(f"🔍 User message: {user_message}")
            
            # Use a modified query for data context that excludes Brand filter when asking FOR brands or comparing brands
            data_context_query = query.copy() if query else {}
            if (is_asking_for_brands or is_comparing_brand) and 'Brand' in data_context_query:
                logger.info(f"🔍 Removing Brand filter from data context query (user is asking FOR brands or comparing brands)")
                logger.info(f"🔍 Original data context query had Brand filter: {data_context_query.get('Brand')}")
                logger.info(f"🔍 is_asking_for_brands: {is_asking_for_brands}, is_comparing_brand: {is_comparing_brand}")
                data_context_query = {k: v for k, v in data_context_query.items() if k != 'Brand'}
                logger.info(f"🔍 Data context query after removing Brand filter: {data_context_query}")
            
            # Remove Business filter from data context query when comparing businesses or asking for all businesses
            if (is_comparing_business or is_asking_for_all_businesses) and 'Business' in data_context_query:
                logger.info(f"🔍 Removing Business filter from data context query (user is comparing businesses or asking for all businesses)")
                logger.info(f"🔍 Original data context query had Business filter: {data_context_query.get('Business')}")
                logger.info(f"🔍 is_comparing_business: {is_comparing_business}, is_asking_for_all_businesses: {is_asking_for_all_businesses}")
                data_context_query = {k: v for k, v in data_context_query.items() if k != 'Business'}
                logger.info(f"🔍 Data context query after removing Business filter: {data_context_query}")
            
            # Also remove Year filter from data_context_query if comparing across years
            # Note: is_across_years is already defined earlier, but check again here for data_context_query
            is_across_years_data = (
                any(phrase in user_msg_lower for phrase in [
                    'across years', 'across all years', 'all years', 'year over year', 'yoy'
                ]) or
                re.search(r'compare.*across\s+years?', user_msg_lower) is not None or
                is_across_years
            )
            if is_across_years_data and 'Year' in data_context_query:
                logger.info("📅 Removing Year filter from data context query for cross-year comparison")
                data_context_query = {k: v for k, v in data_context_query.items() if k != 'Year'}
            
            # Determine analysis type
            is_comparison = any(word in user_msg_lower for word in ['compare', 'comparison', 'vs', 'versus', 'against'])
            is_quarterly = any(word in user_msg_lower for word in ['quarterly', 'q1', 'q2', 'q3', 'q4', 'quarter'])
            is_monthly = any(word in user_msg_lower for word in ['monthly', 'month', 'by month'])
            is_yearly = any(word in user_msg_lower for word in ['yearly', 'year', 'yoy', 'year over year'])
            is_metrics = any(word in user_msg_lower for word in ['metrics', 'details', 'show me', 'tell me'])
            
            # CRITICAL FIX: Convert Q1, Q2, Q3, Q4 to actual months
            quarter_to_months = {
                'q1': ['January', 'February', 'March'],
                'q2': ['April', 'May', 'June'],
                'q3': ['July', 'August', 'September'],
                'q4': ['October', 'November', 'December']
            }
            
            # Extract quarter from message (e.g., "Q1", "q1", "quarter 1")
            quarter_pattern = r'\bq([1-4])\b'
            quarter_matches = re.findall(quarter_pattern, user_msg_lower)
            
            if quarter_matches:
                quarter_num = quarter_matches[0]  # Get first match
                quarter_key = f'q{quarter_num}'
                if quarter_key in quarter_to_months:
                    quarter_months = quarter_to_months[quarter_key]
                    logger.info(f"📅 Detected {quarter_key.upper()} - converting to months: {quarter_months}")
                    
                    # Add quarter months to query
                    if 'Month_Name' in query:
                        # Merge with existing month filter
                        existing_months = query['Month_Name'].get('$in', [])
                        if isinstance(existing_months, list):
                            # Combine and deduplicate
                            combined_months = list(set(existing_months + quarter_months))
                            query['Month_Name'] = {'$in': combined_months}
                            logger.info(f"📅 Merged quarter months with existing: {combined_months}")
                        else:
                            query['Month_Name'] = {'$in': quarter_months}
                    else:
                        query['Month_Name'] = {'$in': quarter_months}
                        logger.info(f"📅 Added quarter months to query: {quarter_months}")
                    
                    # Also update data_context_query with quarter months
                    if 'Month_Name' in data_context_query:
                        existing_data_months = data_context_query['Month_Name'].get('$in', [])
                        if isinstance(existing_data_months, list):
                            combined_data_months = list(set(existing_data_months + quarter_months))
                            data_context_query['Month_Name'] = {'$in': combined_data_months}
                        else:
                            data_context_query['Month_Name'] = {'$in': quarter_months}
                    else:
                        data_context_query['Month_Name'] = {'$in': quarter_months}
            
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
            
            # CRITICAL: Detect if this is a NEW question vs a FOLLOW-UP question
            # Analyze the current question's intent and compare with previous questions
            # This ensures the AI treats each question independently, especially when switching between "top X" and "all"
            
            # Detect scope: 'all', 'top', or 'specific'
            has_top_number = bool(re.search(r'top\s+\d+', user_msg_lower))
            has_all_keyword = 'all' in user_msg_lower and not has_top_number
            
            current_intent = {
                'scope': 'all' if has_all_keyword else ('top' if has_top_number else 'specific'),
                'entity_type': None,
                'question_type': None,
                'top_number': None
            }
            
            # Extract top number if present
            if has_top_number:
                top_match = re.search(r'top\s+(\d+)', user_msg_lower)
                if top_match:
                    current_intent['top_number'] = int(top_match.group(1))
            
            # Detect entity type (check in order of specificity)
            if 'business' in user_msg_lower or 'businesses' in user_msg_lower:
                current_intent['entity_type'] = 'business'
            if 'brand' in user_msg_lower or 'brands' in user_msg_lower:
                current_intent['entity_type'] = 'brand'
            if 'category' in user_msg_lower or 'categories' in user_msg_lower:
                current_intent['entity_type'] = 'category'
            if 'customer' in user_msg_lower or 'customers' in user_msg_lower:
                current_intent['entity_type'] = 'customer'
            if 'channel' in user_msg_lower or 'channels' in user_msg_lower:
                current_intent['entity_type'] = 'channel'
            if 'sku' in user_msg_lower or 'skus' in user_msg_lower:
                current_intent['entity_type'] = 'sku'
            if 'sub-category' in user_msg_lower or 'subcategory' in user_msg_lower or 'sub category' in user_msg_lower:
                current_intent['entity_type'] = 'subcategory'
            
            # Detect question type
            if 'compare' in user_msg_lower or 'comparison' in user_msg_lower or 'vs' in user_msg_lower or 'versus' in user_msg_lower:
                current_intent['question_type'] = 'comparison'
            elif has_top_number or 'rank' in user_msg_lower or 'ranking' in user_msg_lower:
                current_intent['question_type'] = 'ranking'
            elif has_all_keyword and current_intent['entity_type']:
                current_intent['question_type'] = 'all'
            elif 'details' in user_msg_lower or 'detailed' in user_msg_lower or 'tell me about' in user_msg_lower:
                current_intent['question_type'] = 'details'
            
            logger.info(f"🔍 Current question intent: scope={current_intent['scope']}, entity={current_intent['entity_type']}, type={current_intent['question_type']}, top_number={current_intent['top_number']}")
            
            # Check if previous question had different intent
            is_different_question = False
            if request.conversation_history and len(request.conversation_history) > 0:
                # Get the last user question from conversation history
                last_user_question = None
                for msg in reversed(request.conversation_history):
                    if msg.get("role") == "user":
                        last_user_question = msg.get("content", "").lower()
                        break
                
                if last_user_question:
                    # Detect previous intent (same logic as current)
                    prev_has_top = bool(re.search(r'top\s+\d+', last_user_question))
                    prev_has_all = 'all' in last_user_question and not prev_has_top
                    
                    previous_intent = {
                        'scope': 'all' if prev_has_all else ('top' if prev_has_top else 'specific'),
                        'entity_type': None,
                        'question_type': None,
                        'top_number': None
                    }
                    
                    if prev_has_top:
                        prev_top_match = re.search(r'top\s+(\d+)', last_user_question)
                        if prev_top_match:
                            previous_intent['top_number'] = int(prev_top_match.group(1))
                    
                    # Detect previous entity type
                    if 'business' in last_user_question or 'businesses' in last_user_question:
                        previous_intent['entity_type'] = 'business'
                    if 'brand' in last_user_question or 'brands' in last_user_question:
                        previous_intent['entity_type'] = 'brand'
                    if 'category' in last_user_question or 'categories' in last_user_question:
                        previous_intent['entity_type'] = 'category'
                    if 'customer' in last_user_question or 'customers' in last_user_question:
                        previous_intent['entity_type'] = 'customer'
                    if 'channel' in last_user_question or 'channels' in last_user_question:
                        previous_intent['entity_type'] = 'channel'
                    if 'sku' in last_user_question or 'skus' in last_user_question:
                        previous_intent['entity_type'] = 'sku'
                    if 'sub-category' in last_user_question or 'subcategory' in last_user_question:
                        previous_intent['entity_type'] = 'subcategory'
                    
                    # Detect previous question type
                    if 'compare' in last_user_question or 'comparison' in last_user_question or 'vs' in last_user_question:
                        previous_intent['question_type'] = 'comparison'
                    elif prev_has_top or 'rank' in last_user_question:
                        previous_intent['question_type'] = 'ranking'
                    elif prev_has_all and previous_intent['entity_type']:
                        previous_intent['question_type'] = 'all'
                    
                    logger.info(f"🔍 Previous question intent: scope={previous_intent['scope']}, entity={previous_intent['entity_type']}, type={previous_intent['question_type']}, top_number={previous_intent['top_number']}")
                    
                    # Check if intents are different
                    # Case 1: Same entity but different scope (e.g., "top 10 business" vs "all business")
                    if (current_intent['entity_type'] and previous_intent['entity_type'] and
                        current_intent['entity_type'] == previous_intent['entity_type'] and
                        current_intent['scope'] != previous_intent['scope']):
                        is_different_question = True
                        logger.info(f"🔄✅ Detected different scope for same entity: previous='{previous_intent['scope']}', current='{current_intent['scope']}'")
                    # Case 2: Different entity type (e.g., "business" vs "brand")
                    elif (current_intent['entity_type'] and previous_intent['entity_type'] and
                          current_intent['entity_type'] != previous_intent['entity_type']):
                        is_different_question = True
                        logger.info(f"🔄✅ Detected different entity: previous='{previous_intent['entity_type']}', current='{current_intent['entity_type']}'")
                    # Case 3: Different question type (e.g., "comparison" vs "ranking")
                    elif (current_intent['question_type'] and previous_intent['question_type'] and
                          current_intent['question_type'] != previous_intent['question_type']):
                        is_different_question = True
                        logger.info(f"🔄✅ Detected different question type: previous='{previous_intent['question_type']}', current='{current_intent['question_type']}'")
                    # Case 4: Same scope type but different numbers (e.g., "top 10" vs "top 15")
                    elif (current_intent['scope'] == 'top' and previous_intent['scope'] == 'top' and
                          current_intent['top_number'] and previous_intent['top_number'] and
                          current_intent['top_number'] != previous_intent['top_number']):
                        # This is still a different question, but less critical - could be follow-up
                        # For now, treat as different to ensure fresh analysis
                        is_different_question = True
                        logger.info(f"🔄✅ Detected different top number: previous='top {previous_intent['top_number']}', current='top {current_intent['top_number']}'")
            
            # Build conversation history for Perplexity
            # If this is a different question, don't use conversation history (or use minimal history)
            conversation_history = []
            if request.conversation_history and not is_different_question:
                for msg in request.conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role in ["user", "assistant"]:
                        conversation_history.append({"role": role, "content": content})
            elif is_different_question:
                logger.info(f"🔄 This is a NEW question (different from previous) - using empty conversation history")
                # Optionally keep only the very last exchange for minimal context
                # But for now, use empty to ensure fresh analysis
            
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
            if "email" in user_msg_lower or ("write" in user_msg_lower and "email" in user_msg_lower) or ("draft" in user_msg_lower and "email" in user_msg_lower):
                email_context = "CRITICAL: The user is asking for an email. You MUST base the email ONLY on BUSINESS PERFORMANCE DATA (revenue, profit, units, margins, brands, businesses, categories, customers, channels) from the provided dataset. Do NOT include any world events, news, politics, or non-business information. Format your response as a professional business email with: (1) Clear subject line, (2) Professional greeting, (3) Executive summary of key business findings, (4) Detailed business insights with specific numbers, (5) Actionable business recommendations, (6) Professional closing. Keep it concise (around 250 words if specified). "
            
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
                ""
                "ABSOLUTELY CRITICAL - DATA USAGE RESTRICTIONS: "
                "You MUST ONLY use the business data provided in the 'Business Data' section. "
                "You MUST NOT use any external knowledge, general world information, news, historical events, geopolitical information, wars, elections, natural disasters, economics, international relations, or any information outside the provided business data. "
                "CRITICAL: If a user asks about topics NOT related to business data (e.g., global news, politics, wars, natural disasters, world events, economics, international relations), you MUST respond: 'I can only provide insights about business data (revenue, profit, units, margins, brands, businesses, categories, customers, channels). Please ask questions related to your business performance data.' "
                "If the user asks about a time period (e.g., 'November 2025', 'Q1 2024'), you MUST ONLY reference business performance data from that period in the provided dataset. "
                "If the user asks to 'draft an email' or 'write a summary' about a time period (e.g., 'draft an email telling everything which happened in November 2025'), you MUST interpret this as asking for a BUSINESS PERFORMANCE summary email for that period, NOT a summary of world events. Base it ONLY on the business performance data provided (revenue, profit, units, margins, brands, categories, etc.), NOT on world events, news, or general knowledge. "
                ""
                "CRITICAL - HANDLING QUESTIONS ABOUT UNAVAILABLE DATA: "
                "If the user asks about data that is NOT directly available (e.g., 'operational expenses', 'OPEX', 'net profit', 'SG&A', 'marketing spend', 'cost of goods sold', 'COGS'), you should: "
                "(1) FIRST acknowledge what data IS available (e.g., 'I have revenue, gross profit, units, and gross margin data') "
                "(2) THEN provide insights based on the AVAILABLE data that relates to the question (e.g., 'Based on gross profit and margin, here's what operational expenses could impact...') "
                "(3) Explain what the available metrics tell us about the question (e.g., 'Kinetica's 38.4% gross margin indicates strong capacity to absorb operational expenses') "
                "(4) Provide actionable recommendations using the available data "
                "Do NOT just say 'data not available' - use the available data to provide valuable insights related to the question. "
                ""
                "If the provided data does not contain information about what the user is asking, you should say: 'Based on the available business data, [what you can say from the data]. However, I don't have information about [what's missing] in the provided dataset.' "
                "NEVER make up information, reference world events, geopolitical situations, wars, elections, or any non-business information. "
                "Your responses MUST be 100% based on the business data provided: revenue, profit, units, margins, brands, categories, customers, channels, and time periods. "
                ""
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
                "ABSOLUTELY CRITICAL - QUESTION INDEPENDENCE: "
                "You MUST analyze each question as a STANDALONE question, not as a follow-up to previous questions. "
                "Read the CURRENT question carefully and answer EXACTLY what is asked, not what was asked in previous questions. "
                "Examples of DIFFERENT questions (treat each as NEW): "
                "  - 'tell me top 10 business' vs 'tell me about all business' = TWO DIFFERENT questions "
                "  - 'compare brand X' vs 'tell me about all brands' = TWO DIFFERENT questions "
                "  - 'top 5 categories' vs 'all categories' = TWO DIFFERENT questions "
                "  - 'business Food' vs 'all business' = TWO DIFFERENT questions "
                "If the user asks for 'all business', provide details about ALL businesses, NOT filtered by previous 'top 10' question. "
                "If the user asks for 'all brands', provide ALL brands, NOT filtered by previous brand-specific question. "
                "The conversation history is provided for context only - do NOT let it override the current question's intent. "
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
            # CRITICAL: Emphasize that ONLY this data should be used
            question_independence_note = ""
            if is_different_question:
                question_independence_note = (
                    f"\n\n⚠️ CRITICAL: This is a NEW question, NOT a follow-up to previous questions. "
                    f"Analyze this question independently. The user is asking: '{request.message}'. "
                    f"Answer EXACTLY what is asked in this question, not what was asked before. "
                    f"If the user asks for 'all business', provide ALL businesses with complete details. "
                    f"If the user asks for 'top 10 business', provide TOP 10 businesses ranked by revenue/profit. "
                    f"If the user asks for 'all brands', provide ALL brands, not filtered by previous questions. "
                    f"Do NOT mix these up or assume one is a follow-up of the other.\n\n"
                )
            
            user_prompt = (
                f"{chart_context}\n\n"
                f"BUSINESS DATA (USE ONLY THIS DATA - DO NOT USE ANY EXTERNAL KNOWLEDGE):\n"
                f"{data_context}\n\n"
                f"CRITICAL INSTRUCTION: The above 'Business Data' section contains ALL the information you should use to answer the user's question. "
                f"Do NOT use any external knowledge, world events, news, or information outside this dataset. "
                f"If the data doesn't contain information about what the user is asking, acknowledge this limitation. "
                f"{question_independence_note}"
                f"\n\nUser Question: {request.message}"
            )
            
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
                needs_clarification=False,
                suggested_questions=[],
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

