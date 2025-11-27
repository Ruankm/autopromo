"""
Model Offer - Ofertas processadas candidatas a envio.
"""
from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, TIMESTAMP, text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from core.database import Base


class Offer(Base):
    """
    Oferta processada pelo worker.
    
    Cada registro representa uma mensagem de promoção que foi:
    - Ingerida
    - Deduplicada
    - Processada (link trocado, preço extraído)
    - Enfileirada para envio
    
    Status: 'pending', 'sent', 'discarded'
    """
    __tablename__ = "offers"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    source_platform = Column(String)       # 'telegram', 'whatsapp', 'affiliate_api'
    source_group_id = Column(String)       # ID do grupo de origem
    product_unique_id = Column(String)     # Ex: 'AMZN-B08XYZ', 'MLB-123456'
    
    raw_text = Column(Text)                # Texto original da oferta
    monetized_url = Column(Text)           # URL com tag de afiliado
    
    status = Column(String, nullable=False, server_default="pending")  # pending, sent, discarded
    
    # Metadata extra (opcional)
    offer_metadata = Column(JSONB, server_default=text("'{}'::jsonb"))
    
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="offers")
    
    # Indexes para performance
    __table_args__ = (
        Index('idx_offers_user', 'user_id'),
        Index('idx_offers_product', 'product_unique_id'),
        Index('idx_offers_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Offer(id={self.id}, product={self.product_unique_id}, status={self.status})>"
