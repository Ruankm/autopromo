"""
Manual WhatsApp Web Playground - ISOLATED DEBUG TOOL

This is a standalone debug script to test WhatsApp Web with Playwright.
NO database, NO models, NO worker interference.

Purpose:
- Open WhatsApp Web
- Generate QR code
- Scan QR with phone
- Authenticate
- List visible chats/groups

Usage:
    docker-compose exec backend python scripts/manual_whatsapp_playground.py

Output:
    - /app/logs/manual_whatsapp_qr.png (QR code image)
    - /app/logs/manual_whatsapp_connected.png (screenshot after login)
    - Console output with discovered chats
"""
import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def main():
    # Guarantee logs directory exists
    logs_dir = Path("/app/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"[PLAYGROUND] Logs directory: {logs_dir}")
    
    async with async_playwright() as p:
        print("[PLAYGROUND] Launching Chromium browser...")
        browser = await p.chromium.launch(headless=True)
        
        print("[PLAYGROUND] Creating browser context...")
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        
        print("[PLAYGROUND] Opening https://web.whatsapp.com ...")
        await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        # 1) Check if already logged in (chat list visible)
        already_connected = False
        try:
            print("[PLAYGROUND] Checking if already logged in (#pane-side)...")
            await page.wait_for_selector("#pane-side", timeout=10000)
            already_connected = True
            print("[PLAYGROUND] ✓ Already logged in (pane-side found).")
        except PlaywrightTimeoutError:
            print("[PLAYGROUND] Not logged in yet.")
        
        if not already_connected:
            print("[PLAYGROUND] Not logged in. Capturing QR code...")
            
            # Wait for QR code to appear
            try:
                print("[PLAYGROUND] Waiting for QR canvas (max 60s)...")
                qr_canvas = await page.wait_for_selector('canvas[aria-label*="QR"]', timeout=60000)
                print("[PLAYGROUND] ✓ QR canvas found!")
            except PlaywrightTimeoutError:
                print("[PLAYGROUND] ❌ Could not find QR canvas in 60s.")
                await browser.close()
                return
            
            # Capture QR as PNG via toDataURL
            print("[PLAYGROUND] Extracting QR code image...")
            data_url = await qr_canvas.evaluate("(canvas) => canvas.toDataURL('image/png')")
            base64_data = data_url.split(",")[1]
            
            qr_png_path = logs_dir / "manual_whatsapp_qr.png"
            with open(qr_png_path, "wb") as f:
                f.write(base64.b64decode(base64_data))
            
            print(f"[PLAYGROUND] ✓ QR saved to: {qr_png_path}")
            print()
            print("=" * 70)
            print("TO SCAN QR CODE:")
            print("=" * 70)
            print("1. On Windows host, run:")
            print(f"   docker cp autopromo-backend:/app/logs/manual_whatsapp_qr.png .")
            print()
            print("2. Open manual_whatsapp_qr.png in Windows")
            print()
            print("3. Scan with WhatsApp on your phone:")
            print("   - Open WhatsApp > Settings > Linked Devices > Link a Device")
            print("   - Point camera at the QR code")
            print()
            print("4. After scanning, come back here and press ENTER")
            print("=" * 70)
            print()
            
            input("Press ENTER after scanning QR...")
            
            # Wait for connected interface to appear
            try:
                print("[PLAYGROUND] Waiting for login (max 60s)...")
                await page.wait_for_selector("#pane-side", timeout=60000)
                print("[PLAYGROUND] ✓ Login detected! Chat list loaded.")
            except PlaywrightTimeoutError:
                print("[PLAYGROUND] ❌ Could not detect #pane-side after QR scan.")
                await browser.close()
                return
        
        # 2) At this point, should be connected. Take screenshot
        print("[PLAYGROUND] Taking screenshot of connected state...")
        connected_png_path = logs_dir / "manual_whatsapp_connected.png"
        await page.screenshot(path=str(connected_png_path), full_page=True)
        print(f"[PLAYGROUND] ✓ Screenshot saved to: {connected_png_path}")
        print()
        print("To view screenshot on Windows:")
        print(f"  docker cp autopromo-backend:/app/logs/manual_whatsapp_connected.png .")
        print()
        
        # 3) Simple Group Discovery: list visible chat titles
        print("[PLAYGROUND] Starting chat discovery (#pane-side)...")
        print("=" * 70)
        
        sidebar = await page.query_selector("#pane-side")
        if not sidebar:
            print("[PLAYGROUND] ❌ Could not find #pane-side. Exiting.")
            await browser.close()
            return
        
        rows = await sidebar.query_selector_all('div[role="row"]')
        if not rows:
            print("[PLAYGROUND] ⚠️ No rows found in #pane-side.")
        else:
            print(f"[PLAYGROUND] Found {len(rows)} rows. Extracting chat titles...")
            print()
            
            discovered_count = 0
            for idx, row in enumerate(rows, 1):
                title_el = await row.query_selector('span[title]')
                if not title_el:
                    continue
                name = await title_el.get_attribute("title")
                if not name:
                    continue
                
                print(f"[DISCOVERY] Chat #{idx}: {name}")
                discovered_count += 1
            
            print()
            print(f"[PLAYGROUND] ✓ Discovered {discovered_count} chats/groups")
        
        print("=" * 70)
        print("[PLAYGROUND] Keeping browser open for 60s to ensure everything ran...")
        await asyncio.sleep(60)
        
        print("[PLAYGROUND] Closing browser...")
        await browser.close()
        print("[PLAYGROUND] Done!")


if __name__ == "__main__":
    asyncio.run(main())
