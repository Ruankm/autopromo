# -*- coding: utf-8 -*-
"""
Test Amazon Scraper - Validate product image extraction.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.scrapers.amazon_scraper import AmazonScraper

async def main():
    print("=" * 70)
    print("TESTE DO SCRAPER AMAZON")
    print("=" * 70)
    
    # Test ASIN from Echo Dot
    asin = "B09B8VGCR8"
    
    print(f"\nScraping product: {asin}")
    print(f"URL: https://www.amazon.com.br/dp/{asin}")
    
    result = await AmazonScraper.scrape_product(asin)
    
    if result:
        print("\n✅ SCRAPING SUCCESSFUL!")
        print(f"\nTítulo: {result.title}")
        print(f"Preço atual: R$ {result.current_price}")
        print(f"Preço original: R$ {result.original_price}")
        print(f"Desconto: {result.discount_percent}%")
        print(f"Rating: {result.rating} ({result.review_count} reviews)")
        print(f"Prime: {'Sim' if result.is_prime else 'Não'}")
        print(f"\nImagem URL:")
        print(f"{result.image_url}")
        
        if result.coupon_text:
            print(f"\nCupom: {result.coupon_text}")
        
        print("\n" + "=" * 70)
        print("IMAGEM EXTRAÍDA COM SUCESSO!")
        print("Esta URL pode ser enviada pelo WhatsApp")
        print("=" * 70)
    else:
        print("\n❌ Falha no scraping")

if __name__ == "__main__":
    asyncio.run(main())
