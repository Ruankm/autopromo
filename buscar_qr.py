import requests
import json

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5"}

print("Listando todas as instancias e buscando QR Code...")

# Fetch all instances
response = requests.get(f"{base_url}/instance/fetchInstances", headers=headers, params={"fetchQrCode": "true"})
print(f"Status: {response.status_code}")

data = response.json()
print(f"\nTotal de instancias: {len(data)}")

for inst in data:
    print(f"\n{'='*60}")
    print(f"Instancia: {inst.get('instance', {}).get('instanceName', 'N/A')}")
    print(f"Status: {inst.get('instance', {}).get('status', 'N/A')}")
    
    # Verificar todos os campos possiveis onde o QR pode estar
    if 'qrcode' in inst:
        qr_data = inst['qrcode']
        print(f"Campo qrcode: {qr_data}")
        
        if isinstance(qr_data, dict):
            if 'base64' in qr_data and qr_data['base64']:
                print(f"\nENCONTREI QR CODE!")
                with open(f"QR_{inst['instance']['instanceName']}.txt", "w") as f:
                    f.write(qr_data['base64'])
                print(f"Salvo em QR_{inst['instance']['instanceName']}.txt")
            elif 'code' in qr_data and qr_data['code']:
                print(f"\nENcontrei QR CODE no campo 'code'!")
                with open(f"QR_{inst['instance']['instanceName']}.txt", "w") as f:
                    f.write(qr_data['code'])
                print(f"Salvo!")
            else:
                print(f"QR Code vazio: {qr_data}")

print(f"\n{'='*60}")
print("\nSe nenhum QR Code foi encontrado, a Evolution API pode estar com problema.")
print("Verifique os logs: docker logs evolution_api")
