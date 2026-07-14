from decimal import Decimal
from datetime import datetime
from typing import Optional
from jinja2 import Template
import uuid


class ReceiptService:
    
    def __init__(self):
        self._init_templates()
    
    def _init_templates(self):
        """Initialize receipt HTML templates."""
        
        self.thermal_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Courier New', monospace; 
            font-size: 12px; 
            width: 80mm;
            padding: 8px;
            color: #000;
        }
        .header { text-align: center; margin-bottom: 8px; }
        .business-name { font-size: 14px; font-weight: bold; }
        .business-info { font-size: 11px; margin-top: 2px; }
        .divider { border-top: 1px dashed #000; margin: 8px 0; }
        .meta { font-size: 11px; }
        .meta-row { display: flex; justify-content: space-between; }
        table { width: 100%; border-collapse: collapse; margin: 8px 0; }
        th { text-align: left; font-size: 11px; border-bottom: 1px solid #000; padding: 2px 0; }
        td { font-size: 11px; padding: 2px 0; }
        .right { text-align: right; }
        .totals { margin-top: 8px; }
        .total-row { display: flex; justify-content: space-between; font-size: 11px; margin: 2px 0; }
        .grand-total { font-size: 14px; font-weight: bold; margin-top: 4px; }
        .payment { margin-top: 8px; font-size: 11px; }
        .footer { text-align: center; margin-top: 12px; font-size: 11px; }
    </style>
</head>
<body>
    <div class="header">
        {% if data.business_logo_url %}
        <img src="{{ data.business_logo_url }}" alt="Logo" style="max-width: 60px; margin-bottom: 4px;">
        {% endif %}
        <div class="business-name">{{ data.business_name }}</div>
        {% if data.business_address %}
        <div class="business-info">{{ data.business_address }}</div>
        {% endif %}
        {% if data.business_phone %}
        <div class="business-info">Tel: {{ data.business_phone }}</div>
        {% endif %}
    </div>
    
    <div class="divider"></div>
    
    <div class="meta">
        <div class="meta-row">
            <span>Receipt: {{ data.receipt_number }}</span>
        </div>
        <div class="meta-row">
            <span>Date: {{ data.date }}</span>
        </div>
        <div class="meta-row">
            <span>Cashier: {{ data.cashier_name }}</span>
        </div>
        {% if data.customer_name %}
        <div class="meta-row">
            <span>Customer: {{ data.customer_name }}</span>
        </div>
        {% endif %}
    </div>
    
    <div class="divider"></div>
    
    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th class="right">Qty</th>
                <th class="right">Price</th>
                <th class="right">Total</th>
            </tr>
        </thead>
        <tbody>
                        {% for item in data.line_items %}
            <tr>
                <td>{{ item.product_name }}</td>
                <td class="right">{{ item.quantity }}</td>
                <td class="right">{{ data.currency_symbol }}{{ "%.2f"|format(item.unit_price) }}</td>
                <td class="right">{{ data.currency_symbol }}{{ "%.2f"|format(item.total_price) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="divider"></div>
    
    <div class="totals">
        <div class="total-row">
            <span>Subtotal</span>
            <span>{{ data.currency_symbol }}{{ "%.2f"|format(data.subtotal) }}</span>
        </div>
        {% if data.tax > 0 %}
        <div class="total-row">
            <span>Tax ({{ "%.1f"|format(data.tax_rate or 0) }}%)</span>
            <span>{{ data.currency_symbol }}{{ "%.2f"|format(data.tax) }}</span>
        </div>
        {% endif %}
        {% if data.discount > 0 %}
        <div class="total-row">
            <span>Discount</span>
            <span>-{{ data.currency_symbol }}{{ "%.2f"|format(data.discount) }}</span>
        </div>
        {% endif %}
        <div class="total-row grand-total">
            <span>TOTAL</span>
            <span>{{ data.currency_symbol }}{{ "%.2f"|format(data.grand_total) }}</span>
        </div>
    </div>
    
    <div class="divider"></div>
    
    <div class="payment">
        <div>Payment: {{ data.payment_method | upper }}</div>
        {% if data.cash_received is not none %}
        <div class="meta-row">
            <span>Cash Received:</span>
            <span>{{ data.currency_symbol }}{{ "%.2f"|format(data.cash_received) }}</span>
        </div>
        <div class="meta-row">
            <span>Change:</span>
            <span>{{ data.currency_symbol }}{{ "%.2f"|format(data.change_given) }}</span>
        </div>
        {% endif %}
    </div>
    
    <div class="divider"></div>
    
    <div class="footer">
        <div>{{ data.receipt_footer or 'Thank you for your purchase!' }}</div>
    </div>
</body>
</html>
        """)
        
        self.a4_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; 
            font-size: 14px; 
            max-width: 210mm;
            padding: 20mm;
            color: #0F172A;
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: flex-start;
            margin-bottom: 24px;
        }
        .business-name { font-size: 24px; font-weight: 700; color: #0F172A; }
        .business-info { font-size: 13px; color: #475569; margin-top: 4px; }
        .receipt-label { 
            font-size: 32px; 
            font-weight: 700; 
            color: #2563EB; 
            text-transform: uppercase; 
            letter-spacing: 2px;
        }
        .meta-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }
        .meta-item { }
        .meta-label { font-size: 11px; color: #64748B; text-transform: uppercase; letter-spacing: 1px; }
        .meta-value { font-size: 14px; font-weight: 500; color: #0F172A; }
        
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 24px 0;
        }
        th { 
            text-align: left; 
            font-size: 11px; 
            color: #64748B; 
            text-transform: uppercase; 
            letter-spacing: 1px;
            border-bottom: 2px solid #E2E8F0; 
            padding: 12px 8px;
        }
        td { 
            font-size: 14px; 
            padding: 12px 8px; 
            border-bottom: 1px solid #F1F5F9;
            color: #0F172A;
        }
        .right { text-align: right; }
        .totals-section {
            display: flex;
            justify-content: flex-end;
            margin: 24px 0;
        }
        .totals-table { width: 300px; }
        .totals-table td { 
            padding: 6px 8px; 
            font-size: 14px; 
            border: none;
        }
        .totals-table .total-row td { 
            font-size: 18px; 
            font-weight: 700; 
            border-top: 2px solid #0F172A;
            padding-top: 12px;
        }
        .payment-section {
            margin: 24px 0;
            padding: 16px;
            background: #F8FAFC;
            border-radius: 8px;
        }
        .footer { 
            text-align: center; 
            margin-top: 40px; 
            padding-top: 20px;
            border-top: 1px solid #E2E8F0;
            font-size: 12px;
            color: #64748B;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            {% if data.business_logo_url %}
            <img src="{{ data.business_logo_url }}" alt="Logo" style="max-height: 60px; margin-bottom: 8px;">
            {% endif %}
            <div class="business-name">{{ data.business_name }}</div>
            {% if data.business_address %}
            <div class="business-info">{{ data.business_address }}</div>
            {% endif %}
            {% if data.business_phone %}
            <div class="business-info">Tel: {{ data.business_phone }}</div>
            {% endif %}
            {% if data.business_email %}
            <div class="business-info">{{ data.business_email }}</div>
            {% endif %}
        </div>
        <div class="receipt-label">Receipt</div>
    </div>
    
    <div class="meta-grid">
        <div class="meta-item">
            <div class="meta-label">Receipt Number</div>
            <div class="meta-value">{{ data.receipt_number }}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Date & Time</div>
            <div class="meta-value">{{ data.date }}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Cashier</div>
            <div class="meta-value">{{ data.cashier_name }}</div>
        </div>
        {% if data.customer_name %}
        <div class="meta-item">
            <div class="meta-label">Customer</div>
            <div class="meta-value">{{ data.customer_name }}</div>
        </div>
        {% endif %}
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th class="right">Quantity</th>
                <th class="right">Unit Price</th>
                <th class="right">Total</th>
            </tr>
        </thead>
        <tbody>
                        {% for item in data.line_items %}
            <tr>
                <td>{{ item.product_name }}</td>
                <td class="right">{{ item.quantity }}</td>
                <td class="right">{{ data.currency_symbol }}{{ "%.2f"|format(item.unit_price) }}</td>
                <td class="right">{{ data.currency_symbol }}{{ "%.2f"|format(item.total_price) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="totals-section">
        <table class="totals-table">
            <tr>
                <td>Subtotal</td>
                <td class="right">{{ data.currency_symbol }}{{ "%.2f"|format(data.subtotal) }}</td>
            </tr>
            {% if data.tax > 0 %}
            <tr>
                <td>Tax ({{ "%.1f"|format(data.tax_rate or 0) }}%)</td>
                <td class="right">{{ data.currency_symbol }}{{ "%.2f"|format(data.tax) }}</td>
            </tr>
            {% endif %}
            {% if data.discount > 0 %}
            <tr>
                <td>Discount</td>
                <td class="right">-{{ data.currency_symbol }}{{ "%.2f"|format(data.discount) }}</td>
            </tr>
            {% endif %}
            <tr class="total-row">
                <td>Grand Total</td>
                <td class="right">{{ data.currency_symbol }}{{ "%.2f"|format(data.grand_total) }}</td>
            </tr>
        </table>
    </div>
    
    <div class="payment-section">
        <div class="meta-label">Payment Method</div>
        <div class="meta-value" style="font-size: 16px; text-transform: uppercase;">{{ data.payment_method }}</div>
        {% if data.cash_received is not none %}
        <div style="margin-top: 8px; display: flex; gap: 24px;">
            <div>
                <div class="meta-label">Cash Received</div>
                <div class="meta-value">{{ data.currency_symbol }}{{ "%.2f"|format(data.cash_received) }}</div>
            </div>
            <div>
                <div class="meta-label">Change</div>
                <div class="meta-value">{{ data.currency_symbol }}{{ "%.2f"|format(data.change_given) }}</div>
            </div>
        </div>
        {% endif %}
    </div>
    
    <div class="footer">
        <p>{{ data.receipt_footer or 'Thank you for your purchase!' }}</p>
    </div>
</body>
</html>
        """)
    
    def generate(
        self,
        data: dict,
        format: str = "thermal"  # thermal, a4
    ) -> str:
        """Generate receipt HTML."""
        if format == "a4":
            return self.a4_template.render(data=data)
        return self.thermal_template.render(data=data)
    
    def build_receipt_data(
        self,
        sale,
        business,
        product_names: dict
    ) -> dict:
        """Build receipt data dictionary from sale and business objects."""
        branding = {}
        if business.settings and business.settings.branding:
            branding = business.settings.branding
        
        # Convert SQLAlchemy items to plain dicts
        items = []
        for item in sale.items:
            # Build display name: "Carton" or "Half Loaf" from the snapshot
            display_name = item.selling_unit_name if item.selling_unit_name else product_names.get(str(item.product_id), "Product")
            
            items.append({
                "product_name": display_name,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price)
            })
        
        return {
            "business_name": branding.get("store_name", business.legal_name),
            "business_address": branding.get("address"),
            "business_phone": branding.get("phone"),
            "business_email": business.email,
            "business_logo_url": branding.get("logo_url"),
            "receipt_number": sale.receipt_number,
            "cashier_name": "Cashier",
            "customer_name": sale.customer.full_name if sale.customer else None,
            "line_items": items,
            "subtotal": float(sale.subtotal),
            "tax": float(sale.tax),
            "discount": float(sale.discount),
            "grand_total": float(sale.grand_total),
            "payment_method": sale.payment_method,
            "cash_received": float(sale.cash_received) if sale.cash_received else None,
            "change_given": float(sale.change_given) if sale.change_given else None,
            "date": sale.created_at.strftime('%d/%m/%Y %H:%M') if sale.created_at else "",
            "currency_symbol": business.settings.currency_symbol if business.settings else "₦",
            "receipt_footer": branding.get("receipt_footer", "Thank you for your purchase!"),
            "tax_rate": float(business.settings.tax_rate) if business.settings else 0
        }