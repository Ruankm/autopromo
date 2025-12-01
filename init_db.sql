-- Criar tabela users (se não existir)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    config_json JSONB DEFAULT '{"window_start": "08:00", "window_end": "22:00", "min_delay_seconds": 300, "max_messages_per_day": 100}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Criar tabela whatsapp_connections COM os campos QR
CREATE TABLE IF NOT EXISTS whatsapp_connections (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20),
    nickname VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    qr_code_base64 TEXT,
    qr_generated_at TIMESTAMP,
    source_groups JSON DEFAULT '[]'::json,
    destination_groups JSON DEFAULT '[]'::json,
    min_interval_per_group INTEGER DEFAULT 360,
    min_interval_global INTEGER DEFAULT 30,
    max_messages_per_day INTEGER DEFAULT 1000,
    plan_name VARCHAR(50) DEFAULT 'trial',
    max_source_groups INTEGER DEFAULT 5,
    max_destination_groups INTEGER DEFAULT 10,
    last_activity_at TIMESTAMP,
    last_error VARCHAR(500),
    messages_sent_today INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Criar demais tabelas necessárias
CREATE TABLE IF NOT EXISTS offer_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES whatsapp_connections(id) ON DELETE CASCADE,
    group_name VARCHAR(255) NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent'
);

CREATE TABLE IF NOT EXISTS message_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES whatsapp_connections(id) ON DELETE CASCADE,
    source_group VARCHAR(255) NOT NULL,
    message_hash VARCHAR(64) NOT NULL UNIQUE,
    message_text TEXT,
    received_at TIMESTAMP DEFAULT NOW()
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_whatsapp_connections_user_id ON whatsapp_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_connections_status ON whatsapp_connections(status);
CREATE INDEX IF NOT EXISTS idx_offer_logs_connection_id ON offer_logs(connection_id);
CREATE INDEX IF NOT EXISTS idx_message_logs_connection_id ON message_logs(connection_id);
