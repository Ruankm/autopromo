"""
API endpoints for WhatsApp Group management (DOM-based discovery).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
import json

from core.database import get_db
from core.redis_client import redis_client
from models.user import User
from models.whatsapp_connection import WhatsAppConnection
from models.whatsapp_group import WhatsAppGroup
from schemas.whatsapp_group import (
    WhatsAppGroupResponse,
    WhatsAppGroupUpdate,
    WhatsAppGroupBulkUpdate
)
from api.deps import get_current_user

router = APIRouter(prefix="/api/v1/connections", tags=["whatsapp_groups"])


@router.post("/{connection_id}/discover-groups")
async def discover_groups(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger group discovery via Worker.
    
    Worker will:
    1. Navigate to WhatsApp Web
    2. Click "Grupos" tab
    3. Scroll and extract group names
    4. Save to whatsapp_groups table
    
    Returns immediately - discovery happens async in Worker.
    """
    # Verify connection belongs to user
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if conn.status != "connected":
        raise HTTPException(
            status_code=400,
            detail=f"Connection must be 'connected' (current: {conn.status})"
        )
    
    # Publish Redis command to Worker
    command = {
        "type": "DISCOVER_GROUPS",
        "connection_id": str(connection_id),
        "user_id": str(current_user.id)
    }
    
    await redis_client.client.publish(
        "whatsapp:commands",
        json.dumps(command)
    )
    
    return {
        "status": "discovering",
        "message": "Group discovery started. Check GET /groups in 30-60 seconds."
    }


@router.get("/{connection_id}/groups", response_model=List[WhatsAppGroupResponse])
async def list_groups(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all discovered groups for a connection.
    
    Returns groups with:
    - display_name
    - is_source / is_destination flags
    - last_message_preview
    - timestamps
    """
    # Verify connection belongs to user
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Get groups
    result = await db.execute(
        select(WhatsAppGroup)
        .where(WhatsAppGroup.connection_id == connection_id)
        .order_by(WhatsAppGroup.display_name)
    )
    groups = result.scalars().all()
    
    return groups


@router.patch("/{connection_id}/groups/{group_id}", response_model=WhatsAppGroupResponse)
async def update_group(
    connection_id: str,
    group_id: str,
    update_data: WhatsAppGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update group configuration (is_source / is_destination).
    
    Used by frontend to mark which groups to monitor/send.
    """
    # Verify connection belongs to user
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Get group
    result = await db.execute(
        select(WhatsAppGroup).where(
            WhatsAppGroup.id == group_id,
            WhatsAppGroup.connection_id == connection_id
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Update fields
    if update_data.is_source is not None:
        group.is_source = update_data.is_source
    
    if update_data.is_destination is not None:
        group.is_destination = update_data.is_destination
    
    await db.commit()
    await db.refresh(group)
    
    return group


@router.patch("/{connection_id}/groups/bulk")
async def bulk_update_groups(
    connection_id: str,
    bulk_data: WhatsAppGroupBulkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update group configurations.
    
    Body:
    {
        "source_groups": ["uuid1", "uuid2"],
        "destination_groups": ["uuid3", "uuid4"]
    }
    
    Marks specified groups as source/destination.
    """
    # Verify connection belongs to user
    result = await db.execute(
        select(WhatsAppConnection).where(
            WhatsAppConnection.id == connection_id,
            WhatsAppConnection.user_id == current_user.id
        )
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Reset all flags first
    await db.execute(
        update(WhatsAppGroup)
        .where(WhatsAppGroup.connection_id == connection_id)
        .values(is_source=False, is_destination=False)
    )
    
    # Set source groups
    if bulk_data.source_groups:
        await db.execute(
            update(WhatsAppGroup)
            .where(
                WhatsAppGroup.connection_id == connection_id,
                WhatsAppGroup.id.in_(bulk_data.source_groups)
            )
            .values(is_source=True)
        )
    
    # Set destination groups
    if bulk_data.destination_groups:
        await db.execute(
            update(WhatsAppGroup)
            .where(
                WhatsAppGroup.connection_id == connection_id,
                WhatsAppGroup.id.in_(bulk_data.destination_groups)
            )
            .values(is_destination=True)
        )
    
    await db.commit()
    
    return {
        "status": "success",
        "source_groups_updated": len(bulk_data.source_groups),
        "destination_groups_updated": len(bulk_data.destination_groups)
    }
