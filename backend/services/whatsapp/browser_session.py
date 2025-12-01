"""
BrowserSession dataclass para gerenciar sessões Playwright.

Cada WhatsAppConnection tem exatamente 1 BrowserSession.
"""
from dataclasses import dataclass
from datetime import datetime
from playwright.async_api import Browser, BrowserContext, Page, Error as PlaywrightError


@dataclass
class BrowserSession:
    """
    Representa uma sessão ativa do WhatsApp Web.
    
    Cada conexão tem exatamente 1 BrowserSession associada.
    
    Attributes:
        browser: Instância do Browser Playwright
        context: BrowserContext com cookies/storage persistido
        page: Page única para essa conexão (WhatsApp Web)
        last_health_check_at: Timestamp do último health check
    """
    browser: Browser
    context: BrowserContext
    page: Page
    last_health_check_at: datetime
    
    async def is_alive(self) -> bool:
        """
        Verifica se a page ainda está válida e respondendo.
        
        Returns:
            True se page está viva, False caso contrário
        """
        try:
            # page.is_closed() é sync (sem await)
            if self.page.is_closed():
                return False
            
            # Operação barata só pra forçar interação com o browser
            # Se page crashou, vai lançar exception
            await self.page.title()
            return True
        except PlaywrightError:
            # Playwright-specific errors (page closed, browser crashed, etc)
            return False
        except Exception:
            # Outras exceptions - considerar morta
            return False
    
    async def close(self):
        """
        Fecha browser e limpa recursos.
        
        Idempotente - não quebra se já estiver fechado.
        """
        try:
            await self.context.close()
            await self.browser.close()
        except Exception:
            # Já pode estar fechado ou em estado inválido
            pass
