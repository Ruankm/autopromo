    # ========================================================================
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
