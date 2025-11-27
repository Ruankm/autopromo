"""Schemas Pydantic para GroupSource e GroupDestination."""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class GroupSourceCreate(BaseModel):
    """Schema para criação de grupo-fonte."""
    platform: str
    source_group_id: str
    label: Optional[str] = None


class GroupSourceResponse(BaseModel):
    """Schema de resposta com dados do grupo-fonte."""
    id: UUID
    user_id: UUID
    platform: str
    source_group_id: str
    label: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class GroupDestinationCreate(BaseModel):
    """Schema para criação de grupo-destino."""
    platform: str
    destination_group_id: str
    label: Optional[str] = None


class GroupDestinationResponse(BaseModel):
    """Schema de resposta com dados do grupo-destino."""
    id: UUID
    user_id: UUID
    platform: str
    destination_group_id: str
    label: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
