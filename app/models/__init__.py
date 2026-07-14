from app.db.database import Base
from app.models.base import BaseModel
from sqlalchemy import Column, String, Boolean, JSON, DECIMAL, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# --- BUSINESS MODEL ---
class Business(BaseModel):
    __tablename__ = "businesses"
    
    legal_name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)

    settings = relationship("BusinessSettings", backref="business", uselist=False)

# --- BUSINESS SETTINGS MODEL ---
class BusinessSettings(BaseModel):
    __tablename__ = "business_settings"
    
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    timezone = Column(String(50), default="Africa/Lagos")
    language = Column(String(10), default="en")
    currency_symbol = Column(String(5), default="₦")
    receipt_width = Column(DECIMAL(5,2), default=80.00)
    tax_rate = Column(DECIMAL(5,2), default=0.00)
    branding = Column(JSON, default={})

# --- USER MODEL ---
class User(BaseModel):
    __tablename__ = "users"
    
    business_id = Column(UUID(as_uuid=True), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="owner")
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

# --- CATEGORY MODEL ---
class Category(BaseModel):
    __tablename__ = "categories"
    
    business_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    
    products = relationship("Product", back_populates="category")

# --- PRODUCT MODEL ---
class Product(BaseModel):
    __tablename__ = "products"
    
    business_id = Column(UUID(as_uuid=True), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=True)
    
    name = Column(String(255), nullable=False)
    base_unit = Column(String(50), nullable=False, default="Unit")  # e.g., "Loaf", "Bottle", "Kg", "Egg"
    sku = Column(String(100), nullable=True, unique=True)
    barcode = Column(String(100), nullable=True, unique=True)
    price = Column(DECIMAL(12,2), nullable=False)
    image_key = Column(String(255), nullable=True)
    low_stock_threshold = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    
    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    selling_units = relationship("SellingUnit", back_populates="product", cascade="all, delete-orphan")

# --- INVENTORY MODEL ---
class Inventory(BaseModel):
    __tablename__ = "inventory"
    
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    available_quantity = Column(DECIMAL(12,3), default=0.000)
    reserved_quantity = Column(DECIMAL(12,3), default=0.000)
    damaged_quantity = Column(DECIMAL(12,3), default=0.000)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    product = relationship("Product", back_populates="inventory")

# --- SELLING UNIT MODEL ---
class SellingUnit(BaseModel):
    __tablename__ = "selling_units"
    
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    base_unit_quantity = Column(DECIMAL(18,6), nullable=False, default=1.0)
    selling_price = Column(DECIMAL(12,2), nullable=True)  # Null = use product.price
    barcode = Column(String(100), nullable=True)
    sku = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    is_direct_sell = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    product = relationship("Product", back_populates="selling_units")
    sale_items = relationship("SaleItem", back_populates="selling_unit")


# --- STOCK MOVEMENT MODEL ---
class StockMovement(BaseModel):
    __tablename__ = "stock_movements"
    
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    movement_type = Column(String(30), nullable=False)  # SALE, RESTOCK, VOID, DAMAGE, RETURN, MANUAL_ADJUSTMENT, INITIAL_STOCK
    quantity = Column(DECIMAL(18, 6), nullable=False)   # Positive = add, Negative = deduct
    quantity_after = Column(DECIMAL(18, 6), nullable=False)  # Running balance after movement
    reference_type = Column(String(50), nullable=True)  # "sale", "inventory", "manual"
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # ID of related sale, etc.
    notes = Column(String(255), nullable=True)

# --- CUSTOMER MODEL ---
class Customer(BaseModel):
    __tablename__ = "customers"
    
    business_id = Column(UUID(as_uuid=True), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

# --- SUPPLIER MODEL ---
class Supplier(BaseModel):
    __tablename__ = "suppliers"
    
    business_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)    

# --- SALE MODEL ---
class Sale(BaseModel):
    __tablename__ = "sales"
    
    business_id = Column(UUID(as_uuid=True), nullable=False)
    cashier_id = Column(UUID(as_uuid=True), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    
    subtotal = Column(DECIMAL(12,2), nullable=False)
    tax = Column(DECIMAL(12,2), default=0.00)
    discount = Column(DECIMAL(12,2), default=0.00)
    grand_total = Column(DECIMAL(12,2), nullable=False)
    
    payment_method = Column(String(20), nullable=False)
    cash_received = Column(DECIMAL(12,2), nullable=True)
    change_given = Column(DECIMAL(12,2), nullable=True)
    
    status = Column(String(20), default="completed")
    receipt_number = Column(String(50), unique=True, nullable=False)
    
    void_reason = Column(String(255), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    shift_id = Column(UUID(as_uuid=True), nullable=True)  # Future shift management
    
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    customer = relationship("Customer")

# --- SALE ITEM MODEL ---
class SaleItem(BaseModel):
    __tablename__ = "sale_items"
    
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    selling_unit_id = Column(UUID(as_uuid=True), ForeignKey("selling_units.id"), nullable=True)
    selling_unit_name = Column(String(100), nullable=True)          # Snapshot: "Carton", "Half Loaf"
    quantity = Column(DECIMAL(12,3), nullable=False)
    base_unit_quantity_used = Column(DECIMAL(18,6), nullable=False, default=1.0)  # Snapshot
    unit_price = Column(DECIMAL(12,2), nullable=False)
    total_price = Column(DECIMAL(12,2), nullable=False)
    
    sale = relationship("Sale", back_populates="items")
    selling_unit = relationship("SellingUnit", back_populates="sale_items")

# --- ACTIVITY LOG MODEL ---
class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"
    
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    log_metadata = Column(JSON, default={})

# --- AUDIT LOG MODEL ---
class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    description = Column(String(500), nullable=True)