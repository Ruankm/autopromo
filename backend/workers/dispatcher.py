"""
Dispatcher - "The Traffic Controller"

Este dispatcher gerencia o envio de ofertas para os grupos de destino,
respeitando janelas de horário, rate limiting anti-ban, e registrando
todos os envios em logs.

Pipeline:
1. Round-robin por todos os users ativos
2. Para cada user, LPOP queue:dispatch:user:{user_id}
3. Verificar time window (config do usuário)
4. Verificar rate limit (Redis: last_sent)
5. Chamar provider client (WhatsApp/Telegram)
6. Registrar em send_logs
7. Atualizar last_sent
8. Continuar para próximo usuário

Uso:
    python -m workers.dispatcher
"""
import asyncio
import json
import logging
from datetime import datetime, time, timedelta
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.redis_client import redis_client
from models.user import User
from models.send_log import SendLog
from schemas.worker import ProcessedOffer
from services.providers.whatsapp_evolution import whatsapp_client
from services.providers.telegram_bot import telegram_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TIME WINDOW CHECK
# ============================================================================

def is_within_time_window(user_config: dict) -> bool:
    """
    Verifica se está dentro da janela de horário do usuário.
    
    Exemplo de config:
    {
        "window_start": "06:00",
        "window_end": "23:00"
    }
    
    Args:
        user_config: config_json do usuário
    
    Returns:
        True se pode enviar agora, False se fora da janela
    """
    window_start = user_config.get("window_start", "00:00")
    window_end = user_config.get("window_end", "23:59")
    
    # Parse times
    try:
        start_time = datetime.strptime(window_start, "%H:%M").time()
        end_time = datetime.strptime(window_end, "%H:%M").time()
    except ValueError:
        # Config inválido, deixar passar
        logger.warning(f"Invalid time window config, allowing send")
        return True
    
    # Hora atual
    now_time = datetime.now().time()
    
    # Verificar se está dentro da janela
    if start_time <= end_time:
        # Caso normal: 06:00 - 23:00
        return start_time <= now_time <= end_time
    else:
        # Caso overnight: 22:00 - 02:00
        return now_time >= start_time or now_time <= end_time


# ============================================================================
# RATE LIMITING
# ============================================================================

async def check_rate_limit(
    user_id: str,
    destination_group_id: str,
    min_delay_seconds: int
) -> bool:
    """
    Verifica se pode enviar para este grupo (rate limit anti-ban).
    
    Consulta Redis para ver quando foi o último envio para este grupo.
    
    Args:
        user_id: UUID do usuário
        destination_group_id: ID do grupo destino
        min_delay_seconds: Delay mínimo entre envios (do config do usuário)
    
    Returns:
        True se pode enviar (passou do delay), False se precisa esperar
    """
    redis = redis_client.client
    
    # Chave Redis
    rate_limit_key = f"last_sent:user:{user_id}:group:{destination_group_id}"
    
    # Buscar timestamp do último envio
    last_sent_str = await redis.get(rate_limit_key)
    
    if not last_sent_str:
        # Nunca enviou para este grupo, pode enviar
        return True
    
    # Parsear timestamp
    try:
        last_sent = datetime.fromisoformat(last_sent_str.decode('utf-8'))
    except Exception:
        # Erro no parse, deixar enviar
        return True
    
    # Calcular tempo desde o último envio
    elapsed = (datetime.utcnow() - last_sent).total_seconds()
    
    # Verificar se passou do delay mínimo
    return elapsed >= min_delay_seconds


async def update_rate_limit(user_id: str, destination_group_id: str):
    """
    Atualiza timestamp do último envio no Redis.
    
    Args:
        user_id: UUID do usuário
        destination_group_id: ID do grupo destino
    """
    redis = redis_client.client
    
    rate_limit_key = f"last_sent:user:{user_id}:group:{destination_group_id}"
    
    # Salvar timestamp atual com TTL de 24h (depois disso não importa mais)
    await redis.set(
        rate_limit_key,
        datetime.utcnow().isoformat(),
        ex=86400  # 24 horas
    )


# ============================================================================
# PROVIDER DISPATCH
# ============================================================================

