"""Pydantic schemas for API validation."""
from .user import UserCreate, UserLogin, UserResponse, UserUpdate, Token
from .affiliate_tag import AffiliateTagCreate, AffiliateTagResponse
from .group import GroupSourceCreate, GroupSourceResponse, GroupDestinationCreate, GroupDestinationResponse
from .worker import IngestionQueueMessage, ProcessedOffer

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "Token",
    "AffiliateTagCreate",
    "AffiliateTagResponse",
    "GroupSourceCreate",
    "GroupSourceResponse",
    "GroupDestinationCreate",
    "GroupDestinationResponse",
    "IngestionQueueMessage",
    "ProcessedOffer",
]
