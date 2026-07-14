from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User, Sale

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/today")
async def get_today_sales(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today_start = date.today()
    
    # Query total sales for today
    total_sales = db.query(
        func.count(Sale.id).label("total_transactions"),
        func.coalesce(func.sum(Sale.grand_total), 0).label("total_revenue")
    ).filter(
        Sale.business_id == current_user.business_id,
        Sale.status == "completed",
        func.date(Sale.created_at) == today_start
    ).first()
    
    return {
        "date": today_start.isoformat(),
        "total_transactions": total_sales.total_transactions or 0,
        "total_revenue": float(total_sales.total_revenue or 0),
        "currency": "₦"
    }