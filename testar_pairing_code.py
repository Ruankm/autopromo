import requests
import json
import time

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5", "Content-Type": "application/json"}

print("="*60)
print("TESTE: AUTENTICAÇÃO POR NÚMERO (Pairing Code)")
print("="*60)

# Deletar instâncias antigas
print("\n1. Limpando instâncias antigas...")
try:
    response = requests.get(f"{base_url}/instance/fetchInstances", headers=headers, timeout=5)
    if response.status_code == 200:
        instances = response.json()
        for inst in instances:
            name = inst.get("name")
            if name:
                print(f"   Deletando: {name}")
                requests.delete(f"{base_url}/instance/delete/{name}", headers=headers)
except Exception as e:
    print(f"   API ainda não está pronta: {e}")

time.sleep(2)

# Criar instância SEM QR Code, COM número
print("\n2. Criando instância COM NÚMERO para Pairing Code...")
instance_name = "PAIRING_TEST"
numero_brasil = "5531998722744"  # Seu número

payload = {
    "instanceName": instance_name,
    "qrcode": False,  # DESABILITAR QR CODE
    "number": numero_brasil,  # SEU NÚMERO
    "integration": "WHATSAPP-BAILEYS"
}

try:
    response = requests.post(f"{base_url}/instance/create", json=payload, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 201:
        print("\n✅ Instância criada com SUCESSO!")
    else:
        print(f"\n❌ Erro ao criar instância")
        exit(1)
except Exception as e:
    print(f"❌ Erro: {e}")
    exit(1)

print("\nAguardando 3 segundos...")
time.sleep(3)

# Tentar conectar COM número para gerar Pairing Code
print("\n3. Conectando com NÚMERO para gerar Pairing Code...")

for tentativa in range(1, 6):
    print(f"\n   Tentativa {tentativa}/5...")
    
    try:
        # Endpoint /instance/connect com query param ?number=
        response = requests.get(
            f"{base_url}/instance/connect/{instance_name}",
            headers=headers,
            params={"number": numero_brasil},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        
        # Verificar se tem pairingCode
        if "pairingCode" in data and data["pairingCode"]:
            print(f"\n{'*'*60}")
            print(f"🎉 PAIRING CODE GERADO!")
            print(f"{'*'*60}")
            print(f"\nCÓDIGO: {data['pairingCode']}")
            print(f"\nABRA O WHATSAPP NO SEU CELULAR:")
            print(f"1. Vá em 'Aparelhos Conectados'")
            print(f"2. Clique em 'Vincular com número de telefone'")
            print(f"3. Digite o código: {data['pairingCode']}")
            print(f"\nPRONTO! O WhatsApp vai conectar automaticamente!")
            break
        elif "code" in data:
            print(f"\n   QR Code gerado (formato 'code'): {len(data['code'])} caracteres")
            with open("QRCODE_ALTERNATIVO.txt", "w") as f:
                f.write(data["code"])
            print("   Salvo em QRCODE_ALTERNATIVO.txt")
            break
        else:
            print(f"   Nenhum código gerado ainda. Campos: {list(data.keys())}")
            
    except Exception as e:
        print(f"   Erro: {e}")
    
    if tentativa < 5:
        print("   Aguardando 3s...")
        time.sleep(3)

print(f"\n{'='*60}")
print("TESTE CONCLUÍDO")
print(f"{'='*60}")
