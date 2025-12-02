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
        
        if headless:
            print("[PLAYGROUND] ⏳ Keeping browser open for 30s...")
            await asyncio.sleep(30)
        else:
            print("[PLAYGROUND] HEADFUL MODE: Browser window is open.")
            print("[PLAYGROUND] Press F12 to inspect DOM")
            print("[PLAYGROUND] Press CTRL+C to close")
            print()
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print()
                print("[PLAYGROUND] CTRL+C detected. Closing...")
        
        print("[PLAYGROUND] Closing browser...")
        await browser.close()
        print()
        print("=" * 70)
        print("PLAYGROUND SESSION COMPLETE")
        print("=" * 70)
        print()


if __name__ == "__main__":
    asyncio.run(main())
