"""
Monetization Service - URL reconstruction with affiliate tags.

AMAZON STRATEGY:
- Extract ASIN from any Amazon URL format
- Expand short links (amzn.to)
- Rebuild clean URL with user's tag
"""
import re
import httpx
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.affiliate_tag import AffiliateTag


# ============================================================================
# AMAZON ASIN EXTRACTION
# ============================================================================

def extract_amazon_asin(url: str) -> Optional[str]:
    """
    Extract ASIN (Amazon Standard Identification Number) from URL.
    
    Supports multiple formats:
    - https://amazon.com.br/dp/B09B8VGCR8
    - https://amazon.com.br/product-name/dp/B09B8VGCR8?ref=xyz
    - https://amazon.com.br/gp/product/B09B8VGCR8
    - https://www.amazon.com.br/Echo-Dot-5%C2%AA/dp/B09B8VGCR8?pd_rd_w=...
    
    Args:
        url: Amazon URL
    
    Returns:
        ASIN string (ex: B09B8VGCR8) or None
    """
    # Pattern 1: /dp/ASIN
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    # Pattern 2: /gp/product/ASIN
    match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    # Pattern 3: /product/ASIN
    match = re.search(r'/product/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    return None


async def expand_short_url(short_url: str, timeout: int = 5) -> str:
    """
    Expand shortened URLs by following redirects.
    
    Args:
        short_url: Short URL (ex: https://amzn.to/48Fpex6)
        timeout: Request timeout in seconds
    
    Returns:
        Final expanded URL or original if expansion fails
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.head(short_url)
            return str(response.url)
    except Exception:
        # Fallback: return original if expansion fails
        return short_url


def monetize_amazon_url(original_url: str, tag_code: str) -> str:
    """
    Monetize Amazon URL with affiliate tag.
    
    Strategy:
    1. Extract ASIN from URL
    2. Rebuild clean URL: amazon.com.br/dp/{ASIN}?tag={tag}
    
    Args:
        original_url: Original Amazon URL
        tag_code: Affiliate tag (ex: autopromo0b-20)
    
    Returns:
        Monetized URL
    
    Examples:
        Input:  https://www.amazon.com.br/Echo-Dot.../dp/B09B8VGCR8?pd_rd_w=...
        Output: https://www.amazon.com.br/dp/B09B8VGCR8?tag=autopromo0b-20
        
        Input:  https://amazon.com/gp/product/B09B8VGCR8
        Output: https://www.amazon.com.br/dp/B09B8VGCR8?tag=autopromo0b-20
    """
    asin = extract_amazon_asin(original_url)
    
    if not asin:
        # Can't extract ASIN - return original
        return original_url
    
    # Rebuild clean URL with tag
    return f"https://www.amazon.com.br/dp/{asin}?tag={tag_code}"


# ============================================================================
# AFFILIATE TAG LOOKUP
# ============================================================================

async def get_affiliate_tag(
    db: AsyncSession,
    user_id: str,
    store_slug: str
) -> Optional[str]:
    """
    Get user's affiliate tag for a store.
    
    Args:
        db: Database session
        user_id: User UUID
        store_slug: Store slug ('amazon', 'magalu', etc)
    
    Returns:
        Tag code or None
    """
    result = await db.execute(
        select(AffiliateTag).where(
            AffiliateTag.user_id == user_id,
            AffiliateTag.store_slug == store_slug
        )
    )
    
    tag = result.scalar_one_or_none()
    
    if tag:
        return tag.tag_code
    
    return None


def monetize_magalu_url(original_url: str, tag_code: str) -> str:
    """
    Monetize Magalu URL with affiliate parameter.
    
    Args:
        original_url: Original Magalu URL
        tag_code: Affiliate tag (parceiro ID)
    
    Returns:
        Monetized URL
    
    Example:
        Input:  magazineluiza.com.br/produto/123
        Output: magazineluiza.com.br/produto/123?parceiro=kamarao_cdb
    """
    base_url = original_url.split('?')[0]
    return f"{base_url}?parceiro={tag_code}"


def monetize_mercadolivre_url(original_url: str, tag_code: str) -> str:
    """
    Monetize Mercado Livre URL with mshops_redirect parameter.
    
    Args:
        original_url: Original ML URL
        tag_code: Affiliate tag (mshops ID)
    
    Returns:
        Monetized URL
    
    Examples:
        Input:  mercadolivre.com.br/produto/MLB123
        Output: mercadolivre.com.br/produto/MLB123?mshops_redirect=kamarao_cdb
        
        Input:  mercadolivre.com/sec/ABC123
        Output: mercadolivre.com/sec/ABC123?mshops_redirect=kamarao_cdb
    """
    separator = '&' if '?' in original_url else '?'
    return f"{original_url}{separator}mshops_redirect={tag_code}"


# ============================================================================
# MAIN MONETIZATION FUNCTION
# ============================================================================

async def monetize_url(
    db: AsyncSession,
    user_id: str,
    store_slug: Optional[str],
    original_url: str
) -> dict:
    """
    Monetize URL with user's affiliate tag.
    
    Flow:
    1. Expand short links if needed (amzn.to)
    2. Get user's affiliate tag
    3. Apply store-specific monetization
    
    Args:
        db: Database session
        user_id: User UUID
        store_slug: Store slug (amazon, magalu, mercadolivre)
        original_url: Original URL
    
    Returns:
        Dict with monetized_url and store_slug
    """
    # Expand short links for Amazon
    if store_slug == "amazon" and "amzn.to" in original_url:
        try:
            original_url = await expand_short_url(original_url)
        except Exception:
            pass  # Continue with short URL if expansion fails
    
    # No store detected
    if not store_slug:
        return {
            "monetized_url": original_url,
            "store_slug": "unknown"
        }
    
    # Get user's affiliate tag
    tag_code = await get_affiliate_tag(db, user_id, store_slug)
    
    # No tag configured
    if not tag_code:
        return {
            "monetized_url": original_url,
            "store_slug": store_slug
        }
    
    # Apply store-specific monetization
    monetizers = {
        "amazon": monetize_amazon_url,
        "magalu": monetize_magalu_url,
        "mercadolivre": monetize_mercadolivre_url,
    }
    
    monetizer = monetizers.get(store_slug)
    
    if monetizer:
        return {
            "monetized_url": monetizer(original_url, tag_code),
            "store_slug": store_slug
        }
    
    # Unsupported store
    return {
        "monetized_url": original_url,
        "store_slug": store_slug
    }
