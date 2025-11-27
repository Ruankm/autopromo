"""API endpoints para gerenciamento de grupos (Source/Destination)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.group import GroupSource, GroupDestination
from models.whatsapp_instance import WhatsAppInstance
from schemas.group import GroupSourceCreate, GroupSourceResponse, GroupDestinationCreate, GroupDestinationResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


# --- SOURCE GROUPS ---

@router.get("/source", response_model=List[GroupSourceResponse])
async def list_source_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista grupos de origem do usuário."""
    result = await db.execute(
        select(GroupSource).where(GroupSource.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/source", response_model=GroupSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source_group(
    group_in: GroupSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria novo grupo de origem.
    
    **ATENÇÃO**: Para plataforma WhatsApp, é necessário conectar o WhatsApp
    via QR Code ANTES de cadastrar grupos.
    """
    # GATEKEEPER: Validar conexão WhatsApp se platform == "whatsapp"
    if group_in.platform == "whatsapp":
        result = await db.execute(
            select(WhatsAppInstance).where(
                WhatsAppInstance.user_id == current_user.id,
                WhatsAppInstance.status == "connected"
            )
        )
        whatsapp_instance = result.scalar_one_or_none()
        
        if not whatsapp_instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WhatsApp não conectado. Conecte seu WhatsApp via QR Code antes de cadastrar grupos WhatsApp."
            )
    
    # Verificar duplicidade
    result = await db.execute(
        select(GroupSource).where(
            GroupSource.user_id == current_user.id,
            GroupSource.source_group_id == group_in.source_group_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group ID already exists")

    new_group = GroupSource(
        user_id=current_user.id,
        **group_in.model_dump()
    )
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group


@router.delete("/source/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove grupo de origem."""
    result = await db.execute(
        select(GroupSource).where(
            GroupSource.id == group_id,
            GroupSource.user_id == current_user.id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    await db.delete(group)
    await db.commit()


# --- DESTINATION GROUPS ---

@router.get("/destination", response_model=List[GroupDestinationResponse])
async def list_dest_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista grupos de destino do usuário."""
    result = await db.execute(
        select(GroupDestination).where(GroupDestination.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/destination", response_model=GroupDestinationResponse, status_code=status.HTTP_201_CREATED)
async def create_dest_group(
    group_in: GroupDestinationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria novo grupo de destino.
    
    **ATENÇÃO**: Para plataforma WhatsApp, é necessário conectar o WhatsApp
    via QR Code ANTES de cadastrar grupos.
    """
    # GATEKEEPER: Validar conexão WhatsApp se platform == "whatsapp"
    if group_in.platform == "whatsapp":
        result = await db.execute(
            select(WhatsAppInstance).where(
                WhatsAppInstance.user_id == current_user.id,
                WhatsAppInstance.status == "connected"
            )
        )
        whatsapp_instance = result.scalar_one_or_none()
        
        if not whatsapp_instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WhatsApp não conectado. Conecte seu WhatsApp via QR Code antes de cadastrar grupos WhatsApp."
            )
    
    # Verificar duplicidade
    result = await db.execute(
        select(GroupDestination).where(
            GroupDestination.user_id == current_user.id,
            GroupDestination.destination_group_id == group_in.destination_group_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group ID already exists")

    new_group = GroupDestination(
        user_id=current_user.id,
        **group_in.model_dump()
    )
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group


@router.delete("/destination/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dest_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove grupo de destino."""
    result = await db.execute(
        select(GroupDestination).where(
            GroupDestination.id == group_id,
            GroupDestination.user_id == current_user.id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    await db.delete(group)
    await db.commit()
