from sqlalchemy.orm import Session
from app.repositories.customer_repository import CustomerRepository
from uuid import UUID

class CustomerService:
    def __init__(self):
        self.repo = CustomerRepository()

    def create_customer(self, db: Session, business_id: UUID, data: dict):
        existing = self.repo.get_by_phone(db, business_id, data["phone"])
        if existing:
            raise ValueError("A customer with this phone number already exists.")
        return self.repo.create(db, business_id, data)

    def get_customers(self, db: Session, business_id: UUID):
        return self.repo.get_all(db, business_id)

    def search_customers(self, db: Session, business_id: UUID, query: str):
        return self.repo.search(db, business_id, query)