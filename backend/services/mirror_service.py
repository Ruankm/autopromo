"""
Mirror Service - Copia mensagens COM MÍDIA (imagens/vídeos) e monetização.

Suporta:
- Texto puro
- Imagem + legenda
- Vídeo + legenda
- NOVO: Auto-scraping de imagens Amazon quando não há mídia
"""
import os
import logging
import httpx
import base64
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.group import GroupSource, GroupDestination
from services.parsing_service import detect_store
from services.monetization_service import monetize_url, extract_amazon_asin
from services.scrapers.amazon_scraper import AmazonScraper
from services.product_intelligence import ProductIntelligence
import re

logger = logging.getLogger(__name__)


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    if not text:
        return []
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, text)


async def process_incoming_whatsapp_message(
    db: AsyncSession,
    user: User,
    source_group_jid: str,
    raw_text: str,
    instance_name: str,
    raw_payload: dict
) -> dict:
    """
    Mirror com mídia: grupo fonte → grupos destino (URLs monetizadas + mídia).
    
    Suporta:
    - Texto puro
    - Imagem + texto
    - Vídeo + texto
    """
    user_id = str(user.id)
    
    logger.info(f"🎯 Mirror: {source_group_jid}")
    
    # 1. Verificar se é grupo fonte
    result = await db.execute(
        select(GroupSource).where(
            GroupSource.user_id == user.id,
            GroupSource.platform == "whatsapp",
            GroupSource.source_group_id == source_group_jid,
            GroupSource.is_active == True
        )
    )
    group_source = result.scalar_one_or_none()
    
    if not group_source:
        return {"status": "ignored"}
    
    logger.info(f"✅ Source: {group_source.label}")
    
    # 2. Buscar destinos
    result = await db.execute(
        select(GroupDestination).where(
            GroupDestination.user_id == user.id,
            GroupDestination.platform == "whatsapp",
            GroupDestination.is_active == True
        )
    )
    destinations = result.scalars().all()
    
    if not destinations:
        return {"status": "no_destinations"}
    
    logger.info(f"Destinations: {len(destinations)}")
    
    # 3. Detectar tipo de mensagem e extrair mídia
    message_data = raw_payload.get("data", {}).get("message", {})
    
    message_type = None
    image_url = None
    video_url = None
    caption = None
    
    if "imageMessage" in message_data:
        message_type = "image"
        caption = message_data["imageMessage"].get("caption", "")
        image_url = message_data["imageMessage"].get("url")
        logger.info("📷 Detected image message")
        
    elif "videoMessage" in message_data:
        message_type = "video"
        caption = message_data["videoMessage"].get("caption", "")
        video_url = message_data["videoMessage"].get("url")
        logger.info("🎥 Detected video message")
        
    elif "conversation" in message_data:
        message_type = "text"
        caption = message_data.get("conversation", "")
        logger.info("💬 Detected text message")
        
    elif "extendedTextMessage" in message_data:
        message_type = "text"
        caption = message_data["extendedTextMessage"].get("text", "")
        logger.info("💬 Detected extended text message")
    
    # Use caption or raw_text
    text_to_process = caption or raw_text
    
    # 4. Extract and monetize URLs
    urls = extract_urls(text_to_process)
    logger.info(f"Found {len(urls)} URL(s)")
    
    new_text = text_to_process
    monetized_count = 0
    amazon_asins = []
    
    for original_url in urls:
        try:
            store_slug = detect_store(original_url)
            
            if not store_slug:
                continue
            
            # Track Amazon ASINs for scraping
            if store_slug == "amazon":
                asin = extract_amazon_asin(original_url)
                if asin:
                    amazon_asins.append(asin)
            
            result = await monetize_url(
                db=db,
                user_id=user_id,
                store_slug=store_slug,
                original_url=original_url
            )
            
            monetized_url = result.get("monetized_url")
            
            if monetized_url != original_url:
                new_text = new_text.replace(original_url, monetized_url)
                logger.info(f"💰 Monetized ({store_slug})")
                monetized_count += 1
                
        except Exception as e:
            logger.error(f"Failed to monetize {original_url}: {e}")
    
    # 5. SMART FEATURE: Auto-scrape Amazon product if no media
    if not image_url and not video_url and amazon_asins:
        # No media but has Amazon link - scrape product image!
        asin = amazon_asins[0]  # Use first ASIN
        logger.info(f"🤖 No media detected, scraping Amazon product: {asin}")
        
        try:
            product_data = await AmazonScraper.scrape_product(asin)
            
            if product_data and product_data.image_url:
                image_url = product_data.image_url
                message_type = "image"
                logger.info(f"✅ Scraped image: {image_url[:80]}...")
            else:
                logger.warning(f"⚠️ Scraping returned no image for {asin}")
                
        except Exception as e:
            logger.error(f"Scraping failed for {asin}: {e}")
    
    # 6. Send to destinations
    api_url = os.getenv("EVOLUTION_API_BASE_URL", "http://localhost:8081")
    api_key = os.getenv("EVOLUTION_API_TOKEN", "")
    
    if not api_key:
        logger.error("EVOLUTION_API_TOKEN is empty!")
        return {"status": "error", "reason": "missing_api_key"}
    
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    
    sent = 0
    
    for dest in destinations:
        jid = dest.destination_group_id
        label = dest.label or jid[:15]
        
        try:
            logger.info(f"Sending to {label}...")
            
            # Choose endpoint based on message type
            if message_type == "image" and image_url:
                # Send image with caption
                url = f"{api_url}/message/sendMedia/{instance_name}"
                payload = {
                    "number": jid,
                    "mediatype": "image",
                    "media": image_url,
                    "caption": new_text
                }
            elif message_type == "video" and video_url:
                # Send video with caption
                url = f"{api_url}/message/sendMedia/{instance_name}"
                payload = {
                    "number": jid,
                    "mediatype": "video",
                    "media": video_url,
                    "caption": new_text
                }
            else:
                # Send text only WITH DELAY (gives WhatsApp time to generate preview!)
                url = f"{api_url}/message/sendText/{instance_name}"
                payload = {
                    "number": jid,
                    "text": new_text,
                    "options": {
                        "delay": 1200  # 1.2s delay for WhatsApp to generate link preview
                    }
                }
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                
            logger.info(f"✅ Sent to {label}")
            sent += 1
            
        except Exception as e:
            logger.error(f"Failed {label}: {e}")
    
    return {
        "status": "processed",
        "sent": sent,
        "monetized": monetized_count,
        "total_urls": len(urls),
        "message_type": message_type
    }
