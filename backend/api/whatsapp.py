"""
API endpoints para WhatsApp (Evolution API).

⚠️  LEGACY API - Evolution-based endpoints
    
    These endpoints are for old Evolution API integration.
    NEW API: api/whatsapp_connections.py (Playwright-based)
    
    All endpoints return 501 Not Implemented.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from api.deps import get_current_user
from models.user import User
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
    """
    Conecta WhatsApp via QR Code.
    
    DEPRECATED: Use /api/v1/connections instead (Playwright-based)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is deprecated. Use POST /api/v1/connections instead"
    )


@router.get("/status", response_model=WhatsAppInstanceResponse)
async def get_whatsapp_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna status da conexão.
    
    DEPRECATED: Use /api/v1/connections/{id}/status instead
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is deprecated. Use GET /api/v1/connections/{id}/status instead"
    )


@router.post("/discover-groups", response_model=List[GroupDiscoveryResponse])
async def discover_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Descobre grupos do WhatsApp.
    
    DEPRECATED: Groups are now auto-discovered in new Playwright implementation
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is deprecated. Groups are auto-discovered in new implementation"
    )


@router.delete("/disconnect")
async def disconnect_whatsapp(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Desconecta WhatsApp.
    
    DEPRECATED: Use DELETE /api/v1/connections/{id} instead
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is deprecated. Use DELETE /api/v1/connections/{id} instead"
    )
