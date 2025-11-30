# Test inline - bypass cache
import sys
# Remove cached module
if 'services.scrapers.amazon_scraper' in sys.modules:
    del sys.modules['services.scrapers.amazon_scraper']

import asyncio
sys.path.insert(0, 'C:\\Users\\Ruan\\Desktop\\autopromo\\backend')

from services.scrapers.amazon_scraper import AmazonScraper

async def test():
    print("Testing updated scraper...")
    result = await AmazonScraper.scrape_product("B09B8VGCR8")
    
    if result:
        print(f"Title: {result.title}")
        print(f"Image: {result.image_url}")
        print(f"Price: {result.current_price}")
    else:
        print("FAILED")

asyncio.run(test())
