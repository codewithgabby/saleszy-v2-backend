"""add_buying_cost_and_profit_to_sale_items

Revision ID: 39a0a6ee035d
Revises: 0b944694340a
Create Date: 2026-08-02 14:15:26.286299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39a0a6ee035d'
down_revision: Union[str, None] = '0b944694340a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sale_items",
        sa.Column(
            "buying_cost",
            sa.DECIMAL(12, 2),
            nullable=False,
            server_default="0.00"
        )
    )

    op.add_column(
        "sale_items",
        sa.Column(
            "profit",
            sa.DECIMAL(12, 2),
            nullable=False,
            server_default="0.00"
        )
    )

    # Remove the temporary defaults
    op.alter_column(
        "sale_items",
        "buying_cost",
        server_default=None
    )

    op.alter_column(
        "sale_items",
        "profit",
        server_default=None
    )


def downgrade() -> None:
    op.drop_column("sale_items", "profit")
    op.drop_column("sale_items", "buying_cost")
