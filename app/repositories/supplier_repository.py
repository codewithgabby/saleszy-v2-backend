from sqlalchemy.orm import Session
from app.models import Supplier
from typing import List, Optional
import uuid

class SupplierRepository:
    def get_by_phone(self, db: Session, business_id: uuid.UUID, phone: str) -> Optional[Supplier]:
        return db.query(Supplier).filter(
            Supplier.business_id == business_id,
            Supplier.phone == phone,
            Supplier.is_active == True
        ).first()

    def get_by_id(self, db: Session, supplier_id: uuid.UUID) -> Optional[Supplier]:
        return db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_active == True).first()

    def get_all(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Supplier]:
        return db.query(Supplier).filter(
            Supplier.business_id == business_id,
            Supplier.is_active == True
        ).offset(skip).limit(limit).all()

    def create(self, db: Session, business_id: uuid.UUID, data: dict) -> Supplier:
        supplier = Supplier(business_id=business_id, **data)
        db.add(supplier)
        db.flush()
        return supplier

    def search(self, db: Session, business_id: uuid.UUID, query: str) -> List[Supplier]:
        return db.query(Supplier).filter(
            Supplier.business_id == business_id,
            Supplier.is_active == True,
            Supplier.name.ilike(f"%{query}%")
        ).limit(20).all()