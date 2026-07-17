from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.business_service import BusinessService
from app.core.response import api_response

router = APIRouter(prefix="/business", tags=["Business"])
service = BusinessService()

# --- Schemas ---
class BusinessProfileUpdate(BaseModel):
    legal_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, or + prefix')
        return v

class BrandingSchema(BaseModel):
    store_name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    logo_url: Optional[str] = Field(None, max_length=500)
    receipt_footer: Optional[str] = Field(None, max_length=500)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, or + prefix')
        return v

class SettingsUpdateRequest(BaseModel):
    currency_symbol: Optional[str] = Field(None, max_length=5)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    max_discount_percent: Optional[float] = Field(None, ge=0, le=100)
    receipt_width: Optional[float] = Field(None, ge=40, le=120)
    timezone: Optional[str] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    branding: Optional[BrandingSchema] = None

# --- Routes ---
@router.get("/me")
async def get_my_business(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = service.get_business_profile(db, current_user.business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Business not found"
        )
    
    return api_response(
        data={
            "id": str(business.id),
            "legal_name": business.legal_name,
            "slug": business.slug,
            "email": business.email,
            "phone": business.phone,
            "is_active": business.is_active,
            "settings": {
                "timezone": getattr(business.settings, 'timezone', None) or "Africa/Lagos" if business.settings else "Africa/Lagos",
                "language": getattr(business.settings, 'language', None) or "en" if business.settings else "en",
                "currency_symbol": getattr(business.settings, 'currency_symbol', None) or "₦" if business.settings else "₦",
                "receipt_width": float(getattr(business.settings, 'receipt_width', None) or 80.0) if business.settings else 80.0,
                "tax_rate": float(getattr(business.settings, 'tax_rate', None) or 0.0) if business.settings else 0.0,
                "max_discount_percent": float(getattr(business.settings, 'max_discount_percent', None) or 10.0) if business.settings else 10.0,
                "branding": business.settings.branding if business.settings else {}
            }
        },
        message="Business profile retrieved successfully"
    )

@router.patch("/profile")
async def update_business_profile(
    updates: BusinessProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No valid fields to update"
        )
    
    updated = service.update_profile(db, current_user.business_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Business not found"
        )
    
    db.commit()
    return api_response(
        data={
            "id": str(updated.id),
            "legal_name": updated.legal_name,
            "phone": updated.phone
        },
        message="Business profile updated successfully"
    )

@router.patch("/settings")
async def update_business_settings(
    updates: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No valid fields to update"
        )
    
    # Handle branding merge if provided
    if 'branding' in update_data and update_data['branding'] is not None:
        business = service.get_business_profile(db, current_user.business_id)
        if business and business.settings:
            existing_branding = business.settings.branding or {}
            existing_branding.update(update_data['branding'])
            update_data['branding'] = existing_branding
    
    updated = service.update_settings(db, current_user.business_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Settings not found"
        )
    
    db.commit()
    return api_response(
        data={
            "timezone": updated.timezone,
            "language": updated.language,
            "currency_symbol": updated.currency_symbol,
            "receipt_width": float(updated.receipt_width),
            "tax_rate": float(updated.tax_rate),
            "max_discount_percent": float(updated.max_discount_percent) if updated.max_discount_percent else 10.0,
            "branding": updated.branding
        },
        message="Business settings updated successfully"
    )