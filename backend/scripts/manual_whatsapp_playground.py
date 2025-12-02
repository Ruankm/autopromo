"""
Manual WhatsApp Web Playground (Debug Tool)
==========================================

Propósito:
  - Abrir WhatsApp Web com Playwright
  - Gerar QR code e fazer login
  - IR PARA ABA DE GRUPOS
  - COLETAR LISTA COMPLETA DE GRUPOS com scroll automático
  - Salvar dados em JSON
  - Exibir resumo formatado no console

Modo 1: Rodar DENTRO do Docker (headless)
-----------------------------------------------------------------
No host (Windows), dentro do diretório do projeto:

  cd C:\\Users\\Ruan\\Desktop\\autopromo
  docker-compose up -d
  docker-compose exec backend python backend/scripts/manual_whatsapp_playground.py

Modo 2: Rodar DIRETO no Windows (headful, com janela visível)
-------------------------------------------------------------
Pré-requisitos:
  - Python 3 instalado no Windows
  - Playwright instalado:
      cd C:\\Users\\Ruan\\Desktop\\autopromo
      pip install -r backend/requirements.txt
      playwright install chromium

Rodar:

  cd C:\\Users\\Ruan\\Desktop\\autopromo
  python backend/scripts/manual_whatsapp_playground.py --headful

Isso vai abrir uma janela real do Chromium, permitindo F12 para inspecionar DOM.
"""
import asyncio
import base64
import argparse
import os
import json
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


def parse_args():
    parser = argparse.ArgumentParser(
        description="Manual WhatsApp Web playground - Group Discovery Debug Tool."
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser with visible window (for local dev on Windows).",
    )
    return parser.parse_args()


