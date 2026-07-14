from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import AuditLog
from typing import List, Optional
import uuid

class AuditRepository:
    def create(self, db: Session, data: dict) -> AuditLog:
        log = AuditLog(
            business_id=data["business_id"],
            user_id=data["user_id"],
            action=data["action"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            description=data.get("description")
        )
        db.add(log)
        db.flush()
        return log

    def get_by_business(
        self, 
        db: Session, 
        business_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        target_type: Optional[str] = None,
        target_id: Optional[uuid.UUID] = None
    ) -> List[AuditLog]:
        query = db.query(AuditLog).filter(AuditLog.business_id == business_id)
        
        if target_type:
            query = query.filter(AuditLog.target_type == target_type)
        if target_id:
            query = query.filter(AuditLog.target_id == target_id)
        
        return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()