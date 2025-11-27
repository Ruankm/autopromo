"""Test webhook using Python instead of curl."""
import httpx
import asyncio
import json

async def test_webhook():
    """Send test webhook to backend."""
    url = "http://localhost:8000/api/v1/webhook/whatsapp"
    
    payload = {
        "event": "messages.upsert",
        "instance": "test_instance",
        "data": {
            "key": {
                "remoteJid": "120363999999999999@g.us",
                "fromMe": False,
                "id": "TEST_VALIDATION_123"
            },
            "message": {
                "conversation": "🔥 OFERTA! iPhone 15 Pro Max por R$ 4.999 https://www.amazon.com.br/dp/B0CHX1W1XY"
            },
            "messageTimestamp": 1732633200
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
