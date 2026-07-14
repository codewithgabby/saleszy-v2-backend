from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models import Sale, SaleItem
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timezone
import uuid

class SalesRepository:
    def create_sale(
        self, 
        db: Session, 
        business_id: uuid.UUID, 
        cashier_id: uuid.UUID,
        customer_id: uuid.UUID | None,
        subtotal: Decimal,
        tax: Decimal,
        discount: Decimal,
        grand_total: Decimal,
        payment_method: str,
        receipt_number: str,
        cash_received: Decimal | None,
        change_given: Decimal | None,
        items_data: list
    ) -> Sale:
        # 1. Create the Sale record
        sale = Sale(
            business_id=business_id,
            cashier_id=cashier_id,
            customer_id=customer_id,
            subtotal=subtotal,
            tax=tax,
            discount=discount,
            grand_total=grand_total,
            payment_method=payment_method,
            receipt_number=receipt_number,
            cash_received=cash_received,
            change_given=change_given
        )
        db.add(sale)
        db.flush()

        # 2. Create SaleItems (inventory handled by InventoryService)
        for item in items_data:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item["product_id"],
                selling_unit_id=item["selling_unit_id"],
                selling_unit_name=item["selling_unit_name"],
                quantity=item["quantity"],
                base_unit_quantity_used=item["base_unit_quantity_used"],
                unit_price=item["unit_price"],
                total_price=item["total_price"]
            )
            db.add(sale_item)

        db.flush()
        return sale

    def get_sale_by_id(self, db: Session, sale_id: uuid.UUID) -> Optional[Sale]:
        return (
            db.query(Sale)
            .options(joinedload(Sale.items), joinedload(Sale.customer))
            .filter(Sale.id == sale_id)
            .first()
        )

    def get_sales_list(
        self, 
        db: Session, 
        business_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 50,
        status: str | None = None,
        payment_method: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> List[Sale]:
        query = db.query(Sale).filter(Sale.business_id == business_id)
        
        if status:
            query = query.filter(Sale.status == status)
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        if start_date:
            query = query.filter(Sale.created_at >= start_date)
        if end_date:
            query = query.filter(Sale.created_at <= end_date)
        
        return (
            query
            .options(joinedload(Sale.items), joinedload(Sale.customer))
            .order_by(desc(Sale.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent_sales(self, db: Session, business_id: uuid.UUID, limit: int = 20) -> List[Sale]:
        return (
            db.query(Sale)
            .options(joinedload(Sale.items))
            .filter(Sale.business_id == business_id)
            .order_by(desc(Sale.created_at))
            .limit(limit)
            .all()
        )

    def get_sales_count(self, db: Session, business_id: uuid.UUID) -> int:
        return db.query(Sale).filter(Sale.business_id == business_id).count()

    def void_sale(self, db: Session, sale_id: uuid.UUID, void_reason: str) -> Optional[Sale]:
        """Update sale status only. Inventory restoration handled by InventoryService."""
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale or sale.status != "completed":
            return None
        
        sale.status = "voided"
        sale.void_reason = void_reason
        sale.voided_at = datetime.now(timezone.utc)
        
        db.flush()
        return sale

    def get_payment_summary(self, db: Session, business_id: uuid.UUID, date: datetime | None = None) -> dict:
        if not date:
            date = datetime.now(timezone.utc)
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        sales = (
            db.query(Sale)
            .filter(
                Sale.business_id == business_id,
                Sale.status == "completed",
                Sale.created_at >= start_of_day,
                Sale.created_at <= end_of_day
            )
            .all()
        )
        
        summary = {
            "total_sales": len(sales),
            "total_revenue": sum(float(s.grand_total) for s in sales),
            "by_payment_method": {}
        }
        
        for sale in sales:
            method = sale.payment_method
            if method not in summary["by_payment_method"]:
                summary["by_payment_method"][method] = {
                    "count": 0,
                    "total": 0.0
                }
            summary["by_payment_method"][method]["count"] += 1
            summary["by_payment_method"][method]["total"] += float(sale.grand_total)
        
        return summary