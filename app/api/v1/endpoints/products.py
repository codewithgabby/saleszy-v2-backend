from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])
service = ProductService()

# --- Schemas ---
class ProductCreate(BaseModel):
    name: str
    price: Decimal = Field(..., decimal_places=2)
    base_unit: str = "Unit"
    category_id: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    image_key: Optional[str] = None
    low_stock_threshold: int = 5

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    base_unit: str = "Unit"
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    image_key: Optional[str] = None
    low_stock_threshold: int
    is_active: bool
    inventory_available: float

# --- Helper ---
def _format_product(p) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "price": float(p.price),
        "base_unit": p.base_unit,
        "category_id": str(p.category_id) if p.category_id else None,
        "category_name": p.category.name if p.category else None,
        "sku": p.sku,
        "barcode": p.barcode,
        "image_key": p.image_key,
        "low_stock_threshold": p.low_stock_threshold,
        "is_active": p.is_active,
        "inventory_available": float(p.inventory.available_quantity) if p.inventory else 0.0
    }

# --- Routes ---
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
async def create_product(
    request: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        product = service.create_product(
            db,
            current_user.business_id,
            request.name,
            request.price,
            base_unit=request.base_unit,
            category_id=request.category_id,
            sku=request.sku,
            barcode=request.barcode,
            image_key=request.image_key,
            low_stock_threshold=request.low_stock_threshold
        )
        db.commit()
        return _format_product(product)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    products = service.get_products(db, current_user.business_id)
    return [_format_product(p) for p in products]

@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    query: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    products = service.search_products(db, current_user.business_id, query)
    return [_format_product(p) for p in products]