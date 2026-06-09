"""
AI Service Orchestrator
Main service that coordinates the complete AI chatbot flow:
Question → Intent → RBAC → Cache → SQL → ClickHouse → Explanation → Response
"""
import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional

from app.core.database import get_database
from app.database.clickhouse_client import ClickHouseClient
from app.services.ai.ai_intent_service import AIIntentService
from app.services.ai.ai_query_builder import AIQueryBuilder
from app.services.ai.ai_cache_service import AICacheService
from app.services.ai.ai_response_service import AIResponseService
from app.services.ai.ai_clarity_service import AIClarityService
from app.services.ai.utils.permission_hash import generate_permissions_hash
from app.services.ai.utils.intent_hash import generate_intent_hash
from app.services.ai.utils.access import is_wildcard_access
from app.utils.narrative_generator import generate_narrative

logger = logging.getLogger(__name__)


class AIService:
    """
    Main AI Chatbot Service
    
    Orchestrates the complete flow:
    1. Extract intent from question
    2. Load RBAC from MongoDB
    3. Check cache
    4. Build SQL query
    5. Execute on ClickHouse
    6. Generate explanation
    7. Return response
    """
    
    def __init__(self):
        """Initialize AI service"""
        self.intent_service = AIIntentService()
        self.query_builder = AIQueryBuilder()
        self.cache_service = AICacheService()
        self.response_service = AIResponseService()
        self.clarity_service = AIClarityService()
        self.clickhouse_client = ClickHouseClient()
        self.db = get_database()
    
    async def process_question(
        self,
        question: str,
        user_email: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Process user question and return AI response
        
        Complete flow:
        1. Load RBAC from MongoDB (ALWAYS - security)
        2. Extract intent from question (LLM)
        3. Check cache (with permission_hash + intent_hash)
        4. If cache miss: Build SQL → Execute → Cache result
        5. Generate explanation (LLM)
        6. Return response
        
        Args:
            question: User's question
            user_email: User email (from JWT)
            tenant_id: Tenant identifier
        
        Returns:
            Response dict with:
            {
                "response": "Your Food business generated...",
                "data": [...],  # Raw ClickHouse results
                "cached": False  # Whether response was from cache
            }
        """
        t_start = time.perf_counter()
        logger.info("DATA_SOURCE=ClickHouse | AI Chatbot — analytics data from ClickHouse (Mac Studio)")
        try:
            # STEP 1: Load RBAC from MongoDB (CRITICAL - must happen before cache)
            user = await self._load_user_rbac(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")
            
            access = user.get("access", {})
            if not access:
                raise ValueError(f"User has no access permissions: {user_email}")
            
            logger.info(f"Loaded RBAC for user: {user_email}")

            # STEP 1.25: Quick RBAC phrase-level guard for obvious brand/business questions
            q_lower = question.strip().lower()

            def _no_access(list_or_str) -> bool:
                if list_or_str is None:
                    return True
                if isinstance(list_or_str, list):
                    return len(list_or_str) == 0
                return False

            # If user has no brand access and question clearly asks about brands, short-circuit
            if _no_access(access.get("brands")) and (" brand" in q_lower or " brands" in q_lower):
                response_ms = int((time.perf_counter() - t_start) * 1000)
                return {
                    "response": (
                        "You don't currently have permission to view brand-level data for this question. "
                        "Please contact your system administrator if you believe you should have access."
                    ),
                    "data": [],
                    "pivot_table": [],
                    "cached": False,
                    "intent": None,
                    "debug": {},
                    "data_source": "ClickHouse",
                    "response_ms": response_ms,
                    "needs_clarification": False,
                    "suggested_questions": [],
                }

            # If user has no business access and question clearly asks about businesses, short-circuit
            if _no_access(access.get("businesses")) and (" business" in q_lower or " businesses" in q_lower):
                response_ms = int((time.perf_counter() - t_start) * 1000)
                return {
                    "response": (
                        "You don't currently have permission to view business-level data for this question. "
                        "Please contact your system administrator if you believe you should have access."
                    ),
                    "data": [],
                    "pivot_table": [],
                    "cached": False,
                    "intent": None,
                    "debug": {},
                    "data_source": "ClickHouse",
                    "response_ms": response_ms,
                    "needs_clarification": False,
                    "suggested_questions": [],
                }

            # STEP 1.5: Check if question needs clarification (same as live insights chatbot)
            is_clear, suggested_questions = await self.clarity_service.check_question_clarity(question)
            if not is_clear:
                if not suggested_questions:
                    suggested_questions = self.clarity_service._fallback_suggested_questions(question)[:6]
                response_ms = int((time.perf_counter() - t_start) * 1000)
                logger.info("DATA_SOURCE=ClickHouse | returning clarification (question unclear), response_ms=%s", response_ms)
                return {
                    "response": (
                        "I want to make sure I understand your question correctly. "
                        "Could you please select one of these clarified versions, or rewrite your question?"
                    ),
                    "data": [],
                    "pivot_table": [],
                    "cached": False,
                    "intent": None,
                    "debug": {},
                    "data_source": "ClickHouse",
                    "response_ms": response_ms,
                    "needs_clarification": True,
                    "suggested_questions": suggested_questions,
                }

            # STEP 2: Extract intent from question (LLM)
            intent = await self.intent_service.extract_intent(question)
            logger.info("AI_SERVICE | question=%s", question)
            logger.info("AI_SERVICE | intent=%s", intent)

            # STEP 2.5: If user asked for a specific entity they don't have access to, deny with a clear message
            # (avoids returning "0 data" or relying on query/cache to contain "1 = 0")
            intent_filters = (intent or {}).get("filters") or {}
            access_key_map = {
                "business": "businesses",
                "brand": "brands",
                "channel": "channels",
                "category": "categories",
                "sub_category": "sub_categories",
                "customer": "customers",
                "sku": "sku",
            }

            for dimension, access_key in access_key_map.items():
                requested = intent_filters.get(dimension) or []
                if not requested:
                    continue
                allowed = access.get(access_key)
                if allowed is None:
                    allowed = []
                # Wildcard access (e.g. admin with businesses=["*"] or "all") — skip the deny check
                if is_wildcard_access(allowed):
                    continue
                if not isinstance(allowed, list):
                    allowed = []
                allowed_lower = [str(x).strip().lower() for x in allowed if x]
                requested_lower = [str(x).strip().lower() for x in requested if x]
                missing = [v for v in requested_lower if v not in allowed_lower]
                if not missing:
                    continue
                # User requested at least one entity they don't have access to
                denied_names = [x for x in requested if str(x).strip().lower() in missing]
                entity_label = (denied_names or requested)[0]
                if dimension == "business":
                    phrase = f"data for '{entity_label}' business"
                elif dimension == "brand":
                    phrase = f"data for '{entity_label}' brand"
                elif dimension == "channel":
                    phrase = f"data for '{entity_label}' channel"
                elif dimension == "category":
                    phrase = f"data for '{entity_label}' category"
                elif dimension == "sub_category":
                    phrase = f"data for '{entity_label}' sub-category"
                elif dimension == "customer":
                    phrase = f"data for '{entity_label}' customer"
                else:
                    phrase = f"data for '{entity_label}'"
                response_ms = int((time.perf_counter() - t_start) * 1000)
                logger.info("AI_SERVICE | user requested entity without access: dimension=%s requested=%s", dimension, denied_names)
                return {
                    "response": (
                        f"You don't have permission to view {phrase}. "
                        "Please contact your system administrator if you believe you should have access."
                    ),
                    "data": [],
                    "pivot_table": [],
                    "cached": False,
                    "intent": intent,
                    "debug": {},
                    "data_source": "ClickHouse",
                    "response_ms": response_ms,
                    "needs_clarification": False,
                    "suggested_questions": [],
                }
            
            # STEP 3: Check cache and get result
            # Cache service handles: permission_hash, intent_hash, data_version
            debug_info: Dict[str, Any] = {}
            async def query_function():
                """Query function executed on cache miss"""
                # STEP 4: Build SQL query from intent + RBAC
                query, is_lifetime = self.query_builder.build_query(
                    intent=intent,
                    access=access,
                    tenant_id=tenant_id
                )
                debug_info["query"] = query
                debug_info["is_lifetime"] = is_lifetime
                logger.info("AI_SERVICE | sql_query=%s", query)
                # Keep ClickHouse AI chatbot aligned with live dashboard behavior:
                # if user doesn't ask a time range explicitly, query full history.
                # Query builder already injects explicit time conditions when requested.
                enforce_default_time_filter = False if not is_lifetime else False
                debug_info["enforce_time_filter"] = enforce_default_time_filter
                logger.info("AI_SERVICE | enforce_time_filter=%s", enforce_default_time_filter)
                
                # STEP 5: Execute on ClickHouse
                # Pass is_lifetime to skip default time filter if user asked for lifetime
                result = self.clickhouse_client.execute_dict(
                    query=query,
                    tenant_id=tenant_id,
                    enforce_time_filter=enforce_default_time_filter
                )
                debug_info["row_count"] = len(result) if isinstance(result, list) else -1
                debug_info["result_preview"] = result[:3] if isinstance(result, list) else result
                logger.info("AI_SERVICE | db_result_rows=%s preview=%s", len(result), result[:3] if isinstance(result, list) else result)
                
                return result
            
            # Get result (from cache or query)
            result_data = await self.cache_service.get_or_set_cache(
                tenant_id=tenant_id,
                access=access,
                intent=intent,
                query_function=query_function
            )
            logger.info("AI_SERVICE | final_result_rows=%s", len(result_data) if isinstance(result_data, list) else -1)
            
            # Safeguard 1: if query returned no data due to RBAC (no access), return a clear RBAC message
            rows = result_data if isinstance(result_data, list) else []
            query_str = str(debug_info.get("query", "") or "")
            if len(rows) == 0 and "1 = 0" in query_str:
                # RBAC layer deliberately denied this query (no access to requested dimension)
                response_ms = int((time.perf_counter() - t_start) * 1000)
                logger.info("AI_SERVICE | no data due to RBAC (1 = 0 in query), returning access-denied explanation")

                # Detect which dimension was restricted (business, brand, category, channel, customer, sku)
                denied_dimension = None
                dim_order = ["business", "brand", "category", "channel", "customer", "sku"]
                intent_dims = (intent or {}).get("dimensions") or []
                intent_filters = (intent or {}).get("filters") or {}
                access_cfg = access or {}
                access_key_map = {
                    "business": "businesses",
                    "channel": "channels",
                    "brand": "brands",
                    "category": "categories",
                    "sub_category": "sub_categories",
                    "customer": "customers",
                    "sku": "sku",
                }
                for dim in dim_order:
                    if dim not in access_key_map:
                        continue
                    access_key = access_key_map[dim]
                    allowed = access_cfg.get(access_key)
                    # Treat None or empty list as no access
                    no_access = allowed is None or (isinstance(allowed, list) and len(allowed) == 0)
                    dim_used = dim in intent_dims or (intent_filters.get(dim) or [])
                    if no_access and dim_used:
                        denied_dimension = dim
                        break

                if denied_dimension == "business":
                    access_phrase = "business-level data"
                elif denied_dimension == "brand":
                    access_phrase = "brand-level data"
                elif denied_dimension == "category":
                    access_phrase = "category-level data"
                elif denied_dimension == "channel":
                    access_phrase = "channel-level data"
                elif denied_dimension == "customer":
                    access_phrase = "customer-level data"
                elif denied_dimension == "sku":
                    access_phrase = "SKU-level data"
                else:
                    access_phrase = "this data"

                rbac_message = (
                    f"You don't currently have permission to view {access_phrase} for this question. "
                    "Please contact your system administrator if you believe you should have access."
                )
                return {
                    "response": rbac_message,
                    "data": [],
                    "pivot_table": [],
                    "cached": False,
                    "intent": intent,
                    "debug": debug_info,
                    "data_source": "ClickHouse",
                    "response_ms": response_ms,
                    "needs_clarification": False,
                    "suggested_questions": [],
                }
            
            # Safeguard 2: if query returned no data and question is off-topic (e.g. Iran, incident), do not generate an answer — return clarification
            if len(rows) == 0 and self.clarity_service._is_off_topic(question.strip().lower()):
                response_ms = int((time.perf_counter() - t_start) * 1000)
                logger.info("AI_SERVICE | no data and question is off-topic, returning clarification (no LLM answer)")
                return {
                    "response": (
                        "I can only provide insights from our business data (revenue, profit, brands, businesses, categories). "
                        "There is no data for that. Please choose one of the questions below or ask about brands, businesses, or categories we have."
                    ),
                    "data": [],
                    "pivot_table": [],
                    "cached": False,
                    "intent": intent,
                    "debug": debug_info,
                    "data_source": "ClickHouse",
                    "response_ms": response_ms,
                    "needs_clarification": True,
                    "suggested_questions": self.clarity_service._fallback_off_topic_suggestions(),
                }
            
            # Check if result was cached (for response metadata)
            cached = False  # TODO: Return cache status from cache_service
            
            # STEP 5b: Response cache — reuse LLM explanation when same question + same data (avoids slow LLM call)
            # Include question_hash so different questions (e.g. "compare KOKA, Green Aware..." vs "compare Bonne Maman with other brands")
            # do not return the same cached explanation when they happen to produce the same intent/result.
            result_hash = hashlib.sha256(
                json.dumps(result_data, sort_keys=True, default=str).encode()
            ).hexdigest()[:24]
            question_hash = hashlib.sha256(
                question.strip().lower().encode("utf-8")
            ).hexdigest()[:24]
            permissions_hash = generate_permissions_hash(access)
            intent_hash = generate_intent_hash(intent)
            cached_explanation = await self.cache_service.get_cached_response(
                tenant_id, permissions_hash, intent_hash, result_hash, question_hash
            )
            if cached_explanation is not None:
                logger.info("AI_SERVICE | using cached explanation (skip LLM)")
                explanation = cached_explanation
            else:
                # STEP 6: Generate explanation from data (LLM)
                explanation = await self.response_service.generate_response(
                    question=question,
                    data=result_data,
                    intent=intent
                )
                await self.cache_service.set_cached_response(
                    tenant_id, permissions_hash, intent_hash, result_hash, question_hash, explanation
                )
            
            # STEP 7: Build pivot_table for frontend charts/tables (same shape as live insights)
            pivot_table = self._data_to_pivot_table(result_data)

            # STEP 7b: Storytelling Mode — build a short, deterministic narrative from the data
            try:
                narrative = generate_narrative(pivot_table)
            except Exception as nar_err:  # narrative must never break the response
                logger.warning("Narrative generation failed: %s", nar_err)
                narrative = []

            # STEP 8: Return response
            response_ms = int((time.perf_counter() - t_start) * 1000)
            logger.info(f"DATA_SOURCE=ClickHouse | response_ms={response_ms} | returning response (data from ClickHouse)")
            return {
                "response": explanation,
                "data": result_data,
                "pivot_table": pivot_table,
                "narrative": narrative,
                "cached": cached,
                "intent": intent,  # Include for debugging
                "debug": debug_info,
                "data_source": "ClickHouse",
                "response_ms": response_ms,
                "needs_clarification": False,
                "suggested_questions": [],
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"AI service error: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _data_to_pivot_table(rows: list) -> list:
        """
        Convert ClickHouse result rows to pivot_table shape for frontend charts/tables.
        Maps: year->Year, revenue->Revenue, gross_profit->Gross_Profit, total_cases->Cases, margin_pct->Margin_%
        """
        if not rows:
            return []
        pivot = []
        key_map = {
            "year": "Year",
            "revenue": "Revenue",
            "gross_profit": "Gross_Profit",
            "total_cases": "Cases",
            "margin_pct": "Margin_%",
            "business": "Business",
            "channel": "Channel",
            "brand": "Brand",
            "category": "Category",
            "customer": "Customer",
            "month_name": "Month_Name",
            "month": "Month",
        }
        for r in rows:
            if not isinstance(r, dict):
                continue
            row = {}
            for k, v in r.items():
                key = k if isinstance(k, str) else str(k)
                out_key = key_map.get(key.lower())
                if out_key is None:
                    out_key = key.replace("_", " ").title().replace(" ", "_")
                row[out_key] = v
            pivot.append(row)
        return pivot

    async def _load_user_rbac(self, user_email: str) -> Optional[Dict[str, Any]]:
        """
        Load user RBAC from MongoDB
        
        Args:
            user_email: User email
        
        Returns:
            User document with access field, or None if not found
        """
        try:
            users_collection = self.db.users
            user = await users_collection.find_one({"email": user_email})
            return user
        except Exception as e:
            logger.error(f"Failed to load user RBAC: {e}")
            return None
