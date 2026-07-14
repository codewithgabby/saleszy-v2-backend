"""initial_schema

Revision ID: 94bb656280ff
Revises: 
Create Date: 2026-07-13 00:44:24.885866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


# revision identifiers, used by Alembic.
revision: str = '94bb656280ff'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables from models
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    # Drop all tables
    Base.metadata.drop_all(bind=op.get_bind())