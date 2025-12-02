"""
Manual WhatsApp Web Playground (Debug Tool)
==========================================

Propósito:
  - Abrir WhatsApp Web com Playwright
  - Gerar QR code e salvar em /app/logs/manual_whatsapp_qr.png
  - Após login, tirar screenshot da tela conectada
  - Listar no console os chats/grupos visíveis em #pane-side

Modo 1: Rodar DENTRO do Docker (headless) - VPS / ambiente server
-----------------------------------------------------------------
No host (Windows), dentro do diretório do projeto:

  cd C:\\Users\\Ruan\\Desktop\\autopromo
  docker-compose up -d
  docker-compose exec backend python backend/scripts/manual_whatsapp_playground.py

Quando aparecer o log:
  [PLAYGROUND] ✅ QR saved to: /app/logs/manual_whatsapp_qr.png

Copie o arquivo para o Windows:

  docker cp autopromo-backend:/app/logs/manual_whatsapp_qr.png .

Abra o PNG, escaneie o QR com o app do WhatsApp no celular,
volte no terminal e siga as instruções.

Modo 2: Rodar DIRETO no Windows (headful, com janela visível)
-------------------------------------------------------------
Pré-requisitos:
  - Python 3 instalado no Windows
  - Playwright instalado (incluindo browsers):
      cd C:\\Users\\Ruan\\Desktop\\autopromo
      pip install -r backend/requirements.txt
      playwright install chromium

Rodar:

  cd C:\\Users\\Ruan\\Desktop\\autopromo
  python backend/scripts/manual_whatsapp_playground.py --headful

Isso vai abrir uma janela real do Chromium com o WhatsApp Web,
permitindo inspecionar DOM, clicar manualmente, etc.

Observação:
  - NÃO use --headful dentro do container Docker (não há GUI).
"""
import asyncio
import base64
import argparse
import os
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


