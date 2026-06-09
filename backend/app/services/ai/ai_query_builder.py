"""
AI Query Builder
Builds safe ClickHouse SQL from LLM intent + RBAC permissions
"""
import logging
from typing import Dict, Any, List, Optional, Union

from app.core.config import settings
from app.services.ai.utils.access import is_wildcard_access

logger = logging.getLogger(__name__)


class AIQueryBuilder:
    """
    AI Query Builder Service
    
    Converts structured intent + RBAC permissions into safe ClickHouse SQL.
    Always enforces tenant_id and RBAC filters.
    """
    
    # Metric column mapping
    METRIC_COLUMNS = {
        "gsales": "gsales",
        "fgp": "fgp",
        "cases": "cases",
        "price_downs": "price_downs",
        "perm_disc": "perm_disc",
        "transfer_cost": "transfer_cost",
        "group_cost": "group_cost",
        "lta": "lta"
    }
    
    # Dimension column mapping
    DIMENSION_COLUMNS = {
        "business": "business",
        "channel": "channel",
        "brand": "brand",
        "category": "category",
        "sub_category": "sub_category",
        "customer": "customer",
        "sku": "sku",
        "year": "year",
        "month": "month",
        "quarter": "quarter",
        "year_month": "year_month",
        "month_name": "month_name"
    }
    
    # Aggregation function mapping
    AGGREGATION_FUNCTIONS = {
        "sum": "SUM",
        "avg": "AVG",
        "count": "COUNT",
        "max": "MAX",
        "min": "MIN"
    }

    # ClickHouse stores full month names (January, October, ...); intent uses abbreviated (Jan, Oct, ...)
    MONTH_ABBREV_TO_FULL = {
        "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
        "May": "May", "Jun": "June", "Jul": "July", "Aug": "August",
        "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December",
    }
    
    def __init__(self):
        """Initialize query builder"""
        pass
    
    def build_query(
        self,
        intent: Dict[str, Any],
        access: Dict[str, Any],
        tenant_id: str
    ) -> tuple[str, bool]:
        """
        Build ClickHouse SQL query from intent + RBAC
        
        Args:
            intent: LLM intent dict (from AIIntentService)
            access: User's RBAC access dict (from MongoDB)
            tenant_id: Tenant identifier
        
        Returns:
            Tuple of (SQL query string, is_lifetime)
            - is_lifetime: True if user explicitly asked for lifetime (no time filter)
        
        Example:
            >>> intent = {
            >>>     "metric": "gsales",
            >>>     "dimensions": ["business"],
            >>>     "filters": {"business": ["Food"]},
            >>>     "time_range": {"type": "last_n_months", "value": 6},
            >>>     "aggregation": "sum"
            >>> }
            >>> access = {"businesses": ["Food"], "channels": ["*"]}
            >>> query, is_lifetime = builder.build_query(intent, access, "client_001")
        """
        # Extract components
        metric = intent.get("metric") or "gsales"
        # Normalize metric: if LLM returned an unknown/empty metric, fall back to gsales
        if metric not in self.METRIC_COLUMNS:
            metric = "gsales"
        dimensions = intent.get("dimensions", [])
        filters = intent.get("filters", {})
        time_range = intent.get("time_range", {})
        aggregation = intent.get("aggregation", "sum")
        limit = intent.get("limit", 1000)
        try:
            limit = int(limit)
        except Exception:
            limit = 1000
        if limit <= 0:
            limit = 1000
        limit = min(limit, 5000)
        
        # Check if lifetime request
        is_lifetime = time_range.get("type") == "lifetime" or time_range.get("type") == "all_time"
        
        # Build SELECT clause
        select_parts = []
        
        # Add dimensions
        for dim in dimensions:
            if dim in self.DIMENSION_COLUMNS:
                select_parts.append(self.DIMENSION_COLUMNS[dim])
        
        # Add metric aggregation
        metric_col = self.METRIC_COLUMNS.get(metric, "gsales")
        agg_func = self.AGGREGATION_FUNCTIONS.get(aggregation, "SUM")
        order_metric_alias = metric
        if metric == "gsales" and aggregation == "sum":
            # Use revenue alias to avoid alias/column conflicts in ClickHouse aggregate expressions.
            select_parts.append("SUM(gsales) AS revenue")
            order_metric_alias = "revenue"
        else:
            select_parts.append(f"{agg_func}({metric_col}) AS {metric}")
        # Live-style analytics output for sales questions:
        # include profit/cases/margin alongside revenue to match dashboard expectations.
        if metric == "gsales" and aggregation == "sum":
            select_parts.append("SUM(fgp) AS gross_profit")
            select_parts.append("SUM(cases) AS total_cases")
            select_parts.append("round((SUM(fgp) / nullIf(SUM(gsales), 0)) * 100, 2) AS margin_pct")
        
        select_clause = ", ".join(select_parts) if select_parts else f"{agg_func}({metric_col}) AS {metric}"
        
        # Build FROM clause
        from_clause = "FROM bizpulse.sales_analytics"
        
        # Build WHERE clause
        where_conditions = []
        
        # ALWAYS add tenant_id (security)
        where_conditions.append(f"tenant_id = '{tenant_id}'")
        
        # Apply RBAC filters (pass dimensions so we can restrict by allowed values when intent has no filter)
        rbac_filters = self._build_rbac_filters(access, filters, dimensions)
        where_conditions.extend(rbac_filters)
        # Apply non-RBAC time/entity filters coming from intent
        # (e.g. year/quarter/month_name are not part of RBAC access lists)
        direct_filters = self._build_direct_filters(filters)
        where_conditions.extend(direct_filters)
        
        # Apply time filter (unless lifetime)
        if not is_lifetime:
            time_filter = self._build_time_filter(time_range)
            if time_filter:
                where_conditions.append(time_filter)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Build GROUP BY clause
        group_by_clause = ""
        if dimensions:
            group_by_cols = [self.DIMENSION_COLUMNS.get(dim, dim) for dim in dimensions if dim in self.DIMENSION_COLUMNS]
            if group_by_cols:
                group_by_clause = f"GROUP BY {', '.join(group_by_cols)}"
        
        # Build ORDER BY clause (order by metric descending)
        order_by_clause = f"ORDER BY {order_metric_alias} DESC"
        
        # Build LIMIT clause (safety limit)
        limit_clause = f"LIMIT {limit}"
        
        # Combine query
        query_parts = [
            f"SELECT {select_clause}",
            from_clause,
            where_clause,
            group_by_clause,
            order_by_clause,
            limit_clause
        ]
        
        query = " ".join([part for part in query_parts if part])
        
        logger.info("AI_QUERY_BUILDER | metric=%s dimensions=%s filters=%s time_range=%s aggregation=%s limit=%s",
                    metric, dimensions, filters, time_range, aggregation, limit)
        logger.info("AI_QUERY_BUILDER | query=%s", query)
        logger.info("AI_QUERY_BUILDER | is_lifetime=%s", is_lifetime)
        
        return query, is_lifetime
    
    def _build_rbac_filters(
        self,
        access: Dict[str, Any],
        intent_filters: Dict[str, List[str]],
        dimensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        Build RBAC filters from user access + intent filters
        
        When grouping by a dimension (e.g. business) with no intent filter, restrict to user's allowed values.
        
        Args:
            access: User's RBAC access dict
            intent_filters: Filters from intent
            dimensions: Grouping dimensions from intent (so we can apply RBAC when filter is empty)
        
        Returns:
            List of WHERE conditions
        """
        dimensions = dimensions or []
        filters = []
        access_key_map = {
            "business": "businesses",
            "channel": "channels",
            "brand": "brands",
            "category": "categories",
            "sub_category": "sub_categories",
            "customer": "customers",
            "sku": "sku"
        }

        # Wildcard detection is centralised in app.services.ai.utils.access
        # so the chat pre-check (ai_service.STEP 2.5) and the SQL builder here
        # can never disagree on what "full access" means for any user.
        _has_full_access = is_wildcard_access

        def _normalize_allowed(allowed_values: Any) -> List[str]:
            if allowed_values is None:
                return []
            if isinstance(allowed_values, list):
                return allowed_values
            if isinstance(allowed_values, str) and allowed_values.strip().lower() in ("*", "all"):
                return ["*"]
            return []

        # RBAC: dimensions or intent filters that touch a restricted dimension
        restricted_dims = set(dimensions) | {d for d in intent_filters if d in access_key_map and intent_filters.get(d)}
        for dimension in restricted_dims:
            if dimension not in access_key_map:
                continue
            access_key = access_key_map[dimension]
            allowed = _normalize_allowed(access.get(access_key))
            if _has_full_access(allowed):
                continue
            # Empty access = no access to this dimension -> return no rows
            if not allowed or (isinstance(allowed, list) and len(allowed) == 0):
                logger.warning(f"RBAC: user has no access to {dimension} (empty list); denying query.")
                filters.append("1 = 0")
                return filters

        # When intent has no filter for a dimension but user has limited access, restrict to allowed values
        for dimension in dimensions:
            if dimension not in access_key_map:
                continue
            intent_values = intent_filters.get(dimension, [])
            if intent_values:
                continue
            allowed_values = _normalize_allowed(access.get(access_key_map[dimension]))
            if _has_full_access(allowed_values) or not allowed_values:
                continue
            if len(allowed_values) > 0:
                filters.append(
                    f"lowerUTF8({dimension}) IN ({self._format_values(allowed_values, lowercase=True)})"
                )

        # Intent-specified filters (validate against access)
        for dimension, intent_values in intent_filters.items():
            if not intent_values:
                continue
            access_key = access_key_map.get(dimension)
            if not access_key:
                continue
            allowed_values = _normalize_allowed(access.get(access_key))
            if _has_full_access(allowed_values):
                filters.append(
                    f"lowerUTF8({dimension}) IN ({self._format_values(intent_values, lowercase=True)})"
                )
            elif isinstance(allowed_values, list) and len(allowed_values) > 0:
                # CASE-INSENSITIVE access check. LLMs frequently lowercase entity
                # names (e.g. "brillo") while MongoDB stores them in proper case
                # ("Brillo"). Without this normalization a legitimate user would
                # be falsely denied. The SQL itself already wraps the column in
                # lowerUTF8() so case doesn't matter for the actual ClickHouse
                # match — this gate just decides which values we let through.
                allowed_lower_set = {
                    str(v).strip().lower() for v in allowed_values if v not in (None, "")
                }
                valid_values = [
                    v for v in intent_values
                    if str(v).strip().lower() in allowed_lower_set
                ]
                if valid_values:
                    filters.append(
                        f"lowerUTF8({dimension}) IN ({self._format_values(valid_values, lowercase=True)})"
                    )
                else:
                    logger.warning(
                        f"User requested {dimension}={intent_values} but only has access to {allowed_values}"
                    )
                    filters.append("1 = 0")
                    return filters
        return filters

    def _build_direct_filters(self, intent_filters: Dict[str, List[str]]) -> List[str]:
        """
        Build direct (non-RBAC) filters like year/quarter/month_name.
        """
        filters: List[str] = []
        for key in ("year", "quarter", "month_name"):
            values = intent_filters.get(key, [])
            if not values:
                continue
            if key in ("year", "quarter"):
                numeric_values = []
                for v in values:
                    try:
                        numeric_values.append(str(int(v)))
                    except Exception:
                        continue
                if numeric_values:
                    filters.append(f"{key} IN ({', '.join(numeric_values)})")
            elif key == "month_name":
                # ClickHouse table uses full month names (January, October); intent uses Jan, Oct, etc.
                full_months = [
                    self.MONTH_ABBREV_TO_FULL.get(str(v).strip(), str(v).strip())
                    for v in values
                ]
                filters.append(f"{key} IN ({self._format_values(full_months)})")
            else:
                filters.append(f"{key} IN ({self._format_values(values)})")
        return filters
    
    def _build_time_filter(self, time_range: Dict[str, Any]) -> Optional[str]:
        """
        Build time filter from time_range intent
        
        Args:
            time_range: Time range dict from intent
        
        Returns:
            WHERE condition string or None
        """
        time_type = time_range.get("type")
        time_value = time_range.get("value")
        
        if time_type == "last_n_days" and time_value:
            return f"date >= today() - INTERVAL {time_value} DAY"
        elif time_type == "last_n_months" and time_value:
            return f"date >= addMonths(today(), -{time_value})"
        elif time_type == "current_month":
            return "date >= toStartOfMonth(today()) AND date < addMonths(toStartOfMonth(today()), 1)"
        elif time_type == "last_year":
            return "date >= addYears(today(), -1)"
        elif time_type == "custom" and time_value is None:
            # No explicit time - backend will apply default (handled by enforce_time_filter)
            return None
        
        # Default: no time filter (will be handled by default time filter)
        return None
    
    def _format_values(self, values: List[str], lowercase: bool = False) -> str:
        """
        Format list of values for SQL IN clause
        
        Args:
            values: List of string values
        
        Returns:
            Formatted string: 'value1', 'value2', ...
        """
        if lowercase:
            return ", ".join("'" + str(v).lower().replace("'", "''") + "'" for v in values)
        return ", ".join("'" + str(v).replace("'", "''") + "'" for v in values)
