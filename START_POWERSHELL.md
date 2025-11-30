# AutoPromo - Comandos PowerShell para Rodar Localmente

**IMPORTANTE:** Você está usando PowerShell, não CMD!

---

## 🚨 PRIMEIRO: Iniciar Docker Desktop

**Docker Desktop NÃO está rodando!**

Erro encontrado:
```
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

**SOLUÇÃO:**
1. Abrir Docker Desktop manualmente
2. Aguardar inicialização completa
3. Voltar aqui e continuar

---

## ✅ COMANDOS CORRETOS (PowerShell)

### Opção A: Script Automático (RECOMENDADO)

```powershell
# Executar script que faz tudo
cd C:\Users\Ruan\Desktop\autopromo
.\start_all.ps1
```

Se der erro de execução de script:
```powershell
# Permitir execução de scripts (uma vez só)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Depois executar novamente
.\start_all.ps1
```

---

### Opção B: Manual (Passo a Passo)

#### Terminal 1: PostgreSQL + Redis

```powershell
cd C:\Users\Ruan\Desktop\autopromo

# Iniciar serviços
docker-compose up -d postgres redis

# Verificar status
docker-compose ps

# Deve mostrar:
# postgres  running
# redis     running
```

#### Terminal 2: Backend (NOVO TERMINAL)

```powershell
cd C:\Users\Ruan\Desktop\autopromo

# IMPORTANTE: usar .\ antes do .bat no PowerShell
.\start_backend.bat
```

Deve aparecer:
```
[1/3] Activating virtual environment...
[2/3] Checking environment...
Python 3.14.0
[3/3] Starting FastAPI server...
Server will be available at: http://localhost:8000
...
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

#### Terminal 3: Worker (OUTRO NOVO TERMINAL)

```powershell
cd C:\Users\Ruan\Desktop\autopromo

# IMPORTANTE: usar .\ antes do .bat no PowerShell
.\start_worker.bat
```

Deve aparecer:
```
[1/3] Activating virtual environment...
[2/3] Checking environment...
Python 3.14.0
[3/3] Starting WhatsApp Worker...
...
=== Starting WhatsApp Worker ===
✓ Redis connected
✓ Playwright gateway started
=== Worker Ready ===
```

---

## 🔍 VERIFICAÇÕES

### 1. Docker Desktop
```powershell
# Verificar se está rodando
docker ps

# Se der erro, Docker Desktop não está iniciado
```

### 2. Serviços de Banco
```powershell
# Verificar containers
docker-compose ps

# Ver logs PostgreSQL
docker-compose logs postgres

# Ver logs Redis
docker-compose logs redis
```

### 3. Backend
```powershell
# Testar endpoint
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Deve retornar:
# status   : healthy
# database : connected
# redis    : connected
```

### 4. Worker
```powershell
# Ver logs do terminal 3
# Deve mostrar:
# "Starting main loop..."
# Sem erros
```

---

## ❌ TROUBLESHOOTING

### Erro: "Docker Desktop not running"

**Solução:**
1. Abrir Docker Desktop
2. Aguardar logo aparecer no canto inferior direito da tela
3. Tentar novamente

### Erro: "start_backend.bat não reconhecido"

**Causa:** PowerShell precisa de `.\` antes de arquivos locais

**Solução:**
```powershell
# ❌ ERRADO (CMD)
start_backend.bat

# ✅ CORRETO (PowerShell)
.\start_backend.bat
```

### Erro: "porta 8000 já em uso"

**Verificar:**
```powershell
netstat -ano | findstr :8000
```

**Matar processo:**
```powershell
# Pegar PID da última coluna
taskkill /PID <NUMERO_DO_PID> /F
```

### Erro: "Redis connection failed"

**Verificar Redis:**
```powershell
docker-compose ps redis

# Se não rodando:
docker-compose up -d redis
```

### Erro: "PostgreSQL connection failed"

**Verificar PostgreSQL:**
```powershell
docker-compose ps postgres

# Se não rodando:
docker-compose up -d postgres
```

---

## 📋 CHECKLIST

Marque conforme conseguir:

- [ ] Docker Desktop aberto e inicializado
- [ ] `docker ps` funciona sem erro
- [ ] PostgreSQL container rodando
- [ ] Redis container rodando
- [ ] Backend iniciou (porta 8000)
- [ ] `http://localhost:8000/health` retorna healthy
- [ ] Worker iniciou sem erros
- [ ] Worker mostra "Worker Ready"

---

## 🎯 PRÓXIMO PASSO

Quando TODOS os checkboxes acima estiverem marcados:

1. Testar criar conexão via API
2. Obter QR Code
3. Escanear no WhatsApp

**Me avise quando conseguir rodar todos os 3 (Docker + Backend + Worker)!**

---

## 📝 COMANDOS RESUMIDOS (COPIAR/COLAR)

```powershell
# PASSO 1: Iniciar Docker Desktop manualmente

# PASSO 2: Terminal 1 - Database
cd C:\Users\Ruan\Desktop\autopromo
docker-compose up -d postgres redis
docker-compose ps

# PASSO 3: Terminal 2 - Backend (NOVO TERMINAL)
cd C:\Users\Ruan\Desktop\autopromo
.\start_backend.bat

# PASSO 4: Terminal 3 - Worker (NOVO TERMINAL)
cd C:\Users\Ruan\Desktop\autopromo
.\start_worker.bat

# VERIFICAR: Terminal 4 - Health Check
Invoke-RestMethod -Uri "http://localhost:8000/health"
```
