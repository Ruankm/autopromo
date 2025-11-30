import requests
import json

base_url = "http://localhost:8081"
headers = {"apikey": "f708f2fc-471f-4511-83c3-701229e766d5"}

response = requests.get(f"{base_url}/instance/fetchInstances", headers=headers, params={"fetchQrCode": "true"})
print(json.dumps(response.json(), indent=2))
