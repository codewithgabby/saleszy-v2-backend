from sqlalchemy.orm import Session
from app.repositories.analytics_repository import AnalyticsRepository
from typing import Optional
import uuid


class AnalyticsService:
    
    def __init__(self):
        self.repo = AnalyticsRepository()
    
    def get_dashboard(self, db: Session, business_id: uuid.UUID, start_date=None, end_date=None,
                      cashier_id=None, shift_id=None, customer_id=None, payment_method=None):
        return self.repo.get_dashboard_summary(db, business_id, start_date, end_date)
    
    def get_top_products(self, db: Session, business_id: uuid.UUID, limit: int = 10, start_date=None, end_date=None,
                         cashier_id=None, category_id=None):
        return self.repo.get_top_products(db, business_id, limit, start_date, end_date)
    
    def get_inventory_value(self, db: Session, business_id: uuid.UUID):
        return self.repo.get_inventory_value(db, business_id)
    
    def get_financial(self, db: Session, business_id: uuid.UUID, start_date=None, end_date=None,
                      cashier_id=None, shift_id=None, payment_method=None):
        return self.repo.get_financial(db, business_id, start_date, end_date)