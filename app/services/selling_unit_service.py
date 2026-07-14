from sqlalchemy.orm import Session
from app.repositories.selling_unit_repository import SellingUnitRepository
from app.repositories.product_repository import ProductRepository
from decimal import Decimal
from typing import List, Optional
import uuid


class SellingUnitService:
    
    def __init__(self):
        self.repo = SellingUnitRepository()
        self.product_repo = ProductRepository()

    def create_unit(self, db: Session, product_id: uuid.UUID, data: dict) -> dict:
        """Create a new selling unit for a product."""
        product = self.product_repo.get_by_id(db, product_id)
        if not product:
            raise ValueError("Product not found.")

        unit = self.repo.create(db, {
            "product_id": product_id,
            "name": data["name"],
            "base_unit_quantity": data["base_unit_quantity"],
            "selling_price": data.get("selling_price"),
            "barcode": data.get("barcode"),
            "sku": data.get("sku"),
            "display_order": data.get("display_order", 0),
            "is_default": False,  # Only auto-created units are default
            "is_direct_sell": data.get("is_direct_sell", True),
            "is_active": data.get("is_active", True)
        })
        return unit

    def get_units_for_product(self, db: Session, product_id: uuid.UUID) -> List:
        """Get all active selling units for a product."""
        return self.repo.get_by_product(db, product_id)

    def get_unit(self, db: Session, unit_id: uuid.UUID):
        """Get a single selling unit by ID."""
        unit = self.repo.get_by_id(db, unit_id)
        if not unit:
            raise ValueError("Selling unit not found.")
        return unit

    def update_unit(self, db: Session, unit_id: uuid.UUID, updates: dict):
        """Update a selling unit. Cannot change base_unit_quantity if historical sales exist."""
        unit = self.repo.get_by_id(db, unit_id)
        if not unit:
            raise ValueError("Selling unit not found.")

        # Prevent changing base_unit_quantity if historical sales exist
        if "base_unit_quantity" in updates and updates["base_unit_quantity"] is not None:
            if self.repo.has_historical_sales(db, unit_id):
                raise ValueError(
                    "Cannot change base_unit_quantity for a unit with historical sales. "
                    "Archive this unit and create a new one instead."
                )

        return self.repo.update(db, unit_id, updates)

    def delete_unit(self, db: Session, unit_id: uuid.UUID):
        """Archive a selling unit. Cannot delete if historical sales exist."""
        unit = self.repo.get_by_id(db, unit_id)
        if not unit:
            raise ValueError("Selling unit not found.")

        if unit.is_default:
            raise ValueError("Cannot delete the default selling unit.")

        if self.repo.has_historical_sales(db, unit_id):
            # Archive instead of delete
            return self.repo.archive(db, unit_id)

        # Hard delete only if no sales exist
        db.delete(unit)
        return None

    def search_units(self, db: Session, business_id: uuid.UUID, query: str, limit: int = 20) -> List:
        """Search selling units by name, SKU, barcode, or product name."""
        return self.repo.search(db, business_id, query, limit)

    def get_effective_price(self, db: Session, unit_id: uuid.UUID) -> Decimal:
        """Get the selling price for a unit. Falls back to product price if unit has no custom price."""
        unit = self.repo.get_by_id(db, unit_id)
        if not unit:
            raise ValueError("Selling unit not found.")

        if unit.selling_price is not None:
            return unit.selling_price

        product = self.product_repo.get_by_id(db, unit.product_id)
        if not product:
            raise ValueError("Product not found.")

        return product.price