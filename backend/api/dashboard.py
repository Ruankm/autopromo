"""API endpoints para dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.group import GroupSource, GroupDestination
from models.affiliate_tag import AffiliateTag
from models.offer import Offer

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retorna estatísticas para o dashboard."""
    
    # Total na fila (pending)
    queue_query = select(func.count(Offer.id)).where(
        Offer.user_id == current_user.id,
        Offer.status == 'pending'
    )
    total_queue = (await db.execute(queue_query)).scalar() or 0
    
    # Enviados hoje (mockado por enquanto, pois precisaria de query complexa em send_logs ou offers)
    # Vamos contar offers com status 'sent'
    sent_query = select(func.count(Offer.id)).where(
        Offer.user_id == current_user.id,
        Offer.status == 'sent'
    )
    sent_total = (await db.execute(sent_query)).scalar() or 0
    
    # Grupos ativos (source + destination)
    active_sources = (await db.execute(
        select(func.count(GroupSource.id)).where(GroupSource.user_id == current_user.id, GroupSource.is_active == True)
    )).scalar() or 0
    
    active_dests = (await db.execute(
        select(func.count(GroupDestination.id)).where(GroupDestination.user_id == current_user.id, GroupDestination.is_active == True)
    )).scalar() or 0
    
    # Tags ativas
    active_tags = (await db.execute(
        select(func.count(AffiliateTag.id)).where(AffiliateTag.user_id == current_user.id)
    )).scalar() or 0
    
    return {
        "total_queue": total_queue,
        "sent_today": sent_total, # TODO: Filtrar por data de hoje
        "active_groups": active_sources + active_dests,
        "active_tags": active_tags
    }


@router.get("/recent-offers")
async def get_recent_offers(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retorna últimas ofertas processadas."""
    query = select(Offer).where(
        Offer.user_id == current_user.id
    ).order_by(Offer.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    offers = result.scalars().all()
    
    return offers
