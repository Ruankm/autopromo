# AutoPromo Cloud - Step-by-Step Validation Guide (Windows)

## PASSO 1: Verificar Ambiente

Abra PowerShell ou CMD no diretório do projeto:
```cmd
cd C:\Users\Ruan\Desktop\autopromo
```

Verifique Python instalado:
```cmd
python --version
```
Deve mostrar: Python 3.14.x ou similar

---

## PASSO 2: Subir Infraestrutura (Docker)

Inicie PostgreSQL e Redis:
```cmd
docker compose up -d postgres redis
```

Verifique se estão rodando:
```cmd
docker ps
```
Deve mostrar:
- autopromo-postgres (porta 5432)
- autopromo-redis (porta 6379)

---

## PASSO 3: Aplicar Migrations

Entre no diretório backend:
```cmd
cd backend
```

Aplique as migrations:
```cmd
python -m alembic upgrade head
```

Esperado:
```
INFO  [alembic.runtime.migration] Running upgrade 002_add_full_name -> 003_whatsapp_instances, Add whatsapp_instances table
```

Se der erro "alembic not found":
```cmd
pip install alembic
```

---

## PASSO 4: Validar Pipeline (Sem Executar)

Ainda no diretório `backend`, rode:
```cmd
python validate_pipeline.py
```

Esperado:
```
✅ ALL VALIDATIONS PASSED
```

Se der erro de imports, instale dependências:
```cmd
pip install -r requirements.txt
```

---

## PASSO 5: Criar Dados de Teste (Opcional)

```cmd
python setup_test_data.py
```

Isso cria:
- 1 usuário teste
- 2 grupos fonte
- 2 grupos destino  
- 1 tag afiliado Mercado Livre (kamarao_cdb)

---

## PASSO 6: Iniciar Backend API

```cmd
python -m uvicorn main:app --reload --port 8000
```

Esperado:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
[OK] Redis connected
```

Acesse no navegador:
- http://localhost:8000 (deve retornar JSON com "status": "running")
- http://localhost:8000/docs (Swagger UI)

**DEIXE ESTE TERMINAL ABERTO**

---

## PASSO 7: Testar Endpoints (Novo Terminal)

Abra um NOVO terminal/PowerShell.

### 7.1 Testar Health Check
```cmd
curl http://localhost:8000/health
```

Esperado:
```json
{"status":"healthy","database":"connected","redis":"connected"}
```

### 7.2 Registrar Usuário
```cmd
curl -X POST http://localhost:8000/api/v1/users/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"12345678\",\"full_name\":\"Test User\"}"
```

### 7.3 Fazer Login
```cmd
curl -X POST http://localhost:8000/api/v1/users/login ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=test@example.com&password=12345678"
```

Copie o `access_token` retornado.

### 7.4 Testar Endpoint Protegido
```cmd
curl -H "Authorization: Bearer SEU_TOKEN_AQUI" ^
  http://localhost:8000/api/v1/users/me
```

---

## PASSO 8: Iniciar Worker (Novo Terminal)

Abra um TERCEIRO terminal no diretório `backend`:

```cmd
cd C:\Users\Ruan\Desktop\autopromo\backend
python -m workers.worker
```

Esperado:
```
INFO:__main__:Worker started. Waiting for messages in queue:ingestion...
```

**DEIXE ESTE TERMINAL ABERTO**

---

## PASSO 9: Iniciar Dispatcher (Novo Terminal)

Abra um QUARTO terminal no diretório `backend`:

```cmd
cd C:\Users\Ruan\Desktop\autopromo\backend
python -m workers.dispatcher
```

Esperado:
```
INFO:__main__:Dispatcher started. Round-robin mode...
```

**DEIXE ESTE TERMINAL ABERTO**

---

## PASSO 10: Testar Pipeline Completo

### 10.1 Enviar Webhook de Teste

No terminal de testes, envie uma mensagem com link ML:

```cmd
curl -X POST http://localhost:8000/api/v1/webhook/whatsapp ^
  -H "Content-Type: application/json" ^
  -H "X-User-ID: SEU_USER_ID_AQUI" ^
  -d "{\"event\":\"messages.upsert\",\"instance\":\"test\",\"data\":{\"key\":{\"remoteJid\":\"120363999999999@g.us\",\"fromMe\":false},\"message\":{\"conversation\":\"🔥 OFERTA! https://mercadolivre.com.br/produto/MLB1234567890\"}}}"
