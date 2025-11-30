# -*- coding: utf-8 -*-
"""Limpa destino duplicado (teste)."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select, delete
from core.database import AsyncSessionLocal
from models.user import User
from models.group import GroupDestination

async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("LIMPANDO DESTINO DUPLICADO")
        print("=" * 70)
        
        # User
        result = await db.execute(select(User).where(User.email == "ruan@test.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("Usuario nao encontrado!")
            return
        
        # Deletar destino com JID do Escorrega (teste)
        escorrega_jid = "120363042106955836@g.us"
        
        result = await db.execute(
            delete(GroupDestination).where(
                GroupDestination.user_id == user.id,
                GroupDestination.destination_group_id == escorrega_jid
            )
        )
        
        deleted = result.rowcount
        await db.commit()
        
        print(f"Deletados: {deleted} destino(s) com JID do Escorrega")
        
        # Verificar destinos restantes
        result = await db.execute(
            select(GroupDestination).where(GroupDestination.user_id == user.id)
        )
        destinations = result.scalars().all()
        
        print(f"\nDestinos restantes: {len(destinations)}")
        for dest in destinations:
            print(f"  - {dest.label}: {dest.destination_group_id}")
        
        print("\n" + "=" * 70)
        print("OK! Agora o mirror vai enviar APENAS no Autopromo correto")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
