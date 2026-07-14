from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.repositories.category_repository import CategoryRepository
from decimal import Decimal
from uuid import UUID

class ProductService:
    def __init__(self):
        self.repo = ProductRepository()
        self.category_repo = CategoryRepository()

    def create_product(
        self, 
        db: Session, 
        business_id: UUID, 
        name: str, 
        price: Decimal,
        base_unit: str = "Unit",
        category_id: UUID | None = None,
        sku: str | None = None,
        barcode: str | None = None,
        image_key: str | None = None,
        low_stock_threshold: int = 5
    ):
        # Validate Category exists if provided
        if category_id:
            category = self.category_repo.get_by_id(db, category_id)
            if not category:
                raise ValueError("Category does not exist.")

        # Check for duplicate SKU
        if sku:
            existing = self.repo.get_by_sku(db, business_id, sku)
            if existing:
                raise ValueError("A product with this SKU already exists.")

        # Check for duplicate Barcode
        if barcode:
            existing = self.repo.get_by_barcode(db, business_id, barcode)
            if existing:
                raise ValueError("A product with this Barcode already exists.")

        return self.repo.create_product_with_inventory(
            db, business_id, name, price, category_id, sku, barcode, image_key, low_stock_threshold, base_unit
        )

    def get_products(self, db: Session, business_id: UUID):
        return self.repo.get_all(db, business_id)

    def search_products(self, db: Session, business_id: UUID, query: str):
        return self.repo.search_products(db, business_id, query)