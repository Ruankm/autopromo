"""
Quick test - create instance with different name and get QR Code
"""
import httpx
import asyncio
import json
import base64
from pathlib import Path

API_URL = "http://localhost:8081"
API_KEY = "f708f2fc-471f-4511-83c3-701229e766d5"
INSTANCE_NAME = "AutoPromo_Test_001"

async def main():
    headers = {"apikey": API_KEY}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create new instance
        print(f"Creating instance: {INSTANCE_NAME}")
        payload = {
            "instanceName": INSTANCE_NAME,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        resp = await client.post(f"{API_URL}/instance/create", json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 201:
            print(f"Error: {resp.text}")
            return
        
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Wait a bit for QR generation
        print("Waiting 3 seconds for QR Code generation...")
        await asyncio.sleep(3)
        
        # Get QR Code
        print("Fetching QR Code...")
        resp = await client.get(f"{API_URL}/instance/connect/{INSTANCE_NAME}", headers=headers)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            return
        
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Try to find QR Code
        qr_code = None
        
        if "base64" in data:
            qr_code = data["base64"]
            print("Found QR in 'base64' key")
        elif "qrcode" in data:
            qr_obj = data["qrcode"]
            if isinstance(qr_obj, dict):
                qr_code = qr_obj.get("base64") or qr_obj.get("code")
                print(f"Found QR in 'qrcode' dict, keys: {list(qr_obj.keys())}")
            elif isinstance(qr_obj, str):
                qr_code = qr_obj
                print("Found QR in 'qrcode' string")
        elif "code" in data:
            qr_code = data["code"]
            print("Found QR in 'code' key")
        
        if qr_code:
            # Remove data URI prefix if present
            if "," in qr_code:
                qr_code = qr_code.split(",")[1]
            
            # Save QR Code
            qr_bytes = base64.b64decode(qr_code)
            output_path = Path("qrcode_test.png")
            output_path.write_bytes(qr_bytes)
            print(f"QR Code saved to: {output_path.absolute()}")
            print("\nScan this QR Code with WhatsApp!")
        else:
            print("QR Code not found in response")
            print(f"Full response: {json.dumps(data, indent=2)[:1000]}")

if __name__ == "__main__":
    asyncio.run(main())
