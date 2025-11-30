import requests
import json
import time

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5", "Content-Type": "application/json"}

instance_name = "TESTE_FINAL"

print(f"Forçando conexão da instância {instance_name}...")

# Tentar forçar a conexão GET /instance/connect
response = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Aguardar 5 segundos
print("\nAguardando 5 segundos...")
time.sleep(5)

# Buscar novamente
response = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
print(f"\nSegunda tentativa:")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2)}")

# Tentar extrair QR Code de qualquer campo
if "code" in data and data["code"]:
    print(f"\n>>> QR CODE STRING ENCONTRADO!")
    print(f"Tamanho: {len(data['code'])} caracteres")
    with open("QRCODE_STRING.txt", "w") as f:
        f.write(data["code"])
    print("Salvo em QRCODE_STRING.txt")
elif "base64" in data:
    print(f"\n>>> QR CODE BASE64 ENCONTRADO!")
    with open("QRCODE_BASE64.txt", "w") as f:
        f.write(data["base64"])
    print("Salvo em QRCODE_BASE64.txt")
elif "pairingCode" in data:
    print(f"\n>>> PAIRING CODE ENCONTRADO: {data['pairingCode']}")
    print("Digite este código no WhatsApp do celular!")
else:
    print("\nNenhum QR Code encontrado.")
    print("A Evolution API pode estar com problema de compatibilidade.")
