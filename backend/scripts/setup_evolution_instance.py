"""
CORRECTED: Evolution API - Instance Setup & QR Code Generator

The QR Code comes in the CREATE response, not the CONNECT endpoint!
"""
import os
import sys
import base64
import httpx
import asyncio
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Try to load from .env
try:
    from dotenv import load_dotenv
    load_dotenv(backend_path / ".env")
    load_dotenv(backend_path.parent / ".env.evolution")
except ImportError:
    pass

# Configuration
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_BASE_URL", "http://localhost:8081")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_TOKEN", os.getenv("AUTHENTICATION_API_KEY"))
INSTANCE_NAME = f"AutoPromo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def print_header(text: str):
    print(f"\n{'=' * 80}")
    print(f"{text.center(80)}")
    print(f"{'=' * 80}\n")


async def test_connection() -> bool:
    """Test if Evolution API is reachable"""
    print(f"[1/4] Testing connection to {EVOLUTION_API_URL}...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(EVOLUTION_API_URL)
            
            if response.status_code == 200:
                print(f"      SUCCESS - Evolution API v{response.json().get('version', 'unknown')}")
                return True
            else:
                print(f"      ERROR - Status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"      ERROR - {e}")
        print("      Make sure Evolution API is running: docker compose up -d evolution-api")
        return False


async def create_instance_with_qr() -> tuple[dict | None, str | None]:
    """Create instance and extract QR Code from response"""
    print(f"[2/4] Creating instance '{INSTANCE_NAME}'...")
    
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "instanceName": INSTANCE_NAME,
        "qrcode": True,  # CRITICAL: Request QR Code in creation
        "integration": "WHATSAPP-BAILEYS"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 201:
                print("      SUCCESS - Instance created!")
                data = response.json()
                
                # Extract QR Code from CREATE response
                qr_code = None
                
                if "qrcode" in data:
                    qr_obj = data["qrcode"]
                    if isinstance(qr_obj, dict):
                        # Try different possible keys
                        qr_code = (qr_obj.get("base64") or 
                                  qr_obj.get("code") or 
                                  qr_obj.get("pairingCode"))
                    elif isinstance(qr_obj, str):
                        qr_code = qr_obj
                
                return data, qr_code
            else:
                print(f"      ERROR - Status {response.status_code}")
                print(f"      Response: {response.text}")
                return None, None
                
    except Exception as e:
        print(f"      ERROR - {e}")
        return None, None


def save_qr_code(qr_base64: str) -> Path | None:
    """Save QR Code as PNG file"""
    print("[3/4] Saving QR Code...")
    
    try:
        # Remove data URI prefix if present
        if "," in qr_base64:
            qr_base64 = qr_base64.split(",")[1]
        
        # Decode base64
        qr_bytes = base64.b64decode(qr_base64)
        
        # Save to file
        output_path = Path("qrcode_whatsapp.png")
        output_path.write_bytes(qr_bytes)
        
        print(f"      SUCCESS - Saved to: {output_path.absolute()}")
        return output_path
        
    except Exception as e:
        print(f"      ERROR - {e}")
        return None


async def wait_for_connection(instance_name: str, timeout: int = 120) -> bool:
    """Wait for WhatsApp connection (optional)"""
    print(f"[4/4] Waiting for WhatsApp connection (timeout: {timeout}s)...")
    print("      Scan the QR Code now!")
    
    headers = {"apikey": EVOLUTION_API_KEY}
    start_time = asyncio.get_event_loop().time()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                response = await client.get(
                    f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    state = data.get("state", "unknown")
                    
                    if state == "open":
                        print("      SUCCESS - WhatsApp connected!")
                        return True
                    elif state == "close":
                        print(f"      Waiting... (status: {state})", end="\r")
                
            except:
                pass
            
            await asyncio.sleep(3)
    
    print("\n      TIMEOUT - QR Code expired or not scanned")
    print("      You can still scan it later or create a new instance")
    return False


async def main():
    """Main execution flow"""
    print_header("Evolution API - WhatsApp QR Code Generator")
    
    print(f"Configuration:")
    print(f"  API URL: {EVOLUTION_API_URL}")
    print(f"  Instance: {INSTANCE_NAME}")
    print()
    
    # Validate configuration
    if not EVOLUTION_API_KEY:
        print("ERROR: EVOLUTION_API_TOKEN not set!")
        print("Set it in backend/.env or .env.evolution")
        return 1
    
    # Step 1: Test connection
    if not await test_connection():
        return 1
    
    # Step 2: Create instance and get QR Code
    instance_data, qr_code = await create_instance_with_qr()
    
    if not instance_data:
        return 1
    
    if not qr_code:
        print("      WARNING - QR Code not found in response")
        print(f"      Response keys: {list(instance_data.keys())}")
        print("      Instance created but QR Code unavailable")
        print("      Try accessing Evolution API dashboard or check logs")
        return 1
    
    # Step 3: Save QR Code
    qr_path = save_qr_code(qr_code)
    if not qr_path:
        return 1
    
    # Step 4: Wait for connection (optional, with timeout)
    print()
    print("=" * 80)
    print("QR CODE READY!".center(80))
    print("=" * 80)
    print()
    print(f"1. Open the QR Code image: {qr_path.absolute()}")
    print("2. Open WhatsApp on your phone")
    print("3. Go to: Settings -> Linked Devices -> Link a Device")
    print("4. Scan the QR Code")
    print()
    print("Waiting for connection (or press Ctrl+C to skip)...")
    print()
    
    try:
        await wait_for_connection(INSTANCE_NAME, timeout=60)
    except KeyboardInterrupt:
        print("\n\nSkipped waiting. You can scan the QR Code anytime!")
    
    # Final instructions
    print()
    print_header("Setup Complete!")
    print(f"Instance Name: {INSTANCE_NAME}")
    print(f"QR Code: {qr_path.absolute()}")
    print()
    print("Next steps:")
    print("  - If not connected yet, scan the QR Code")
    print("  - Access AutoPromo dashboard: http://localhost:3000/dashboard/whatsapp")
    print(f"  - Check status: http://localhost:8081/instance/connectionState/{INSTANCE_NAME}")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
