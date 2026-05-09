"""
forecasting/engine.py — Demand forecasting using statsmodels.

Supports: exponential_smoothing, linear_regression, moving_average.
Returns historical monthly demand + forecast with confidence bounds
and an inventory recommendation.
"""
import warnings
from typing import Any
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")


def _fetch_monthly_demand(group_by: str, group_value: str, db: Session) -> pd.DataFrame:
    if group_by == "sku":
        sql = """
            SELECT DATE_TRUNC('month', order_date) AS month, SUM(quantity) AS quantity
            FROM orders
            WHERE sku = :value
            GROUP BY month
            ORDER BY month
        """
    elif group_by == "product_category":
        sql = """
            SELECT DATE_TRUNC('month', order_date) AS month, SUM(quantity) AS quantity
            FROM orders
            WHERE product_category = :value
            GROUP BY month
            ORDER BY month
        """
    else:
        raise ValueError(f"Invalid group_by for forecast: '{group_by}'. Use 'sku' or 'product_category'.")

    rows = db.execute(text(sql), {"value": group_value}).fetchall()
    if not rows:
        raise ValueError(f"No data found for {group_by}='{group_value}'")

    df = pd.DataFrame(rows, columns=["month", "quantity"])
    df["month"] = pd.to_datetime(df["month"])
    df = df.set_index("month").sort_index()
    return df


def _exponential_smoothing(series: pd.Series, horizon: int) -> tuple[list[float], list[float], list[float], str]:
    if len(series) < 3:
        return _moving_average(series, horizon)

    model = ExponentialSmoothing(series, trend="add", initialization_method="estimated")
    fit = model.fit(optimized=True)
    forecast = fit.forecast(horizon)
    std = np.std(series.values)
    lower = (forecast - 1.96 * std).clip(min=0).tolist()
    upper = (forecast + 1.96 * std).tolist()
    return forecast.tolist(), lower, upper, "Holt-Winters Exponential Smoothing (additive trend)"


def _linear_regression(series: pd.Series, horizon: int) -> tuple[list[float], list[float], list[float], str]:
    x = np.arange(len(series)).reshape(-1, 1)
    y = series.values

    # Use numpy polyfit to avoid sklearn dependency
    coeffs = np.polyfit(x.flatten(), y, 1)
    future_x = np.arange(len(series), len(series) + horizon)
    forecast = np.polyval(coeffs, future_x).clip(min=0).tolist()
    residuals = y - np.polyval(coeffs, x.flatten())
    std = np.std(residuals)
    lower = [max(0, v - 1.96 * std) for v in forecast]
    upper = [v + 1.96 * std for v in forecast]
    return forecast, lower, upper, "Linear Regression (OLS)"


def _moving_average(series: pd.Series, horizon: int, window: int = 3) -> tuple[list[float], list[float], list[float], str]:
    window = min(window, len(series))
    avg = float(series.tail(window).mean())
    std = float(series.tail(window).std() or 0)
    forecast = [round(avg, 1)] * horizon
    lower = [max(0, avg - 1.96 * std)] * horizon
    upper = [avg + 1.96 * std] * horizon
    return forecast, lower, upper, f"Moving Average (window={window})"


def run_forecast(
    group_by: str,
    group_value: str,
    horizon_months: int,
    method: str,
    db: Session,
) -> dict[str, Any]:
    df = _fetch_monthly_demand(group_by, group_value, db)
    series = df["quantity"].astype(float)

    horizon_months = max(1, min(horizon_months, 12))

    dispatch = {
        "exponential_smoothing": _exponential_smoothing,
        "linear_regression": _linear_regression,
        "moving_average": _moving_average,
    }
    forecast_fn = dispatch.get(method, _exponential_smoothing)
    forecast_values, lower, upper, methodology = forecast_fn(series, horizon_months)

    # Build future month labels
    last_month = series.index[-1]
    future_months = pd.date_range(start=last_month + pd.DateOffset(months=1), periods=horizon_months, freq="MS")

    historical = [
        {"month": idx.strftime("%Y-%m"), "quantity": int(qty)}
        for idx, qty in series.items()
    ]
    forecast_out = [
        {
            "month": m.strftime("%Y-%m"),
            "quantity": round(forecast_values[i], 1),
            "lower": round(lower[i], 1),
            "upper": round(upper[i], 1),
        }
        for i, m in enumerate(future_months)
    ]

    avg_forecast = round(float(np.mean(forecast_values)), 1)
    buffer = round(avg_forecast * 0.25, 1)
    inventory_recommendation = (
        f"Plan for approximately {avg_forecast} units/month. "
        f"Recommended buffer stock: {buffer} units (25% safety margin)."
    )

    return {
        "historical": historical,
        "forecast": forecast_out,
        "inventory_recommendation": inventory_recommendation,
        "methodology": methodology,
    }
