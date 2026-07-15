from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.selling_unit_service import SellingUnitService
from app.schemas.selling_unit import SellingUnitCreate, SellingUnitUpdate, SellingUnitResponse
from app.core.response import api_response

router = APIRouter(prefix="/selling-units", tags=["Selling Units"])
service = SellingUnitService()


def _format_unit(unit) -> dict:
    product = unit.product
    base_name = product.base_unit if product else "unit"
    
    # Build display label with clean number formatting
    qty = unit.base_unit_quantity
    # Remove trailing zeros: 6.000000 -> 6, 0.500000 -> 0.5
    qty_str = str(float(qty)).rstrip('0').rstrip('.') if '.' in str(float(qty)) else str(int(qty))
    
    if qty == 1:
        display_label = unit.name
    else:
        display_label = f"{unit.name} ({qty_str} {base_name}{'s' if qty > 1 else ''})"
    
    return {
        "id": str(unit.id),
        "product_id": str(unit.product_id),
        "name": unit.name,
        "display_label": display_label,
        "base_unit_quantity": float(unit.base_unit_quantity),
        "selling_price": float(unit.selling_price) if unit.selling_price else None,
        "barcode": unit.barcode,
        "sku": unit.sku,
        "display_order": unit.display_order,
        "is_default": unit.is_default,
        "is_direct_sell": unit.is_direct_sell,
        "is_active": unit.is_active,
        "created_at": unit.created_at.isoformat() if unit.created_at else None
    }


# --- Product-scoped routes ---
@router.get("/products/{product_id}/units")
async def get_product_units(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")

    units = service.get_units_for_product(db, product_uuid)
    
    return api_response(
        data=[_format_unit(u) for u in units],
        message=f"Retrieved {len(units)} selling units"
    )


@router.post("/products/{product_id}/units", status_code=status.HTTP_201_CREATED)
async def create_product_unit(
    product_id: str,
    request: SellingUnitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")

    try:
        unit = service.create_unit(db, product_uuid, request.model_dump())
        db.commit()
        return api_response(
            data=_format_unit(unit),
            message="Selling unit created successfully"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Unit-scoped routes ---
@router.get("/{unit_id}")
async def get_selling_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        unit_uuid = UUID(unit_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid unit ID")

    try:
        unit = service.get_unit(db, unit_uuid)
        return api_response(
            data=_format_unit(unit),
            message="Selling unit retrieved successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{unit_id}")
async def update_selling_unit(
    unit_id: str,
    request: SellingUnitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        unit_uuid = UUID(unit_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid unit ID")

    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    try:
        unit = service.update_unit(db, unit_uuid, update_data)
        db.commit()
        return api_response(
            data=_format_unit(unit),
            message="Selling unit updated successfully"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{unit_id}")
async def delete_selling_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        unit_uuid = UUID(unit_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid unit ID")

    try:
        result = service.delete_unit(db, unit_uuid)
        db.commit()
        
        if result:
            return api_response(
                data=_format_unit(result),
                message="Selling unit archived successfully (historical sales exist)"
            )
        return api_response(
            message="Selling unit deleted successfully"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/search/all")
async def search_selling_units(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    units = service.search_units(db, current_user.business_id, q, limit)
    
    return api_response(
        data=[_format_unit(u) for u in units],
        message=f"Found {len(units)} selling units"
    )