"""
Connection Pool - Gerencia persistent contexts do Playwright.

Um browser context por conexão, com recovery automático.
"""
import logging
from typing import Dict, Optional
from playwright.async_api import async_playwright, BrowserContext, Playwright

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Gerencia conexões WhatsApp via Playwright persistent contexts.
    
    Características:
    - 1 persistent context por connection_id
    - Sessão salva em whatsapp_sessions/{connection_id}/
    - Recovery automático (detecta context morto e recria)
    - Headless por padrão
    """
    
    def __init__(self, sessions_dir: str = "./whatsapp_sessions"):
        self.sessions_dir = sessions_dir
        self.playwright: Optional[Playwright] = None
        self.contexts: Dict[str, BrowserContext] = {}
        logger.info("ConnectionPool initialized")
    
    async def start(self):
        """Inicia o Playwright."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            logger.info("Playwright started")
    
    async def get_or_create(
        self,
        connection_id: str,
        headless: bool = True
    ) -> BrowserContext:
        """
        Obtém ou cria persistent context para connection.
        
        Inclui recovery: se context estiver morto, recria automaticamente.
        
        Args:
            connection_id: UUID da WhatsAppConnection
            headless: Rodar em modo headless?
            
        Returns:
            BrowserContext ativo e pronto
        """
        # Verificar se já existe
        if connection_id in self.contexts:
            context = self.contexts[connection_id]
            
            # RECOVERY: Verificar se context ainda está vivo
            try:
                # Tentar acessar pages (se falhar, context morreu)
                pages = context.pages
                if pages and len(pages) > 0:
                    page = pages[0]
                    if not page.is_closed():
                        logger.debug(f"Context {connection_id} already exists and is alive")
                        return context
                
                logger.warning(f"Context {connection_id} is dead, recreating...")
            except Exception as e:
                logger.error(f"Context {connection_id} check failed: {e}")
            
            # Context morreu, remover e recriar
            try:
                await context.close()
            except:
                pass
            del self.contexts[connection_id]
        
        # Criar novo persistent context
        user_data_dir = f"{self.sessions_dir}/{connection_id}"
        
        logger.info(f"Creating persistent context for {connection_id}")
        
        context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            viewport={'width': 1280, 'height': 720},
            locale='pt-BR',
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ],
            # User agent realista
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Garantir que tem pelo menos uma página
        if len(context.pages) == 0:
            await context.new_page()
        
        page = context.pages[0]
        
        # Navegar para WhatsApp Web
        logger.info(f"Opening WhatsApp Web for {connection_id}")
        try:
            await page.goto('https://web.whatsapp.com', timeout=60000, wait_until='domcontentloaded')
        except Exception as e:
            logger.error(f"Failed to open WhatsApp Web: {e}")
            # Não fazer raise, deixar para próxima tentativa
        
        # Salvar no pool
        self.contexts[connection_id] = context
        logger.info(f"[OK] Context created and saved: {connection_id}")
        
        return context
    
    async def close(self, connection_id: str):
        """Fecha context específico."""
        if connection_id in self.contexts:
            try:
                await self.contexts[connection_id].close()
                logger.info(f"Context closed: {connection_id}")
            except Exception as e:
                logger.error(f"Error closing context {connection_id}: {e}")
            finally:
                del self.contexts[connection_id]
    
    async def close_all(self):
        """Fecha todos os contexts e o Playwright."""
        logger.info("Closing all contexts...")
        
        for connection_id in list(self.contexts.keys()):
            await self.close(connection_id)
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            logger.info("Playwright stopped")
    
    def get_active_count(self) -> int:
        """Retorna número de contexts ativos."""
        return len(self.contexts)
    
    async def health_check(self, connection_id: str) -> bool:
        """
        Verifica se context está saudável.
        
        Returns:
            True se context está ativo e responsivo
        """
        if connection_id not in self.contexts:
            return False
        
        try:
            context = self.contexts[connection_id]
            pages = context.pages
            if not pages or len(pages) == 0:
                return False
            
            page = pages[0]
            if page.is_closed():
                return False
            
            # Tentar avaliar JS simples
            await page.evaluate("1 + 1")
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed for {connection_id}: {e}")
            return False
