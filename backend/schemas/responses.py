from typing import Any, Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class KPIResponse(BaseModel):
    id: str
    label: str
    value: float | int
    format: str


class ChartDataset(BaseModel):
    label: str
    data: list[Any]
    backgroundColor: str | None = None
    borderColor: str | None = None


class ChartData(BaseModel):
    labels: list[str]
    datasets: list[dict]


class ExplanationDetail(BaseModel):
    metric: str
    group_by: str | None = None
    filters_applied: dict = {}
    query_plan: str | None = None


class AskResponse(BaseModel):
    answer: str
    needs_clarification: bool = False
    chart_type: str | None = None
    chart_data: dict | None = None
    explanation: ExplanationDetail | None = None
    filters_used: dict = {}
    raw_data: list[dict] = []
    inventory_recommendation: str | None = None


class ForecastRequest(BaseModel):
    group_by: str
    group_value: str
    horizon_months: int = 3
    method: str = "exponential_smoothing"


class ForecastDataPoint(BaseModel):
    month: str
    quantity: float
    lower: float | None = None
    upper: float | None = None


class ForecastResponse(BaseModel):
    historical: list[ForecastDataPoint]
    forecast: list[ForecastDataPoint]
    inventory_recommendation: str
    methodology: str
