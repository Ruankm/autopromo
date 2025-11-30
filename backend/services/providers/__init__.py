"""
Providers package - External service integrations.

NOTE: Evolution API removed - now using Playwright-based WhatsApp automation.
See services/whatsapp/ for new implementation.
"""
from .telegram_bot import telegram_client, TelegramBotClient

__all__ = [
    "telegram_client",
    "TelegramBotClient",
]
