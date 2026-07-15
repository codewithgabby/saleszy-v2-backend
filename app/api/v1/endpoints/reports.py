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

@router.get("/top-products")
async def get_top_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    from app.models import SaleItem, Product, SellingUnit
    
    today_start = date.today()
    
    results = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            SellingUnit.name.label("selling_unit_name"),
            func.sum(SaleItem.quantity).label("quantity_sold"),
            func.sum(SaleItem.total_price).label("total_revenue")
        )
        .join(Sale, SaleItem.sale_id == Sale.id)
        .join(Product, SaleItem.product_id == Product.id)
        .outerjoin(SellingUnit, SaleItem.selling_unit_id == SellingUnit.id)
        .filter(
            Sale.business_id == current_user.business_id,
            Sale.status == "completed",
            func.date(Sale.created_at) == today_start
        )
        .group_by(Product.id, Product.name, SellingUnit.name)
        .order_by(func.sum(SaleItem.total_price).desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "product_id": str(r.product_id),
            "product_name": r.product_name,
            "selling_unit_name": r.selling_unit_name or "Unit",
            "quantity_sold": float(r.quantity_sold),
            "total_revenue": float(r.total_revenue)
        }
        for r in results
    ]    