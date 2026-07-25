from alembic.util import status
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

    def get_customers(
        self,
        db: Session,
        business_id: UUID,
        status: str = "active"
    ):
        return self.repo.get_all(
            db=db,
            business_id=business_id,
            status=status
        )

    def search_customers(self, db: Session, business_id: UUID, query: str):
        return self.repo.search(db, business_id, query)

    def update_customer(self, db: Session, business_id: UUID, customer_id: UUID, data: dict):
        customer = self.repo.get_by_id(db, customer_id)

        if not customer or customer.business_id != business_id:
            raise ValueError("Customer not found.")

        return self.repo.update(db, customer, data)