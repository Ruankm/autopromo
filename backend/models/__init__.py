"""SQLAlchemy models package."""
from .user import User
from .whatsapp_instance import WhatsAppInstance
from .affiliate_tag import AffiliateTag
from .group import GroupSource, GroupDestination
from .offer import Offer
from .price_history import PriceHistory
from .send_log import SendLog

# WhatsApp Web Automation Models
from .whatsapp_connection import WhatsAppConnection
from .whatsapp_group import WhatsAppGroup
from .message_log import MessageLog
from .offer_log import OfferLog

__all__ = [
    "User",
    "WhatsAppInstance",
    "AffiliateTag",
    "GroupSource",
    "GroupDestination",
    "Offer",
    "PriceHistory",
    "SendLog",
    # WhatsApp Automation
    "WhatsAppConnection",
    "WhatsAppGroup",
    "MessageLog",
    "OfferLog",
]
