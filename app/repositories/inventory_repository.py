from sqlalchemy.orm import Session
from app.models import Inventory
from typing import Optional
import uuid

class InventoryRepository:
    def get_by_product_id(self, db: Session, product_id: uuid.UUID, with_lock: bool = False) -> Optional[Inventory]:
        query = db.query(Inventory).filter(Inventory.product_id == product_id)
        if with_lock:
            query = query.with_for_update()
        return query.first()

    def create_inventory(self, db: Session, product_id: uuid.UUID):
        inventory = Inventory(
            product_id=product_id,
            available_quantity=0,
            reserved_quantity=0,
            damaged_quantity=0
        )
        db.add(inventory)
        db.flush()
        return inventory