def parse_args():
    parser = argparse.ArgumentParser(
        description="Manual WhatsApp Web playground (debug only)."
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser with visible window (for local dev on Windows).",
    )
    return parser.parse_args()


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
    print("WHATSAPP WEB PLAYGROUND - MANUAL TESTING")
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
        
        # ALWAYS take loading screenshot - helps debug if QR detection fails
        print("[PLAYGROUND] Taking loading screenshot...")
        loading_png_path = logs_dir / "manual_whatsapp_loading.png"
        await page.screenshot(path=str(loading_png_path), full_page=True)
        print(f"[PLAYGROUND] ✅ Loading screenshot saved to: {loading_png_path}")
        print()
        
        # 1) Check if already logged in (chat list visible)
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
            
            # Wait for QR code to appear
            print("[PLAYGROUND] ⏳ Waiting for QR canvas (max 60s)...")
            print("[PLAYGROUND]    Selector: canvas[aria-label*=\"QR\"]")
            print("[PLAYGROUND]    This may take 10-30 seconds...")
            print()
            
            try:
                qr_canvas = await page.wait_for_selector('canvas[aria-label*="QR"]', timeout=60000)
                print("[PLAYGROUND] ✅ QR canvas found!")
            except PlaywrightTimeoutError:
                print()
                print("=" * 70)
                print("❌ TIMEOUT: Could not find QR canvas in 60 seconds")
                print("=" * 70)
                print()
                print("Possible reasons:")
                print("  1. WhatsApp Web changed the QR canvas selector")
                print("  2. Page loaded too slowly")
                print("  3. Already logged in but #pane-side not detected")
                print()
                
                # Take timeout screenshot for debugging
                error_png_path = logs_dir / "manual_whatsapp_qr_timeout.png"
                await page.screenshot(path=str(error_png_path), full_page=True)
                print(f"[PLAYGROUND] Timeout screenshot saved to: {error_png_path}")
                print()
                print("To debug, copy screenshot to Windows:")
                print(f"  cd C:\\Users\\Ruan\\Desktop\\autopromo")
                print(f"  docker cp autopromo-backend:/app/logs/manual_whatsapp_qr_timeout.png .")
                print()
                print("Then open the PNG and inspect what the page looks like.")
                print("=" * 70)
                
                await browser.close()
                return
            
            # Capture QR as PNG via toDataURL
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
            print("2. Open manual_whatsapp_qr.png in Windows image viewer")
            print()
            print("3. Scan with WhatsApp on your phone:")
            print("   - Open WhatsApp > Settings > Linked Devices > Link a Device")
            print("   - Point camera at the QR code on your screen")
            print()
            print("4. After scanning, come back here and press ENTER")
            print("=" * 70)
            print()
            
            input("⏸️  Press ENTER after scanning QR code...")
            print()
            
            # Wait for connected interface to appear
            print("[PLAYGROUND] ⏳ Waiting for login to complete (max 60s)...")
            try:
                await page.wait_for_selector("#pane-side", timeout=60000)
                print("[PLAYGROUND] ✅ Login detected! Chat list loaded.")
            except PlaywrightTimeoutError:
                print()
                print("=" * 70)
                print("❌ TIMEOUT: Could not detect #pane-side after QR scan")
                print("=" * 70)
                print()
                print("Possible reasons:")
                print("  1. QR code expired (try again)")
                print("  2. WhatsApp Web changed the chat list selector")
                print("  3. Login is still loading")
                print()
                
                post_scan_png_path = logs_dir / "manual_whatsapp_post_scan_timeout.png"
                await page.screenshot(path=str(post_scan_png_path), full_page=True)
                print(f"[PLAYGROUND] Post-scan screenshot saved to: {post_scan_png_path}")
                print()
                print("To debug:")
                print(f"  docker cp autopromo-backend:/app/logs/manual_whatsapp_post_scan_timeout.png .")
                print("=" * 70)
                
                await browser.close()
                return
        
        # 2) At this point, should be connected. Take screenshot
        print()
        print("[PLAYGROUND] 📸 Taking screenshot of connected state...")
        connected_png_path = logs_dir / "manual_whatsapp_connected.png"
        await page.screenshot(path=str(connected_png_path), full_page=True)
        print(f"[PLAYGROUND] ✅ Screenshot saved to: {connected_png_path}")
        print()
        print("To view screenshot on Windows:")
        print(f"  cd C:\\Users\\Ruan\\Desktop\\autopromo")
        print(f"  docker cp autopromo-backend:/app/logs/manual_whatsapp_connected.png .")
        print()
        
        # 3) Simple Group Discovery: list visible chat titles
        print("=" * 70)
        print("STARTING CHAT DISCOVERY")
        print("=" * 70)
        print("[PLAYGROUND] Looking for chats in #pane-side...")
        print()
        
        sidebar = await page.query_selector("#pane-side")
        if not sidebar:
            print("[PLAYGROUND] ❌ Could not find #pane-side. Exiting.")
            await browser.close()
            return
        
        rows = await sidebar.query_selector_all('div[role="row"]')
        if not rows:
            print("[PLAYGROUND] ⚠️ No rows found in #pane-side.")
            print("[PLAYGROUND] This might mean:")
            print("  - No chats/groups visible")
            print("  - WhatsApp Web changed the DOM structure")
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
                
                print(f"  [DISCOVERY] Chat #{idx:2d}: {name}")
                discovered_count += 1
            
            print()
            print(f"[PLAYGROUND] ✅ Discovered {discovered_count} chats/groups")
        
        print("=" * 70)
        print()
        
        if headless:
            print("[PLAYGROUND] ⏳ Keeping browser open for 60s to ensure everything ran...")
            await asyncio.sleep(60)
        else:
            print("[PLAYGROUND] HEADFUL MODE: Browser window is open.")
            print("[PLAYGROUND] Press F12 to inspect DOM")
            print("[PLAYGROUND] Press CTRL+C to close when done")
            print()
            
            try:
                # Keep browser open indefinitely in headful mode
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print()
                print("[PLAYGROUND] CTRL+C detected. Closing browser...")
        
        print("[PLAYGROUND] Closing browser...")
        await browser.close()
        print()
        print("=" * 70)
        print("PLAYGROUND SESSION COMPLETE")
        print("=" * 70)
        print()


if __name__ == "__main__":
    asyncio.run(main())