async def dispatch_to_provider(
    offer: ProcessedOffer
) -> bool:
    """
    Envia oferta para o provider correto (WhatsApp ou Telegram).
    
    Args:
        offer: Oferta processada para envio
    
    Returns:
        True se enviou com sucesso, False se falhou
    """
    try:
        if offer.destination_platform == "whatsapp":
            # Enviar via Evolution API
            await whatsapp_client.send_text_message(
                instance="default",  # TODO: pegar do config do usuário
                group_jid=offer.destination_group_id,
                text=offer.final_text,
                delay_ms=1000
            )
            logger.info(f"✓ Sent to WhatsApp group {offer.destination_group_id}")
            return True
        
        elif offer.destination_platform == "telegram":
            # Enviar via Telegram Bot API
            await telegram_client.send_message(
                chat_id=offer.destination_group_id,
                text=offer.final_text,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            logger.info(f"✓ Sent to Telegram chat {offer.destination_group_id}")
            return True
        
        else:
            logger.error(f"Unknown platform: {offer.destination_platform}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to send offer: {e}", exc_info=True)
        return False


# ============================================================================
# DISPATCH PIPELINE
# ============================================================================

async def process_user_queue(db: AsyncSession, user_id: str, user_config: dict) -> int:
    """
    Processa fila de dispatch de um usuário.
    
    Tenta enviar UMA mensagem da fila do usuário (se possível).
    
    Args:
        db: Sessão do banco
        user_id: UUID do usuário
        user_config: config_json do usuário
    
    Returns:
        1 se enviou uma mensagem, 0 se não enviou
    """
    # 1. Verificar time window
    if not is_within_time_window(user_config):
        # Fora da janela, pular este usuário
        logger.debug(f"User {user_id} outside time window, skipping")
        return 0
    
    # 2. Tentar pegar uma mensagem da fila
    redis = redis_client.client
    queue_key = f"queue:dispatch:user:{user_id}"
    
    result = await redis.lpop(queue_key)
    
    if not result:
        # Fila vazia
        return 0
    
    # 3. Parsear oferta
    try:
        offer = ProcessedOffer.model_validate_json(result)
    except Exception as e:
        logger.error(f"Failed to parse offer from queue: {e}")
        return 0
    
    # 4. Verificar rate limit
    min_delay = user_config.get("min_delay_seconds", 300)  # Default: 5 minutos
    
    can_send = await check_rate_limit(
        user_id,
        offer.destination_group_id,
        min_delay
    )
    
    if not can_send:
        # Não pode enviar ainda, recolocar no FINAL da fila
        await redis.rpush(queue_key, result)
        logger.debug(
            f"Rate limit active for user {user_id}, group {offer.destination_group_id}, "
            f"re-queued"
        )
        return 0
    
    # 5. Enviar para o provider
    success = await dispatch_to_provider(offer)
    
    if not success:
        # Falhou, recolocar na fila (com limite de retries)
        # TODO: implementar contador de retries
        await redis.rpush(queue_key, result)
        return 0
    
    # 6. Registrar em send_logs
    send_log = SendLog(
        user_id=offer.user_id,
        source_platform=offer.source_platform,
        destination_group_id=offer.destination_group_id,
        product_unique_id=offer.product_unique_id,
        original_url=offer.monetized_url,  # URL já monetizada
        monetized_url=offer.monetized_url
    )
    
    db.add(send_log)
    await db.commit()
    
    logger.info(
        f"✅ Sent offer for user {user_id} to {offer.destination_platform} "
        f"group {offer.destination_group_id}"
    )
    
    # 7. Atualizar rate limit
    await update_rate_limit(user_id, offer.destination_group_id)
    
    return 1


async def get_active_users(db: AsyncSession) -> List[str]:
    """
    Busca lista de usuários ativos.
    
    Args:
        db: Sessão do banco
    
    Returns:
        Lista de user_ids ativos
    """
    result = await db.execute(
        select(User.id).where(User.is_active == True)
    )
    
    user_ids = [str(row[0]) for row in result.all()]
    
    return user_ids


# ============================================================================
# DISPATCHER LOOP
# ============================================================================

async def dispatcher_loop():
    """
    Loop principal do dispatcher.
    
    Round-robin por todos os usuários ativos, tentando enviar mensagens
    de suas filas respeitando time windows e rate limits.
    """
    logger.info("🚀 Dispatcher started - round-robin mode")
    
    # Conectar ao Redis
    await redis_client.connect()
    
    try:
        while True:
            async with AsyncSessionLocal() as db:
                # 1. Buscar usuários ativos
                user_ids = await get_active_users(db)
                
                if not user_ids:
                    logger.debug("No active users, sleeping...")
                    await asyncio.sleep(5)
                    continue
                
                logger.debug(f"Round-robin over {len(user_ids)} users...")
                
                total_sent = 0
                
                # 2. Round-robin: processar UMA mensagem de cada usuário
                for user_id in user_ids:
                    try:
                        # Buscar config do usuário
                        result = await db.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        
                        if not user:
                            continue
                        
                        # Processar fila do usuário
                        sent = await process_user_queue(db, user_id, user.config_json)
                        total_sent += sent
                    
                    except Exception as e:
                        logger.error(f"Error processing user {user_id}: {e}", exc_info=True)
                        continue
                
                if total_sent > 0:
                    logger.info(f"📤 Sent {total_sent} messages this round")
                
                # Pequeno delay entre rounds para não sobrecarregar
                await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Dispatcher stopped by user")
    
    finally:
        # Desconectar do Redis
        await redis_client.disconnect()
        logger.info("Dispatcher shutdown complete")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    asyncio.run(dispatcher_loop())
