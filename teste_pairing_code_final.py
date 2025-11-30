import requests
import json
import time

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5", "Content-Type": "application/json"}

print("="*60)
print("TESTE: AUTENTICACAO POR NUMERO (Pairing Code)")
print("="*60)

# Criar instância SEM QR Code, COM número
print("\nCriando instancia COM NUMERO para Pairing Code...")
instance_name = "PAIRING_TEST"
numero_brasil = "5531998722744"

payload = {
    "instanceName": instance_name,
    "qrcode": False,
    "number": numero_brasil,
    "integration": "WHATSAPP-BAILEYS"
}

try:
    response = requests.post(f"{base_url}/instance/create", json=payload, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 201:
        print("\nInstancia criada com SUCESSO!")
    else:
        print(f"\nErro ao criar instancia")
        exit(1)
except Exception as e:
    print(f"Erro: {e}")
    exit(1)

print("\nAguardando 3 segundos...")
time.sleep(3)

# Tentar conectar COM número para gerar Pairing Code
print("\nConectando com NUMERO para gerar Pairing Code...")

for tentativa in range(1, 6):
    print(f"\nTentativa {tentativa}/5...")
    
    try:
        response = requests.get(
            f"{base_url}/instance/connect/{instance_name}",
            headers=headers,
            params={"number": numero_brasil},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Verificar se tem pairingCode
        if "pairingCode" in data and data["pairingCode"]:
            print("\n" + "="*60)
            print(f"PAIRING CODE GERADO: {data['pairingCode']}")
            print("="*60)
            print("\nABRA O WHATSAPP NO SEU CELULAR:")
            print("1. Va em 'Aparelhos Conectados'")
            print("2. Clique em 'Vincular com numero de telefone'")
            print(f"3. Digite o codigo: {data['pairingCode']}")
            print("\nPRONTO! O WhatsApp vai conectar automaticamente!")
            break
        elif "code" in data and data["code"]:
            print(f"\nQR Code gerado: {len(data['code'])} caracteres")
            with open("QRCODE_FINAL.txt", "w") as f:
                f.write(data["code"])
            print("Salvo em QRCODE_FINAL.txt")
            break
        elif "base64" in data and data["base64"]:
            print(f"\nQR Code base64 gerado: {len(data['base64'])} caracteres")
            with open("QRCODE_FINAL.txt", "w") as f:
                f.write(data["base64"])
            print("Salvo em QRCODE_FINAL.txt")
            break
        else:
            print(f"Nenhum codigo gerado. Campos: {list(data.keys())}")
            
    except Exception as e:
        print(f"Erro: {e}")
    
    if tentativa < 5:
        print("Aguardando 3s...")
        time.sleep(3)

print("\n" + "="*60)
print("TESTE CONCLUIDO")
print("="*60)
