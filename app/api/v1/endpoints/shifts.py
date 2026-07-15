from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from uuid import UUID
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.shift_service import ShiftService
from app.core.response import api_response

router = APIRouter(prefix="/shifts", tags=["Shifts"])
service = ShiftService()


class OpenShiftRequest(BaseModel):
    opening_cash: Decimal = Decimal('0.00')

class CloseShiftRequest(BaseModel):
    actual_cash: Decimal


def _format_shift(s) -> dict:
    return {
        "id": str(s.id),
        "business_id": str(s.business_id),
        "user_id": str(s.user_id),
        "status": s.status,
        "opening_cash": float(s.opening_cash),
        "expected_cash": float(s.expected_cash) if s.expected_cash else None,
        "actual_cash": float(s.actual_cash) if s.actual_cash else None,
        "cash_variance": float(s.cash_variance) if s.cash_variance else None,
        "total_sales": float(s.total_sales),
        "total_transactions": s.total_transactions,
        "total_refunds": float(s.total_refunds),
        "opened_at": s.opened_at.isoformat() if s.opened_at else None,
        "closed_at": s.closed_at.isoformat() if s.closed_at else None,
    }


@router.post("/open", status_code=status.HTTP_201_CREATED)
async def open_shift(
    request: OpenShiftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        shift = service.open_shift(
            db, current_user.business_id, current_user.id, current_user.id, request.opening_cash
        )
        db.commit()
        return api_response(data=_format_shift(shift), message="Shift opened")
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/current")
async def get_current_shift(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shift = service.get_current_shift(db, current_user.id)
    if not shift:
        return api_response(data=None, message="No open shift")
    return api_response(data=_format_shift(shift), message="Current shift")


@router.post("/{shift_id}/close")
async def close_shift(
    shift_id: str,
    request: CloseShiftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        shift = service.close_shift(db, UUID(shift_id), current_user.id, request.actual_cash)
        db.commit()
        return api_response(data=_format_shift(shift), message="Shift closed")
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/")
async def list_shifts(
    user_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    uid = UUID(user_id) if user_id else None
    shifts = service.get_shifts(db, current_user.business_id, uid, skip, limit)
    return api_response(data=[_format_shift(s) for s in shifts], message=f"Retrieved {len(shifts)} shifts")


@router.get("/{shift_id}")
async def get_shift_detail(
    shift_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        shift, events = service.get_shift_detail(db, UUID(shift_id))
        return api_response(data={
            "shift": _format_shift(shift),
            "events": [
                {"event_type": e.event_type, "amount": float(e.amount) if e.amount else None, "notes": e.notes, "created_at": e.created_at.isoformat() if e.created_at else None}
                for e in events
            ]
        }, message="Shift details")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))