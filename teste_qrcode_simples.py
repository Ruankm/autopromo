import requests
import json
import time

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5", "Content-Type": "application/json"}

print("="*60)
print("TESTE: QR CODE SIMPLES (conforme Postman)")
print("="*60)

# Deletar instância antiga
try:
    requests.delete(f"{base_url}/instance/delete/QRCODE_TEST", headers=headers)
except:
    pass

time.sleep(2)

# Criar instância EXATAMENTE como no Postman
print("\nCriando instancia SIMPLES com qrcode=true...")
instance_name = "QRCODE_TEST"

payload = {
    "instanceName": instance_name,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

response = requests.post(f"{base_url}/instance/create", json=payload, headers=headers)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2)}")

if response.status_code == 201:
    print("\nInstancia criada!")
    
    # Verificar se já tem QR code na resposta
    if "qrcode" in data and "code" in data["qrcode"]:
        print(f"\nQR Code JA NA RESPOSTA: {data['qrcode']}")
    elif "qrcode" in data and "base64" in data["qrcode"]:
        print(f"\nQR Code base64 JA NA RESPOSTA: {len(data['qrcode']['base64'])} chars")
else:
    print("\nErro ao criar")
    exit(1)

print("\nAguardando 5 segundos...")
time.sleep(5)

# Buscar QR Code
print("\nBuscando QR Code via /instance/connect...")

for tentativa in range(1, 8):
    print(f"\nTentativa {tentativa}/7...")
    
    response = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if "code" in data and data.get("code"):
        print(f"\n*** QR CODE ENCONTRADO! ***")
        with open("QRCODE_SUCCESS.txt", "w") as f:
            f.write(data["code"])
        print("Salvo em QRCODE_SUCCESS.txt")
        print("Use: https://qr.io/pt/ para visualizar")
        break
    elif "base64" in data and data.get("base64"):
        print(f"\n*** QR CODE BASE64 ENCONTRADO! ***")
        with open("QRCODE_SUCCESS_BASE64.txt", "w") as f:
            f.write(data["base64"])
        print("Salvo em QRCode_SUCCESS_BASE64.txt")
        break
    elif "pairingCode" in data and data.get("pairingCode"):
        print(f"\n*** PAIRING CODE: {data['pairingCode']} ***")
        break
    elif data.get("count", 0) > 0:
        print(f"Count: {data['count']} - QR Code pode estar gerando...")
    else:
        print("Nenhum codigo ainda...")
    
    if tentativa < 7:
        time.sleep(4)

# Verificar status da instância
print("\nVerificando status da instancia...")
response = requests.get(f"{base_url}/instance/connectionState/{instance_name}", headers=headers)
print(f"Connection state: {json.dumps(response.json(), indent=2)}")

print("\n" + "="*60)
print("TESTE CONCLUIDO")
print("="*60)
