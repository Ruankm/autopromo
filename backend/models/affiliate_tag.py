"""
Model AffiliateTag - Tags de afiliado por loja.
"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from core.database import Base


class AffiliateTag(Base):
    """
    Tag de afiliado para monetização.
    
    Cada usuário pode ter uma tag por loja (amazon, magalu, etc).
    Ex: user_id=XYZ, store_slug='amazon', tag_code='ruan-20'
    """
    __tablename__ = "affiliate_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    store_slug = Column(String, nullable=False)  # 'amazon', 'magalu', 'mercadolivre'
    tag_code = Column(String, nullable=False)     # Tag do afiliado para essa loja
    
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="affiliate_tags")
    
    # Constraint: um usuário só pode ter uma tag por loja
    __table_args__ = (
        UniqueConstraint('user_id', 'store_slug', name='uq_user_store'),
    )
    
    def __repr__(self):
        return f"<AffiliateTag(user_id={self.user_id}, store={self.store_slug}, tag={self.tag_code})>"
