"""
Parsing Service - Extração de informações de lojas e produtos.

Identifica lojas, extrai IDs de produtos e cria product_unique_id.
"""
import re
from typing import Optional, Tuple
import httpx


# ============================================================================
# STORE DETECTION
# ============================================================================

STORE_PATTERNS = {
    "amazon": [
        r"amazon\.com\.br",
        r"amzn\.to",
        r"a\.co",
    ],
    "magalu": [
        r"magazineluiza\.com\.br",
        r"magalu\.com\.br",
    ],
    "mercadolivre": [
        r"mercadolivre\.com\.br",
        r"produto\.mercadolivre\.com\.br",
    ],
    "americanas": [
        r"americanas\.com\.br",
    ],
    "shopee": [
        r"shopee\.com\.br",
    ],
}


def detect_store(url: str) -> Optional[str]:
    """
    Detecta a loja a partir da URL.
    
    Args:
        url: URL do produto
    
    Returns:
        Slug da loja ('amazon', 'magalu', etc) ou None
    """
    url_lower = url.lower()
    
    for store_slug, patterns in STORE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return store_slug
    
    return None


# ============================================================================
# PRODUCT ID EXTRACTION
# ============================================================================

def extract_amazon_asin(url: str) -> Optional[str]:
    """
    Extrai ASIN da Amazon.
    
    Exemplos:
    - /dp/B08XYZ123
    - /gp/product/B08XYZ123
    - amzn.to/abc (após unshorten)
    
    Args:
        url: URL da Amazon
    
    Returns:
        ASIN (ex: 'B08XYZ123') ou None
    """
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_magalu_product_id(url: str) -> Optional[str]:
    """
    Extrai ID de produto do Magalu.
    
    Exemplo: magazineluiza.com.br/produto/123456789
    
    Args:
        url: URL do Magalu
    
    Returns:
        ID do produto ou None
    """
    pattern = r'/produto/(\d+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    return None


def extract_mercadolivre_mlb(url: str) -> Optional[str]:
    """
    Extrai MLB (MercadoLivre Brasil) ID.
    
    Exemplo: produto.mercadolivre.com.br/MLB-1234567890
    
    Args:
        url: URL do Mercado Livre
    
    Returns:
        MLB ID (ex: 'MLB-1234567890') ou None
    """
    pattern = r'(MLB-?\d+)'
    match = re.search(pattern, url, re.IGNORECASE)
    
    if match:
        mlb_id = match.group(1).upper()
        # Normalizar formato
        if not mlb_id.startswith("MLB-"):
            mlb_id = mlb_id.replace("MLB", "MLB-")
        return mlb_id
    
    return None


def extract_product_id(store_slug: str, url: str) -> Optional[str]:
    """
    Extrai ID de produto baseado na loja.
    
    Args:
        store_slug: Slug da loja ('amazon', 'magalu', etc)
        url: URL do produto
    
    Returns:
        ID do produto ou None
    """
    extractors = {
        "amazon": extract_amazon_asin,
        "magalu": extract_magalu_product_id,
        "mercadolivre": extract_mercadolivre_mlb,
    }
    
    extractor = extractors.get(store_slug)
    if extractor:
        return extractor(url)
    
    return None


def create_product_unique_id(store_slug: str, product_id: str) -> str:
    """
    Cria product_unique_id padronizado.
    
    Formato: STORE-PRODUCTID
    Exemplo: AMZN-B08XYZ123, MGLU-123456, MLB-1234567890
    
    Args:
        store_slug: Slug da loja
        product_id: ID do produto
    
    Returns:
        product_unique_id formatado
    """
    store_prefixes = {
        "amazon": "AMZN",
        "magalu": "MGLU",
        "mercadolivre": "MLB",
        "americanas": "AMER",
        "shopee": "SHOP",
    }
    
    prefix = store_prefixes.get(store_slug, store_slug.upper()[:4])
    
    # Se já tem prefixo (ex: MLB-123), não duplicar
    if product_id.startswith(prefix + "-"):
        return product_id
    
    return f"{prefix}-{product_id}"