```

### 10.2 Verificar Logs

- **Terminal Worker**: Deve mostrar processamento da mensagem
- **Terminal Dispatcher**: Deve tentar enviar para grupos destino

### 10.3 Verificar Database

```cmd
docker exec -it autopromo-postgres psql -U autopromo -d autopromo_db
```

Dentro do psql:
```sql
SELECT id, user_id, product_unique_id, monetized_url FROM offers LIMIT 5;
SELECT * FROM price_history LIMIT 5;
SELECT * FROM send_logs LIMIT 5;
```

Para sair do psql:
```
\q
```

---

## RESUMO DE TERMINAIS ABERTOS

Você deve ter 4 terminais rodando:

1. **Terminal 1 (Backend)**: `python -m uvicorn main:app --reload --port 8000`
2. **Terminal 2 (Worker)**: `python -m workers.worker`
3. **Terminal 3 (Dispatcher)**: `python -m workers.dispatcher`
4. **Terminal 4 (Testes)**: Para executar comandos curl

---

## PRÓXIMOS PASSOS

### WhatsApp Real (Evolution API)

1. Deploy Evolution API server
2. Obter URL + API Key
3. Chamar:
   ```cmd
   curl -X POST http://localhost:8000/api/v1/whatsapp/connect ^
     -H "Authorization: Bearer SEU_TOKEN" ^
     -H "Content-Type: application/json" ^
     -d "{\"api_url\":\"https://evolution.api.com\",\"api_key\":\"sua-key\"}"
   ```
4. QR Code será retornado em base64
5. Escanear com WhatsApp
6. Verificar status:
   ```cmd
   curl -H "Authorization: Bearer SEU_TOKEN" ^
     http://localhost:8000/api/v1/whatsapp/status
   ```
7. Descobrir grupos:
   ```cmd
   curl -X POST -H "Authorization: Bearer SEU_TOKEN" ^
     http://localhost:8000/api/v1/whatsapp/discover-groups
   ```

---

## TROUBLESHOOTING

### Erro: "ModuleNotFoundError: No module named 'workers'"

Solução: Certifique-se de estar no diretório `backend`:
```cmd
cd C:\Users\Ruan\Desktop\autopromo\backend
python -m workers.worker
```

### Erro: "alembic not found"

Solução:
```cmd
pip install alembic
```

### Erro: "Redis connection failed"

Solução:
1. Verifique se Redis está rodando: `docker ps`
2. Reinicie: `docker compose restart redis`

### Erro: "Database connection failed"

Solução:
1. Verifique se PostgreSQL está rodando: `docker ps`
2. Reinicie: `docker compose restart postgres
3. Verifique credenciais em `.env` ou `core/config.py`

---

## COMANDOS ÚTEIS

### Parar tudo
```cmd
REM Para Docker
docker compose down

REM Para Backend/Workers (Ctrl+C em cada terminal)
```

### Limpar Database
```cmd
docker compose down -v
docker compose up -d postgres redis
cd backend
python -m alembic upgrade head
python setup_test_data.py
```

### Ver Logs Docker
```cmd
docker compose logs -f postgres
docker compose logs -f redis
```

### Acessar PostgreSQL
```cmd
docker exec -it autopromo-postgres psql -U autopromo -d autopromo_db
```

Comandos úteis no psql:
```sql
\dt                  -- Listar tabelas
\d whatsapp_instances  -- Ver estrutura da tabela
SELECT * FROM users;   -- Ver usuários
```

---

## STATUS ESPERADO

Após seguir todos os passos:

✅ Docker: Postgres + Redis rodando  
✅ Migrations: 003_whatsapp_instances aplicada  
✅ Backend: API rodando na porta 8000  
✅ Worker: Processando queue:ingestion  
✅ Dispatcher: Processando queue:dispatch  
✅ Database: Ofertas sendo criadas  

**Sistema 100% funcional para testes locais!**
