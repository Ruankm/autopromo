# -*- coding: utf-8 -*-
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.affiliate_tag import AffiliateTag
from models.group import GroupSource, GroupDestination

# JID do grupo CONFIRMADO
GROUP_SOURCE_JID = "120363042106955836@g.us"
GROUP_DEST_JID = "120363042106955836@g.us"  # Mesmo grupo para teste

async def quick_setup():
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("QUICK SETUP - Escorrega -> Autopromo")
        print("=" * 70)
        
        # User
        result = await db.execute(
            select(User).where(User.email == "ruan@test.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email="ruan@test.com",
                full_name="Ruan Test",
                password_hash="$2b$12$dummy",
                subscription_tier="premium",
                config_json={}
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        print(f"OK User: {user.email}")
        
        # Tags
        result = await db.execute(
            select(AffiliateTag).where(
                AffiliateTag.user_id == user.id,
                AffiliateTag.store_slug == "amazon"
            )
        )
        if not result.scalar_one_or_none():
            db.add(AffiliateTag(
                user_id=user.id,
                store_slug="amazon",
                tag_code="autopromo0b-20"
            ))
            await db.commit()
        
        print("OK Tag: amazon -> autopromo0b-20")
        
        # Source
        result = await db.execute(
            select(GroupSource).where(
                GroupSource.user_id == user.id,
                GroupSource.source_group_id == GROUP_SOURCE_JID
            )
        )
        if not result.scalar_one_or_none():
            db.add(GroupSource(
                user_id=user.id,
                platform="whatsapp",
                source_group_id=GROUP_SOURCE_JID,
                label="Escorrega",
                is_active=True
            ))
            await db.commit()
        
        print(f"OK Source: {GROUP_SOURCE_JID}")
        
        # Destination
        result = await db.execute(
            select(GroupDestination).where(
                GroupDestination.user_id == user.id,
                GroupDestination.destination_group_id == GROUP_DEST_JID
            )
        )
        if not result.scalar_one_or_none():
            db.add(GroupDestination(
                user_id=user.id,
                platform="whatsapp",
                destination_group_id=GROUP_DEST_JID,
                label="Autopromo",
                is_active=True
            ))
            await db.commit()
        
        print(f"OK Dest: {GROUP_DEST_JID}")
        
        print()
        print("=" * 70)
        print("SETUP COMPLETO!")
        print("=" * 70)
        print()
        print("Proximo: python scripts/configure_webhook.py")

if __name__ == "__main__":
    asyncio.run(quick_setup())
