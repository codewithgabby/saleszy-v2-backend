from sqlalchemy.orm import Session
from app.repositories.activity_repository import ActivityRepository
from typing import Optional
import uuid

class ActivityService:
    def __init__(self):
        self.repo = ActivityRepository()

    def log(
        self,
        db: Session,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        description: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None
    ):
        return self.repo.create(db, {
            "business_id": business_id,
            "user_id": user_id,
            "action": action,
            "description": description,
            "target_type": target_type,
            "target_id": target_id,
            "metadata": metadata or {}
        })

    def log_login(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID):
        return self.log(db, business_id, user_id, "user_login", "User logged in")

    def log_sale_completed(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, sale_id: uuid.UUID, total: float):
        return self.log(
            db, business_id, user_id, 
            "sale_completed", 
            f"Sale completed: ₦{total:,.2f}",
            "sale", sale_id,
            {"total": total}
        )

    def log_sale_voided(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, sale_id: uuid.UUID, reason: str):
        return self.log(
            db, business_id, user_id,
            "sale_voided",
            f"Sale voided: {reason}",
            "sale", sale_id,
            {"reason": reason}
        )

    def log_stock_added(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, product_id: uuid.UUID, quantity: float):
        return self.log(
            db, business_id, user_id,
            "stock_added",
            f"Added {quantity} stock",
            "product", product_id,
            {"quantity": quantity}
        )

    def get_logs(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 50, action: str = None):
        return self.repo.get_by_business(db, business_id, skip, limit, action)