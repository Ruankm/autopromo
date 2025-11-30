# -*- coding: utf-8 -*-
"""Setup FINAL: Escorrega (fonte) -> Autopromo (destino)."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.affiliate_tag import AffiliateTag
from models.group import GroupSource, GroupDestination

# JIDs CONFIRMADOS
GROUP_SOURCE_JID = "120363042106955836@g.us"  # Escorrega o Preco
GROUP_DEST_JID = "120363423418139194@g.us"    # Autopromo (REAL!)

async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("SETUP FINAL: Escorrega -> Autopromo")
        print("=" * 70)
        
        # User
        result = await db.execute(select(User).where(User.email == "ruan@test.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email="ruan@test.com",
                full_name="Ruan Test",
                password_hash="$2b$12$dummy",
                config_json={}
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        print(f"OK User: {user.email}")
        
        # Tag Amazon
        result = await db.execute(
            select(AffiliateTag).where(
                AffiliateTag.user_id == user.id,
                AffiliateTag.store_slug == "amazon"
            )
        )
        tag = result.scalar_one_or_none()
        if not tag:
            tag = AffiliateTag(
                user_id=user.id,
                store_slug="amazon",
                tag_code="autopromo0b-20"
            )
            db.add(tag)
            await db.commit()
        
        print(f"OK Tag Amazon: {tag.tag_code}")
        
        # GroupSource (Escorrega o Preco)
        result = await db.execute(
            select(GroupSource).where(
                GroupSource.user_id == user.id,
                GroupSource.source_group_id == GROUP_SOURCE_JID
            )
        )
        src = result.scalar_one_or_none()
        if not src:
            src = GroupSource(
                user_id=user.id,
                platform="whatsapp",
                source_group_id=GROUP_SOURCE_JID,
                label="Escorrega o Preco",
                is_active=True
            )
            db.add(src)
            await db.commit()
        
        print(f"OK Source: {GROUP_SOURCE_JID} (Escorrega)")
        
        # GroupDestination (Autopromo - DIFERENTE!)
        result = await db.execute(
            select(GroupDestination).where(
                GroupDestination.user_id == user.id,
                GroupDestination.destination_group_id == GROUP_DEST_JID
            )
        )
        dest = result.scalar_one_or_none()
        if not dest:
            dest = GroupDestination(
                user_id=user.id,
                platform="whatsapp",
                destination_group_id=GROUP_DEST_JID,
                label="Autopromo",
                is_active=True
            )
            db.add(dest)
            await db.commit()
        
        print(f"OK Dest: {GROUP_DEST_JID} (Autopromo)")
        print()
        print("=" * 70)
        print("COMPLETO! PRONTO PARA TESTE!")
        print("=" * 70)
        print()
        print("TESTE AGORA:")
        print("1. Envie no 'Escorrega o Preco' uma mensagem com link Amazon")
        print("2. Veja chegar no 'Autopromo' com tag autopromo0b-20")
        print()
        print("Exemplo:")
        print("  TV Samsung OLED 55\"")
        print("  Por R$ 3.299")
        print("  https://amzn.to/abc123")

if __name__ == "__main__":
    asyncio.run(main())
