"""add full_name to users

Revision ID: 002_add_full_name
Revises: 001_initial
Create Date: 2025-11-26 11:27:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_full_name'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full_name column to users table as nullable
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove full_name column
    op.drop_column('users', 'full_name')
