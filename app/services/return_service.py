from sqlalchemy.orm import Session
from app.repositories.return_repository import ReturnRepository
from app.repositories.sales_repository import SalesRepository
from app.services.inventory_service import InventoryService, StockMovementType
from app.services.shift_service import ShiftService
from app.models import SaleItem
from decimal import Decimal
from datetime import datetime
from enum import Enum
import uuid


class ReturnReason(str, Enum):
    CUSTOMER_CHANGED_MIND = "CUSTOMER_CHANGED_MIND"
    WRONG_ITEM = "WRONG_ITEM"
    DAMAGED_ITEM = "DAMAGED_ITEM"
    EXPIRED_ITEM = "EXPIRED_ITEM"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    CASHIER_ERROR = "CASHIER_ERROR"
    OTHER = "OTHER"


class RefundMethod(str, Enum):
    CASH = "CASH"
    TRANSFER = "TRANSFER"
    POS = "POS"


class ReturnService:
    
    def __init__(self):
        self.repo = ReturnRepository()
        self.sale_repo = SalesRepository()
        self.inventory_service = InventoryService()
        self.shift_service = ShiftService()
    
    def _generate_return_number(self, business_id: uuid.UUID) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"RTN-{timestamp}"
    
    def process_return(
        self,
        db: Session,
        business_id: uuid.UUID,
        sale_id: uuid.UUID,
        shift_id: uuid.UUID,
        user_id: uuid.UUID,
        return_type: str,
        reason_code: str,
        refund_method: str,
        items: list,
        notes: str = None,
        customer_id: uuid.UUID = None,
    ):
        # 1. Validate sale exists and is completed
        sale = self.sale_repo.get_sale_by_id(db, sale_id)
        if not sale:
            raise ValueError("Sale not found")
        if sale.status not in ["completed", "partially_returned"]:
            raise ValueError("Can only return completed sales")
        if sale.business_id != business_id:
            raise ValueError("Sale does not belong to this business")
        
        # 2. Get current returned quantities
        returned_map = self.repo.get_sale_returned_quantities(db, sale_id)
        
        # 3. Validate each return item
        subtotal = Decimal('0.00')
        processed_items = []
        
        for item in items:
            sale_item = None
            for si in sale.items:
                if str(si.id) == item["sale_item_id"]:
                    sale_item = si
                    break
            
            if not sale_item:
                raise ValueError(f"Sale item {item['sale_item_id']} not found in this sale")
            
            # Check remaining returnable quantity
            already_returned = Decimal(str(returned_map.get(item["sale_item_id"], 0)))
            returnable = sale_item.quantity - already_returned
            if item["quantity"] > returnable:
                raise ValueError(f"Cannot return {item['quantity']}. Only {returnable} remaining for this item")
            
            refund_amount = sale_item.unit_price * item["quantity"]
            subtotal += refund_amount
            
            processed_items.append({
                "sale_item_id": sale_item.id,
                "product_id": sale_item.product_id,
                "selling_unit_id": sale_item.selling_unit_id,
                "selling_unit_name": sale_item.selling_unit_name,
                "quantity": item["quantity"],
                "base_unit_quantity_used": float(sale_item.base_unit_quantity_used),
                "refund_amount": refund_amount,
            })
        
        # 4. Calculate totals
        tax = subtotal * (sale.tax / sale.subtotal) if sale.subtotal > 0 else Decimal('0.00')
        total_refund = subtotal + tax
        
        # 5. Generate return number
        return_number = self._generate_return_number(business_id)
        
        # 6. Create return
        ret = self.repo.create_return(db, {
            "business_id": business_id,
            "sale_id": sale_id,
            "shift_id": shift_id,
            "customer_id": customer_id or sale.customer_id,
            "processed_by_user_id": user_id,
            "return_number": return_number,
            "return_type": return_type,
            "reason_code": reason_code,
            "refund_method": refund_method,
            "notes": notes,
            "subtotal": subtotal,
            "tax": tax,
            "total_refund": total_refund,
        }, processed_items)
        
        # 7. Restore inventory
        for item in processed_items:
            restore_qty = Decimal(str(item["base_unit_quantity_used"])) * item["quantity"]
            self.inventory_service.adjust_stock(
                db, business_id, item["product_id"], user_id,
                restore_qty,
                StockMovementType.RETURN,
                reference_type="return",
                reference_id=ret.id,
                notes=f"Return {return_number}: {item['selling_unit_name']} x {item['quantity']}"
            )
        
        # 8. Update sale status
        total_returned = sum(
            float(si.returned_quantity) for si in db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
        )
        total_original = sum(float(si.quantity) for si in sale.items)
        if total_returned >= total_original:
            sale.status = "fully_returned"
        
        # 9. Update shift totals
        shift = self.shift_service.get_current_shift(db, user_id) if not shift_id else None
        if shift:
            self.shift_service.repo.update_shift_totals(db, shift.id, -total_refund)
        
        return ret
    
    def get_return(self, db: Session, return_id: uuid.UUID):
        ret = self.repo.get_return_by_id(db, return_id)
        if not ret:
            raise ValueError("Return not found")
        return ret
    
    def get_returns(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 20):
        return self.repo.get_returns(db, business_id, skip, limit)
    
    def cancel_return(self, db: Session, return_id: uuid.UUID, user_id: uuid.UUID):
        ret = self.repo.get_return_by_id(db, return_id)
        if not ret:
            raise ValueError("Return not found")
        if ret.status != "COMPLETED":
            raise ValueError("Only completed returns can be cancelled")
        
        # Reverse inventory
        for item in ret.items:
            deduct_qty = Decimal(str(item.base_unit_quantity_used)) * item.quantity
            self.inventory_service.adjust_stock(
                db, ret.business_id, item.product_id, user_id,
                -deduct_qty,
                StockMovementType.RETURN,
                reference_type="return_cancel",
                reference_id=ret.id,
                notes=f"Cancelled return {ret.return_number}"
            )
        
        return self.repo.cancel_return(db, ret)