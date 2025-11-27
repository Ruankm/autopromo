"""API endpoints para gerenciamento de tags de afiliado."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.affiliate_tag import AffiliateTag
from schemas.affiliate_tag import AffiliateTagCreate, AffiliateTagResponse

router = APIRouter(prefix="/affiliate-tags", tags=["Affiliate Tags"])


@router.get("", response_model=List[AffiliateTagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista tags de afiliado do usuário."""
    result = await db.execute(
        select(AffiliateTag).where(AffiliateTag.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("", response_model=AffiliateTagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_in: AffiliateTagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria nova tag de afiliado."""
    # Verificar duplicidade (store_slug)
    result = await db.execute(
        select(AffiliateTag).where(
            AffiliateTag.user_id == current_user.id,
            AffiliateTag.store_slug == tag_in.store_slug
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tag for this store already exists")

    new_tag = AffiliateTag(
        user_id=current_user.id,
        **tag_in.model_dump()
    )
    db.add(new_tag)
    await db.commit()
    await db.refresh(new_tag)
    return new_tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove tag de afiliado."""
    result = await db.execute(
        select(AffiliateTag).where(
            AffiliateTag.id == tag_id,
            AffiliateTag.user_id == current_user.id
        )
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    await db.delete(tag)
    await db.commit()
