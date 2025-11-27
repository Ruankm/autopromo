"""
Quick test script to check Evolution API and get QR Code
"""
import httpx
import asyncio
import json

API_URL = "http://localhost:8081"
API_KEY = "f708f2fc-471f-4511-83c3-701229e766d5"

async def main():
    headers = {"apikey": API_KEY}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. List instances
        print("1. Fetching instances...")
        resp = await client.get(f"{API_URL}/instance/fetchInstances", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        print()
        
        # 2. Delete instance if exists
        print("2. Deleting AutoPromo_Main if exists...")
        resp = await client.delete(f"{API_URL}/instance/delete/AutoPromo_Main", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        print()
        
        # 3. Create new instance
        print("3. Creating new instance...")
        payload = {
            "instanceName": "AutoPromo_Main",
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        resp = await client.post(f"{API_URL}/instance/create", json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Full response: {json.dumps(data, indent=2)[:500]}")
        print()
        
        # 4. Try to get QR Code
        print("4. Getting QR Code...")
        resp = await client.get(f"{API_URL}/instance/connect/AutoPromo_Main", headers=headers)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        
        if "base64" in data:
            print("✓ Found QR Code in 'base64' key!")
        elif "qrcode" in data:
            print(f"✓ Found 'qrcode' key, type: {type(data['qrcode'])}")
            if isinstance(data['qrcode'], dict):
                print(f"  QR Code keys: {list(data['qrcode'].keys())}")
        else:
            print(f"✗ QR Code not found. Available keys: {list(data.keys())}")
            print(f"Full response: {json.dumps(data, indent=2)[:500]}")

if __name__ == "__main__":
    asyncio.run(main())
