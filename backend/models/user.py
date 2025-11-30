"""
Model User - Usuário do SaaS (afiliado).
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from core.database import Base


class User(Base):
    """
    Usuário (afiliado) do AutoPromo Cloud.
    
    Cada usuário possui configurações próprias de janela de envio,
    delays, limites, e blacklist de lojas.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)  # Optional field for user display name
    
    # Configurações do usuário (JSON)
    # Exemplo: {"window_start": "08:00", "window_end": "22:00", "min_delay_seconds": 300}
    config_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationships (CASCADE via ondelete no FK da outra tabela)
    whatsapp_instance = relationship("WhatsAppInstance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    affiliate_tags = relationship("AffiliateTag", back_populates="user", cascade="all, delete-orphan")
    group_sources = relationship("GroupSource", back_populates="user", cascade="all, delete-orphan")
    group_destinations = relationship("GroupDestination", back_populates="user", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="user", cascade="all, delete-orphan")
    send_logs = relationship("SendLog", back_populates="user", cascade="all, delete-orphan")
    
    # WhatsApp Web Automation (Multi-número)
    whatsapp_connections = relationship("WhatsAppConnection", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