async def collect_groups(page, logs_dir):
    """
    Collect all groups from WhatsApp Web Groups tab with auto-scroll.
    
    Returns:
        list[dict]: List of groups with display_name, last_message_time, 
                    last_message_preview, unread_count
    """
    print()
    print("=" * 70)
    print("GROUP DISCOVERY - STARTING COLLECTION")
    print("=" * 70)
    print()
    
    # 1) Click on Groups tab
    print("[DISCOVERY] Step 1: Clicking on 'Groups' tab...")
    try:
        groups_tab = await page.wait_for_selector(
            'button#group-filter[role="tab"][aria-controls="chat-list"]',
            timeout=10000
        )
        await groups_tab.click()
        print("[DISCOVERY] ✅ Groups tab clicked")
        
        # Wait for tab to be selected
        await page.wait_for_selector(
            'button#group-filter[aria-pressed="true"]',
            timeout=5000
        )
        print("[DISCOVERY] ✅ Groups tab selected (aria-pressed=true)")
    except PlaywrightTimeoutError:
        print("[DISCOVERY] ❌ Could not find or click Groups tab")
        print("[DISCOVERY] Selector: button#group-filter[role=\"tab\"]")
        return []
    
    await asyncio.sleep(1)  # Let the list load
    
    # 2) Get conversations grid
    print()
    print("[DISCOVERY] Step 2: Locating conversations grid...")
    try:
        grid = await page.wait_for_selector(
            'div[aria-label="Lista de conversas"][role="grid"]',
            timeout=10000
        )
        print("[DISCOVERY] ✅ Conversations grid found")
        
        # Try to get expected row count
        aria_rowcount = await grid.get_attribute("aria-rowcount")
        if aria_rowcount:
            print(f"[DISCOVERY] Expected rows (aria-rowcount): {aria_rowcount}")
        else:
            print("[DISCOVERY] aria-rowcount not available")
    except PlaywrightTimeoutError:
        print("[DISCOVERY] ❌ Could not find conversations grid")
        print("[DISCOVERY] Selector: div[aria-label=\"Lista de conversas\"][role=\"grid\"]")
        return []
    
    # 3) Collect groups with scroll
    print()
    print("[DISCOVERY] Step 3: Collecting groups (with auto-scroll)...")
    print()
    
    seen_names = set()
    groups = []
    max_iterations = 50  # Safety limit
    iteration = 0
    previous_scroll_top = -1
    no_change_count = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Get all visible rows
        rows = await grid.query_selector_all('div[role="row"]')
        print(f"[DISCOVERY] Iteration {iteration}: Found {len(rows)} visible rows")
        
        new_groups_this_iteration = 0
        
        for row in rows:
            try:
                # Extract display name
                title_el = await row.query_selector('div._ak8q span[dir="auto"][title]')
                if not title_el:
                    continue
                
                display_name = await title_el.get_attribute('title')
                if not display_name or display_name in seen_names:
                    continue
                
                seen_names.add(display_name)
                
                # Extract last message time
                time_el = await row.query_selector('div._ak8i.x1s688f')
                last_message_time = ""
                if time_el:
                    last_message_time = (await time_el.inner_text()).strip()
                
                # Extract last message preview
                preview_el = await row.query_selector('div._ak8k span.x78zum5.x1cy8zhl')
                last_message_preview = ""
                if preview_el:
                    # Try title first, then inner_text
                    preview = await preview_el.get_attribute('title')
                    if not preview:
                        preview = await preview_el.inner_text()
                    last_message_preview = preview.strip() if preview else ""
                
                # Extract unread count
                unread_el = await row.query_selector('span[aria-label$="mensagens não lidas"]')
                unread_count = 0
                if unread_el:
                    unread_text = await unread_el.inner_text()
                    try:
                        unread_count = int(unread_text.strip())
                    except ValueError:
                        unread_count = 0
                
                # Add to results
                groups.append({
                    "display_name": display_name,
                    "last_message_time": last_message_time,
                    "last_message_preview": last_message_preview,
                    "unread_count": unread_count
                })
                
                new_groups_this_iteration += 1
                
                # Log the first few for visibility
                if len(groups) <= 5:
                    preview_short = last_message_preview[:40] + "..." if len(last_message_preview) > 40 else last_message_preview
                    unread_badge = f" ({unread_count} não lidas)" if unread_count > 0 else ""
                    print(f"  ✓ [{last_message_time}] {display_name}{unread_badge}")
                    if preview_short:
                        print(f"    └─ {preview_short}")
            
            except Exception as e:
                # Skip rows that fail to parse
                continue
        
        print(f"[DISCOVERY] New groups found this iteration: {new_groups_this_iteration}")
        print(f"[DISCOVERY] Total unique groups so far: {len(groups)}")
        
        # Check if we have all expected groups
        if aria_rowcount and len(groups) >= int(aria_rowcount):
            print(f"[DISCOVERY] ✅ Collected all {len(groups)} groups (matched aria-rowcount)")
            break
        
        # Scroll down
        current_scroll_top = await grid.evaluate("el => el.scrollTop")
        scroll_height = await grid.evaluate("el => el.scrollHeight")
        
        print(f"[DISCOVERY] Scrolling... (current: {current_scroll_top}, height: {scroll_height})")
        
        await grid.evaluate("el => el.scrollBy(0, 1000)")
        await asyncio.sleep(0.5)  # Wait for new content to load
        
        # Check if scroll position changed
        new_scroll_top = await grid.evaluate("el => el.scrollTop")
        
        if new_scroll_top == previous_scroll_top:
            no_change_count += 1
            print(f"[DISCOVERY] Scroll position unchanged ({no_change_count}/3)")
            
            if no_change_count >= 3:
                print("[DISCOVERY] ✅ Reached bottom (scroll position stable)")
                break
        else:
            no_change_count = 0
        
        previous_scroll_top = new_scroll_top
        print()
    
    if iteration >= max_iterations:
        print(f"[DISCOVERY] ⚠️ Stopped at max iterations ({max_iterations})")
    
    print()
    print("=" * 70)
    print(f"COLLECTION COMPLETE: {len(groups)} unique groups found")
    print("=" * 70)
    print()
    
    return groups


def format_groups_console(groups):
    """Print groups in a nice readable format."""
    print()
    print("=" * 70)
    print("GROUPS SUMMARY")
    print("=" * 70)
    print()
    
    if not groups:
        print("  No groups found.")
        return
    
    # Sort by time (most recent first) - basic sorting
    # For simplicity, just reverse order if times look like HH:MM
    try:
        groups_sorted = sorted(groups, key=lambda g: g.get("last_message_time", ""), reverse=True)
    except:
        groups_sorted = groups
    
    for idx, group in enumerate(groups_sorted, 1):
        name = group.get("display_name", "Unknown")
        time = group.get("last_message_time", "")
        preview = group.get("last_message_preview", "")
        unread = group.get("unread_count", 0)
        
        # Format preview (max 50 chars)
        preview_short = preview[:50] + "..." if len(preview) > 50 else preview
        
        # Format unread badge
        unread_badge = f" 🔥 ({unread} não lidas)" if unread > 0 else ""
        
        # Print formatted line
        print(f"{idx:3d}. [{time:5s}] {name}{unread_badge}")
        if preview_short:
            print(f"      └─ {preview_short}")
    
    print()
    print("=" * 70)
    print()


