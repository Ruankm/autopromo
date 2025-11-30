import httpx
import asyncio

async def manage_instances():
    base_url = "http://localhost:8081"
    headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Listar todas as instâncias
        print("=== Listando instâncias ===")
        try:
            response = await client.get(f"{base_url}/instance/fetchInstances", headers=headers)
            print(f"Status: {response.status_code}")
            instances = response.json()
            print(f"Instâncias encontradas: {len(instances)}")
            for inst in instances:
                print(f"  - {inst.get('instance', {}).get('instanceName', 'N/A')}")
        except Exception as e:
            print(f"Erro ao listar: {e}")
        
        # 2. Deletar a instância problemática
        instance_name = "user_bcb19b3b-acbf-47ab-b03c-73c9a7ab5839_whatsapp"
        print(f"\n=== Deletando {instance_name} ===")
        try:
            response = await client.delete(f"{base_url}/instance/delete/{instance_name}", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Erro ao deletar: {e}")
        
        # 3. Listar novamente para confirmar
        print("\n=== Listando novamente ===")
        try:
            response = await client.get(f"{base_url}/instance/fetchInstances", headers=headers)
            instances = response.json()
            print(f"Instâncias restantes: {len(instances)}")
            for inst in instances:
                print(f"  - {inst.get('instance', {}).get('instanceName', 'N/A')}")
        except Exception as e:
            print(f"Erro ao listar: {e}")

asyncio.run(manage_instances())
