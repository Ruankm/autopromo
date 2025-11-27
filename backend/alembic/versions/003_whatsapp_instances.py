"""Add whatsapp_instances table

Revision ID: 003_whatsapp_instances
Revises: 002_add_full_name
Create Date: 2025-11-26 15:55:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '003_whatsapp_instances'
down_revision = '002_add_full_name'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela whatsapp_instances
    op.create_table(
        'whatsapp_instances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('instance_name', sa.String(100), nullable=False, unique=True),
        sa.Column('api_url', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='disconnected'),
        sa.Column('qr_code', sa.Text(), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('last_sync_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    # Índices
    op.create_index('idx_whatsapp_instances_user', 'whatsapp_instances', ['user_id'])
    op.create_index('idx_whatsapp_instances_status', 'whatsapp_instances', ['status'])
    
    # Constraint: um usuário = uma instância
    op.create_unique_constraint('uq_user_whatsapp_instance', 'whatsapp_instances', ['user_id'])
    
    # Adicionar colunas em group_sources
    op.add_column('group_sources', sa.Column('instance_id', UUID(as_uuid=True), nullable=True))
    op.add_column('group_sources', sa.Column('auto_discovered', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('group_sources', sa.Column('discovered_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('group_sources', sa.Column('group_name', sa.String(255), nullable=True))
    op.add_column('group_sources', sa.Column('participant_count', sa.Integer(), nullable=True))
    
    # Foreign key para group_sources
    op.create_foreign_key(
        'fk_group_sources_instance',
        'group_sources',
        'whatsapp_instances',
        ['instance_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Adicionar colunas em group_destinations
    op.add_column('group_destinations', sa.Column('instance_id', UUID(as_uuid=True), nullable=True))
    op.add_column('group_destinations', sa.Column('auto_discovered', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('group_destinations', sa.Column('discovered_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('group_destinations', sa.Column('group_name', sa.String(255), nullable=True))
    op.add_column('group_destinations', sa.Column('participant_count', sa.Integer(), nullable=True))
    
    # Foreign key para group_destinations
    op.create_foreign_key(
        'fk_group_destinations_instance',
        'group_destinations',
        'whatsapp_instances',
        ['instance_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Remover foreign keys
    op.drop_constraint('fk_group_destinations_instance', 'group_destinations', type_='foreignkey')
    op.drop_constraint('fk_group_sources_instance', 'group_sources', type_='foreignkey')
    
    # Remover colunas de group_destinations
    op.drop_column('group_destinations', 'participant_count')
    op.drop_column('group_destinations', 'group_name')
    op.drop_column('group_destinations', 'discovered_at')
    op.drop_column('group_destinations', 'auto_discovered')
    op.drop_column('group_destinations', 'instance_id')
    
    # Remover colunas de group_sources
    op.drop_column('group_sources', 'participant_count')
    op.drop_column('group_sources', 'group_name')
    op.drop_column('group_sources', 'discovered_at')
    op.drop_column('group_sources', 'auto_discovered')
    op.drop_column('group_sources', 'instance_id')
    
    # Remover índices
    op.drop_index('idx_whatsapp_instances_status', 'whatsapp_instances')
    op.drop_index('idx_whatsapp_instances_user', 'whatsapp_instances')
    
    # Remover tabela
    op.drop_table('whatsapp_instances')
