from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from app.core.response import api_response
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

class SellingUnitItem(BaseModel):
    id: str
    name: str
    display_label: str
    base_unit_quantity: float
    selling_price: Optional[float] = None
    is_default: bool
    is_active: bool

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
    selling_units: List[SellingUnitItem] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[Decimal] = Field(None, decimal_places=2, gt=0)
    base_unit: Optional[str] = Field(None, min_length=1, max_length=50)
    category_id: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    image_key: Optional[str] = None
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None    

def _get_display_label(unit, product) -> str:
    qty = float(unit.base_unit_quantity)
    base = product.base_unit or "unit"
    if qty == 1:
        return unit.name
    qty_str = str(qty).rstrip('0').rstrip('.') if '.' in str(qty) else str(int(qty))
    return f"{unit.name} ({qty_str} {base}{'s' if qty > 1 else ''})"    

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
        "inventory_available": float(p.inventory.available_quantity) if p.inventory else 0.0,
        "selling_units": [
            {
                "id": str(u.id),
                "name": u.name,
                "display_label": _get_display_label(u, p),
                "base_unit_quantity": float(u.base_unit_quantity),
                "selling_price": float(u.selling_price) if u.selling_price else float(p.price),
                "is_default": u.is_default,
                "is_active": u.is_active,
            }
            for u in (p.selling_units or [])
            if u.is_active
        ]
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

@router.get("/barcode/{barcode}")
async def get_product_by_barcode(
    barcode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = service.repo.get_by_barcode(db, current_user.business_id, barcode)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return api_response(
        data=_format_product(product),
        message="Product found"
    )

@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    query: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    products = service.search_products(db, current_user.business_id, query)
    return [_format_product(p) for p in products]

@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    request: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from uuid import UUID
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")

    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    product = service.repo.get_by_id(db, product_uuid)
    if not product or product.business_id != current_user.business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return _format_product(product)    