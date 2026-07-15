"""add_missing_indexes

Revision ID: d486e64515bc
Revises: 94bb656280ff
Create Date: 2026-07-13 00:45:59.693753

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd486e64515bc'
down_revision: Union[str, None] = '94bb656280ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    indexes_to_create = [
        ("ix_selling_units_product_id", "selling_units", "product_id"),
        ("ix_selling_units_name", "selling_units", "name"),
        ("ix_selling_units_barcode", "selling_units", "barcode"),
        ("ix_selling_units_sku", "selling_units", "sku"),
        ("ix_selling_units_display_order", "selling_units", "display_order"),
        ("ix_stock_movements_product_id", "stock_movements", "product_id"),
        ("ix_stock_movements_movement_type", "stock_movements", "movement_type"),
        ("ix_stock_movements_reference", "stock_movements", "reference_type, reference_id"),
    ]
    for index_name, table, columns in indexes_to_create:
        op.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})")


def downgrade() -> None:
    indexes_to_drop = [
        "ix_selling_units_product_id", "ix_selling_units_name", "ix_selling_units_barcode",
        "ix_selling_units_sku", "ix_selling_units_display_order",
        "ix_stock_movements_product_id", "ix_stock_movements_movement_type", "ix_stock_movements_reference",
    ]
    for index_name in indexes_to_drop:
        op.execute(f"DROP INDEX IF EXISTS {index_name}")