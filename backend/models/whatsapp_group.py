"""
Model WhatsAppGroup - Grupos descobertos via DOM scraping.
"""
from sqlalchemy import Column, String, Boolean, Text, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from core.database import Base


class WhatsAppGroup(Base):
    """
    Grupo WhatsApp descoberto via DOM scraping.
    
    Identificado por display_name (nome visível na UI).
    Configurável como SOURCE (monitorado) ou DESTINATION (recebe mensagens).
    """
    __tablename__ = "whatsapp_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_connections.id", ondelete="CASCADE"), nullable=False)
    
    # Identificação (SEM JID - usamos busca sempre)
    display_name = Column(String(255), nullable=False)  # Nome que aparece na UI
    last_message_preview = Column(Text, nullable=True)   # Preview da última mensagem
    
    # Configuração (marcado pelo usuário via painel)
    is_source = Column(Boolean, nullable=False, server_default=text("false"))
    is_destination = Column(Boolean, nullable=False, server_default=text("false"))
    
    # Metadados
    last_sync_at = Column(TIMESTAMP, nullable=True)
    last_message_at = Column(TIMESTAMP, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationship
    connection = relationship("WhatsAppConnection", back_populates="groups")
    
    def __repr__(self):
        return f"<WhatsAppGroup(id={self.id}, display_name={self.display_name}, is_source={self.is_source}, is_destination={self.is_destination})>"
