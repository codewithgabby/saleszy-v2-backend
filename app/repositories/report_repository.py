from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.models import Sale, SaleItem


class ReportRepository:

    def get_today_summary(
        self,
        db: Session,
        business_id,
    ):
        today = date.today()

        return (
            db.query(
                func.count(Sale.id).label("transactions"),
                func.coalesce(func.sum(Sale.grand_total), 0).label("revenue"),
                func.coalesce(func.sum(SaleItem.buying_cost * SaleItem.quantity), 0).label("cogs"),
                func.coalesce(func.sum(SaleItem.profit), 0).label("profit"),
            )
            .join(SaleItem, Sale.id == SaleItem.sale_id)
            .filter(
                Sale.business_id == business_id,
                Sale.status == "completed",
                func.date(Sale.created_at) == today,
            )
            .first()
        )