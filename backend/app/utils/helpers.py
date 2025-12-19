"""
Helper utility functions
Common functions used across the application
"""
import math
import pandas as pd
from typing import Optional, List, Any, Union, Dict
import logging

logger = logging.getLogger(__name__)

def safe_float(value: Any) -> float:
    """
    Safely convert value to float, handling NaN, None, and invalid values
    """
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            if pd.isna(value) or math.isnan(value) or math.isinf(value):
                return 0.0
            return float(value)
        # Try to convert string to float
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def format_currency(value: float) -> str:
    """
    Format currency value with M (millions) or k (thousands) suffix
    """
    if abs(value) >= 1_000_000:
        return f"€{(value / 1_000_000):.1f}M"
    elif abs(value) >= 1_000:
        return f"€{(value / 1_000):.1f}k"
    else:
        return f"€{value:,.0f}"

def format_units(value: float) -> str:
    """
    Format units value with M (millions) or k (thousands) suffix
    """
    if abs(value) >= 1_000_000:
        return f"{(value / 1_000_000):.1f}M"
    elif abs(value) >= 1_000:
        return f"{(value / 1_000):.1f}k"
    else:
        return f"{value:,.0f}"

def parse_list(value: Optional[str], cast=None) -> List[Any]:
    """
    Parse comma-separated string into list
    Optionally cast each item to a specific type
    """
    if not value:
        return []
    items = []
    for part in value.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            if cast:
                items.append(cast(part))
            else:
                items.append(part)
        except Exception:
            continue
    return items

def normalize_category_name(category: str) -> str:
    """
    Normalize category name for case-insensitive matching
    """
    if not category:
        return ""
    # Convert to lowercase and strip whitespace
    normalized = category.lower().strip()
    # Capitalize first letter of each word
    return ' '.join(word.capitalize() for word in normalized.split())

def get_month_order(month_name: str) -> int:
    """
    Get month order for sorting (1-12)
    Handles both full names (January) and abbreviations (Jan)
    """
    month_order_map = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9, 'sept': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    month_lower = str(month_name).lower().strip()
    return month_order_map.get(month_lower, 999)  # Unknown months go to end

def sort_by_month(data_list: List[Dict], month_key: str = "Month_Name") -> List[Dict]:
    """
    Sort list of dictionaries by month in chronological order (Jan, Feb, Mar, ...)
    """
    return sorted(data_list, key=lambda x: get_month_order(x.get(month_key, "")))

def sort_by_year(data_list: List[Dict], year_key: str = "Year") -> List[Dict]:
    """
    Sort list of dictionaries by year in ascending order (2023, 2024, 2025)
    """
    return sorted(data_list, key=lambda x: int(x.get(year_key, 0)) if x.get(year_key) else 0)

def sort_by_metric(data_list: List[Dict], metric_key: str, reverse: bool = True) -> List[Dict]:
    """
    Sort list of dictionaries by metric in descending order (largest first)
    """
    return sorted(data_list, key=lambda x: safe_float(x.get(metric_key, 0)), reverse=reverse)



