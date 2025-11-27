"""
Debug script to see exact QR Code structure
"""
import httpx
import asyncio
import json

API_URL = "http://localhost:8081"
API_KEY = "f708f2fc-471f-4511-83c3-701229e766d5"

async def main():
    headers = {"apikey": API_KEY}
    
    # Delete old instance
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.delete(f"{API_URL}/instance/delete/AutoPromo_20251126_184020", headers=headers)
    
    await asyncio.sleep(2)
    
    # Create new one
    payload = {
        "instanceName": "DEBUG_TEST",
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{API_URL}/instance/create", json=payload, headers=headers)
        data = resp.json()
        
        print("=== FULL RESPONSE ===")
        print(json.dumps(data, indent=2))
        print()
        
        print("=== QR CODE OBJECT ===")
        if "qrcode" in data:
            qr_obj = data["qrcode"]
            print(f"Type: {type(qr_obj)}")
            print(f"Value: {qr_obj}")
            
            if isinstance(qr_obj, dict):
                print(f"Keys: {list(qr_obj.keys())}")
                for key in qr_obj.keys():
                    val = qr_obj[key]
                    print(f"  {key}: {type(val)} - {str(val)[:100]}")

if __name__ == "__main__":
    asyncio.run(main())
