from sqlalchemy.orm import Session
from app.repositories.sales_repository import SalesRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.business_repository import BusinessRepository
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
import uuid
from app.services.activity_service import ActivityService
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService, StockMovementType
from app.services.selling_unit_service import SellingUnitService

class SalesService:
    def __init__(self):
        self.repo = SalesRepository()
        self.product_repo = ProductRepository()
        self.inventory_repo = InventoryRepository()
        self.business_repo = BusinessRepository()
        self.activity_service = ActivityService()
        self.audit_service = AuditService()
        self.selling_unit_service = SellingUnitService()
        self.inventory_service = InventoryService()

    def _generate_receipt_number(self, business_id: uuid.UUID) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"SLS-{timestamp}"

    def _get_tax_rate(self, db: Session, business_id: uuid.UUID) -> Decimal:
        business = self.business_repo.get_business_with_settings(db, business_id)
        if business and business.settings:
            return Decimal(str(business.settings.tax_rate)) / Decimal('100')
        return Decimal('0.00')

    def process_sale(
        self, 
        db: Session, 
        business_id: uuid.UUID, 
        cashier_id: uuid.UUID,
        customer_id: uuid.UUID | None,
        items: list,
        payment_method: str,
        cash_received: Optional[Decimal] = None,
        discount: Decimal = Decimal('0.00')
    ):
        if not items:
            raise ValueError("Sale must contain at least one item.")

        subtotal = Decimal('0.00')
        processed_items = []

        # 1. Validate all products and calculate totals
        for item in items:
            selling_unit = self.selling_unit_service.get_unit(db, uuid.UUID(item["selling_unit_id"]))
            if not selling_unit:
                raise ValueError(f"Selling unit with ID {item['selling_unit_id']} not found.")
            
            product = self.product_repo.get_by_id(db, selling_unit.product_id)
            if not product:
                raise ValueError(f"Product not found for selling unit.")

            unit_price = self.selling_unit_service.get_effective_price(db, selling_unit.id)
            base_units_to_deduct = selling_unit.base_unit_quantity * item["quantity"]
            
            # Check stock with row lock to prevent overselling
            inventory = self.inventory_repo.get_by_product_id(db, selling_unit.product_id, with_lock=True)
            if not inventory or inventory.available_quantity < base_units_to_deduct:
                raise ValueError(f"Insufficient stock for product: {product.name}")

            line_total = unit_price * item["quantity"]
            subtotal += line_total
            
            processed_items.append({
                "product_id": selling_unit.product_id,
                "selling_unit_id": selling_unit.id,
                "selling_unit_name": selling_unit.name,
                "quantity": item["quantity"],
                "base_unit_quantity_used": selling_unit.base_unit_quantity,
                "unit_price": unit_price,
                "total_price": line_total
            })

        # 2. Calculate Tax and Grand Total
        tax_rate = self._get_tax_rate(db, business_id)
        tax = subtotal * tax_rate
        grand_total = subtotal + tax - discount

        if grand_total < 0:
            raise ValueError("Discount cannot exceed the subtotal.")

        # 3. Calculate change for cash payments
        change_given = None
        if payment_method == "cash" and cash_received:
            if cash_received < grand_total:
                raise ValueError("Cash received is less than the grand total.")
            change_given = cash_received - grand_total

        # 4. Generate Receipt Number
        receipt_number = self._generate_receipt_number(business_id)

        # 5. Save Sale (without inventory deduction - that's now in step 6)
        sale = self.repo.create_sale(
            db,
            business_id,
            cashier_id,
            customer_id,
            subtotal,
            tax,
            discount,
            grand_total,
            payment_method,
            receipt_number,
            cash_received,
            change_given,
            processed_items
        )

        # 6. Deduct inventory through centralized service (with stock ledger)
        for item in processed_items:
            deduction_qty = Decimal(str(item["base_unit_quantity_used"])) * item["quantity"]
            self.inventory_service.adjust_stock(
                db,
                business_id,
                item["product_id"],
                cashier_id,
                -deduction_qty,
                StockMovementType.SALE,
                reference_type="sale",
                reference_id=sale.id,
                notes=f"Sale {sale.receipt_number}: {item['selling_unit_name']} x {item['quantity']}"
            )

        # 7. Log activity
        self.activity_service.log_sale_completed(
            db, business_id, cashier_id, sale.id, float(grand_total)
        )

        return sale

    def get_sale(self, db: Session, sale_id: uuid.UUID, business_id: uuid.UUID) -> Optional[dict]:
        sale = self.repo.get_sale_by_id(db, sale_id)
        if not sale or sale.business_id != business_id:
            return None
        return sale

    def get_sales(
        self, 
        db: Session, 
        business_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        payment_method: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> List:
        return self.repo.get_sales_list(db, business_id, skip, limit, status, payment_method, start_date, end_date)

    def get_recent_sales(self, db: Session, business_id: uuid.UUID, limit: int = 20) -> List:
        return self.repo.get_recent_sales(db, business_id, limit)

    def void_sale(self, db: Session, sale_id: uuid.UUID, business_id: uuid.UUID, void_reason: str):
        sale = self.repo.get_sale_by_id(db, sale_id)
        if not sale:
            raise ValueError("Sale not found.")
        if sale.business_id != business_id:
            raise ValueError("Sale does not belong to this business.")
        if sale.status != "completed":
            raise ValueError("Only completed sales can be voided.")
        
        # Void the sale (status update only, no inventory change here)
        voided_sale = self.repo.void_sale(db, sale_id, void_reason)

        # Restore inventory through centralized service (with stock ledger)
        for item in voided_sale.items:
            restore_qty = item.base_unit_quantity_used * item.quantity
            self.inventory_service.adjust_stock(
                db,
                business_id,
                item.product_id,
                sale.cashier_id,
                restore_qty,
                StockMovementType.VOID,
                reference_type="sale",
                reference_id=sale_id,
                notes=f"Void sale {sale.receipt_number}: {item.selling_unit_name} x {item.quantity}"
            )

        # Log activity and audit
        self.activity_service.log_sale_voided(db, business_id, sale.cashier_id, sale_id, void_reason)
        self.audit_service.log_sale_void(db, business_id, sale.cashier_id, sale_id, void_reason)
        
        return voided_sale

    def get_payment_summary(self, db: Session, business_id: uuid.UUID, date: datetime | None = None):
        return self.repo.get_payment_summary(db, business_id, date)