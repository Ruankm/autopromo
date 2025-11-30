import requests
import json
import time

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5", "Content-Type": "application/json"}

print("="*60)
print("LIMPANDO INSTANCIAS ANTIGAS")
print("="*60)

# Listar todas as instâncias
response = requests.get(f"{base_url}/instance/fetchInstances", headers=headers)
instances = response.json()

for inst in instances:
    name = inst.get("name", "N/A")
    if name != "N/A":
        print(f"Deletando: {name}")
        try:
            requests.delete(f"{base_url}/instance/delete/{name}", headers=headers)
        except:
            pass

time.sleep(2)

print("\n" + "="*60)
print("CRIANDO NOVA INSTANCIA")
print("="*60)

# Criar instância conforme documentação Postman
instance_name = "AUTOPROMO_WHATSAPP"
payload = {
    "instanceName": instance_name,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

response = requests.post(f"{base_url}/instance/create", json=payload, headers=headers)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2)}")

print("\nAguardando 5 segundos para API processar...")
time.sleep(5)

print("\n" + "="*60)
print("BUSCANDO QR CODE VIA GET /instance/connect")
print("="*60)

# Tentar buscar QR Code (conforme documentação)
for tentativa in range(1, 6):
    print(f"\nTentativa {tentativa}/5...")
    
    response = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
    print(f"Status: {response.status_code}")
    
    qr_data = response.json()
    print(f"Response: {json.dumps(qr_data, indent=2)}")
    
    # Verificar todos os campos possíveis
    if "base64" in qr_data and qr_data["base64"]:
        print(f"\n{'*'*60}")
        print("QR CODE BASE64 ENCONTRADO!")
        print(f"{'*'*60}")
        with open("QRCODE_SUCESSO.txt", "w") as f:
            f.write(qr_data["base64"])
        print("\nQR Code salvo em: QRCODE_SUCESSO.txt")
        print("COPIE O CONTEUDO e cole em: https://qr.io/pt/")
        break
    elif "code" in qr_data and qr_data["code"]:
        print(f"\n{'*'*60}")
        print("QR CODE STRING ENCONTRADO!")
        print(f"{'*'*60}")
        with open("QRCODE_SUCESSO.txt", "w") as f:
            f.write(qr_data["code"])
        print("\nQR Code salvo em: QRCODE_SUCESSO.txt")
        break
    elif "pairingCode" in qr_data and qr_data["pairingCode"]:
        print(f"\n{'*'*60}")
        print(f"PAIRING CODE: {qr_data['pairingCode']}")
        print(f"{'*'*60}")
        print("\nDigite este codigo no WhatsApp do celular:")
        print("WhatsApp > Aparelhos Conectados > Vincular com numero de telefone")
        break
    
    if tentativa < 5:
        print("QR Code ainda nao esta pronto, aguardando 3s...")
        time.sleep(3)

print("\n" + "="*60)
print("TESTE CONCLUIDO")
print("="*60)
