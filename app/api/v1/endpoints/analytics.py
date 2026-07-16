from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.analytics_service import AnalyticsService
from app.core.response import api_response

router = APIRouter(prefix="/analytics", tags=["Analytics"])
service = AnalyticsService()

# TODO: Restrict analytics to Owner and Manager roles


def _validate_dates(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date")


@router.get("/dashboard", summary="Dashboard analytics", description="Returns KPIs for the selected period")
async def get_dashboard(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _validate_dates(start_date, end_date)
    data = service.get_dashboard(db, current_user.business_id, start_date, end_date)
    return api_response(data=data, message="Dashboard data")


@router.get("/top-products", summary="Top selling products", description="Returns top products by revenue")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _validate_dates(start_date, end_date)
    data = service.get_top_products(db, current_user.business_id, limit, start_date, end_date)
    return api_response(data=data, message="Top products")


@router.get("/inventory", summary="Inventory summary", description="Returns inventory value and counts")
async def get_inventory_value(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = service.get_inventory_value(db, current_user.business_id)
    return api_response(data=data, message="Inventory value")


@router.get("/financial", summary="Financial summary", description="Returns revenue, tax, discounts, and net")
async def get_financial(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _validate_dates(start_date, end_date)
    data = service.get_financial(db, current_user.business_id, start_date, end_date)
    return api_response(data=data, message="Financial data")