# ============================================================================
# URL UNSHORTENING
# ============================================================================

async def unshorten_url(short_url: str, max_redirects: int = 5) -> str:
    """
    Resolve URL encurtada seguindo redirects.
    
    Usa HTTP HEAD para velocidade.
    
    **ROBUSTEZ**:
    - Timeout baixo (3s) para não travar o worker
    - Limite de redirects (5)
    - Fallback para URL original em caso de erro
    
    Args:
        short_url: URL encurtada (ex: amzn.to/abc123)
        max_redirects: Número máximo de redirects a seguir
    
    Returns:
        URL final (ou URL original se falhar)
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=max_redirects,
            timeout=3.0  # Timeout de 3 segundos
        ) as client:
            response = await client.head(short_url)
            return str(response.url)
    
    except httpx.TimeoutException:
        # Timeout - usar URL original
        import logging
        logging.warning(f"Timeout unshortening {short_url}, using original")
        return short_url
    
    except httpx.TooManyRedirects:
        # Muitos redirects - usar URL original
        import logging
        logging.warning(f"Too many redirects for {short_url}, using original")
        return short_url
    
    except Exception as e:
        # Qualquer outro erro - fallback para original
        import logging
        logging.warning(f"Failed to unshorten {short_url}: {e}, using original")
        return short_url


#============================================================================
# PRICE EXTRACTION
# ============================================================================

def extract_price_from_text(text: str) -> Optional[int]:
    """
    Extrai preço do texto e converte para centavos.
    
    **ZERO ALUCINAÇÃO**: Se não houver preço claro, retorna None.
    NÃO inventa nem adivinha preços.
    
    Padrões suportados (muito específicos):
    - R$ 199,90
    - 199,90
    - por R$ 99,99
    
    Args:
        text: Texto contendo preço
    
    Returns:
        Preço em centavos (ex: 19990 para R$ 199,90) ou None
    """
    # Padrões de preço - MUITO ESPECÍFICOS
    patterns = [
        r'R\$\s*(\d{1,6})[,.](\d{2})\b',  # R$ 199,90 (limita a 999.999,99)
        r'por\s+R\$\s*(\d{1,6})[,.](\d{2})\b',  # por R$ 99,90
        r'\b(\d{1,6})[,.](\d{2})\s*reais\b',  # 99,90 reais
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                reais = int(match.group(1))
                centavos = int(match.group(2))
                
                # Validação adicional: preços muito altos ou muito baixos são suspeitos
                price_cents = reais * 100 + centavos
                
                # Ignorar preços < R$ 0,10 ou > R$ 999.999,99
                if price_cents < 10 or price_cents > 99999999:
                    continue
                
                return price_cents
            
            except (ValueError, IndexError):
                # Se falhou o parse, não retornar nada
                continue
    
    # NÃO ENCONTROU PREÇO CLARO - retornar None
    # ZERO ALUCINAÇÃO: não inventar
    return None


# ============================================================================
# MAIN PARSING FUNCTION
# ============================================================================

async def parse_offer(url: str, text: str) -> dict:
    """
    Parse completo de uma oferta.
    
    Retorna todas as informações extraídas:
    - URL final (após unshorten)
    - Loja detectada
    - Product ID
    - Product Unique ID
    - Preço (se encontrado)
    
    Args:
        url: URL da oferta
        text: Texto da mensagem
    
    Returns:
        Dict com informações parse ada
    """
    # 1. Unshorten URL
    final_url = await unshorten_url(url)
    
    # 2. Detectar loja
    store_slug = detect_store(final_url)
    
    # 3. Extrair product ID
    product_id = None
    product_unique_id = None
    
    if store_slug:
        product_id = extract_product_id(store_slug, final_url)
        
        if product_id:
            product_unique_id = create_product_unique_id(store_slug, product_id)
    
    # 4. Extrair preço
    price_cents = extract_price_from_text(text)
    
    return {
        "original_url": url,
        "final_url": final_url,
        "store_slug": store_slug,
        "product_id": product_id,
        "product_unique_id": product_unique_id,
        "price_cents": price_cents,
    }
