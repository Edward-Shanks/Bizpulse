"""
Permission Hash Generator
Generates deterministic hash from user RBAC access object
"""
import hashlib
import json
from typing import Dict, Any, Union, List


def generate_permissions_hash(access: Dict[str, Any]) -> str:
    """
    Generate deterministic hash from user RBAC access object
    
    Critical: Must hash FULL access object with deterministic sorting
    to ensure same permissions always generate same hash.
    
    Args:
        access: User access dict from MongoDB (e.g., bizpulse_rbac.users.access)
            Structure:
            {
                "businesses": ["Food"] or ["*"],
                "channels": ["Grocery"],
                "brands": ["Cali Cali", "Bensons"],
                "categories": "all" or ["Snacks"],
                "sub_categories": "all" or ["Chips"],
                "customers": "all" or ["Amazon"],
                "allowed_metrics": ["gsales", "fgp"] or ["*"]
            }
    
    Returns:
        SHA256 hash string (hex)
    
    Example:
        >>> access1 = {"businesses": ["Food"], "channels": ["Grocery"]}
        >>> access2 = {"businesses": ["Food"], "channels": ["Grocery"]}
        >>> hash1 = generate_permissions_hash(access1)
        >>> hash2 = generate_permissions_hash(access2)
        >>> assert hash1 == hash2  # Same permissions = same hash
    """
    def _canonicalize(value: Union[str, List[str], None]) -> Union[str, List[str]]:
        """
        Canonicalize permission values for deterministic hashing
        
        - Lists are sorted
        - Strings like "all" are kept as-is
        - None becomes empty list
        """
        if value is None:
            return []
        if isinstance(value, list):
            return sorted(value)
        return value
    
    normalized = {
        "businesses": _canonicalize(access.get("businesses", [])),
        "channels": _canonicalize(access.get("channels", [])),
        "brands": _canonicalize(access.get("brands", [])),
        "categories": _canonicalize(access.get("categories")),
        "sub_categories": _canonicalize(access.get("sub_categories")),
        "customers": _canonicalize(access.get("customers")),
        "metrics": _canonicalize(access.get("allowed_metrics", []))
    }
    
    # Convert to JSON string with sorted keys for deterministic hashing
    permissions_string = json.dumps(normalized, sort_keys=True)
    
    # Generate SHA256 hash
    return hashlib.sha256(permissions_string.encode()).hexdigest()
