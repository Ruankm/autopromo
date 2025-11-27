"""
Models GroupSource e GroupDestination - Grupos fonte e destino.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from core.database import Base


class GroupSource(Base):
    """
    Grupo-Fonte: de onde vêm as promoções.
    
    Ex: Grupos do Telegram/WhatsApp que o usuário monitora.
    """
    __tablename__ = "group_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    platform = Column(String, nullable=False)           # 'telegram' ou 'whatsapp'
    source_group_id = Column(String, nullable=False)    # ID do grupo na plataforma
    label = Column(String)                               # Nome amigável (opcional)
    
    # WhatsApp Evolution API fields
    instance_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_instances.id", ondelete="CASCADE"), nullable=True)
    auto_discovered = Column(Boolean, default=False, nullable=False)
    discovered_at = Column(TIMESTAMP, nullable=True)
    group_name = Column(String(255), nullable=True)      # Nome original do grupo
    participant_count = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="group_sources")
    whatsapp_instance = relationship("WhatsAppInstance", back_populates="group_sources")
    
    def __repr__(self):
        return f"<GroupSource(user_id={self.user_id}, platform={self.platform}, label={self.label})>"


class GroupDestination(Base):
    """
    Grupo-Destino: para onde o afiliado envia as promoções.
    
    Ex: Canal do Telegram do próprio afiliado.
    """
    __tablename__ = "group_destinations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    platform = Column(String, nullable=False)                # 'telegram' ou 'whatsapp'
    destination_group_id = Column(String, nullable=False)    # ID do grupo de destino
    label = Column(String)                                    # Nome amigável (opcional)
    
    # WhatsApp Evolution API fields
    instance_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_instances.id", ondelete="CASCADE"), nullable=True)
    auto_discovered = Column(Boolean, default=False, nullable=False)
    discovered_at = Column(TIMESTAMP, nullable=True)
    group_name = Column(String(255), nullable=True)      # Nome original do grupo
    participant_count = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="group_destinations")
    whatsapp_instance = relationship("WhatsAppInstance", back_populates="group_destinations")
    
    def __repr__(self):
        return f"<GroupDestination(user_id={self.user_id}, platform={self.platform}, label={self.label})>"
