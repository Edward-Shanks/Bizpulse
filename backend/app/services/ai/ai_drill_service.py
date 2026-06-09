"""
AI Drill-Down Service ("Why this number?")

Given a clicked pivot row (e.g. {Brand: "Brillo", Year: 2024}) and a chosen
breakdown dimension (e.g. "customer"), returns the top-N contributors at that
next level along with their share of the total.

This service is a thin orchestrator on top of:
  - AIQueryBuilder  — for safe ClickHouse SQL with RBAC
  - ClickHouseClient — for executing queries
  - utils.access.is_wildcard_access — single source of truth for RBAC wildcards

It deliberately does NOT call the LLM. The drill-down must be fast, factual
and identical to what the dashboard shows.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.database import get_database
from app.database.clickhouse_client import ClickHouseClient
from app.services.ai.ai_query_builder import AIQueryBuilder
from app.services.ai.utils.access import is_wildcard_access

logger = logging.getLogger(__name__)


class AIDrillService:
    """Build a "Why this number?" breakdown for a clicked pivot row."""

    # Dimensions the user is allowed to break down into
    SUPPORTED_BREAKDOWNS = [
        "customer", "channel", "month_name", "sub_category",
        "category", "business", "brand", "sku",
    ]

    # Map from intent-style filter key -> MongoDB access key
    DIM_TO_ACCESS_KEY = {
        "business": "businesses",
        "channel": "channels",
        "brand": "brands",
        "category": "categories",
        "sub_category": "sub_categories",
        "customer": "customers",
        "sku": "sku",
    }

    EXPECTED_FILTER_KEYS = [
        "business", "channel", "brand", "category", "sub_category",
        "customer", "sku", "year", "quarter", "month_name",
    ]

    def __init__(self) -> None:
        self.query_builder = AIQueryBuilder()
        self.clickhouse_client = ClickHouseClient()
        self.db = get_database()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def drill_down(
        self,
        breakdown_by: str,
        filters: Dict[str, Any],
        measure: Optional[str],
        limit: Optional[int],
        user_email: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Return the breakdown of the given (filter context) by the chosen
        dimension. Always RBAC-enforced.

        Returns dict:
          {
            "breakdown_by": "customer",
            "measure": "gsales",
            "filters_applied": {...},
            "total": 3950000.0,
            "rows": [
              {"Customer": "BWG", "Revenue": 2.1M, "share_pct": 53.2, ...},
              ...
            ],
            "denied": False,
            "message": null
          }
        """
        if breakdown_by not in self.SUPPORTED_BREAKDOWNS:
            raise ValueError(f"Unsupported breakdown dimension: {breakdown_by}")

        # 1) Load RBAC
        user = await self._load_user(user_email)
        if not user:
            raise ValueError(f"User not found: {user_email}")
        access = user.get("access") or {}
        if not access:
            raise ValueError(f"User has no access permissions: {user_email}")

        normalized_filters = self._normalize_filters(filters or {})

        # 2) RBAC: deny if the user can't see the breakdown dim at all
        denial = self._check_rbac_deny(breakdown_by, normalized_filters, access)
        if denial:
            return {
                "breakdown_by": breakdown_by,
                "measure": measure or "gsales",
                "filters_applied": normalized_filters,
                "total": 0,
                "rows": [],
                "denied": True,
                "message": denial,
            }

        # 3) Build synthetic intent and reuse the existing query builder.
        # Using time_range=lifetime because any time slice the user wants
        # is already encoded explicitly in filters.year / quarter / month_name.
        safe_limit = max(1, min(int(limit or 10), 50))
        intent: Dict[str, Any] = {
            "metric": measure or "gsales",
            "dimensions": [breakdown_by],
            "filters": normalized_filters,
            "time_range": {"type": "lifetime", "value": None},
            "aggregation": "sum",
            "limit": safe_limit,
        }

        query, _ = self.query_builder.build_query(intent, access, tenant_id)
        logger.info(
            "AI_DRILL | user=%s breakdown_by=%s filters=%s",
            user_email, breakdown_by, normalized_filters,
        )
        logger.info("AI_DRILL | query=%s", query)

        # 4) Execute on ClickHouse (no implicit time filter — we already have one if needed)
        result = self.clickhouse_client.execute_dict(
            query=query,
            tenant_id=tenant_id,
            enforce_time_filter=False,
        )
        rows = result if isinstance(result, list) else []
        pivot = self._data_to_pivot(rows)

        # 5) Compute total + share %
        total = self._sum_primary_measure(pivot)
        for r in pivot:
            primary = self._row_primary_measure(r)
            r["share_pct"] = round((primary / total) * 100, 1) if total > 0 else 0.0

        return {
            "breakdown_by": breakdown_by,
            "measure": intent["metric"],
            "filters_applied": normalized_filters,
            "total": float(total),
            "rows": pivot,
            "denied": False,
            "message": None,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _load_user(self, user_email: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.db.users.find_one({"email": user_email})
        except Exception as err:
            logger.error("AI_DRILL | failed to load user RBAC: %s", err)
            return None

    def _check_rbac_deny(
        self,
        breakdown_by: str,
        filters: Dict[str, List[Any]],
        access: Dict[str, Any],
    ) -> Optional[str]:
        """
        Return a user-facing deny message string if the user is not allowed to
        view either:
          - the chosen breakdown dimension
          - any specific filter value (e.g. clicked Brand)
        Otherwise return None.
        """
        # (a) Breakdown dimension must be visible at all
        access_key = self.DIM_TO_ACCESS_KEY.get(breakdown_by)
        if access_key:
            allowed = access.get(access_key)
            if not is_wildcard_access(allowed):
                empty = allowed is None or (isinstance(allowed, list) and len(allowed) == 0)
                if empty:
                    return (
                        f"You don't have permission to break this down by {breakdown_by.replace('_', ' ')}."
                    )

        # (b) Every filter value the caller pinned must be inside the allow list
        for dim, vals in filters.items():
            if not vals:
                continue
            if dim not in self.DIM_TO_ACCESS_KEY:
                continue  # year/quarter/month_name are not RBAC-gated
            allowed = access.get(self.DIM_TO_ACCESS_KEY[dim])
            if is_wildcard_access(allowed):
                continue
            allowed_list = allowed if isinstance(allowed, list) else []
            allowed_lower = {str(x).strip().lower() for x in allowed_list if x}
            for v in vals:
                if str(v).strip().lower() not in allowed_lower:
                    return (
                        f"You don't have permission to view data for the selected "
                        f"{dim.replace('_', ' ')} '{v}'."
                    )
        return None

    def _normalize_filters(self, filters: Dict[str, Any]) -> Dict[str, List[Any]]:
        out: Dict[str, List[Any]] = {}
        for key in self.EXPECTED_FILTER_KEYS:
            raw = filters.get(key) if isinstance(filters, dict) else None
            if raw is None:
                out[key] = []
                continue
            if isinstance(raw, list):
                cleaned = [v for v in raw if v is not None and v != ""]
            else:
                cleaned = [raw] if raw not in (None, "") else []
            if key == "year":
                # ints please
                ints: List[int] = []
                for v in cleaned:
                    try:
                        ints.append(int(v))
                    except (TypeError, ValueError):
                        continue
                out[key] = ints
            elif key == "quarter":
                qs: List[int] = []
                for v in cleaned:
                    try:
                        qv = int(v)
                        if 1 <= qv <= 4:
                            qs.append(qv)
                    except (TypeError, ValueError):
                        continue
                out[key] = qs
            else:
                out[key] = [str(v) for v in cleaned]
        return out

    @staticmethod
    def _sum_primary_measure(pivot: List[Dict[str, Any]]) -> float:
        total = 0.0
        for r in pivot:
            v = AIDrillService._row_primary_measure(r)
            total += v
        return total

    @staticmethod
    def _row_primary_measure(row: Dict[str, Any]) -> float:
        """Pick the most meaningful numeric field in this row for share%."""
        for key in ("Revenue", "Gross_Profit", "Cases"):
            if key in row:
                try:
                    val = row[key]
                    if isinstance(val, Decimal):
                        return float(val)
                    if val is None:
                        return 0.0
                    return float(val)
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    @staticmethod
    def _data_to_pivot(rows: list) -> list:
        """Same key mapping convention as AIService._data_to_pivot_table()."""
        if not rows:
            return []
        key_map = {
            "year": "Year",
            "revenue": "Revenue",
            "gross_profit": "Gross_Profit",
            "total_cases": "Cases",
            "margin_pct": "Margin_%",
            "business": "Business",
            "channel": "Channel",
            "brand": "Brand",
            "category": "Category",
            "sub_category": "Sub_Category",
            "customer": "Customer",
            "sku": "Sku",
            "month_name": "Month_Name",
            "month": "Month",
        }
        pivot: List[Dict[str, Any]] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            row: Dict[str, Any] = {}
            for k, v in r.items():
                key = k if isinstance(k, str) else str(k)
                out_key = key_map.get(key.lower())
                if out_key is None:
                    out_key = key.replace("_", " ").title().replace(" ", "_")
                # Convert Decimal to float so JSON serialization is consistent
                # (FastAPI's encoder turns Decimal into string by default,
                # which would force every consumer to re-parse).
                if isinstance(v, Decimal):
                    try:
                        row[out_key] = float(v)
                    except (TypeError, ValueError):
                        row[out_key] = 0.0
                else:
                    row[out_key] = v
            pivot.append(row)
        return pivot
