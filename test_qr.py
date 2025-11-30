import requests
import json

# Testar endpoint de QR Code
url = "http://localhost:8081/instance/connect/user_bcb19b3b-acbf-47ab-b03c-73c9a7ab5839_whatsapp"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5"}

print("Testando endpoint de QR Code...")
print(f"URL: {url}")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"\nStatus: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Salvar QR Code se existir
    data = response.json()
    if "base64" in data:
        print("\nQR CODE ENCONTRADO NO CAMPO 'base64'!")
        with open("qrcode.txt", "w") as f:
            f.write(data["base64"])
        print("QR Code salvo em qrcode.txt")
    elif "code" in data:
        print("\nQR CODE ENCONTRADO NO CAMPO 'code'!")
        with open("qrcode.txt", "w") as f:
            f.write(data["code"])
        print("QR Code salvo em qrcode.txt")
    elif "qrcode" in data:
        print(f"\nCampo 'qrcode': {data['qrcode']}")
    else:
        print(f"\nCampos disponiveis: {list(data.keys())}")
        
except requests.exceptions.RequestException as e:
    print(f"\nErro: {e}")
