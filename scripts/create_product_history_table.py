# -*- coding: utf-8 -*-
"""Create product_history table."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import text
from core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS product_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                store_slug VARCHAR(50) NOT NULL,
                product_id VARCHAR(255) NOT NULL,
                current_price NUMERIC(10, 2),
                original_price NUMERIC(10, 2),
                discount_percent NUMERIC(5, 2),
                title VARCHAR(500),
                image_url VARCHAR(1000),
                product_url VARCHAR(1000),
               rating NUMERIC(3, 2),
                review_count INTEGER,
                is_prime BOOLEAN DEFAULT FALSE,
                extra_data JSONB,
                scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS ix_product_history_store_slug ON product_history(store_slug);
            CREATE INDEX IF NOT EXISTS ix_product_history_product_id ON product_history(product_id);
            CREATE INDEX IF NOT EXISTS ix_product_history_scraped_at ON product_history(scraped_at);
            CREATE INDEX IF NOT EXISTS ix_product_history_product ON product_history(store_slug, product_id);
        """))
        
        await db.commit()
        print("✅ Table product_history created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
