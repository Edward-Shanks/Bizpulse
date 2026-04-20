"""
AI Question Clarity Service
Uses the LLM to understand whether a question is about business data we can answer.
If not (any topic: news, war, greetings, jokes, etc.), returns clarification with ONLY business-related suggestions.
No fixed keyword list — the LLM handles all kinds of phrasing so the chatbot works for thousands of users.
"""
import json
import logging
import re
from typing import List, Tuple

from app.utils.ai_service import query_llm

logger = logging.getLogger(__name__)


class AIClarityService:
    """
    Question relevance checker for the AI chatbot.
    LLM decides: "Is this question about our business data (revenue, profit, brands, etc.)?"
    If no → return clarification with 5-6 business-only suggested questions. If yes → proceed to answer.
    """

    # Used only for safeguard when query returns empty: avoid generating an answer about these topics (ai_service)
    OFF_TOPIC_KEYWORDS = frozenset({
        "russia", "ukraine", "iran", "israel", "war", "conflict", "invasion", "incident", "recent events",
        "election", "politics", "crime", "murder", "attack", "strike", "hello", "how are you", "joke", "news",
        "stock", "share price", "trading", "nasdaq", "sensex", "crypto", "bitcoin",
    })

    # Patterns that indicate an OBVIOUS business question — skip LLM to save tokens
    CLEAR_PATTERNS = [
        r"top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers|channel|channels)",
        r"show\s+me\s+top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers)",
        r"tell\s+me\s+top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers)",
        r"compare\s+(brand|brands|business|businesses|category|categories)\s+",
        r"compare\s+q[1-4].*business",
        r"compare\s+q[1-4].*for\s+business",
        r"q[1-4].*for\s+business.*compare",
        r"q[1-4].*business.*across",
        r"compare\s+q[1-4].*across\s+years?",
        r"all\s+(brand|brands|business|businesses|category|categories|customer|customers)",
        r"tell\s+me\s+about\s+all\s+(brand|brands|business|businesses|category|categories)",
        r"show\s+me\s+all\s+(brand|brands|business|businesses|category|categories)",
        r"show\s+me\s+(the\s+)?q[1-4]\s+\d{4}\s+revenue\s+for\s+(brands?|business)",
        r"what\s+is\s+the\s+q[1-4]\s+\d{4}\s+revenue\s+for",
        r"could\s+you\s+provide\s+(the\s+)?q[1-4]",
        r"please\s+show\s+me\s+the\s+revenue\s+figures\s+for\s+q[1-4]",
        r"can\s+you\s+display\s+the\s+q[1-4]",
    ]

    # Phrases that mean "not our business data" — stock market, financial markets, etc. Fast path so we never answer these.
    NOT_OUR_BUSINESS_PHRASES = (
        "stock market", "share market", "share price", "share prices", "trading", "equity market",
        "nasdaq", "sensex", "dow jones", "stock exchange", "nifty", "market index", "market indices",
        "crypto", "bitcoin", "forex", "currency exchange", "exchange rate",
    )

    # LLM prompt: single decision — "Is this question about business data we can answer?"
    BUSINESS_RELEVANCE_SYSTEM = (
        "You are a classifier for a BUSINESS INTELLIGENCE chatbot. "
        "This chatbot ONLY answers questions about the COMPANY'S OWN business data it has: revenue, profit, units sold, margins, brands, businesses, categories, customers, channels, SKUs, sub-categories, sales performance, time periods (quarters, years, months). "
        "It does NOT answer: stock market, share prices, trading, equity markets, financial markets, crypto, forex, world news, wars, politics, elections, crimes, incidents, greetings, jokes, weather, sports, general knowledge, or any topic that is not about this company's business data (revenue, profit, brands, categories, etc.). "
        "CRITICAL: 'Business' here means the company's sales/revenue data (brands, categories, profit), NOT the stock market or share market. Questions about 'today stock market', 'share price', 'trading' are NOT business questions for this chatbot. "
        ""
        "Your task: Decide if the user's question is asking about such BUSINESS DATA (revenue, profit, brands, businesses, categories, etc.) that the chatbot can answer from its data. "
        "- If YES (question is clearly about the company's revenue, profit, brands, categories, customers, channels, margins, units, sales performance) → set is_business_question to true, suggested_questions to []. "
        "- If NO (question is about stock market, share price, news, war, politics, incident, joke, greeting, or anything not in the company's business data) → set is_business_question to false and suggest EXACTLY 5-6 questions that ARE only about business data (revenue, profit, brands, businesses, categories). "
        ""
        "Respond ONLY with this JSON, no other text: "
        '{"is_business_question": true or false, "suggested_questions": ["question1", "question2", "question3", "question4", "question5", "question6"]}'
        "If is_business_question is true, suggested_questions must be []. If false, suggested_questions must have 5-6 business-only questions."
    )

    async def check_question_clarity(self, user_message: str) -> Tuple[bool, List[str]]:
        """
        Decide if the question is about business data we can answer.
        Returns (is_clear: bool, suggested_questions: List[str]).
        is_clear=True means proceed to answer; False means return clarification with suggested_questions (business-only).
        """
        if not user_message or not user_message.strip():
            return True, []

        user_msg_lower = user_message.lower().strip()

        # Fast path: obvious business question (save LLM call)
        for pattern in self.CLEAR_PATTERNS:
            if re.search(pattern, user_msg_lower):
                logger.info("AI_CLARITY | obvious business pattern, proceed")
                return True, []

        # Fast path: very short greeting only (save LLM call)
        if re.match(r"^(hi|hello|hey|yo|how are you|what\'?s up|good morning|good afternoon|good evening)[\s.!?]*$", user_msg_lower):
            logger.info("AI_CLARITY | short greeting, return business-only suggestions")
            return False, self._fallback_off_topic_suggestions()

        # Fast path: stock market / financial markets / share price — not our business data
        if any(phrase in user_msg_lower for phrase in self.NOT_OUR_BUSINESS_PHRASES):
            logger.info("AI_CLARITY | question about stock market/financial markets, return business-only suggestions")
            return False, self._fallback_off_topic_suggestions()

        # LLM decides: is this question about our business data? Handles any phrasing (news, war, incidents, vague, etc.)
        try:
            is_business, suggested = await self._check_business_relevance_llm(user_message)
            if not is_business:
                if not suggested:
                    suggested = self._fallback_off_topic_suggestions()
                logger.info("AI_CLARITY | LLM: not business question, returning %s suggestions", len(suggested))
                return False, suggested[:6]
            logger.info("AI_CLARITY | LLM: business question, proceed")
            return True, []
        except Exception as e:
            logger.warning("AI_CLARITY | LLM relevance check failed, proceeding to answer: %s", e)
            return True, []

    async def _check_business_relevance_llm(self, question: str) -> Tuple[bool, List[str]]:
        """Ask LLM: is this question about business data we can answer? Returns (is_business_question, suggested_questions)."""
        prompt = (
            f"User question: {question}\n\n"
            "Is this question about business data (revenue, profit, brands, businesses, categories, customers, channels, margins, units, sales performance) that the chatbot can answer? "
            "Reply with JSON only: {\"is_business_question\": true/false, \"suggested_questions\": [\"...\", ...]}"
        )
        response = await query_llm(
            prompt,
            conversation_history=None,
            custom_system_message=self.BUSINESS_RELEVANCE_SYSTEM,
            temperature=0.2,
            max_tokens=800,
        )
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                is_business = data.get("is_business_question", True)
                suggestions = data.get("suggested_questions", [])
                if not isinstance(suggestions, list):
                    suggestions = []
                return is_business, suggestions
        except json.JSONDecodeError:
            pass
        return True, []  # On parse error, proceed so we don't block legitimate questions

    def _fallback_suggested_questions(self, user_message: str) -> List[str]:
        """Generate fallback suggested questions when LLM marks unclear but returns no suggestions."""
        user_msg_lower = (user_message or "").lower()
        if "brand" in user_msg_lower or "brands" in user_msg_lower:
            return [
                "Show me the Q2 2023 revenue for brands Cali Cali, Bonne Maman, and Green Aware.",
                "Could you provide the Q2 2023 revenue details for Cali Cali, Bonne Maman, and Green Aware?",
                "What is the Q2 2023 revenue for each of the three brands: Cali Cali, Bonne Maman, and Green Aware?",
                "Please show me the revenue figures for Q2 2023 for the brands Cali Cali, Bonne Maman, and Green Aware.",
                "Can you display the Q2 2023 revenue for the brands Cali Cali, Bonne Maman, and Green Aware?",
                "Tell me about all brands by revenue and profit.",
            ]
        if "business" in user_msg_lower or "businesses" in user_msg_lower:
            return [
                "Tell me about all businesses by revenue and profit.",
                "Show me the top 10 businesses by revenue.",
                "Compare all businesses by revenue and margin.",
                "Tell me about business performance by revenue and profit margin.",
                "Show me business rankings by revenue.",
                "Tell me about business revenue, profit, and units.",
            ]
        if "category" in user_msg_lower or "categories" in user_msg_lower:
            return [
                "Tell me about all categories by revenue and profit.",
                "Show me the top 10 categories by revenue.",
                "Compare all categories by revenue and margin.",
                "Tell me about category performance by revenue and profit margin.",
                "Show me category rankings by revenue.",
                "Tell me about category revenue, profit, and units.",
            ]
        return [
            "Tell me about all brands by revenue and profit.",
            "Show me the top 10 brands by revenue.",
            "Compare all brands by revenue and margin.",
            "Show me the Q2 2023 revenue for brands Cali Cali, Bonne Maman, and Green Aware.",
            "Tell me about brand performance by revenue and profit margin.",
            "Show me brand rankings by revenue.",
        ]

    def _is_off_topic(self, question_lower: str) -> bool:
        """True if the question is clearly not about business data (greetings, news, war, politics, etc.)."""
        if not question_lower or len(question_lower.strip()) < 3:
            return False
        # Short greetings
        if question_lower.strip() in ("hi", "hello", "hey", "yo", "good morning", "good afternoon", "good evening"):
            return True
        # Single short phrase that looks like greeting
        if re.match(r"^(hi|hello|hey|how are you|what\'?s up|how do you do)[\s.!?]*$", question_lower.strip()):
            return True
        # Contains off-topic keywords (avoid matching "business" in "business performance")
        words = set(re.findall(r"\b\w+\b", question_lower))
        if words & self.OFF_TOPIC_KEYWORDS:
            return True
        # Phrase contains off-topic bigrams/trigrams
        for phrase in self.OFF_TOPIC_KEYWORDS:
            if phrase in question_lower:
                return True
        return False

    def _fallback_off_topic_suggestions(self) -> List[str]:
        """Business-only suggested questions when user asks off-topic (no LLM call). Matches live chatbot behavior."""
        return [
            "Can you show me the top 10 brands by revenue?",
            "Could you provide a comparison of all businesses by profit margin?",
            "What are the sales units for each category in November 2025?",
            "Please draft an email summarizing the business performance for November 2025.",
            "Show me the top 5 customers based on revenue generated.",
            "Compare the performance of all categories for the last quarter.",
        ]
