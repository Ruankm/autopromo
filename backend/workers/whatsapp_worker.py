"""
WhatsApp Worker - Main worker loop for Playwright automation.

Responsibilities:
- Initialize PlaywrightGateway
- Monitor source groups for new messages
- Queue messages for sending
- Process send queue with rate limiting
- Listen for Redis commands (pause, resume, etc)
- Graceful shutdown

Architecture:
- Runs in separate process/container from FastAPI
- Communicates via Redis pub/sub
- Manages all WhatsApp connections for all users
- Handles persistent contexts lifecycle
"""
import asyncio
import logging
import signal
import sys
from typing import Dict, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import AsyncSessionLocal
from core.redis_client import redis_client
from models.whatsapp_connection import WhatsAppConnection
from services.whatsapp.playwright_gateway import PlaywrightWhatsAppGateway
from services.whatsapp.queue_manager import QueueManager
from services.monetization_service import monetize_text

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WhatsAppWorker:
    """
    Main WhatsApp worker managing all connections and message processing.
    
    Single worker instance handles multiple WhatsApp connections,
    each with their own persistent context.
    """
    
    def __init__(self):
        self.gateway: PlaywrightWhatsAppGateway = None
        self.queue_manager = QueueManager()
        self.running = False
        self.active_connections: Set[str] = set()
        
        # State
        self.monitor_interval = 30  # seconds between monitoring cycles
        self.send_interval = 5      # seconds between send attempts
        
        logger.info("WhatsAppWorker initialized")
    
    async def start(self):
        """Start worker and all services."""
        logger.info("=== Starting WhatsApp Worker ===")
        
        # Connect to Redis
        await redis_client.connect()
        logger.info("✓ Redis connected")
        
        # Initialize Playwright gateway
        async with AsyncSessionLocal() as db:
            self.gateway = PlaywrightWhatsAppGateway(
                db=db,
                sessions_dir="./whatsapp_sessions"
            )
            await self.gateway.start()
        logger.info("✓ Playwright gateway started")
        
        self.running = True
        logger.info("=== Worker Ready ===")
    
    async def stop(self):
        """Stop worker gracefully."""
        logger.info("=== Stopping WhatsApp Worker ===")
        
        self.running = False
        
        # Shutdown Playwright
        if self.gateway:
            await self.gateway.shutdown()
            logger.info("✓ Playwright gateway stopped")
        
        # Disconnect Redis
        await redis_client.disconnect()
        logger.info("✓ Redis disconnected")
        
        logger.info("=== Worker Stopped ===")
    
    async def get_active_connections(self, db: AsyncSession) -> list[WhatsAppConnection]:
        """
        Get all active WhatsApp connections.
        
        Returns:
            List of WhatsAppConnection objects with status='connected'
        """
        result = await db.execute(
            select(WhatsAppConnection).where(
                WhatsAppConnection.status == "connected"
            )
        )
        
        connections = result.scalars().all()
        return list(connections)
    
    async def monitor_cycle(self):
        """
        Single monitoring cycle - check all source groups for new messages.
        """
        async with AsyncSessionLocal() as db:
            # Get active connections
            connections = await self.get_active_connections(db)
            
            if not connections:
                logger.debug("No active connections to monitor")
                return
            
            logger.info(f"Monitoring {len(connections)} connection(s)...")
            
            for conn in connections:
                try:
                    # Get source groups
                    source_groups = [g["name"] for g in conn.source_groups]
                    
                    if not source_groups:
                        logger.debug(f"Connection {conn.nickname} has no source groups")
                        continue
                    
                    # Check for new messages
                    new_messages = await self.gateway.get_new_messages(
                        connection_id=str(conn.id),
                        source_groups=source_groups
                    )
                    
                    if new_messages:
                        logger.info(f"Found {len(new_messages)} new message(s) for {conn.nickname}")
                        
                        # Process each new message
                        for msg in new_messages:
                            await self.process_new_message(db, conn, msg)
                    
                except Exception as e:
                    logger.error(f"Error monitoring connection {conn.id}: {e}", exc_info=True)
                    continue
    
    async def process_new_message(
        self,
        db: AsyncSession,
        conn: WhatsAppConnection,
        msg
    ):
        """
        Process new message from source group.
        
        1. Monetize URLs
        2. Queue for destination groups
        """
        try:
            # Monetize text
            monetized_text = await monetize_text(db, msg.text, str(conn.user_id))
            
            # Get destination groups
            dest_groups = [g["name"] for g in conn.destination_groups]
            
            if not dest_groups:
                logger.warning(f"Connection {conn.nickname} has no destination groups")
                return
            
            # Queue message for each destination group
            for group_name in dest_groups:
                self.queue_manager.add(
                    connection_id=str(conn.id),
                    group_name=group_name,
                    text=monetized_text
                )
                
                logger.info(f"Queued message for {group_name} (connection: {conn.nickname})")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def send_cycle(self):
        """
        Single send cycle - attempt to send queued messages.
        """
        async with AsyncSessionLocal() as db:
            # Get active connections
            connections = await self.get_active_connections(db)
            
            for conn in connections:
                try:
                    # Get destination groups
                    dest_groups = [g["name"] for g in conn.destination_groups]
                    
                    for group_name in dest_groups:
                        # Check if we have queued messages
                        if self.queue_manager.get_queue_size(group_name) == 0:
                            continue
                        
                        # Check rate limit
                        can_send = self.queue_manager.can_send(
                            connection_id=str(conn.id),
                            group_name=group_name,
                            min_interval_per_group=conn.min_interval_per_group,
                            min_interval_global=conn.min_interval_global
                        )
                        
                        if not can_send:
                            wait_time = self.queue_manager.get_time_until_next_send(
                                connection_id=str(conn.id),
                                group_name=group_name,
                                min_interval_per_group=conn.min_interval_per_group,
                                min_interval_global=conn.min_interval_global
                            )
                            logger.debug(f"Rate limit: {group_name} needs {wait_time}s more")
                            continue
                        
                        # Get message from queue
                        msg = self.queue_manager.get_next(group_name)
                        
                        if not msg:
                            continue
                        
                        # Send message
                        result = await self.gateway.send_message(
                            connection_id=str(conn.id),
                            group_name=group_name,
                            text=msg.text,
                            wait_for_preview=True
                        )
                        
                        if result["status"] == "sent":
                            # Remove from queue
                            self.queue_manager.pop(group_name)
                            
                            # Mark as sent
                            self.queue_manager.mark_sent(
                                connection_id=str(conn.id),
                                group_name=group_name
                            )
                            
                            logger.info(
                                f"✓ Sent to {group_name} (preview: {result.get('preview_generated')}, "
                                f"{result.get('duration_ms')}ms)"
                            )
                            
                            # TODO: Save to OfferLog
                        else:
                            logger.error(f"Failed to send to {group_name}: {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"Error in send cycle for {conn.id}: {e}", exc_info=True)
                    continue
    
    async def main_loop(self):
        """
        Main worker loop.
        
        Runs two concurrent tasks:
        1. Monitor task (check for new messages)
        2. Send task (process send queue)
        """
        logger.info("Starting main loop...")
        
        try:
            while self.running:
                # Run both cycles concurrently
                await asyncio.gather(
                    self.monitor_cycle(),
                    self.send_cycle(),
                    return_exceptions=True
                )
                
                # Small delay
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
        
        finally:
            logger.info("Main loop stopped")
    
    async def cleanup_cycle(self):
        """
        Periodic cleanup task.
        
        Runs every hour to:
        - Clear old queued messages
        - Check connection health
        """
        while self.running:
            try:
                # Clear old queues (messages older than 24h)
                self.queue_manager.clear_old_queues(max_age_hours=24)
                
                logger.info("Cleanup cycle completed")
            
            except Exception as e:
                logger.error(f"Cleanup cycle error: {e}")
            
            # Run every hour
            await asyncio.sleep(3600)


# ============================================================================
# GRACEFUL SHUTDOWN
# ============================================================================

worker_instance = None


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    
    if worker_instance:
        asyncio.create_task(worker_instance.stop())
        sys.exit(0)


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    global worker_instance
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Create worker
    worker_instance = WhatsAppWorker()
    
    try:
        # Start worker
        await worker_instance.start()
        
        # Run main loop and cleanup concurrently
        await asyncio.gather(
            worker_instance.main_loop(),
            worker_instance.cleanup_cycle()
        )
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    
    finally:
        await worker_instance.stop()


if __name__ == "__main__":
    asyncio.run(main())
