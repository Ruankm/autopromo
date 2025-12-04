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
  - COPIAR mensagens entre grupos (single + multi-message com scroll)

USAGE INSTRUCTIONS:

1. DOCKER (Headless Mode):
   cd C:/Users/Ruan/Desktop/autopromo
   docker-compose up -d
   docker-compose exec backend python backend/scripts/manual_whatsapp_playground.py

2. WINDOWS (Headful Mode - Visual Debugging):
   cd C:/Users/Ruan/Desktop/autopromo
   pip install -r backend/requirements.txt
   playwright install chromium
   python backend/scripts/manual_whatsapp_playground.py --headful

CONFIGURATION:
  Edit the constants below to configure message forwarding defaults:
  - SOURCE_GROUP_NAME: Group to copy messages FROM
  - TARGET_GROUP_NAME: Group to send messages TO
  - MESSAGES_TO_FORWARD: How many messages to collect (default)
  - MAX_SCROLLS_FOR_MESSAGES: Max scroll-up iterations when collecting
  - DELAY_BETWEEN_MESSAGES: Seconds to wait between sending each message
"""
import asyncio
import base64
import argparse
import os
import json
from pathlib import Path
from dataclasses import dataclass
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# ============================================================================
# PLAYGROUND CONFIGURATION
# ============================================================================
SOURCE_GROUP_NAME = "Escorrega o Preço | 121 🔥"  # Can be partial match
TARGET_GROUP_NAME = "Autopromo"                    # Can be partial match
MESSAGES_TO_FORWARD = 5                            # Number of messages to collect
MAX_SCROLLS_FOR_MESSAGES = 10                      # Max scroll iterations when collecting
DELAY_BETWEEN_MESSAGES = 2.0                       # Seconds between sending each message
# ============================================================================


@dataclass
class ScrapedMessage:
    """Represents a scraped message from WhatsApp."""
    text: str
    index: int  # Position in chat (for ordering oldest to newest)


def dedupe_lines_preserving_order(text: str) -> str:
    """
    Remove duplicate lines from text while preserving order.
    Fixes the bug where link card subtitles are duplicated.
    
    Args:
        text: Raw text with potential duplicates
        
    Returns:
        Text with duplicate lines removed, emojis preserved
    """
    lines = text.split('\n')
    seen = set()
    result = []
    
    for line in lines:
        norm = line.strip()
        if not norm:
            # Keep empty lines for formatting, but don't duplicate consecutive ones
            if not result or result[-1] != '':
                result.append('')
            continue
        
        if norm in seen:
            continue  # Skip duplicate line
        
        seen.add(norm)
        result.append(line)
    
    return '\n'.join(result)


def normalize_link_message(text: str) -> str:
    """
    Aggressively normalize link messages (Mercado Livre, Amazon, etc.) to fix:
      - Redundant domain-only lines when full URL exists
      - Duplicate titles (with/without emoji)
      - Duplicate URLs
    
    Args:
        text: Text after dedupe_lines_preserving_order
        
    Returns:
        Normalized text with link card issues fixed
    """
    import re
    
    lines = text.split('\n')
    
    # Debug logging
    print("[NORMALIZE] INPUT:")
    for i, line in enumerate(lines[:10], 1):  # Show first 10 lines
        print(f"  {i}. {line[:80]!r}")
    if len(lines) > 10:
        print(f"  ... ({len(lines)} total lines)")
    
    # Step 1: Fix concatenated domain+title
    # Example: "mercadolivre.comPower Bank..." -> two lines
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed_lines.append('')
            continue
        
        # Pattern: domain.com[Title with Capital]
        domain_title_pattern = r'^([\w.-]+\.(com|com\.br|net|org|to))([A-ZÀ-Ú][^\s].*)$'
        match = re.match(domain_title_pattern, stripped)
        
        if match:
            domain = match.group(1)
            title = match.group(3)
            fixed_lines.append(domain)
            if title.strip():
                fixed_lines.append(title)
        else:
            fixed_lines.append(line)
    
    # Step 2: Identify all URLs and domain-only lines
    url_pattern = r'https?://\S+'
    all_urls = []
    domain_only_lines = set()
    
    for line in fixed_lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Find URLs
        urls = re.findall(url_pattern, stripped)
        all_urls.extend(urls)
        
        # Identify domain-only lines (mercadolivre.com, amazon.com.br, amzn.to, etc.)
        if re.match(r'^([\w.-]+\.(com|com\.br|net|org|to))$', stripped):
            domain_only_lines.add(stripped)
    
    has_full_url = len(all_urls) > 0
    
    # Step 3: Remove redundant domains if we have full URLs
    result = []
    for line in fixed_lines:
        stripped = line.strip()
        
        if not stripped:
            result.append('')
            continue
        
        # Skip domain-only lines if we have full URLs
        if has_full_url and stripped in domain_only_lines:
            continue  # Remove redundant domain
        
        result.append(line)
    
    # Step 4: Dedupe URLs (keep richer version)
    seen_urls = {}  # url -> line
    final_result = []
    
    for line in result:
        stripped = line.strip()
        
        if not stripped:
            final_result.append('')
            continue
        
        # Check if line contains URL
        urls = re.findall(url_pattern, stripped)
        
        if urls:
            url = urls[0]  # Take first URL
            
            if url in seen_urls:
                # Duplicate URL - keep richer line
                existing = seen_urls[url]
                if len(stripped) > len(existing):
                    # Replace with richer version
                    # Find and replace in final_result
                    for i, existing_line in enumerate(final_result):
                        if existing_line.strip() == existing:
                            final_result[i] = line
                            break
                    seen_urls[url] = stripped
                # Skip this line
                continue
            else:
                seen_urls[url] = stripped
                final_result.append(line)
        else:
            # No URL in this line
            final_result.append(line)
    
    # Step 5: Dedupe similar titles (aggressive for product names)
    # Normalize titles by removing emoji, punctuation, extra spaces
    def normalize_title(text):
        # Remove emojis (rough pattern)
        text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+', '', text)
        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
    
    def is_title_line(line):
        """Check if line looks like a product title (not price, not CUPOM, not URL)"""
        stripped = line.strip()
        if not stripped:
            return False
        # Exclude lines with price markers, CUPOM, URL indicators
        if any(marker in stripped for marker in ['R$', 'CUPOM', 'Acesse', 'https://', 'http://']):
            return False
        # Exclude lines starting with emoji or symbols only
        if re.match(r'^[^\w]+', stripped):
            return False
        return True
    
    deduped_result = []
    seen_titles = {}  # normalized_title -> original line
    
    for line in final_result:
        stripped = line.strip()
        
        if not stripped:
            deduped_result.append('')
            continue
        
        if is_title_line(line):
            normalized = normalize_title(stripped)
            
            if normalized in seen_titles:
                # Duplicate title - keep the richer one (usually with emoji)
                existing = seen_titles[normalized]
                if len(stripped) > len(existing):
                    # Replace existing with richer version
                    for i, existing_line in enumerate(deduped_result):
                        if existing_line.strip() == existing:
                            deduped_result[i] = line
                            break
                    seen_titles[normalized] = stripped
                # Skip this line
                continue
            else:
                seen_titles[normalized] = stripped
                deduped_result.append(line)
        else:
            # Not a title, keep as-is
            deduped_result.append(line)
    
    output_text = '\n'.join(deduped_result)
    
    # Debug logging
    output_lines = output_text.split('\n')
    print("[NORMALIZE] OUTPUT:")
    for i, line in enumerate(output_lines[:10], 1):
        print(f"  {i}. {line[:80]!r}")
    if len(output_lines) > 10:
        print(f"  ... ({len(output_lines)} total lines)")
    
    # Summary
    removed_count = len(lines) - len(output_lines)
    if removed_count > 0:
        print(f"[NORMALIZE] Removed {removed_count} redundant lines")
    
    return output_text


def parse_args():
    parser = argparse.ArgumentParser(
        description="Manual WhatsApp Web playground - Group Discovery & Message Forwarding Tool."
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser with visible window (for local dev on Windows).",
    )
    return parser.parse_args()


async def get_conversations_scroll_container(page):
    """
    Get the actual scrollable container for the conversations list.
    The grid itself doesn't scroll - its parent container does.
    
    Returns:
        Playwright ElementHandle for the scroll container, or None if not found
    """
    try:
        # First get the grid
        grid = await page.wait_for_selector(
            'div[aria-label="Lista de conversas"][role="grid"]',
            timeout=5000
        )
        
        # The parent of the grid is typically the scroll container
        # Use JavaScript to find the scrollable parent
        scroll_container = await page.evaluate("""
            () => {
                const grid = document.querySelector('div[aria-label="Lista de conversas"][role="grid"]');
                if (!grid) return null;
                
                // Walk up the DOM tree to find the scrollable parent
                let parent = grid.parentElement;
                while (parent) {
                    const style = window.getComputedStyle(parent);
                    const overflowY = style.overflowY;
                    const scrollHeight = parent.scrollHeight;
                    const clientHeight = parent.clientHeight;
                    
                    // Found a scrollable container
                    if ((overflowY === 'auto' || overflowY === 'scroll') && scrollHeight > clientHeight) {
                        // Return a unique identifier
                        if (!parent.id) {
                            parent.id = 'conversations-scroll-container-' + Date.now();
                        }
                        return parent.id;
                    }
                    
                    parent = parent.parentElement;
                }
                
                return null;
            }
        """)
        
        if scroll_container:
            print(f"[SCROLL] ✅ Found scroll container: #{scroll_container}")
            return await page.wait_for_selector(f"#{scroll_container}")
        else:
            print("[SCROLL] ⚠️ Could not find scroll container, falling back to grid")
            return grid
            
    except Exception as e:
        print(f"[SCROLL] ❌ Error finding scroll container: {e}")
        return None


async def ensure_chat_scrolled_to_bottom(page):
    """
    Ensure the chat panel is scrolled to the bottom (most recent messages).
    Useful when opening a chat that may have the "new messages" arrow visible.
    
    Logs scroll position before and after.
    """
    log_prefix = "[CHAT_SCROLL]"
    
    try:
        # Find the conversation panel
        panel = await page.wait_for_selector(
            '[data-testid="conversation-panel-body"]',
            timeout=5000
        )
        
        # Get current scroll position
        scroll_info_before = await panel.evaluate("""
            (el) => ({
                scrollTop: el.scrollTop,
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight
            })
        """)
        
        print(f"{log_prefix} Before scroll: top={scroll_info_before['scrollTop']}, "
              f"height={scroll_info_before['scrollHeight']}, "
              f"client={scroll_info_before['clientHeight']}")
        
        # Scroll to bottom
        await panel.evaluate("(el) => { el.scrollTop = el.scrollHeight; }")
        
        # Wait for any lazy-loaded content
        await asyncio.sleep(0.5)
        
        # Get new scroll position
        scroll_info_after = await panel.evaluate(
            "(el) => ({ scrollTop: el.scrollTop, scrollHeight: el.scrollHeight })"
        )
        
        print(f"{log_prefix} After scroll: top={scroll_info_after['scrollTop']}, "
              f"height={scroll_info_after['scrollHeight']}")
        
        if scroll_info_after['scrollTop'] > scroll_info_before['scrollTop']:
            print(f"{log_prefix} ✅ Scrolled down by {scroll_info_after['scrollTop'] - scroll_info_before['scrollTop']}px")
        else:
            print(f"{log_prefix} ✅ Already at bottom")
            
    except Exception as e:
        print(f"{log_prefix} ❌ Error scrolling chat to bottom: {e}")


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
    
    # 2) Get conversations grid and scroll container
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
    
    # Get the actual scroll container (parent of grid)
    print("[DISCOVERY] Finding scroll container...")
    scroll_container = await get_conversations_scroll_container(page)
    if not scroll_container:
        print("[DISCOVERY] ❌ Could not find scroll container, aborting")
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
        
        # Scroll down using the correct scroll container
        current_scroll_top = await scroll_container.evaluate("el => el.scrollTop")
        scroll_height = await scroll_container.evaluate("el => el.scrollHeight")
        
        print(f"[DISCOVERY] Scrolling... (current: {current_scroll_top}, height: {scroll_height})")
        
        await scroll_container.evaluate("el => el.scrollBy(0, 1000)")
        await asyncio.sleep(0.5)  # Wait for new content to load
        
        # Check if scroll position changed
        new_scroll_top = await scroll_container.evaluate("el => el.scrollTop")
        
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


async def get_conversations_search_input(page):
    """
    Get the search input field from the conversations SIDEBAR (not the message composer).
    
    Returns:
        Playwright ElementHandle for search input, or None if not found
    """
    try:
        # The search is inside #side (the left sidebar)
        # More specific selectorsthan just contenteditable to avoid composer
        search_selectors = [
            # Most specific: inside #side container
            '#side div[contenteditable="true"][data-tab="3"]',
            # Alternative: search by parent structure
            'div[role="textbox"][data-tab="3"]',
            # Fallback: first contenteditable in #side
            '#side div[contenteditable="true"]',
        ]
        
        for selector in search_selectors:
            try:
                search_input = await page.wait_for_selector(selector, timeout=2000)
                if search_input:
                    print(f"[SEARCH] ✅ Found search input: {selector}")
                    return search_input
            except PlaywrightTimeoutError:
                continue
        
        print("[SEARCH] ⚠️ Could not find search input in sidebar")
        return None
        
    except Exception as e:
        print(f"[SEARCH] ❌ Error finding search input: {e}")
        return None


async def clear_search_input_if_present(page):
    """
    Clear the search input field if it exists and has text.
    Useful to restore normal conversation list after search.
    """
    try:
        search_input = await get_conversations_search_input(page)
        if search_input:
            await search_input.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Escape")  # Close search
            await asyncio.sleep(0.3)
            print("[SEARCH] ✅ Search input cleared")
            return True
        return False
    except Exception as e:
        print(f"[SEARCH] ⚠️ Error clearing search: {e}")
        return False


async def _click_row_and_wait_chat_open(page, row, display_name: str) -> bool:
    """
    Click on a conversation row and wait for the chat to actually open.
    
    Validates chat opened by checking for:
      - Chat header with name
      - Compose message field
    
    Returns:
        bool: True if chat opened successfully, False otherwise
    """
    try:
        # Click the row
        await row.click()
        print(f"[FORWARD] Clicked on row for: '{display_name}'")
        
        # Wait for chat to load - try multiple indicators
        chat_opened = False
        
        # Option 1: Wait for chat header
        try:
            await page.wait_for_selector(
                'header div[role="button"] span[dir="auto"]',
                timeout=3000
            )
            chat_opened = True
        except PlaywrightTimeoutError:
            pass
        
        # Option 2: Wait for compose field (from send_message_to_open_chat selectors)
        if not chat_opened:
            try:
                await page.wait_for_selector(
                    'div[aria-label*="Digitar"][data-lexical-editor="true"]',
                    timeout=3000
                )
                chat_opened = True
            except PlaywrightTimeoutError:
                pass
        
        if chat_opened:
            print(f"[FORWARD] ✅ Chat '{display_name}' opened successfully")
            return True
        else:
            print(f"[FORWARD] ⚠️ Row clicked but chat header/compose not found for '{display_name}'")
            return False
            
    except Exception as e:
        print(f"[FORWARD] ❌ Error clicking row for '{display_name}': {e}")
        return False


async def find_and_open_group(page, target_name: str, max_scrolls: int = 30):
    """
    Find and open a group/contact by name (case-insensitive, partial match).
    
    Strategy (NEW ORDER):
      1. Try SCROLL through conversations list FIRST (most reliable)
      2. If scroll fails, fallback to SEARCH field (works for any chat type)
    
    Args:
        page: Playwright page object
        target_name: Name (or part of name) of the group/contact to find
        max_scrolls: Maximum scroll iterations
    
    Returns:
        bool: True if chat found and opened, False otherwise
    """
    print(f"[FORWARD] Searching for group: '{target_name}'...")
    
    # Normalize target name for comparison
    target_name_normalized = target_name.lower().strip()
    
    # ========================================================================
    # STEP A: Try SCROLL method first (most reliable, uses #pane-side)
    # ========================================================================
    print("[FORWARD] Step A: Scanning list with scroll...")
    
    # Ensure Groups tab is selected for scroll
    if not await ensure_groups_tab_selected(page):
        print("[FORWARD] ⚠️ Could not select Groups tab, will try search anyway")
    else:
        # Try scroll method
        try:
            # Get conversations grid
            grid = await page.wait_for_selector(
                'div[aria-label="Lista de conversas"][role="grid"]',
                timeout=10000
            )
            
            # Get scroll container (#pane-side)
            scroll_container = await get_conversations_scroll_container(page)
            if not scroll_container:
                print("[FORWARD] ⚠️ Could not find scroll container, skipping to search")
            else:
                # Scroll to top first
                await scroll_container.evaluate("el => el.scrollTop = 0")
                await asyncio.sleep(0.5)
                
                # Search with scroll
                for iteration in range(max_scrolls):
                    rows = await grid.query_selector_all('div[role="row"]')
                    
                    # Scan all visible rows
                    for row in rows:
                        try:
                            name_el = await row.query_selector('div._ak8q span[dir="auto"][title]')
                            if not name_el:
                                continue
                            
                            display_name = await name_el.get_attribute('title')
                            if not display_name:
                                display_name = await name_el.inner_text()
                            
                            display_name_normalized = display_name.lower().strip()
                            
                            # Check match
                            if target_name_normalized in display_name_normalized:
                                print(f"[FORWARD] ✅ Found via scroll: '{display_name}'")
                                
                                # Click and validate
                                if await _click_row_and_wait_chat_open(page, row, display_name):
                                    return True
                                else:
                                    # Click failed, continue searching
                                    continue
                        
                        except Exception as e:
                            continue
                    
                    # Scroll down for more
                    await scroll_container.evaluate("el => el.scrollBy(0, 1000)")
                    await asyncio.sleep(0.4)
                
                print(f"[FORWARD] ⚠️ Not found via scroll after {max_scrolls} iterations")
        
        except Exception as e:
            print(f"[FORWARD] ⚠️ Scroll method failed: {e}")
    
    # ========================================================================
    # STEP B: Fallback to SEARCH field (works for contacts/groups not in tab)
    # ========================================================================
    print("[FORWARD] Step B: Trying search field...")
    
    try:
        # Get search input from SIDEBAR (not composer)
        search_input = await get_conversations_search_input(page)
        
        if not search_input:
            print("[FORWARD] ❌ Search input not found")
            return False
        
        # Clear any existing search
        await search_input.click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)
        
        # Type target name
        await page.keyboard.type(target_name, delay=50)
        await asyncio.sleep(0.8)  # Wait for search results
        
        # Get results grid
        try:
            grid = await page.wait_for_selector(
                'div[aria-label="Lista de conversas"][role="grid"]',
                timeout=3000
            )
        except PlaywrightTimeoutError:
            print("[FORWARD] ⚠️ Grid not found after search")
            await clear_search_input_if_present(page)
            return False
        
        rows = await grid.query_selector_all('div[role="row"]')
        print(f"[FORWARD] Found {len(rows)} search results")
        
        # Scan search results
        for row in rows:
            try:
                name_el = await row.query_selector('div._ak8q span[dir="auto"][title]')
                if not name_el:
                    continue
                
                display_name = await name_el.get_attribute('title')
                if not display_name:
                    display_name = await name_el.inner_text()
                
                display_name_normalized = display_name.lower().strip()
                
                if target_name_normalized in display_name_normalized:
                    print(f"[FORWARD] ✅ Found via search: '{display_name}'")
                    
                    # Click and validate
                    success = await _click_row_and_wait_chat_open(page, row, display_name)
                    
                    # Clear search to restore normal list
                    await clear_search_input_if_present(page)
                    
                    if success:
                        return True
                    else:
                        # Click failed but still return False after clearing
                        return False
            
            except Exception as e:
                continue
        
        print(f"[FORWARD] ⚠️ Search did not find '{target_name}'")
        
        # Clear search and restore state
        await clear_search_input_if_present(page)
        
    except Exception as e:
        print(f"[FORWARD] ❌ Search method failed: {e}")
        # Try to clear search anyway
        await clear_search_input_if_present(page)
    
    # Both methods failed
    print(f"[FORWARD] ❌ Could not find '{target_name}' via scroll or search")
    return False


async def get_last_message_text_in_open_chat(page, max_messages_to_check: int = 20):
    """
    Get the text of the last TEXT message in the currently open chat.
    
    - Traverses backwards (last → previous)
    - Ignores messages with no text (images, stickers, audio only)
    - Applies deduplication to fix link card subtitle bug
    - Uses selectors compatible with current WhatsApp Web DOM:
      * Containers: div.message-in / div.message-out / div.focusable-list-item.message-*
      * Content: div.copyable-text + spans/divs with actual text
    
    Args:
        page: Playwright page object
        max_messages_to_check: Maximum number of messages to check (from last to first)
    
    Returns:
        str | None: Text of last text message with deduplication, or None if not found
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
            # while preserving spacing and line breaks
            
            try:
                # Use JavaScript to extract text + emojis in order
                # Improved to handle link cards better (domain, title separate lines)
                text = await content.evaluate("""
                    (element) => {
                        function extractTextAndEmojis(node, isRoot = false) {
                            let result = [];
                            
                            for (let i = 0; i < node.childNodes.length; i++) {
                                let child = node.childNodes[i];
                                
                                if (child.nodeType === Node.TEXT_NODE) {
                                    // It's a text node - add the text AS IS (no trim!)
                                    let text = child.textContent;
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
                                        // Check if this element should force a line break
                                        // (block-level elements like DIV, P, SPAN with display:block, etc.)
                                        const style = window.getComputedStyle(child);
                                        const display = style.display;
                                        const isBlockLevel = (
                                            child.tagName === 'DIV' || 
                                            child.tagName === 'P' ||
                                            display === 'block' ||
                                            display === 'flex' ||
                                            display === 'grid'
                                        );
                                        
                                        // Add newline before block element (if not the first item)
                                        if (isBlockLevel && result.length > 0 && !isRoot) {
                                            // Only add newline if the last item isn't already a newline
                                            if (result[result.length - 1] !== '\\n') {
                                                result.push('\\n');
                                            }
                                        }
                                        
                                        // Recursively process children
                                        result = result.concat(extractTextAndEmojis(child, false));
                                        
                                        // Add newline after block element
                                        if (isBlockLevel && !isRoot) {
                                            // Only add if last item isn't already a newline
                                            if (result.length > 0 && result[result.length - 1] !== '\\n') {
                                                result.push('\\n');
                                            }
                                        }
                                    }
                                }
                            }
                            
                            return result;
                        }
                        
                        let parts = extractTextAndEmojis(element, true);
                        let fullText = parts.join('');
                        
                        // Only trim the FINAL result, not individual pieces
                        return fullText.trim();
                    }
                """)
                
            except Exception as e:
                print(f"{log_prefix} Error extracting text with JS: {e}")
                # Fallback to simple inner_text
                text = await content.inner_text()
                text = text.strip()
            
            if text:
                # Apply deduplication to fix link card subtitle duplication bug
                text_raw = text
                text = dedupe_lines_preserving_order(text)
                text_after_dedupe = text
                
                # Apply link message normalization (fixes domain+title concatenation)
                text = normalize_link_message(text)
                
                # Log raw vs deduped vs normalized for comparison
                preview_raw = text_raw.replace("\n", " ")[:100]
                preview_deduped = text_after_dedupe.replace("\n", " ")[:100]
                preview_normalized = text.replace("\n", " ")[:100]
                
                # Log only if there were changes
                if text_after_dedupe != text_raw:
                    lines_removed = text_raw.count('\n') - text_after_dedupe.count('\n')
                    print(f"{log_prefix} [RAW] {preview_raw!r}")
                    print(f"{log_prefix} [DEDUPED] {preview_deduped!r} (removed {lines_removed} duplicate lines)")
                
                if text != text_after_dedupe:
                    print(f"{log_prefix} [NORMALIZE] Before: {preview_deduped!r}")
                    print(f"{log_prefix} [NORMALIZE] After: {preview_normalized!r}")
                
                if text == text_raw and text == text_after_dedupe:
                    # No changes from either dedupe or normalize
                    print(f"{log_prefix} ✅ Last TEXT message found at index {idx}: {preview_normalized!r}")
                
                return text
            
            # If we got here, message is probably media-only (image, sticker, etc.)
            print(f"{log_prefix} Message #{idx} has no text (media only?), skipping")
        
        print(f"{log_prefix} ❌ No TEXT messages found in last {max_messages_to_check} messages")
        return None
    
    except Exception as e:
        print(f"{log_prefix} ❌ Error reading last message: {e}")
        return None


