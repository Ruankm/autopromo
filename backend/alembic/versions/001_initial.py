"""Initial migration - all tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-25 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('config_json', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create affiliate_tags table
    op.create_table('affiliate_tags',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('store_slug', sa.String(), nullable=False),
    sa.Column('tag_code', sa.String(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'store_slug', name='uq_user_store')
    )
    
    # Create group_sources table
    op.create_table('group_sources',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('platform', sa.String(), nullable=False),
    sa.Column('source_group_id', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create group_destinations table
    op.create_table('group_destinations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('platform', sa.String(), nullable=False),
    sa.Column('destination_group_id', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create offers table
    op.create_table('offers',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('source_platform', sa.String(), nullable=True),
    sa.Column('source_group_id', sa.String(), nullable=True),
    sa.Column('product_unique_id', sa.String(), nullable=True),
    sa.Column('raw_text', sa.Text(), nullable=True),
    sa.Column('monetized_url', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False, server_default='pending'),
    sa.Column('offer_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_offers_user', 'offers', ['user_id'], unique=False)
    op.create_index('idx_offers_product', 'offers', ['product_unique_id'], unique=False)
    op.create_index('idx_offers_status', 'offers', ['status'], unique=False)
    
    # Create price_history table
    op.create_table('price_history',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('product_unique_id', sa.String(), nullable=False),
    sa.Column('price_cents', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(), server_default='BRL'),
    sa.Column('recorded_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_price_product', 'price_history', ['product_unique_id'], unique=False)
    op.create_index('idx_price_recorded', 'price_history', ['recorded_at'], unique=False)
    
    # Create send_logs table
    op.create_table('send_logs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('source_platform', sa.String(), nullable=True),
    sa.Column('destination_group_id', sa.String(), nullable=True),
    sa.Column('product_unique_id', sa.String(), nullable=True),
    sa.Column('original_url', sa.Text(), nullable=True),
    sa.Column('monetized_url', sa.Text(), nullable=True),
    sa.Column('sent_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_logs_dedup', 'send_logs', ['user_id', 'product_unique_id', 'sent_at'], unique=False)
    op.create_index('idx_logs_user_sent', 'send_logs', ['user_id', 'sent_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_logs_user_sent', table_name='send_logs')
    op.drop_index('idx_logs_dedup', table_name='send_logs')
    op.drop_table('send_logs')
    
    op.drop_index('idx_price_recorded', table_name='price_history')
    op.drop_index('idx_price_product', table_name='price_history')
    op.drop_table('price_history')
    
    op.drop_index('idx_offers_status', table_name='offers')
    op.drop_index('idx_offers_product', table_name='offers')
    op.drop_index('idx_offers_user', table_name='offers')
    op.drop_table('offers')
    
    op.drop_table('group_destinations')
    op.drop_table('group_sources')
    op.drop_table('affiliate_tags')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
