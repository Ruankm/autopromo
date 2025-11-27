"""
Telegram Provider Client - Telegram Bot API.

Este módulo gerencia o envio de mensagens via Telegram Bot API.
Toda comunicação com o provedor é feita via HTTP REST.
"""
import httpx
from typing import Optional
from core.config import settings


class TelegramBotClient:
    """Cliente para Telegram Bot API."""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False
    ) -> dict:
        """
        Envia mensagem de texto para um chat/grupo Telegram.
        
        Args:
            chat_id: ID do chat/grupo (ex: '-1001234567890')
            text: Texto da mensagem
            parse_mode: Modo de parse ('HTML', 'Markdown', ou None)
            disable_web_page_preview: Desabilitar preview de links
        
        Returns:
            Response do Telegram Bot API
        
        Raises:
            httpx.HTTPError: Em caso de erro na requisição
        """
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> dict:
        """
        Envia foto para um chat/grupo Telegram.
        
        Args:
            chat_id: ID do chat/grupo
            photo_url: URL da foto
            caption: Legenda opcional
            parse_mode: Modo de parse da legenda
        
        Returns:
            Response do Telegram Bot API
        """
        url = f"{self.base_url}/sendPhoto"
        
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption or "",
            "parse_mode": parse_mode
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()


# Instância global
telegram_client = TelegramBotClient()
