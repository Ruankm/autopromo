"""
Monetization Service - Reconstrução de URLs com tags de afiliado.

Busca tags do usuário e reconstrói URLs para monetização.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.affiliate_tag import AffiliateTag


async def get_affiliate_tag(
    db: AsyncSession,
    user_id: str,
    store_slug: str
) -> Optional[str]:
    """
    Busca tag de afiliado do usuário para uma loja.
    
    Args:
        db: Sessão do banco de dados
        user_id: UUID do usuário
        store_slug: Slug da loja ('amazon', 'magalu', etc)
    
    Returns:
        Tag code ou None se não encontrar
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


def monetize_amazon_url(original_url: str, tag_code: str) -> str:
    """
    Reconstrói URL da Amazon com tag de afiliado.
    
    Exemplo:
    Input: https://amazon.com.br/dp/B08XYZ123
    Output: https://amazon.com.br/dp/B08XYZ123?tag=meutag-20
    
    Args:
        original_url: URL original
        tag_code: Tag de afiliado
    
    Returns:
        URL monetizada
    """
    # Remover query string existente
    base_url = original_url.split('?')[0]
    
    # Adicionar tag
    return f"{base_url}?tag={tag_code}"


def monetize_magalu_url(original_url: str, tag_code: str) -> str:
    """
    Reconstrói URL do Magalu com tag de afiliado.
    
    Exemplo:
    Input: https://magazineluiza.com.br/produto/123456
    Output: https://magazineluiza.com.br/produto/123456?parceiro=meutag
    
    Args:
        original_url: URL original
        tag_code: Tag de afiliado
    
    Returns:
        URL monetizada
    """
    base_url = original_url.split('?')[0]
    return f"{base_url}?parceiro={tag_code}"


def monetize_mercadolivre_url(original_url: str, tag_code: str) -> str:
    """
    Monetiza URL do Mercado Livre com parâmetro mshops_redirect.
    
    Args:
        original_url: URL original do produto
        tag_code: Código da etiqueta de afiliado (ex: kamarao_cdb)
    
    Returns:
        URL monetizada
    
    Exemplos:
        Input:  mercadolivre.com.br/produto/MLB123
        Output: mercadolivre.com.br/produto/MLB123?mshops_redirect=kamarao_cdb
        
        Input:  mercadolivre.com/sec/ABC123
        Output: mercadolivre.com/sec/ABC123?mshops_redirect=kamarao_cdb
    """
    # Adicionar parâmetro mshops_redirect
    separator = '&' if '?' in original_url else '?'
    return f"{original_url}{separator}mshops_redirect={tag_code}"


async def monetize_url(
    db: AsyncSession,
    user_id: str,
    store_slug: Optional[str],
    original_url: str
) -> str:
    """
    Monetiza URL com tag de afiliado do usuário.
    
    Se não houver tag cadastrada, retorna URL original (fail-safe).
    
    Args:
        db: Sessão do banco de dados
        user_id: UUID do usuário
        store_slug: Slug da loja
        original_url: URL original
    
    Returns:
        URL monetizada (ou original se não houver tag)
    """
    # Se não detectou loja, retornar original
    if not store_slug:
        return original_url
    
    # Buscar tag do usuário
    tag_code = await get_affiliate_tag(db, user_id, store_slug)
    
    # Se não tiver tag, retornar original (fail-safe)
    if not tag_code:
        return original_url
    
    # Monetizar baseado na loja
    monetizers = {
        "amazon": monetize_amazon_url,
        "magalu": monetize_magalu_url,
        "mercadolivre": monetize_mercadolivre_url,
    }
    
    monetizer = monetizers.get(store_slug)
    
    if monetizer:
        return monetizer(original_url, tag_code)
    
    # Loja não suportada, retornar original
    return original_url
