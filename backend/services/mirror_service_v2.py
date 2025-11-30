"""
Mirror Service V2 - Playwright-based mirroring with monetization.

NEW VERSION usando PlaywrightGateway (WhatsApp Web nativo).

Features:
- Native link previews (SEMPRE funciona)
- Connection-based (usa WhatsAppConnection)
- Saves OfferLog for analytics
- Monetization via monetization_service
"""
import logging
import time
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.whatsapp_connection import WhatsAppConnection
from models.offer_log import OfferLog
from services.whatsapp.playwright_gateway import PlaywrightWhatsAppGateway
from services.monetization_service import monetize_text
from services.ingestion_service import extract_urls

logger = logging.getLogger(__name__)


async def mirror_message_playwright(
    db: AsyncSession,
    connection_id: str,
    source_group_name: str,
    destination_group_name: str,
    original_text: str
) -> dict:
    """
    Mirror message using Playwright (WhatsApp Web).
    
    Args:
        db: Database session
        connection_id: UUID of WhatsAppConnection
        source_group_name: Source group name
        destination_group_name: Destination group name
        original_text: Original message text
        
    Returns:
        {
            "status": "sent" | "error",
            "preview_generated": bool,
            "duration_ms": int,
            "monetized_urls": int
        }
    """
    start_time = time.time()
    
    try:
        # 1. Get connection
        result = await db.execute(
            select(WhatsAppConnection).where(
                WhatsAppConnection.id == connection_id
            )
        )
        
        connection = result.scalar_one_or_none()
        
        if not connection:
            return {
                "status": "error",
                "error": "Connection not found"
            }
        
        # 2. Monetize text
        monetized_text = await monetize_text(
            db=db,
            text=original_text,
            user_id=str(connection.user_id)
        )
        
        # 3. Extract URLs for logging
        urls = extract_urls(original_text)
        monetized_urls = extract_urls(monetized_text)
        
        links_found = [
            {
                "original": orig,
                "monetized": mon
            }
            for orig, mon in zip(urls, monetized_urls)
        ]
        
        # 4. Send via PlaywrightGateway
        gateway = PlaywrightWhatsAppGateway(db=db)
        await gateway.start()
        
        try:
            result = await gateway.send_message(
                connection_id=str(connection_id),
                group_name=destination_group_name,
                text=monetized_text,
                wait_for_preview=True
            )
            
            send_status = result.get("status")
            preview_generated = result.get("preview_generated", False)
            duration_ms = result.get("duration_ms", 0)
            
            # 5. Save OfferLog
            if send_status == "sent":
                offer_log = OfferLog(
                    connection_id=connection_id,
                    source_group_name=source_group_name,
                    destination_group_name=destination_group_name,
                    original_text=original_text,
                    monetized_text=monetized_text,
                    links_found=links_found,
                    preview_generated="yes" if preview_generated else "no",
                    send_duration_ms=duration_ms
                )
                
                db.add(offer_log)
                await db.commit()
                
                # Update connection stats
                connection.messages_sent_today += 1
                connection.last_activity_at = datetime.utcnow()
                await db.commit()
                
                logger.info(
                    f"[MIRROR] {source_group_name} → {destination_group_name} "
                    f"(preview: {preview_generated}, {duration_ms}ms)"
                )
            
            return {
                "status": send_status,
                "preview_generated": preview_generated,
                "duration_ms": duration_ms,
                "monetized_urls": len(links_found)
            }
        
        finally:
            await gateway.shutdown()
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[MIRROR ERROR] {e}", exc_info=True)
        
        return {
            "status": "error",
            "error": str(e),
            "duration_ms": duration_ms
        }


async def mirror_to_all_destinations(
    db: AsyncSession,
    connection_id: str,
    source_group_name: str,
    original_text: str
) -> dict:
    """
    Mirror message to ALL destination groups of a connection.
    
    Args:
        db: Database session
        connection_id: UUID of WhatsAppConnection
        source_group_name: Source group name
        original_text: Original message text
        
    Returns:
        {
            "status": "completed",
            "sent": int,
            "failed": int,
            "results": [...]
        }
    """
    # Get connection
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id
        )
    )
    
    connection = result.scalar_one_or_none()
    
    if not connection:
        return {
            "status": "error",
            "error": "Connection not found"
        }
    
    # Get destination groups
    dest_groups = [g["name"] for g in connection.destination_groups]
    
    if not dest_groups:
        logger.warning(f"Connection {connection.nickname} has no destination groups")
        return {
            "status": "completed",
            "sent": 0,
            "failed": 0,
            "results": []
        }
    
    # Mirror to each destination
    results = []
    sent = 0
    failed = 0
    
    for dest_group_name in dest_groups:
        result = await mirror_message_playwright(
            db=db,
            connection_id=connection_id,
            source_group_name=source_group_name,
            destination_group_name=dest_group_name,
            original_text=original_text
        )
        
        results.append({
            "destination": dest_group_name,
            **result
        })
        
        if result.get("status") == "sent":
            sent += 1
        else:
            failed += 1
    
    return {
        "status": "completed",
        "sent": sent,
        "failed": failed,
        "results": results
    }
