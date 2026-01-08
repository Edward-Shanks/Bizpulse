"""
Service for Insights Chat functionality
MongoDB-based View Insights Chatbot for all screens
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.insights import InsightsChatRequest, InsightsChatResponse
from app.utils.query_builder import build_mongodb_query_from_context, parse_query_from_natural_language
from app.utils.data_context import get_comprehensive_data_context
# NOTE: query_perplexity() actually uses the provider configured in LLM_PROVIDER env variable
# It can be Ollama (local LLM) or Perplexity (API) depending on .env configuration
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
            # Q1/Q2/Q3/Q4 comparison patterns - these are clear questions
            r'compare\s+q[1-4].*business',
            r'compare\s+q[1-4].*for\s+business',
            r'q[1-4].*for\s+business.*compare',
            r'q[1-4].*business.*across',
            r'compare\s+q[1-4].*across\s+years?',
            r'q[1-4].*for\s+business.*across',
            r'compare.*q[1-4].*business.*across',
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
            
            # If user selected a previous question, retrieve it and add context
            previous_question_context = ""
            if request.selected_previous_question_id:
                try:
                    previous_q = await self.db.user_questions.find_one({"id": request.selected_previous_question_id})
                    if previous_q:
                        previous_question_context = f"\n\nCONTEXT: The user is asking a follow-up question about a previous question they asked.\n"
                        previous_question_context += f"Previous Question: {previous_q.get('question', '')}\n"
                        previous_question_context += f"Previous Response: {previous_q.get('response', '')[:500]}\n"
                        previous_question_context += f"Current Question: {user_message}\n"
                        previous_question_context += "Please provide a response that builds on the previous question and answer, addressing the current question in that context."
                        logger.info(f"📝 Using previous question context: {previous_q.get('question', '')[:50]}")
                except Exception as e:
                    logger.warning(f"⚠️ Error retrieving previous question: {str(e)}")
                    # Continue without previous question context
            
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
            # CRITICAL: Extract structured intent FIRST (Query Planning Phase)
            # This ensures we understand what the user wants BEFORE building queries
            logger.info(f"🔍 STEP 2: Extracting structured intent from question: '{user_message}'")
            
            # Define quarter-to-months mapping (CODE, not LLM - as per ChatGPT recommendation)
            # CRITICAL FIX: Use abbreviated month names (Jan, Feb, Mar) to match database format
            QUARTER_TO_MONTHS = {
                'q1': ['Jan', 'Feb', 'Mar'],
                'q2': ['Apr', 'May', 'Jun'],
                'q3': ['Jul', 'Aug', 'Sep'],
                'q4': ['Oct', 'Nov', 'Dec']
            }
            
            # Extract structured intent
            user_msg_lower_for_years = user_message.lower()
            
            # Extract quarter if mentioned
            quarter_pattern = r'\bq([1-4])\b'
            quarter_matches = re.findall(quarter_pattern, user_msg_lower_for_years)
            detected_quarter = None
            detected_quarter_months = None
            if quarter_matches:
                quarter_num = quarter_matches[0]
                quarter_key = f'q{quarter_num}'
                if quarter_key in QUARTER_TO_MONTHS:
                    detected_quarter = quarter_key.upper()
                    detected_quarter_months = QUARTER_TO_MONTHS[quarter_key]
                    logger.info(f"📅 INTENT: Detected {detected_quarter} → months: {detected_quarter_months}")
            
            # Extract business if mentioned
            detected_business = None
            business_patterns = [
                r'business\s+([a-zA-Z\s,&]+?)(?:\s+in|\s+for|\s+across|\s+and|\s+or|$)',
                r'for\s+business\s+([a-zA-Z\s,&]+?)(?:\s+in|\s+for|\s+across|\s+and|\s+or|$)',
            ]
            for pattern in business_patterns:
                match = re.search(pattern, user_msg_lower_for_years)
                if match:
                    detected_business = match.group(1).strip()
                    logger.info(f"📅 INTENT: Detected business: '{detected_business}'")
                    break
            
            # Extract years if mentioned
            detected_years = []
            year_pattern = r'\b(20\d{2})\b'
            years_in_message = re.findall(year_pattern, user_message)
            detected_years = [int(y) for y in years_in_message if 2000 <= int(y) <= 2100]
            if detected_years:
                logger.info(f"📅 INTENT: Detected years: {detected_years}")
            
            # Extract metric if mentioned
            detected_metric = None
            metric_patterns = [
                r'(gross\s+sales|revenue|profit|units|margin)',
                r'(sales|revenue|profit|units)',
            ]
            for pattern in metric_patterns:
                match = re.search(pattern, user_msg_lower_for_years)
                if match:
                    detected_metric = match.group(1).lower()
                    logger.info(f"📅 INTENT: Detected metric: '{detected_metric}'")
                    break
            
            # Check for "across years" intent
            is_across_years = (
                any(phrase in user_msg_lower_for_years for phrase in [
                    'across years', 'across all years', 'all years', 'year over year', 'yoy'
                ]) or
                re.search(r'compare.*across\s+years?', user_msg_lower_for_years) is not None
            )
            if is_across_years:
                logger.info(f"📅 INTENT: User wants comparison across ALL years (not specific years)")
                detected_years = []  # Clear specific years if comparing across all years
            
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
            # CRITICAL FIX: Database uses abbreviated month names (Jan, Feb, Mar), so convert to abbreviated format
            month_abbr_map = {
                'january': 'Jan', 'jan': 'Jan',
                'february': 'Feb', 'feb': 'Feb',
                'march': 'Mar', 'mar': 'Mar',
                'april': 'Apr', 'apr': 'Apr',
                'may': 'May',
                'june': 'Jun', 'jun': 'Jun',
                'july': 'Jul', 'jul': 'Jul',
                'august': 'Aug', 'aug': 'Aug',
                'september': 'Sep', 'sep': 'Sep', 'sept': 'Sep',
                'october': 'Oct', 'oct': 'Oct',
                'november': 'Nov', 'nov': 'Nov',
                'december': 'Dec', 'dec': 'Dec'
            }
            user_msg_lower_for_months = user_message.lower()
            requested_months = []
            for month_key, month_abbr in month_abbr_map.items():
                # Match whole words only to avoid false positives (e.g., "march" in "marching")
                pattern = r'\b' + re.escape(month_key) + r'\b'
                if re.search(pattern, user_msg_lower_for_months):
                    if month_abbr not in requested_months:
                        requested_months.append(month_abbr)
            logger.info(f"📅 Extracted months from message (converted to abbreviated format): {requested_months if requested_months else 'None'}")
            
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
            # CRITICAL: Now returns structured output with filters and intent (as per ChatGPT recommendation)
            parsed_result = await parse_query_from_natural_language(user_message, self.db)
            
            # Extract filters and intent from structured output
            if isinstance(parsed_result, dict) and "filters" in parsed_result:
                parsed_query = parsed_result["filters"]
                query_intent = parsed_result.get("intent", {})
                logger.info(f"📊 Query intent extracted: {query_intent}")
            else:
                # Backward compatibility: if old format (just filters dict), use as-is
                parsed_query = parsed_result if isinstance(parsed_result, dict) else {}
                query_intent = {}
                logger.warning("⚠️ parse_query_from_natural_language returned old format, using backward compatibility")
            
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
            # CRITICAL: Distinguish between:
            # 1. "Compare X with other brands" → Remove Brand filter (show all brands)
            # 2. "Compare Q1 for Food and KOKA brand" → Keep Brand filter (filter BY KOKA, compare across years)
            is_comparing_brand = any(phrase in user_msg_lower for phrase in [
                'compare brand', 'compare brands', 'brand vs', 'brands vs', 'brand versus', 'brands versus',
                'vs other brands', 'versus other brands', 'against other brands', 'to other brands',
                'with other brands', 'compared to other brands', 'compared with other brands',
                'relative to other brands', 'among other brands', 'alongside other brands',
                'how does', 'how do', 'how is', 'how are'
            ]) and ('brand' in user_msg_lower or 'brands' in user_msg_lower)
            
            # CRITICAL: Check if user is filtering BY a specific brand (not comparing brands)
            # Pattern: "Food and KOKA brand" or "business Food and KOKA brand" = filtering BY brand
            is_filtering_by_specific_brand = (
                'Brand' in query and
                not is_comparing_brand and
                (
                    re.search(r'and\s+[A-Z][a-zA-Z\s]+\s+brand', user_msg_lower) or  # "and KOKA brand"
                    re.search(r'business\s+[^,]+\s+and\s+[A-Z][a-zA-Z\s]+\s+brand', user_msg_lower) or  # "business Food and KOKA brand"
                    ('brand' in user_msg_lower and 'and' in user_msg_lower and not any(phrase in user_msg_lower for phrase in ['other brands', 'other brand', 'vs other', 'versus other']))
                )
            )
            
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
            # BUT: Keep Brand filter if user is filtering BY a specific brand (e.g., "Food and KOKA brand")
            if is_comparing_brand and 'Brand' in query and not is_filtering_by_specific_brand:
                logger.info(f"🔍 Removing Brand filter from main query (user is comparing brands)")
                logger.info(f"🔍 Original query had Brand filter: {query.get('Brand')}")
                query = {k: v for k, v in query.items() if k != 'Brand'}
                logger.info(f"🔍 Main query after removing Brand filter: {query}")
            elif is_filtering_by_specific_brand:
                logger.info(f"🔍 Keeping Brand filter in main query (user is filtering BY specific brand: {query.get('Brand')})")
            
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
            
            # Use a modified query for data context
            # CRITICAL: Only remove Brand filter if user is asking FOR brands (listing all brands) or comparing brands
            # BUT: Keep Brand filter if user is filtering BY a specific brand (e.g., "Compare Q1 for Food and KOKA brand")
            data_context_query = query.copy() if query else {}
            if (is_asking_for_brands or (is_comparing_brand and not is_filtering_by_specific_brand)) and 'Brand' in data_context_query:
                logger.info(f"🔍 Removing Brand filter from data context query (user is asking FOR brands or comparing brands)")
                logger.info(f"🔍 Original data context query had Brand filter: {data_context_query.get('Brand')}")
                logger.info(f"🔍 is_asking_for_brands: {is_asking_for_brands}, is_comparing_brand: {is_comparing_brand}")
                data_context_query = {k: v for k, v in data_context_query.items() if k != 'Brand'}
                logger.info(f"🔍 Data context query after removing Brand filter: {data_context_query}")
            
            # CRITICAL: Detect if user is filtering BY a specific channel (not comparing channels)
            # Pattern: "Food and grocery channel" OR "Food and channel grocery" = filtering BY channel
            is_filtering_by_specific_channel = (
                'Channel' in query and
                (
                    re.search(r'and\s+[a-z][a-zA-Z\s]+\s+channel', user_msg_lower) or  # "and grocery channel"
                    re.search(r'and\s+channel\s+[a-z][a-zA-Z\s]+', user_msg_lower) or  # "and channel grocery"
                    re.search(r'business\s+[^,]+\s+and\s+[a-z][a-zA-Z\s]+\s+channel', user_msg_lower) or  # "business Food and grocery channel"
                    re.search(r'business\s+[^,]+\s+and\s+channel\s+[a-z][a-zA-Z\s]+', user_msg_lower) or  # "business Food and channel grocery"
                    ('channel' in user_msg_lower and 'and' in user_msg_lower and not any(phrase in user_msg_lower for phrase in ['other channels', 'other channel', 'vs other', 'versus other']))
                )
            )
            
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
            # CRITICAL FIX: Use abbreviated month names (Jan, Feb, Mar) to match database format
            quarter_to_months = {
                'q1': ['Jan', 'Feb', 'Mar'],
                'q2': ['Apr', 'May', 'Jun'],
                'q3': ['Jul', 'Aug', 'Sep'],
                'q4': ['Oct', 'Nov', 'Dec']
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
            logger.info(f"📊 Query intent: {query_intent}")
            
            # CRITICAL: Use intent to determine aggregation needs (as per ChatGPT recommendation)
            # If operation is "compare" and group_by is "Year", we need year-over-year aggregation
            needs_year_aggregation = (
                query_intent.get("operation") == "compare" and 
                query_intent.get("group_by") == "Year"
            )
            if needs_year_aggregation:
                logger.info("📊 Intent requires year-over-year comparison aggregation")
                is_yearly = True  # Force yearly breakdown for comparison
            
            # CRITICAL: Implement query fallback logic - if query returns no data, try progressively relaxed queries
            data_context = None
            fallback_attempts = []
            original_query = data_context_query.copy()
            
            try:
                # Try original query first
                # CRITICAL: Set is_comparison to True when comparing brands or businesses
                # This ensures brand/business breakdowns are shown in data context
                is_comparison_for_context = (
                    is_comparison or 
                    (query_intent.get("operation") == "compare") or
                    is_comparing_brand or
                    is_comparing_business
                )
                
                # Extract detected metric from query intent
                detected_metric = query_intent.get("metric") if query_intent else None
                logger.info(f"📊 Detected metric from query intent: {detected_metric}")
                
                data_context = await get_comprehensive_data_context(
                    data_context_query,  # Use modified query without Brand filter when asking FOR brands
                    user_message,
                    self.db,
                    is_comparison=is_comparison_for_context,
                    is_quarterly=is_quarterly,
                    is_monthly=is_monthly,
                    is_yearly=is_yearly or needs_year_aggregation,
                    is_metrics=is_metrics,
                    detected_metric=detected_metric
                )
                logger.info(f"📈 Data context length: {len(data_context)} characters")
                logger.info(f"📈 Data context preview: {data_context[:500]}...")
                
                # Check if query returned no data
                if "⚠️ Note: No data found matching the specified filters" in data_context or "Total Revenue: €0" in data_context:
                    logger.warning(f"⚠️ Original query returned no data. Attempting fallback queries...")
                    fallback_attempts.append(f"Original query: {original_query}")
                    
                    # Fallback 1: Remove Month_Name filter (keep Business and Year)
                    if 'Month_Name' in data_context_query:
                        fallback_query_1 = {k: v for k, v in data_context_query.items() if k != 'Month_Name'}
                        logger.info(f"🔄 Fallback 1: Trying without Month_Name filter: {fallback_query_1}")
                        fallback_context_1 = await get_comprehensive_data_context(
                            fallback_query_1,
                            user_message,
                            self.db,
                            is_comparison=is_comparison,
                            is_quarterly=is_quarterly,
                            is_monthly=is_monthly,
                            is_yearly=is_yearly,
                            is_metrics=is_metrics,
                            detected_metric=detected_metric
                        )
                        if "⚠️ Note: No data found" not in fallback_context_1 and "Total Revenue: €0" not in fallback_context_1:
                            logger.info(f"✅ Fallback 1 succeeded - found data without Month_Name filter")
                            # CRITICAL: Do NOT add misleading notes about "Q1-specific data not available"
                            # The data exists, it's just aggregated differently - LLM should still use it
                            data_context = fallback_context_1
                            fallback_attempts.append(f"Fallback 1 (no Month_Name): Found data")
                        else:
                            fallback_attempts.append(f"Fallback 1 (no Month_Name): No data")
                            
                            # Fallback 2: Remove Year filter (keep Business and Month_Name)
                            if 'Year' in data_context_query:
                                fallback_query_2 = {k: v for k, v in data_context_query.items() if k != 'Year'}
                                logger.info(f"🔄 Fallback 2: Trying without Year filter: {fallback_query_2}")
                                fallback_context_2 = await get_comprehensive_data_context(
                                    fallback_query_2,
                                    user_message,
                                    self.db,
                                    is_comparison=is_comparison,
                                    is_quarterly=is_quarterly,
                                    is_monthly=is_monthly,
                                    is_yearly=is_yearly,
                                    is_metrics=is_metrics,
                                    detected_metric=detected_metric
                                )
                                if "⚠️ Note: No data found" not in fallback_context_2 and "Total Revenue: €0" not in fallback_context_2:
                                    logger.info(f"✅ Fallback 2 succeeded - found data without Year filter")
                                    # CRITICAL: Do NOT add misleading notes about "year-specific data not available"
                                    # The data exists, it's just aggregated differently - LLM should still use it
                                    data_context = fallback_context_2
                                    fallback_attempts.append(f"Fallback 2 (no Year): Found data")
                                else:
                                    fallback_attempts.append(f"Fallback 2 (no Year): No data")
                                    
                                    # Fallback 3: Keep only Business filter
                                    if 'Business' in data_context_query:
                                        fallback_query_3 = {'Business': data_context_query['Business']}
                                        logger.info(f"🔄 Fallback 3: Trying with only Business filter: {fallback_query_3}")
                                        fallback_context_3 = await get_comprehensive_data_context(
                                            fallback_query_3,
                                            user_message,
                                            self.db,
                                            is_comparison=is_comparison,
                                            is_quarterly=is_quarterly,
                                            is_monthly=is_monthly,
                                            is_yearly=is_yearly,
                                            is_metrics=is_metrics,
                                            detected_metric=detected_metric
                                        )
                                        if "⚠️ Note: No data found" not in fallback_context_3 and "Total Revenue: €0" not in fallback_context_3:
                                            logger.info(f"✅ Fallback 3 succeeded - found data with only Business filter")
                                            # CRITICAL: Do NOT add misleading notes about "Q1-specific data not available"
                                            # The data exists, it's just aggregated differently - LLM should still use it
                                            data_context = fallback_context_3
                                            fallback_attempts.append(f"Fallback 3 (only Business): Found data")
                                        else:
                                            fallback_attempts.append(f"Fallback 3 (only Business): No data")
                    
                    # Log all fallback attempts
                    logger.info(f"📋 Fallback attempts summary: {fallback_attempts}")
                
                # CRITICAL: Validate query results BEFORE answering (as per ChatGPT recommendation)
                # Check if we have sufficient data for the requested comparison
                if "Overall Totals" in data_context:
                    # Extract total revenue from context
                    revenue_match = re.search(r'Total Revenue: (€[\d.]+[kM]?)', data_context)
                    if revenue_match:
                        revenue_str = revenue_match.group(1)
                        logger.info(f"📊 Total revenue in data context: {revenue_str}")
                        
                        # Check if revenue is zero (no data found)
                        if revenue_str == "€0" or "€0.0" in revenue_str:
                            logger.warning(f"⚠️ Query returned zero revenue - validating intent vs results")
                            logger.warning(f"⚠️ Intent: quarter={detected_quarter}, business={detected_business}, years={detected_years}")
                            logger.warning(f"⚠️ This suggests the query filters may not match the database schema or data")
                    else:
                        logger.warning(f"⚠️ Could not extract total revenue from data context")
                
                # Validate if we have data for comparison queries
                if is_comparison and detected_years and len(detected_years) >= 2:
                    # For comparison queries, check if we have data for all requested years
                    year_data_check = []
                    for year in detected_years:
                        year_pattern = re.compile(rf'{year}.*?Revenue.*?(€[\d.]+[kM]?)', re.IGNORECASE)
                        if year_pattern.search(data_context):
                            year_data_check.append(year)
                    if len(year_data_check) < len(detected_years):
                        missing_years = [y for y in detected_years if y not in year_data_check]
                        logger.warning(f"⚠️ Comparison query: Missing data for years {missing_years}. Available: {year_data_check}")
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
            
            # Check if this is a follow-up question (e.g., "write an email for this", "draft an email for this")
            is_follow_up_question = False
            follow_up_patterns = [
                r'write\s+(an\s+)?(a\s+)?email\s+(for\s+)?(this|that)',
                r'draft\s+(an\s+)?(a\s+)?email\s+(for\s+)?(this|that)',
                r'email\s+(for\s+)?(this|that)',
                r'summarize\s+(this|that)',
                r'explain\s+(this|that)\s+(more|further|in\s+detail)',
                r'tell\s+me\s+more\s+about\s+(this|that)',
                r'what\s+about\s+(this|that)',
                r'can\s+you\s+(write|draft|create|make)\s+(an\s+)?(a\s+)?(email|summary|report)\s+(for\s+)?(this|that)',
            ]
            for pattern in follow_up_patterns:
                if re.search(pattern, user_msg_lower):
                    is_follow_up_question = True
                    logger.info(f"🔄✅ Detected FOLLOW-UP question: '{user_message[:50]}...' - Will use conversation history")
                    break
            
            # Check if previous question had different intent (only if NOT a follow-up question)
            is_different_question = False
            if request.conversation_history and len(request.conversation_history) > 0 and not is_follow_up_question:
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
            # CRITICAL: If this is a follow-up question, ALWAYS use conversation history
            # If this is a different question, don't use conversation history (or use minimal history)
            conversation_history = []
            follow_up_context_for_prompt = ""  # Store follow-up context to add to user_prompt
            if is_follow_up_question:
                # For follow-up questions, ALWAYS include conversation history
                logger.info(f"🔄 FOLLOW-UP question detected - using FULL conversation history")
                if request.conversation_history:
                    for msg in request.conversation_history:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role in ["user", "assistant"]:
                            conversation_history.append({"role": role, "content": content})
                # Also add explicit context about the previous question/response
                if conversation_history and len(conversation_history) >= 2:
                    last_user_msg = None
                    last_assistant_msg = None
                    for msg in reversed(conversation_history):
                        if msg.get("role") == "assistant" and not last_assistant_msg:
                            last_assistant_msg = msg.get("content", "")
                        elif msg.get("role") == "user" and not last_user_msg:
                            last_user_msg = msg.get("content", "")
                            if last_assistant_msg:
                                break
                    
                    if last_user_msg and last_assistant_msg:
                        # Add explicit context to help LLM understand what "this" refers to
                        # CRITICAL: This will be added to user_prompt, not just conversation_history
                        follow_up_context_for_prompt = (
                            f"\n\n{'='*80}\n"
                            f"⚠️⚠️⚠️ CRITICAL CONTEXT: This is a FOLLOW-UP question ⚠️⚠️⚠️\n"
                            f"{'='*80}\n"
                            f"The user is asking about their PREVIOUS question and response:\n\n"
                            f"PREVIOUS QUESTION: {last_user_msg}\n\n"
                            f"PREVIOUS RESPONSE: {last_assistant_msg[:2000]}{'...' if len(last_assistant_msg) > 2000 else ''}\n\n"
                            f"CURRENT QUESTION: {user_message}\n\n"
                            f"⚠️⚠️⚠️ CRITICAL: When the user says 'this' or 'that', they are referring to the PREVIOUS QUESTION and RESPONSE above.\n"
                            f"You MUST base your answer EXCLUSIVELY on the PREVIOUS QUESTION and RESPONSE context.\n"
                            f"Do NOT use any other data or default to generic responses like 'top 10 brands'.\n"
                            f"Your response MUST be about the PREVIOUS QUESTION and RESPONSE content.\n"
                            f"{'='*80}\n\n"
                        )
                        logger.info(f"🔄 FOLLOW-UP context prepared: Previous Q: {last_user_msg[:50]}..., Previous A: {last_assistant_msg[:50]}...")
            elif request.conversation_history and not is_different_question:
                # Normal case: use conversation history if not a different question
                for msg in request.conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role in ["user", "assistant"]:
                        conversation_history.append({"role": role, "content": content})
            elif is_different_question:
                logger.info(f"🔄 This is a NEW question (different from previous) - using empty conversation history")
                # Optionally keep only the very last exchange for minimal context
                # But for now, use empty to ensure fresh analysis
            
            # CRITICAL: Generate pivot table BEFORE building prompt so we can reference it
            # Get pivot table data for visualization - make it relevant to the question
            # BUT: For follow-up questions, we should NOT generate a new pivot table that might override context
            # Instead, we'll use the previous response's context
            pivot_table = []
            if not is_follow_up_question:
                # Only generate pivot table for new questions, not follow-ups
                pivot_table = await self._generate_pivot_table(request, query, user_msg_lower, chart_title_lower)
            else:
                logger.info(f"🔄 FOLLOW-UP question - skipping pivot table generation to preserve previous context")
            
            # Log pivot table for debugging
            if pivot_table and len(pivot_table) > 0:
                logger.info(f"📊 Pivot table generated with {len(pivot_table)} rows - will be included in LLM prompt")
                logger.info(f"📊 First pivot row keys: {list(pivot_table[0].keys())}")
            
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
            
            # CRITICAL: Add hard constraints for quarterly aggregation (as per ChatGPT recommendation)
            quarterly_rules = (
                "You are a business analytics assistant querying structured monthly sales data.\n\n"
                "IMPORTANT RULES (NON-NEGOTIABLE):\n"
                "1. Quarterly terms are ALWAYS implicit aggregations:\n"
                "   - Q1 = January, February, March (ALWAYS)\n"
                "   - Q2 = April, May, June (ALWAYS)\n"
                "   - Q3 = July, August, September (ALWAYS)\n"
                "   - Q4 = October, November, December (ALWAYS)\n"
                "2. The dataset does NOT store quarters explicitly. Quarters MUST be computed by aggregating months.\n"
                "3. If monthly data exists for the requested year(s), business, and metric, you MUST compute the quarterly result.\n"
                "   You are NOT allowed to say 'data not available' or 'Q1 data is not available' in this case.\n"
                "4. You may only say 'data not available' if:\n"
                "   - One or more required months are completely missing from the dataset (e.g., no January data at all), OR\n"
                "   - The requested business or metric truly does not exist in the dataset.\n"
                "5. If a question asks for a comparison, you MUST compute and compare both values numerically whenever possible.\n"
                "6. NEVER infer or speculate. Use only values derived from the aggregated data provided in context.\n"
                "7. The data context provided is the result of correct database aggregation. You MUST treat these numbers as authoritative.\n"
                "   Do NOT question their availability. Do NOT say 'data not available' if the data context shows aggregated values.\n"
                "8. CRITICAL: If the data context shows ANY aggregated values (even yearly totals), you MUST use them to answer the question.\n"
                "   For example, if data shows 'Yearly Breakdown: 2023: Gross Sales €12.3M' and user asks for Q1, use this yearly data.\n"
                "   Do NOT refuse to answer just because Q1-specific breakdown is not shown.\n"
            )
            
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
                f"{quarterly_rules}\n"
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
                "CRITICAL - QUARTER-TO-MONTHS MAPPING (BUSINESS RULE - DO NOT FORGET THIS): "
                "The database does NOT have a 'quarter' field. Quarters are derived from months. "
                "Q1 = January + February + March (data is filtered by these 3 months) "
                "Q2 = April + May + June "
                "Q3 = July + August + September "
                "Q4 = October + November + December "
                "When the user asks for Q1/Q2/Q3/Q4 data, the query filters by the corresponding months. "
                "If Q1 data is requested, it means data for January, February, and March combined. "
                "If the data shows zero values for Q1, it means no data exists for those specific months, NOT that quarters don't exist in the database. "
                "CRITICAL - INTELLIGENT DATA INTERPRETATION: "
                "When the user asks about specific time periods (e.g., 'Q1', 'November 2025') or entities (e.g., 'Food business'), but the exact data is not available: "
                "(1) Check if related data exists (e.g., other quarters, other months, similar business names) "
                "(2) If related data exists, provide analysis based on that and explain what it implies about the requested period/entity "
                "(3) If the data context mentions fallback queries or broader data, use that data to provide insights "
                "(4) Suggest potential reasons why the exact data might not be available (e.g., business name mismatch, time period not in dataset) "
                "(5) NEVER just state 'no data available' - always try to provide value from related available data "
                "(6) NEVER use proxy quarters (e.g., do NOT use Q2 data to estimate Q1) unless the user explicitly asks for estimates "
                "(7) NEVER assume even distribution across quarters unless explicitly stated "
                "For Q1/Q2/Q3/Q4 queries: If Q1 data (January-March) is missing but the business has data in other quarters, analyze those quarters and explain what they suggest about Q1, but DO NOT use them as proxies. "
                "For business name queries: If exact business name doesn't match, check if similar business names exist and suggest the user verify the exact name. "
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
                "Keep it engaging and provide comprehensive analysis in plain business language that any executive can understand. "
                "CRITICAL: Answer the user's question directly using the data provided. "
                "Do NOT explain data limitations unless explicitly asked. "
                "Do NOT suggest next steps unless requested. "
                "Do NOT say 'data not available' if the data context shows aggregated values for the requested period."
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
            
            # Build query intent summary for LLM context (as per ChatGPT recommendation)
            intent_summary = []
            if detected_quarter:
                intent_summary.append(f"Quarter: {detected_quarter} (months: {', '.join(detected_quarter_months)})")
            if detected_business:
                intent_summary.append(f"Business: {detected_business}")
            if detected_years:
                intent_summary.append(f"Years: {', '.join(map(str, detected_years))}")
            if detected_metric:
                intent_summary.append(f"Metric: {detected_metric}")
            if is_across_years:
                intent_summary.append("Comparison: Across all years")
            
            intent_context = ""
            if intent_summary:
                intent_context = f"\nQUERY INTENT (what the user asked for):\n" + "\n".join(f"  - {item}" for item in intent_summary) + "\n"
                intent_context += f"\nIMPORTANT: The database does NOT have a 'quarter' field. "
                intent_context += f"Q1/Q2/Q3/Q4 queries filter by months (e.g., Q1 = January + February + March). "
                intent_context += f"If the data shows zero values, it means no data exists for those specific months/business/years, NOT that quarters don't exist.\n"
            
            # CRITICAL: Add note about pivot table data if available
            pivot_table_note = ""
            if pivot_table and len(pivot_table) > 0:
                # Get the dimension type from first row
                first_row = pivot_table[0]
                dimension_type = None
                dimension_key = None
                if "Brand" in first_row:
                    dimension_type = "brand"
                    dimension_key = "Brand"
                elif "Category" in first_row:
                    dimension_type = "category"
                    dimension_key = "Category"
                elif "Business" in first_row:
                    dimension_type = "business"
                    dimension_key = "Business"
                elif "Customer" in first_row:
                    dimension_type = "customer"
                    dimension_key = "Customer"
                elif "Channel" in first_row:
                    dimension_type = "channel"
                    dimension_key = "Channel"
                elif "Year" in first_row:
                    dimension_type = "year"
                    dimension_key = "Year"
                elif "Month_Name" in first_row:
                    dimension_type = "month"
                    dimension_key = "Month_Name"
                
                if dimension_type and dimension_key:
                    # Format pivot table data for LLM in a clear, structured way
                    # CRITICAL: Use K for values < 1M, M for values >= 1M
                    from app.utils.helpers import format_currency
                    pivot_data_text = "\n".join([
                        f"  {i+1}. {row[dimension_key]}: Revenue {format_currency(row['Revenue'])}, Profit {format_currency(row['Gross_Profit'])} ({row.get('Margin_%', 0):.1f}% margin), Cases {row['Cases']:,.0f}"
                        for i, row in enumerate(pivot_table[:min(len(pivot_table), 10)])  # Show first 10 in prompt
                    ])
                    
                    pivot_table_note = (
                        f"\n\n{'='*80}\n"
                        f"⚠️ CRITICAL: PIVOT TABLE DATA AVAILABLE - YOU MUST USE THIS DATA\n"
                        f"{'='*80}\n"
                        f"A structured pivot table with {len(pivot_table)} {dimension_type}(s) has been generated.\n"
                        f"This pivot table contains the EXACT answer to the user's question.\n"
                        f"\n📊 PIVOT TABLE DATA (Top {min(len(pivot_table), 10)} {dimension_type}s):\n"
                        f"{pivot_data_text}\n"
                        f"\n{'='*80}\n"
                        f"CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE:\n"
                        f"{'='*80}\n"
                        f"1. START your response by listing the EXACT {dimension_type}s from the pivot table above.\n"
                        f"   Example format: '1. [Name]: Revenue €X.XM, Profit €Y.YM (Z.Z% margin), Units N'\n"
                        f"2. List ALL {dimension_type}s from the pivot table (up to the number requested by the user).\n"
                        f"3. Use the EXACT names and numbers from the pivot table - do NOT use generic descriptions.\n"
                        f"4. DO NOT say 'these 5 customers' or 'top customers' - use ACTUAL NAMES like 'Musgrave ROI', 'Dunnes ROI', etc.\n"
                        f"5. DO NOT say 'data not available', 'no breakdown available', or 'I can only provide insights about business data'.\n"
                        f"6. After listing the {dimension_type}s, provide insights and recommendations based on the specific data.\n"
                        f"7. The pivot table will be displayed as charts/tables - your text should complement and explain this visual data.\n"
                        f"\nEXAMPLE OF CORRECT RESPONSE FORMAT:\n"
                        f"Top 5 Customers by Revenue:\n"
                        f"1. Musgrave ROI: Revenue €86.78M, Profit €19.72M (22.73% margin), Units 3.6M\n"
                        f"2. Dunnes ROI: Revenue €84.26M, Profit €22.33M (26.5% margin), Units 3.2M\n"
                        f"... (continue with all 5)\n"
                        f"\nThen provide insights based on these specific numbers.\n"
                        f"{'='*80}\n\n"
                    )
            
            user_prompt = (
                f"{follow_up_context_for_prompt}"  # CRITICAL: Add follow-up context FIRST if it exists
                f"{previous_question_context}"
                f"{chart_context}\n\n"
                f"{intent_context}"
                f"{pivot_table_note if not is_follow_up_question else ''}"  # Skip pivot table note for follow-ups
                f"BUSINESS DATA (USE ONLY THIS DATA - DO NOT USE ANY EXTERNAL KNOWLEDGE):\n"
                f"{data_context}\n\n"
                f"CRITICAL INSTRUCTION: The above 'Business Data' section contains ALL the information you should use to answer the user's question. "
                f"The following data context is the result of correct database aggregation. "
                f"You MUST treat these numbers as authoritative. "
                f"Do NOT question their availability. "
                f"SYSTEM RULE: If Month_Name filter exists in the query (e.g., January, February, March for Q1), the data IS available. "
                f"Never state 'data not available' unless an explicit ⚠️ Note: No data found appears. "
                f"Q1 always means January–March. If you see 'Q1 Performance' or '📌 Quarter Interpretation: Q1', the data EXISTS. "
                f"Do NOT say 'data not available' if the data context shows ANY aggregated values (even if labeled as 'all months' or 'broader data'). "
                f"If you see notes like 'Data shown includes all months', this means the data EXISTS - extract the relevant values and use them. "
                f"Do NOT interpret fallback notes as 'data not available'. "
                f"Do NOT use any external knowledge, world events, news, or information outside this dataset. "
                f"Do NOT search the web or use external APIs to find information about customers, businesses, or any entities mentioned in the question. "
                f"ONLY use the data provided in the 'Business Data' section above. "
                f"If the data shows €0 or 'No data found', state that clearly based ONLY on the provided data, without adding external context or search results. "
                f"{question_independence_note}"
                f"\nIMPORTANT - HANDLING INCOMPLETE DATA:\n"
                f"If the data shows zero values or 'No data found', you should:\n"
                f"(1) FIRST check if there's related data available (e.g., if Q1 data is missing, check if there's data for the business in other quarters or all months)\n"
                f"(2) If related data exists, provide insights based on that available data and explain what it tells us about the requested period\n"
                f"(3) If the data context mentions fallback queries (e.g., 'Data shown includes all months'), acknowledge this and provide analysis based on the available broader data\n"
                f"(4) Suggest what filters might need adjustment to find the specific data requested (e.g., business name might not match exactly)\n"
                f"(5) NEVER just say 'no data available' - always try to provide value from related available data\n"
                f"(6) NEVER use proxy quarters (e.g., do NOT use Q2 data to estimate Q1) unless the user explicitly asks for estimates\n"
                f"CRITICAL: If the data context shows ANY aggregated values (e.g., 'Q1 Performance: Revenue €X.XM', 'Yearly Breakdown: 2023: Gross Sales €Y.YM', "
                f"'Overall Totals: Total Revenue: €Z.ZM'), this means the data EXISTS and has been aggregated correctly. "
                f"You MUST use these values to answer the question. Do NOT say 'data not available' when ANY aggregated values are present.\n"
                f"CRITICAL: Even if the data context shows yearly totals instead of Q1-specific breakdowns, you MUST extract the relevant information. "
                f"For example, if the data shows 'Yearly Breakdown: 2023: Gross Sales €12.3M' and 'Yearly Breakdown: 2024: Gross Sales €13.5M', "
                f"and the user asks for Q1 comparison, you should use these yearly values to provide insights about Q1 trends. "
                f"Say something like: 'Based on the yearly data, Food business shows €12.3M in 2023 and €13.5M in 2024, indicating a positive trend that likely extends to Q1.'\n"
                f"Do NOT say 'Q1 data is not available' when the data context shows ANY aggregated values.\n"
                f"Do NOT interpret the absence of Q1-specific breakdowns as 'data not available' - use the available aggregated data.\n"
                f"\n\nUser Question: {request.message}"
            )
            
            # Add critical reminder for follow-up questions (outside f-string to avoid backslash issue)
            if is_follow_up_question:
                reminder = (
                    "\n\n⚠️⚠️⚠️ CRITICAL REMINDER: This is a FOLLOW-UP question. "
                    "You MUST base your response EXCLUSIVELY on the PREVIOUS QUESTION and RESPONSE shown at the top of this prompt. "
                    "Do NOT use any pivot table data or default responses like 'top 10 brands'. "
                    "Your response MUST be about the PREVIOUS QUESTION and RESPONSE content only. ⚠️⚠️⚠️"
                )
                user_prompt += reminder
            
            # CRITICAL: Add validation note for quarterly queries (as per ChatGPT recommendation)
            if detected_quarter_months and detected_years and detected_business:
                validation_note = (
                    f"\n\nVALIDATION CHECK: "
                    f"The user asked for {detected_quarter} ({', '.join(detected_quarter_months)}) data for business '{detected_business}' in years {detected_years}. "
                    f"If the data context shows any aggregated values for this period, you MUST use them. "
                    f"Do NOT say 'data not available' when aggregated values are present in the data context."
                )
                user_prompt += validation_note
                logger.info(f"🔒 VALIDATION: Added validation note for {detected_quarter} query")
            
            logger.info(f"🤖 Sending to AI - Prompt length: {len(user_prompt)} characters")
            logger.info(f"🤖 System context length: {len(system_context)} characters")
            
            # Query Perplexity API with custom system message to ensure non-technical language
            try:
                ai_response = await query_perplexity(user_prompt, conversation_history, custom_system_message=system_context)
                logger.info(f"✅ AI Response received - Length: {len(ai_response)} characters")
                
                # CRITICAL: Validate response for invalid refusals (as per ChatGPT recommendation)
                if detected_quarter_months and detected_years and detected_business:
                    refusal_phrases = [
                        "not available", "data not available", "no data", "unavailable",
                        "q1 data is not available", "q1-specific data is not available"
                    ]
                    response_lower = ai_response.lower()
                    has_refusal = any(phrase in response_lower for phrase in refusal_phrases)
                    
                    if has_refusal:
                        logger.warning(f"⚠️ REFUSAL VALIDATOR: Response contains refusal but intent suggests data should exist")
                        logger.warning(f"⚠️ Intent: quarter={detected_quarter}, business={detected_business}, years={detected_years}")
                        logger.warning(f"⚠️ This may be an invalid refusal - data context should be checked")
            except Exception as e:
                logger.error(f"❌ Error querying Perplexity: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                ai_response = f"I apologize, but I encountered an error while processing your request. Please try rephrasing your question or contact support if the issue persists. Error: {str(e)}"
            
            # Pivot table was already generated before building the prompt (see line 1169)
            # No need to regenerate it here
            else:
                logger.warning(f"⚠️ WARNING: Pivot table is EMPTY! Message: '{request.message}', Chart: '{request.chart_title}'")
            
            # Get total row count
            total_rows = await self.db.business_data.count_documents(query) if query else await self.db.business_data.count_documents({})
            
            # Generate dynamic follow-up questions based on the question asked
            follow_up_questions = self._generate_follow_up_questions(user_msg_lower, chart_title_lower)
            
            # Format timestamp
            timestamp = datetime.now().strftime("%I:%M %p IST on %B %d, %Y")
            
            # Build response data
            response_data = {
                "pivot_table": pivot_table,
                "columns": ["Revenue", "Gross_Profit", "Cases"],
                "filters": query,
                "is_trend_query": "trend" in (request.message or "").lower(),
                "is_loser_query": any(word in (request.message or "").lower() for word in ["worst", "lowest", "loser", "least"]),
                "total_rows": total_rows,
                "follow_up_questions": follow_up_questions
            }
            
            # CRITICAL: Log response data structure
            logger.info(f"📊 RESPONSE DATA - pivot_table length: {len(response_data['pivot_table'])}, columns: {response_data['columns']}")
            
            return InsightsChatResponse(
                response=ai_response,
                timestamp=timestamp,
                needs_clarification=False,
                suggested_questions=[],
                context=data_context,
                data=response_data
            )
            
        except Exception as e:
            logger.error(f"View Insights Chat error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def process_chat_stream(
        self, 
        request: InsightsChatRequest,
        think: bool = False
    ):
        """
        Streaming version of process_chat
        Yields chunks as they are generated by LLM
        
        Args:
            request: Chat request
            think: Enable thinking mode for supported models
            
        Yields:
            Dict with "type" (thinking/content/done) and "data" (text chunk)
        """
        try:
            logger.info(f"📊 View Insights Chat Stream - Chart: {request.chart_title}, Message: {request.message[:100]}")
            
            user_message = request.message or ""
            user_msg_lower = user_message.lower()
            
            # Check if this is a follow-up question (e.g., "write an email for this", "draft an email for this")
            is_follow_up_question = False
            follow_up_patterns = [
                r'write\s+(an\s+)?(a\s+)?email\s+(for\s+)?(this|that)',
                r'draft\s+(an\s+)?(a\s+)?email\s+(for\s+)?(this|that)',
                r'email\s+(for\s+)?(this|that)',
                r'summarize\s+(this|that)',
                r'explain\s+(this|that)\s+(more|further|in\s+detail)',
                r'tell\s+me\s+more\s+about\s+(this|that)',
                r'what\s+about\s+(this|that)',
                r'can\s+you\s+(write|draft|create|make)\s+(an\s+)?(a\s+)?(email|summary|report)\s+(for\s+)?(this|that)',
            ]
            for pattern in follow_up_patterns:
                if re.search(pattern, user_msg_lower):
                    is_follow_up_question = True
                    logger.info(f"🔄✅ STREAM: Detected FOLLOW-UP question: '{user_message[:50]}...' - Will use conversation history")
                    break
            
            # Skip clarification check for streaming (always proceed)
            # You can add clarification logic here if needed
            
            # Parse query and get data context (same as process_chat)
            parsed_query_result = await parse_query_from_natural_language(user_message, self.db)
            query = parsed_query_result["filters"]
            intent = parsed_query_result["intent"]
            
            # Get comprehensive data context
            data_context = await get_comprehensive_data_context(
                query,
                user_message,
                self.db,
                detected_metric=intent.get("metric", "Gross_Sales")  # Pass detected metric
            )
            # Note: get_comprehensive_data_context returns only a string (data_context), not a tuple
            
            # Build system context (same as process_chat)
            system_context = (
                f"{data_context}\n\n"
                "Answer the user's question based on this data. "
                "Be specific, data-driven, and actionable. "
                "All monetary values are in Euros (€)."
            )
            
            # Build user prompt
            user_prompt = user_message
            
            # Get conversation history - CRITICAL: For follow-up questions, ALWAYS use conversation history
            conversation_history = []
            if is_follow_up_question:
                # For follow-up questions, ALWAYS include conversation history
                logger.info(f"🔄 STREAM: FOLLOW-UP question detected - using FULL conversation history")
                if request.conversation_history:
                    for msg in request.conversation_history:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role in ["user", "assistant"]:
                            conversation_history.append({"role": role, "content": content})
                # Also add explicit context about the previous question/response
                if conversation_history and len(conversation_history) >= 2:
                    last_user_msg = None
                    last_assistant_msg = None
                    for msg in reversed(conversation_history):
                        if msg.get("role") == "assistant" and not last_assistant_msg:
                            last_assistant_msg = msg.get("content", "")
                        elif msg.get("role") == "user" and not last_user_msg:
                            last_user_msg = msg.get("content", "")
                            if last_assistant_msg:
                                break
                    
                    if last_user_msg and last_assistant_msg:
                        # Add explicit context to help LLM understand what "this" refers to
                        # CRITICAL: This will be prepended to user_prompt
                        follow_up_context = (
                            f"\n\n{'='*80}\n"
                            f"⚠️⚠️⚠️ CRITICAL CONTEXT: This is a FOLLOW-UP question ⚠️⚠️⚠️\n"
                            f"{'='*80}\n"
                            f"The user is asking about their PREVIOUS question and response:\n\n"
                            f"PREVIOUS QUESTION: {last_user_msg}\n\n"
                            f"PREVIOUS RESPONSE: {last_assistant_msg[:2000]}{'...' if len(last_assistant_msg) > 2000 else ''}\n\n"
                            f"CURRENT QUESTION: {user_message}\n\n"
                            f"⚠️⚠️⚠️ CRITICAL: When the user says 'this', 'that', or 'it', they are referring to the PREVIOUS QUESTION and RESPONSE above.\n"
                            f"You MUST base your answer EXCLUSIVELY on the PREVIOUS QUESTION and RESPONSE context.\n"
                            f"Do NOT use any other data or default to generic responses like 'top 10 brands'.\n"
                            f"Your response MUST be about the PREVIOUS QUESTION and RESPONSE content.\n"
                            f"Ignore any pivot table data or other context that might be provided below.\n"
                            f"{'='*80}\n\n"
                        )
                        # Prepend this context to the user message
                        user_prompt = follow_up_context + user_prompt
                        logger.info(f"🔄 STREAM: FOLLOW-UP context added to prompt: Previous Q: {last_user_msg[:50]}..., Previous A: {last_assistant_msg[:50]}...")
                        logger.info(f"🔄 STREAM: FOLLOW-UP context added to prompt: Previous Q: {last_user_msg[:50]}..., Previous A: {last_assistant_msg[:50]}...")
            else:
                # Normal case: use conversation history if available
                conversation_history = request.conversation_history or []
            
            # Stream from LLM
            from app.utils.ai_service import stream_llm
            
            logger.info(f"🔄 Starting LLM stream with think={think}")
            logger.info(f"🔄 User prompt length: {len(user_prompt)}")
            logger.info(f"🔄 System context length: {len(system_context)}")
            
            # Yield chunks immediately as they arrive (no accumulation)
            async for chunk in stream_llm(
                prompt=user_prompt,
                conversation_history=conversation_history,
                custom_system_message=system_context,
                think=think
            ):
                # Yield immediately - this ensures streaming works
                yield chunk
            
            # After streaming completes, generate and send pivot table and metadata
            logger.info("🔄 Streaming complete, generating pivot table and metadata")
            
            # Generate pivot table (same logic as process_chat)
            pivot_table = await self._generate_pivot_table(request, query, user_msg_lower, request.chart_title.lower() if request.chart_title else "")
            
            # Get total rows
            total_rows = await self.db.business_data.count_documents(query) if query else await self.db.business_data.count_documents({})
            
            # Generate follow-up questions
            follow_up_questions = self._generate_follow_up_questions(user_msg_lower, request.chart_title.lower() if request.chart_title else "")
            
            # Send final metadata
            yield {
                "type": "metadata",
                "data": {
                    "pivot_table": pivot_table,
                    "columns": ["Revenue", "Gross_Profit", "Cases"],
                    "filters": query,
                    "is_trend_query": "trend" in user_msg_lower,
                    "is_loser_query": any(word in user_msg_lower for word in ["worst", "lowest", "loser", "least"]),
                    "total_rows": total_rows,
                    "follow_up_questions": follow_up_questions,
                    "needs_clarification": False,
                    "suggested_questions": []
                }
            }
                
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield {
                "type": "error",
                "data": f"Error: {str(e)}"
            }
    
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
            # CRITICAL: Check questions in order of specificity to avoid conflicts
            # Priority: Year comparisons > Category > Brand > Customer > Channel > Business > Trends
            
            # Check for year-over-year comparisons FIRST (highest priority)
            # Pattern: "compare X in 2023 and 2024", "2023 vs 2024", "across years"
            is_year_comparison = (
                re.search(r'compare.*\d{4}.*\d{4}', user_msg_lower) is not None or
                re.search(r'\d{4}.*and.*\d{4}', user_msg_lower) is not None or
                re.search(r'\d{4}.*vs.*\d{4}', user_msg_lower) is not None or
                re.search(r'across\s+years?', user_msg_lower) is not None or
                (re.search(r'\d{4}', user_msg_lower) is not None and 'compare' in user_msg_lower and len(re.findall(r'\d{4}', user_msg_lower)) >= 2)
            )
            
            if is_year_comparison:
                logger.info("Detected YEAR COMPARISON question - generating year-based pivot table")
                # User is comparing across years - show year-by-year breakdown
                match_stage = {"$match": query} if query else {"$match": {}}
                
                pipeline_pivot = [
                    match_stage,
                    {
                        "$group": {
                            "_id": "$Year",
                            "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                            "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                        }
                    },
                    {"$match": {"_id": {"$nin": [None, "", "Unknown", "null", "None"]}}},
                    {"$sort": {"_id": 1}}  # Sort by year ascending
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
                                "Year": year,  # Store as integer
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Cases": safe_float(item.get("Cases", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
                            logger.info(f"  Added year {year}: Revenue {revenue}")
                
                logger.info(f"📊 Final year comparison pivot table has {len(pivot_table)} years")
            
            # Check for category questions (before brand, as "category" might be in "brand category")
            elif "category" in user_msg_lower or "categories" in user_msg_lower or "category" in chart_title_lower:
                logger.info("Detected CATEGORY question - generating category-level pivot table")
                # User asked about categories - show category-level aggregated data
                match_stage = {"$match": query} if query else {"$match": {}}
                
                # Detect how many categories requested
                category_limit = 15  # Default
                message_numbers = re.findall(r'\b(\d+)\b', user_msg_lower)
                if message_numbers:
                    try:
                        valid_numbers = [int(num) for num in message_numbers if 1 <= int(num) <= 50]
                        if valid_numbers:
                            category_limit = max(valid_numbers)
                            logger.info(f"✅ Detected category limit from USER MESSAGE: {category_limit}")
                    except:
                        pass
                
                # If no number in message, check chart title
                if category_limit == 15:
                    chart_numbers = re.findall(r'\b(\d+)\b', chart_title_lower)
                    if chart_numbers:
                        try:
                            valid_chart_numbers = [int(num) for num in chart_numbers if 1 <= int(num) <= 50]
                            if valid_chart_numbers:
                                category_limit = max(valid_chart_numbers)
                                logger.info(f"✅ Detected category limit from CHART TITLE: {category_limit}")
                        except:
                            pass
                
                logger.info(f"Category pivot table: Final limit = {category_limit} for message: '{request.message}'")
                
                pipeline_pivot = [
                    match_stage,
                    {
                        "$group": {
                            "_id": "$Category",
                            "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                            "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                        }
                    },
                    {"$match": {"_id": {"$nin": [None, "", "Unknown", "null", "None"]}}},
                    {"$sort": {"Revenue": -1}},
                    {"$limit": category_limit + 5}  # Get extra to ensure we have enough after filtering
                ]
                
                logger.info(f"📊 Category pipeline: {json.dumps(pipeline_pivot, default=str)[:300]}...")
                
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(category_limit + 5)
                logger.info(f"📊 Category pivot results count: {len(pivot_results)} (will show top {category_limit})")
                
                categories_added = 0
                for item in pivot_results:
                    if categories_added >= category_limit:
                        logger.info(f"✅ Reached requested limit of {category_limit} categories, stopping")
                        break
                    category_name = str(item.get("_id", ""))
                    if category_name and category_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Category": category_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Cases": safe_float(item.get("Cases", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
                            categories_added += 1
                            logger.info(f"  Added category {categories_added}/{category_limit}: {category_name} - Revenue: {revenue}")
                            if len(pivot_table) >= category_limit:
                                logger.info(f"Category pivot table: Reached limit of {category_limit}, stopping")
                                break
                
                logger.info(f"📊 Final category pivot table has {len(pivot_table)} categories")
            
            # Check for brand questions (after category to avoid conflicts)
            elif "brand" in user_msg_lower or "brand" in chart_title_lower:
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
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                "Cases": safe_float(item.get("Cases", 0))
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
                                "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                    "Cases": safe_float(item.get("Cases", 0))
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
                                "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                    "Cases": safe_float(item.get("Cases", 0))
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
                                "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                    "Cases": safe_float(item.get("Cases", 0))
                                }
                                pivot_table.append(pivot_row)
            
            elif "customer" in user_msg_lower or "customer" in chart_title_lower:
                logger.info("Detected CUSTOMER question - generating customer-level pivot table")
                # User asked about customers - show customer-level aggregated data
                match_stage = {"$match": query} if query else {"$match": {}}
                
                # Detect how many customers requested
                customer_limit = 15  # Default
                message_numbers = re.findall(r'\b(\d+)\b', user_msg_lower)
                if message_numbers:
                    try:
                        valid_numbers = [int(num) for num in message_numbers if 1 <= int(num) <= 50]
                        if valid_numbers:
                            customer_limit = max(valid_numbers)
                            logger.info(f"✅ Detected customer limit from USER MESSAGE: {customer_limit}")
                    except:
                        pass
                
                # If no number in message, check chart title
                if customer_limit == 15:
                    chart_numbers = re.findall(r'\b(\d+)\b', chart_title_lower)
                    if chart_numbers:
                        try:
                            valid_chart_numbers = [int(num) for num in chart_numbers if 1 <= int(num) <= 50]
                            if valid_chart_numbers:
                                customer_limit = max(valid_chart_numbers)
                                logger.info(f"✅ Detected customer limit from CHART TITLE: {customer_limit}")
                        except:
                            pass
                
                logger.info(f"Customer pivot table: Final limit = {customer_limit} for message: '{request.message}'")
                
                pipeline_pivot = [
                    match_stage,
                    {
                        "$group": {
                            "_id": "$Customer",
                            "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                            "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                        }
                    },
                    {"$match": {"_id": {"$nin": [None, "", "Unknown", "null", "None"]}}},
                    {"$sort": {"Revenue": -1}},
                    {"$limit": customer_limit + 5}  # Get extra to ensure we have enough after filtering
                ]
                pivot_results = await self.db.business_data.aggregate(pipeline_pivot).to_list(customer_limit + 5)
                logger.info(f"📊 Customer pivot results count: {len(pivot_results)} (will show top {customer_limit})")
                
                customers_added = 0
                for item in pivot_results:
                    if customers_added >= customer_limit:
                        logger.info(f"✅ Reached requested limit of {customer_limit} customers, stopping")
                        break
                    customer_name = str(item.get("_id", ""))
                    if customer_name and customer_name.lower() not in ["unknown", "none", "", "null"]:
                        revenue = safe_float(item.get("Revenue", 0))
                        if revenue > 0:
                            pivot_row = {
                                "Customer": customer_name,
                                "Revenue": revenue,
                                "Gross_Profit": safe_float(item.get("Gross_Profit", 0)),
                                "Cases": safe_float(item.get("Cases", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
                            customers_added += 1
                            logger.info(f"  Added customer {customers_added}/{customer_limit}: {customer_name} - Revenue: {revenue}")
                            if len(pivot_table) >= customer_limit:
                                logger.info(f"Customer pivot table: Reached limit of {customer_limit}, stopping")
                                break
                
                logger.info(f"📊 Final customer pivot table has {len(pivot_table)} customers")
            
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
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                "Cases": safe_float(item.get("Cases", 0))
                            }
                            if revenue > 0:
                                pivot_row["Margin_%"] = round((pivot_row["Gross_Profit"] / revenue * 100), 2)
                            else:
                                pivot_row["Margin_%"] = 0.0
                            pivot_table.append(pivot_row)
            
            elif ("channel" in user_msg_lower or "channels" in user_msg_lower or "channel" in chart_title_lower) and not is_year_comparison:
                # CRITICAL: Only detect channel if NOT a year comparison
                # Don't use "sales" as a trigger - it's too broad and catches year comparison questions
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
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                "Cases": safe_float(item.get("Cases", 0))
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
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                "Cases": safe_float(item.get("Cases", 0))
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
                            "Cases": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
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
                                "Cases": safe_float(item.get("Cases", 0))
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

