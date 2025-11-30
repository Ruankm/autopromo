"""
Humanized Sender - Envia mensagens simulando comportamento humano.

Características:
- Typing char-by-char com delays aleatórios
- Aguarda preview carregar (2-4s)  
- Random delays entre ações
- Fallback de seletores
"""
import asyncio
import random
import logging
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class HumanizedSender:
    """
    Envia mensagens WhatsApp simulando comportamento humano.
    
    Isso minimiza risco de detecção/ban:
    - Digita caractere por caractere (velocidade variável)
    - Aguarda preview carregar antes de enviar
    - Usa delays aleatórios
    """
    
    def __init__(self):
        self.min_char_delay = 0.03  # 30ms mínimo entre caracteres
        self.max_char_delay = 0.12  # 120ms máximo
        self.preview_wait_min = 2.5  # 2.5s mínimo para preview
        self.preview_wait_max = 4.0  # 4s máximo
    
    async def send_with_preview(
        self,
        page: Page,
        group_name: str,
        text: str
    ) -> dict:
        """
        Envia mensagem aguardando preview carregar.
        
        Args:
            page: Página do Playwright
            group_name: Nome do grupo
            text: Texto da mensagem
            
        Returns:
            {
                "status": "sent" | "error",
                "preview_generated": bool,
                "duration_ms": int,
                "error": str (opcional)
            }
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Abrir grupo
            await self._open_group(page, group_name)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 2. Clicar no input
            input_elem = await self._get_input_element(page)
            await input_elem.click()
            await asyncio.sleep(random.uniform(0.2, 0.4))
            
            # 3. Digitar NATURALMENTE (char por char)
            for char in text:
                await page.keyboard.type(char)
                # Delay humano entre teclas
                delay = random.uniform(self.min_char_delay, self.max_char_delay)
                await asyncio.sleep(delay)
            
            # 4. AGUARDAR PREVIEW GERAR (CRÍTICO!)
            preview_wait = random.uniform(self.preview_wait_min, self.preview_wait_max)
            logger.debug(f"Waiting {preview_wait:.2f}s for preview...")
            await asyncio.sleep(preview_wait)
            
            # 5. Enviar (Enter)
            await page.keyboard.press('Enter')
            await asyncio.sleep(0.5)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"[OK] Message sent to {group_name} (preview: yes, {duration_ms}ms)")
            
            return {
                "status": "sent",
                "preview_generated": True,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[ERROR] Failed to send to {group_name}: {e}")
            
            return {
                "status": "error",
                "preview_generated": False,
                "duration_ms": duration_ms,
                "error": str(e)
            }
    
    async def _open_group(self, page: Page, group_name: str):
        """
        Abre grupo via busca por nome.
        
        Args:
            page: Página do Playwright
            group_name: Nome do grupo
        """
        # Seletores da barra de busca (com fallback)
        search_selectors = [
            'div[data-testid="chat-list-search"]',
            'div[contenteditable="true"][data-tab="3"]',
            'div[title="Search input textbox"]'
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                search_box = await page.wait_for_selector(selector, timeout=3000)
                if search_box:
                    break
            except:
                continue
        
        if not search_box:
            raise Exception("Search box not found - DOM may have changed")
        
        # Limpar e digitar nome do grupo
        await search_box.click()
        await asyncio.sleep(0.2)
        
        # Selecionar tudo e apagar
        await page.keyboard.press('Control+A')
        await page.keyboard.press('Backspace')
        await asyncio.sleep(0.1)
        
        # Digitar nome do grupo
        await search_box.type(group_name, delay=random.uniform(50, 100))
        
        # Aguardar resultados aparecerem
        await asyncio.sleep(1.5)
        
        # Clicar no primeiro resultado (seletores com fallback)
        result_selectors = [
            f'span[title="{group_name}"]',
            'div[data-testid="cell-frame-container"]:first-child',
            'div[role="listitem"]:first-child'
        ]
        
        result_clicked = False
        for selector in result_selectors:
            try:
                result = await page.wait_for_selector(selector, timeout=2000)
                if result:
                    await result.click()
                    result_clicked = True
                    logger.debug(f"Opened group via selector: {selector}")
                    break
            except:
                continue
        
        if not result_clicked:
            raise Exception(f"Group '{group_name}' not found in search results")
        
        # Aguardar grupo abrir
        await asyncio.sleep(random.uniform(0.5, 1.0))
    
    async def _get_input_element(self, page: Page):
        """
        Obtém elemento do input com fallback de seletores.
        
        Returns:
            Element handle do input
        """
        # Seletores do input de mensagem (com fallback)
        input_selectors = [
           'div[data-testid="conversation-compose-box-input"]',
            'div[contenteditable="true"][data-tab="10"]',
            'div.copyable-text[contenteditable="true"]',
            'div[role="textbox"]'
        ]
        
        for selector in input_selectors:
            try:
                elem = await page.wait_for_selector(selector, timeout=3000)
                if elem:
                    logger.debug(f"Input found via selector: {selector}")
                    return elem
            except:
                continue
        
        raise Exception("Input element not found - DOM may have changed")
