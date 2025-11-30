# -*- coding: utf-8 -*-
"""Test quick - verifica se scraper Amazon funciona."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def test():
    try:
        from services.scrapers.amazon_scraper import AmazonScraper
        
        print("Testing Amazon scraper...")
        print("ASIN: B09B8VGCR8")
        
        result = await AmazonScraper.scrape_product("B09B8VGCR8")
        
        if result:
            print("SUCCESS!")
            print(f"Title: {result.title}")
            print(f"Image: {result.image_url}")
            print(f"Price: {result.current_price}")
        else:
            print("FAILED - No result")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback        
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
