from sqlalchemy.orm import Session
from app.models import Return, ReturnItem, SaleItem
from typing import Optional, List
from decimal import Decimal
import uuid
from datetime import datetime


class ReturnRepository:
    
    def create_return(self, db: Session, data: dict, items_data: list) -> Return:
        ret = Return(
            business_id=data["business_id"],
            sale_id=data["sale_id"],
            shift_id=data["shift_id"],
            customer_id=data.get("customer_id"),
            processed_by_user_id=data["processed_by_user_id"],
            return_number=data["return_number"],
            return_type=data["return_type"],
            reason_code=data["reason_code"],
            refund_method=data["refund_method"],
            notes=data.get("notes"),
            subtotal=data["subtotal"],
            tax=data["tax"],
            total_refund=data["total_refund"],
        )
        db.add(ret)
        db.flush()
        
        for item in items_data:
            ri = ReturnItem(
                return_id=ret.id,
                sale_item_id=item["sale_item_id"],
                product_id=item["product_id"],
                selling_unit_id=item.get("selling_unit_id"),
                selling_unit_name=item.get("selling_unit_name"),
                quantity=item["quantity"],
                base_unit_quantity_used=item["base_unit_quantity_used"],
                refund_amount=item["refund_amount"],
            )
            db.add(ri)
            
            # Update sale_item returned_quantity
            sale_item = db.query(SaleItem).filter(SaleItem.id == item["sale_item_id"]).first()
            if sale_item:
                sale_item.returned_quantity += item["quantity"]
        
        db.flush()
        return ret
    
    def get_return_by_id(self, db: Session, return_id: uuid.UUID) -> Optional[Return]:
        return db.query(Return).filter(Return.id == return_id).first()
    
    def get_returns(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 20) -> List[Return]:
        return db.query(Return).filter(Return.business_id == business_id)\
            .order_by(Return.created_at.desc()).offset(skip).limit(limit).all()
    
    def cancel_return(self, db: Session, ret: Return) -> Return:
        ret.status = "CANCELLED"
        db.flush()
        return ret
    
    def get_sale_returned_quantities(self, db: Session, sale_id: uuid.UUID) -> dict:
        """Get total returned quantity per sale_item for validation."""
        items = db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
        return {str(item.id): float(item.returned_quantity or 0) for item in items}