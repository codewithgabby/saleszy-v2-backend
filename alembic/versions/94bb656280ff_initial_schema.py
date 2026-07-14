"""initial_schema

Revision ID: 94bb656280ff
Revises: 
Create Date: 2026-07-13 00:44:24.885866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94bb656280ff'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old indexes (if they exist from previous manual creation)
    op.execute("DROP INDEX IF EXISTS idx_activity_action")
    op.execute("DROP INDEX IF EXISTS idx_activity_business")
    op.create_index(op.f('ix_activity_logs_business_id'), 'activity_logs', ['business_id'], unique=False)
    
    op.execute("DROP INDEX IF EXISTS idx_audit_business")
    op.execute("DROP INDEX IF EXISTS idx_audit_target")
    op.create_index(op.f('ix_audit_logs_business_id'), 'audit_logs', ['business_id'], unique=False)
    
    op.execute("DROP INDEX IF EXISTS ix_selling_units_barcode")
    op.execute("DROP INDEX IF EXISTS ix_selling_units_display_order")
    op.execute("DROP INDEX IF EXISTS ix_selling_units_name")
    op.execute("DROP INDEX IF EXISTS ix_selling_units_sku")
    
    op.execute("DROP INDEX IF EXISTS idx_stock_movements_business")
    op.execute("DROP INDEX IF EXISTS idx_stock_movements_product")
    op.execute("DROP INDEX IF EXISTS idx_stock_movements_reference")
    op.execute("DROP INDEX IF EXISTS idx_stock_movements_type")
    op.create_index(op.f('ix_stock_movements_business_id'), 'stock_movements', ['business_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_stock_movements_business_id'), table_name='stock_movements')
    op.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements (movement_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements (reference_type, reference_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements (product_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_business ON stock_movements (business_id)")
    
    op.execute("CREATE INDEX IF NOT EXISTS ix_selling_units_sku ON selling_units (sku)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_selling_units_name ON selling_units (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_selling_units_display_order ON selling_units (display_order)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_selling_units_barcode ON selling_units (barcode)")
    
    op.drop_index(op.f('ix_audit_logs_business_id'), table_name='audit_logs')
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs (target_type, target_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_business ON audit_logs (business_id)")
    
    op.drop_index(op.f('ix_activity_logs_business_id'), table_name='activity_logs')
    op.execute("CREATE INDEX IF NOT EXISTS idx_activity_business ON activity_logs (business_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_logs (action)")