from sqlalchemy.orm import Session
from app.repositories.business_repository import BusinessRepository

class BusinessService:
    def __init__(self):
        self.repo = BusinessRepository()

    def get_business_profile(self, db: Session, business_id: str):
        return self.repo.get_business_with_settings(db, business_id)

    def update_profile(self, db: Session, business_id: str, updates: dict):
        return self.repo.update_business_profile(db, business_id, updates)

    def update_settings(self, db: Session, business_id: str, updates: dict):
        return self.repo.update_business_settings(db, business_id, updates)