"""
Intent Hash Generator
Generates deterministic hash from LLM intent JSON
"""
import hashlib
import json
from typing import Dict, Any


def generate_intent_hash(intent: Dict[str, Any]) -> str:
    """
    Generate deterministic hash from LLM intent JSON
    
    Args:
        intent: LLM intent dict
            Structure:
            {
                "metric": "gsales",
                "dimensions": ["business"],
                "filters": {
                    "business": ["Food"]
                },
                "time_range": {
                    "type": "last_n_months",
                    "value": 6
                }
            }
    
    Returns:
        SHA256 hash string (hex)
    
    Example:
        >>> intent1 = {"metric": "gsales", "business": "Food"}
        >>> intent2 = {"metric": "gsales", "business": "Food"}
        >>> hash1 = generate_intent_hash(intent1)
        >>> hash2 = generate_intent_hash(intent2)
        >>> assert hash1 == hash2  # Same intent = same hash
    """
    # Convert to JSON string with sorted keys for deterministic hashing
    intent_string = json.dumps(intent, sort_keys=True)
    
    # Generate SHA256 hash
    return hashlib.sha256(intent_string.encode()).hexdigest()
