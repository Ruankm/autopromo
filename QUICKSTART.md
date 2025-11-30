# AutoPromo - Quick Start Guide

**Última atualização:** 2025-11-30

---

## 🚀 COMO RODAR LOCALMENTE (Windows)

### Pré-requisitos
- [x] Python 3.11+ instalado
- [x] PostgreSQL rodando
- [x] Redis rodando
- [x] Chromium instalado (Playwright)

---

### PASSO 1: Iniciar Serviços (Docker)

```powershell
# Terminal 1: PostgreSQL + Redis
cd c:\Users\Ruan\Desktop\autopromo
docker-compose up postgres redis

# Aguarde mensagens:
# - postgres ready to accept connections
# - redis ready to accept connections
```

---

### PASSO 2: Backend (FastAPI)

**Opção A: Usando script (FÁCIL)**
```powershell
# Duplo-clique no arquivo:
start_backend.bat

# Ou no terminal:
.\start_backend.bat
```

**Opção B: Manual**
```powershell
# Terminal 2: Backend
cd c:\Users\Ruan\Desktop\autopromo\backend

# Ativar venv (se existir)
.\venv\Scripts\activate

# Verificar instalação
python -m pip list | findstr fastapi

# Iniciar servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verificar:**
- Backend rodando: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

### PASSO 3: Worker (Playwright)

**Opção A: Usando script (FÁCIL)**
```powershell
# Duplo-clique no arquivo:
start_worker.bat

# Ou no terminal:
.\start_worker.bat
```

**Opção B: Manual**
```powershell
# Terminal 3: Worker
cd c:\Users\Ruan\Desktop\autopromo\backend

# Ativar venv (se existir)
.\venv\Scripts\activate

# Iniciar worker
python -m workers.whatsapp_worker
```

**Verificar logs:**
```
=== Starting WhatsApp Worker ===
✓ Redis connected
✓ Playwright gateway started
=== Worker Ready ===
Starting main loop...
```

---

### PASSO 4: Testar API

**Criar Conexão:**
```powershell
# PowerShell
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer YOUR_TOKEN_HERE"
}

$body = @{
    nickname = "Meu Número Teste"
    source_groups = @(
        @{ name = "Escorrega Promoções" }
    )
    destination_groups = @(
        @{ name = "Família Teste" }
    )
    min_interval_per_group = 360
    min_interval_global = 30
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/connections" -Method POST -Headers $headers -Body $body
```

**Listar Conexões:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/connections" -Headers $headers
```

**Obter QR Code:**
```powershell
$qr = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/connections/{CONNECTION_ID}/qr" -Headers $headers
echo $qr.qr_code  # Base64 do QR
```

---

## 🧪 TESTE END-TO-END

### 1. Preparação
- [ ] Backend rodando (porta 8000)
- [ ] Worker rodando (monitorando)
- [ ] PostgreSQL + Redis ativos

### 2. Criar Conexão
```powershell
# Use o comando acima ou acesse:
http://localhost:8000/docs
# POST /api/v1/connections
```

### 3. Escanear QR Code
- Obter QR via API: `/connections/{id}/qr`
- Decodificar base64
- Escanear no WhatsApp
- Aguardar status = "connected"

### 4. Configurar Grupos
```powershell
# PATCH /api/v1/connections/{id}
$body = @{
    source_groups = @(
        @{ name = "Nome Exato Grupo Fonte" }
    )
    destination_groups = @(
        @{ name = "Nome Exato Grupo Destino" }
    )
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/connections/{ID}" -Method PATCH -Headers $headers -Body $body
```

### 5. Enviar Mensagem Teste
- Abrir WhatsApp manualmente
- Enviar no grupo FONTE:
```
🔥 TESTE DE OFERTA

Notebook Gamer
R$ 3.499,90

https://amazon.com.br/dp/B08XYZ123
```

### 6. Verificar Processamento

**Logs do Worker:**
```
[INFO] Found 1 new message(s) for Meu Número Teste
[INFO] Queued message for Família Teste
[INFO] ✓ Sent to Família Teste (preview: True, 2847ms)
```

**Database:**
```sql
-- MessageLog
SELECT * FROM message_logs ORDER BY processed_at DESC LIMIT 1;

-- OfferLog
SELECT * FROM offer_logs ORDER BY created_at DESC LIMIT 1;
```

**Grupo Destino:**
- Verificar mensagem chegou
- Link foi monetizado?
- Preview foi gerado?

### 7. Testar Deduplicação
- Enviar MESMA mensagem novamente
- Worker deve ignorar (log: "Message already processed")
- Grupo destino NÃO recebe duplicata

---

## ⚠️ TROUBLESHOOTING

### Backend não sobe
```powershell
# Verificar porta 8000 livre
netstat -ano | findstr :8000

# Se ocupada, matar processo:
taskkill /PID <PID> /F

# Verificar dependências
cd backend
python -m pip install -r requirements.txt
```

### Worker não conecta
```powershell
# Verificar Redis
docker ps | findstr redis

# Se não rodando:
docker-compose up -d redis

# Verificar Playwright
python -m playwright install chromium
```

### Banco de dados erro
```powershell
# Verificar PostgreSQL
docker ps | findstr postgres

# Rodar migrations
cd backend
python -m alembic upgrade head
```

### QR Code não gera
- Verificar worker está rodando
- Verificar Playwright inicializou
- Verificar whatsapp_sessions/ tem permissões
- Tentar remover `whatsapp_sessions/{connection_id}/` e tentar novamente

---

## 📊 CHECKLIST DE SUCESSO

### Backend
- [ ] Porta 8000 disponível
- [ ] /health retorna 200
- [ ] /docs carrega
- [ ] Redis conectado
- [ ] PostgreSQL conectado

### Worker
- [ ] Playwright inicializou
- [ ] Redis conectado
- [ ] Main loop rodando
- [ ] Sem erros nos logs

### End-to-End
- [ ] Conexão criada
- [ ] QR Code obtido
- [ ] WhatsApp conectado (status = "connected")
- [ ] Grupos configurados
- [ ] Mensagem detectada
- [ ] Preview gerado
- [ ] MessageLog salvou
- [ ] OfferLog salvou
- [ ] Sem duplicata

---

## 🎯 PRÓXIMOS PASSOS

Quando tudo acima funcionar:
1. Frontend integração
2. Testes com 2-3 conexões
3. Deploy Docker
4. Primeiro cliente real

---

**Dúvidas?** Verifique logs em:
- Backend: Terminal 2
- Worker: Terminal 3
- PostgreSQL: `docker logs autopromo-postgres`
- Redis: `docker logs autopromo-redis`
