from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.connection import get_db
from forecasting.engine import run_forecast
from schemas.responses import ForecastRequest, ForecastResponse

router = APIRouter(prefix="/api", tags=["forecast"])

ALLOWED_METHODS = {"exponential_smoothing", "linear_regression", "moving_average"}
ALLOWED_GROUP_BY = {"sku", "product_category"}


@router.post("/forecast", response_model=ForecastResponse)
def forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    """
    Direct forecasting endpoint. Also called internally by the AI orchestrator.
    """
    if request.group_by not in ALLOWED_GROUP_BY:
        raise HTTPException(status_code=422, detail=f"group_by must be one of {ALLOWED_GROUP_BY}")

    if request.method not in ALLOWED_METHODS:
        raise HTTPException(status_code=422, detail=f"method must be one of {ALLOWED_METHODS}")

    if not 1 <= request.horizon_months <= 12:
        raise HTTPException(status_code=422, detail="horizon_months must be between 1 and 12")

    try:
        result = run_forecast(
            group_by=request.group_by,
            group_value=request.group_value,
            horizon_months=request.horizon_months,
            method=request.method,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return result
