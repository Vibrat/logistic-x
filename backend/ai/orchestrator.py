"""
orchestrator.py — Groq-powered AI orchestration layer.

Responsibilities:
1. Build tool definitions with kpi.json metric IDs injected as enum constraints.
2. Send the user question to Groq with tool definitions.
3. Parse the tool call response and dispatch to the correct handler.
4. Return a unified response envelope.

AI never generates SQL. It only returns structured tool call parameters.
"""
import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq
from sqlalchemy.orm import Session

from ai.tool_schemas import build_tool_definitions
from db.query_builder import execute_analytics_query
from forecasting.engine import run_forecast

load_dotenv()

"""
orchestrator.py — Groq-powered AI orchestration layer.

Responsibilities:
1. Build tool definitions with kpi.json metric IDs injected as enum constraints.
2. Run an agentic loop (up to MAX_STEPS rounds) where the AI can:
   a. Call explore_data to discover real dimension values from the DB.
   b. Ask the user a clarifying question (no tool call).
   c. Call analytics_query or forecast to produce the final answer.
3. Return a unified response envelope.

AI never generates SQL. It only returns structured tool call parameters.
"""
import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq
from sqlalchemy.orm import Session

from ai.tool_schemas import build_tool_definitions
from db.explorer import explore_column
from db.query_builder import execute_analytics_query
from forecasting.engine import run_forecast

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
MAX_STEPS = 5  # max explore_data calls before forcing a clarification

SYSTEM_PROMPT = """You are an analytics assistant for a logistics company.

You have THREE tools available:

1. explore_data — Query the database for real dimension values (SKUs, carriers, regions, etc.).
   Use this FIRST whenever the user mentions a vague or partial value you are unsure about.
   After seeing the results, either proceed with the correct value or show the options to the user.

2. analytics_query — Compute KPI metrics, aggregations, breakdowns, and trends.
   Only call this once all filter/dimension values are confirmed real values from the database.

3. forecast — Predict future demand for a specific SKU or product category.
   Only call this once you have the exact SKU code or category name.

Decision flow:
- User mentions something vague (e.g. "SKU X", "the paper category", "FedEx deliveries")?
  → Call explore_data with the relevant column and a search hint.
- explore_data returns multiple matches?
  → Ask the user to pick one from the list (respond with text, no tool call).
- explore_data returns exactly one match, or the user provided an exact value?
  → Call analytics_query or forecast directly.
- Question is ambiguous about what metric or dimension to use?
  → Ask ONE concise clarifying question (respond with text, no tool call).

Rules:
- Never guess or invent dimension values. Always verify with explore_data first.
- Never call analytics_query or forecast with unverified values.
- For time-based questions, use group_by: "week" or "month".
- For comparison questions, include sort: "desc" and a reasonable limit.
- Keep clarifying questions short and specific.
"""


def ask(question: str, history: list[dict], db: Session) -> dict[str, Any]:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    tools = build_tool_definitions()

    # Build initial message list: system + prior turns + new user message
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    for _step in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0,
        )

        choice = response.choices[0]
        message = choice.message

        # ── No tool call: AI is responding with text (clarification or final prose) ──
        if not message.tool_calls:
            text = message.content or "Could you please clarify your question?"
            return {
                "answer": text,
                "needs_clarification": True,
                "chart_type": None,
                "chart_data": None,
                "explanation": None,
                "filters_used": {},
                "raw_data": [],
            }

        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # ── explore_data: run query, inject result, loop again ─────────────────
        if tool_name == "explore_data":
            try:
                values = explore_column(
                    column=tool_args["column"],
                    search=tool_args.get("search"),
                    db=db,
                )
                tool_result = {
                    "column": tool_args["column"],
                    "values": values,
                    "count": len(values),
                }
            except ValueError as e:
                tool_result = {"error": str(e), "values": []}

            # Append the assistant's tool call + the tool result to the message thread
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": tool_call.function.arguments,
                    },
                }],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result),
            })
            continue  # back to top of loop — AI sees the results and decides next step

        # ── analytics_query: run and return final response ─────────────────────
        elif tool_name == "analytics_query":
            return _handle_analytics_query(question, tool_args, db)

        # ── forecast: run and return final response ────────────────────────────
        elif tool_name == "forecast":
            return _handle_forecast(question, tool_args, db)

        # ── unknown tool ───────────────────────────────────────────────────────
        else:
            return {
                "answer": f"Unknown tool requested: {tool_name}",
                "needs_clarification": False,
                "chart_type": None,
                "chart_data": None,
                "explanation": None,
                "filters_used": {},
                "raw_data": [],
            }

    # Loop exhausted without a final answer — ask the user
    return {
        "answer": "I wasn't able to resolve your question automatically. Could you provide more specific details?",
        "needs_clarification": True,
        "chart_type": None,
        "chart_data": None,
        "explanation": None,
        "filters_used": {},
        "raw_data": [],
    }