async def ensure_groups_tab_selected(page):
    """
    Ensure the Groups tab is selected.
    Reusable function for both discovery and forwarding.
    """
    try:
        # Check if already selected
        already_selected = await page.query_selector('button#group-filter[aria-pressed="true"]')
        if already_selected:
            print("[FORWARD] ✅ Groups tab already selected")
            return True
        
        # Click to select
        print("[FORWARD] Clicking on Groups tab...")
        groups_tab = await page.wait_for_selector(
            'button#group-filter[role="tab"][aria-controls="chat-list"]',
            timeout=10000
        )
        await groups_tab.click()
        
        # Wait for selection
        await page.wait_for_selector(
            'button#group-filter[aria-pressed="true"]',
            timeout=5000
        )
        print("[FORWARD] ✅ Groups tab selected")
        await asyncio.sleep(0.5)
        return True
    
    except PlaywrightTimeoutError:
        print("[FORWARD] ❌ Could not find or select Groups tab")
        return False


async def find_and_open_group(page, target_name: str, max_scrolls: int = 30):
    """
    Find and open a group by name (case-insensitive, partial match).
    
    Args:
        page: Playwright page object
        target_name: Name (or part of name) of the group to find
        max_scrolls: Maximum scroll iterations
    
    Returns:
        bool: True if group found and opened, False otherwise
    """
    print(f"[FORWARD] Searching for group: '{target_name}'...")
    
    # Ensure Groups tab is selected
    if not await ensure_groups_tab_selected(page):
        return False
    
    # Normalize target name for comparison
    target_name_normalized = target_name.lower().strip()
    
    # Get conversations grid
    try:
        grid = await page.wait_for_selector(
            'div[aria-label="Lista de conversas"][role="grid"]',
            timeout=10000
        )
    except PlaywrightTimeoutError:
        print("[FORWARD] ❌ Could not find conversations grid")
        return False
    
    # IMPORTANT: Scroll to top first to ensure we start from beginning
    print("[FORWARD] Scrolling to top of conversations list...")
    await grid.evaluate("el => el.scrollTop = 0")
    await asyncio.sleep(0.5)  # Let it settle
    
    # Search with scroll
    for iteration in range(max_scrolls):
        print(f"[FORWARD] Search iteration {iteration + 1}/{max_scrolls}...")
        
        rows = await grid.query_selector_all('div[role="row"]')
        
        for row in rows:
            try:
                # Get group name
                name_el = await row.query_selector('div._ak8q span[dir="auto"][title]')
                if not name_el:
                    continue
                
                display_name = await name_el.get_attribute('title')
                if not display_name:
                    display_name = await name_el.inner_text()
                
                display_name_normalized = display_name.lower().strip()
                
                # Check if match (partial match, case-insensitive)
                if target_name_normalized in display_name_normalized:
                    print(f"[FORWARD] ✅ Found group: '{display_name}'")
                    print(f"[FORWARD] Clicking to open...")
                    
                    # Click on the row
                    await row.click()
                    
                    # Wait for chat to load
                    await asyncio.sleep(1.5)
                    
                    # Verify chat opened by checking for compose box
                    try:
                        await page.wait_for_selector(
                            'div[contenteditable="true"][data-lexical-editor="true"]',
                            timeout=5000
                        )
                        print(f"[FORWARD] ✅ Group '{display_name}' opened successfully")
                        return True
                    except PlaywrightTimeoutError:
                        print(f"[FORWARD] ⚠️ Group seems opened but compose box not found")
                        return True  # Still consider success
            
            except Exception as e:
                continue
        
        # Scroll down for more groups
        await grid.evaluate("el => el.scrollBy(0, 1000)")
        await asyncio.sleep(0.4)
    
    print(f"[FORWARD] ❌ Group '{target_name}' not found after {max_scrolls} scrolls")
    return False


