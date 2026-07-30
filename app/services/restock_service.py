from sqlalchemy.orm import Session
from decimal import Decimal
import uuid

from app.repositories.restock_repository import RestockRepository
from app.repositories.inventory_repository import InventoryRepository
from app.services.inventory_service import (
    InventoryService,
    StockMovementType
)


class RestockService:

    def __init__(self):
        self.restock_repo = RestockRepository()
        self.inventory_repo = InventoryRepository()
        self.inventory_service = InventoryService()

    def create_restock(
        self,
        db: Session,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        supplier_id: uuid.UUID | None,
        quantity: Decimal,
        buying_cost: Decimal,
        reference_number: str | None,
        notes: str | None,
        user_id: uuid.UUID,
    ):

        inventory = self.inventory_repo.get_by_product_id(
            db,
            product_id,
            with_lock=True
        )

        if not inventory:
            raise ValueError("Inventory record not found.")

        restock = self.restock_repo.create(
            db=db,
            business_id=business_id,
            product_id=product_id,
            supplier_id=supplier_id,
            received_quantity=quantity,
            buying_cost=buying_cost,
            reference_number=reference_number,
            notes=notes,
            received_by_user_id=user_id
        )

        self.inventory_service.adjust_stock(
            db=db,
            business_id=business_id,
            product_id=product_id,
            user_id=user_id,
            quantity=quantity,
            movement_type=StockMovementType.RESTOCK,
            reference_type="restock",
            reference_id=restock.id,
            notes=notes,
            with_lock=False
        )

        return restock