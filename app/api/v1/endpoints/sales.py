from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import Sale, User
from app.services.sales_service import SalesService
from app.core.response import api_response

router = APIRouter(prefix="/sales", tags=["Sales"])
service = SalesService()

# --- Schemas ---
class SaleItemInput(BaseModel):
    selling_unit_id: str
    quantity: Decimal

class SaleCreate(BaseModel):
    items: List[SaleItemInput]
    payment_method: str = Field(..., description="cash, transfer, pos")
    customer_id: Optional[str] = None
    cash_received: Optional[Decimal] = None
    discount: Decimal = Decimal('0.00')
    discount_type: Optional[str] = None  # PERCENTAGE, FIXED
    discount_reason: Optional[str] = None

class VoidRequest(BaseModel):
    void_reason: str = Field(..., min_length=5, max_length=255)

class SaleItemResponse(BaseModel):
    product_id: str
    selling_unit_name: Optional[str] = None
    quantity: float
    base_unit_quantity_used: Optional[float] = None
    unit_price: float
    total_price: float

class SaleResponse(BaseModel):
    id: str
    receipt_number: str
    subtotal: float
    tax: float
    discount: float
    grand_total: float
    payment_method: str
    cash_received: Optional[float] = None
    change_given: Optional[float] = None
    status: str
    cashier_id: str
    customer_id: Optional[str] = None
    items: List[SaleItemResponse]
    void_reason: Optional[str] = None
    voided_at: Optional[str] = None
    created_at: str

# --- Helper Functions ---
def _format_sale_response(sale) -> dict:
    return {
        "id": str(sale.id),
        "receipt_number": sale.receipt_number,
        "subtotal": float(sale.subtotal),
        "tax": float(sale.tax),
        "discount": float(sale.discount),
        "grand_total": float(sale.grand_total),
        "payment_method": sale.payment_method,
        "cash_received": float(sale.cash_received) if sale.cash_received else None,
        "change_given": float(sale.change_given) if sale.change_given else None,
        "status": sale.status,
        "cashier_id": str(sale.cashier_id),
        "cashier_name": getattr(sale, 'cashier_name', None),
        "customer_id": str(sale.customer_id) if sale.customer_id else None,
        "customer_name": sale.customer.full_name if sale.customer else None,
        "shift_id": str(sale.shift_id) if sale.shift_id else None,
        "items": [
            {
                "sale_item_id": str(item.id),
                "product_id": str(item.product_id),
                "product_name": getattr(item, 'product_name', None) or (item.selling_unit_name or 'Item'),
                "selling_unit_name": item.selling_unit_name,
                "quantity": float(item.quantity),
                "base_unit_quantity_used": float(item.base_unit_quantity_used) if item.base_unit_quantity_used else None,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "returned_quantity": float(item.returned_quantity) if item.returned_quantity else 0,
            } for item in sale.items
        ],
        "void_reason": sale.void_reason,
        "voided_at": sale.voided_at.isoformat() if sale.voided_at else None,
        "created_at": sale.created_at.isoformat()
    }

# --- Routes ---
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sale(
    request: SaleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Discount permission: cashiers cannot discount, managers limited
    if request.discount > 0 and current_user.role == "cashier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cashiers cannot apply discounts. Ask a manager."
        )

    try:
        sale = service.process_sale(
            db,
            current_user.business_id,
            current_user.id,
            request.customer_id,
            [item.model_dump() for item in request.items],
            request.payment_method,
            request.cash_received,
            request.discount,
            request.discount_type,
            request.discount_reason,
        )
        db.commit()
        
        return api_response(
            data=_format_sale_response(sale),
            message="Sale completed successfully"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{sale_id}")
async def get_sale(
    sale_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from uuid import UUID
    try:
        sale_uuid = UUID(sale_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sale ID format")
    
    sale = service.get_sale(db, sale_uuid, current_user.business_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    
    return api_response(
        data=_format_sale_response(sale),
        message="Sale retrieved successfully"
    ) 

@router.get("/receipt/{receipt_number}")
async def get_sale_by_receipt(
    receipt_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(
        Sale.business_id == current_user.business_id,
        Sale.receipt_number == receipt_number
    ).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    return api_response(
        data=_format_sale_response(sale),
        message="Sale retrieved"
    )

@router.get("/")
async def list_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sales = service.get_sales(
        db,
        current_user.business_id,
        skip=skip,
        limit=limit,
        status=status,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date
    )
    
    return api_response(
        data=[_format_sale_response(sale) for sale in sales],
        message=f"Retrieved {len(sales)} sales"
    )

@router.get("/recent/list")
async def get_recent_sales(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sales = service.get_recent_sales(db, current_user.business_id, limit)
    
    return api_response(
        data=[_format_sale_response(sale) for sale in sales],
        message=f"Retrieved {len(sales)} recent sales"
    )

@router.post("/{sale_id}/void")
async def void_sale(
    sale_id: str,
    request: VoidRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from uuid import UUID
    try:
        sale_uuid = UUID(sale_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sale ID format")
    
    try:
        voided_sale = service.void_sale(db, sale_uuid, current_user.business_id, request.void_reason)
        db.commit()
        
        return api_response(
            data=_format_sale_response(voided_sale),
            message="Sale voided successfully. Inventory restored."
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/summary/payments")
async def get_payment_summary(
    date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = service.get_payment_summary(db, current_user.business_id, date)
    
    return api_response(
        data=summary,
        message="Payment summary retrieved successfully"
    )