"""
Teste rápido do Playwright - valida instalação
"""
import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    print("Testando Playwright...")
    
    async with async_playwright() as p:
        print("[OK] Playwright iniciado")
        
        # Testar persistent context (nossa abordagem)
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./test_session",
            headless=True
        )
        print("[OK] Persistent context criado")
        
        # Abrir página
        page = context.pages[0] if context.pages else await context.new_page()
        print("[OK] Pagina criada")
        
        # Navegar para Google (teste simples)
        await page.goto("https://www.google.com")
        title = await page.title()
        print(f"[OK] Navegacao OK: {title}")
        
        # Fechar
        await context.close()
        print("[OK] Context fechado")
        
    print("\n SUCCESS! Playwright esta funcionando perfeitamente!")

if __name__ == "__main__":
    asyncio.run(test_playwright())
