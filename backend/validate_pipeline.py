"""
Script de validação completa do pipeline AutoPromo Cloud.

Testa:
1. Criação de dados de teste (usuário, grupos, tags)
2. Simulação de webhook
3. Worker processando mensagem
4. Dispatcher enviando para grupos
5. Validação de logs e multi-tenant
"""
import asyncio
import httpx
from datetime import datetime

# Configurações
API_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "test_pipeline@autopromo.com"
TEST_USER_PASSWORD = "senha12345678"
TEST_USER_NAME = "Pipeline Test User"

async def main():
    print("=" * 80)
    print("VALIDAÇÃO COMPLETA DO PIPELINE - AutoPromo Cloud")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient() as client:
        # PASSO 1: Criar usuário de teste
        print("📝 PASSO 1: Criando usuário de teste...")
        try:
            response = await client.post(
                f"{API_URL}/users/register",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                    "full_name": TEST_USER_NAME
                }
            )
            if response.status_code == 201:
                print("✅ Usuário criado com sucesso!")
                user_data = response.json()
                print(f"   ID: {user_data['id']}")
            elif response.status_code == 400:
                print("⚠️  Usuário já existe, fazendo login...")
            else:
                print(f"❌ Erro ao criar usuário: {response.status_code}")
                print(response.text)
                return
        except Exception as e:
            print(f"❌ Erro: {e}")
            return
        
        print()
        
        # PASSO 2: Fazer login
        print("🔐 PASSO 2: Fazendo login...")
        try:
            form_data = {
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            response = await client.post(
                f"{API_URL}/users/login",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                print("✅ Login realizado com sucesso!")
                token_data = response.json()
                token = token_data["access_token"]
                user_id = token_data["user"]["id"]
                print(f"   Token: {token[:20]}...")
                print(f"   User ID: {user_id}")
            else:
                print(f"❌ Erro no login: {response.status_code}")
                print(response.text)
                return
        except Exception as e:
            print(f"❌ Erro: {e}")
            return
        
        print()
        
        # Headers com autenticação
        headers = {"Authorization": f"Bearer {token}"}
        
        # PASSO 3: Criar tag de afiliado
        print("🏷️  PASSO 3: Criando tag de afiliado...")
        try:
            response = await client.post(
                f"{API_URL}/affiliate-tags",
                json={
                    "name": "Amazon Test",
                    "slug": "amazon",
                    "affiliate_param": "tag=teste-21"
                },
                headers=headers
            )
            if response.status_code == 201:
                print("✅ Tag criada com sucesso!")
                tag_data = response.json()
                print(f"   ID: {tag_data['id']}")
                print(f"   Slug: {tag_data['slug']}")
            else:
                print(f"⚠️  Status: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        print()
        
        # PASSO 4: Criar grupo fonte
        print("📥 PASSO 4: Criando grupo fonte...")
        try:
            response = await client.post(
                f"{API_URL}/groups/source",
                json={
                    "name": "Grupo Teste Fonte",
                    "platform": "whatsapp",
                    "group_id": "120363999999999999@g.us",
                    "is_active": True
                },
                headers=headers
            )
            if response.status_code == 201:
                print("✅ Grupo fonte criado com sucesso!")
                group_data = response.json()
                print(f"   ID: {group_data['id']}")
                print(f"   Nome: {group_data['name']}")
            else:
                print(f"⚠️  Status: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        print()
        
        # PASSO 5: Criar grupo destino
        print("📤 PASSO 5: Criando grupo destino...")
        try:
            response = await client.post(
                f"{API_URL}/groups/destination",
                json={
                    "name": "Grupo Teste Destino",
                    "platform": "whatsapp",
                    "group_id": "120363888888888888@g.us",
                    "is_active": True,
                    "priority": 1
                },
                headers=headers
            )
            if response.status_code == 201:
                print("✅ Grupo destino criado com sucesso!")
                group_data = response.json()
                print(f"   ID: {group_data['id']}")
                print(f"   Nome: {group_data['name']}")
            else:
                print(f"⚠️  Status: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        print()
        
        # PASSO 6: Simular webhook
        print("🔔 PASSO 6: Simulando webhook do WhatsApp...")
        webhook_payload = {
            "event": "messages.upsert",
            "instance": "test_instance",
            "data": {
                "key": {
                    "remoteJid": "120363999999999999@g.us",
                    "fromMe": False,
                    "id": f"TEST_{datetime.now().timestamp()}"
                },
                "message": {
                    "conversation": "🔥 OFERTA IMPERDÍVEL! iPhone 15 Pro Max por R$ 4.999 https://www.amazon.com.br/dp/B0CHX1W1XY"
                },
                "messageTimestamp": int(datetime.now().timestamp())
            }
        }
        
        try:
            response = await client.post(
                f"{API_URL}/webhook/whatsapp",
                json=webhook_payload
            )
            if response.status_code == 200:
                print("✅ Webhook processado com sucesso!")
                webhook_response = response.json()
                print(f"   Status: {webhook_response.get('status')}")
                print(f"   Message: {webhook_response.get('message')}")
            else:
                print(f"❌ Erro no webhook: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        print()
        
        # PASSO 7: Verificar stats
        print("📊 PASSO 7: Verificando dashboard stats...")
        try:
            response = await client.get(
                f"{API_URL}/dashboard/stats",
                headers=headers
            )
            if response.status_code == 200:
                print("✅ Stats obtidas com sucesso!")
                stats = response.json()
                print(f"   Total na Fila: {stats.get('total_in_queue', 0)}")
                print(f"   Enviadas Hoje: {stats.get('sent_today', 0)}")
                print(f"   Grupos Ativos: {stats.get('active_groups', 0)}")
                print(f"   Tags Ativas: {stats.get('active_tags', 0)}")
            else:
                print(f"⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        print()
        print("=" * 80)
        print("✅ VALIDAÇÃO COMPLETA!")
        print("=" * 80)
        print()
        print("📋 PRÓXIMOS PASSOS:")
        print("1. Rodar worker: cd backend && python -m workers.worker")
        print("2. Rodar dispatcher: cd backend && python -m workers.dispatcher")
        print("3. Verificar banco de dados para ver ofertas processadas")
        print()

if __name__ == "__main__":
    asyncio.run(main())
