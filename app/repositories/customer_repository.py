from sqlalchemy.orm import Session
from app.models import Customer
from typing import List, Optional
import uuid

class CustomerRepository:
    def get_by_phone(self, db: Session, business_id: uuid.UUID, phone: str) -> Optional[Customer]:
        return db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.phone == phone,
            Customer.is_active == True
        ).first()

    def get_by_id(self, db: Session, customer_id: uuid.UUID) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.id == customer_id, Customer.is_active == True).first()

    def get_all(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Customer]:
        return db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.is_active == True
        ).offset(skip).limit(limit).all()

    def create(self, db: Session, business_id: uuid.UUID, data: dict) -> Customer:
        customer = Customer(business_id=business_id, **data)
        db.add(customer)
        db.flush()
        return customer

    def search(self, db: Session, business_id: uuid.UUID, query: str) -> List[Customer]:
        return db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.is_active == True,
            Customer.full_name.ilike(f"%{query}%")
        ).limit(20).all()