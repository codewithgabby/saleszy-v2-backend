from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import SellingUnit
from typing import List, Optional
from decimal import Decimal
import uuid


class SellingUnitRepository:
    
    def create(self, db: Session, data: dict) -> SellingUnit:
        unit = SellingUnit(
            product_id=data["product_id"],
            name=data["name"],
            base_unit_quantity=data["base_unit_quantity"],
            selling_price=data.get("selling_price"),
            barcode=data.get("barcode"),
            sku=data.get("sku"),
            display_order=data.get("display_order", 0),
            is_default=data.get("is_default", False),
            is_direct_sell=data.get("is_direct_sell", True),
            is_active=data.get("is_active", True)
        )
        db.add(unit)
        db.flush()
        return unit

    def get_by_id(self, db: Session, unit_id: uuid.UUID) -> Optional[SellingUnit]:
        return db.query(SellingUnit).filter(SellingUnit.id == unit_id).first()

    def get_by_product(self, db: Session, product_id: uuid.UUID) -> List[SellingUnit]:
        return (
            db.query(SellingUnit)
            .filter(SellingUnit.product_id == product_id, SellingUnit.is_active == True)
            .order_by(SellingUnit.display_order, SellingUnit.name)
            .all()
        )

    def get_default_for_product(self, db: Session, product_id: uuid.UUID) -> Optional[SellingUnit]:
        return (
            db.query(SellingUnit)
            .filter(SellingUnit.product_id == product_id, SellingUnit.is_default == True)
            .first()
        )

    def search(self, db: Session, business_id: uuid.UUID, query: str, limit: int = 20) -> List[SellingUnit]:
        """Search selling units by name, SKU, barcode, or product name."""
        from app.models import Product
        search_term = f"%{query}%"
        
        return (
            db.query(SellingUnit)
            .join(Product, SellingUnit.product_id == Product.id)
            .filter(
                Product.business_id == business_id,
                Product.is_active == True,
                SellingUnit.is_active == True,
                or_(
                    SellingUnit.name.ilike(search_term),
                    SellingUnit.sku.ilike(search_term),
                    SellingUnit.barcode.ilike(search_term),
                    Product.name.ilike(search_term)
                )
            )
            .order_by(SellingUnit.display_order, SellingUnit.name)
            .limit(limit)
            .all()
        )

    def update(self, db: Session, unit_id: uuid.UUID, updates: dict) -> Optional[SellingUnit]:
        unit = self.get_by_id(db, unit_id)
        if not unit:
            return None
        for key, value in updates.items():
            if hasattr(unit, key) and value is not None:
                setattr(unit, key, value)
        db.flush()
        return unit

    def has_historical_sales(self, db: Session, unit_id: uuid.UUID) -> bool:
        from app.models import SaleItem
        count = (
            db.query(SaleItem)
            .filter(SaleItem.selling_unit_id == unit_id)
            .count()
        )
        return count > 0

    def archive(self, db: Session, unit_id: uuid.UUID) -> Optional[SellingUnit]:
        unit = self.get_by_id(db, unit_id)
        if not unit:
            return None
        unit.is_active = False
        db.flush()
        return unit