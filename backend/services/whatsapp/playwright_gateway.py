"""
Playwright Gateway - Implementação do WhatsAppGateway usando Playwright.

Une todos os componentes:
- ConnectionPool (gerencia contexts)
- MessageMonitor (detecta novas mensagens)
- HumanizedSender (envia com preview)
- QueueManager (rate limit)
"""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from services.whatsapp.gateway import (
    WhatsAppGateway,
    WhatsAppMessage,
    ConnectionStatus
)
from services.whatsapp.connection_pool import ConnectionPool
from services.whatsapp.message_monitor import MessageMonitor
from services.whatsapp.humanized_sender import HumanizedSender

logger = logging.getLogger(__name__)


class PlaywrightWhatsAppGateway:
    """
    Implementação do WhatsAppGateway usando Playwright.
    
    Responsabilidades:
    - Gerenciar connections (pool)
    - Monitorar mensagens (monitor)
    - Enviar mensagens (sender)
    - Obter status/QR Code
    """
    
    def __init__(
        self,
        db: AsyncSession,
        sessions_dir: str = "./whatsapp_sessions"
    ):
        self.db = db
        self.pool = ConnectionPool(sessions_dir=sessions_dir)
        self.monitor = MessageMonitor(db=db)
        self.sender = HumanizedSender()
        
        logger.info("PlaywrightWhatsAppGateway initialized")
    
    async def start(self):
        """Inicia o Playwright."""
        await self.pool.start()
    
    async def send_message(
        self,
        connection_id: str,
        group_name: str,
        text: str,
        wait_for_preview: bool = True
    ) -> dict:
        """
        Envia mensagem para grupo.
        
        Implementa WhatsAppGateway.send_message()
        """
        try:
            # Obter context
            context = await self.pool.get_or_create(connection_id)
            page = context.pages[0]
            
            # Enviar com preview
            result = await self.sender.send_with_preview(
                page=page,
                group_name=group_name,
                text=text
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {
                "status": "error",
                "preview_generated": False,
                "error": str(e)
            }
    
    async def get_new_messages(
        self,
        connection_id: str,
        source_groups: List[str]
    ) -> List[WhatsAppMessage]:
        """
        Obtém novas mensagens dos grupos fonte.
        
        Implementa WhatsAppGateway.get_new_messages()
        """
        new_messages = []
        
        try:
            # Obter context
            context = await self.pool.get_or_create(connection_id)
            page = context.pages[0]
            
            # Verificar cada grupo fonte
            for group_name in source_groups:
                try:
                    msg = await self.monitor.check_group(
                        connection_id=connection_id,
                        page=page,
                        group_name=group_name
                    )
                    
                    if msg:
                        new_messages.append(msg)
                        
                except Exception as e:
                    logger.error(f"Error checking {group_name}: {e}")
                    continue
            
            return new_messages
            
        except Exception as e:
            logger.error(f"Get new messages error: {e}")
            return []
    
    async def get_connection_status(
        self,
        connection_id: str
    ) -> ConnectionStatus:
        """
        Verifica status da conexão.
        
        Implementa WhatsAppGateway.get_connection_status()
        """
        try:
            # Verificar se context existe e está saudável
            is_healthy = await self.pool.health_check(connection_id)
            
            if not is_healthy:
                return ConnectionStatus(
                    status="disconnected",
                    is_authenticated=False,
                    error="Context not healthy"
                )
            
            # Obter context e verificar WhatsApp
            context = await self.pool.get_or_create(connection_id)
            page = context.pages[0]
            
            # Verificar se está na tela de QR Code
            try:
                qr_elem = await page.wait_for_selector(
                    'canvas[aria-label="Scan this QR code to link a device!"]',
                    timeout=2000
                )
                
                if qr_elem:
                    # Precisa fazer QR Code
                    return ConnectionStatus(
                        status="qr_needed",
                        is_authenticated=False
                    )
            except:
                pass
            
            # Verificar se está autenticado (tem lista de chats)
            try:
                chats = await page.wait_for_selector(
                    'div[data-testid="chat-list"]',
                    timeout=3000
                )
                
                if chats:
                    return ConnectionStatus(
                        status="connected",
                        is_authenticated=True
                    )
            except:
                pass
            
            # Estado desconhecido
            return ConnectionStatus(
                status="disconnected",
                is_authenticated=False
            )
            
        except Exception as e:
            logger.error(f"Get connection status error: {e}")
            return ConnectionStatus(
                status="error",
                is_authenticated=False,
                error=str(e)
            )
    
    async def disconnect(
        self,
        connection_id: str
    ) -> None:
        """
        Desconecta número WhatsApp.
        
        Implementa WhatsAppGateway.disconnect()
        """
        try:
            await self.pool.close(connection_id)
            logger.info(f"Disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    async def get_qr_code(
        self,
        connection_id: str
    ) -> Optional[str]:
        """
        Obtém QR Code para autenticação.
        
        Implementa WhatsAppGateway.get_qr_code()
        
        Returns:
            QR Code em base64 ou None
        """
        try:
            context = await self.pool.get_or_create(connection_id)
            page = context.pages[0]
            
            # Verificar se tela de QR existe
            qr_selector = 'canvas[aria-label="Scan this QR code to link a device!"]'
            
            try:
                qr_elem = await page.wait_for_selector(qr_selector, timeout=5000)
                
                if qr_elem:
                    # Capturar screenshot do QR Code
                    qr_screenshot = await qr_elem.screenshot()
                    
                    # Converter para base64
                    import base64
                    qr_base64 = base64.b64encode(qr_screenshot).decode('utf-8')
                    
                    logger.info(f"QR Code generated for {connection_id}")
                    return qr_base64
                    
            except:
                # Não está na tela de QR (pode já estar autenticado)
                logger.info(f"No QR Code needed for {connection_id}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Get QR Code error: {e}")
            return None
    
    async def shutdown(self):
        """Desliga tudo gracefully."""
        logger.info("Shutting down PlaywrightWhatsAppGateway...")
        await self.pool.close_all()
