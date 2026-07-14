from sqlalchemy.orm import Session
from app.models import Product, Inventory, Category, SellingUnit
from typing import Optional, List
import uuid
from decimal import Decimal

class ProductRepository:
    def get_by_sku(self, db: Session, business_id: uuid.UUID, sku: str) -> Optional[Product]:
        return db.query(Product).filter(
            Product.business_id == business_id,
            Product.sku == sku
        ).first()

    def get_by_barcode(self, db: Session, business_id: uuid.UUID, barcode: str) -> Optional[Product]:
        return db.query(Product).filter(
            Product.business_id == business_id,
            Product.barcode == barcode
        ).first()

    def get_by_id(self, db: Session, product_id: uuid.UUID) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()

    def get_all(self, db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Product]:
        return db.query(Product).filter(
            Product.business_id == business_id,
            Product.is_active == True
        ).offset(skip).limit(limit).all()

    def create_product_with_inventory(
        self, 
        db: Session, 
        business_id: uuid.UUID,
        name: str, 
        price: Decimal,
        category_id: uuid.UUID | None = None,
        sku: str | None = None,
        barcode: str | None = None,
        image_key: str | None = None,
        low_stock_threshold: int = 5,
        base_unit: str = "Unit"
    ) -> Product:
        # 1. Create the Product
        product = Product(
            business_id=business_id,
            name=name,
            base_unit=base_unit,
            price=price,
            category_id=category_id,
            sku=sku,
            barcode=barcode,
            image_key=image_key,
            low_stock_threshold=low_stock_threshold
        )
        db.add(product)
        db.flush()

        # 2. Create the Inventory record
        inventory = Inventory(
            product_id=product.id,
            available_quantity=Decimal('0.000'),
            reserved_quantity=Decimal('0.000'),
            damaged_quantity=Decimal('0.000')
        )
        db.add(inventory)
        db.flush()

        # 3. Create default SellingUnit
        default_unit = SellingUnit(
            product_id=product.id,
            name=base_unit,
            base_unit_quantity=Decimal('1.0'),
            selling_price=price,
            is_default=True,
            is_direct_sell=True,
            display_order=0
        )
        db.add(default_unit)
        db.flush()
        
        return product

    def search_products(self, db: Session, business_id: uuid.UUID, query: str) -> List[Product]:
        return db.query(Product).filter(
            Product.business_id == business_id,
            Product.is_active == True,
            Product.name.ilike(f"%{query}%")
        ).limit(20).all()