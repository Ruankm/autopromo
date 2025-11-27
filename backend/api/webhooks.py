"""
API endpoints para webhooks - Recepção direta de mensagens dos provedores.

Este módulo implementa os endpoints que recebem webhooks de:
- Evolution API (WhatsApp)
- Telegram Bot API

Cada webhook extrai o user_id, normaliza o payload e chama o serviço de ingestão.
"""
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from services.ingestion_service import process_raw_message

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


# ============================================================================
# SCHEMAS
# ============================================================================

class WhatsAppWebhookData(BaseModel):
    """Schema para webhook da Evolution API (WhatsApp)."""
    event: str
    instance: str
    data: dict


class TelegramUpdate(BaseModel):
    """Schema para webhook do Telegram Bot API."""
    update_id: int
    message: Optional[dict] = None
    edited_message: Optional[dict] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/whatsapp")
async def whatsapp_webhook(
    payload: WhatsAppWebhookData,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Webhook para Evolution API (WhatsApp).
    
    Recebe mensagens do WhatsApp via Evolution API e processa.
    
    **Headers opcionais**:
    - `X-User-ID`: UUID do usuário (se configurado na Evolution API)
    
    **Resolução de user_id**:
    1. Tenta usar header `X-User-ID` se presente
    2. Se não, busca em `group_sources` por (platform='whatsapp', source_group_id)
    3. Se não encontrar, ignora a mensagem
    
    **Fluxo**:
    1. Valida evento (apenas 'messages.upsert')
    2. Extrai texto e mídia da mensagem
    3. Identifica grupo de origem (remoteJid)
    4. Resolve user_id
    5. Chama serviço de ingestão (dedup + queue)
    
    **Exemplo de payload**:
    ```json
    {
      "event": "messages.upsert",
      "instance": "instance_name",
      "data": {
        "key": {
          "remoteJid": "5511999998888@g.us",
          "fromMe": false
        },
        "message": {
          "conversation": "🔥 OFERTA! ..."
        }
      }
    }
    ```
    """
    # Validar evento
    if payload.event != "messages.upsert":
        # Ignorar outros eventos silenciosamente
        return {"status": "ignored", "reason": "event_not_supported"}
    
    # Extrair dados da mensagem
    data = payload.data
    key = data.get("key", {})
    message = data.get("message", {})
    
    # Verificar se é mensagem de grupo (não privada)
    remote_jid = key.get("remoteJid", "")
    if not remote_jid.endswith("@g.us"):
        # Não é grupo, ignorar
        return {"status": "ignored", "reason": "not_group_message"}
    
    # Verificar se não é mensagem própria
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "own_message"}
    
    # Extrair texto
    raw_text = (
        message.get("conversation") or
        message.get("extendedTextMessage", {}).get("text") or
        ""
    )
    
    if not raw_text:
        # Sem texto, ignorar
        return {"status": "ignored", "reason": "no_text"}
    
    # ========================================================================
    # RESOLUÇÃO DE USER_ID
    # ========================================================================
    user_id = x_user_id
    
    if not user_id:
        # Fallback: buscar em group_sources
        from sqlalchemy import select
        from core.database import AsyncSessionLocal
        from models.group import GroupSource
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(GroupSource).where(
                    GroupSource.platform == "whatsapp",
                    GroupSource.source_group_id == remote_jid,
                    GroupSource.is_active == True
                )
            )
            group_source = result.scalar_one_or_none()
            
            if group_source:
                user_id = str(group_source.user_id)
            else:
                # Não encontrou mapeamento
                import logging
                logging.warning(
                    f"WhatsApp webhook: No user_id mapping for group {remote_jid}. "
                    f"Message ignored."
                )
                return {
                    "status": "ignored",
                    "reason": "no_user_mapping",
                    "source_group_id": remote_jid
                }
    
    # Extrair mídia (se houver)
    media_urls = []
    # TODO: Implementar extração de mídia quando necessário
    
    # Processar mensagem
    result = await process_raw_message(
        user_id=user_id,
        source_platform="whatsapp",
        source_group_id=remote_jid,
        raw_text=raw_text,
        media_urls=media_urls,
        timestamp=datetime.fromtimestamp(data.get("messageTimestamp", 0))
    )
    
    return result


@router.post("/telegram")
async def telegram_webhook(
    update: TelegramUpdate,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Webhook para Telegram Bot API.
    
    Recebe updates do Telegram Bot e processa mensagens de grupos.
    
    **Headers opcionais**:
    - `X-User-ID`: UUID do usuário (se configurado)
    
    **Resolução de user_id**:
    1. Tenta usar header `X-User-ID` se presente
    2. Se não, busca em `group_sources` por (platform='telegram', source_group_id=chat_id)
    3. Se não encontrar, ignora a mensagem
    
    **Fluxo**:
    1. Extrai mensagem do update
    2. Verifica se é mensagem de grupo/supergroup
    3. Extrai texto
    4. Resolve user_id
    5. Chama serviço de ingestão (dedup + queue)
    
    **Exemplo de payload**:
    ```json
    {
      "update_id": 123456789,
      "message": {
        "message_id": 1,
        "chat": {
          "id": -1001234567890,
          "type": "supergroup",
          "title": "Grupo de Ofertas"
        },
        "text": "🔥 OFERTA! ...",
        "date": 1700000000
      }
    }
    ```
    """
    # Extrair mensagem (pode ser message ou edited_message)
    message = update.message or update.edited_message
    
    if not message:
        return {"status": "ignored", "reason": "no_message"}
    
    # Verificar se é grupo/supergroup
    chat = message.get("chat", {})
    chat_type = chat.get("type", "")
    
    if chat_type not in ["group", "supergroup"]:
        return {"status": "ignored", "reason": "not_group_message"}
    
    # Extrair texto
    raw_text = message.get("text") or message.get("caption") or ""
    
    if not raw_text:
        return {"status": "ignored", "reason": "no_text"}
    
    # Chat ID como source_group_id
    chat_id = str(chat.get("id", ""))
    
    # ========================================================================
    # RESOLUÇÃO DE USER_ID
    # ========================================================================
    user_id = x_user_id
    
    if not user_id:
        # Fallback: buscar em group_sources
        from sqlalchemy import select
        from core.database import AsyncSessionLocal
        from models.group import GroupSource
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(GroupSource).where(
                    GroupSource.platform == "telegram",
                    GroupSource.source_group_id == chat_id,
                    GroupSource.is_active == True
                )
            )
            group_source = result.scalar_one_or_none()
            
            if group_source:
                user_id = str(group_source.user_id)
            else:
                # Não encontrou mapeamento
                import logging
                logging.warning(
                    f"Telegram webhook: No user_id mapping for chat {chat_id}. "
                    f"Message ignored."
                )
                return {
                    "status": "ignored",
                    "reason": "no_user_mapping",
                    "chat_id": chat_id,
                    "chat_title": chat.get("title", "")
                }
    
    # Extrair mídia (se houver)
    media_urls = []
    if "photo" in message:
        # TODO: Implementar extração de URL da foto quando necessário
        pass
    
    # Processar mensagem
    result = await process_raw_message(
        user_id=user_id,
        source_platform="telegram",
        source_group_id=chat_id,
        raw_text=raw_text,
        media_urls=media_urls,
        timestamp=datetime.fromtimestamp(message.get("date", 0))
    )
    
    return result
