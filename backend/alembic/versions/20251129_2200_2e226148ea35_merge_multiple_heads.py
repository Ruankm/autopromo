"""merge_multiple_heads

Revision ID: 2e226148ea35
Revises: 003_whatsapp_instances, add_product_history
Create Date: 2025-11-29 22:00:53.575973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e226148ea35'
down_revision: Union[str, None] = ('003_whatsapp_instances', 'add_product_history')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
