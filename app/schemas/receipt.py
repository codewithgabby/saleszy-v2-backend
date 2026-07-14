from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


class ReceiptItem(BaseModel):
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal


class ReceiptData(BaseModel):
    # Business
    business_name: str
    business_address: Optional[str] = None
    business_phone: Optional[str] = None
    business_email: Optional[str] = None
    business_logo_url: Optional[str] = None
    
    # Sale
    receipt_number: str
    cashier_name: str
    customer_name: Optional[str] = None
    items: List[ReceiptItem]
    
    # Totals
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    grand_total: Decimal
    
    # Payment
    payment_method: str
    cash_received: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    
    # Meta
    date: datetime
    currency_symbol: str = "₦"
    receipt_footer: Optional[str] = None
    tax_rate: Optional[Decimal] = None


class ReceiptResponse(BaseModel):
    receipt_number: str
    html: str
    format: str