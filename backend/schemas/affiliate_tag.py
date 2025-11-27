"""Schemas Pydantic para AffiliateTag."""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AffiliateTagCreate(BaseModel):
    """Schema para criação de tag de afiliado."""
    store_slug: str
    tag_code: str


class AffiliateTagResponse(BaseModel):
    """Schema de resposta com dados da tag."""
    id: UUID
    user_id: UUID
    store_slug: str
    tag_code: str
    created_at: datetime
    
    class Config:
        from_attributes = True
