# WhatsApp Integration - Quick Test Guide

## 🚀 Setup (5 minutos)

### 1. Evolution API
```bash
cd C:\Users\Ruan\Desktop\autopromo
docker compose -f docker-compose.evolution.yml up -d
```

Verificar:
```bash
curl http://localhost:8081
# Deve retornar: {"status":200,"message":"Welcome to Evolution API..."}
```

### 2. Backend
```bash
cd backend
uvicorn main:app --reload
```

### 3. Frontend
```bash
cd frontend
npm run dev
```

## ✅ Teste Completo

### Passo 1: Registrar Usuário
- http://localhost:3000/register
- Email: `teste@test.com`
- Senha: `Test1234!`

### Passo 2: Conectar WhatsApp
- http://localhost:3000/dashboard/whatsapp
- Clicar "Conectar via QR Code"
- QR Code aparece
- Escanear com WhatsApp
- Status muda para "Conectado"

### Passo 3: Descobrir Grupos
- Clicar "Descobrir Grupos"
- Lista de grupos aparece
- Ir para /dashboard/groups

### Passo 4: Cadastrar Grupo
- Selecionar grupo fonte
- Ativar
- Configurar grupo destino

### Passo 5: Testar Webhook (Opcional)
- Enviar mensagem para grupo fonte
- Verificar logs do worker
- Verificar mensagem no grupo destino

## 🔍 Troubleshooting

**QR Code não aparece:**
- Verificar logs: `docker compose -f docker-compose.evolution.yml logs -f`
- Acessar Evolution Manager: http://localhost:8081/manager
- API Key: `f708f2fc-471f-4511-83c3-701229e766d5`

**Erro 400 ao descobrir grupos:**
- WhatsApp não está conectado
- Verificar status: GET /api/v1/whatsapp/status

**Evolution API não responde:**
- Verificar porta 8081 livre
- Reiniciar: `docker compose -f docker-compose.evolution.yml restart`

## 📊 Endpoints para Testar (Postman)

```bash
# Status
GET http://localhost:8000/api/v1/whatsapp/status
Authorization: Bearer <token>

# Descobrir Grupos
POST http://localhost:8000/api/v1/whatsapp/discover-groups
Authorization: Bearer <token>

# Desconectar
DELETE http://localhost:8000/api/v1/whatsapp/disconnect
Authorization: Bearer <token>
```

## ✅ Sucesso
- [ ] Evolution API rodando
- [ ] QR Code gerado
- [ ] WhatsApp conectado
- [ ] Grupos descobertos
- [ ] Grupos cadastrados no sistema
