"""
Schemas para o Worker de Processamento.

Define os modelos Pydantic para payloads de filas e ofertas processadas.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IngestionQueueMessage(BaseModel):
    """
    Payload da queue:ingestion (enviado pelo ingestion_service).
    """
    user_id: str
    source_platform: str  # 'whatsapp' ou 'telegram'
    source_group_id: str
    raw_text: str
    media_urls: list[str] = []
    timestamp: str  # ISO8601
    dedup_hash: str


class ProcessedOffer(BaseModel):
    """
    Oferta processada pronta para dispatch.
    """
    user_id: str
    destination_group_id: str
    destination_platform: str
    
    # Dados da oferta
    product_unique_id: Optional[str] = None
    monetized_url: Optional[str] = None
    final_text: str
    
    # Metadata
    source_platform: str
    source_group_id: str
    store_slug: Optional[str] = None
    price_cents: Optional[int] = None
