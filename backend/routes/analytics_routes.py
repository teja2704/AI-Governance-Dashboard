from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.db import get_db

from backend.services.analytics_service import (
    get_analytics,
    get_model_usage,
    get_dashboard_kpis
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/")
def analytics(
    db: Session = Depends(get_db)
):
    return get_analytics(db)


@router.get("/model-usage")
def model_usage(
    db: Session = Depends(get_db)
):
    return get_model_usage(db)


@router.get("/dashboard-kpis")
def dashboard_kpis(
    db: Session = Depends(get_db)
):
    return get_dashboard_kpis(db)