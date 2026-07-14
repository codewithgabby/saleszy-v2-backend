from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])
service = CustomerService()

class CustomerCreate(BaseModel):
    full_name: str
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CustomerResponse)
async def create_customer(
    request: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        customer = service.create_customer(
            db, 
            current_user.business_id, 
            request.model_dump()
        )
        db.commit()
        return {
            "id": str(customer.id),
            "full_name": customer.full_name,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
            "notes": customer.notes,
            "is_active": customer.is_active
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customers = service.get_customers(db, current_user.business_id)
    return [
        {
            "id": str(c.id),
            "full_name": c.full_name,
            "phone": c.phone,
            "email": c.email,
            "address": c.address,
            "notes": c.notes,
            "is_active": c.is_active
        }
        for c in customers
    ]

@router.get("/search", response_model=List[CustomerResponse])
async def search_customers(
    query: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customers = service.search_customers(db, current_user.business_id, query)
    return [
        {
            "id": str(c.id),
            "full_name": c.full_name,
            "phone": c.phone,
            "email": c.email,
            "address": c.address,
            "notes": c.notes,
            "is_active": c.is_active
        }
        for c in customers
    ]