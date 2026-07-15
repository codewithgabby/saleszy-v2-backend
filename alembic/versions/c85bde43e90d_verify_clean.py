"""verify_clean

Revision ID: c85bde43e90d
Revises: d486e64515bc
Create Date: 2026-07-13 00:53:18.485140

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c85bde43e90d'
down_revision: Union[str, None] = 'd486e64515bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass