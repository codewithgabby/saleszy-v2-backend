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
        supplier_id: UUID | None = None,
        sku: str | None = None,
        barcode: str | None = None,
        image_key: str | None = None,
        low_stock_threshold: int = 5
    ):
        name = " ".join(name.strip().split())

        # Validate Category exists if provided
        if category_id:
            category = self.category_repo.get_by_id(db, category_id)
            if not category:
                raise ValueError("Category does not exist.")

        # Check for duplicate Product Name
        existing = self.repo.get_by_name(db, business_id, name)
        if existing:
            raise ValueError(
                 f'Product "{existing.name}" already exists.\n'
                 "Please edit the existing product instead of creating another one."
            )


        # Check for duplicate SKU
        if sku:
            existing = self.repo.get_by_sku(db, business_id, sku)
            if existing:
                raise ValueError(
                    f'SKU "{sku}" already exists.'
                )

        # Check for duplicate Barcode
        if barcode:
            existing = self.repo.get_by_barcode(db, business_id, barcode)
            if existing:
                raise ValueError(
                    f'Barcode "{barcode}" already exists.'
                )

        return self.repo.create_product_with_inventory(
    db,
    business_id,
    name,
    price,
    category_id,
    supplier_id,
    sku,
    barcode,
    image_key,
    low_stock_threshold,
    base_unit,
)

    def get_products(
        self,
        db: Session,
        business_id: UUID,
        status: str = "active"
):
        return self.repo.get_all(
            db=db,
            business_id=business_id,
            status=status
        )

    def search_products(self, db: Session, business_id: UUID, query: str):
        return self.repo.search_products(db, business_id, query)