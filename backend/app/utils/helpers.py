"""
Helper utility functions
Common functions used across the application
"""
import math
import pandas as pd
from typing import Optional, List, Any, Union
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



