# -*- coding: utf-8 -*-
"""Verifica configuração de grupos no banco."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.group import GroupSource, GroupDestination

async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("VERIFICANDO GRUPOS CADASTRADOS")
        print("=" * 70)
        
        # User
        result = await db.execute(select(User).where(User.email == "ruan@test.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("Usuario nao encontrado!")
            return
        
        print(f"\nUsuario: {user.email}")
        
        # Grupos FONTE
        print("\n--- GRUPOS FONTE (de onde copia) ---")
        result = await db.execute(
            select(GroupSource).where(GroupSource.user_id == user.id)
        )
        sources = result.scalars().all()
        
        for src in sources:
            print(f"  - {src.label}: {src.source_group_id} (ativo={src.is_active})")
        
        # Grupos DESTINO
        print("\n--- GRUPOS DESTINO (para onde envia) ---")
        result = await db.execute(
            select(GroupDestination).where(GroupDestination.user_id == user.id)
        )
        destinations = result.scalars().all()
        
        for dest in destinations:
            print(f"  - {dest.label}: {dest.destination_group_id} (ativo={dest.is_active})")
        
        print("\n" + "=" * 70)
        print("ATENÇÃO:")
        print("  - Escorrega o Preco deve estar APENAS em FONTE")
        print("  - Autopromo deve estar APENAS em DESTINO")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
