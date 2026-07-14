from sqlalchemy.orm import Session
from app.models import Category
from typing import Optional, List
import uuid

class CategoryRepository:
    def get_by_name(self, db: Session, business_id: uuid.UUID, name: str) -> Optional[Category]:
        return db.query(Category).filter(
            Category.business_id == business_id,
            Category.name == name,
            Category.is_active == True
        ).first()

    def get_by_id(self, db: Session, category_id: uuid.UUID) -> Optional[Category]:
        return db.query(Category).filter(Category.id == category_id, Category.is_active == True).first()

    def get_all(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Category]:
        return db.query(Category).filter(
            Category.business_id == business_id,
            Category.is_active == True
        ).offset(skip).limit(limit).all()

    def create(self, db: Session, business_id: uuid.UUID, name: str) -> Category:
        category = Category(business_id=business_id, name=name)
        db.add(category)
        db.flush()
        return category

    def delete(self, db: Session, category: Category) -> None:
        # Soft delete (just deactivate it)
        category.is_active = False
        db.flush()