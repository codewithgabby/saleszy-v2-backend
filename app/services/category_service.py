from sqlalchemy.orm import Session
from app.repositories.category_repository import CategoryRepository
from uuid import UUID

class CategoryService:
    def __init__(self):
        self.repo = CategoryRepository()

    def create_category(self, db: Session, business_id: UUID, name: str):
        # Check if category with same name already exists
        existing = self.repo.get_by_name(db, business_id, name)
        if existing:
            raise ValueError("A category with this name already exists.")
        
        return self.repo.create(db, business_id, name)

    def get_categories(self, db: Session, business_id: UUID):
        return self.repo.get_all(db, business_id)

    def delete_category(self, db: Session, category_id: UUID):
        category = self.repo.get_by_id(db, category_id)
        if not category:
            raise ValueError("Category not found.")
        self.repo.delete(db, category)