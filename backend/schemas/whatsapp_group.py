"""
Pyd

antic schemas for WhatsAppGroup model.
"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional


class WhatsAppGroupBase(BaseModel):
    """Base schema for WhatsAppGroup"""
    display_name: str
    is_source: bool = False
    is_destination: bool = False


class WhatsAppGroupCreate(WhatsAppGroupBase):
    """Schema for creating a new group (via discovery)"""
    last_message_preview: Optional[str] = None


class WhatsAppGroupUpdate(BaseModel):
    """Schema for updating group configuration"""
    is_source: Optional[bool] = None
    is_destination: Optional[bool] = None


class WhatsAppGroupResponse(WhatsAppGroupBase):
    """Schema for group response"""
    id: UUID4
    connection_id: UUID4
    last_message_preview: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WhatsAppGroupBulkUpdate(BaseModel):
    """Schema for bulk updating groups"""
    source_groups: list[UUID4] = []
    destination_groups: list[UUID4] = []
