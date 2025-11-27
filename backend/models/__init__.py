"""SQLAlchemy models para todas as entidades do sistema."""
from .user import User
from .affiliate_tag import AffiliateTag
from .group import GroupSource, GroupDestination
from .offer import Offer
from .price_history import PriceHistory
from .send_log import SendLog

__all__ = [
    "User",
    "AffiliateTag",
    "GroupSource",
    "GroupDestination",
    "Offer",
    "PriceHistory",
    "SendLog",
]
