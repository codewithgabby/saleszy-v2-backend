from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal


class SellingUnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="e.g., 'Carton', 'Half Loaf', '5kg Bag'")
    base_unit_quantity: Decimal = Field(..., gt=0, description="How many base units this represents")
    selling_price: Optional[Decimal] = Field(None, gt=0, description="Null = use product's default price")
    barcode: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    display_order: int = Field(0, ge=0)
    is_direct_sell: bool = Field(True)
    is_active: bool = Field(True)


class SellingUnitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_unit_quantity: Optional[Decimal] = Field(None, gt=0)
    selling_price: Optional[Decimal] = Field(None, gt=0)
    barcode: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)
    is_direct_sell: Optional[bool] = None
    is_active: Optional[bool] = None


class SellingUnitResponse(BaseModel):
    id: str
    product_id: str
    name: str
    base_unit_quantity: float
    selling_price: Optional[float] = None
    barcode: Optional[str] = None
    sku: Optional[str] = None
    display_order: int
    is_default: bool
    is_direct_sell: bool
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True