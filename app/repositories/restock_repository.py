from sqlalchemy.orm import Session
from app.models import Restock
import uuid


class RestockRepository:

    def create(
        self,
        db: Session,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        supplier_id: uuid.UUID | None,
        received_quantity,
        buying_cost,
        reference_number,
        notes,
        received_by_user_id: uuid.UUID
    ) -> Restock:

        restock = Restock(
            business_id=business_id,
            product_id=product_id,
            supplier_id=supplier_id,
            received_quantity=received_quantity,
            buying_cost=buying_cost,
            reference_number=reference_number,
            notes=notes,
            received_by_user_id=received_by_user_id
        )

        db.add(restock)
        db.flush()

        return restock

    def get_latest_restock(
        self,
        db: Session,
        product_id: uuid.UUID,
    ) -> Restock | None:

        return (
            db.query(Restock)
            .filter(Restock.product_id == product_id)
            .order_by(Restock.created_at.desc())
            .first()
        )