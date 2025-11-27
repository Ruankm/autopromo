"""
Model SendLog - Log de envios para auditoria e deduplicação 24h.
"""
from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, TIMESTAMP, text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


class SendLog(Base):
    """
    Log de cada envio de oferta para auditoria e deduplicação.
    
    Usado para:
    - Garantir que o mesmo produto não seja enviado 2x em 24h
    - Analytics de performance
    - Auditoria
    """
    __tablename__ = "send_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    source_platform = Column(String)           # De onde veio a oferta
    destination_group_id = Column(String)      # Para onde foi enviado
    product_unique_id = Column(String)         # ID do produto
    
    original_url = Column(Text)                # URL original
    monetized_url = Column(Text)               # URL com tag de afiliado
    
    sent_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="send_logs")
    
    # Indexes críticos para deduplicação e queries
    __table_args__ = (
        Index('idx_logs_dedup', 'user_id', 'product_unique_id', 'sent_at'),
        Index('idx_logs_user_sent', 'user_id', 'sent_at'),
    )
    
    def __repr__(self):
        return f"<SendLog(id={self.id}, user_id={self.user_id}, product={self.product_unique_id})>"
