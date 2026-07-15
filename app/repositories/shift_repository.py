from sqlalchemy.orm import Session
from app.models import Shift, ShiftEvent
from typing import Optional, List
from decimal import Decimal
import uuid
from datetime import datetime, timezone


class ShiftRepository:
    
    def get_current_shift(self, db: Session, user_id: uuid.UUID) -> Optional[Shift]:
        return db.query(Shift).filter(
            Shift.user_id == user_id,
            Shift.status == "OPEN"
        ).first()
    
    def get_shift_by_id(self, db: Session, shift_id: uuid.UUID) -> Optional[Shift]:
        return db.query(Shift).filter(Shift.id == shift_id).first()
    
    def open_shift(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, opened_by: uuid.UUID, opening_cash: Decimal) -> Shift:
        shift = Shift(
            business_id=business_id,
            user_id=user_id,
            opened_by_user_id=opened_by,
            opening_cash=opening_cash,
            status="OPEN"
        )
        db.add(shift)
        db.flush()
        
        # Log event
        event = ShiftEvent(
            shift_id=shift.id,
            event_type="OPENED",
            amount=opening_cash,
            notes="Shift opened",
            created_by=opened_by
        )
        db.add(event)
        db.flush()
        return shift
    
    def close_shift(self, db: Session, shift: Shift, closed_by: uuid.UUID, actual_cash: Decimal) -> Shift:
        # Calculate expected cash
        expected = shift.opening_cash + shift.total_sales - shift.total_refunds
        shift.expected_cash = expected
        shift.actual_cash = actual_cash
        shift.cash_variance = actual_cash - expected
        shift.status = "CLOSED"
        shift.closed_by_user_id = closed_by
        shift.closed_at = datetime.now(timezone.utc)
        db.flush()
        
        # Log event
        event = ShiftEvent(
            shift_id=shift.id,
            event_type="CLOSED",
            amount=actual_cash,
            notes=f"Shift closed. Expected: {expected}, Actual: {actual_cash}, Variance: {actual_cash - expected}",
            created_by=closed_by
        )
        db.add(event)
        db.flush()
        return shift
    
    def update_shift_totals(self, db: Session, shift_id: uuid.UUID, sale_amount: Decimal):
        shift = db.query(Shift).filter(Shift.id == shift_id).first()
        if shift:
            shift.total_sales += sale_amount
            shift.total_transactions += 1
            db.flush()
    
    def get_shifts(self, db: Session, business_id: uuid.UUID, user_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 20) -> List[Shift]:
        query = db.query(Shift).filter(Shift.business_id == business_id)
        if user_id:
            query = query.filter(Shift.user_id == user_id)
        return query.order_by(Shift.opened_at.desc()).offset(skip).limit(limit).all()
    
    def get_shift_events(self, db: Session, shift_id: uuid.UUID) -> List[ShiftEvent]:
        return db.query(ShiftEvent).filter(ShiftEvent.shift_id == shift_id).order_by(ShiftEvent.created_at.asc()).all()