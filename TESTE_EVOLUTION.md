# 🔧 Evolution API v2.2.0 - Guia de Teste Manual

## ✅ Status da Configuração

**Versão:** Evolution API v2.2.0  
**Modo:** File Storage (MINIMALISTA - sem DB, sem Redis)  
**Porta:** http://localhost:8081  
**API Key:** `f708f2fc-471f-4511-83c3-701229e766d5`

---

## 🌐 Acessar Evolution Manager

1. **Abrir navegador:** http://localhost:8081/manager
2. **Inserir API Key:** `f708f2fc-471f-4511-83c3-701229e766d5`

---

## 📝 Criar Instância (Teste Manual)

### Via Manager (Interface Web):

1. Acesse: http://localhost:8081/manager
2. Clique em **"Create Instance"**
3. Preencha:
   - **Instance Name:** `Worker01`
   - **Integration:** `WHATSAPP-BAILEYS`
   - **QR Code:** ✅ `true`
   - **Number:** (deixar vazio para QR Code OU preencher `5531998722744` para Pairing Code)

4. Clique em **"Create"**
5. **AGUARDE** o QR Code aparecer OU o Pairing Code

---

## 📋 Comandos Úteis

### Ver logs em tempo real:
```powershell
docker logs evolution_api -f
```

### Verificar status:
```powershell
docker ps
```

### Reiniciar se necessário:
```powershell
docker restart evolution_api
```

### Parar e limpar TUDO:
```powershell
docker compose -f docker-compose.evolution.yml down -v
```

---

## 🧪 Teste via API (curl)

### 1. Criar Instância com QR Code:
```powershell
curl.exe -X POST "http://localhost:8081/instance/create" `
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5" `
  -H "Content-Type: application/json" `
  -d '{
    "instanceName": "Worker01",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

### 2. Buscar QR Code:
```powershell
curl.exe -X GET "http://localhost:8081/instance/connect/Worker01" `
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5"
```

### 3. Verificar Status:
```powershell
curl.exe -X GET "http://localhost:8081/instance/connectionState/Worker01" `
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5"
```

### 4. Deletar Instância:
```powershell
curl.exe -X DELETE "http://localhost:8081/instance/delete/Worker01" `
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5"
```

---

## ⚠️ Troubleshooting

### Se QR Code não aparecer:

1. **Verificar logs:**
   ```powershell
   docker logs evolution_api --tail 50
   ```

2. **Procurar por erros:**
   - `redis disconnected` = Redis tentando conectar (não deveria acontecer)
   - `database error` = Database tentando conectar (não deveria acontecer)
   - `Baileys version` = OK (está inicializando)

3. **Se houver loop de reconexão:**
   - Verificar se `DATABASE_ENABLED=false` e `CACHE_REDIS_ENABLED=false` no `.env.evolution`
   - Reiniciar: `docker restart evolution_api`

---

## 📊 Resultado Esperado

✅ **SUCESSO:** QR Code aparece no Manager OU via API  
✅ **SUCESSO:** Pairing Code gerado (se usar número)  
❌ **FALHA:** Resposta `{"count": 0}` persistente  
❌ **FALHA:** Loop de reconexão nos logs

---

**Próximo Passo:** Teste AGORA pelo Manager e me diga o resultado! 🚀
