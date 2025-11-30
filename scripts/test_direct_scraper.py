# Test scraper directly
import asyncio
import httpx
from bs4 import BeautifulSoup

async def test():
    url = "https://www.amazon.com.br/dp/B09B8VGCR8"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find image
    img_elem = soup.find('img', {'id': 'landingImage'})
    if img_elem:
        img_url = img_elem.get('data-old-hires') or img_elem.get('src')
        print(f"Image URL: {img_url}")
    else:
        print("Image element not found")

asyncio.run(test())
