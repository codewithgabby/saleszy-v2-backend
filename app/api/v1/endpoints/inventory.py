from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from uuid import UUID
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.restock_service import RestockService
from app.core.response import api_response

router = APIRouter(prefix="/inventory", tags=["Inventory"])
restock_service = RestockService()

class CreateRestockRequest(BaseModel):
    product_id: str
    supplier_id: str | None = None
    quantity: Decimal
    buying_cost: Decimal
    reference_number: str | None = None
    notes: str | None = None


@router.post("/restock", status_code=status.HTTP_201_CREATED)
async def create_restock(
    request: CreateRestockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        product_uuid = UUID(request.product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )

    supplier_uuid = None

    if request.supplier_id:
        try:
            supplier_uuid = UUID(request.supplier_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid supplier ID"
            )

    try:
        restock = restock_service.create_restock(
            db=db,
            business_id=current_user.business_id,
            product_id=product_uuid,
            supplier_id=supplier_uuid,
            quantity=request.quantity,
            buying_cost=request.buying_cost,
            reference_number=request.reference_number,
            notes=request.notes,
            user_id=current_user.id
        )

        db.commit()

        return api_response(
            data={
                "restock_id": str(restock.id),
                "product_id": str(product_uuid)
            },
            message="Inventory restocked successfully."
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )