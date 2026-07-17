"""set_max_discount_default

Revision ID: d88d307ac9de
Revises: 8854db6a5086
Create Date: 2026-07-17 01:51:49.985874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd88d307ac9de'
down_revision: Union[str, None] = '8854db6a5086'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE business_settings SET max_discount_percent = 10 WHERE max_discount_percent IS NULL")
    op.alter_column('business_settings', 'max_discount_percent', nullable=False, server_default=sa.text('10'))

def downgrade() -> None:
    op.alter_column('business_settings', 'max_discount_percent', nullable=True, server_default=None)