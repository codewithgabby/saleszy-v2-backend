from sqlalchemy.orm import Session
from app.repositories.shift_repository import ShiftRepository
from decimal import Decimal
from typing import Optional, List
import uuid


class ShiftService:
    
    def __init__(self):
        self.repo = ShiftRepository()
    
    def open_shift(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, opened_by: uuid.UUID, opening_cash: Decimal = Decimal('0.00')):
        # Check if already open
        existing = self.repo.get_current_shift(db, user_id)
        if existing:
            raise ValueError("You already have an open shift. Close it before opening a new one.")
        
        return self.repo.open_shift(db, business_id, user_id, opened_by, opening_cash)
    
    def get_current_shift(self, db: Session, user_id: uuid.UUID):
        return self.repo.get_current_shift(db, user_id)
    
    def close_shift(self, db: Session, shift_id: uuid.UUID, user_id: uuid.UUID, actual_cash: Decimal):
        shift = self.repo.get_shift_by_id(db, shift_id)
        if not shift:
            raise ValueError("Shift not found")
        if shift.status != "OPEN":
            raise ValueError("Shift is already closed")
        
        return self.repo.close_shift(db, shift, user_id, actual_cash)
    
    def get_shifts(self, db: Session, business_id: uuid.UUID, user_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 20):
        return self.repo.get_shifts(db, business_id, user_id, skip, limit)
    
    def get_shift_detail(self, db: Session, shift_id: uuid.UUID):
        shift = self.repo.get_shift_by_id(db, shift_id)
        if not shift:
            raise ValueError("Shift not found")
        events = self.repo.get_shift_events(db, shift_id)
        return shift, events

    def update_shift_totals(self, db: Session, shift_id: uuid.UUID, sale_amount: Decimal):
        return self.repo.update_shift_totals(db, shift_id, sale_amount)    