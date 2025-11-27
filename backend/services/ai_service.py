"""
Serviço de IA - Ganchos para funcionalidades futuras com LLMs.

IMPORTANTE: Este módulo contém APENAS STUBS (placeholders).
Nenhuma chamada real a APIs de IA é feita na V1.

Os ganchos estão preparados para integração futura com:
- Claude (Anthropic)
- Gemini (Google)

Casos de uso planejados:
1. Copywriting de "Super Ofertas" (quando desconto >= X%)
2. Classificação de categoria quando regras estáticas falharem
"""
from typing import Optional


async def generate_super_offer_copy(
    product_name: str,
    original_price_cents: int,
    current_price_cents: int,
    discount_percentage: float,
    store_name: str,
    original_text: Optional[str] = None
) -> str:
    """
    [FUTURO - V2] Gera copy persuasivo para ofertas com alto desconto.
    
    Quando implementado, este método vai:
    - Chamar Claude/Gemini via API
    - Passar contexto do produto e desconto
    - Gerar texto persuasivo mantendo informações factuais
    - Adicionar emojis e formatação otimizada
    
    Prompt planejado (exemplo):
    ```
    Você é um copywriter especializado em ofertas de afiliados.
    
    Produto: {product_name}
    Loja: {store_name}
    Preço original: R$ {original_price}
    Preço atual: R$ {current_price}
    Desconto: {discount_percentage}%
    
    Crie um texto persuasivo de 2-3 linhas destacando:
    - O desconto expressivo
    - Urgência (oferta limitada)
    - Benefício principal do produto
    
    Use emojis relevantes. Seja direto e impactante.
    NÃO invente informações. Use apenas os dados fornecidos.
    ```
    
    Args:
        product_name: Nome do produto
        original_price_cents: Preço original em centavos
        current_price_cents: Preço atual em centavos
        discount_percentage: Percentual de desconto
        store_name: Nome da loja
        original_text: Texto original da oferta (opcional)
    
    Returns:
        Texto gerado (na V1, retorna placeholder determinístico)
    """
    # V1: Retornar placeholder determinístico
    # V2: Chamar Claude/Gemini aqui
    
    original_price = original_price_cents / 100
    current_price = current_price_cents / 100
    
    placeholder = f"""🔥 OFERTA IMPERDÍVEL! {product_name}

💰 De R$ {original_price:.2f} por R$ {current_price:.2f}
📉 {discount_percentage:.0f}% OFF na {store_name}!

⚡ Aproveite enquanto dura!"""
    
    return placeholder


async def classify_offer_category(
    product_name: str,
    product_description: Optional[str] = None,
    store_name: Optional[str] = None
) -> str:
    """
    [FUTURO - V2] Classifica categoria da oferta usando IA.
    
    Usado como FALLBACK quando regras estáticas (regex, keywords) falharem.
    
    Quando implementado, este método vai:
    - Chamar Claude/Gemini via API
    - Passar nome e descrição do produto
    - Retornar categoria normalizada
    
    Prompt planejado (exemplo):
    ```
    Classifique este produto em UMA das categorias:
    - eletronicos
    - moda
    - casa
    - esportes
    - livros
    - beleza
    - alimentos
    - outros
    
    Produto: {product_name}
    Descrição: {product_description}
    
    Retorne APENAS o nome da categoria, em lowercase, sem explicações.
    ```
    
    Args:
        product_name: Nome do produto
        product_description: Descrição (opcional)
        store_name: Nome da loja (opcional)
    
    Returns:
        Categoria normalizada (na V1, retorna 'outros')
    """
    # V1: Retornar categoria padrão
    # V2: Chamar Claude/Gemini aqui
    
    # Regras estáticas simples (fallback básico)
    product_lower = product_name.lower()
    
    if any(word in product_lower for word in ['notebook', 'celular', 'fone', 'tv', 'tablet']):
        return 'eletronicos'
    elif any(word in product_lower for word in ['camisa', 'calça', 'tênis', 'roupa']):
        return 'moda'
    elif any(word in product_lower for word in ['panela', 'cama', 'mesa', 'cadeira']):
        return 'casa'
    else:
        return 'outros'


# Configuração futura de LLMs (não usado na V1)
AI_CONFIG = {
    "provider": "claude",  # ou "gemini"
    "model": "claude-3-5-sonnet-20241022",  # ou "gemini-2.0-flash-exp"
    "max_tokens": 200,
    "temperature": 0.7,
    "enabled": False  # V1: desabilitado
}
