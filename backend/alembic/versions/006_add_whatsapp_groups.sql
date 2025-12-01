-- Migration 006: Add whatsapp_groups table (DOM-based discovery)
-- Run: Get-Content 006_add_whatsapp_groups.sql | docker-compose exec -T postgres psql -U autopromo -d autopromo_db

-- Create whatsapp_groups table
CREATE TABLE IF NOT EXISTS whatsapp_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL REFERENCES whatsapp_connections(id) ON DELETE CASCADE,
    
    -- Identificação (SEM JID)
    display_name VARCHAR(255) NOT NULL,
    last_message_preview TEXT,
    
    -- Configuração
    is_source BOOLEAN DEFAULT FALSE NOT NULL,
    is_destination BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Metadados
    last_sync_at TIMESTAMP,
    last_message_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    -- Unique constraint
    UNIQUE(connection_id, display_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_groups_connection ON whatsapp_groups(connection_id);
CREATE INDEX IF NOT EXISTS idx_groups_source ON whatsapp_groups(connection_id, is_source) WHERE is_source = TRUE;
CREATE INDEX IF NOT EXISTS idx_groups_destination ON whatsapp_groups(connection_id, is_destination) WHERE is_destination = TRUE;

-- Insert into alembic_version
INSERT INTO alembic_version (version_num) VALUES ('006_add_whatsapp_groups')
ON CONFLICT DO NOTHING;
