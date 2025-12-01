"""add qr fields to whatsapp connection

Revision ID: 005_add_qr_fields
Revises: 20251129_2202_d9c4b549b632
Create Date: 2025-11-30 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_qr_fields'
down_revision = '20251129_2202_d9c4b549b632'
branch_labels = None
depends_on = None


def upgrade():
    # Add QR code fields
    op.add_column(
        'whatsapp_connections',
        sa.Column('qr_code_base64', sa.Text(), nullable=True)
    )
    op.add_column(
        'whatsapp_connections',
        sa.Column('qr_generated_at', sa.DateTime(), nullable=True)
    )
    
    # Update existing connections from old flow to new flow
    # qr_needed → pending (will be reprocessed by new Worker)
    op.execute(
        """
        UPDATE whatsapp_connections 
        SET status = 'pending' 
        WHERE status = 'qr_needed'
        """
    )
    
    # Add comment documenting status values
    op.execute(
        """
        COMMENT ON COLUMN whatsapp_connections.status IS 
        'Values: pending (created, awaiting Worker), qr_needed (QR generated, awaiting scan), connecting (QR scanned, loading), connected (ready), disconnected (logged out), error (failed)'
        """
    )


def downgrade():
    op.drop_column('whatsapp_connections', 'qr_generated_at')
    op.drop_column('whatsapp_connections', 'qr_code_base64')
