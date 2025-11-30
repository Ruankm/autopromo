#!/usr/bin/env python3
"""
Configura cenário de teste no banco de dados:
- User de teste
- Affiliate Tags (Amazon, Mercado Livre, etc)
- GroupSource (Escorrega o Preço)
- GroupDestination (Autopromo)

ANTES DE EXECUTAR:
1. Execute scripts/list_groups.py para pegar os IDs
2. Edite GROUP_SOURCE_JID e GROUP_DEST_JID abaixo

Uso:
    python scripts/setup_test_scenario.py
"""
import asyncio
import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.affiliate_tag import AffiliateTag
from models.group import GroupSource, GroupDestination

# ============================================================================
# CONFIGURAÇÃO - EDITE AQUI COM OS IDs REAIS DO list_groups.py
# ============================================================================

# IDs dos grupos (formato: 5511XXXXXXXXX-YYYYYYYYYY@g.us)
GROUP_SOURCE_JID = "SEU_ID_ESCORREGA_AQUI@g.us"  # ← EDITAR
GROUP_DEST_JID = "SEU_ID_AUTOPROMO_AQUI@g.us"    # ← EDITAR

# Tags de afiliado (Amazon CONFIRMADA: autopromo0b-20)
AFFILIATE_TAGS = {
    "amazon": "autopromo0b-20",          # ✅ Confirmada
    "mercadolivre": "EDITAR_AQUI",       # ← EDITAR se tiver
    "magalu": "EDITAR_AQUI",             # ← EDITAR se tiver
}


async def setup_test_scenario():
    """Popula banco com cenário de teste."""
    
    # Validar configuração
    if "SEU_ID" in GROUP_SOURCE_JID or "SEU_ID" in GROUP_DEST_JID:
        print("❌ ERRO: Você precisa editar os IDs dos grupos!")
        print("   1. Execute: python scripts/list_groups.py")
        print("   2. Copie os IDs dos grupos 'Escorrega o Preço' e 'Autopromo'")
        print("   3. Edite este arquivo (setup_test_scenario.py)")
        print("   4. Rode novamente")
        return
    
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print(" SETUP DE CENÁRIO DE TESTE")
        print("=" * 80)
        print()
        
        # 1. Criar ou pegar usuário
        print("1️⃣ Configurando usuário...")
        result = await db.execute(
            select(User).where(User.email == "ruan@test.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email="ruan@test.com",
                full_name="Ruan Test",
                password_hash="$2b$12$dummy_hash_for_testing",
                subscription_tier="premium",
                config_json={}
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"   ✅ Usuário criado: {user.email} (ID: {user.id})")
        else:
            print(f"   ✅ Usuário existente: {user.email} (ID: {user.id})")
        
        user_id = user.id
        
        # 2. Criar Affiliate Tags
        print("\n2️⃣ Configurando tags de afiliado...")
        for store_slug, tag_code in AFFILIATE_TAGS.items():
            if tag_code == "EDITAR_AQUI":
                print(f"   ⚠️  {store_slug}: TAG NÃO CONFIGURADA (pulando)")
                continue
            
            result = await db.execute(
                select(AffiliateTag).where(
                    AffiliateTag.user_id == user_id,
                    AffiliateTag.store_slug == store_slug
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                tag = AffiliateTag(
                    user_id=user_id,
                    store_slug=store_slug,
                    tag_code=tag_code
                )
                db.add(tag)
                print(f"   ✅ {store_slug}: {tag_code}")
            else:
                print(f"   ✅ {store_slug}: {existing.tag_code} (já existe)")
        
        await db.commit()
        
        # 3. Criar GroupSource (Escorrega o Preço)
        print("\n3️⃣ Configurando grupo fonte (Escorrega o Preço)...")
        result = await db.execute(
            select(GroupSource).where(
                GroupSource.user_id == user_id,
                GroupSource.platform == "whatsapp",
                GroupSource.source_group_id == GROUP_SOURCE_JID
            )
        )
        group_source = result.scalar_one_or_none()
        
        if not group_source:
            group_source = GroupSource(
                user_id=user_id,
                platform="whatsapp",
                source_group_id=GROUP_SOURCE_JID,
                label="Escorrega o Preço",
                is_active=True
            )
            db.add(group_source)
            await db.commit()
            print(f"   ✅ GroupSource criado")
        else:
            print(f"   ✅ GroupSource já existe")
        
        print(f"      JID: {GROUP_SOURCE_JID}")
        
        # 4. Criar GroupDestination (Autopromo)
        print("\n4️⃣ Configurando grupo destino (Autopromo)...")
        result = await db.execute(
            select(GroupDestination).where(
                GroupDestination.user_id == user_id,
                GroupDestination.platform == "whatsapp",
                GroupDestination.destination_group_id == GROUP_DEST_JID
            )
        )
        group_dest = result.scalar_one_or_none()
        
        if not group_dest:
            group_dest = GroupDestination(
                user_id=user_id,
                platform="whatsapp",
                destination_group_id=GROUP_DEST_JID,
                label="Autopromo",
                is_active=True
            )
            db.add(group_dest)
            await db.commit()
            print(f"   ✅ GroupDestination criado")
        else:
            print(f"   ✅ GroupDestination já existe")
        
        print(f"      JID: {GROUP_DEST_JID}")
        
        # Resumo
        print()
        print("=" * 80)
        print(" ✅ SETUP COMPLETO!")
        print("=" * 80)
        print()
        print(f"User ID: {user_id}")
        print(f"Email: {user.email}")
        print(f"Tags: {len([t for t in AFFILIATE_TAGS.values() if t != 'EDITAR_AQUI'])} configuradas")
        print(f"Fonte: {GROUP_SOURCE_JID}")
        print(f"Destino: {GROUP_DEST_JID}")
        print()
        print("🎯 Próximo passo: python scripts/configure_webhook.py")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(setup_test_scenario())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