async def get_last_message_text_in_open_chat(page, max_messages_to_check: int = 20):
    """
    Get the text of the last TEXT message in the currently open chat.
    
    - Traverses backwards (last → previous)
    - Ignores messages with no text (images, stickers, audio only)
    - Uses selectors compatible with current WhatsApp Web DOM:
      * Containers: div.message-in / div.message-out / div.focusable-list-item.message-*
      * Content: div.copyable-text + spans/divs with actual text
    
    Args:
        page: Playwright page object
        max_messages_to_check: Maximum number of messages to check (from last to first)
    
    Returns:
        str | None: Text of last text message, or None if not found
    """
    log_prefix = "[FORWARD]"
    
    try:
        # Give time for chat to finish rendering
        await page.wait_for_timeout(1000)
        
        # Message container selectors (from DOM inspection)
        msg_container_selector = (
            "div.focusable-list-item.message-in, "
            "div.focusable-list-item.message-out, "
            "div.message-in, "
            "div.message-out"
        )
        
        messages = page.locator(msg_container_selector)
        count = await messages.count()
        print(f"{log_prefix} Found {count} message containers in open chat")
        
        if count == 0:
            print(f"{log_prefix} ❌ No messages found in DOM")
            return None
        
        # Scan backwards, but limit quantity for safety
        start_index = max(0, count - max_messages_to_check)
        
        for idx in range(count - 1, start_index - 1, -1):
            msg = messages.nth(idx)
            
            # "Copyable content" of the message (from DOM structure)
            content = msg.locator("div.copyable-text")
            
            if await content.count() == 0:
                print(f"{log_prefix} Message #{idx} has no div.copyable-text, skipping (system/media)")
                continue
            
            # Inside copyable-text, extract ALL text and emojis
            # We need to recursively process the entire DOM tree
            # because text and emojis are mixed in various nested elements
            
            try:
                # Use JavaScript to extract text + emojis in order
                text = await content.evaluate("""
                    (element) => {
                        function extractTextAndEmojis(node) {
                            let result = [];
                            
                            for (let child of node.childNodes) {
                                if (child.nodeType === Node.TEXT_NODE) {
                                    // It's a text node - add the text
                                    let text = child.textContent.trim();
                                    if (text) {
                                        result.push(text);
                                    }
                                } else if (child.nodeType === Node.ELEMENT_NODE) {
                                    // It's an element
                                    if (child.tagName === 'IMG' && child.classList.contains('emoji')) {
                                        // It's an emoji image - get alt attribute
                                        let emoji = child.getAttribute('alt');
                                        if (emoji) {
                                            result.push(emoji);
                                        }
                                    } else if (child.tagName === 'BR') {
                                        // Line break
                                        result.push('\\n');
                                    } else {
                                        // Recursively process children
                                        result = result.concat(extractTextAndEmojis(child));
                                    }
                                }
                            }
                            
                            return result;
                        }
                        
                        let parts = extractTextAndEmojis(element);
                        return parts.join('');
                    }
                """)
                
                text = text.strip()
            except Exception as e:
                print(f"{log_prefix} Error extracting text with JS: {e}")
                # Fallback to simple inner_text
                text = await content.inner_text()
                text = text.strip()
            
            if text:
                preview = text.replace("\n", " ")[:120]
                print(f"{log_prefix} ✅ Last TEXT message found at index {idx}: {preview!r}")
                return text
            
            # If we got here, message is probably media-only (image, sticker, etc.)
            print(f"{log_prefix} Message #{idx} has no text (media only?), skipping")
        
        print(f"{log_prefix} ❌ No TEXT messages found in last {max_messages_to_check} messages")
        return None
    
    except Exception as e:
        print(f"{log_prefix} ❌ Error reading last message: {e}")
        return None


