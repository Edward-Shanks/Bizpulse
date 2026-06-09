"""
Narrative Generator — Storytelling Mode

Builds a short, deterministic list of "Key Insights" bullet strings from a
pivot_table (the same shape consumed by the frontend chart). Insights are
computed from the data itself (top contributor, share %, range, YoY change,
margin highlights), so they are always factually correct and do not depend
on the LLM.

This runs in microseconds. It returns 3–5 short, human-readable bullets.

Pivot table shape (list of dicts), examples of keys:
  - dimensions: Year, Month_Name, Month, Business, Channel, Brand, Category,
                Sub_Category, Customer, Sku
  - measures:   Revenue, Gross_Profit, Cases, Units, Margin_%
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Column classification
# ---------------------------------------------------------------------------

_TIME_KEYS = ("Year", "Month_Name", "Month Name", "Month", "Quarter", "Date")

# Columns that look numeric but are NOT business measures (so they must never
# be auto-picked as the storytelling measure)
_NON_MEASURE_NUMERIC_KEYS = {
    "Year",
    "Month",
    "Quarter",
    "Day",
    "Week",
    "Period",
}

_DIMENSION_KEYS_PRIORITY = (
    "Brand",
    "Business",
    "Category",
    "Sub_Category",
    "Channel",
    "Customer",
    "Sku",
)

# Ordered by importance — first hit wins as primary measure for storytelling
_MEASURE_KEYS_PRIORITY = (
    "Revenue",
    "Gross_Profit",
    "Cases",
    "Units",
    "Margin_%",
)


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float, Decimal)):
        return True
    if isinstance(value, str):
        try:
            float(value.replace(",", "").replace("€", "").replace("$", "").strip())
            return True
        except (ValueError, AttributeError):
            return False
    # Any other type that exposes __float__ (e.g. numpy scalars) is treated as numeric
    if hasattr(value, "__float__"):
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
    return False


def _to_float(value: Any) -> float:
    if value is None or isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    if isinstance(value, str):
        try:
            return float(
                value.replace(",", "").replace("€", "").replace("$", "").strip()
            )
        except (ValueError, AttributeError):
            return 0.0
    if hasattr(value, "__float__"):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _detect_time_column(sample_row: Dict[str, Any]) -> Optional[str]:
    for key in _TIME_KEYS:
        if key in sample_row:
            return key
    return None


def _detect_dimension_column(
    sample_row: Dict[str, Any], time_col: Optional[str]
) -> Optional[str]:
    for key in _DIMENSION_KEYS_PRIORITY:
        if key in sample_row and key != time_col:
            return key
    # Fallback: any non-numeric column that's not the time column
    for key, value in sample_row.items():
        if key == time_col:
            continue
        if not _is_number(value):
            return key
    return None


def _detect_measure_column(sample_row: Dict[str, Any]) -> Optional[str]:
    for key in _MEASURE_KEYS_PRIORITY:
        if key in sample_row and _is_number(sample_row[key]):
            return key
    # Fallback: any numeric column that is NOT a time/date column. We do NOT
    # want "Year" or "Month" to be treated as a measure — those are dimensions.
    for key, value in sample_row.items():
        if key in _NON_MEASURE_NUMERIC_KEYS:
            continue
        if key in _TIME_KEYS:
            continue
        if _is_number(value):
            return key
    return None


# ---------------------------------------------------------------------------
# Formatting helpers — must match the look-and-feel used in the frontend
# ---------------------------------------------------------------------------

def _format_currency(value: float) -> str:
    """€X.XXM for >= 1M, €XK for >= 1K, else €X."""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"€{value / 1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"€{value / 1_000:.0f}K"
    return f"€{value:,.0f}"


def _format_number(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def _format_measure(measure: str, value: float) -> str:
    if measure in ("Revenue", "Gross_Profit"):
        return _format_currency(value)
    if measure == "Margin_%":
        return f"{value:.1f}%"
    return _format_number(value)


def _pretty_measure_name(measure: str) -> str:
    return {
        "Revenue": "revenue",
        "Gross_Profit": "gross profit",
        "Cases": "cases",
        "Units": "units",
        "Margin_%": "margin",
    }.get(measure, measure.replace("_", " ").lower())


def _pretty_dim_name(dim: str) -> str:
    return {
        "Sub_Category": "sub-category",
        "Sku": "SKU",
    }.get(dim, dim.lower())


def _pretty_dim_plural(dim: str) -> str:
    return {
        "Brand": "brands",
        "Business": "businesses",
        "Category": "categories",
        "Sub_Category": "sub-categories",
        "Channel": "channels",
        "Customer": "customers",
        "Sku": "SKUs",
    }.get(dim, _pretty_dim_name(dim) + "s")


# ---------------------------------------------------------------------------
# Insight builders
# ---------------------------------------------------------------------------

def _aggregate_by_dim(
    rows: List[Dict[str, Any]], dim_col: str, measure: str, how: str = "sum"
) -> List[Tuple[Any, float]]:
    """
    Collapse rows by dimension. When the same dimension value appears multiple
    times (e.g. one row per year), we sum (or average) the measure across rows
    so that the dimension's true contribution is reflected.

    Returns a list of (dim_value, aggregated_measure) tuples.
    """
    bucket_sum: Dict[Any, float] = {}
    bucket_count: Dict[Any, int] = {}
    for r in rows:
        dim_v = r.get(dim_col)
        if dim_v is None:
            continue
        m = r.get(measure)
        if not _is_number(m):
            continue
        bucket_sum[dim_v] = bucket_sum.get(dim_v, 0.0) + _to_float(m)
        bucket_count[dim_v] = bucket_count.get(dim_v, 0) + 1

    if how == "avg":
        return [(k, v / bucket_count[k]) for k, v in bucket_sum.items() if bucket_count[k] > 0]
    return list(bucket_sum.items())


def _insight_total(
    rows: List[Dict[str, Any]], measure: str, dim_col: Optional[str]
) -> Optional[str]:
    if measure == "Margin_%":
        # Margin should be averaged across rows, not summed
        values = [_to_float(r.get(measure)) for r in rows if _is_number(r.get(measure))]
        if not values:
            return None
        avg = sum(values) / len(values)
        return f"Average {_pretty_measure_name(measure)} across the selection is {_format_measure(measure, avg)}."
    total = sum(_to_float(r.get(measure)) for r in rows if _is_number(r.get(measure)))
    if total == 0:
        return None
    if dim_col:
        unique_count = len({r.get(dim_col) for r in rows if r.get(dim_col) is not None})
        if unique_count > 0:
            dim_word = _pretty_dim_name(dim_col) if unique_count == 1 else _pretty_dim_plural(dim_col)
            scope = f"{unique_count} {dim_word}"
            return f"Total {_pretty_measure_name(measure)} in this view is {_format_measure(measure, total)} across {scope}."
    return f"Total {_pretty_measure_name(measure)} in this view is {_format_measure(measure, total)} across {len(rows)} rows."


def _insight_top_contributor(
    rows: List[Dict[str, Any]], dim_col: str, measure: str
) -> Optional[str]:
    if measure == "Margin_%":
        return None
    aggregated = _aggregate_by_dim(rows, dim_col, measure, how="sum")
    if not aggregated:
        return None
    total = sum(v for _, v in aggregated)
    if total <= 0:
        return None
    top = max(aggregated, key=lambda x: x[1])
    share = (top[1] / total) * 100
    return (
        f"{top[0]} leads with {_format_measure(measure, top[1])} of "
        f"{_pretty_measure_name(measure)} — {share:.1f}% of the total."
    )


def _insight_top_three_share(
    rows: List[Dict[str, Any]], dim_col: str, measure: str
) -> Optional[str]:
    if measure == "Margin_%":
        return None
    aggregated = _aggregate_by_dim(rows, dim_col, measure, how="sum")
    if len(aggregated) < 4:
        return None
    total = sum(v for _, v in aggregated)
    if total <= 0:
        return None
    aggregated.sort(key=lambda x: x[1], reverse=True)
    top3 = aggregated[:3]
    top3_share = sum(v for _, v in top3) / total * 100
    top3_names = ", ".join(str(name) for name, _ in top3)
    return (
        f"The top 3 {_pretty_dim_plural(dim_col)} ({top3_names}) account for "
        f"{top3_share:.1f}% of total {_pretty_measure_name(measure)}."
    )


def _insight_yoy_change(
    rows: List[Dict[str, Any]], time_col: str, measure: str
) -> Optional[str]:
    if measure == "Margin_%":
        return None
    if time_col != "Year":
        return None
    by_year: Dict[int, float] = {}
    for r in rows:
        try:
            year = int(_to_float(r.get(time_col)))
        except (TypeError, ValueError):
            continue
        if not _is_number(r.get(measure)):
            continue
        by_year[year] = by_year.get(year, 0.0) + _to_float(r.get(measure))
    if len(by_year) < 2:
        return None
    sorted_years = sorted(by_year.keys())
    latest, prev = sorted_years[-1], sorted_years[-2]
    latest_v, prev_v = by_year[latest], by_year[prev]
    if prev_v == 0:
        return None
    change_pct = (latest_v - prev_v) / abs(prev_v) * 100
    direction = "up" if change_pct >= 0 else "down"
    return (
        f"{measure.replace('_', ' ')} in {latest} is {direction} {abs(change_pct):.1f}% "
        f"vs {prev} ({_format_measure(measure, latest_v)} vs {_format_measure(measure, prev_v)})."
    )


def _insight_biggest_mover(
    rows: List[Dict[str, Any]], dim_col: str, time_col: str, measure: str
) -> Optional[str]:
    if measure == "Margin_%":
        return None
    if time_col != "Year":
        return None
    # Group by (dim, year)
    by_dim_year: Dict[Any, Dict[int, float]] = {}
    for r in rows:
        dim_v = r.get(dim_col)
        if dim_v is None:
            continue
        try:
            year = int(_to_float(r.get(time_col)))
        except (TypeError, ValueError):
            continue
        if not _is_number(r.get(measure)):
            continue
        by_dim_year.setdefault(dim_v, {}).setdefault(year, 0.0)
        by_dim_year[dim_v][year] += _to_float(r.get(measure))
    movers: List[Tuple[Any, float, float, int, int]] = []
    for dim_v, years in by_dim_year.items():
        if len(years) < 2:
            continue
        sorted_years = sorted(years.keys())
        latest, prev = sorted_years[-1], sorted_years[-2]
        latest_v, prev_v = years[latest], years[prev]
        if prev_v == 0:
            continue
        change_pct = (latest_v - prev_v) / abs(prev_v) * 100
        movers.append((dim_v, change_pct, latest_v - prev_v, latest, prev))
    if not movers:
        return None
    biggest = max(movers, key=lambda x: abs(x[1]))
    dim_v, pct, _abs_delta, latest, prev = biggest
    direction = "grew" if pct >= 0 else "declined"
    return (
        f"Biggest mover: {dim_v} {direction} {abs(pct):.1f}% from {prev} to {latest}."
    )


def _insight_margin_leader(
    rows: List[Dict[str, Any]], dim_col: str
) -> Optional[str]:
    # Average margin per dimension so that a brand split across years gets
    # collapsed into a single, fair comparison value.
    aggregated = _aggregate_by_dim(rows, dim_col, "Margin_%", how="avg")
    if len(aggregated) < 2:
        return None
    top = max(aggregated, key=lambda x: x[1])
    if top[1] <= 0:
        return None
    return f"Highest margin: {top[0]} at {top[1]:.1f}%."


def _insight_concentration_warning(
    rows: List[Dict[str, Any]], dim_col: str, measure: str
) -> Optional[str]:
    if measure == "Margin_%":
        return None
    aggregated = _aggregate_by_dim(rows, dim_col, measure, how="sum")
    if len(aggregated) < 3:
        return None
    total = sum(v for _, v in aggregated)
    if total <= 0:
        return None
    aggregated.sort(key=lambda x: x[1], reverse=True)
    top_share = aggregated[0][1] / total * 100
    if top_share >= 50:
        return (
            f"Concentration risk: a single {_pretty_dim_name(dim_col)} ({aggregated[0][0]}) "
            f"contributes {top_share:.1f}% of {_pretty_measure_name(measure)}."
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_narrative(pivot_table: List[Dict[str, Any]]) -> List[str]:
    """
    Produce 3–5 short, factual bullet insights for the given pivot table.

    Returns an empty list when the data is empty or insufficient.
    """
    if not pivot_table or not isinstance(pivot_table, list):
        return []
    sample = next((r for r in pivot_table if isinstance(r, dict)), None)
    if not sample:
        return []

    rows = [r for r in pivot_table if isinstance(r, dict)]
    if not rows:
        return []

    time_col = _detect_time_column(sample)
    dim_col = _detect_dimension_column(sample, time_col)
    measure = _detect_measure_column(sample)
    if not measure:
        return []

    insights: List[str] = []

    total_bullet = _insight_total(rows, measure, dim_col)
    if total_bullet:
        insights.append(total_bullet)

    if dim_col:
        top_bullet = _insight_top_contributor(rows, dim_col, measure)
        if top_bullet:
            insights.append(top_bullet)

    if time_col == "Year":
        yoy = _insight_yoy_change(rows, time_col, measure)
        if yoy:
            insights.append(yoy)
        if dim_col:
            mover = _insight_biggest_mover(rows, dim_col, time_col, measure)
            if mover:
                insights.append(mover)

    if dim_col and len(insights) < 5:
        top3 = _insight_top_three_share(rows, dim_col, measure)
        if top3:
            insights.append(top3)

    # Margin / concentration only when we still have room
    if dim_col and len(insights) < 5:
        margin = _insight_margin_leader(rows, dim_col)
        if margin:
            insights.append(margin)

    if dim_col and len(insights) < 5:
        concentration = _insight_concentration_warning(rows, dim_col, measure)
        if concentration:
            insights.append(concentration)

    # Dedupe while preserving order, cap at 5
    seen = set()
    deduped: List[str] = []
    for b in insights:
        if b in seen:
            continue
        seen.add(b)
        deduped.append(b)
        if len(deduped) >= 5:
            break

    return deduped
