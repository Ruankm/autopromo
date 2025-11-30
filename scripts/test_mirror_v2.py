"""
Test Mirror Service V2 - Integration test.

Validates:
- mirror_message_playwright() functionality
- OfferLog saving
- PlaywrightGateway integration
- Preview generation
"""
import asyncio
import uuid
from datetime import datetime
from sqlalchemy import select

# Add backend to path
import sys
from pathlib import Path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from core.database import AsyncSessionLocal
from models.whatsapp_connection import WhatsAppConnection
from models.user import User
from models.offer_log import OfferLog
from services.mirror_service_v2 import (
    mirror_message_playwright,
    mirror_to_all_destinations
)


async def setup_test_connection():
    """Create test connection in database."""
    async with AsyncSessionLocal() as db:
        # Get or create test user
        result = await db.execute(
            select(User).where(User.email == "test@autopromo.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="test@autopromo.com",
                password_hash="test_hash",
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # Create test connection
        connection = WhatsAppConnection(
            id=uuid.uuid4(),
            user_id=user.id,
            nickname="Test Connection",
            phone_number="+5511999999999",
            status="connected",  # Simulate connected
            source_groups=[
                {"name": "Grupo Teste Fonte"}
            ],
            destination_groups=[
                {"name": "Grupo Teste Destino 1"},
                {"name": "Grupo Teste Destino 2"}
            ],
            min_interval_per_group=60,
            min_interval_global=10,
            max_messages_per_day=100
        )
        
        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        
        print(f"[OK] Test connection created: {connection.id}")
        print(f"     User: {user.email}")
        print(f"     Nickname: {connection.nickname}")
        print(f"     Source groups: {len(connection.source_groups)}")
        print(f"     Destination groups: {len(connection.destination_groups)}")
        
        return connection.id, user.id


async def test_mirror_single():
    """Test mirroring to single destination."""
    print("\n=== TEST: mirror_message_playwright ===")
    
    connection_id, user_id = await setup_test_connection()
    
    test_message = """
    🔥 OFERTA IMPERDÍVEL!
    
    Notebook Gamer
    R$ 3.499,90
    
    Link: https://amazon.com.br/dp/B08XYZ123
    """
    
    async with AsyncSessionLocal() as db:
        result = await mirror_message_playwright(
            db=db,
            connection_id=str(connection_id),
            source_group_name="Grupo Teste Fonte",
            destination_group_name="Grupo Teste Destino 1",
            original_text=test_message
        )
        
        print(f"\n[RESULT]")
        print(f"  Status: {result.get('status')}")
        print(f"  Preview: {result.get('preview_generated')}")
        print(f"  Duration: {result.get('duration_ms')}ms")
        print(f"  Monetized URLs: {result.get('monetized_urls')}")
        
        # Check if OfferLog was saved
        if result.get('status') == 'sent':
            offer_result = await db.execute(
                select(OfferLog)
                .where(OfferLog.connection_id == connection_id)
                .order_by(OfferLog.created_at.desc())
                .limit(1)
            )
            
            offer = offer_result.scalar_one_or_none()
            
            if offer:
                print(f"\n[OFFER LOG SAVED]")
                print(f"  Source: {offer.source_group_name}")
                print(f"  Destination: {offer.destination_group_name}")
                print(f"  Links found: {len(offer.links_found)}")
                print(f"  Preview: {offer.preview_generated}")
                print(f"  Duration: {offer.send_duration_ms}ms")
            else:
                print(f"\n[WARNING] OfferLog not found!")
        
        return result


async def test_mirror_broadcast():
    """Test mirroring to all destinations."""
    print("\n=== TEST: mirror_to_all_destinations ===")
    
    connection_id, user_id = await setup_test_connection()
    
    test_message = """
    💰 SUPER DESCONTO!
    
    Fone Bluetooth
    De R$ 299,00 por R$ 149,90
    
    https://magazineluiza.com.br/produto/ABC123
    """
    
    async with AsyncSessionLocal() as db:
        result = await mirror_to_all_destinations(
            db=db,
            connection_id=str(connection_id),
            source_group_name="Grupo Teste Fonte",
            original_text=test_message
        )
        
        print(f"\n[BROADCAST RESULT]")
        print(f"  Status: {result.get('status')}")
        print(f"  Sent: {result.get('sent')}")
        print(f"  Failed: {result.get('failed')}")
        
        for idx, res in enumerate(result.get('results', []), 1):
            print(f"\n  Destination {idx}: {res.get('destination')}")
            print(f"    Status: {res.get('status')}")
            print(f"    Preview: {res.get('preview_generated')}")
            print(f"    Duration: {res.get('duration_ms')}ms")
        
        return result


async def test_offer_log_stats():
    """Test OfferLog statistics query."""
    print("\n=== TEST: OfferLog Statistics ===")
    
    connection_id, user_id = await setup_test_connection()
    
    async with AsyncSessionLocal() as db:
        # Count total offers
        from sqlalchemy import func
        
        total_result = await db.execute(
            select(func.count(OfferLog.id))
            .where(OfferLog.connection_id == connection_id)
        )
        total = total_result.scalar() or 0
        
        # Get recent offers
        recent_result = await db.execute(
            select(OfferLog)
            .where(OfferLog.connection_id == connection_id)
            .order_by(OfferLog.created_at.desc())
            .limit(5)
        )
        
        recent_offers = recent_result.scalars().all()
        
        print(f"\n[STATISTICS]")
        print(f"  Total offers: {total}")
        print(f"  Recent offers: {len(recent_offers)}")
        
        for offer in recent_offers:
            print(f"\n  - {offer.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    {offer.source_group_name} → {offer.destination_group_name}")
            print(f"    Links: {len(offer.links_found)}")
            print(f"    Preview: {offer.preview_generated}")


async def cleanup():
    """Clean up test data."""
    print("\n=== CLEANUP ===")
    
    async with AsyncSessionLocal() as db:
        # Delete test connections
        result = await db.execute(
            select(WhatsAppConnection).where(
                WhatsAppConnection.nickname == "Test Connection"
            )
        )
        
        connections = result.scalars().all()
        
        for conn in connections:
            await db.delete(conn)
        
        await db.commit()
        
        print(f"[OK] Deleted {len(connections)} test connection(s)")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Mirror Service V2 - Integration Tests")
    print("=" * 60)
    
    try:
        # Test 1: Single destination
        await test_mirror_single()
        
        # Small delay
        await asyncio.sleep(2)
        
        # Test 2: Broadcast
        await test_mirror_broadcast()
        
        # Test 3: Statistics
        await test_offer_log_stats()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        # await cleanup()  # Uncomment to clean test data
        pass


if __name__ == "__main__":
    print("\n⚠️  NOTE: This test requires:")
    print("  1. PostgreSQL running")
    print("  2. Playwright installed")
    print("  3. WhatsApp Web accessible")
    print("  4. Test connection to be manually scanned (QR Code)")
    print("\nThis is a DRY RUN showing the flow.")
    print("For real testing, ensure all services are running.\n")
    
    asyncio.run(main())
