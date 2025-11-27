"""
Model PriceHistory - Histórico de preços dos produtos.
"""
from sqlalchemy import Column, String, Integer, BigInteger, TIMESTAMP, text, Index

from core.database import Base


class PriceHistory(Base):
    """
    Histórico de preços para analytics e detecção de ofertas.
    
    Armazena o preço em centavos para evitar problemas com float.
    Ex: R$ 29,90 = 2990 centavos
    """
    __tablename__ = "price_history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    product_unique_id = Column(String, nullable=False)  # Ex: 'AMZN-B08XYZ'
    price_cents = Column(Integer, nullable=False)       # Preço em centavos
    currency = Column(String, server_default="BRL")     # Moeda (BRL por padrão)
    
    recorded_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Indexes para queries de histórico
    __table_args__ = (
        Index('idx_price_product', 'product_unique_id'),
        Index('idx_price_recorded', 'recorded_at'),
    )
    
    def __repr__(self):
        price_reais = self.price_cents / 100
        return f"<PriceHistory(product={self.product_unique_id}, price=R${price_reais:.2f})>"
