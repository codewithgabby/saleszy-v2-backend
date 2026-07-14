from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from uuid import UUID
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.inventory_service import InventoryService, StockMovementType
from app.core.response import api_response

router = APIRouter(prefix="/inventory", tags=["Inventory"])
inventory_service = InventoryService()

class AddStockRequest(BaseModel):
    product_id: str
    quantity: Decimal


@router.post("/add-stock", status_code=status.HTTP_200_OK)
async def add_stock(
    request: AddStockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        product_uuid = UUID(request.product_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")

    try:
        inventory = inventory_service.adjust_stock(
            db,
            current_user.business_id,
            product_uuid,
            current_user.id,
            request.quantity,
            StockMovementType.RESTOCK,
            reference_type="inventory",
            notes="Manual stock addition"
        )
        db.commit()
        
        return api_response(
            data={
                "product_id": str(product_uuid),
                "new_available_quantity": float(inventory.available_quantity)
            },
            message=f"Successfully added {request.quantity} stock"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))