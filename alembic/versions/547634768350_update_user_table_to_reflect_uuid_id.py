"""Update user table to reflect uuid ID

Revision ID: 547634768350
Revises: 63e461c5ff75
Create Date: 2025-07-21 17:32:34.565353

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '547634768350'
down_revision: Union[str, Sequence[str], None] = '63e461c5ff75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'users',
        'id',
        existing_type=sa.VARCHAR(),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="id::uuid"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users',
        'id',
        existing_type=sa.UUID(),
        type_=sa.VARCHAR(),
        existing_nullable=False
    )
