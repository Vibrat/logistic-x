"""
tool_schemas.py — Groq tool definitions for analytics_query, forecast, and explore_data.

The metric enum is populated at runtime from kpi.json so that Groq is always
constrained to registered, validated metric IDs only.
"""
from db.kpi_engine import load_kpi_registry


def build_tool_definitions() -> list[dict]:
    registry = load_kpi_registry()
    valid_metric_ids = [k["id"] for k in registry]

    return [
        # ── 1. Explore data ────────────────────────────────────────────────────
        {
            "type": "function",
            "function": {
                "name": "explore_data",
                "description": (
                    "Look up distinct values that exist in the database for a given dimension column. "
                    "Call this BEFORE analytics_query or forecast whenever you are uncertain about the "
                    "exact value to use (e.g. the user says 'SKU X', 'my carrier', or any vague term). "
                    "Use the results to either proceed with the correct value or ask the user to pick "
                    "from the returned list. Never guess dimension values."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "column": {
                            "type": "string",
                            "enum": [
                                "sku", "product_category", "carrier", "region",
                                "warehouse", "status", "origin_city", "destination_city",
                            ],
                            "description": "The dimension column to look up values for.",
                        },
                        "search": {
                            "type": "string",
                            "description": (
                                "Optional partial text to narrow results (case-insensitive). "
                                "E.g. 'PAPER' to find all paper-related SKUs."
                            ),
                        },
                    },
                    "required": ["column"],
                },
            },
        },
        # ── 2. Analytics query ─────────────────────────────────────────────────
        {
            "type": "function",
            "function": {
                "name": "analytics_query",
                "description": (
                    "Execute an analytics query against the logistics orders dataset. "
                    "Use this for KPI calculations, aggregations, breakdowns, and trend queries. "
                    "The metric must be one of the registered KPI IDs. "
                    "Only call this once you have confirmed all dimension/filter values are exact."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "enum": valid_metric_ids,
                            "description": "The KPI metric to compute.",
                        },
                        "group_by": {
                            "type": "string",
                            "enum": [
                                "carrier", "region", "warehouse", "product_category",
                                "sku", "origin_city", "destination_city", "status",
                                "week", "month", "day",
                            ],
                            "description": "Dimension to group results by. Omit for a single aggregate value.",
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional filters to apply.",
                            "properties": {
                                "carrier":          {"type": "string"},
                                "region":           {"type": "string"},
                                "warehouse":        {"type": "string"},
                                "product_category": {"type": "string"},
                                "sku":              {"type": "string"},
                                "status":           {"type": "string", "enum": ["delivered", "delayed", "in_transit", "exception"]},
                                "date_from":        {"type": "string", "description": "ISO date YYYY-MM-DD"},
                                "date_to":          {"type": "string", "description": "ISO date YYYY-MM-DD"},
                            },
                            "additionalProperties": False,
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "description": "Sort direction for results.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return.",
                        },
                    },
                    "required": ["metric"],
                },
            },
        },
        # ── 3. Forecast ────────────────────────────────────────────────────────
        {
            "type": "function",
            "function": {
                "name": "forecast",
                "description": (
                    "Forecast future demand for a specific SKU or product category. "
                    "Use this for questions about predicted future orders, inventory planning, or demand trends. "
                    "Only call this once you have the exact SKU code or category name from explore_data or the user."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group_by": {
                            "type": "string",
                            "enum": ["sku", "product_category"],
                            "description": "Whether to forecast by individual SKU or product category.",
                        },
                        "group_value": {
                            "type": "string",
                            "description": "The specific SKU code or product category name to forecast.",
                        },
                        "horizon_months": {
                            "type": "integer",
                            "description": "Number of future months to forecast (1–12).",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["exponential_smoothing", "linear_regression", "moving_average"],
                            "description": "Forecasting method to apply.",
                        },
                    },
                    "required": ["group_by", "group_value", "horizon_months"],
                },
            },
        },
    ]
