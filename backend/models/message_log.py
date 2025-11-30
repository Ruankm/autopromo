"""
Message Log Model - Deduplicação POR CONEXÃO + GRUPO
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, BigInteger, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class MessageLog(Base):
    """
    Log de mensagens processadas - Deduplicação connection-scoped.
    
    CRÍTICO: Deduplicação deve ser por:
    - connection_id (cada cliente tem seu próprio log)
    - group_name (grupo específico)
    - message_id (ID único da mensagem)
    
    Isso evita que dois clientes com grupos de mesmo nome
    tenham conflito de deduplicação.
    """
    __tablename__ = "message_logs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # CRÍTICO: Connection ID para scoping correto
    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("whatsapp_connections.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Identificação da mensagem
    group_name = Column(String(200), nullable=False)  # Nome do grupo (não JID)
    message_id = Column(String(200), nullable=False)  # ID único do WhatsApp
    
    # Hash do texto (backup para deduplicação)
    text_hash = Column(String(32))  # MD5 do texto
    
    # Timestamp da mensagem
    timestamp = Column(BigInteger)  # Unix timestamp
    
    # Quando foi processada
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    connection = relationship("WhatsAppConnection", back_populates="message_logs")
    
    # Índices e constraints
    __table_args__ = (
        # Índice para queries rápidas (connection + grupo + msg_id)
        Index('idx_conn_group_msg', 'connection_id', 'group_name', 'message_id'),
        
        # Constraint de unicidade (evita duplicatas)
        UniqueConstraint(
            'connection_id',
            'group_name', 
            'message_id',
            name='uq_message_per_connection'
        ),
    )
    
    def __repr__(self):
        return f"<MessageLog {self.group_name} - {self.message_id[:8]}...>"
