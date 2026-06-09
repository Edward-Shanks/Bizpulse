"""
AI Intent Service
Extracts structured intent from user questions using LLM
"""
import json
import logging
import re
from typing import Dict, Any, Optional

from app.utils.ai_service import query_llm

logger = logging.getLogger(__name__)


class AIIntentService:
    """
    AI Intent Extraction Service
    
    Converts user questions into structured intent JSON that can be used
    to build ClickHouse SQL queries safely.
    """
    
    INTENT_EXTRACTION_PROMPT = """You are an AI assistant that extracts structured intent from business analytics questions.

Convert the user's question into a JSON object with the following structure:
{
    "metric": "gsales" | "fgp" | "cases" | "price_downs" | "perm_disc" | "transfer_cost" | "group_cost" | "lta",
    "dimensions": ["business"] | ["channel"] | ["brand"] | ["category"] | ["customer"] | ["sub_category"] | ["sku"] | ["year"] | ["quarter"] | ["month_name"] | [],
    "filters": {
        "business": ["Food"] | [],
        "channel": ["Grocery"] | [],
        "brand": ["Cali Cali"] | [],
        "category": ["Snacks"] | [],
        "sub_category": ["Chips"] | [],
        "customer": ["Amazon"] | [],
        "sku": ["SKU123"] | [],
        "year": [2023, 2024] | [],
        "quarter": [1,2,3,4] | [],
        "month_name": ["Jan"] | []
    },
    "time_range": {
        "type": "last_n_days" | "last_n_months" | "current_month" | "last_year" | "lifetime" | "custom",
        "value": 6  // for last_n_days, last_n_months, etc.
    },
    "aggregation": "sum" | "avg" | "count" | "max" | "min",
    "limit": 10  // for top N questions; default 1000
}

Rules:
1. If user asks for "lifetime", "all time", "all history" → time_range.type = "lifetime"
2. If user asks for "last 6 months" → time_range.type = "last_n_months", value = 6
3. If user asks for "last 7 days" → time_range.type = "last_n_days", value = 7
4. If user asks for "current month" → time_range.type = "current_month"
5. If no time mentioned → time_range.type = "custom", value = null (backend will apply default)
6. Extract metric from question (revenue = gsales, profit = fgp, etc.)
7. Extract dimensions for grouping (by business, by channel, etc.)
8. Extract filters from question (for Food business, for Grocery channel, etc.)
9. Default aggregation is "sum" unless specified
10. If question says "top N", set limit=N
11. For year-over-year or multi-year comparison (e.g. "Q1 2022, 2023, 2024", "compare 2023 and 2024"): put ALL mentioned years in filters.year (e.g. [2022, 2023, 2024]), put quarter in filters.quarter if Q1/Q2/Q3/Q4 mentioned (e.g. [1]), include "year" in dimensions, and set time_range.type = "lifetime" so the query uses only year/quarter filters (data for missing years will be omitted by the database; the answer will show available years).
12. CRITICAL - "Compare X with other brands": If the user asks to compare a brand with other brands (e.g. "Compare brand Bonne Maman with other brands", "Bonne Maman vs other brands", "compare X to other brands"), set dimensions to ["brand"], leave filters.brand EMPTY ([]), and set limit to 20 or 25. Do NOT put the mentioned brand name in filters.brand—the query must return ALL brands so the answer can compare that brand against others. Same idea for "compare business X with other businesses" or "compare category X with other categories": leave that entity's filter empty and set the matching dimension.
13. CRITICAL - "Compare brand A and B" (two or more named brands): If the user asks to compare specific brands by name (e.g. "Compare brand Killeen and Koka brand", "compare Koka, Killeen and McDonnells"), set dimensions to ["brand"], leave filters.brand EMPTY ([]), and set limit to 20 or 25. Return ALL brands so the answer can compare the named ones in context. Do NOT set filters.brand to only the named brands—same as rule 12.
14. "Compare X performance in Channel A vs B" (e.g. "Compare Kinetica performance in Convenience vs Grocery"): Set dimensions to ["channel"], filters.brand to the mentioned entity (e.g. ["Kinetica"]), and filters.channel to the two channels (e.g. ["Convenience", "Grocery"]) so the query returns one row per channel for that brand.
15. "Before and after January 2024" or "sales before and after [month] [year]": To return comparable data, set time_range to last_n_months 24 (or 12) and include "month_name" in dimensions so the answer can show before/after breakdown. Do not leave time_range empty.
16. Specific month or year: If the user asks for a particular month (e.g. "in January", "January 2024", "Jan", "for March", "first month", "1st month", "month 1"), set filters.month_name to the abbreviated month (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec). If they mention a year (e.g. 2024), set filters.year to [that year]. Use time_range.type = "lifetime" when filtering by a specific month so the query uses year + month_name filters. "First month" or "month 1" = January (Jan), "second month" = February (Feb), etc.
17. Quarter: If the user says "Q1", "Q2", "quarter 1", "quarter1", "quarter 2", "quarter two", "quarter one", set filters.quarter to [1], [2], [3], or [4] accordingly. If they mention a year, set filters.year. Use time_range.type = "lifetime" when quarter is set so only year/quarter filters apply. "Top 5 business in Q1" = dimensions ["business"], limit 5, filters.quarter [1], and year if mentioned.
18. CRITICAL — Natural "X and Y business" phrases (NOT compare): If the user asks "how X and Y business performs", "how X, Y and Z business is doing", "tell me X and Y business in 2024", "show X business and Y business", or any similar phrasing where the word IMMEDIATELY before "business" / "businesses" is an entity list, those entities are BUSINESS filter values. Set filters.business = [X, Y, Z], include "business" in dimensions. Do NOT classify them as brands. Do NOT include "brand" in dimensions and do NOT set filters.brand unless the user EXPLICITLY uses the word "brand" or "brands". Same rule for "X and Y channel" → filters.channel; "X and Y category" → filters.category; "X and Y customer" → filters.customer.

Return ONLY valid JSON, no explanation.

User question: {question}

Intent JSON:"""

    def __init__(self):
        """Initialize intent service"""
        pass
    
    async def extract_intent(self, question: str) -> Dict[str, Any]:
        """
        Extract structured intent from user question
        
        Args:
            question: User's question (e.g., "Show revenue for Food business last 6 months")
        
        Returns:
            Intent dict with metric, dimensions, filters, time_range, aggregation
        
        Example:
            >>> question = "Show revenue for Food business last 6 months"
            >>> intent = await service.extract_intent(question)
            >>> # Returns:
            >>> {
            >>>     "metric": "gsales",
            >>>     "dimensions": ["business"],
            >>>     "filters": {"business": ["Food"]},
            >>>     "time_range": {"type": "last_n_months", "value": 6},
            >>>     "aggregation": "sum"
            >>> }
        """
        try:
            # IMPORTANT: Don't use .format() on raw JSON template braces.
            # It raises KeyError and causes fallback intent for almost every question.
            prompt = self.INTENT_EXTRACTION_PROMPT.replace("{question}", question)
            
            # Use low temperature for deterministic intent extraction
            response = await query_llm(
                prompt=prompt,
                temperature=0.1,  # Very low temperature for consistent JSON
                max_tokens=500,
                custom_system_message="You are a JSON extraction assistant. Return only valid JSON."
            )
            logger.info("AI_INTENT | raw_llm_response=%s", response[:1200])
            
            # Clean response (remove markdown code blocks if present)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON
            intent = json.loads(response)
            
            # Validate and normalize intent (pass question for compare-with-others detection)
            intent = self._normalize_intent(intent, question)
            
            logger.info("AI_INTENT | parsed_intent=%s", json.dumps(intent, ensure_ascii=True))
            return intent
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent JSON: {e}")
            logger.error(f"LLM response: {response}")
            # Return default intent
            return self._get_default_intent(question)
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return self._get_default_intent(question)
    
    def _normalize_intent(self, intent: Dict[str, Any], question: Optional[str] = None) -> Dict[str, Any]:
        """
        Normalize and validate intent structure
        
        Args:
            intent: Raw intent from LLM
            question: Original user question (for compare-with-others detection)
        
        Returns:
            Normalized intent dict
        """
        # Ensure required fields exist
        raw_metric = intent.get("metric") or "gsales"
        # Normalize metric: only allow known metrics; default to gsales when unknown/empty
        allowed_metrics = {"gsales", "fgp", "cases", "price_downs", "perm_disc", "transfer_cost", "group_cost", "lta"}
        metric = raw_metric if raw_metric in allowed_metrics else "gsales"

        normalized = {
            "metric": metric,
            "dimensions": intent.get("dimensions", []),
            "filters": intent.get("filters", {}),
            "time_range": intent.get("time_range", {"type": "custom", "value": None}),
            "aggregation": intent.get("aggregation", "sum"),
            "limit": intent.get("limit", 1000)
        }
        
        # Normalize filters (ensure all filter keys exist)
        filter_keys = ["business", "channel", "brand", "category", "sub_category", "customer", "sku", "year", "quarter", "month_name"]
        for key in filter_keys:
            if key not in normalized["filters"]:
                normalized["filters"][key] = []
        
        # Normalize time_range
        time_range = normalized["time_range"]
        if not isinstance(time_range, dict):
            time_range = {"type": "custom", "value": None}
        
        if "type" not in time_range:
            time_range["type"] = "custom"
        if "value" not in time_range:
            time_range["value"] = None
        
        normalized["time_range"] = time_range
        # Normalize limit
        try:
            normalized["limit"] = int(normalized.get("limit", 1000))
        except Exception:
            normalized["limit"] = 1000
        if normalized["limit"] <= 0:
            normalized["limit"] = 1000
        # Guardrail: keep bounds safe but practical for UI
        normalized["limit"] = min(normalized["limit"], 5000)

        # Normalize month_name filter to abbreviated (Jan, Feb, ...) for DB
        month_vals = normalized["filters"].get("month_name") or []
        if month_vals:
            normalized["filters"]["month_name"] = self._normalize_month_name_filter(month_vals)
        
        # If LLM forgot the month but the question clearly mentions one, infer it.
        # Example: "in October 2025", "October 2025", "in Jan", "month 1", "first month".
        if not month_vals and question:
            inferred_month = self._parse_month_from_question(question)
            if inferred_month:
                normalized["filters"]["month_name"] = [inferred_month]
                month_vals = normalized["filters"]["month_name"]
        
        # If LLM forgot the year but the question mentions a specific year, infer it.
        years = normalized["filters"].get("year", [])
        if (not years) and question:
            q_lower_years = (question or "").lower()
            found_years = re.findall(r"\b(20\d{2})\b", q_lower_years)
            if found_years:
                years = [int(y) for y in sorted(set(found_years))]
                normalized["filters"]["year"] = years
        
        # If multiple years are explicitly requested, force year-wise comparison grouping.
        if isinstance(years, list) and len(years) > 1 and "year" not in normalized["dimensions"]:
            normalized["dimensions"].append("year")
        # When user asks for a specific year (e.g. "top 5 business in 2025"), use lifetime so query uses only year/quarter/month filters
        if (
            isinstance(years, list)
            and len(years) >= 1
            and normalized["time_range"].get("type") == "custom"
            and not normalized["time_range"].get("value")
        ):
            normalized["time_range"] = {"type": "lifetime", "value": None}

        # "Before and after January 2024": ensure we have a time range and month dimension so data is returned
        question_lower_norm = (question or "").lower()
        if "before and after" in question_lower_norm and re.search(
            r"(?:january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)\s*(20\d{2})?",
            question_lower_norm,
        ):
            if not normalized["time_range"].get("value") and normalized["time_range"].get("type") == "custom":
                normalized["time_range"] = {"type": "last_n_months", "value": 24}
            if "month_name" not in normalized["dimensions"]:
                normalized["dimensions"].append("month_name")
        
        # If user explicitly talks about a category question and dimensions are empty, default to category dimension.
        if not normalized["dimensions"] and ("category" in (question or "").lower() or "categories" in (question or "").lower()):
            normalized["dimensions"] = ["category"]
        
        # CRITICAL: "Compare X with other brands" → clear brand filter so we get all brands.
        # "Compare brand A, B, C and D" (specific brands listed) → keep filter = [A,B,C,D]; do NOT clear.
        question_lower = (question or "").lower()
        compare_with_others_phrases = [
            "with other brands", "vs other brands", "versus other brands", "to other brands",
            "compared to other brands", "compared with other brands", "against other brands",
            "with other businesses", "vs other businesses", "to other businesses",
            "with other categories", "vs other categories", "to other categories",
        ]
        is_compare_with_others = any(p in question_lower for p in compare_with_others_phrases)
        # "Compare brand KOKA, Green Aware, Kinetica and Powerforce" = specific brands; "compare X with other brands" = clear filter
        is_compare_two_or_more_brands = (
            "compare" in question_lower and ("brand" in question_lower or "brands" in question_lower)
            and (" and " in question_lower or " & " in question_lower or ("," in question_lower and "brand" in question_lower))
        )
        is_compare_two_or_more_businesses = (
            "compare" in question_lower and ("business" in question_lower or "businesses" in question_lower)
            and (" and " in question_lower or " & " in question_lower or "," in question_lower)
        )
        is_compare_two_or_more_categories = (
            "compare" in question_lower and ("category" in question_lower or "categories" in question_lower)
            and (" and " in question_lower or " & " in question_lower or "," in question_lower)
        )
        if is_compare_with_others or is_compare_two_or_more_brands or is_compare_two_or_more_businesses or is_compare_two_or_more_categories:
            if "brand" in question_lower or "brands" in question_lower or is_compare_two_or_more_brands:
                parsed_brands = self._parse_multiple_brands_from_question(question)
                if is_compare_with_others:
                    normalized["filters"]["brand"] = []
                elif len(parsed_brands) >= 2:
                    # Use parsed brands (cleaned: "koka brand" -> "Koka") so DB filter matches
                    normalized["filters"]["brand"] = parsed_brands
                    normalized["limit"] = min(normalized.get("limit", 1000), len(parsed_brands) + 5)
                else:
                    # "Compare A and B" but parser got 0–1 names: clear so query returns all brands (LLM compares in context)
                    normalized["filters"]["brand"] = []
                if "brand" not in normalized["dimensions"]:
                    normalized["dimensions"].append("brand")
                if normalized.get("limit", 1000) == 1000 and not normalized["filters"]["brand"]:
                    normalized["limit"] = 20
            if "business" in question_lower or "businesses" in question_lower or is_compare_two_or_more_businesses:
                parsed_businesses = self._parse_multiple_entities_from_question(
                    question, r"business(es)?", "business", None
                )
                if is_compare_with_others:
                    normalized["filters"]["business"] = []
                elif len(parsed_businesses) >= 2:
                    normalized["filters"]["business"] = parsed_businesses
                    normalized["limit"] = min(normalized.get("limit", 1000), len(parsed_businesses) + 5)
                else:
                    normalized["filters"]["business"] = []
                if "business" not in normalized["dimensions"]:
                    normalized["dimensions"].append("business")
                if normalized.get("limit", 1000) == 1000 and not normalized["filters"]["business"]:
                    normalized["limit"] = 20
            if "category" in question_lower or "categories" in question_lower or is_compare_two_or_more_categories:
                parsed_categories = self._parse_multiple_entities_from_question(
                    question, r"categor(y|ies)", "category", None
                )
                if is_compare_with_others:
                    normalized["filters"]["category"] = []
                elif len(parsed_categories) >= 2:
                    normalized["filters"]["category"] = parsed_categories
                    normalized["limit"] = min(normalized.get("limit", 1000), len(parsed_categories) + 5)
                else:
                    normalized["filters"]["category"] = []
                if "category" not in normalized["dimensions"]:
                    normalized["dimensions"].append("category")
                if normalized.get("limit", 1000) == 1000 and not normalized["filters"]["category"]:
                    normalized["limit"] = 20
        
        # "Tell me all three brands Q2 2023 revenue of X, Y and Z" (no "compare") — still extract brand list
        if "brand" in question_lower or "brands" in question_lower:
            current_brands = normalized.get("filters", {}).get("brand") or []
            if len(current_brands) < 2:
                revenue_brands = self._parse_brands_from_revenue_phrase(question)
                if len(revenue_brands) >= 2:
                    normalized["filters"]["brand"] = revenue_brands
                    if "brand" not in normalized["dimensions"]:
                        normalized["dimensions"].append("brand")
                    normalized["limit"] = min(normalized.get("limit", 1000), len(revenue_brands) + 5)

        # "Compare X performance in Convenience vs Grocery" (or "X in A vs B") → channel dimension + brand + channels
        channel_comparison = self._parse_channel_comparison(question)
        if channel_comparison:
            brand_name, channel_list = channel_comparison
            if brand_name and len(channel_list) >= 2:
                normalized["dimensions"] = ["channel"] if "channel" not in normalized["dimensions"] else normalized["dimensions"]
                normalized["filters"]["brand"] = [brand_name]
                normalized["filters"]["channel"] = channel_list
                normalized["limit"] = min(normalized.get("limit", 1000), len(channel_list) + 5)

        # NATURAL "X and Y business" / "X, Y and Z category" rescue:
        # The LLM frequently mis-classifies these as brands when the question doesn't
        # use the word "compare". We detect them deterministically here and override.
        # Only runs when: the suffix word ("business", "category", etc.) appears in the
        # question, the matching filter is still empty, AND the question is not a
        # "compare ... with other ..." (those are handled above).
        question_lower_full = (question or "").lower()
        is_compare_question = "compare" in question_lower_full
        natural_targets = [
            ("business", r"business(?:es)?", "business", "brand"),
            ("category", r"categor(?:y|ies)", "category", None),
            ("channel", r"channels?", "channel", None),
            ("customer", r"customers?", "customer", None),
        ]
        for word, suffix_regex, filter_key, conflicting_dim in natural_targets:
            if word not in question_lower_full:
                continue
            if is_compare_question:
                continue  # handled by the compare path
            existing = normalized.get("filters", {}).get(filter_key) or []
            if existing:
                continue
            parsed = self._parse_multiple_entities_in_natural_phrase(
                question, suffix_regex
            )
            if not parsed:
                continue
            normalized["filters"][filter_key] = parsed
            if filter_key not in normalized["dimensions"]:
                normalized["dimensions"].append(filter_key)
            # If the LLM mistakenly added a conflicting dimension that the user
            # never mentioned, remove it. Example: user says "X and Y business"
            # but LLM returns dimensions=["brand"] — drop "brand".
            if (
                conflicting_dim
                and conflicting_dim in normalized["dimensions"]
                and conflicting_dim not in question_lower_full
            ):
                normalized["dimensions"].remove(conflicting_dim)
                # Also clear the conflicting filter if it's empty/stale
                if not normalized.get("filters", {}).get(conflicting_dim):
                    normalized["filters"][conflicting_dim] = []
            # Tighten limit when we have a small named list
            if len(parsed) >= 2:
                normalized["limit"] = min(
                    normalized.get("limit", 1000), max(20, len(parsed) + 5)
                )

        return normalized

    # Stop words to drop when extracting entity names from "Compare Q2 2023 revenue of A, B and C brands"
    _ENTITY_STOP_WORDS = frozenset({
        "q1", "q2", "q3", "q4", "revenue", "profit", "cases", "margin", "of", "for",
        "comparison", "compare", "brand", "brands", "business", "businesses", "category", "categories",
        "channel", "channels", "customer", "customers", "sales", "volume", "gross", "and", "the",
    })

    # Known channel names for "X in Convenience vs Grocery" parsing (case-insensitive match, then title-cased)
    _KNOWN_CHANNELS = (
        "Convenience", "Grocery", "Wholesale", "International", "Online",
        "Sports & Others", "Sports and Others",
    )

    # Month names and ordinals → abbreviated (ClickHouse/DB use Jan, Feb, ...)
    _MONTH_TO_ABBREV = {
        "january": "Jan", "jan": "Jan",
        "february": "Feb", "feb": "Feb",
        "march": "Mar", "mar": "Mar",
        "april": "Apr", "apr": "Apr",
        "may": "May",
        "june": "Jun", "jun": "Jun",
        "july": "Jul", "jul": "Jul",
        "august": "Aug", "aug": "Aug",
        "september": "Sep", "sep": "Sep", "sept": "Sep",
        "october": "Oct", "oct": "Oct",
        "november": "Nov", "nov": "Nov",
        "december": "Dec", "dec": "Dec",
    }
    _ORDINAL_MONTH = {
        "first": 1, "1st": 1, "1": 1, "one": 1,
        "second": 2, "2nd": 2, "two": 2,
        "third": 3, "3rd": 3, "three": 3,
        "fourth": 4, "4th": 4, "four": 4,
        "fifth": 5, "5th": 5, "five": 5,
        "sixth": 6, "6th": 6, "six": 6,
        "seventh": 7, "7th": 7, "seven": 7,
        "eighth": 8, "8th": 8, "eight": 8,
        "ninth": 9, "9th": 9, "nine": 9,
        "tenth": 10, "10th": 10, "ten": 10,
        "eleventh": 11, "11th": 11, "eleven": 11,
        "twelfth": 12, "12th": 12, "twelve": 12,
    }
    _MONTH_NUM_TO_ABBREV = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

    def _parse_month_from_question(self, question: Optional[str]) -> Optional[str]:
        """
        Parse a specific month from the question: "January", "Jan", "in March", "first month", "month 1".
        Returns abbreviated month (Jan, Feb, ...) or None.
        """
        if not question or not question.strip():
            return None
        q = (question or "").strip().lower()
        # Full or abbreviated month name (e.g. "in January", "January 2024", "for Jan")
        for name, abbrev in self._MONTH_TO_ABBREV.items():
            if re.search(rf"\b{re.escape(name)}\b", q):
                return abbrev
        # "month 1", "month 7", "month 12"
        month_num_m = re.search(r"\bmonth\s+(1[0-2]|[1-9])\b", q)
        if month_num_m:
            num = int(month_num_m.group(1))
            if 1 <= num <= 12:
                return self._MONTH_NUM_TO_ABBREV[num - 1]
        # "first month", "1st month", "second month", "month one"
        ord_match = re.search(
            r"(?:first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|sixth|6th|seventh|7th|eighth|8th|ninth|9th|tenth|10th|eleventh|11th|twelfth|12th|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+month",
            q,
        )
        if ord_match:
            rest = ord_match.group(0).replace("month", "").strip()
            num = self._ORDINAL_MONTH.get(rest)
            if num and 1 <= num <= 12:
                return self._MONTH_NUM_TO_ABBREV[num - 1]
        return None

    def _parse_quarter_from_question(self, question: Optional[str]) -> Optional[int]:
        """Parse quarter from 'Q1', 'Q2', 'quarter 1', 'quarter1', 'quarter two'. Returns 1-4 or None."""
        if not question or not question.strip():
            return None
        q = (question or "").strip().lower()
        m = re.search(r"\bq([1-4])\b", q)
        if m:
            return int(m.group(1))
        m = re.search(r"quarter\s*(1|2|3|4|one|two|three|four)\b", q)
        if m:
            g = m.group(1).lower()
            if g in ("1", "one"):
                return 1
            if g in ("2", "two"):
                return 2
            if g in ("3", "three"):
                return 3
            if g in ("4", "four"):
                return 4
        return None

    def _normalize_month_name_filter(self, month_values: list) -> list:
        """Normalize month_name filter values to abbreviated form (Jan, Feb, ...)."""
        if not month_values:
            return []
        out = []
        for v in (month_values or []):
            s = str(v).strip()
            if not s:
                continue
            lower = s.lower()
            if lower in self._MONTH_TO_ABBREV:
                out.append(self._MONTH_TO_ABBREV[lower])
            elif s in self._MONTH_NUM_TO_ABBREV:
                out.append(s)
            elif lower in ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"):
                out.append(self._MONTH_TO_ABBREV[lower])
            else:
                out.append(s)
        return list(dict.fromkeys(out))  # dedupe, preserve order

    def _parse_channel_comparison(self, question: Optional[str]) -> Optional[tuple]:
        """
        Parse "Compare Kinetica performance in Convenience vs Grocery" or "X in A vs B".
        Returns (brand_name, [channel1, channel2]) or None.
        """
        if not question or not question.strip():
            return None
        q = question.strip()
        q_lower = q.lower()
        if " vs " not in q_lower and " versus " not in q_lower:
            return None
        # Find which known channels appear in the question (in order)
        found_channels = []
        for ch in self._KNOWN_CHANNELS:
            if ch.lower() in q_lower:
                found_channels.append(ch)
        if len(found_channels) < 2:
            return None
        # Take first two found (user usually says "Convenience vs Grocery" in order)
        channels = found_channels[:2]
        # Extract brand: "Compare Kinetica performance in ..." or "Kinetica in Convenience vs ..."
        brand = None
        m = re.search(
            r"\bcompare\s+([a-z0-9&\-\s]+?)\s+(?:performance\s+)?in\s+",
            q,
            re.IGNORECASE,
        )
        if m:
            brand = m.group(1).strip()
        if not brand:
            # "Kinetica in Convenience vs Grocery" — word(s) before " in "
            m2 = re.search(r"\b([a-z0-9&\-\s]+?)\s+in\s+(?:convenience|grocery|wholesale|international|online|sports)",
                           q_lower)
            if m2:
                brand = q[m2.start(1):m2.end(1)].strip()
        if brand:
            # Drop stop words from brand
            tokens = [t for t in brand.split() if t.lower() not in self._ENTITY_STOP_WORDS and not re.match(r"^20\d{2}$", t)]
            brand = " ".join(tokens).strip().title() if tokens else brand.strip().title()
        if not brand:
            return None
        return (brand, channels)

    def _parse_multiple_entities_from_question(
        self,
        question: Optional[str],
        word_pattern: str,
        strip_suffix: str,
        normalizations: Optional[Dict[str, str]] = None,
    ) -> list:
        """Extract entity names for 'compare X, Y and Z {word}' or 'compare Q2 2023 revenue of A, B and C {word}'. word_pattern e.g. r'brands?' or r'business(es)?'."""
        if not question or not question.strip():
            return []
        normalizations = normalizations or {}
        q = question.strip()
        segment = None
        # Pattern 1: "compare brand X, Y and Z" (word then list)
        m1 = re.search(
            rf"\bcompare\s+{word_pattern}\s+([^.]*?)(?:\s+and\s+tell|\s+tell\s+me|\s+how\s+all|\s+performance|\s+performing|$)",
            q,
            re.IGNORECASE | re.DOTALL,
        )
        if m1:
            segment = m1.group(1).strip()
        if not segment:
            # Pattern 2: "compare ... X, Y and Z brands" (list then word at end)
            m2 = re.search(
                rf"\bcompare\s+(.+?)\s+{word_pattern}\s*(?:\s+and\s+tell|\s+tell\s+me|\s+how\s+all|\s+performance|\s+performing|$)",
                q,
                re.IGNORECASE | re.DOTALL,
            )
            if m2:
                segment = m2.group(1).strip()
        if not segment:
            return []
        parts = re.split(r"\s*,\s*|\s+and\s+|\s+&\s+", segment, flags=re.IGNORECASE)
        def clean(s: str) -> str:
            s = s.strip()
            s = re.sub(rf"\s+{re.escape(strip_suffix)}s?\s*$", "", s, flags=re.IGNORECASE).strip()
            return s.title() if s else ""
        raw = [clean(p) for p in parts if p and clean(p)]
        entities = []
        for b in raw:
            tokens = b.split()
            kept = []
            for t in tokens:
                t_lower = t.lower()
                if t_lower in self._ENTITY_STOP_WORDS or re.match(r"^20\d{2}$", t) or re.match(r"^q[1-4]$", t_lower):
                    continue
                kept.append(t)
            name = " ".join(kept).strip()
            if name:
                entities.append(name)
        entities = [normalizations.get(e, e) for e in entities]
        return entities

    def _parse_multiple_brands_from_question(self, question: Optional[str]) -> list:
        """Extract brand names; uses generic entity parser with brand-specific normalizations."""
        normalizations = {
            "Poweforce": "Powerforce",
            "Greenaware": "Green Aware",
            "Koka Brand": "Koka",
            "Calli Calli": "Cali Cali",
            "Calli": "Cali Cali",  # live suggested question may say "Calli" only
        }
        return self._parse_multiple_entities_from_question(question, r"brands?", "brand", normalizations)

    # Common verbs and filler words that should NEVER be treated as an entity name
    # when parsing "<entities> business/channel/category..." phrases.
    _ENTITY_FILLER_WORDS = frozenset({
        "tell", "show", "give", "list", "me", "us", "please", "kindly",
        "how", "what", "which", "where", "when",
        "is", "are", "was", "were", "be", "been", "being",
        "do", "does", "did",
        "perform", "performs", "performed", "performing", "performance",
        "run", "runs", "running", "doing", "say", "saying", "tells", "showing",
        "the", "a", "an", "this", "that", "these", "those",
        "in", "on", "for", "of", "at", "by", "from", "to", "with", "without",
    })

    def _parse_multiple_entities_in_natural_phrase(
        self,
        question: Optional[str],
        suffix_word_regex: str,
        normalizations: Optional[Dict[str, str]] = None,
    ) -> list:
        """
        Parse entity names from a NATURAL (non-compare) phrase like:
          - "how brillo and cali cali business performs in 2024"
          - "show food, snacks and household business"
          - "for X channel and Y channel"

        We capture the segment ending just before the suffix word (e.g. "business"),
        then split on commas / "and" / "&". Stop words and 4-digit years are dropped.

        Returns a deduped list of cleaned entity names (Title Case), or [] when nothing
        confident was found. NEVER more than 10 names (cap for safety).
        """
        if not question or not question.strip():
            return []
        normalizations = normalizations or {}
        q = question.strip()

        patterns = [
            # "how/for/of/in <segment> business[es]"  — caller usually says intent verb first
            rf"(?:\bhow\b|\bof\b|\bfor\b|\bin\b)\s+(.+?)\s+{suffix_word_regex}\b",
            # "show/tell me <segment> business[es]"
            rf"(?:\bshow\b|\btell\b)(?:\s+me)?\s+(.+?)\s+{suffix_word_regex}\b",
            # "<segment> business[es] <verb>"  — e.g. "X and Y business performs"
            rf"\b([A-Za-z][A-Za-z0-9&\-\s,]+?)\s+{suffix_word_regex}\s+(?:perform|performs|performed|performing|performance|do|does|did|run|runs|is|are|was|were|in|for)\b",
        ]
        segment: Optional[str] = None
        for pat in patterns:
            m = re.search(pat, q, re.IGNORECASE | re.DOTALL)
            if m:
                segment = m.group(1).strip()
                break
        if not segment:
            return []

        parts = re.split(r"\s*,\s*|\s+and\s+|\s+&\s+", segment, flags=re.IGNORECASE)
        entities: list = []
        seen: set = set()
        for p in parts:
            p = p.strip()
            if not p:
                continue
            tokens = p.split()
            kept = [
                t for t in tokens
                if t.lower() not in self._ENTITY_STOP_WORDS
                and t.lower() not in self._ENTITY_FILLER_WORDS
                and not re.match(r"^20\d{2}$", t)
                and not re.match(r"^q[1-4]$", t.lower())
            ]
            name = " ".join(kept).strip().title()
            if not name:
                continue
            name = normalizations.get(name, name)
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            entities.append(name)
            if len(entities) >= 10:
                break
        return entities

    def _parse_brands_from_revenue_phrase(self, question: Optional[str]) -> list:
        """Extract brand names from 'revenue of X, Y and Z' or 'revenue for X and Y and Z' (no 'compare')."""
        if not question or not question.strip():
            return []
        q = question.strip()
        # "revenue of Calli Calli and Bonne Maman and Green Aware" or "revenue for brands X, Y and Z"
        m = re.search(
            r"revenue\s+(?:of|for)\s+(?:brands?\s+)?([^.]+?)(?:\s+and\s+tell|\s*$|\.)",
            q,
            re.IGNORECASE | re.DOTALL,
        )
        if not m:
            return []
        segment = m.group(1).strip()
        parts = re.split(r"\s*,\s*|\s+and\s+|\s+&\s+", segment, flags=re.IGNORECASE)
        normalizations = {
            "Poweforce": "Powerforce",
            "Greenaware": "Green Aware",
            "Koka Brand": "Koka",
            "Calli Calli": "Cali Cali",
            "Calli": "Cali Cali",
        }
        brands = []
        for b in parts:
            b = b.strip()
            b = re.sub(r"\s+brands?\s*$", "", b, flags=re.IGNORECASE).strip()
            if not b:
                continue
            tokens = b.split()
            kept = [
                t for t in tokens
                if t.lower() not in self._ENTITY_STOP_WORDS
                and not re.match(r"^20\d{2}$", t)
                and not re.match(r"^q[1-4]$", t.lower())
            ]
            name = " ".join(kept).strip().title()
            if name:
                brands.append(normalizations.get(name, name))
        return brands

    def _get_default_intent(self, question: str) -> Dict[str, Any]:
        """
        Get default intent when extraction fails
        
        Args:
            question: User question
        
        Returns:
            Default intent dict
        """
        logger.warning("Using default intent due to extraction failure")
        question_lower = (question or "").lower()
        parsed = {
            "metric": "gsales",
            "dimensions": [],
            "filters": {
                "business": [],
                "channel": [],
                "brand": [],
                "category": [],
                "sub_category": [],
                "customer": [],
                "sku": [],
                "year": [],
                "quarter": [],
                "month_name": []
            },
            "time_range": {
                "type": "custom",
                "value": None
            },
            "aggregation": "sum"
        }
        # Deterministic fallback parser for common production queries.
        metric_map = {
            "revenue": "gsales",
            "gross sales": "gsales",
            "sales": "gsales",
            "profit": "fgp",
            "gross profit": "fgp",
            "cases": "cases",
            "volume": "cases",
        }
        for k, v in metric_map.items():
            if k in question_lower:
                parsed["metric"] = v
                break

        # common entity extraction: "business Food", "channel Convenience", etc.
        entity_patterns = {
            "business": r"business\s+([a-z0-9&\-\s]+?)(?:,| and | for | in |$)",
            "channel": r"channel\s+([a-z0-9&\-\s]+?)(?:,| and | for | in |$)",
            "customer": r"customer\s+([a-z0-9&\-\s]+?)(?:,| and | for | in |$)",
            "brand": r"brand\s+([a-z0-9&\-\s]+?)(?:,| and | for | in |$)",
            "category": r"category\s+([a-z0-9&\-\s]+?)(?:,| and | for | in |$)",
            "sub_category": r"sub[ -]?category\s+([a-z0-9&\-\s]+?)(?:,| and | for | in |$)",
        }
        for key, pattern in entity_patterns.items():
            m = re.search(pattern, question_lower, flags=re.IGNORECASE)
            if m:
                parsed["filters"][key] = [m.group(1).strip().title()]

        # "Compare X performance in Convenience vs Grocery" — default intent
        channel_comparison = self._parse_channel_comparison(question)
        if channel_comparison:
            brand_name, channel_list = channel_comparison
            if brand_name and len(channel_list) >= 2:
                parsed["dimensions"] = ["channel"]
                parsed["filters"]["brand"] = [brand_name]
                parsed["filters"]["channel"] = channel_list
                parsed["limit"] = min(parsed.get("limit", 1000), len(channel_list) + 5)

        # Time parsing
        months_match = re.search(r"last\s+(\d+)\s+months?", question_lower)
        days_match = re.search(r"last\s+(\d+)\s+days?", question_lower)
        before_after = re.search(
            r"before\s+and\s+after\s+(?:January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|September|Sep|Oct|November|Nov|December|Dec)\s*(20\d{2})?",
            question_lower,
        )
        if before_after:
            # "before and after January 2024" → get data around that period (e.g. last 24 months) with month dimension
            parsed["time_range"] = {"type": "last_n_months", "value": 24}
            if "month_name" not in parsed["dimensions"]:
                parsed["dimensions"].append("month_name")
        if months_match and not before_after:
            parsed["time_range"] = {"type": "last_n_months", "value": int(months_match.group(1))}
        elif days_match:
            parsed["time_range"] = {"type": "last_n_days", "value": int(days_match.group(1))}
        elif any(x in question_lower for x in ["lifetime", "all time", "all history"]):
            parsed["time_range"] = {"type": "lifetime", "value": None}

        # Quarter: Q1, Q2, "quarter 1", "quarter1", "quarter two"
        quarter_num = self._parse_quarter_from_question(question)
        if quarter_num is not None:
            parsed["filters"]["quarter"] = [quarter_num]
            if not parsed["time_range"].get("value") and parsed["time_range"].get("type") == "custom":
                parsed["time_range"] = {"type": "lifetime", "value": None}

        # Specific month: January, Jan, "in March", "first month", "month 1"
        month_abbrev = self._parse_month_from_question(question)
        if month_abbrev:
            parsed["filters"]["month_name"] = [month_abbrev]
            if not parsed["time_range"].get("value") and parsed["time_range"].get("type") == "custom":
                parsed["time_range"] = {"type": "lifetime", "value": None}

        years = re.findall(r"\b(20\d{2})\b", question_lower)
        if years:
            parsed["filters"]["year"] = [int(y) for y in sorted(set(years))]
            if len(parsed["filters"]["year"]) > 1 and "year" not in parsed["dimensions"]:
                parsed["dimensions"].append("year")
            # Multi-year or Q1/Q2/Q3/Q4 comparison: use lifetime so only year/quarter filters apply
            if len(parsed["filters"]["year"]) >= 1 and (parsed["filters"].get("quarter") or parsed["filters"].get("month_name")):
                parsed["time_range"] = {"type": "lifetime", "value": None}
        top_match = re.search(r"\btop\s+(\d+)\b", question_lower)
        parsed["limit"] = int(top_match.group(1)) if top_match else 1000
        # "top 5 business in Q1", "top 10 brands" → set dimension when not already set
        if not parsed["dimensions"] and "top" in question_lower:
            if re.search(r"top\s+\d+\s+(business|businesses)\b", question_lower):
                parsed["dimensions"] = ["business"]
            elif re.search(r"top\s+\d+\s+(brand|brands)\b", question_lower):
                parsed["dimensions"] = ["brand"]
            elif re.search(r"top\s+\d+\s+(categor|categories)\b", question_lower):
                parsed["dimensions"] = ["category"]
            elif re.search(r"top\s+\d+\s+(channel|channels)\b", question_lower):
                parsed["dimensions"] = ["channel"]
            elif re.search(r"top\s+\d+\s+(customer|customers)\b", question_lower):
                parsed["dimensions"] = ["customer"]
            elif re.search(r"top\s+\d+\s+(sub[- ]?categor|sub[- ]?categories)\b", question_lower):
                parsed["dimensions"] = ["sub_category"]
            elif re.search(r"top\s+\d+\s+(sku|skus)\b", question_lower):
                parsed["dimensions"] = ["sku"]

        # Run normalization (e.g. "compare X with other brands" → clear brand filter, dimensions=[brand], limit=20)
        parsed = self._normalize_intent(parsed, question)
        logger.info("AI_INTENT | default_fallback_intent=%s", json.dumps(parsed, ensure_ascii=True))
        return parsed
