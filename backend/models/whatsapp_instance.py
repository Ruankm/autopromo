"""
Model WhatsAppInstance - Instâncias WhatsApp via Evolution API.
"""
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid

from core.database import Base


class WhatsAppInstance(Base):
    """
    Instância WhatsApp conectada via Evolution API.
    
    Cada usuário pode ter UMA instância WhatsApp conectada.
    A instância é criada no servidor Evolution API e vinculada ao usuário.
    """
    __tablename__ = "whatsapp_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Dados da Evolution API
    instance_name = Column(String(100), nullable=False, unique=True)
    api_url = Column(String(255), nullable=False)
    api_key = Column(String(255), nullable=False)
    
    # Status da conexão
    status = Column(String(20), nullable=False, default="disconnected")
    qr_code = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Sync
    last_sync_at = Column(TIMESTAMP, nullable=True)
    
    # Metadados (nome da coluna no banco é 'metadata', mas usamos 'extra_metadata' no Python)
    extra_metadata = Column("metadata", JSON, default={}, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="whatsapp_instance")
    group_sources = relationship("GroupSource", back_populates="whatsapp_instance", cascade="all, delete-orphan")
    group_destinations = relationship("GroupDestination", back_populates="whatsapp_instance", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WhatsAppInstance(user_id={self.user_id}, status={self.status}, phone={self.phone_number})>"
