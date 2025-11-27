# -*- coding: utf-8 -*-
"""
Script completo de setup para testes do pipeline - SEM EMOJIS (Windows CMD)
"""
import asyncio
import httpx
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.group import GroupSource, GroupDestination
from models.affiliate_tag import AffiliateTag
from core.security import get_password_hash
import uuid

API_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "worker_test@autopromo.com"
TEST_PASSWORD = "senha12345678"
TEST_GROUP_ID = "120363999999999999@g.us"

async def setup_test_data():
    """Cria dados de teste no banco."""
    async with AsyncSessionLocal() as db:
        print("[*] Criando dados de teste...")
        
        # Verificar se usuario ja existe
        result = await db.execute(select(User).where(User.email == TEST_EMAIL))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email=TEST_EMAIL,
                password_hash=get_password_hash(TEST_PASSWORD),
                full_name="Worker Test User"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"[OK] Usuario criado: {user.id}")
        else:
            print(f"[OK] Usuario ja existe: {user.id}")
        
        user_id = user.id
        
        # Criar grupo fonte
        result = await db.execute(
            select(GroupSource).where(
                GroupSource.user_id == user_id,
                GroupSource.source_group_id == TEST_GROUP_ID
            )
        )
        group_source = result.scalar_one_or_none()
        
        if not group_source:
            group_source = GroupSource(
                user_id=user_id,
                label="Grupo Teste Fonte",
                platform="whatsapp",
                source_group_id=TEST_GROUP_ID,
                is_active=True
            )
            db.add(group_source)
            await db.commit()
            print(f"[OK] Grupo fonte criado: {group_source.id}")
        else:
            print(f"[OK] Grupo fonte ja existe: {group_source.id}")
        
        # Criar grupo destino
        result = await db.execute(
            select(GroupDestination).where(
                GroupDestination.user_id == user_id
            )
        )
        group_dest = result.scalar_one_or_none()
        
        if not group_dest:
            group_dest = GroupDestination(
                user_id=user_id,
                label="Grupo Teste Destino",
                platform="whatsapp",
                destination_group_id="120363888888888888@g.us",
                is_active=True
            )
            db.add(group_dest)
            await db.commit()
            print(f"[OK] Grupo destino criado: {group_dest.id}")
        else:
            print(f"[OK] Grupo destino ja existe: {group_dest.id}")
        
        # Criar tag de afiliado
        result = await db.execute(
            select(AffiliateTag).where(
                AffiliateTag.user_id == user_id,
                AffiliateTag.store_slug == "amazon"
            )
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            tag = AffiliateTag(
                user_id=user_id,
                store_slug="amazon",
                tag_code="teste-21"
            )
            db.add(tag)
            await db.commit()
            print(f"[OK] Tag criada: {tag.id}")
        else:
            print(f"[OK] Tag ja existe: {tag.id}")
        
        print()
        print(f"[INFO] User ID: {user_id}")
        print(f"[INFO] Group ID: {TEST_GROUP_ID}")
        print()
        
        return user_id

async def send_test_webhook():
    """Envia webhook de teste."""
    print("[*] Enviando webhook de teste...")
    
    payload = {
        "event": "messages.upsert",
        "instance": "test_instance",
        "data": {
            "key": {
                "remoteJid": TEST_GROUP_ID,
                "fromMe": False,
                "id": f"TEST_{uuid.uuid4()}"
            },
            "message": {
                "conversation": "SUPER OFERTA! iPhone 15 Pro Max 256GB por apenas R$ 4.999! https://www.amazon.com.br/dp/B0CHX1W1XY"
            },
            "messageTimestamp": 1732633200
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/webhook/whatsapp",
            json=payload
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if result.get("status") == "queued":
            print("[OK] Mensagem enfileirada com sucesso!")
            return True
        else:
            print(f"[WARN] Status: {result.get('status')} - {result.get('reason')}")
            return False

async def main():
    print("=" * 80)
    print("SETUP DE TESTES - AutoPromo Cloud")
    print("=" * 80)
    print()
    
    user_id = await setup_test_data()
    success = await send_test_webhook()
    
    print()
    print("=" * 80)
    if success:
        print("[OK] SETUP COMPLETO!")
        print()
        print("[INFO] Proximos passos:")
        print("1. Rodar: cmd /c python -m workers.worker")
        print("2. Worker vai processar a mensagem")
        print("3. Verificar banco de dados para ver oferta criada")
    else:
        print("[ERROR] Erro no webhook. Verifique os logs acima.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
