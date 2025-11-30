"""
API endpoints para WhatsApp (Evolution API).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
import httpx
import asyncio

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.whatsapp_instance import WhatsAppInstance
from models.group import GroupSource
from services.providers.whatsapp_evolution import EvolutionAPIClient
from schemas.whatsapp import (
    WhatsAppInstanceCreate,
    WhatsAppInstanceResponse,
    GroupDiscoveryResponse,
    QRCodeResponse
)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/connect", response_model=QRCodeResponse)
async def connect_whatsapp(
    payload: WhatsAppInstanceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Conecta WhatsApp via QR Code."""
    # Verificar se já conectado
    result = await db.execute(
        select(WhatsAppInstance).where(WhatsAppInstance.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    if existing and existing.status == "connected":
        raise HTTPException(400, "WhatsApp já conectado")
    
    # Criar instância
    instance_name = f"user_{current_user.id}_whatsapp"
    client = EvolutionAPIClient(payload.api_url, payload.api_key)
    
    try:
        print(f"[DEBUG] Creating instance: {instance_name}")
        print(f"[DEBUG] API URL: {payload.api_url}")
        print(f"[DEBUG] API Key: {payload.api_key[:10]}...")
        
        # Criar instância
        data = await client.create_instance(instance_name)
        print(f"[DEBUG] Instance created: {data}")
        
        # Aguardar QR Code ser gerado (processamento assíncrono na Evolution API)
        print(f"[DEBUG] Waiting for QR Code generation (3s)...")
        await asyncio.sleep(3)
        
        # Buscar QR Code com retry
        qr_code = None
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"[DEBUG] Fetching QR Code (attempt {attempt}/{max_attempts})...")
            qr_code = await client.fetch_qrcode(instance_name)
            
            if qr_code:
                print(f"[DEBUG] QR Code fetched successfully: {qr_code[:50]}...")
                break
            
            if attempt < max_attempts:
                print(f"[DEBUG] QR Code not ready yet, waiting 2s...")
                await asyncio.sleep(2)
        
        if not qr_code:
            print(f"[ERROR] QR Code not available after {max_attempts} attempts!")
            raise HTTPException(500, "QR Code não gerado após múltiplas tentativas. Verifique se a Evolution API está funcionando corretamente.")
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] HTTP Error creating instance: {e.response.status_code}")
        print(f"[ERROR] Response: {e.response.text}")
        raise HTTPException(500, f"Erro ao criar instância: {e.response.status_code} {e.response.text}")
    except Exception as e:
        print(f"[ERROR] Exception creating instance: {type(e).__name__}: {str(e)}")
        raise HTTPException(500, f"Erro ao criar instância: {str(e)}")
    
    # Salvar no banco
    if existing:
        existing.api_url = payload.api_url
        existing.api_key = payload.api_key
        existing.instance_name = instance_name
        existing.status = "connecting"
        existing.qr_code = qr_code
        existing.updated_at = datetime.utcnow()
        instance = existing
    else:
        instance = WhatsAppInstance(
            user_id=current_user.id,
            instance_name=instance_name,
            api_url=payload.api_url,
            api_key=payload.api_key,
            status="connecting",
            qr_code=qr_code
        )
        db.add(instance)
    
    await db.commit()
    await db.refresh(instance)
    
    return QRCodeResponse(
        qr_code=qr_code,
        instance_id=str(instance.id),
        status="connecting"
    )


@router.get("/status", response_model=WhatsAppInstanceResponse)
async def get_whatsapp_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retorna status da conexão."""
    result = await db.execute(
        select(WhatsAppInstance).where(WhatsAppInstance.user_id == current_user.id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(404, "WhatsApp não conectado")
    
    # Sync com Evolution API
    client = EvolutionAPIClient(instance.api_url, instance.api_key)
    
    try:
        status_data = await client.get_connection_status(instance.instance_name)
        
        if status_data.get("state") == "open":
            instance.status = "connected"
            instance.qr_code = None
        elif status_data.get("state") == "close":
            instance.status = "disconnected"
        
        instance.updated_at = datetime.utcnow()
        await db.commit()
    except:
        pass  # Manter status atual se falhar
    
    return WhatsAppInstanceResponse.model_validate(instance)


@router.post("/discover-groups", response_model=List[GroupDiscoveryResponse])
async def discover_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Descobre grupos do WhatsApp."""
    # Gatekeeper
    result = await db.execute(
        select(WhatsAppInstance).where(WhatsAppInstance.user_id == current_user.id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance or instance.status != "connected":
        raise HTTPException(400, "WhatsApp não conectado. Conecte via /dashboard/whatsapp primeiro.")
    
    # Buscar grupos
    client = EvolutionAPIClient(instance.api_url, instance.api_key)
    groups = await client.fetch_all_groups(instance.instance_name)
    
    discovered = []
    
    for group in groups:
        # Verificar se já existe
        result = await db.execute(
            select(GroupSource).where(
                GroupSource.user_id == current_user.id,
                GroupSource.source_group_id == group["id"]
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            new_group = GroupSource(
                user_id=current_user.id,
                instance_id=instance.id,
                platform="whatsapp",
                source_group_id=group["id"],
                label=group.get("subject", "Sem nome"),
                group_name=group.get("subject", "Sem nome"),
                participant_count=group.get("size", 0),
                is_active=False,
                auto_discovered=True,
                discovered_at=datetime.utcnow()
            )
            db.add(new_group)
            discovered.append(new_group)
        else:
            existing.group_name = group.get("subject", "Sem nome")
            existing.participant_count = group.get("size", 0)
            existing.discovered_at = datetime.utcnow()
            discovered.append(existing)
    
    await db.commit()
    instance.last_sync_at = datetime.utcnow()
    await db.commit()
    
    return [GroupDiscoveryResponse.model_validate(g) for g in discovered]


@router.delete("/disconnect")
async def disconnect_whatsapp(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Desconecta WhatsApp."""
    result = await db.execute(
        select(WhatsAppInstance).where(WhatsAppInstance.user_id == current_user.id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(404, "WhatsApp não encontrado")
    
    # Tentar deletar na Evolution
    client = EvolutionAPIClient(instance.api_url, instance.api_key)
    try:
        await client.delete_instance(instance.instance_name)
    except:
        pass
    
    # Marcar como desconectado
    instance.status = "disconnected"
    instance.qr_code = None
    instance.phone_number = None
    instance.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "WhatsApp desconectado com sucesso"}
