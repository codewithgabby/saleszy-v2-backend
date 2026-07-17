from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

# Active sale statuses — single source of truth
ACTIVE_SALE_STATUSES = ["completed", "partially_returned"]

# Default payment methods
DEFAULT_PAYMENT_METHODS = ["cash", "transfer", "pos"]


class AnalyticsRepository:
    
    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------
    
    def _date_filter(self, query, model, start_date=None, end_date=None):
        """Apply date range filter to query. TODO: Use indexed datetime range for performance."""
        today = date.today()
        sd = start_date or today
        ed = end_date or today
        return query.filter(
            func.date(model.created_at) >= sd,
            func.date(model.created_at) <= ed,
        )
    
    def _build_sales_query(self, db: Session, business_id: uuid.UUID, start_date=None, end_date=None,
                           cashier_id=None, shift_id=None, category_id=None, customer_id=None,
                           supplier_id=None, payment_method=None):
        """Base query for all sales analytics. Every sales metric extends this."""
        from app.models import Sale
        query = db.query(Sale).filter(
            Sale.business_id == business_id,
            Sale.status.in_(ACTIVE_SALE_STATUSES),
        )
        query = self._date_filter(query, Sale, start_date, end_date)
        
        if cashier_id:
            query = query.filter(Sale.cashier_id == cashier_id)
        if shift_id:
            query = query.filter(Sale.shift_id == shift_id)
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        
        return query
    
    def _get_period(self, start_date=None, end_date=None):
        today = date.today()
        return {
            "start_date": (start_date or today).isoformat(),
            "end_date": (end_date or today).isoformat(),
        }
    
    # ---------------------------------------------------------------
    # Dashboard
    # ---------------------------------------------------------------
    
    def get_dashboard_summary(self, db: Session, business_id: uuid.UUID, start_date=None, end_date=None):
        from app.models import Sale, SaleItem, Product, Inventory, Customer, Return
        
        # Sales — extend base query for aggregation
        base = self._build_sales_query(db, business_id, start_date, end_date)
        sales_data = db.query(
            func.count(Sale.id).label("transactions"),
            func.coalesce(func.sum(Sale.subtotal), 0).label("revenue"),
            func.coalesce(func.sum(Sale.tax), 0).label("tax"),
            func.coalesce(func.sum(Sale.discount), 0).label("discounts"),
            func.coalesce(func.sum(Sale.grand_total), 0).label("net_revenue"),
        ).filter(Sale.id.in_(base.with_entities(Sale.id))).first()
        
        # Refunds
        refund_base = db.query(Return).filter(
            Return.business_id == business_id,
            Return.status == "COMPLETED",
        )
        refund_base = self._date_filter(refund_base, Return, start_date, end_date)
        refunds = db.query(func.coalesce(func.sum(Return.total_refund), 0)).filter(
            Return.id.in_(refund_base.with_entities(Return.id))
        ).scalar()
        
        # Items sold
        from app.models import SaleItem as SI
        items_base = db.query(SI).join(Sale, SI.sale_id == Sale.id).filter(
            Sale.id.in_(base.with_entities(Sale.id))
        )
        items_sold = db.query(func.coalesce(func.sum(SI.quantity), 0)).filter(
            SI.id.in_(items_base.with_entities(SI.id))
        ).scalar()
        
        # Payment breakdown — initialize all methods with zero
        payment_data = db.query(
            Sale.payment_method,
            func.count(Sale.id).label("count"),
            func.coalesce(func.sum(Sale.grand_total), 0).label("total"),
        ).filter(Sale.id.in_(base.with_entities(Sale.id))).group_by(Sale.payment_method).all()
        
        total_payments = sum(float(p.total) for p in payment_data)
        payments = {m: {"count": 0, "total": 0, "percentage": 0} for m in DEFAULT_PAYMENT_METHODS}
        for p in payment_data:
            pct = round((float(p.total) / total_payments) * 100, 1) if total_payments > 0 else 0
            payments[p.payment_method] = {"count": p.count, "total": p.total, "percentage": pct}
        
        # Inventory summary
        inventory_data = db.query(
            func.count(Product.id).label("total"),
            func.count(Product.id).filter(Inventory.available_quantity > Product.low_stock_threshold).label("in_stock"),
            func.count(Product.id).filter(Inventory.available_quantity > 0, Inventory.available_quantity <= Product.low_stock_threshold).label("low_stock"),
            func.count(Product.id).filter(Inventory.available_quantity <= 0).label("out_of_stock"),
        ).join(Inventory, Product.id == Inventory.product_id).filter(
            Product.business_id == business_id,
            Product.is_active == True,
        ).first()
        
        # New customers
        cust_base = db.query(Customer).filter(Customer.business_id == business_id)
        cust_base = self._date_filter(cust_base, Customer, start_date, end_date)
        new_customers = db.query(func.count(Customer.id)).filter(
            Customer.id.in_(cust_base.with_entities(Customer.id))
        ).scalar()
        
        gt = sales_data.net_revenue
        txns = sales_data.transactions
        avg = gt / txns if txns > 0 else 0
        
        return {
            "period": self._get_period(start_date, end_date),
            "sales": {
                "subtotal": sales_data.revenue,
                "tax": sales_data.tax,
                "discounts": sales_data.discounts,
                "refunds": refunds or 0,
                "grand_total": sales_data.net_revenue,
                "transactions": txns,
                "average_sale": avg,
                "items_sold": items_sold or 0,
            },
            "payments": payments,
            "inventory": {
                "in_stock": inventory_data.in_stock,
                "low_stock": inventory_data.low_stock,
                "out_of_stock": inventory_data.out_of_stock,
                "total_products": inventory_data.total,
            },
            "customers": {
                "new": new_customers,
            },
        }
    
    # ---------------------------------------------------------------
    # Products
    # ---------------------------------------------------------------
    
    def get_top_products(self, db: Session, business_id: uuid.UUID, limit: int = 10, start_date=None, end_date=None):
        from app.models import Sale, SaleItem, Product
        
        base = self._build_sales_query(db, business_id, start_date, end_date)
        
        results = db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(SaleItem.quantity).label("total_qty"),
            func.sum(SaleItem.total_price).label("total_revenue"),
            func.count(func.distinct(Sale.id)).label("times_sold"),
        ).join(Sale, SaleItem.sale_id == Sale.id).join(Product, SaleItem.product_id == Product.id).filter(
            Sale.id.in_(base.with_entities(Sale.id))
        ).group_by(Product.id, Product.name).order_by(func.sum(SaleItem.total_price).desc()).limit(limit).all()
        
        return [
            {
                "product_id": str(r.product_id),
                "product_name": r.product_name,
                "quantity_sold": r.total_qty,
                "revenue": r.total_revenue,
                "times_sold": r.times_sold,
            }
            for r in results
        ]
    
    # ---------------------------------------------------------------
    # Inventory
    # ---------------------------------------------------------------
    
    def get_inventory_value(self, db: Session, business_id: uuid.UUID):
        from app.models import Product, Inventory
        
        result = db.query(
            func.count(Product.id).label("total_products"),
            # TODO: Add cost_value and potential_profit when cost_price is available
            func.coalesce(func.sum(Inventory.available_quantity * Product.price), 0).label("selling_value"),
        ).join(Inventory, Product.id == Inventory.product_id).filter(
            Product.business_id == business_id,
            Product.is_active == True,
        ).first()
        
        return {
            "total_products": result.total_products,
            "selling_value": result.selling_value,
        }
    
    # ---------------------------------------------------------------
    # Financial
    # ---------------------------------------------------------------
    
    def get_financial(self, db: Session, business_id: uuid.UUID, start_date=None, end_date=None):
        from app.models import Sale
        
        base = self._build_sales_query(db, business_id, start_date, end_date)
        
        data = db.query(
            func.count(Sale.id).label("transactions"),
            func.coalesce(func.sum(Sale.subtotal), 0).label("revenue"),
            func.coalesce(func.sum(Sale.tax), 0).label("tax"),
            func.coalesce(func.sum(Sale.discount), 0).label("discounts"),
            func.coalesce(func.sum(Sale.grand_total), 0).label("net"),
        ).filter(Sale.id.in_(base.with_entities(Sale.id))).first()
        
        return {
            "period": self._get_period(start_date, end_date),
            "subtotal": data.revenue,
            "tax": data.tax,
            "discounts": data.discounts,
            "grand_total": data.net,
            "transactions": data.transactions,
            "profit_available": False,
        }