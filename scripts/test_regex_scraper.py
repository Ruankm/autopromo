# Test usando Amazon Product Advertising API alternative - usar link direto
# Amazon.com tem endpoint público de dados de product que podemos tentar

import asyncio
import httpx

async def test():
    # Tentar via endpoint mobile do Amazon (mais leve)
    asin = "B09B8VGCR8"
    
    # URL do produto mobile - HTML mais simples
    url = f"https://www.amazon.com.br/dp/{asin}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    }
    
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
    
    # Procurar pela URL da imagem no HTML
    html = response.text
    
    # Procurar padrão de URL de imagem Amazon
    import re
    pattern = r'https://m\.media-amazon\.com/images/I/[^"\']+\._AC_[^"\']+\.jpg'
    matches = re.findall(pattern, html)
    
    if matches:
        # Pegar a maior resolução (SL1000 ou maior)
        high_res = [m for m in matches if 'SL1000' in m or 'SL1500' in m]
        if high_res:
            print(f"High res image: {high_res[0]}")
        else:
            print(f"Image found: {matches[0]}")
    else:
        print("No image found")

asyncio.run(test())
