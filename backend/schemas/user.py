"""Schemas Pydantic para User."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    """Schema para criação de usuário."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(default="")  # Optional field, defaults to empty string


class UserLogin(BaseModel):
    """Schema para login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema de resposta com dados do usuário."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    config_json: dict
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema para atualização de configurações do usuário."""
    config_json: Optional[dict] = None


class Token(BaseModel):
    """Schema de resposta do token JWT."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
