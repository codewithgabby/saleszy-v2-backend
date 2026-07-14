from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import ActivityLog
from typing import List, Optional
import uuid

class ActivityRepository:
    def create(self, db: Session, data: dict) -> ActivityLog:
        log = ActivityLog(
            business_id=data["business_id"],
            user_id=data["user_id"],
            action=data["action"],
            description=data.get("description"),
            target_type=data.get("target_type"),
            target_id=data.get("target_id"),
            log_metadata=data.get("metadata", {})
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
        action: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> List[ActivityLog]:
        query = db.query(ActivityLog).filter(ActivityLog.business_id == business_id)
        
        if action:
            query = query.filter(ActivityLog.action == action)
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        
        return query.order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit).all()