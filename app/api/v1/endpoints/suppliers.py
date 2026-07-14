from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])
service = SupplierService()

class SupplierCreate(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class SupplierResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SupplierResponse)
async def create_supplier(
    request: SupplierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        supplier = service.create_supplier(
            db, 
            current_user.business_id, 
            request.model_dump()
        )
        db.commit()
        return {
            "id": str(supplier.id),
            "name": supplier.name,
            "phone": supplier.phone,
            "email": supplier.email,
            "address": supplier.address,
            "is_active": supplier.is_active
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[SupplierResponse])
async def get_suppliers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    suppliers = service.get_suppliers(db, current_user.business_id)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "phone": s.phone,
            "email": s.email,
            "address": s.address,
            "is_active": s.is_active
        }
        for s in suppliers
    ]

@router.get("/search", response_model=List[SupplierResponse])
async def search_suppliers(
    query: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    suppliers = service.search_suppliers(db, current_user.business_id, query)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "phone": s.phone,
            "email": s.email,
            "address": s.address,
            "is_active": s.is_active
        }
        for s in suppliers
    ]