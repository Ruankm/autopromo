"""
Message Monitor - Monitora grupos fonte com deduplicação DB + cache.

Características:
- Deduplicação connection-scoped (cache + DB)
- Busca grupos por nome
- Extração de mensagens do DOM
- Fallback de seletores
- Healthcheck automático
"""
import hashlib
import logging
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from playwright.async_api import Page

from models.message_log import MessageLog
from services.whatsapp.gateway import WhatsAppMessage

logger = logging.getLogger(__name__)


class MessageMonitor:
    """
    Monitora grupos WhatsApp fonte por novas mensagens.
    
    Deduplicação em dois níveis:
    1. Cache em memória (rápido)
    2. Database (fonte da verdade, sobrevive restart)
    
    Connection-scoped: Cada conexão tem seu próprio log.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Cache por connection_id
        self.cache: Dict[str, Dict[str, dict]] = {}
        # cache[connection_id][group_name] = {"message_id": "...", "timestamp": 123}
    
    async def check_group(
        self,
        connection_id: str,
        page: Page,
        group_name: str
    ) -> Optional[WhatsAppMessage]:
        """
        Verifica grupo por nova mensagem.
        
        Args:
            connection_id: UUID da WhatsAppConnection
            page: Página do Playwright
            group_name: Nome do grupo
            
        Returns:
            WhatsAppMessage se encontrou nova, None caso contrário
        """
        try:
            # Abrir grupo
            await self._open_group(page, group_name)
            
            # Extrair última mensagem
            msg = await self._extract_last_message(page, group_name)
            
            if not msg:
                logger.debug(f"No message found in {group_name}")
                return None
            
            # Verificar se é nova (cache + DB)
            if await self._is_new_message(connection_id, group_name, msg):
                # Marcar como processada
                await self._mark_processed(connection_id, group_name, msg)
                logger.info(f"[NEW MESSAGE] {group_name}: {msg.text[:50]}...")
                return msg
            else:
                logger.debug(f"Message already processed: {msg.id}")
                return None
                
        except Exception as e:
            logger.error(f"Error checking {group_name}: {e}")
            return None
    
    async def _is_new_message(
        self,
        connection_id: str,
        group_name: str,
        msg: WhatsAppMessage
    ) -> bool:
        """
        Verifica se mensagem é nova (cache + DB).
        
        Returns:
            True se é nova e deve ser processada
        """
        # 1. Verificar cache primeiro (rápido)
        if connection_id in self.cache:
            if group_name in self.cache[connection_id]:
                cached = self.cache[connection_id][group_name]
                if msg.id == cached.get("message_id"):
                    return False
        
        # 2. Verificar DB (fonte da verdade)
        result = await self.db.execute(
            select(MessageLog).where(
                MessageLog.connection_id == connection_id,
                MessageLog.group_name == group_name,
                MessageLog.message_id == msg.id
            )
        )
        
        existing = result.scalar_one_or_none()
        
        return existing is None
    
    async def _mark_processed(
        self,
        connection_id: str,
        group_name: str,
        msg: WhatsAppMessage
    ):
        """
        Marca mensagem como processada (DB + cache).
        
        Args:
            connection_id: UUID da conexão
            group_name: Nome do grupo
            msg: Mensagem processada
        """
        # Salvar no DB
        text_hash = hashlib.md5(msg.text.encode()).hexdigest()
        
        log = MessageLog(
            connection_id=connection_id,
            group_name=group_name,
            message_id=msg.id,
            text_hash=text_hash,
            timestamp=msg.timestamp
        )
        
        self.db.add(log)
        await self.db.commit()
        
        # Atualizar cache
        if connection_id not in self.cache:
            self.cache[connection_id] = {}
        
        self.cache[connection_id][group_name] = {
            "message_id": msg.id,
            "timestamp": msg.timestamp
        }
        
        logger.debug(f"Marked as processed: {group_name} - {msg.id}")
    
    async def _open_group(self, page: Page, group_name: str):
        """
        Abre grupo via busca por nome.
        
        Mesma lógica do HumanizedSender._open_group
        """
        import asyncio
        import random
        
        # Seletores da barra de busca
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
            raise Exception("Search box not found")
        
        # Limpar e digitar
        await search_box.click()
        await asyncio.sleep(0.2)
        await page.keyboard.press('Control+A')
        await page.keyboard.press('Backspace')
        await asyncio.sleep(0.1)
        
        await search_box.type(group_name, delay=random.uniform(50, 100))
        await asyncio.sleep(1.5)
        
        # Clicar no resultado
        result_selectors = [
            f'span[title="{group_name}"]',
            'div[data-testid="cell-frame-container"]:first-child',
            'div[role="listitem"]:first-child'
        ]
        
        for selector in result_selectors:
            try:
                result = await page.wait_for_selector(selector, timeout=2000)
                if result:
                    await result.click()
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    return
            except:
                continue
        
        raise Exception(f"Group '{group_name}' not found")
    
    async def _extract_last_message(
        self,
        page: Page,
        group_name: str
    ) -> Optional[WhatsAppMessage]:
        """
        Extrai última mensagem do grupo (DOM).
        
        Returns:
            WhatsAppMessage ou None se não encontrar
        """
        import time
        
        # Seletores para última mensagem (com fallback)
        message_selectors = [
            'div[data-testid="msg-container"]:last-child',
            'div.message-in:last-child',
            'div[class*="message"]:last-child'
        ]
        
        message_elem = None
        for selector in message_selectors:
            try:
                message_elem = await page.wait_for_selector(selector, timeout=3000)
                if message_elem:
                    logger.debug(f"Message found via: {selector}")
                    break
            except:
                continue
        
        if not message_elem:
            logger.warning(f"No message element found in {group_name}")
            return None
        
        # Extrair dados da mensagem
        try:
            # Texto (seletores com fallback)
            text_selectors = [
                'span.copyable-text',
                'div[data-testid="conversation-text"]',
                'span[dir="ltr"]'
            ]
            
            text = ""
            for selector in text_selectors:
                try:
                    text_elem = await message_elem.query_selector(selector)
                    if text_elem:
                        text = await text_elem.inner_text()
                        if text:
                            break
                except:
                    continue
            
            if not text:
                # Fallback: pegar todo o texto do container
                text = await message_elem.inner_text()
            
            text = text.strip()
            
            if not text:
                logger.debug("Message has no text content")
                return None
            
            # ID da mensagem (usar hash do texto + timestamp como fallback)
            timestamp = int(time.time())
            message_id = f"{group_name}_{timestamp}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
            
            # Criar WhatsAppMessage
            msg = WhatsAppMessage(
                id=message_id,
                group_id=group_name,
                sender="unknown",  # Não extraímos sender por enquanto
                text=text,
                timestamp=timestamp,
                has_media=False
            )
            
            return msg
            
        except Exception as e:
            logger.error(f"Error extracting message data: {e}")
            return None
