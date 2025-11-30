"""
Product Intelligence Service - Price analysis and deal validation.

Features:
- Price history tracking
- Fake deal detection
- Quality score calculation
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_history import ProductHistory

logger = logging.getLogger(__name__)


class PriceAnalysis:
    """Container for price analysis results."""
    def __init__(self):
        self.avg_price_30d: Optional[float] = None
        self.avg_price_60d: Optional[float] = None
        self.avg_price_90d: Optional[float] = None
        self.min_price_30d: Optional[float] = None
        self.max_price_30d: Optional[float] = None
        self.quality_score: int = 0  # 0-100
        self.is_real_deal: bool = False
        self.is_inflated: bool = False
        self.recommendation: str = "UNKNOWN"


class ProductIntelligence:
    """Service for product price analysis."""
    
    @staticmethod
    async def save_product_snapshot(
        db: AsyncSession,
        store_slug: str,
        product_id: str,
        product_data: Dict
    ) -> ProductHistory:
        """
        Save product snapshot to history.
        
        Args:
            db: Database session
            store_slug: Store identifier
            product_id: Product ID (ASIN, MLB, etc)
            product_data: Product data dictionary
        
        Returns:
            ProductHistory instance
        """
        snapshot = ProductHistory(
            store_slug=store_slug,
            product_id=product_id,
            current_price=product_data.get("current_price"),
            original_price=product_data.get("original_price"),
            discount_percent=product_data.get("discount_percent"),
            title=product_data.get("title"),
            image_url=product_data.get("image_url"),
            product_url=product_data.get("product_url"),
            rating=product_data.get("rating"),
            review_count=product_data.get("review_count"),
            is_prime=product_data.get("is_prime", False),
            extra_data={
                "coupon_text": product_data.get("coupon_text"),
                "availability": product_data.get("availability"),
            },
            scraped_at=datetime.utcnow()
        )
        
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        
        logger.info(f"💾 Saved product snapshot: {store_slug}:{product_id}")
        return snapshot
    
    @staticmethod
    async def analyze_price_history(
        db: AsyncSession,
        store_slug: str,
        product_id: str,
        current_price: float,
        original_price: Optional[float] = None
    ) -> PriceAnalysis:
        """
        Analyze price history and detect fake deals.
        
        Args:
            db: Database session
            store_slug: Store identifier
            product_id: Product ID
            current_price: Current selling price
            original_price: "De" price (may be inflated)
        
        Returns:
            PriceAnalysis with recommendations
        """
        analysis = PriceAnalysis()
        
        # Calculate date thresholds
        now = datetime.utcnow()
        date_30d = now - timedelta(days=30)
        date_60d = now - timedelta(days=60)
        date_90d = now - timedelta(days=90)
        
        # Get historical prices (30d)
        result = await db.execute(
            select(
                func.avg(ProductHistory.current_price).label('avg'),
                func.min(ProductHistory.current_price).label('min'),
                func.max(ProductHistory.current_price).label('max')
            ).where(
                ProductHistory.store_slug == store_slug,
                ProductHistory.product_id == product_id,
                ProductHistory.scraped_at >= date_30d
            )
        )
        stats_30d = result.first()
        
        if stats_30d and stats_30d.avg:
            analysis.avg_price_30d = float(stats_30d.avg)
            analysis.min_price_30d = float(stats_30d.min)
            analysis.max_price_30d = float(stats_30d.max)
        
        # Get 60d average
        result = await db.execute(
            select(func.avg(ProductHistory.current_price)).where(
                ProductHistory.store_slug == store_slug,
                ProductHistory.product_id == product_id,
                ProductHistory.scraped_at >= date_60d
            )
        )
        avg_60d = result.scalar()
        if avg_60d:
            analysis.avg_price_60d = float(avg_60d)
        
        # Get 90d average
        result = await db.execute(
            select(func.avg(ProductHistory.current_price)).where(
                ProductHistory.store_slug == store_slug,
                ProductHistory.product_id == product_id,
                ProductHistory.scraped_at >= date_90d
            )
        )
        avg_90d = result.scalar()
        if avg_90d:
            analysis.avg_price_90d = float(avg_90d)
        
        # ANALYSIS: Detect inflated "from" price
        if original_price and analysis.avg_price_30d:
            # If "original" price is much higher than 30-day average, it's inflated
            inflation_threshold = analysis.avg_price_30d * 1.15  # 15% tolerance
            
            if original_price > inflation_threshold:
                analysis.is_inflated = True
                logger.warning(f"🚨 Inflated 'from' price detected: {original_price} vs avg {analysis.avg_price_30d}")
        
        # ANALYSIS: Real deal detection
        if analysis.avg_price_30d:
            # Real deal if current price is at least 10% below average
            if current_price < (analysis.avg_price_30d * 0.90):
                analysis.is_real_deal = True
                logger.info(f"🔥 REAL DEAL: {current_price} vs avg {analysis.avg_price_30d}")
        
        # QUALITY SCORE (0-100)
        score = 50  # Base score
        
        # +20 if real deal
        if analysis.is_real_deal:
            score += 20
        
        # -30 if inflated "from" price
        if analysis.is_inflated:
            score -= 30
        
        # +10 if current price is at min_price_30d
        if analysis.min_price_30d and abs(current_price - analysis.min_price_30d) < 0.01:
            score += 10
        
        # +20 if price is below 60d average
        if analysis.avg_price_60d and current_price < analysis.avg_price_60d:
            score += 20
        
        analysis.quality_score = max(0, min(100, score))
        
        # RECOMMENDATION
        if analysis.quality_score >= 70:
            analysis.recommendation = "EXCELENTE OFERTA 🔥"
        elif analysis.quality_score >= 50:
            analysis.recommendation = "BOA OFERTA ✅"
        elif analysis.quality_score >= 30:
            analysis.recommendation = "OFERTA MODERADA ⚠️"
        else:
            analysis.recommendation = "OFERTA SUSPEITA ❌"
        
        return analysis
