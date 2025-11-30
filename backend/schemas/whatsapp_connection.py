"""
Schemas for WhatsApp Connections API.

Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field, UUID4
from typing import List, Optional
from datetime import datetime


# ============================================================================
# CONNECTION SCHEMAS
# ============================================================================

class GroupConfig(BaseModel):
    """Configuration for a single group (source or destination)."""
    name: str = Field(..., description="Group name")


class ConnectionCreate(BaseModel):
    """Schema for creating a new WhatsApp connection."""
    phone_number: Optional[str] = Field(None, description="Phone number (+5511999999999)")
    nickname: str = Field(..., description="Friendly name for this connection")
    
    source_groups: List[GroupConfig] = Field(default_factory=list, description="Source groups to monitor")
    destination_groups: List[GroupConfig] = Field(default_factory=list, description="Destination groups to send to")
    
    # Rate limiting
    min_interval_per_group: int = Field(360, description="Min seconds between messages per group (default: 6 min)")
    min_interval_global: int = Field(30, description="Min seconds between any messages (default: 30s)")
    max_messages_per_day: int = Field(1000, description="Max messages per day")
    
    # Plan config
    plan_name: str = Field("trial", description="Plan name (trial, basic, pro)")
    max_source_groups: int = Field(5, description="Max source groups allowed")
    max_destination_groups: int = Field(10, description="Max destination groups allowed")


class ConnectionUpdate(BaseModel):
    """Schema for updating connection configuration."""
    nickname: Optional[str] = None
    
    source_groups: Optional[List[GroupConfig]] = None
    destination_groups: Optional[List[GroupConfig]] = None
    
    min_interval_per_group: Optional[int] = None
    min_interval_global: Optional[int] = None
    max_messages_per_day: Optional[int] = None


class ConnectionResponse(BaseModel):
    """Schema for connection response."""
    id: UUID4
    user_id: UUID4
    
    phone_number: Optional[str]
    nickname: str
    status: str  # disconnected, qr_needed, connected, error
    
    source_groups: List[dict]
    destination_groups: List[dict]
    
    # Rate limits
    min_interval_per_group: int
    min_interval_global: int
    max_messages_per_day: int
    
    # Plan
    plan_name: str
    max_source_groups: int
    max_destination_groups: int
    
    # Health
    last_activity_at: Optional[datetime]
    last_error: Optional[str]
    messages_sent_today: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConnectionListResponse(BaseModel):
    """Schema for list of connections."""
    connections: List[ConnectionResponse]
    total: int


class QRCodeResponse(BaseModel):
    """Schema for QR Code response."""
    qr_code: str = Field(..., description="QR Code image in base64")
    status: str = Field(..., description="Connection status")


class ConnectionStatusResponse(BaseModel):
    """Schema for connection status."""
    status: str  # disconnected, qr_needed, connected, error
    is_authenticated: bool
    last_seen: Optional[datetime]
    error: Optional[str]


class ConnectionStatsResponse(BaseModel):
    """Schema for connection statistics."""
    connection_id: UUID4
    nickname: str
    
    # Counters
    total_offers_sent: int
    offers_sent_today: int
    offers_sent_this_week: int
    offers_sent_this_month: int
    
    # Recent activity
    last_offer_sent_at: Optional[datetime]
    
    # Groups
    active_source_groups: int
    active_destination_groups: int