async def collect_last_n_messages(
    page, 
    count: int = 5, 
    max_scrolls: int = 10
) -> list[ScrapedMessage]:
    """
    Collect the last N messages from currently open chat.
    Scrolls up if needed to collect enough messages.
    
    Args:
        page: Playwright page object
        count: Number of messages to collect
        max_scrolls: Maximum scroll-up iterations
        
    Returns:
        List of ScrapedMessage objects, ordered oldest to newest
    """
    log_prefix = "[COLLECT]"
    print(f"{log_prefix} Collecting last {count} messages...")
    
    # Message container selectors (same as get_last_message_text_in_open_chat)
    msg_container_selector = (
        "div.focusable-list-item.message-in, "
        "div.focusable-list-item.message-out, "
        "div.message-in, "
        "div.message-out"
    )
    
    collected_messages = []
    scroll_iterations = 0
    
    while len(collected_messages) < count and scroll_iterations < max_scrolls:
        # Get current messages
        messages = page.locator(msg_container_selector)
        total_count = await messages.count()
        
        if total_count == 0:
            print(f"{log_prefix} No messages found in chat")
            break
        
        # How many do we need?
        needed = count - len(collected_messages)
        
        # Determine range to scan (from end backwards)
        start_idx = max(0, total_count - needed - len(collected_messages))
        
        # Collect from this batch
        for idx in range(total_count - 1, start_idx - 1, -1):
            if len(collected_messages) >= count:
                break
            
            # Check if we already have this message index
            if any(m.index == idx for m in collected_messages):
                continue
            
            msg = messages.nth(idx)
            content = msg.locator("div.copyable-text")
            
            if await content.count() == 0:
                continue  # Skip system/media messages
            
            # Extract text using same logic as get_last_message_text_in_open_chat
            try:
                text = await content.evaluate("""
                    (element) => {
                        function extractTextAndEmojis(node, isRoot = false) {
                            let result = [];
                            
                            for (let i = 0; i < node.childNodes.length; i++) {
                                let child = node.childNodes[i];
                                
                                if (child.nodeType === Node.TEXT_NODE) {
                                    let text = child.textContent;
                                    if (text) {
                                        result.push(text);
                                    }
                                } else if (child.nodeType === Node.ELEMENT_NODE) {
                                    if (child.tagName === 'IMG' && child.classList.contains('emoji')) {
                                        let emoji = child.getAttribute('alt');
                                        if (emoji) {
                                            result.push(emoji);
                                        }
                                    } else if (child.tagName === 'BR') {
                                        result.push('\\n');
                                    } else if (child.tagName === 'DIV' || child.tagName === 'P') {
                                        if (result.length > 0 && !isRoot) {
                                            result.push('\\n');
                                        }
                                        result = result.concat(extractTextAndEmojis(child, false));
                                    } else {
                                        result = result.concat(extractTextAndEmojis(child, false));
                                    }
                                }
                            }
                            
                            return result;
                        }
                        
                        let parts = extractTextAndEmojis(element, true);
                        let fullText = parts.join('');
                        return fullText.trim();
                    }
                """)
                
                if text:
                    # Apply deduplication
                    text = dedupe_lines_preserving_order(text)
                    # Apply link normalization (fixes domain+title concatenation)
                    text = normalize_link_message(text)
                    collected_messages.append(ScrapedMessage(text=text, index=idx))
                    print(f"{log_prefix} Collected message {len(collected_messages)}/{count} (idx={idx})")
            
            except Exception as e:
                print(f"{log_prefix} Error extracting message at idx {idx}: {e}")
                continue
        
        # If we have enough, stop
        if len(collected_messages) >= count:
            break
        
        # Otherwise, scroll up to get more
        print(f"{log_prefix} Need more messages, scrolling up... (iteration {scroll_iterations + 1}/{max_scrolls})")
        await page.evaluate("document.querySelector('[data-testid=\"conversation-panel-body\"]').scrollBy(0, -500)")
        await asyncio.sleep(0.5)
        scroll_iterations += 1
    
    # Sort by index (oldest first)
    collected_messages.sort(key=lambda m: m.index)
    
    print(f"{log_prefix} ✅ Collected {len(collected_messages)} messages (requested {count}, scrolls: {scroll_iterations})")
    
    return collected_messages


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
    
    # Wait for link preview to load (simplified, deterministic approach)
    # No DOM detection - just wait a fixed amount of time for WhatsApp to render the card
    import re
    has_url = bool(re.search(r'https?://\S+', text))
    
    if has_url:
        # Fixed 8-second wait for link preview to render
        # This is more reliable than trying to detect preview in DOM
        print("[FORWARD] ⏳ Message contains URL, waiting 8s for link preview to render...")
        await page.wait_for_timeout(8000)
        print("[FORWARD] ✅ Preview wait complete")
    else:
        # Quick delay for non-link messages
        await page.wait_for_timeout(300)
    
    # Now send
    print("[FORWARD] ⏎ Pressing Enter to send...")
    await page.keyboard.press("Enter")
    
    # Wait a bit to ensure message was sent
    await asyncio.sleep(1)
    
    print("[FORWARD] ✅ Message sent!")


