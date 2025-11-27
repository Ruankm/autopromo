"""
Worker de Processamento - "The Brain"

Este worker processa ofertas da queue:ingestion, aplica transformações,
monetiza URLs e enfileira para dispatch.

Pipeline:
1. BLPOP queue:ingestion
2. Unshorten URL
3. Detectar loja e extrair product_id
4. Monetizar URL com affiliate tag
5. Extrair e salvar preço
6. Quality Gate (blacklist + janela 24h)
7. Criar registro em offers
8. Enfileirar para cada grupo destino do usuário

Uso:
    python -m workers.worker
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.redis_client import redis_client
from models.user import User
from models.offer import Offer
from models.price_history import PriceHistory
from models.send_log import SendLog
from models.group import GroupDestination
from schemas.worker import IngestionQueueMessage, ProcessedOffer
from services.parsing_service import parse_offer
from services.monetization_service import monetize_url
from services.ingestion_service import extract_urls

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# QUALITY GATE
# ============================================================================

async def check_blacklist(
    db: AsyncSession,
    user_id: str,
    store_slug: Optional[str]
) -> bool:
    """
    Verifica se a loja está na blacklist do usuário.
    
    A blacklist é armazenada no config_json do usuário:
    {"blacklist_stores": ["shopee", "aliexpress"]}
    
    Args:
        db: Sessão do banco
        user_id: UUID do usuário
        store_slug: Slug da loja
    
    Returns:
        True se está na blacklist (deve ignorar), False caso contrário
    """
    if not store_slug:
        return False
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return True  # Usuário não existe, ignorar
    
    blacklist = user.config_json.get("blacklist_stores", [])
    
    return store_slug in blacklist


async def check_24h_window(
    db: AsyncSession,
    user_id: str,
    product_unique_id: Optional[str],
    destination_group_id: str
) -> bool:
    """
    Verifica se o produto já foi enviado para ESTE grupo nas últimas 24h.
    
    **MULTI-DESTINATION**: A mesma oferta pode ir para vários grupos,
    mas não flood no mesmo grupo.
    
    Consulta send_logs filtrando por:
    - user_id
    - product_unique_id
    - destination_group_id (IMPORTANTE!)
    - sent_at >= 24h atrás
    
    Args:
        db: Sessão do banco
        user_id: UUID do usuário
        product_unique_id: ID único do produto
        destination_group_id: ID do grupo destino
    
    Returns:
        True se já foi enviado NESTE GRUPO (deve ignorar), False caso contrário
    """
    if not product_unique_id:
        return False  # Sem product_id, deixar passar
    
    # Calcular timestamp 24h atrás
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    result = await db.execute(
        select(SendLog).where(
            SendLog.user_id == user_id,
            SendLog.product_unique_id == product_unique_id,
            SendLog.destination_group_id == destination_group_id,  # FILTRO POR GRUPO!
            SendLog.sent_at >= cutoff_time
        ).limit(1)
    )
    
    log_entry = result.scalar_one_or_none()
    
    # Se encontrou, já foi enviado recentemente NESTE GRUPO
    return log_entry is not None


async def apply_quality_gate(
    db: AsyncSession,
    user_id: str,
    store_slug: Optional[str],
    product_unique_id: Optional[str],
    destination_group_id: str
) -> bool:
    """
    Aplica quality gate completo PARA UM GRUPO DESTINO ESPECÍFICO.
    
    Verifica:
    1. Blacklist de lojas (global do usuário)
    2. Janela de 24h (específica do grupo destino)
    
    Args:
        db: Sessão do banco
        user_id: UUID do usuário
        store_slug: Slug da loja
        product_unique_id: ID único do produto
        destination_group_id: ID do grupo destino
    
    Returns:
        True se PASSOU no gate (pode enviar), False se deve ignorar
    """
    # 1. Verificar blacklist (global do usuário)
    is_blacklisted = await check_blacklist(db, user_id, store_slug)
    
    if is_blacklisted:
        logger.info(f"Offer blocked by blacklist: user={user_id}, store={store_slug}")
        return False
    
    # 2. Verificar janela 24h POR GRUPO
    was_sent_recently = await check_24h_window(
        db, user_id, product_unique_id, destination_group_id
    )
    
    if was_sent_recently:
        logger.info(
            f"Offer blocked by 24h window: user={user_id}, "
            f"product={product_unique_id}, group={destination_group_id}"
        )
        return False
    
    # Passou em todos os gates PARA ESTE GRUPO
    return True


# ============================================================================
# PROCESSING PIPELINE
# ============================================================================

async def process_message(message_data: dict) -> None:
    """
    Processa uma mensagem da queue:ingestion.
    
    Pipeline completo de transformação e enfileiramento.
    
    Args:
        message_data: Dict com dados da mensagem (raw JSON da fila)
    """
    # 1. Parsear payload
    try:
        message = IngestionQueueMessage(**message_data)
    except Exception as e:
    )
        if parsed['price_cents'] is None:
            offer_metadata["price_parse_failed"] = True
        
        offer = Offer(
            user_id=message.user_id,
            source_platform=message.source_platform,
            source_group_id=message.source_group_id,
            product_unique_id=parsed['product_unique_id'],
            raw_text=message.raw_text,
            monetized_url=monetized_url,
            status='pending',
            offer_metadata=offer_metadata
        )
        
        db.add(offer)
        await db.flush()  # Para obter o ID
        
        logger.info(f"Created offer record: id={offer.id}")
        
        # 6. Salvar preço em price_history (APENAS SE HOUVER)
        if parsed['price_cents'] is not None and parsed['product_unique_id']:
            price_entry = PriceHistory(
                product_unique_id=parsed['product_unique_id'],
                price_cents=parsed['price_cents'],
                currency='BRL'
            )
            db.add(price_entry)
            logger.info(
                f"Saved price: product={parsed['product_unique_id']}, "
                f"price={parsed['price_cents']/100:.2f} BRL"
            )
        else:
            logger.info("No price detected, not saving to price_history (zero hallucination)")
        
        # 7. Buscar grupos destino ativos do usuário
        result = await db.execute(
            select(GroupDestination).where(
                GroupDestination.user_id == message.user_id,
                GroupDestination.is_active == True
            )
        )
        
        destination_groups = result.scalars().all()
        
        if not destination_groups:
            logger.warning(f"No active destination groups for user {message.user_id}")
            await db.commit()
            return
        
        # 8. Para cada grupo destino, aplicar quality gate E enfileirar
        redis = redis_client.client
        enqueued_count = 0
        
        for group in destination_groups:
            # QUALITY GATE POR GRUPO (blacklist global + 24h window per group)
            passes_gate = await apply_quality_gate(
                db,
                message.user_id,
                parsed['store_slug'],
                parsed['product_unique_id'],
                group.destination_group_id  # Passa o ID do grupo!
            )
            
            if not passes_gate:
                logger.info(
                    f"Offer did not pass quality gate for group {group.destination_group_id}, skipping"
                )
                continue
            
            # Criar oferta processada para dispatch
            processed_offer = ProcessedOffer(
                user_id=message.user_id,
                destination_group_id=group.destination_group_id,
                destination_platform=group.platform,
                product_unique_id=parsed['product_unique_id'],
                monetized_url=monetized_url,
                final_text=message.raw_text,  # Pode ser melhorado com IA no futuro
                source_platform=message.source_platform,
                source_group_id=message.source_group_id,
                store_slug=parsed['store_slug'],
                price_cents=parsed['price_cents']
            )
            
            # RPUSH na fila do usuário
            queue_key = f"queue:dispatch:user:{message.user_id}"
            await redis.rpush(queue_key, processed_offer.model_dump_json())
            
            enqueued_count += 1
            
            logger.info(
                f"Enqueued for dispatch: user={message.user_id}, "
                f"destination={group.destination_group_id}, "
                f"platform={group.platform}"
            )
        
        # Commit de todas as mudanças no banco
        await db.commit()
        
        logger.info(
            f"✅ Successfully processed message for user {message.user_id} "
            f"({enqueued_count}/{len(destination_groups)} groups enqueued)"
        )


# ============================================================================
# WORKER LOOP
# ============================================================================

async def worker_loop():
    """
    Loop principal do worker.
    
    Faz BLPOP na queue:ingestion e processa mensagens indefinidamente.
    """
    logger.info("🚀 Worker started - listening on queue:ingestion")
    
    # Conectar ao Redis
    await redis_client.connect()
    redis = redis_client.client
    
    try:
        while True:
            try:
                # BLPOP com timeout de 5 segundos
                result = await redis.blpop("queue:ingestion", timeout=5)
                
                if result:
                    queue_name, message_json = result
                    
                    # Parsear JSON
                    message_data = json.loads(message_json)
                    
                    # Processar mensagem
                    await process_message(message_data)
                
                else:
                    # Timeout, nenhuma mensagem na fila
                    pass
            
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Continuar o loop mesmo com erro
                await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    
    finally:
        # Desconectar do Redis
        await redis_client.disconnect()
        logger.info("Worker shutdown complete")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    asyncio.run(worker_loop())