def _handle_analytics_query(question: str, args: dict, db: Session) -> dict[str, Any]:
    metric = args["metric"]
    group_by = args.get("group_by")
    filters = args.get("filters", {})
    sort = args.get("sort", "desc")
    limit = args.get("limit", 10)

    result = execute_analytics_query(
        metric=metric,
        group_by=group_by,
        filters=filters,
        sort=sort,
        limit=limit,
        db=db,
    )

    rows = result["rows"]
    chart_type, chart_data = _build_chart(metric, group_by, rows)

    # Generate natural language answer
    answer = _summarise_analytics(metric, group_by, rows, filters)

    return {
        "answer": answer,
        "needs_clarification": False,
        "chart_type": chart_type,
        "chart_data": chart_data,
        "explanation": {
            "metric": result["query_plan"]["metric"],
            "group_by": group_by,
            "filters_applied": filters,
            "query_plan": result["query_plan"]["metric_expression"],
        },
        "filters_used": filters,
        "raw_data": rows,
    }


def _handle_forecast(question: str, args: dict, db: Session) -> dict[str, Any]:
    try:
        result = run_forecast(
            group_by=args["group_by"],
            group_value=args["group_value"],
            horizon_months=args.get("horizon_months", 3),
            method=args.get("method", "exponential_smoothing"),
            db=db,
        )
    except ValueError as e:
        return {
            "answer": str(e),
            "needs_clarification": False,
            "chart_type": None,
            "chart_data": None,
            "explanation": None,
            "filters_used": {"group_value": args.get("group_value", "")},
            "raw_data": [],
        }

    historical_labels = [r["month"] for r in result["historical"]]
    historical_values = [r["quantity"] for r in result["historical"]]
    forecast_labels = [r["month"] for r in result["forecast"]]
    forecast_values = [r["quantity"] for r in result["forecast"]]

    # Bridge: repeat the last historical value as the first point of the forecast
    # dataset so the two lines connect visually on the chart.
    last_historical = historical_values[-1] if historical_values else None
    forecast_data_with_bridge = (
        [None] * (len(historical_labels) - 1)
        + [last_historical]
        + forecast_values
    )

    chart_data = {
        "labels": historical_labels + forecast_labels,
        "datasets": [
            {
                "label": "Historical Demand",
                "data": historical_values + [None] * len(forecast_labels),
                "borderColor": "#3b82f6",
                "backgroundColor": "rgba(59,130,246,0.1)",
            },
            {
                "label": "Forecast",
                "data": forecast_data_with_bridge,
                "borderColor": "#f59e0b",
                "backgroundColor": "rgba(245,158,11,0.1)",
                "borderDash": [5, 5],
            },
        ],
    }

    answer = (
        f"Demand forecast for {args['group_value']} over the next "
        f"{args.get('horizon_months', 3)} months using {result['methodology']}. "
        f"{result['inventory_recommendation']}"
    )

    return {
        "answer": answer,
        "needs_clarification": False,
        "chart_type": "line",
        "chart_data": chart_data,
        "explanation": {
            "metric": "demand_quantity",
            "group_by": args["group_by"],
            "filters_applied": {"group_value": args["group_value"]},
            "query_plan": result["methodology"],
        },
        "filters_used": {"group_value": args["group_value"]},
        "raw_data": result["historical"] + result["forecast"],
        "inventory_recommendation": result["inventory_recommendation"],
    }


def _build_chart(metric: str, group_by: str | None, rows: list[dict]) -> tuple[str | None, dict | None]:
    if not group_by or not rows:
        return None, None

    time_groups = {"week", "month", "day"}
    chart_type = "line" if group_by in time_groups else "bar"

    # Normalise dimension values to strings for labels
    labels = [str(r.get("dimension", "")) for r in rows]
    values = [float(r.get("value", 0) or 0) for r in rows]

    return chart_type, {
        "labels": labels,
        "datasets": [
            {
                "label": metric.replace("_", " ").title(),
                "data": values,
                "backgroundColor": "rgba(59,130,246,0.6)",
                "borderColor": "#3b82f6",
            }
        ],
    }


def _summarise_analytics(metric: str, group_by: str | None, rows: list[dict], filters: dict) -> str:
    if not rows:
        return "No data found for the given filters."

    metric_label = metric.replace("_", " ").title()

    if not group_by:
        value = rows[0].get("value", "N/A")
        return f"{metric_label}: {value}"

    top = rows[0]
    dim = top.get("dimension", "")
    val = top.get("value", "")
    filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items()) if filters else "no additional filters"
    return (
        f"Top result for {metric_label} by {group_by}: "
        f"{dim} with {val} ({filter_desc})."
    )
