"""
query_builder.py — Translates analytics_query tool parameters into safe,
parameterized SQL by resolving the metric formula from kpi.json.

AI (Groq) never generates SQL. It only provides:
  - metric: a valid kpi.json ID
  - group_by: a dimension from the allowlist
  - filters: key/value pairs from the allowlist
  - sort, limit

This module converts those into a parameterized query against PostgreSQL.
"""
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from db.kpi_engine import load_kpi_registry

# Allowlists to prevent injection of arbitrary column names
ALLOWED_GROUP_BY = {
    "carrier", "region", "warehouse", "product_category",
    "sku", "origin_city", "destination_city", "status",
    "week", "month", "day",
}

ALLOWED_FILTER_KEYS = {
    "carrier", "region", "warehouse", "product_category",
    "sku", "status",
}

DATE_FILTER_KEYS = {"date_from", "date_to"}


def _resolve_metric_expression(metric_id: str) -> str:
    """
    Return the SQL expression for a given kpi.json metric ID.
    Raises ValueError if the metric ID is not registered.
    """
    registry = load_kpi_registry()
    kpi = next((k for k in registry if k["id"] == metric_id), None)
    if not kpi:
        raise ValueError(f"Unknown metric: '{metric_id}'. Must be one of: {[k['id'] for k in registry]}")

    agg = kpi["aggregation"]

    if agg == "count":
        filters = kpi.get("filters", {})
        if filters.get("status"):
            return f"COUNT(*) FILTER (WHERE status = '{filters['status']}')"
        return "COUNT(*)"

    elif agg == "ratio":
        num_status = kpi["numerator"]["filters"].get("status")
        if num_status:
            return f"ROUND(COUNT(*) FILTER (WHERE status = '{num_status}')::numeric / NULLIF(COUNT(*), 0) * 100, 1)"
        return "ROUND(COUNT(*)::numeric / NULLIF(COUNT(*), 0) * 100, 1)"

    elif agg == "avg_date_diff":
        return "ROUND(AVG(delivery_date - order_date)::numeric, 1)"

    raise ValueError(f"Unsupported aggregation: {agg}")


def _resolve_group_by_expression(group_by: str) -> str:
    """Map group_by value to a SQL expression."""
    if group_by not in ALLOWED_GROUP_BY:
        raise ValueError(f"Invalid group_by: '{group_by}'. Allowed: {sorted(ALLOWED_GROUP_BY)}")

    time_expressions = {
        "week":  "DATE_TRUNC('week', order_date)",
        "month": "DATE_TRUNC('month', order_date)",
        "day":   "order_date",
    }
    return time_expressions.get(group_by, group_by)


def execute_analytics_query(
    metric: str,
    group_by: str | None,
    filters: dict,
    sort: str | None,
    limit: int | None,
    db: Session,
) -> dict[str, Any]:
    """
    Build and execute a parameterized analytics query.
    Returns { columns, rows, query_plan }.
    """
    metric_expr = _resolve_metric_expression(metric)

    where_clauses = []
    params: dict[str, Any] = {}

    # Validate and apply dimension filters
    for key, value in filters.items():
        if key in ALLOWED_FILTER_KEYS:
            param_name = f"filter_{key}"
            where_clauses.append(f"{key} = :{param_name}")
            params[param_name] = value
        elif key == "date_from":
            where_clauses.append("order_date >= :date_from")
            params["date_from"] = value
        elif key == "date_to":
            where_clauses.append("order_date <= :date_to")
            params["date_to"] = value

    # kpi.json built-in filters (e.g., delivery_date IS NOT NULL for avg)
    registry = load_kpi_registry()
    kpi_def = next((k for k in registry if k["id"] == metric), None)
    if kpi_def and kpi_def.get("filters", {}).get("delivery_date__not_null"):
        where_clauses.append("delivery_date IS NOT NULL")

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    if group_by:
        group_expr = _resolve_group_by_expression(group_by)
        select = f"SELECT {group_expr} AS dimension, {metric_expr} AS value"
        group_clause = f"GROUP BY {group_expr}"
        order_clause = f"ORDER BY value {'DESC' if sort == 'desc' else 'ASC'}"
        limit_clause = f"LIMIT {int(limit)}" if limit else ""

        sql = f"{select} FROM orders {where} {group_clause} {order_clause} {limit_clause}"
        columns = ["dimension", "value"]
    else:
        sql = f"SELECT {metric_expr} AS value FROM orders {where}"
        columns = ["value"]

    rows = db.execute(text(sql), params).fetchall()
    data = [dict(zip(columns, row)) for row in rows]

    return {
        "columns": columns,
        "rows": data,
        "query_plan": {
            "metric": metric,
            "metric_expression": metric_expr,
            "group_by": group_by,
            "filters": filters,
            "sort": sort,
            "limit": limit,
        },
    }
