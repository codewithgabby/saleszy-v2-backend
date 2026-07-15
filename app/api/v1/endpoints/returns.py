from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.return_service import ReturnService
from app.services.shift_service import ShiftService
from app.core.response import api_response

router = APIRouter(prefix="/returns", tags=["Returns"])
service = ReturnService()
shift_service = ShiftService()


class ReturnItemInput(BaseModel):
    sale_item_id: str
    quantity: Decimal

class ReturnCreate(BaseModel):
    sale_id: str
    return_type: str = Field(..., description="FULL or PARTIAL")
    reason_code: str = Field(..., description="CUSTOMER_CHANGED_MIND, WRONG_ITEM, DAMAGED_ITEM, EXPIRED_ITEM, QUALITY_ISSUE, CASHIER_ERROR, OTHER")
    refund_method: str = Field(..., description="CASH, TRANSFER, POS")
    items: List[ReturnItemInput]
    notes: Optional[str] = None


def _format_return(r) -> dict:
    return {
        "id": str(r.id),
        "return_number": r.return_number,
        "sale_id": str(r.sale_id),
        "return_type": r.return_type,
        "reason_code": r.reason_code,
        "refund_method": r.refund_method,
        "subtotal": float(r.subtotal),
        "tax": float(r.tax),
        "total_refund": float(r.total_refund),
        "status": r.status,
        "notes": r.notes,
        "items": [
            {
                "sale_item_id": str(i.sale_item_id),
                "selling_unit_name": i.selling_unit_name,
                "quantity": float(i.quantity),
                "refund_amount": float(i.refund_amount),
            }
            for i in (r.items or [])
        ],
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_return(
    request: ReturnCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get current shift
    shift = shift_service.get_current_shift(db, current_user.id)
    if not shift:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No open shift")
    
    try:
        ret = service.process_return(
            db,
            current_user.business_id,
            UUID(request.sale_id),
            shift.id,
            current_user.id,
            request.return_type,
            request.reason_code,
            request.refund_method,
            [{"sale_item_id": i.sale_item_id, "quantity": i.quantity} for i in request.items],
            request.notes,
        )
        db.commit()
        return api_response(data=_format_return(ret), message="Return processed")
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/")
async def list_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    returns = service.get_returns(db, current_user.business_id, skip, limit)
    return api_response(data=[_format_return(r) for r in returns], message=f"Retrieved {len(returns)} returns")


@router.get("/{return_id}")
async def get_return(
    return_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        ret = service.get_return(db, UUID(return_id))
        return api_response(data=_format_return(ret), message="Return details")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{return_id}/cancel")
async def cancel_return(
    return_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        ret = service.cancel_return(db, UUID(return_id), current_user.id)
        db.commit()
        return api_response(data=_format_return(ret), message="Return cancelled")
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))