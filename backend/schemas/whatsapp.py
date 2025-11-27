"""
Schemas para WhatsApp Evolution API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class WhatsAppInstanceCreate(BaseModel):
    """Schema para criar conexão WhatsApp."""
    api_url: str = Field(..., description="URL da Evolution API")
    api_key: str = Field(..., description="API Key da Evolution API")


class WhatsAppInstanceResponse(BaseModel):
    """Schema de resposta da instância WhatsApp."""
    id: UUID
    user_id: UUID
    instance_name: str
    status: str
    phone_number: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class QRCodeResponse(BaseModel):
    """Schema para resposta do QR Code."""
    qr_code: str = Field(..., description="QR Code em base64")
    instance_id: UUID
    status: str


class GroupDiscoveryResponse(BaseModel):
    """Schema para grupo descoberto."""
    id: UUID
    source_group_id: str
    group_name: str
    participant_count: int
    platform: str
    is_active: bool
    auto_discovered: bool
    discovered_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WhatsAppGroupInfo(BaseModel):
    """Informações de um grupo do WhatsApp (Evolution API)."""
    id: str = Field(..., description="ID do grupo (ex: 120363...@g.us)")
    subject: str = Field(..., description="Nome do grupo")
    size: int = Field(..., description="Número de participantes")
    creation: Optional[int] = Field(None, description="Timestamp de criação")
    owner: Optional[str] = Field(None, description="Dono do grupo")
