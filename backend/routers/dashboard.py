from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.connection import get_db
from db.kpi_engine import compute_all_kpis
from db.query_builder import execute_analytics_query
from schemas.responses import KPIResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=list[KPIResponse])
def get_kpis(db: Session = Depends(get_db)):
    """Return all KPIs defined in kpi.json, computed against the live database."""
    return compute_all_kpis(db)


@router.get("/charts")
def get_charts(db: Session = Depends(get_db)):
    """Return datasets for the three default dashboard charts."""

    # Chart 1: Order volume by month
    volume = execute_analytics_query(
        metric="total_orders",
        group_by="month",
        filters={},
        sort="asc",
        limit=None,
        db=db,
    )

    # Chart 2: Delivery status breakdown by region
    status_by_region = execute_analytics_query(
        metric="on_time_delivery_rate",
        group_by="region",
        filters={},
        sort="desc",
        limit=None,
        db=db,
    )

    # Chart 3: Delay rate by carrier
    delay_by_carrier = execute_analytics_query(
        metric="delayed_orders",
        group_by="carrier",
        filters={},
        sort="desc",
        limit=10,
        db=db,
    )

    return {
        "order_volume_by_month": volume["rows"],
        "on_time_rate_by_region": status_by_region["rows"],
        "delayed_orders_by_carrier": delay_by_carrier["rows"],
    }
