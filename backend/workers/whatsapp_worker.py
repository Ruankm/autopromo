"""
WhatsApp Worker - Main worker loop for Playwright automation.

NEW ARCHITECTURE: Worker is sole owner of Playwright!
Backend delegates via Redis Pub/Sub.

Responsibilities:
- Process NEW_CONNECTION events (initialize Playwright, generate QR)
- login_cycle(): detect QR scan and login completion
- Monitor source groups for new messages (status='connected' only)
- Queue messages for sending
- Process send queue with rate limiting
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
import json
import base64
from typing import Dict, Set, Optional
from datetime import datetime
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


# QR Code selectors (fallbacks for different WhatsApp versions)
QR_SELECTORS = [
    'canvas[aria-label*="Scan me"]',
    'canvas[aria-label*="QR code"]',
    'div[data-ref] canvas',
    'canvas[aria-label*="escanear"]',  # Portuguese
]


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
        self.redis_subscriber = None
        
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
        
        # Subscribe to Redis commands (using .client property!)
        self.redis_subscriber = redis_client.client.pubsub()
        await self.redis_subscriber.subscribe("whatsapp:commands")
        logger.info("✓ Redis subscriber ready")
        
        self.running = True
        logger.info("=== Worker Ready ===")
    
    async def stop(self):
        """Stop worker gracefully."""
        logger.info("=== Stopping WhatsApp Worker ===")
        
        self.running = False
        
        # Unsubscribe from Redis
        if self.redis_subscriber:
            try:
                await self.redis_subscriber.unsubscribe("whatsapp:commands")
                await self.redis_subscriber.close()
            except Exception as e:
                logger.error(f"Error closing Redis subscriber: {e}")
        
        # Shutdown Playwright
        if self.gateway:
            await self.gateway.shutdown()
            logger.info("✓ Playwright gateway stopped")
        
        # Disconnect Redis
        await redis_client.disconnect()
        logger.info("✓ Redis disconnected")
        
        logger.info("=== Worker Stopped ===")
    
    # ========================================================================
    # REDIS COMMAND LISTENER
    # ========================================================================
    
    async def redis_command_listener(self):
        """
        Listen for Redis commands from Backend.
        
        Commands:
        - NEW_CONNECTION: Initialize new connection
        - REGENERATE_QR: Reload page to generate new QR
        """
        try:
            logger.info("Redis command listener started")
            
            async for message in self.redis_subscriber.listen():
                if not self.running:
                    break
                
                if message["type"] != "message":
                    continue
                
                try:
                    data = json.loads(message["data"])
                    cmd_type = data.get("type")
                    
                    logger.info(f"Received command: {cmd_type}")
                    
                    if cmd_type == "NEW_CONNECTION":
                        await self.handle_new_connection(data)
                    elif cmd_type == "REGENERATE_QR":
                        await self.handle_regenerate_qr(data)
                    elif cmd_type == "DISCOVER_GROUPS":
                        await self.handle_discover_groups(data)
                    else:
                        logger.warning(f"Unknown command type: {cmd_type}")
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in Redis message: {e}")
                except Exception as e:
                    logger.error(f"Error processing Redis command: {e}", exc_info=True)
        
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
        except Exception as e:
            logger.error(f"Redis listener error: {e}", exc_info=True)
    
    async def handle_new_connection(self, data: dict):
        """
        Handle NEW_CONNECTION command.
        
        Backend created a connection with status='pending'.
        We just log it - login_cycle() will process it.
        """
        conn_id = data.get("connection_id")
        nickname = data.get("nickname", "Unknown")
        
        logger.info(f"📝 NEW_CONNECTION: {nickname} ({conn_id})")
        logger.info(f"login_cycle() will process this connection")
    
    async def handle_regenerate_qr(self, data: dict):
        """
        Handle REGENERATE_QR command.
        
        QR expired, reload page to generate new one.
        """
        conn_id = data.get("connection_id")
        
        logger.info(f"🔄 REGENERATE_QR: {conn_id}")
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WhatsAppConnection).where(
                    WhatsAppConnection.id == conn_id
                )
            )
            conn = result.scalar_one_or_none()
            
            if not conn:
                logger.warning(f"Connection {conn_id} not found")
                return
            
            try:
                # Get context
                context = await self.gateway.pool.get_or_create(conn_id)
                if context.pages:
                    page = context.pages[0]
                    await page.reload()
                    
                    # Reset status to trigger new QR generation
                    conn.status = "qr_needed"
                    conn.qr_code_base64 = None
                    conn.qr_generated_at = None
                    await db.commit()
                    
                    logger.info(f"✓ Page reloaded for {conn_id}")
            
            except Exception as e:
                logger.error(f"Error regenerating QR for {conn_id}: {e}")
    
    # ========================================================================
    # LOGIN CYCLE - QR DETECTION & LOGIN MONITORING
    # ========================================================================
    
    async def login_cycle(self):
        """
        Monitor connections awaiting login.
        
        Processes connections with status:
        - pending: Open WhatsApp Web
        - qr_needed: Generate and save QR Code
        - connecting: Wait for login completion
        
        Once connected, monitor_cycle() takes over.
        """
        async with AsyncSessionLocal() as db:
            # Get connections awaiting login
            result = await db.execute(
                select(WhatsAppConnection).where(
                    WhatsAppConnection.status.in_(["pending", "qr_needed", "connecting"])
                )
            )
            connections = result.scalars().all()
            
            if not connections:
                return
            
            for conn in connections:
                try:
                    conn_id = str(conn.id)
                    
                    # Get or create persistent context
                    context = await self.gateway.pool.get_or_create(conn_id)
                    
                    # Ensure we have a page
                    if not context.pages:
                        page = await context.new_page()
                    else:
                        page = context.pages[0]
                    
                    # === PENDING: Open WhatsApp Web ===
                    if conn.status == "pending":
                        logger.info(f"📱 Opening WhatsApp Web for {conn.nickname}")
                        await page.goto(
                            "https://web.whatsapp.com",
                            wait_until="networkidle",
                            timeout=60000
                        )
                        
                        conn.status = "qr_needed"
                        await db.commit()
                        logger.info(f"✓ WhatsApp Web opened for {conn.nickname}")
                        continue
                    
                    # === QR_NEEDED: Generate and save QR ===
                    if conn.status == "qr_needed":
                        # Check if QR needs update (first gen or >50s old)
                        should_update_qr = (
                            not conn.qr_generated_at or
                            (datetime.utcnow() - conn.qr_generated_at).total_seconds() > 50
                        )
                        
                        if should_update_qr:
                            qr_element = await self._get_qr_element(page)
                            
                            if qr_element:
                                try:
                                    # Screenshot QR code
                                    qr_bytes = await qr_element.screenshot()
                                    qr_base64 = base64.b64encode(qr_bytes).decode()
                                    
                                    # Save to database
                                    conn.qr_code_base64 = qr_base64
                                    conn.qr_generated_at = datetime.utcnow()
                                    await db.commit()
                                    
                                    logger.info(f"✓ QR code generated for {conn.nickname}")
                                
                                except Exception as e:
                                    logger.error(f"Error capturing QR for {conn_id}: {e}")
                        
                        # Check if user scanned QR
                        if await self._is_logged_in(page):
                            conn.status = "connecting"
                            await db.commit()
                            logger.info(f"📲 QR scanned for {conn.nickname}, connecting...")
                        
                        continue
                    
                    # === CONNECTING: Wait for full connection ===
                    if conn.status == "connecting":
                        if await self._is_fully_connected(page):
                            conn.status = "connected"
                            conn.last_activity_at = datetime.utcnow()
                            conn.qr_code_base64 = None  # Clear QR
                            conn.qr_generated_at = None
                            await db.commit()
                            
                            logger.info(f"✅ {conn.nickname} fully connected!")
                        
                        continue
                
                except Exception as e:
                    logger.error(f"Error in login_cycle for {conn.id}: {e}", exc_info=True)
                    continue
    
    async def _get_qr_element(self, page):
        """Try multiple selectors to find QR code element."""
        for selector in QR_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    return element
            except Exception:
                continue
        return None
    
    async def _is_logged_in(self, page) -> bool:
        """Check if WhatsApp Web is logged in (QR disappeared)."""
        try:
            qr = await self._get_qr_element(page)
            return qr is None
        except Exception:
            return False
    
    async def _is_fully_connected(self, page) -> bool:
        """Check if WhatsApp Web is fully loaded and ready."""
        try:
            # Check if chat list sidebar is visible
            sidebar = await page.query_selector('[data-testid="chat-list"]')
            if sidebar:
                return True
            
            # Fallback: check for main app container
            app = await page.query_selector('#app')
            if app:
                # Additional check: no loading screen
                loading = await page.query_selector('[data-testid="loader"]')
                return loading is None
            
            return False
        
        except Exception:
            return False
    
    # ========================================================================
    # MONITOR CYCLE - MESSAGE DETECTION (connected only)
    # ========================================================================
    
    async def get_active_connections(self, db: AsyncSession) -> list[WhatsAppConnection]:
        """
        Get all CONNECTED WhatsApp connections.
        
        Only 'connected' status is monitored for messages.
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
        Monitor source groups for new messages.
        
        Only processes connections with status='connected'.
        """
        async with AsyncSessionLocal() as db:
            connections = await self.get_active_connections(db)
            
            if not connections:
                return
            
            for conn in connections:
                try:
                    source_groups = [g["name"] for g in conn.source_groups]
                    
                    if not source_groups:
                        continue
                    
                    # Check for new messages
                    new_messages = await self.gateway.get_new_messages(
                        connection_id=str(conn.id),
                        source_groups=source_groups
                    )
                    
                    if new_messages:
                        logger.info(f"Found {len(new_messages)} new message(s) for {conn.nickname}")
                        
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
    
    # ========================================================================
    # SEND CYCLE - MESSAGE SENDING (connected only)
    # ========================================================================
    
    async def send_cycle(self):
        """
        Send queued messages with rate limiting.
        
        Only processes connections with status='connected'.
        """
        async with AsyncSessionLocal() as db:
            connections = await self.get_active_connections(db)
            
            for conn in connections:
                try:
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
    
    # ========================================================================
    # MAIN LOOP
    # ========================================================================
    
    async def main_loop(self):
        """
        Main worker loop.
        
        Runs THREE concurrent cycles:
        1. login_cycle() - Process pending/qr_needed/connecting
        2. monitor_cycle() - Monitor messages (connected only)
        3. send_cycle() - Send queued messages (connected only)
        """
        logger.info("Starting main loop...")
        
        try:
            while self.running:
                # Run all three cycles concurrently
                await asyncio.gather(
                    self.login_cycle(),     # NEW!
                    self.monitor_cycle(),   # connected only
                    self.send_cycle(),      # connected only
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
        
        Runs every hour to clear old queued messages.
        """
        while self.running:
            try:
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
        
        # Run: main_loop + cleanup + Redis listener
        await asyncio.gather(
            worker_instance.main_loop(),
            worker_instance.cleanup_cycle(),
            worker_instance.redis_command_listener()  # NEW!
        )
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    
    finally:
        await worker_instance.stop()