async def send_message_to_open_chat(page, text: str):
    """
    Send a message to the currently open chat.
    
    Uses multiple fallback selectors for the compose box to handle
    different WhatsApp Web versions.
    
    Args:
        page: Playwright page object
        text: Text to send
    """
    print("[FORWARD] Sending message to open chat...")
    
    # Multiple fallback selectors, starting with most specific
    # IMPORTANT: Use aria-label to distinguish from search field!
    selectors = [
        # 1) Most specific: editor with "Digitar" in aria-label (message field, not search)
        'div[aria-label*="Digitar"][data-lexical-editor="true"]',
        # 2) Role textbox with "Digitar" label
        'div[role="textbox"][aria-label*="Digitar"][data-lexical-editor="true"]',
        # 3) Broader: any lexical editor with textbox role
        'div[role="textbox"][data-lexical-editor="true"]',
        # 4) Fallback: paragraph inside any contenteditable (less safe)
        'div[contenteditable="true"] p.selectable-text.copyable-text',
    ]
    
    compose = None
    
    for selector in selectors:
        try:
            print(f"[FORWARD] Trying compose selector: {selector[:70]}...")
            loc = page.locator(selector).first
            await loc.wait_for(state="visible", timeout=4000)
            compose = loc
            print(f"[FORWARD] ✅ Compose box found!")
            break
        except PlaywrightTimeoutError:
            print(f"[FORWARD] ⚠️ Not found, trying next...")
            continue
    
    if compose is None:
        print("[FORWARD] ❌ Could not find any compose selector")
        raise Exception("Compose box not found with any selector")
    
    # Click the <p> element inside (the actual editable area)
    print("[FORWARD] Locating inner <p> element...")
    try:
        inner_p = compose.locator('p.selectable-text.copyable-text').first
        await inner_p.wait_for(state="visible", timeout=2000)
        print("[FORWARD] ✅ Found inner <p>, clicking...")
        await inner_p.click()
    except PlaywrightTimeoutError:
        print("[FORWARD] ⚠️ Inner <p> not found, clicking outer div...")
        await compose.click()
    
    await asyncio.sleep(0.3)
    
    # Clear any previous text (optional, but helps)
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Backspace")
    await asyncio.sleep(0.2)
    
    # Type the message LINE BY LINE with Shift+Enter for line breaks
    # This prevents WhatsApp from sending on each \n
    print(f"[FORWARD] ⌨️  Typing message ({len(text)} chars) line-by-line...")
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line:  # Only type non-empty lines
            await page.keyboard.type(line, delay=10)
        
        # Add line break with Shift+Enter (doesn't send message)
        if i < len(lines) - 1:  # Don't add extra line break after last line
            await page.keyboard.press("Shift+Enter")
            await asyncio.sleep(0.05)  # Small delay between lines
    
    # Wait 4 seconds for link preview to load (increased from 2s)
    print("[FORWARD] ⏳ Waiting 4s for link preview to load...")
    await page.wait_for_timeout(4000)
    
    # Try to detect if preview loaded - check multiple times
    preview_found = False
    for attempt in range(3):
        try:
            preview = page.locator('div._ahwq img[src^="data:image/jpeg;base64,"]').first
            await preview.wait_for(state="visible", timeout=1000)
            print(f"[FORWARD] ✅ Link preview detected on attempt {attempt + 1}")
            preview_found = True
            break
        except PlaywrightTimeoutError:
            if attempt < 2:
                print(f"[FORWARD] ⚠️ Preview not found yet, waiting 1s more...")
                await page.wait_for_timeout(1000)
    
    if not preview_found:
        print("[FORWARD] ⚠️ Link preview not detected after 6s total, sending anyway")
    
    # Now send
    print("[FORWARD] ⏎ Pressing Enter to send...")
    await page.keyboard.press("Enter")
    
    # Wait a bit to ensure message was sent
    await asyncio.sleep(1)
    
    print("[FORWARD] ✅ Message sent!")


