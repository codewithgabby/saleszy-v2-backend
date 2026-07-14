from sqlalchemy.orm import Session
from app.repositories.supplier_repository import SupplierRepository
from uuid import UUID

class SupplierService:
    def __init__(self):
        self.repo = SupplierRepository()

    def create_supplier(self, db: Session, business_id: UUID, data: dict):
        existing = self.repo.get_by_phone(db, business_id, data["phone"])
        if existing:
            raise ValueError("A supplier with this phone number already exists.")
        return self.repo.create(db, business_id, data)

    def get_suppliers(self, db: Session, business_id: UUID):
        return self.repo.get_all(db, business_id)

    def search_suppliers(self, db: Session, business_id: UUID, query: str):
        return self.repo.search(db, business_id, query)