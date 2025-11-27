# AutoPromo Cloud - API Contract

## REST Endpoints

### 1. Webhooks (Ingestão Direta)

#### POST `/api/v1/webhook/whatsapp`
Recebe mensagens da Evolution API (WhatsApp).

**Headers**:
- `X-User-ID`: UUID do usuário (mapeamento configurado na Evolution API)
- `X-API-Key`: Chave de autenticação do webhook (opcional, para validação)

**Request Body** (Evolution API format):
```json
{
  "event": "messages.upsert",
  "instance": "instance_name",
  "data": {
    "key": {
      "remoteJid": "5511999998888@g.us",
      "fromMe": false,
      "id": "msg_id"
    },
    "message": {
      "conversation": "🔥 OFERTA! Notebook Gamer...\nhttps://amzn.to/abc123"
    },
    "messageTimestamp": 1700000000,
    "pushName": "Sender Name"
  }
}
```

**Response** (200 OK):
```json
{
  "status": "accepted"|"duplicate",
  "dedup_hash": "a3f5b2c1..."
}
```

---

#### POST `/api/v1/webhook/telegram`
Recebe updates do Telegram Bot API.

**Headers**:
- `X-User-ID`: UUID do usuário (mapeamento via bot token ou chat_id)

**Request Body** (Telegram Bot API format):
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 123456,
      "is_bot": false,
      "first_name": "User"
    },
    "chat": {
      "id": -1001234567890,
      "title": "Grupo de Ofertas",
      "type": "supergroup"
    },
    "date": 1700000000,
    "text": "🔥 OFERTA! Notebook Gamer...\nhttps://amzn.to/abc123"
  }
}
```

**Response** (200 OK):
```json
{
  "status": "accepted"|"duplicate",
  "dedup_hash": "a3f5b2c1..."
}
```

---

### 2. Authentication
- **POST** `/api/v1/users/register` - Registrar novo usuário
- **POST** `/api/v1/users/login` - Login (retorna JWT)
- **GET** `/api/v1/users/me` - Dados do usuário autenticado
- **PATCH** `/api/v1/users/me` - Atualizar config do usuário

### 3. Affiliate Tags
- **GET** `/api/v1/tags` - Listar tags do usuário
- **POST** `/api/v1/tags` - Body: `{ store_slug, tag_code }`
- **DELETE** `/api/v1/tags/{tag_id}`

### 4. Groups Management
- **GET** `/api/v1/groups/sources` - Listar grupos-fonte
- **POST** `/api/v1/groups/sources` - Body: `{ platform, source_group_id, label }`
- **GET** `/api/v1/groups/destinations` - Listar grupos-destino
- **POST** `/api/v1/groups/destinations` - Body: `{ platform, destination_group_id, label }`

### 5. Dashboard
- **GET** `/api/v1/dashboard/stats` - Estatísticas (fila, enviados hoje, etc)
- **GET** `/api/v1/offers/recent?limit=50&status=pending` - Ofertas recentes

---

## Provider Clients (Dispatcher → APIs)

### WhatsApp (Evolution API)

**Dispatcher chama**: `services/providers/whatsapp_evolution.py`

**Função**: `async def send_message(session: str, group_jid: str, text: str, media_urls: list[str] = None)`

**HTTP Request** (interno):
```http
POST https://evolution-api-url/message/sendText/{instance}
Authorization: Bearer {EVOLUTION_API_TOKEN}
Content-Type: application/json

{
  "number": "5511999998888@g.us",
  "text": "🔥 OFERTA! ...",
  "delay": 1000
}
```

---

### Telegram (Bot API)

**Dispatcher chama**: `services/providers/telegram_bot.py`

**Função**: `async def send_message(chat_id: str, text: str, parse_mode: str = "HTML")`

**HTTP Request** (interno):
```http
POST https://api.telegram.org/bot{BOT_TOKEN}/sendMessage
Content-Type: application/json

{
  "chat_id": "-1001234567890",
  "text": "🔥 OFERTA! ...",
  "parse_mode": "HTML",
  "disable_web_page_preview": false
}
```

---

## Database Tables

```sql
-- Usuários
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    config_json JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tags de Afiliado
CREATE TABLE affiliate_tags (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    store_slug VARCHAR NOT NULL,
    tag_code VARCHAR NOT NULL,
    UNIQUE(user_id, store_slug)
);

-- Grupos-Fonte
CREATE TABLE group_sources (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR NOT NULL,
    source_group_id VARCHAR NOT NULL,
    label VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Grupos-Destino
CREATE TABLE group_destinations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR NOT NULL,
    destination_group_id VARCHAR NOT NULL,
    label VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ofertas
CREATE TABLE offers (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_platform VARCHAR,
    source_group_id VARCHAR,
    product_unique_id VARCHAR,
    raw_text TEXT,
    monetized_url TEXT,
    status VARCHAR DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_offers_user ON offers(user_id);
CREATE INDEX idx_offers_product ON offers(product_unique_id);

-- Histórico de Preços
CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    product_unique_id VARCHAR NOT NULL,
    price_cents INTEGER NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_price_product ON price_history(product_unique_id);

-- Log de Envios
CREATE TABLE send_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_platform VARCHAR,
    destination_group_id VARCHAR,
    product_unique_id VARCHAR,
    original_url TEXT,
    monetized_url TEXT,
    sent_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_logs_dedup ON send_logs(user_id, product_unique_id, sent_at);
```

## Redis Keys

| Pattern | Type | Purpose | TTL |
|---------|------|---------|-----|
| `ingestion_dedup:{hash}` | String | Deduplicação | 600s |
| `queue:ingestion` | List | Fila de ingestão | - |
| `queue:dispatch:user:{user_id}` | List | Fila por usuário | - |
| `last_sent:user:{uid}:group:{gid}` | String | Rate limit | 86400s |

## Configuração de Provedores

### Evolution API (WhatsApp)
```env
EVOLUTION_API_BASE_URL=https://your-evolution-api.com
EVOLUTION_API_TOKEN=your_api_token_here
```

### Telegram Bot
```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

## Fluxo Completo (Sem n8n)

1. **Ingestão**: Evolution API / Telegram Bot → `POST /webhook/*` → Ingestion Service
2. **Deduplicação**: Redis SET NX com hash SHA-256
3. **Enfileiramento**: `RPUSH queue:ingestion`
4. **Processamento**: Worker → BLPOP → Parser → Monetização → `RPUSH queue:dispatch:user:{id}`
5. **Dispatch**: Dispatcher → Provider Client (Python) → Evolution API / Telegram Bot API
6. **Auditoria**: Gravar em `send_logs`
