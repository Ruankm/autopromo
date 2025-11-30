"""
WhatsApp Connections API - CRUD + QR Code + Stats

Endpoints:
- POST /api/v1/connections - Create new connection
- GET /api/v1/connections - List all connections
- GET /api/v1/connections/{id} - Get connection details
- GET /api/v1/connections/{id}/qr - Get QR Code for authentication
- GET /api/v1/connections/{id}/status - Get connection status
- GET /api/v1/connections/{id}/stats - Get connection statistics
- PATCH /api/v1/connections/{id} - Update connection config
- DELETE /api/v1/connections/{id} - Delete connection
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timedelta
import uuid

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.whatsapp_connection import WhatsAppConnection
from models.offer_log import OfferLog
from schemas.whatsapp_connection import (
    ConnectionCreate,
    ConnectionUpdate,
    ConnectionResponse,
    ConnectionListResponse,
    QRCodeResponse,
    ConnectionStatusResponse,
    ConnectionStatsResponse
)
from services.whatsapp.playwright_gateway import PlaywrightWhatsAppGateway

router = APIRouter(prefix="/api/v1/connections", tags=["WhatsApp Connections"])


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new WhatsApp connection.
    
    Status will be 'disconnected' initially. User must scan QR Code.
    """
    # Create connection
    connection = WhatsAppConnection(
        id=uuid.uuid4(),
        user_id=current_user.id,
        phone_number=data.phone_number,
        nickname=data.nickname,
        status="disconnected",
        source_groups=[g.dict() for g in data.source_groups],
        destination_groups=[g.dict() for g in data.destination_groups],
        min_interval_per_group=data.min_interval_per_group,
        min_interval_global=data.min_interval_global,
        max_messages_per_day=data.max_messages_per_day,
        plan_name=data.plan_name,
        max_source_groups=data.max_source_groups,
        max_destination_groups=data.max_destination_groups
    )
    
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    
    return connection


@router.get("", response_model=ConnectionListResponse)
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all WhatsApp connections for current user."""
    result = await db.execute(
        select(WhatsAppConnection)
        .where(WhatsAppConnection.user_id == current_user.id)
        .order_by(WhatsAppConnection.created_at.desc())
    )
    
    connections = result.scalars().all()
    
    return ConnectionListResponse(
        connections=connections,
        total=len(connections)
    )


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single connection details."""
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    return connection


@router.patch("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: uuid.UUID,
    data: ConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update connection configuration."""
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Update fields
    update_data = data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in ["source_groups", "destination_groups"] and value is not None:
            # Convert to dict format
            setattr(connection, field, [g.dict() for g in value])
        else:
            setattr(connection, field, value)
    
    connection.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(connection)
    
    return connection


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete WhatsApp connection.
    
    This will also delete all associated message logs and offer logs (cascade).
    """
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    await db.delete(connection)
    await db.commit()
    
    return None


# ============================================================================
# QR CODE & STATUS ENDPOINTS
# ============================================================================

@router.get("/{connection_id}/qr", response_model=QRCodeResponse)
async def get_qr_code(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get QR Code for WhatsApp authentication.
    
    Returns base64-encoded QR Code image.
    Call this endpoint when status is 'qr_needed'.
    """
    # Verify ownership
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Get QR Code from gateway
    gateway = PlaywrightWhatsAppGateway(db=db)
    await gateway.start()
    
    try:
        qr_code = await gateway.get_qr_code(str(connection_id))
        
        if not qr_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR Code not available (already connected or error)"
            )
        
        # Update status
        connection.status = "qr_needed"
        await db.commit()
        
        return QRCodeResponse(
            qr_code=qr_code,
            status=connection.status
        )
    
    finally:
        await gateway.shutdown()


@router.get("/{connection_id}/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check connection status (real-time).
    
    This hits the actual Playwright context to check if WhatsApp is connected.
    """
    # Verify ownership
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Check real-time status
    gateway = PlaywrightWhatsAppGateway(db=db)
    await gateway.start()
    
    try:
        conn_status = await gateway.get_connection_status(str(connection_id))
        
        # Update database
        connection.status = conn_status.status
        connection.last_activity_at = datetime.utcnow()
        
        if conn_status.error:
            connection.last_error = conn_status.error
        
        await db.commit()
        
        return ConnectionStatusResponse(
            status=conn_status.status,
            is_authenticated=conn_status.is_authenticated,
            last_seen=conn_status.last_seen,
            error=conn_status.error
        )
    
    finally:
        await gateway.shutdown()


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@router.get("/{connection_id}/stats", response_model=ConnectionStatsResponse)
async def get_connection_stats(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get connection statistics.
    
    Returns offer counts and activity metrics.
    """
    # Verify ownership
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Get total offers
    total_result = await db.execute(
        select(func.count(OfferLog.id)).where(
            OfferLog.connection_id == connection_id
        )
    )
    total_offers = total_result.scalar() or 0
    
    # Offers today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(OfferLog.id)).where(
            OfferLog.connection_id == connection_id,
            OfferLog.created_at >= today_start
        )
    )
    offers_today = today_result.scalar() or 0
    
    # Offers this week
    week_start = today_start - timedelta(days=today_start.weekday())
    week_result = await db.execute(
        select(func.count(OfferLog.id)).where(
            OfferLog.connection_id == connection_id,
            OfferLog.created_at >= week_start
        )
    )
    offers_week = week_result.scalar() or 0
    
    # Offers this month
    month_start = today_start.replace(day=1)
    month_result = await db.execute(
        select(func.count(OfferLog.id)).where(
            OfferLog.connection_id == connection_id,
            OfferLog.created_at >= month_start
        )
    )
    offers_month = month_result.scalar() or 0
    
    # Last offer
    last_offer_result = await db.execute(
        select(OfferLog.created_at)
        .where(OfferLog.connection_id == connection_id)
        .order_by(OfferLog.created_at.desc())
        .limit(1)
    )
    last_offer_at = last_offer_result.scalar_one_or_none()
    
    return ConnectionStatsResponse(
        connection_id=connection.id,
        nickname=connection.nickname,
        total_offers_sent=total_offers,
        offers_sent_today=offers_today,
        offers_sent_this_week=offers_week,
        offers_sent_this_month=offers_month,
        last_offer_sent_at=last_offer_at,
        active_source_groups=len(connection.source_groups),
        active_destination_groups=len(connection.destination_groups)
    )
