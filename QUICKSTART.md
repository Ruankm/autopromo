# 🚀 QUICKSTART - AutoPromo Cloud

## Passo 1: Subir o Banco de Dados (Docker)

Abra um terminal **na raiz do projeto** (`c:\Users\Ruan\Desktop\autopromo`):

```powershell
docker compose up -d
```

Aguarde alguns segundos. Verifique se está tudo rodando:

```powershell
docker compose ps
```

Você deve ver:
- `autopromo-postgres` (UP)
- `autopromo-redis` (UP)

---

## Passo 2: Criar as Tabelas no Banco

Abra um terminal em `backend/`:

```powershell
cd backend
python -m alembic upgrade head
```

Se tudo der certo, verá: `Running upgrade -> 001_initial, Initial migration - all tables`

---

## Passo 3: Rodar o Backend

No mesmo terminal `backend/`:

```powershell
python -m uvicorn main:app --reload --port 8000
```

Aguarde até ver: `✅ Redis connected` e `Application startup complete`

Teste: Abra http://localhost:8000 no navegador. Deve mostrar:
```json
{"message": "AutoPromo Cloud API", "version": "0.1.0", "status": "running"}
```

---

## Passo 4: Rodar o Frontend

Abra **outro terminal** em `frontend/`:

```powershell
cd frontend
npm run dev
```

Aguarde até ver: `Ready in ...s`

Acesse: http://localhost:3002 (ou a porta que aparecer)

---

## Passo 5: Testar o Registro

1. Clique em **"Criar Conta"**
2. Preencha:
   - Email: `teste@autopromo.com`
   - Senha: `password123`
3. Clique em "Criar Conta"

**Se funcionar**: Você será redirecionado para `/dashboard`

**Se der erro**: Abra o terminal do backend e veja o log de erro.

---

## Comandos Úteis

### Parar tudo:
```powershell
# Terminal backend
Ctrl+C

# Terminal frontend
Ctrl+C

# Parar containers
docker compose down
```

### Ver logs do banco:
```powershell
docker compose logs postgres
```

### Limpar e recomeçar (⚠️ perde dados):
```powershell
docker compose down -v
docker compose up -d
cd backend
python -m alembic upgrade head
```