async def copy_last_message_between_groups(page, source_name: str, target_name: str):
    """
    Copy the last message from source group to target group.
    
    Args:
        page: Playwright page object
        source_name: Name (or part) of source group
        target_name: Name (or part) of target group
    """
    print()
    print("=" * 70)
    print(f"COPYING MESSAGE: '{source_name}' → '{target_name}'")
    print("=" * 70)
    print()
    
    # Step 1: Open source group
    print("[FORWARD] Step 1: Opening source group...")
    success = await find_and_open_group(page, source_name)
    if not success:
        print("[FORWARD] ❌ Failed to open source group. Aborting.")
        return
    
    await asyncio.sleep(0.8)  # Let messages load
    
    # Step 2: Get last message text
    print()
    print("[FORWARD] Step 2: Reading last message...")
    last_message = await get_last_message_text_in_open_chat(page)
    if not last_message:
        print("[FORWARD] ❌ Could not read last message. Aborting.")
        return
    
    # Log full message (truncated)
    message_preview = last_message[:120] + "..." if len(last_message) > 120 else last_message
    print()
    print("-" * 70)
    print(f"MESSAGE TO FORWARD:")
    print(f"\"{message_preview}\"")
    print("-" * 70)
    print()
    
    # Step 3: Go back to Groups tab
    print("[FORWARD] Step 3: Returning to Groups tab...")
    await ensure_groups_tab_selected(page)
    await asyncio.sleep(0.5)
    
    # Step 4: Open target group
    print()
    print("[FORWARD] Step 4: Opening target group...")
    success = await find_and_open_group(page, target_name)
    if not success:
        print("[FORWARD] ❌ Failed to open target group. Aborting.")
        return
    
    await asyncio.sleep(0.8)
    
    # Step 5: Send the message
    print()
    print("[FORWARD] Step 5: Sending message to target group...")
    try:
        await send_message_to_open_chat(page, last_message)
        print()
        print("=" * 70)
        print("✅ MESSAGE FORWARDED SUCCESSFULLY!")
        print("=" * 70)
        print()
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ FAILED TO SEND MESSAGE: {e}")
        print("=" * 70)
        print()


