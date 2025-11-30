"""
Database migration: Add ProductHistory table.

Revision ID: add_product_history
Create Date: 2025-11-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_product_history'
down_revision = None  # Set to your latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    """Add product_history table."""
    op.create_table(
        'product_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_slug', sa.String(50), nullable=False, index=True),
        sa.Column('product_id', sa.String(255), nullable=False, index=True),
        sa.Column('current_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('original_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(1000), nullable=True),
        sa.Column('product_url', sa.String(1000), nullable=True),
        sa.Column('rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('review_count', sa.Integer, nullable=True),
        sa.Column('is_prime', sa.Boolean, default=False),
        sa.Column('extra_data', postgresql.JSONB, nullable=True),
        sa.Column('scraped_at', sa.DateTime, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Create composite indexes
    op.create_index(
        'ix_product_history_product',
        'product_history',
        ['store_slug', 'product_id']
    )


def downgrade():
    """Remove product_history table."""
    op.drop_index('ix_product_history_product', table_name='product_history')
    op.drop_table('product_history')
