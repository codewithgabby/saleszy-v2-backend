from sqlalchemy.orm import Session
from app.repositories.audit_repository import AuditRepository
from typing import Optional, Any
import uuid

class AuditService:
    def __init__(self):
        self.repo = AuditRepository()

    def log(
        self,
        db: Session,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: uuid.UUID,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        description: Optional[str] = None
    ):
        return self.repo.create(db, {
            "business_id": business_id,
            "user_id": user_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "old_value": old_value,
            "new_value": new_value,
            "description": description
        })

    def log_price_change(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, product_id: uuid.UUID, old_price: float, new_price: float):
        return self.log(
            db, business_id, user_id,
            "price_change", "product", product_id,
            {"price": old_price}, {"price": new_price},
            f"Price changed from ₦{old_price:,.2f} to ₦{new_price:,.2f}"
        )

    def log_tax_change(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, old_rate: float, new_rate: float):
        return self.log(
            db, business_id, user_id,
            "tax_change", "settings", business_id,
            {"tax_rate": old_rate}, {"tax_rate": new_rate},
            f"Tax rate changed from {old_rate}% to {new_rate}%"
        )

    def log_sale_void(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, sale_id: uuid.UUID, reason: str):
        return self.log(
            db, business_id, user_id,
            "sale_voided", "sale", sale_id,
            {"status": "completed"}, {"status": "voided", "reason": reason},
            f"Sale voided: {reason}"
        )

    def log_settings_update(self, db: Session, business_id: uuid.UUID, user_id: uuid.UUID, old_settings: dict, new_settings: dict):
        return self.log(
            db, business_id, user_id,
            "settings_updated", "settings", business_id,
            old_settings, new_settings,
            "Business settings updated"
        )

    def get_logs(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 50, target_type: str = None):
        return self.repo.get_by_business(db, business_id, skip, limit, target_type)