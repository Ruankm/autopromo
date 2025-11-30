# -*- coding: utf-8 -*-
"""
Script de teste do mirror com monetização REAL.

Simula mensagem com link Amazon real.
"""
import asyncio
import httpx
import sys

BACKEND_URL = "http://localhost:8000"

async def test_mirror_with_amazon():
    """Testa mirror com link Amazon REAL."""
    
    print("=" * 70)
    print("TESTE DO MIRROR - Com Link Amazon REAL")
    print("=" * 70)
    print()
    
    # URLs reais para testar
    test_cases = [
        {
            "name": "Link completo Amazon",
            "url": "https://www.amazon.com.br/Echo-Dot-5%C2%AA-gera%C3%A7%C3%A3o-Cor-Preta/dp/B09B8VGCR8?pd_rd_w=KkTAE"
        },
        {
            "name": "Link curto amzn.to",
            "url": "https://amzn.to/48Fpex6"
        },
        {
            "name": "Link simples /dp/",
            "url": "https://www.amazon.com.br/dp/B09B8VGCR8"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- TESTE {i}: {test['name']} ---")
        print(f"URL original: {test['url']}")
        
        # Payload simulando webhook
        payload = {
            "event": "messages.upsert",
            "instance": "ruan",
            "data": {
                "key": {
                    "remoteJid": "120363042106955836@g.us",
                    "fromMe": False
                },
                "message": {
                    "conversation": f"Echo Dot 5ª Geração por R$ 303,95\n{test['url']}"
                },
                "messageTimestamp": 1700000000
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BACKEND_URL}/api/v1/webhook/whatsapp",
                    json=payload,
                    timeout=10
                )
                
                print(f"Status: {resp.status_code}")
                result = resp.json()
                print(f"Response: {result}")
                
                if resp.status_code == 200:
                    if result.get("monetized", 0) > 0:
                        print("✅ URL monetizada com sucesso!")
                    else:
                        print("⚠️ URL não foi monetizada")
                else:
                    print("❌ Erro no backend")
                    
        except httpx.ConnectError:
            print("❌ Backend não está rodando!")
            print("Inicie: cd backend && python -m uvicorn main:app --reload")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 70)
    print("TESTE COMPLETO")
    print("=" * 70)
    print("\nVerifique:")
    print("1. Logs do backend mostram 'Monetized (amazon)'")
    print("2. Mensagem enviada no WhatsApp contém '?tag=autopromo0b-20'")

if __name__ == "__main__":
    asyncio.run(test_mirror_with_amazon())
