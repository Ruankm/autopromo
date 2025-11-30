"""
Offer Log Model - Histórico de ofertas espelhadas para analytics
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, JSON, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class OfferLog(Base):
    """
    Log de ofertas espelhadas - Base para analytics e inteligência de preços.
    
    Salva:
    - Texto original
    - Texto monetizado
    - Links encontrados e suas transformações
    - Grupos de origem/destino
    
    Futuro: Pode ser usado para:
    - Análise de performance de grupos
    - Histórico de preços
    - Estatísticas no painel do cliente
    - Machine learning / detecção de padrões
    """
    __tablename__ = "offer_logs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Conexão que enviou
    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("whatsapp_connections.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # De onde veio / para onde foi
    source_group_name = Column(String(200))
    destination_group_name = Column(String(200))
    
    # Conteúdo
    original_text = Column(Text)      # Texto original do grupo fonte
    monetized_text = Column(Text)     # Texto com links monetizados
    
    # Links encontrados e transformados
    links_found = Column(JSON, default=list)
    # Exemplo: [
    #   {
    #     "original": "https://amazon.com.br/dp/B123",
    #     "monetized": "https://amazon.com.br/dp/B123?tag=autopromo0b-20",
    #     "marketplace": "amazon"
    #   }
    # ]
    
    # Métricas
    preview_generated = Column(String(10))  # "yes", "no", "unknown"
    send_duration_ms = Column(Integer)       # Tempo para enviar (ms)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relacionamento
    connection = relationship("WhatsAppConnection", back_populates="offer_logs")
    
    # Índices para queries
    __table_args__ = (
        Index('idx_conn_created', 'connection_id', 'created_at'),
        Index('idx_source_group', 'source_group_name'),
        Index('idx_dest_group', 'destination_group_name'),
    )
    
    def __repr__(self):
        return f"<OfferLog {self.source_group_name} -> {self.destination_group_name}>"
