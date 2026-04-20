"""
TTL Calculator for AI Cache
Calculates cache TTL based on query type and intent
"""
from typing import Dict, Any


def get_cache_ttl(intent: Dict[str, Any]) -> int:
    """
    Calculate cache TTL (in seconds) based on query intent
    
    Dynamic TTL based on query type:
    - "last 7 days" / "today" → 6 hours (data changes daily)
    - "current month" → 2 hours (monthly data updates)
    - "last year" → 24 hours (yearly data less volatile)
    - Custom date range → 12 hours (balance freshness vs performance)
    - "lifetime" / "all time" → 24 hours (historical data rarely changes)
    
    Args:
        intent: LLM intent dict with time_range info
            Structure:
            {
                "time_range": {
                    "type": "last_n_days" | "current_month" | "last_year" | "lifetime" | "custom",
                    "value": 6  # for last_n_days, last_n_months, etc.
                }
            }
    
    Returns:
        TTL in seconds (int)
    
    Example:
        >>> intent = {"time_range": {"type": "last_n_days", "value": 7}}
        >>> ttl = get_cache_ttl(intent)
        >>> assert ttl == 6 * 3600  # 6 hours
    """
    time_range = intent.get("time_range", {})
    time_type = time_range.get("type", "custom")
    time_value = time_range.get("value", 0)
    
    # Last 7 days or today → 6 hours
    if time_type == "last_n_days" and time_value <= 7:
        return 6 * 3600  # 6 hours
    
    # Current month → 2 hours
    if time_type == "current_month":
        return 2 * 3600  # 2 hours
    
    # Lifetime / all time → 24 hours
    if time_type == "lifetime" or time_type == "all_time":
        return 24 * 3600  # 24 hours
    
    # Last year → 24 hours
    if time_type == "last_year":
        return 24 * 3600  # 24 hours
    
    # Default: 12 hours (for custom ranges, last_n_months, etc.)
    return 12 * 3600  # 12 hours
