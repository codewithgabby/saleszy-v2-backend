from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.category_service import CategoryService
from typing import List

router = APIRouter(prefix="/categories", tags=["Categories"])
service = CategoryService()

# --- Schemas ---
class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: str
    name: str
    is_active: bool

# --- Routes ---
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CategoryResponse)
async def create_category(
    request: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        category = service.create_category(db, current_user.business_id, request.name)
        db.commit()
        return {"id": str(category.id), "name": category.name, "is_active": category.is_active}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    categories = service.get_categories(db, current_user.business_id)
    return [
        {"id": str(c.id), "name": c.name, "is_active": c.is_active}
        for c in categories
    ]

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service.delete_category(db, category_id)
        db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))