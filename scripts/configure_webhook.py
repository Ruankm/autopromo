#!/usr/bin/env python3
"""
Configura webhook da Evolution API para chamar o backend AutoPromo.

Uso:
    python scripts/configure_webhook.py
"""
import requests
import os
    """Configura webhook na Evolution API."""
    
    print("=" * 80)
    print(" CONFIGURANDO WEBHOOK DA EVOLUTION API")
    print("=" * 80)
    print()
    print(f"Instância: {INSTANCE_NAME}")
    print(f"URL Backend: {BACKEND_WEBHOOK_URL}")
    print(f"Eventos: MESSAGES_UPSERT")
    print()
    
    # Payload do webhook
    payload = {
        "url": BACKEND_WEBHOOK_URL,
        "enabled": True,
        "webhookByEvents": True,
        "events": ["MESSAGES_UPSERT"]
    }
    
    url = f"{EVOLUTION_BASE_URL}/webhook/set/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        print("✅ WEBHOOK CONFIGURADO COM SUCESSO!")
        print()
        print("🎯 Agora mensagens de grupos do WhatsApp serão:")
        print("   1. Recebidas pela Evolution API")
        print("   2. Enviadas via webhook para o backend")
        print("   3. Processadas pelo mirror_service")
        print("   4. Monetizadas com sua tag de afiliado")
        print("   5. Repostadas nos grupos destino")
        print()
        print("=" * 80)
        print(" TESTE AGORA:")
        print("=" * 80)
        print()
        print("1. Certifique-se que o backend está rodando:")
        print("   cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print()
        print("2. Envie uma mensagem com link no grupo 'Escorrega o Preço'")
        print()
        print("3. Veja a mágica acontecer no grupo 'Autopromo'! 🚀")
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO: {e}")
        print()
        print("Verifique:")
        print("  - Evolution API está rodando (http://localhost:8081)")
        print("  - API Key está correta no .env.evolution")
        print("  - Instância 'Worker01' existe e está conectada")


if __name__ == "__main__":
    configure_webhook()
