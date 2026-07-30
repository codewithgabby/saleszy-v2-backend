from sqlalchemy.orm import Session
from app.repositories.supplier_repository import SupplierRepository
from uuid import UUID

class SupplierService:
    def __init__(self):
        self.repo = SupplierRepository()

    def create_supplier(self, db: Session, business_id: UUID, data: dict):
        data["name"] = " ".join(data["name"].strip().split())

        existing = self.repo.get_by_phone(db, business_id, data["phone"])
        if existing:
            raise ValueError(
                f'Phone number "{data["phone"]}" already belongs to another supplier.'
            )

        existing = self.repo.get_by_name(db, business_id, data["name"])
        if existing:
            raise ValueError(
                f'Supplier "{existing.name}" already exists.'
            )

        return self.repo.create(
            db,
            business_id,
            data
        )

    def get_suppliers(self, db: Session, business_id: UUID, status: str = "active"):
        return self.repo.get_all(db, business_id, status=status)

    def search_suppliers(self, db: Session, business_id: UUID, query: str):
        return self.repo.search(db, business_id, query)

    def update_supplier(
        self,
        db: Session,
        supplier_id: UUID,
        business_id: UUID,
        data: dict
    ):
        supplier = self.repo.get_by_id(db, supplier_id)

        if "name" in data:
            data["name"] = " ".join(data["name"].strip().split())

        if not supplier:
            raise ValueError("Supplier not found.")

        if supplier.business_id != business_id:
            raise ValueError("Supplier not found.")

        if "name" in data and data["name"] != supplier.name:
            existing = self.repo.get_by_name(
                db,
                business_id,
                data["name"]
            )

            if existing and existing.id != supplier.id:
                raise ValueError(
                    f'Supplier "{existing.name}" already exists.'
                )

        if "phone" in data and data["phone"] != supplier.phone:
            existing = self.repo.get_by_phone(
                db,
                business_id,
                data["phone"]
            )

            if existing and existing.id != supplier.id:
                raise ValueError(
                    f'Phone number "{data["phone"]}" already belongs to another supplier.'
                )

        return self.repo.update(
            db,
            supplier,
            data
        )

    def delete_supplier(
        self,
        db: Session,
        supplier_id: UUID,
        business_id: UUID
):
        supplier = self.repo.get_by_id(db, supplier_id)

        if not supplier:
            raise ValueError("Supplier not found.")

        if supplier.business_id != business_id:
            raise ValueError("Supplier not found.")

        if not supplier.is_active:
            raise ValueError("Supplier has already been archived.")

        return self.repo.delete(
            db,
            supplier
        )