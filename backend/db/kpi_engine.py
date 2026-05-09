"""
kpi_engine.py — Reads kpi.json and executes each KPI formula against PostgreSQL.

Both the dashboard endpoint and the query_builder resolve formulas from this
registry, guaranteeing formula consistency between the two interfaces.
"""
import json
from pathlib import Path
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

KPI_PATH = Path(__file__).parent.parent / "config" / "kpi.json"


def load_kpi_registry() -> list[dict]:
    with open(KPI_PATH) as f:
        return json.load(f)


def _build_where(filters: dict) -> tuple[str, dict]:
    """Convert a kpi.json filters dict to a SQL WHERE clause + bind params."""
    clauses = []
    params: dict[str, Any] = {}

    for key, value in filters.items():
        if key == "delivery_date__not_null":
            clauses.append("delivery_date IS NOT NULL")
        else:
            param_name = key
            clauses.append(f"{key} = :{param_name}")
            params[param_name] = value

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def compute_kpi(kpi: dict, db: Session) -> float | int:
    agg = kpi["aggregation"]

    if agg == "count":
        where, params = _build_where(kpi.get("filters", {}))
        sql = f"SELECT COUNT(*) FROM orders {where}"
        result = db.execute(text(sql), params).scalar()
        return int(result or 0)

    elif agg == "ratio":
        num_where, num_params = _build_where(kpi["numerator"].get("filters", {}))
        den_where, den_params = _build_where(kpi["denominator"].get("filters", {}))

        # Rename param keys to avoid collision
        num_params = {f"num_{k}": v for k, v in num_params.items()}
        den_params = {f"den_{k}": v for k, v in den_params.items()}

        num_sql = num_where.replace(":status", ":num_status")
        den_sql = den_where.replace(":status", ":den_status")

        numerator = db.execute(text(f"SELECT COUNT(*) FROM orders {num_sql}"), num_params).scalar() or 0
        denominator = db.execute(text(f"SELECT COUNT(*) FROM orders {den_sql}"), den_params).scalar() or 1

        return round(numerator / denominator * 100, 1)

    elif agg == "avg_date_diff":
        where, params = _build_where(kpi.get("filters", {}))
        sql = f"""
            SELECT AVG(delivery_date - order_date)
            FROM orders
            {where}
        """
        result = db.execute(text(sql), params).scalar()
        return round(float(result or 0), 1)

    raise ValueError(f"Unknown aggregation type: {agg}")


def compute_all_kpis(db: Session) -> list[dict]:
    registry = load_kpi_registry()
    results = []
    for kpi in registry:
        value = compute_kpi(kpi, db)
        results.append({
            "id": kpi["id"],
            "label": kpi["label"],
            "value": value,
            "format": kpi["format"],
        })
    return results
