# 🚀 INÍCIO RÁPIDO - AutoPromo Backend

## ⚡ Comandos Rápidos (Windows)

### Iniciar Backend
```bash
# OPÇÃO 1: Double-click no arquivo
start_backend.bat

# OPÇÃO 2: No terminal
cd C:\Users\Ruan\Desktop\autopromo\backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testar Mirror
```bash
# OPÇÃO 1: Double-click no arquivo
test_mirror.bat

# OPÇÃO 2: No terminal
cd C:\Users\Ruan\Desktop\autopromo
python scripts\test_mirror.py
```

---

## 📋 Passo a Passo Completo

### 1. Abrir Terminal no Projeto
```bash
cd C:\Users\Ruan\Desktop\autopromo
```

### 2. Iniciar Backend (Terminal 1)
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Aguardar ver:**
```
INFO: Uvicorn running on http://0.0.0.0:8000
[OK] Redis connected
INFO: Application startup complete.
```

### 3. Testar Mirror (Terminal 2 - NOVO)
```bash
cd C:\Users\Ruan\Desktop\autopromo
python scripts\test_mirror.py
```

**Resultado esperado:**
```
OK Webhook recebido pelo backend!
```

**E no Terminal 1 (backend):**
```
INFO: 🎯 Mirror Service: Processing message...
INFO: Monetized (amazon): ...
INFO: ✅ Sent to ...
```

---

## ❌ Erros Comuns

### "Could not import module 'main'"
**Causa:** Tentou rodar `uvicorn main:app` FORA da pasta `backend/`

**Solução:**
```bash
# SEMPRE rodar de dentro de backend/
cd C:\Users\Ruan\Desktop\autopromo\backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### "Backend nao esta rodando"
**Causa:** Backend não está iniciado ou parou

**Solução:**
```bash
# Iniciar backend primeiro
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### "Redis connection failed"
**Causa:** Redis não está rodando

**Solução:**
```bash
# Verificar Docker
docker ps | findstr redis

# Iniciar se necessário
docker start autopromo-redis
```

---

## 🎯 Workflow Recomendado

### Para Desenvolvimento:
1. **Terminal 1:** Backend rodando
2. **Terminal 2:** Testes manuais
3. **Terminal 3:** Logs da Evolution API (opcional)

### Para Teste Real:
1. Iniciar backend: `start_backend.bat`
2. Aguardar mensagem no grupo "Escorrega o Preço"
3. Verificar logs no terminal
4. Confirmar mensagem no grupo "Autopromo"

---

## 📁 Estrutura de Pastas

```
C:\Users\Ruan\Desktop\autopromo\
├── backend/
│   ├── main.py           ← IMPORTANTE: uvicorn roda AQUI
│   ├── api/
│   ├── services/
│   └── models/
├── scripts/
│   ├── test_mirror.py    ← Testes
│   ├── setup_db.py
│   └── setup_webhook.ps1
├── start_backend.bat      ← Helper para iniciar
└── test_mirror.bat        ← Helper para testar
```

**REGRA:** Para rodar o backend, **SEMPRE** estar dentro de `backend/`!
