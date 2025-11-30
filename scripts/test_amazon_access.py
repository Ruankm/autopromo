# -*- coding: utf-8 -*-
"""Teste de acesso Amazon - verifica se consegue acessar a página."""
import asyncio
import httpx

async def test():
    url = "https://www.amazon.com.br/dp/B09B8VGCR8"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            
            print(f"Status: {response.status_code}")
            print(f"Content length: {len(response.text)} bytes")
            print(f"Title tag present: {'<title' in response.text}")
            print(f"Product title tag: {'productTitle' in response.text}")
            
            # Save HTML for inspection
            with open("amazon_response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("\nHTML saved to: amazon_response.html")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