async def send_multiple_messages_to_open_chat(
    page,
    messages: list[ScrapedMessage],
    delay_between: float = 2.0
) -> None:
    """
    Send multiple messages to currently open chat with delays.
    
    Args:
        page: Playwright page object
        messages: List of ScrapedMessage objects
        delay_between: Seconds to wait between messages
    """
    log_prefix = "[SEND]"
    total = len(messages)
    
    for i, message in enumerate(messages, 1):
        print(f"{log_prefix} Sending message {i}/{total}...")
        
        try:
            await send_message_to_open_chat(page, message.text)
            
            if i < total:  # Don't wait after last message
                print(f"{log_prefix} Waiting {delay_between}s before next message...")
                await asyncio.sleep(delay_between)
        
        except Exception as e:
            print(f"{log_prefix} ❌ Failed to send message {i}/{total}: {e}")
            # Continue with next message
    
    print(f"{log_prefix} ✅ Sent {total} messages")


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
    
    # Ensure chat is scrolled to bottom (most recent messages)
    print()
    print("[FORWARD] Ensuring chat is at bottom...")
    await ensure_chat_scrolled_to_bottom(page)
    
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


async def copy_multiple_messages_between_groups(
    page,
    source_name: str,
    target_name: str,
    count: int = 5,
    max_scrolls: int = 10
) -> None:
    """
    Copy the last N messages from source group to target group.
    
    Args:
        page: Playwright page object
        source_name: Name (or part) of source group
        target_name: Name (or part) of target group
        count: Number of messages to forward
        max_scrolls: Max scroll iterations when collecting
    """
    print()
    print("=" * 70)
    print(f"COPYING {count} MESSAGES: '{source_name}' → '{target_name}'")
    print("=" * 70)
    print()
    
    # Step 1: Open source group
    print("[FORWARD] Step 1: Opening source group...")
    success = await find_and_open_group(page, source_name)
    if not success:
        print("[FORWARD] ❌ Failed to open source group. Aborting.")
        return
    
    await asyncio.sleep(1.0)
    
    # Ensure chat is scrolled to bottom (most recent messages)
    print()
    print("[FORWARD] Ensuring chat is at bottom...")
    await ensure_chat_scrolled_to_bottom(page)
    
    # Step 2: Collect messages
    print()
    print(f"[FORWARD] Step 2: Collecting last {count} messages...")
    messages = await collect_last_n_messages(page, count, max_scrolls)
    
    if not messages:
        print("[FORWARD] ❌ No messages collected. Aborting.")
        return
    
    # Log collected messages preview
    print()
    print("-" * 70)
    print(f"COLLECTED {len(messages)} MESSAGES:")
    for i, msg in enumerate(messages, 1):
        preview = msg.text[:80].replace('\n', ' ')
        print(f"  {i}. {preview}...")
    print("-" * 70)
    print()
    
    # Step 3: Return to Groups tab
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
    
    await asyncio.sleep(1.0)
    
    # Step 5: Send all messages
    print()
    print(f"[FORWARD] Step 5: Sending {len(messages)} messages to target group...")
    try:
        await send_multiple_messages_to_open_chat(page, messages, DELAY_BETWEEN_MESSAGES)
        print()
        print("=" * 70)
        print(f"✅ {len(messages)} MESSAGES FORWARDED SUCCESSFULLY!")
        print("=" * 70)
        print()
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ FAILED TO SEND MESSAGES: {e}")
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
    print("WHATSAPP WEB PLAYGROUND - GROUP DISCOVERY & FORWARDING TOOL")
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
            print(f"   cd C:/Users/Ruan/Desktop/autopromo")
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
            print(f"  cd C:/Users/Ruan/Desktop/autopromo")
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
        print("2. Copy LAST N messages from one group to another")
        print("0. Exit (close browser)")
        print()
        
        choice = input("Choose an option (0/1/2): ").strip()
        
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
        
        elif choice == "2":
            print()
            source_name = input("Enter (part of) SOURCE group name: ").strip()
            target_name = input("Enter (part of) TARGET group name: ").strip()
            count_input = input(f"How many messages to forward? (default: {MESSAGES_TO_FORWARD}): ").strip()
            count = int(count_input) if count_input.isdigit() else MESSAGES_TO_FORWARD
            
            if source_name and target_name:
                try:
                    await copy_multiple_messages_between_groups(
                        page, source_name, target_name, count, MAX_SCROLLS_FOR_MESSAGES
                    )
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
