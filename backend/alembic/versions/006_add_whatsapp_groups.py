"""add whatsapp groups dom based

Revision ID: 006_add_whatsapp_groups
Revises: 005_add_qr_fields
Create Date: 2024-12-01 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '006_add_whatsapp_groups'
down_revision = '005_add_qr_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create whatsapp_groups table
    op.create_table(
        'whatsapp_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('last_message_preview', sa.Text(), nullable=True),
        sa.Column('is_source', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_destination', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['connection_id'], ['whatsapp_connections.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('connection_id', 'display_name', name='uq_connection_group_name')
    )
    
    # Create indexes
    op.create_index('idx_groups_connection', 'whatsapp_groups', ['connection_id'])
    op.create_index(
        'idx_groups_source',
        'whatsapp_groups',
        ['connection_id', 'is_source'],
        postgresql_where=sa.text('is_source = true')
    )
    op.create_index(
        'idx_groups_destination',
        'whatsapp_groups',
        ['connection_id', 'is_destination'],
        postgresql_where=sa.text('is_destination = true')
    )


def downgrade() -> None:
    op.drop_index('idx_groups_destination', table_name='whatsapp_groups')
    op.drop_index('idx_groups_source', table_name='whatsapp_groups')
    op.drop_index('idx_groups_connection', table_name='whatsapp_groups')
    op.drop_table('whatsapp_groups')
