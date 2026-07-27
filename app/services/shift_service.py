from sqlalchemy.orm import Session
from app.repositories.shift_repository import ShiftRepository
from app.models import User
from decimal import Decimal
from typing import Optional, List
import uuid


class ShiftService:
    
    def __init__(self):
        self.repo = ShiftRepository()

    def _can_view_shift(self, viewer: User, shift_owner: User) -> bool:
        """
        RBAC Rules

        Owner:
        - Can view everyone

    Manager:
        - Can view own shifts
        - Can view cashier shifts
        - Cannot view owner shifts

    Cashier:
        - Can only view own shifts
    """

    # Owner can see everything
        if viewer.role == "owner":
            return True

    # Everyone can view their own shifts
        if viewer.id == shift_owner.id:
            return True

    # Manager can only view cashier shifts
        if (
            viewer.role == "manager"
            and shift_owner.role == "cashier"
        ):
            return True

        return False    
    
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
    
    def get_shifts(
        self,
        db: Session,
        business_id: uuid.UUID,
        current_user: User,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20
    ):
        shifts = self.repo.get_shifts(
            db,
            business_id,
            user_id,
            skip,
            limit
        )

        # Owner can view every shift
        if current_user.role == "owner":
            return shifts

        allowed_shifts = []

        for shift in shifts:
            shift_owner = (
                db.query(User)
                .filter(User.id == shift.user_id)
                .first()
            )

            if shift_owner and self._can_view_shift(current_user, shift_owner):
                allowed_shifts.append(shift)

        return allowed_shifts
    
    def get_shift_detail(
        self,
        db: Session,
        shift_id: uuid.UUID,
        current_user: User
    ):
        shift = self.repo.get_shift_by_id(db, shift_id)

        if not shift:
            raise ValueError("Shift not found")

        shift_owner = (
            db.query(User)
            .filter(User.id == shift.user_id)
            .first()
        )

        if not shift_owner:
            raise ValueError("Shift owner not found")

        if not self._can_view_shift(current_user, shift_owner):
            raise PermissionError("You are not authorized to view this shift.")

        summary = self.repo.get_shift_summary(db, shift_id)
        events = self.repo.get_shift_events(db, shift_id)

        return summary, events

    def get_shift_summary(self, db: Session, shift_id: uuid.UUID):
        summary = self.repo.get_shift_summary(db, shift_id)

        if not summary:
            raise ValueError("Shift not found")

        return summary

    def update_shift_totals(self, db: Session, shift_id: uuid.UUID, sale_amount: Decimal):
        return self.repo.update_shift_totals(db, shift_id, sale_amount)    