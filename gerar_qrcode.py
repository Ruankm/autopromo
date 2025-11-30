import requests
import json
import time

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5"}

# 1. Deletar instância antiga
instance_name = "TESTE_FINAL"
print(f"1. Deletando instancia {instance_name}...")
try:
    requests.delete(f"{base_url}/instance/delete/{instance_name}", headers=headers)
    print("   Deletada!")
except:
    print("   Nao existia")

time.sleep(2)

# 2. Criar nova instância
print(f"\n2. Criando instancia {instance_name}...")
payload = {
    "instanceName": instance_name,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS",
    "number": "5531998722744"
}

response = requests.post(f"{base_url}/instance/create", json=payload, headers=headers)
print(f"   Status: {response.status_code}")
print(f"   Resposta: {json.dumps(response.json(), indent=2)}")

time.sleep(5)

# 3. Buscar QR Code
print(f"\n3. Buscando QR Code...")
for tentativa in range(1, 6):
    print(f"   Tentativa {tentativa}/5...")
    response = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
    data = response.json()
    
    if "base64" in data and data["base64"]:
        print(f"\n   QR CODE ENCONTRADO!")
        print(f"   Tamanho: {len(data['base64'])} caracteres")
        with open("QRCODE_FINAL.txt", "w") as f:
            f.write(data["base64"])
        print(f"\n   QR Code salvo em QRCODE_FINAL.txt")
        print(f"\n   ABRA O ARQUIVO E COPIE O CONTEUDO")
        print(f"   Depois cole em https://qr.io/pt/ PARA VER O QR CODE!")
        break
    elif "code" in data and data["code"]:
        print(f"\n   QR CODE ENCONTRADO NO CAMPO 'code'!")
        with open("QRCODE_FINAL.txt", "w") as f:
            f.write(data["code"])
        print(f"\n   QR Code salvo em QRCODE_FINAL.txt")
        break
    else:
        print(f"   Resposta: {data}")
        time.sleep(3)
else:
    print("\n   FALHOU! QR Code nao foi gerado.")
