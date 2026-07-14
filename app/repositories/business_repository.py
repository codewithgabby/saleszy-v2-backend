from sqlalchemy.orm import Session
from app.models import Business, BusinessSettings, User

class BusinessRepository:
    def get_business_with_settings(self, db: Session, business_id: str) -> Business | None:
        return db.query(Business).filter(Business.id == business_id).first()

    def update_business_profile(self, db: Session, business_id: str, updates: dict) -> Business | None:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return None
        
        for key, value in updates.items():
            if hasattr(business, key):
                setattr(business, key, value)
        return business

    def update_business_settings(self, db: Session, business_id: str, updates: dict) -> BusinessSettings | None:
        settings = db.query(BusinessSettings).filter(BusinessSettings.business_id == business_id).first()
        if not settings:
            return None
        
        for key, value in updates.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        return settings