from fastapi import APIRouter
from app.api.v1.endpoints import auth, business, categories, products, customers, suppliers, sales, inventory, reports, receipts, selling_units

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(business.router)
router.include_router(categories.router)
router.include_router(products.router)
router.include_router(customers.router)
router.include_router(suppliers.router)
router.include_router(sales.router)
router.include_router(inventory.router)
router.include_router(reports.router)
router.include_router(receipts.router)
router.include_router(selling_units.router)