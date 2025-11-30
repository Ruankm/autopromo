"""
Product History Model - Track price changes over time.

Enables:
- Price tracking
- Fake deal detection
- Smart recommendations
"""
from sqlalchemy import Column, String, Numeric, DateTime, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from core.database import Base


class ProductHistory(Base):
    """
    Historical price data for products.
    
    Used for:
    - Price trend analysis
    - Fake deal detection (inflated "from" price)
    - Smart recommendations
    """
    __tablename__ = "product_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Product identification
    store_slug = Column(String(50), nullable=False, index=True)  # amazon, magalu, ml
    product_id = Column(String(255), nullable=False, index=True)  # ASIN, MLB, etc
    
    # Price data
    current_price = Column(Numeric(10, 2), nullable=True)  # Actual selling price
    original_price = Column(Numeric(10, 2), nullable=True)  # "De" price (may be inflated)
    discount_percent = Column(Numeric(5, 2), nullable=True)  # Calculated discount
    
    # Product metadata
    title = Column(String(500), nullable=True)
    image_url = Column(String(1000), nullable=True)
    product_url = Column(String(1000), nullable=True)
    
    # Quality indicators
    rating = Column(Numeric(3, 2), nullable=True)  # 0.00 - 5.00
    review_count = Column(Integer, nullable=True)
    is_prime = Column(Boolean, default=False)
    
    # Additional data (coupons, badges, etc)
    extra_data = Column(JSONB, nullable=True)
    
    # Timestamps
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('ix_product_history_product', 'store_slug', 'product_id'),
        Index('ix_product_history_scraped_date', 'scraped_at'),
    )
    
    def __repr__(self):
        return f"<ProductHistory {self.store_slug}:{self.product_id} @ {self.current_price}>"