if __name__ == "__main__":
    asyncio.run(main())    # ========================================================================
    # GROUP DISCOVERY - DOM-BASED HELPERS (NEW!)
    # ========================================================================
    
    async def handle_discover_groups(self, data: dict):
        """
        Handle DISCOVER_GROUPS command - DOM scraping via aba "Grupos".
        
        Strategy:
        1. Navigate to WhatsApp Web
        2. Click "Grupos" tab (filters only groups)
        3. Scroll list multiple times to load all
        4. Extract display_name via DOM for each group
        5. Save to DB (UPSERT)
        
        NO JID extraction - not needed in this version.
        """
        conn_id = data.get("connection_id")
        
        logger.info(f"🔍 DISCOVER_GROUPS: {conn_id}")
        
        async with AsyncSessionLocal() as db:
            from models.whatsapp_group import WhatsAppGroup
            from sqlalchemy.dialects.postgresql import insert
            
            conn = await db.get(WhatsAppConnection, conn_id)
            if not conn:
                logger.error(f"Connection {conn_id} not found")
                return
            
            try:
                # Get Playwright page
                context = await self.gateway.pool.get_or_create(conn_id)
                page = context.pages[0]
                
                # Ensure we're on WhatsApp Web
                await page.goto("https://web.whatsapp.com", wait_until="networkidle", timeout=60000)
                
                # 1. Try to click "Grupos" tab (optional)
                try:
                    groups_tab = await page.wait_for_selector(
                        'button[aria-label*="Grupos"], button:has-text("Grupos")',
                        timeout=10000
                    )
                    await groups_tab.click()
                    await page.wait_for_timeout(1000)
                    logger.info("✓ Clicked 'Grupos' tab")
                except Exception as e:
                    logger.warning(f"Could not click Grupos tab: {e}. Continuing with all chats...")
                
                # 2. Scroll to load all groups
                chat_list_selector = '[data-testid="chat-list"]'
                chat_list = await page.wait_for_selector(chat_list_selector, timeout=20000)
                
                logger.info("Scrolling to load all groups...")
                for i in range(15):  # 15 scrolls
                    await chat_list.evaluate("el => el.scrollBy(0, 1000)")
                    await page.wait_for_timeout(500)
                
                # 3. Extract groups via DOM
                groups = []
                chat_items = await page.query_selector_all('[data-testid^="cell-frame-container"]')
                
                logger.info(f"Found {len(chat_items)} chat items, extracting groups...")
                
                for item in chat_items:
                    try:
                        # Check if it's a group (has group icon)
                        is_group = await item.query_selector('[data-icon="group"]')
                        if not is_group:
                            continue  # Skip private chats
                        
                        # Extract group name
                        title_el = await item.query_selector('[title]')
                        if not title_el:
                            continue
                        
                        display_name = await title_el.get_attribute('title')
                        
                        # Extract last message preview (optional)
                        preview_el = await item.query_selector('.selectable-text')
                        last_message_preview = None
                        if preview_el:
                            last_message_preview = await preview_el.text_content()
                        
                        groups.append({
                            "display_name": display_name,
                            "last_message_preview": last_message_preview[:200] if last_message_preview else None
                        })
                        
                        logger.debug(f"Found group: {display_name}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting group: {e}")
                        continue
                
                # 4. Save to DB (UPSERT)
                saved_count = 0
                for g in groups:
                    stmt = insert(WhatsAppGroup).values(
                        connection_id=conn_id,
                        display_name=g["display_name"],
                        last_message_preview=g["last_message_preview"],
                        last_sync_at=datetime.utcnow()
                    ).on_conflict_do_update(
                        index_elements=["connection_id", "display_name"],
                        set_={
                            "last_message_preview": g["last_message_preview"],
                            "last_sync_at": datetime.utcnow()
                        }
                    )
                    await db.execute(stmt)
                    saved_count += 1
                
                await db.commit()
                logger.info(f"✓ Discovered and saved {saved_count} groups for connection {conn_id}")
            
            except Exception as e:
                logger.error(f"Error in handle_discover_groups: {e}", exc_info=True)
    
    async def open_group_by_search(
        self,
        page,
        group_display_name: str,
        validate_name: bool = True
    ) -> bool:
        """
        Opens a group using WhatsApp Web search field.
        
        Imitates human behavior:
        1. Click on search field
        2. Type group name
        3. Wait for results
        4. Click first result
        5. Optionally validate opened correct group
        
        Args:
            page: Playwright page
            group_display_name: Group name (ex: "Escorrega o Preço")
            validate_name: If True, confirms name in header
            
        Returns:
            True if successfully opened, False otherwise
        """
        import random
        
        try:
            # 1. Focus on search field (top of chat list)
            search_selector = '[data-testid="chat-list-search"]'
            search_box = await page.wait_for_selector(search_selector, timeout=10000)
            
            # 2. Clear previous search (if any)
            await search_box.click()
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Backspace')
            
            # 3. Type group name (with human delay)
            for char in group_display_name:
                await page.keyboard.type(char)
                await page.wait_for_timeout(random.randint(50, 150))
            
            # 4. Wait for results to appear
            await page.wait_for_timeout(1000)
            
            # 5. Click first result
            first_result = '[data-testid="cell-frame-container"]:first-child'
            await page.wait_for_selector(first_result, timeout=5000)
            await page.click(first_result)
            
            # 6. Wait for conversation to open
            await page.wait_for_timeout(1500)
            
            # 7. Validate name in header (optional)
            if validate_name:
                header_selector = '[data-testid="conversation-header"] [title]'
                header = await page.query_selector(header_selector)
                if header:
                    actual_name = await header.get_attribute('title')
                    if group_display_name.lower() not in actual_name.lower():
                        logger.warning(f"Nome não bate: esperado '{group_display_name}', got '{actual_name}'")
                        return False
            
            logger.info(f"✓ Opened group: {group_display_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open group '{group_display_name}': {e}")
            return False
    
    async def send_message_to_group(
        self,
        page,
        group_display_name: str,
        message_text: str,
        wait_for_preview: bool = True
    ) -> bool:
        """
        Sends message to group using search.
        
        Human flow:
        1. Open group via search
        2. Click compose field
        3. Type message (with link)
        4. Wait for preview to load (2-3 seconds)
        5. Click send
        """
        import random
        
        try:
            # 1. Open group
            if not await self.open_group_by_search(page, group_display_name):
                return False
            
            # 2. Focus compose field
            compose_selector = '[data-testid="conversation-compose-box-input"]'
            compose_box = await page.wait_for_selector(compose_selector, timeout=10000)
            await compose_box.click()
            
            # 3. Type message (slowly, like human)
            lines = message_text.split('\n')
            for i, line in enumerate(lines):
                for char in line:
                    await page.keyboard.type(char)
                    await page.wait_for_timeout(random.randint(30, 100))
                
                # Enter for line break (except last)
                if i < len(lines) - 1:
                    await page.keyboard.press('Shift+Enter')
            
            # 4. Wait for preview to load (if has link)
            if wait_for_preview and ('http://' in message_text or 'https://' in message_text):
                logger.info("Waiting for link preview to load...")
                await page.wait_for_timeout(3000)  # 3 seconds for preview
            
            # 5. Send message
            send_button = '[data-testid="send"]'
            await page.wait_for_selector(send_button, timeout=5000)
            await page.click(send_button)
            
            # 6. Wait for send confirmation
            await page.wait_for_timeout(1000)
            
            logger.info(f"✓ Sent message to {group_display_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {group_display_name}: {e}")
            return False


