"""
RBAC Access — wildcard detection

A single source of truth for "does this access value mean full access?".
Used by:
  - app.services.ai.ai_service.process_question  (STEP 2.5 deny pre-check)
  - app.services.ai.ai_query_builder            (WHERE-clause RBAC restriction)

MongoDB stores per-dimension access in a few different shapes across the
codebase / tenant data. All of the following must be treated as "full access":

  - the plain string  "all" or "*"            (case-insensitive)
  - a list containing "all" or "*"            (e.g. ["*"], ["all"], ["*", "..."])
  - a list containing any token whose lowercase is "all" or "*"

Anything else (None, empty list, list of specific values) is NOT full access.
"""
from __future__ import annotations

from typing import Any

__all__ = ["is_wildcard_access"]


_WILDCARD_TOKENS = {"all", "*"}


def is_wildcard_access(allowed_value: Any) -> bool:
    """
    Return True when the given access value represents unrestricted access.

    This is intentionally permissive about input shape so it cannot be the
    cause of a false-deny: any of the forms below count as wildcard.

    >>> is_wildcard_access("all")
    True
    >>> is_wildcard_access("*")
    True
    >>> is_wildcard_access(["*"])
    True
    >>> is_wildcard_access(["all"])
    True
    >>> is_wildcard_access(["*", "Food"])  # mixed wildcard + explicit
    True
    >>> is_wildcard_access(["Food"])
    False
    >>> is_wildcard_access([])
    False
    >>> is_wildcard_access(None)
    False
    """
    if allowed_value is None:
        return False
    if isinstance(allowed_value, str):
        return allowed_value.strip().lower() in _WILDCARD_TOKENS
    if isinstance(allowed_value, (list, tuple, set)):
        for item in allowed_value:
            if isinstance(item, str) and item.strip().lower() in _WILDCARD_TOKENS:
                return True
        return False
    return False
