# 🎯 ARQUITETURA MULTI-TENANT WHATSAPP - AutoPromo Cloud

## ✅ COMO FUNCIONA (Cada usuário tem seu próprio WhatsApp)

Você está **100% correto**! O sistema já está preparado para isso:

---

## 🏗️ ARQUITETURA ATUAL

### 1. **Cada Usuário = 1 Instância WhatsApp**

```
Usuário A (user_id: abc-123)
  └─ WhatsApp Instance: "autopromo_abc123"
      ├─ QR Code próprio
      ├─ Número próprio
      ├─ Grupos próprios
      └─ Webhooks próprios

Usuário B (user_id: def-456)
  └─ WhatsApp Instance: "autopromo_def456"
      ├─ QR Code próprio
      ├─ Número próprio
      ├─ Grupos próprios
      └─ Webhooks próprios
```

---

## 📊 TABELA: whatsapp_instances

Cada registro representa **1 usuário = 1 WhatsApp**:

```sql
CREATE TABLE whatsapp_instances (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE,  -- ⚠️ UNIQUE! 1 usuário = 1 instância
    instance_name VARCHAR,
    api_url VARCHAR,
    api_key VARCHAR,
    status VARCHAR,  -- 'connected', 'disconnected', 'connecting'
    qr_code TEXT,
    phone_number VARCHAR,
    created_at TIMESTAMP
);
```

**Regra**: `user_id` é **UNIQUE** = cada usuário só pode ter 1 WhatsApp conectado.

---

## 🔄 FLUXO DE CONEXÃO

### Passo 1: Usuário A conecta WhatsApp

```
POST /api/v1/whatsapp/connect
Headers: Authorization: Bearer <token_usuario_A>
Body: {
  "api_url": "http://localhost:8080",
  "api_key": "autopromo_key_2024"
}
```

**O que acontece**:
1. Backend cria instância na Evolution API: `autopromo_<user_id_A>`
2. Salva no banco: `whatsapp_instances` (user_id = A)
3. Retorna QR Code
4. Usuário A escaneia com **SEU WhatsApp**
5. Status muda para `connected`

### Passo 2: Usuário B conecta WhatsApp

```
POST /api/v1/whatsapp/connect
Headers: Authorization: Bearer <token_usuario_B>
Body: {
  "api_url": "http://localhost:8080",
  "api_key": "autopromo_key_2024"
}
```

**O que acontece**:
1. Backend cria **OUTRA** instância: `autopromo_<user_id_B>`
2. Salva no banco: `whatsapp_instances` (user_id = B)
3. Retorna **OUTRO** QR Code
4. Usuário B escaneia com **SEU WhatsApp**
5. Status muda para `connected`

---

## 📱 ISOLAMENTO DE DADOS

### Grupos (group_sources / group_destinations)

```sql
SELECT * FROM group_sources WHERE user_id = 'abc-123';
-- Retorna APENAS grupos do Usuário A

SELECT * FROM group_sources WHERE user_id = 'def-456';
-- Retorna APENAS grupos do Usuário B
```

**Cada grupo tem**:
- `user_id` → Dono do grupo
- `instance_id` → Qual WhatsApp (qual instância Evolution)
- `source_group_id` → ID do grupo no WhatsApp (ex: `120363...@g.us`)

### Webhooks

Quando uma mensagem chega:

```
Webhook Evolution API → Backend
  ├─ Header: X-Instance-Name: autopromo_abc123
  ├─ Resolve: instance_name → user_id (via whatsapp_instances)
  ├─ Processa mensagem para user_id = abc-123
  └─ Enfileira: queue:ingestion (com user_id)
```

**Worker processa**:
```
Worker pega mensagem
  ├─ user_id = abc-123
  ├─ Busca grupos APENAS do usuário abc-123
  ├─ Monetiza com tag APENAS do usuário abc-123
  └─ Envia para grupos APENAS do usuário abc-123
```

---

## 🔐 SEGURANÇA MULTI-TENANT

### 1. API Endpoints (Todos filtram por user_id)

```python
# backend/api/groups.py
@router.get("/source")
async def list_source_groups(current_user: User = Depends(get_current_user)):
    # Retorna APENAS grupos do current_user.id
    result = await db.execute(
        select(GroupSource).where(GroupSource.user_id == current_user.id)
    )
```

### 2. WhatsApp Connection (1 por usuário)

```python
# backend/api/whatsapp.py
@router.post("/connect")
async def connect_whatsapp(current_user: User = Depends(get_current_user)):
    # Verifica se usuário JÁ tem instância
    existing = await db.execute(
        select(WhatsAppInstance).where(
            WhatsAppInstance.user_id == current_user.id
        )
    )
    
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Você já tem um WhatsApp conectado")
    
    # Cria NOVA instância APENAS para este usuário
    instance_name = f"autopromo_{current_user.id}"
```

### 3. Worker Processing (Isolado por user_id)

```python
# backend/workers/worker.py
async def process_message(message_data: dict):
    message = IngestionQueueMessage(**message_data)
    user_id = message.user_id  # ← Vem da mensagem
    
    # Busca grupos APENAS deste usuário
    groups = await db.execute(
        select(GroupDestination).where(
            GroupDestination.user_id == user_id,
            GroupDestination.is_active == True
        )
    )
    
    # Monetiza com tag APENAS deste usuário
    tag = await get_affiliate_tag(db, user_id, store_slug)
```

---

## 🎯 RESUMO

### ✅ Cada usuário tem:
- 1 WhatsApp próprio (1 instância Evolution)
- Seus próprios grupos fonte
- Seus próprios grupos destino
- Suas próprias tags de afiliado
- Suas próprias ofertas processadas

### ✅ Isolamento garantido por:
- `user_id` em TODAS as tabelas
- Filtros em TODOS os endpoints
- JWT token identifica o usuário
- Evolution API cria instâncias separadas

### ✅ Escalabilidade:
- 1 Evolution API pode ter **múltiplas instâncias**
- Cada instância = 1 WhatsApp diferente
- Todos compartilham a mesma API Key
- Mas cada um tem seu `instance_name` único

---

## 🚀 PRÓXIMO PASSO

Aguardar Evolution API terminar de subir (~1 minuto) e testar conexão!

**Arquitetura está 100% pronta para multi-tenant!** 🎉
