"""
Serviço de Ingestão - Processa mensagens brutas e enfileira para processamento.

Este módulo centraliza a lógica de:
- Normalização de texto
- Extração de URLs
- Deduplicação via Redis (SHA-256 hash)
- Enfileiramento em queue:ingestion
"""
import re
import hashlib
import json
from typing import Optional
from datetime import datetime
from redis.asyncio import Redis

from core.redis_client import get_redis


async def normalize_text(text: str) -> str:
    """
    Normaliza texto para deduplicação.
    
    - Converte para lowercase
    - Remove espaços extras
    - Remove emojis redundantes (simples)
    
    Args:
        text: Texto bruto
    
    Returns:
        Texto normalizado
    """
    # Lowercase
    normalized = text.lower()
    
    # Remover espaços extras
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def extract_urls(text: str) -> list[str]:
    """
    Extrai todas as URLs do texto.
    
    Args:
        text: Texto contendo URLs
    
    Returns:
        Lista de URLs encontradas
    """
    # Regex simples para URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return urls


def create_dedup_hash(user_id: str, canonical_url: str, text_snippet: str) -> str:
    """
    Cria hash SHA-256 para deduplicação.
    
    Args:
        user_id: UUID do usuário
        canonical_url: URL canônica extraída
        text_snippet: Snippet do texto normalizado (primeiros 100 chars)
    
    Returns:
        Hash SHA-256 em hexadecimal
    """
    # Combinar componentes
    combined = f"{user_id}|{canonical_url}|{text_snippet[:100]}"
    
    # Gerar hash
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return hash_obj.hexdigest()


async def process_raw_message(
    user_id: str,
    source_platform: str,
    source_group_id: str,
    raw_text: str,
    media_urls: Optional[list[str]] = None,
    timestamp: Optional[datetime] = None
) -> dict:
    """
    Processa mensagem bruta e enfileira se não for duplicada.
    
    Este é o ponto central de ingestão, chamado pelos webhooks.
    
    Args:
        user_id: UUID do usuário
        source_platform: 'whatsapp' ou 'telegram'
        source_group_id: ID do grupo de origem
        raw_text: Texto bruto da mensagem
        media_urls: URLs de mídia (opcional)
        timestamp: Timestamp da mensagem (opcional)
    
    Returns:
        Dict com status: 'accepted' ou 'duplicate' e dedup_hash
    """
    redis: Redis = await get_redis()
    
    # 1. Normalizar texto
    normalized_text = await normalize_text(raw_text)
    
    # 2. Extrair URLs
    urls = extract_urls(raw_text)
    canonical_url = urls[0] if urls else ""
    
    # 3. Criar hash de deduplicação
    dedup_hash = create_dedup_hash(user_id, canonical_url, normalized_text)
    
    # 4. Tentar inserir no Redis com SET NX (atomic lock)
    dedup_key = f"ingestion_dedup:{dedup_hash}"
    is_new = await redis.set(dedup_key, "1", ex=600, nx=True)
    
    if not is_new:
        # Duplicado - retornar sem enfileirar
        return {
            "status": "duplicate",
            "dedup_hash": dedup_hash
        }
    
    # 5. Serializar mensagem para enfileiramento
    message_payload = {
        "user_id": user_id,
        "source_platform": source_platform,
        "source_group_id": source_group_id,
        "raw_text": raw_text,
        "media_urls": media_urls or [],
        "timestamp": timestamp.isoformat() if timestamp else datetime.utcnow().isoformat(),
        "dedup_hash": dedup_hash
    }
    
    # 6. Enfileirar em queue:ingestion
    await redis.rpush("queue:ingestion", json.dumps(message_payload))
    
    return {
        "status": "accepted",
        "dedup_hash": dedup_hash
    }
