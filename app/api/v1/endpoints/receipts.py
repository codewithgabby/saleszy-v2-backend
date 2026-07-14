from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.sales_service import SalesService
from app.services.receipt_service import ReceiptService
from app.services.business_service import BusinessService
from app.core.response import api_response
from uuid import UUID

router = APIRouter(prefix="/receipts", tags=["Receipts"])
sales_service = SalesService()
receipt_service = ReceiptService()
business_service = BusinessService()


def _get_product_names(db: Session, sale) -> dict:
    """Build a map of product_id -> product_name."""
    from app.models import Product
    product_ids = [item.product_id for item in sale.items]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    return {str(p.id): p.name for p in products}


@router.get("/{sale_id}")
async def get_receipt(
    sale_id: str,
    format: str = Query("thermal", pattern="^(thermal|a4)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a receipt for a completed sale."""
    try:
        sale_uuid = UUID(sale_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sale ID format")
    
    sale = sales_service.get_sale(db, sale_uuid, current_user.business_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    
    # Get business with branding
    business = business_service.get_business_profile(db, current_user.business_id)
    
    # Get product names
    product_names = _get_product_names(db, sale)
    
    # Build receipt data
    receipt_data = receipt_service.build_receipt_data(sale, business, product_names)
    
    # Override cashier name with actual user
    receipt_data["cashier_name"] = current_user.full_name
    
    # Generate HTML
    html = receipt_service.generate(receipt_data, format)
    
    return api_response(
        data={
            "receipt_number": sale.receipt_number,
            "format": format,
            "html": html
        },
        message="Receipt generated successfully"
    )