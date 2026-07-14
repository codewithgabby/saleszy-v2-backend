from sqlalchemy.orm import Session
from app.repositories.inventory_repository import InventoryRepository
from app.models import Inventory, StockMovement
from decimal import Decimal
from enum import Enum
from typing import Optional
import uuid


class StockMovementType(str, Enum):
    SALE = "SALE"
    RESTOCK = "RESTOCK"
    VOID = "VOID"
    DAMAGE = "DAMAGE"
    RETURN = "RETURN"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
    INITIAL_STOCK = "INITIAL_STOCK"


class InventoryService:
    
    def __init__(self):
        self.repo = InventoryRepository()
    
    def adjust_stock(
        self,
        db: Session,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        user_id: uuid.UUID,
        quantity: Decimal,
        movement_type: StockMovementType,
        reference_type: Optional[str] = None,
        reference_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
        with_lock: bool = False
    ) -> Inventory:
        """
        Centralized inventory adjustment.
        ALL inventory changes must go through this method.
        Creates a stock movement ledger entry for every change.
        """
        inventory = self.repo.get_by_product_id(db, product_id, with_lock=with_lock)
        
        if not inventory:
            raise ValueError(f"Inventory not found for product {product_id}")
        
        new_quantity = inventory.available_quantity + quantity
        
        if new_quantity < 0:
            raise ValueError(
                f"Insufficient stock. Available: {inventory.available_quantity}, Requested: {abs(quantity)}"
            )
        
        inventory.available_quantity = new_quantity
        
        movement = StockMovement(
            business_id=business_id,
            product_id=product_id,
            user_id=user_id,
            movement_type=movement_type.value,
            quantity=quantity,
            quantity_after=new_quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )
        db.add(movement)
        db.flush()
        
        return inventory
    
    def get_movements(
        self,
        db: Session,
        business_id: uuid.UUID,
        product_id: Optional[uuid.UUID] = None,
        movement_type: Optional[StockMovementType] = None,
        skip: int = 0,
        limit: int = 50
    ):
        query = db.query(StockMovement).filter(StockMovement.business_id == business_id)
        
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type.value)
        
        return query.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_current_stock(self, db: Session, product_id: uuid.UUID) -> Optional[Inventory]:
        return self.repo.get_by_product_id(db, product_id)