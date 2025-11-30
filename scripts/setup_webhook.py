# -*- coding: utf-8 -*-
"""Configura webhook da Evolution API."""
import os

try:
    import requests
except ImportError:
    print("ERRO: Modulo requests nao encontrado")
    print("Instale: pip install requests")
    exit(1)

# Configuracao
EVOLUTION_URL = "http://localhost:8081"
API_KEY = "f708f2fc-471f-4511-83c3-701229e766d5"
INSTANCE = "ruan"  # CORRIGIDO: era Worker01
BACKEND_URL = "http://host.docker.internal:8000/api/v1/webhook/whatsapp"

def main():
    print("=" * 70)
    print("CONFIGURANDO WEBHOOK")
    print("=" * 70)
    print(f"Instancia: {INSTANCE}")
    print(f"Backend: {BACKEND_URL}")
    print()
    
    payload = {
        "url": BACKEND_URL,
        "enabled": True,
        "webhookByEvents": True,
        "events": ["MESSAGES_UPSERT"]
    }
    
    url = f"{EVOLUTION_URL}/webhook/set/{INSTANCE}"
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        print("OK Webhook configurado!")
        print()
        print("Proximo passo:")
        print("  cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"ERRO: {e}")
        print()
        print("Verifique:")
        print("  - Evolution API rodando? http://localhost:8081")
        print("  - Instancia 'ruan' existe?")

if __name__ == "__main__":
    main()
