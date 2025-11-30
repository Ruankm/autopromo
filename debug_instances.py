import httpx
import asyncio
import json

async def debug_instances():
    base_url = "http://localhost:8081"
    headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Listar com resposta completa
        print("=== Resposta completa da API ===")
        try:
            response = await client.get(f"{base_url}/instance/fetchInstances", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Erro: {e}")

asyncio.run(debug_instances())