async def main():
    args = parse_args()
    
    # Determine headless mode
    env_headless = os.getenv("WHATSAPP_PLAYGROUND_HEADLESS")
    if args.headful:
        headless = False
    elif env_headless is not None:
        headless = env_headless.lower() not in ("0", "false", "no")
    else:
        headless = True
    
    print("=" * 70)
    print("WHATSAPP WEB PLAYGROUND - GROUP DISCOVERY DEBUG TOOL")
    print("=" * 70)
    print(f"[PLAYGROUND] Mode: {'HEADLESS (invisible)' if headless else 'HEADFUL (visible window)'}")
    
    # Guarantee logs directory exists
    logs_dir = Path("/app/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"[PLAYGROUND] Logs directory: {logs_dir}")
    print()
    
    async with async_playwright() as p:
        print("[PLAYGROUND] Launching Chromium browser...")
        browser = await p.chromium.launch(headless=headless)
        
        print("[PLAYGROUND] Creating browser context...")
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        
        print("[PLAYGROUND] Opening https://web.whatsapp.com ...")
        await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        # ALWAYS take loading screenshot
        print("[PLAYGROUND] Taking loading screenshot...")
        loading_png_path = logs_dir / "manual_whatsapp_loading.png"
        await page.screenshot(path=str(loading_png_path), full_page=True)
        print(f"[PLAYGROUND] ✅ Loading screenshot saved to: {loading_png_path}")
        print()
        
        # Check if already logged in
        already_connected = False
        try:
            print("[PLAYGROUND] Checking if already logged in (#pane-side)...")
            await page.wait_for_selector("#pane-side", timeout=10000)
            already_connected = True
            print("[PLAYGROUND] ✅ Already logged in (pane-side found).")
        except PlaywrightTimeoutError:
            print("[PLAYGROUND] Not logged in yet.")
        
        if not already_connected:
            print("[PLAYGROUND] Not logged in. Starting QR capture process...")
            print()
            
            # Wait for QR code
            print("[PLAYGROUND] ⏳ Waiting for QR canvas (max 60s)...")
            
            try:
                qr_canvas = await page.wait_for_selector('canvas[aria-label*="QR"]', timeout=60000)
                print("[PLAYGROUND] ✅ QR canvas found!")
            except PlaywrightTimeoutError:
                print()
                print("=" * 70)
                print("❌ TIMEOUT: Could not find QR canvas in 60 seconds")
                print("=" * 70)
                
                error_png_path = logs_dir / "manual_whatsapp_qr_timeout.png"
                await page.screenshot(path=str(error_png_path), full_page=True)
                print(f"[PLAYGROUND] Timeout screenshot saved to: {error_png_path}")
                
                await browser.close()
                return
            
            # Capture QR
            print("[PLAYGROUND] Extracting QR code image from canvas...")
            data_url = await qr_canvas.evaluate("(canvas) => canvas.toDataURL('image/png')")
            base64_data = data_url.split(",")[1]
            
            qr_png_path = logs_dir / "manual_whatsapp_qr.png"
            with open(qr_png_path, "wb") as f:
                f.write(base64.b64decode(base64_data))
            
            print()
            print("=" * 70)
            print("✅ QR CODE SAVED SUCCESSFULLY!")
            print("=" * 70)
            print(f"File: {qr_png_path}")
            print()
            print("TO SCAN QR CODE:")
            print("-" * 70)
            print("1. On Windows host, run:")
            print(f"   cd C:\\Users\\Ruan\\Desktop\\autopromo")
            print(f"   docker cp autopromo-backend:/app/logs/manual_whatsapp_qr.png .")
            print()
            print("2. Open manual_whatsapp_qr.png and scan with phone")
            print("3. Press ENTER here after scanning")
            print("=" * 70)
            print()
            
            input("⏸️  Press ENTER after scanning QR code...")
            print()
            
            # Wait for login
            print("[PLAYGROUND] ⏳ Waiting for login to complete (max 60s)...")
            try:
                await page.wait_for_selector("#pane-side", timeout=60000)
                print("[PLAYGROUND] ✅ Login detected! Chat list loaded.")
            except PlaywrightTimeoutError:
                print("❌ TIMEOUT: Could not detect login")
                await browser.close()
                return
        
        # Take screenshot after login
        print()
        print("[PLAYGROUND] 📸 Taking screenshot of connected state...")
        connected_png_path = logs_dir / "manual_whatsapp_connected.png"
        await page.screenshot(path=str(connected_png_path), full_page=True)
        print(f"[PLAYGROUND] ✅ Screenshot saved to: {connected_png_path}")
        
        # MAIN FEATURE: Collect all groups
        groups = await collect_groups(page, logs_dir)
        
        # Print formatted summary
        format_groups_console(groups)
        
        # Save to JSON
        if groups:
            json_path = logs_dir / "manual_whatsapp_groups.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(groups, f, ensure_ascii=False, indent=2)
            
            print(f"[PLAYGROUND] ✅ Groups data saved to: {json_path}")
            print(f"[PLAYGROUND] Total groups saved: {len(groups)}")
            print()
            print("To copy JSON to Windows:")
            print(f"  cd C:\\Users\\Ruan\\Desktop\\autopromo")
            print(f"  docker cp autopromo-backend:/app/logs/manual_whatsapp_groups.json .")
            print()
            
            # Show first 5 examples
            if len(groups) >= 5:
                print("First 5 groups as example:")
                for i, g in enumerate(groups[:5], 1):
                    print(f"  {i}. {g['display_name']}")
                print()
        else:
            print("[PLAYGROUND] ⚠️ No groups found, JSON not created.")
        
        # INTERACTIVE MENU - Message Forwarding
        print()
        print("=" * 70)
        print("PLAYGROUND ACTIONS")
        print("=" * 70)
        print("1. Copy LAST message from one group to another")
        print("0. Exit (close browser)")
        print()
        
        choice = input("Choose an option (0/1): ").strip()
        
        if choice == "1":
            print()
            source_name = input("Enter (part of) SOURCE group name: ").strip()
            target_name = input("Enter (part of) TARGET group name: ").strip()
            
            if source_name and target_name:
                try:
                    await copy_last_message_between_groups(page, source_name, target_name)
                except Exception as e:
                    print(f"[PLAYGROUND] Error during forwarding: {e}")
            else:
                print("[PLAYGROUND] ⚠️ Both group names are required")
        
        # After action or if choice == "0", proceed to close
        if headless:
            print()
            print("[PLAYGROUND] ⏳ Keeping browser open for 10s before closing...")
            await asyncio.sleep(10)
        else:
            print()
            print("[PLAYGROUND] HEADFUL MODE: Browser window remains open.")
            print("[PLAYGROUND] You can:")
            print("  - Press F12 to inspect DOM")
            print("  - Interact with WhatsApp manually")
            print("  - Press CTRL+C when done")
            print()
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print()
                print("[PLAYGROUND] CTRL+C detected. Closing...")
        
        print()
        print("[PLAYGROUND] Closing browser...")
        await browser.close()
        print()
        print("=" * 70)
        print("PLAYGROUND SESSION COMPLETE")
        print("=" * 70)
        print()


if __name__ == "__main__":
    asyncio.run(main())
