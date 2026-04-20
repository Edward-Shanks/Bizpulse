"""
AI Response Service
Generates human-friendly explanations from ClickHouse query results using LLM
"""
import json
import logging
import re
from typing import Dict, Any, List, Optional

from app.utils.ai_service import query_llm

logger = logging.getLogger(__name__)

# Dimension key -> live-style plural label for "Top N X by Revenue"
DIMENSION_HEADER_LABELS = {
    "business": "Businesses",
    "brand": "Brands",
    "category": "Categories",
    "channel": "Channels",
    "customer": "Customers",
    "sub_category": "Sub-categories",
    "sku": "SKUs",
}


class AIResponseService:
    """
    AI Response Generation Service
    
    Converts raw ClickHouse query results into human-friendly business explanations.
    """
    
    EXPLANATION_PROMPT = """You are Vector AI, a strategic business intelligence analyst for ThriveBrands. You provide business insights and recommendations to non-technical executives. You MUST answer only from the business data provided below.

{data_intro}

Query Results (USE ONLY THIS DATA - DO NOT USE EXTERNAL KNOWLEDGE):
{data}

User Question: {question}

CRITICAL INSTRUCTIONS (same as live BI chatbot):
1. START your response by listing the EXACT entities from the data above (e.g. "Koka: Revenue €67.56M, Profit €21.52M (31.9% margin), Cases 3,138,667"). Use the EXACT names and numbers from the data. Do NOT use generic descriptions like "top brands" without names.
2. Then provide "Key Insights:" with 3-5 bullet points (who leads on revenue, who has best margin, trends). Then "Performance Analysis" or "What These Numbers Mean" when the user asked about specific entities. Then "Recommendations:" with 3-5 actionable bullets (why and how). Optionally "Next Steps" or "Potential Risks & Opportunities."
3. You MUST use ONLY the data provided above. Do NOT say "data not available" or "no data" when the data section contains rows—treat the numbers as authoritative. If the user asked for specific entities (e.g. Koka, Green Aware, Kinetica), focus your insights on those names using the full list for context.
4. Use EXACT numbers from the data. Format currency as €X.XXM or €XXXK. Include margin % in parentheses after profit with ONE decimal place (e.g. "Profit €21.52M (31.9% margin)", "41.0% margin").
5. For partial data (e.g. user asked for 2022, 2023, 2024 but only 2023–2024 exist): state which period is missing and present the available data. Never say "no data found" when any rows are provided.
6. Speak only in business language. Do not mention database, query, API, or technical terms.

Generate a comprehensive business explanation:"""

    def __init__(self):
        """Initialize response service"""
        pass

    @staticmethod
    def _top_n_header(question: str, intent: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Build live-style header for top-N queries: "Top N Businesses by Revenue:" or "Top 5 Categories by Revenue in 2025:".
        Returns None if this is not a top-N single-dimension query.
        """
        intent = intent or {}
        dimensions = intent.get("dimensions") or []
        limit = intent.get("limit", 1000)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 1000
        years = intent.get("filters") or {}
        years = years.get("year") or []
        if not isinstance(years, list):
            years = [years] if years else []
        year_str = ""
        if len(years) == 1:
            year_str = f" in {years[0]}"
        elif len(years) > 1:
            year_str = f" ({', '.join(str(y) for y in sorted(years))})"
        # Single dimension + limit looks like "top N"
        if len(dimensions) == 1 and limit <= 100:
            dim = dimensions[0]
            label = DIMENSION_HEADER_LABELS.get(dim, dim.replace("_", " ").title() + "s")
            return f"Top {limit} {label} by Revenue{year_str}:"
        # Parse question as fallback: "top 6 business", "top 5 categories in 2025"
        q = (question or "").strip().lower()
        top_m = re.search(r"top\s+(\d+)\s+(businesses?|brands?|categories?|channels?|customers?|skus?|sub[- ]?categories?)", q)
        if top_m:
            n = int(top_m.group(1))
            w = top_m.group(2).lower()
            if "business" in w:
                label = "Businesses"
            elif "brand" in w:
                label = "Brands"
            elif "categor" in w and "sub" not in w:
                label = "Categories"
            elif "channel" in w:
                label = "Channels"
            elif "customer" in w:
                label = "Customers"
            elif "sub" in w or "sku" in w:
                label = "Sub-categories" if "sub" in w else "SKUs"
            else:
                label = w.title() + ("s" if not w.endswith("s") else "")
            year_m = re.search(r"\b(20\d{2})\b", question or "")
            year_str = f" in {year_m.group(1)}" if year_m else ""
            return f"Top {n} {label} by Revenue{year_str}:"
        return None

    async def generate_response(
        self,
        question: str,
        data: List[Dict[str, Any]],
        intent: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate human-friendly explanation from query results
        
        Args:
            question: Original user question
            data: ClickHouse query results (list of dicts)
        
        Returns:
            Human-friendly explanation string
        
        Example:
            >>> question = "Show revenue for Food business last 6 months"
            >>> data = [{"business": "Food", "gsales": 45800000}]
            >>> explanation = await service.generate_response(question, data)
            >>> # Returns: "Your Food business generated ₹4.58 crore revenue in the last 6 months..."
        """
        try:
            # Format data for prompt
            if not data:
                data_str = "No data found for this query."
                data_intro = ""
                # When user asked for multiple years, hint so LLM can suggest trying available years
                requested_years = (intent or {}).get("filters", {}).get("year", [])
                if requested_years:
                    data_str += f"\n\nContext: The user asked for year(s) {requested_years}. If data is missing for some years (e.g. 2022), suggest they can try asking for the years that may have data (e.g. 2023 and 2024) and present any available data if the query is retried with those years."
            else:
                # Convert to readable format
                data_str = json.dumps(data, indent=2, default=str)
                # Live-style intro: tell LLM this data is the source of truth (matches insights_service pivot_table_note)
                data_intro = (
                    "CRITICAL: The data below is the exact result for the user's question. "
                    "You MUST start your response by listing these entities with their Revenue, Profit (margin %), and Cases. "
                    "Use the EXACT names and numbers. Then provide Key Insights, Performance Analysis, and Recommendations.\n\n"
                )
                # For "top N" questions: require live-style header and one-decimal margin (e.g. 31.9%, 41.0%)
                top_header = self._top_n_header(question, intent)
                if top_header:
                    data_intro += (
                        f"TOP-N FORMAT: This is a 'top N' query. You MUST start your response with exactly this line: \"{top_header}\" "
                        "(then a blank line, then list each entity). Use margin with ONE decimal place (e.g. 31.9% margin, 41.0% margin).\n\n"
                    )
            
            prompt = self.EXPLANATION_PROMPT.format(
                question=question,
                data=data_str,
                data_intro=data_intro
            )
            logger.info("AI_RESPONSE | question=%s", question)
            logger.info("AI_RESPONSE | data_preview=%s", data_str[:1200])
            
            # Temperature 0.5 = focused, consistent explanations. max_tokens 1500 = full answers without truncation.
            response = await query_llm(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1500,
                custom_system_message=(
                    "You are Vector AI, a business intelligence analyst for ThriveBrands. "
                    "You MUST use ONLY the business data provided in the user message. Do NOT use external knowledge, news, or assumptions. "
                    "CRITICAL: When data rows are provided, you MUST NOT say 'data not available' or 'no data'—use the provided numbers as authoritative. "
                    "Structure every response: (1) List entities with exact Revenue, Profit (margin %), Cases; (2) Key Insights; (3) Performance Analysis / What These Numbers Mean; (4) Recommendations with why and how; (5) Next Steps or Risks & Opportunities. "
                    "Use EXACT numbers from the data. Format as €X.XXM or €XXXK. Always show margin with one decimal (e.g. 31.9%, 41.0%). Speak only in business language; never mention database, query, or API."
                )
            )
            
            logger.info("AI_RESPONSE | generated_chars=%s", len(response))
            out = response.strip()
            # Normalize integer margin to one decimal (e.g. "41%" -> "41.0%"); leave "31.9%" unchanged
            # group(2) is "% margin" so do not append " margin" again
            def _one_decimal(m):
                return m.group(1) + ".0" + m.group(2)
            out = re.sub(r"(\d+)(?!\.\d)(% margin)", _one_decimal, out)
            out = re.sub(r"\((\d+)(?!\.\d)(% margin)\)", r"(\1.0\2)", out)
            # Fix any double-decimal margin (e.g. 33.0.0% -> 33.0%)
            out = re.sub(r"(\d+)\.0\.0(% margin)", r"\1.0\2", out)
            out = re.sub(r"\((\d+)\.0\.0(% margin)\)", r"(\1.0\2)", out)
            return out
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback: return simple summary
            return self._generate_fallback_response(question, data, intent)
    
    def _generate_fallback_response(
        self,
        question: str,
        data: List[Dict[str, Any]],
        intent: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a structured fallback when LLM fails. Match live-style sections: list, Key Insights, Recommendations.
        Uses live-style "Top N X by Revenue [in YYYY]:" header when applicable.
        """
        if not data:
            return f"I couldn't find any data matching your question: '{question}'. Please try rephrasing your question or check your filters."
        # Parse rows into (label, rev_f, profit_f, cases, margin_pct) for insights
        rows_parsed: List[tuple] = []
        for row in data[:25]:
            if not isinstance(row, dict):
                continue
            rev = row.get("revenue") or row.get("Revenue") or 0
            profit = row.get("gross_profit") or row.get("Gross_Profit") or 0
            cases = row.get("total_cases") or row.get("Cases") or row.get("cases") or 0
            margin = row.get("margin_pct") or row.get("Margin_%") or ""
            label = (
                row.get("channel") or row.get("Channel")
                or row.get("brand") or row.get("Brand")
                or row.get("business") or row.get("Business")
                or row.get("category") or row.get("Category")
                or row.get("year") or row.get("Year")
                or ""
            )
            try:
                rev_f = float(rev) if rev is not None else 0
                profit_f = float(profit) if profit is not None else 0
                margin_f = float(str(margin).replace("%", "")) if margin and str(margin).replace(".", "").replace("%", "").isdigit() else 0
            except (TypeError, ValueError):
                rev_f, profit_f, margin_f = 0, 0, 0
            rows_parsed.append((label, rev_f, profit_f, cases, margin_f))
        if not rows_parsed:
            return f"I couldn't find any data matching your question: '{question}'."
        # Section 1: Live-style header when "top N" + entity list with one-decimal margin
        top_header = self._top_n_header(question, intent)
        lines = [top_header if top_header else "**Data:**"]
        for (label, rev_f, profit_f, cases, margin_f) in rows_parsed:
            rev_str = f"€{rev_f/1e6:.2f}M" if rev_f >= 1e6 else f"€{rev_f/1e3:.0f}K" if rev_f >= 1e3 else f"€{rev_f:,.0f}"
            profit_str = f"€{profit_f/1e6:.2f}M" if profit_f >= 1e6 else f"€{profit_f/1e3:.0f}K" if profit_f >= 1e3 else f"€{profit_f:,.0f}"
            cases_str = f"{int(float(cases)):,}" if cases is not None and str(cases).replace(".", "").isdigit() else str(cases)
            margin_str = f"{margin_f:.1f}%" if margin_f else ""
            lines.append(f"{label}: Revenue {rev_str}, Profit {profit_str}" + (f" ({margin_str} margin)" if margin_str else "") + f", Cases {cases_str}")
        # Section 2: Key Insights (derived from data)
        top_rev = max(rows_parsed, key=lambda r: r[1])
        top_margin = max(rows_parsed, key=lambda r: r[4]) if any(r[4] for r in rows_parsed) else None
        lines.append("\n**Key Insights:**")
        lines.append(f"• {top_rev[0]} leads in revenue (€{top_rev[1]/1e6:.2f}M).")
        if top_margin and top_margin[0] and top_margin[4]:
            lines.append(f"• {top_margin[0]} has the highest profit margin ({top_margin[4]:.1f}%).")
        lines.append("• Use the table and chart below for full metrics.")
        # Section 3: Recommendations
        lines.append("\n**Recommendations:**")
        lines.append("• Review cost structures for brands with lower margins to improve profitability.")
        lines.append("• Explore volume growth and marketing for high-margin brands to scale revenue.")
        lines.append("• Benchmark top performers and replicate successful pricing and distribution strategies.")
        if len(data) > 25:
            lines.append(f"\n(Showing top 25 of {len(data)} results.)")
        return "\n".join(lines)
