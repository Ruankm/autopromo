"""
Status checker - Determina status da conexão analisando DOM do WhatsApp Web.

100% baseado em seletores DOM - como um humano olhando a tela.
"""
from playwright.async_api import Page
import logging

logger = logging.getLogger(__name__)


async def check_connection_status(page: Page) -> str:
    """
    Determina status da conexão analisando DOM.
    
    Lógica:
    - qr_needed: QR Code visível (canvas ou texto de instruções)
    - connecting: Textos de "Conectando..." ou loading
    - connected: Interface principal carregada (search box, chat list)
    - error: Nenhum estado reconhecido
    
    Args:
        page: Playwright Page object
        
    Returns:
        Status: "qr_needed" | "connecting" | "connected" | "error"
    """
    try:
        # 1. DESCONECTADO (QR necessário)
        qr_canvas = await page.query_selector('canvas[aria-label*="QR"]')
        if qr_canvas:
            logger.debug("Detected: QR canvas visible")
            return "qr_needed"
        
        qr_text = await page.query_selector('text=/Passos para iniciar/')
        if qr_text:
            logger.debug("Detected: QR instructions text")
            return "qr_needed"
        
        # Outro seletor comum para QR
        qr_container = await page.query_selector('div._3aOk7')
        if qr_container:
            logger.debug("Detected: QR container")
            return "qr_needed"
        
        # 2. CONECTANDO
        connecting_text = await page.query_selector('text=/Usando o WhatsApp/')
        if connecting_text:
            logger.debug("Detected: Connecting state")
            return "connecting"
        
        landing_title = await page.query_selector('.landing-title')
        if landing_title:
            logger.debug("Detected: Landing/loading state")
            return "connecting"
        
        # 3. CONECTADO (interface principal)
        # Prioridade: search box (mais confiável)
        search_box = await page.query_selector('[data-testid="chat-list-search"]')
        if search_box:
            logger.debug("Detected: Chat search box (connected)")
            return "connected"
        
        # Alternativa: conversation panel
        chat_panel = await page.query_selector('[data-testid="conversation-panel"]')
        if chat_panel:
            logger.debug("Detected: Conversation panel (connected)")
            return "connected"
        
        # Alternativa: sidebar de chats
        pane_side = await page.query_selector('#pane-side')
        if pane_side:
            logger.debug("Detected: Chat list pane (connected)")
            return "connected"
        
        # 4. ERRO (nenhum estado reconhecido)
        logger.warning("Could not determine status from DOM")
        return "error"
        
    except Exception as e:
        logger.exception(f"Error checking status: {e}")
        return "error"
