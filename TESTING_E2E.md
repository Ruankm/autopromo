# 🧪 TESTE END-TO-END - WhatsApp Connection & Group Discovery

## ✅ Estado Atual

**Worker Fixed:** `main_loop()` e `cleanup_cycle()` adicionados  
**Compilação:** ✅ Sem erros  
**Fluxo:** QR → Login → Discovery

---

## 🎯 O Que Funciona AGORA

### 1. Worker Cycles Rodando:
- `login_cycle()` - Gera QR e detecta login
- `monitor_cycle()` - Monitora mensagens  
- `send_cycle()` - Envia mensagens  
- `cleanup_cycle()` - Limpa filas antigas  
- `redis_command_listener()` - Escuta comandos

### 2. Login Flow:
```
pending → qr_needed → connecting → connected
```

### 3. Group Discovery:
- Via Redis command: `DISCOVER_GROUPS`
- Scrape completo com scroll
- Logs em tempo real: `[DISCOVERY] <nickname> → <group_name>`
- Salva no banco (UPSERT)

---

## 📋 Teste Passo-a-Passo

### Preparação:

```powershell
cd C:\Users\Ruan\Desktop\autopromo

# 1. Rebuild containers
docker-compose build backend worker

# 2. Subir serviços
docker-compose up -d

# 3. Ver logs do worker
docker-compose logs worker -f
```

### Teste 1: QR Generation

**1. Criar conexão via API:**

```powershell
# Login primeiro
$login = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/users/login" `
    -Body "username=test@autopromo.com&password=senha123" `
    -ContentType "application/x-www-form-urlencoded"

$token = $login.access_token
$headers = @{"Authorization" = "Bearer $token"}

# Criar conexão
$conn = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/connections" -Headers $headers -Body (@{
    nickname = "Test End-to-End"
    min_interval_per_group = 60
    min_interval_global = 30
} | ConvertTo-Json) -ContentType "application/json"

Write-Host "Connection ID: $($conn.id)"
```

**2. Ver logs do Worker:**

```
Esperar log:
[INFO] 📱 Opening WhatsApp Web for Test End-to-End
[INFO] ✓ WhatsApp Web opened for Test End-to-End
[INFO] ✓ QR code generated for Test End-to-End
```

**3. Pegar QR Code:**

```powershell
# Aguardar ~5-10s após criar conexão
$qr = Invoke-RestMethod -Method GET -Uri "http://localhost:8000/api/v1/connections/$($conn.id)/qr" -Headers $headers

# Exibir QR (cria HTML)
$html = @"
<!DOCTYPE html>
<html><head><title>QR - Test E2E</title>
<style>body{display:flex;justify-content:center;align-items:center;min-height:100vh;background:#0f172a}
img{max-width:400px;border:4px solid #06b6d4;border-radius:10px}</style></head>
<body><img src='data:image/png;base64,$($qr.qr_code)'/></body></html>
"@
$html | Set-Content "C:\Users\Ruan\Desktop\qr_test_e2e.html"
Start-Process "C:\Users\Ruan\Desktop\qr_test_e2e.html"
```

**4. Escanear QR no celular WhatsApp**

**5. Ver logs de conexão:**

```
Esperar logs:
[INFO] 📲 QR scanned for Test End-to-End, connecting...
[INFO] ✅ Test End-to-End fully connected!
```

### Teste 2: Group Discovery

**Método 1: Via Redis (Backend dispara)**

```powershell
# Disparar discovery via API
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/connections/$($conn.id)/discover-groups" -Headers $headers
```

**Método 2: Via Redis Manual**

```powershell
# Publicar comando Redis diretamente
docker-compose exec redis redis-cli PUBLISH whatsapp:commands '{"type":"DISCOVER_GROUPS","connection_id":"'$($conn.id)'"}'
```

**Logs esperados:**

```
[INFO] Received command: DISCOVER_GROUPS
[INFO] Scrolling to load all groups...
[INFO] Found 45 chat items, extracting groups...
[INFO] [DISCOVERY] Test End-to-End → Grupo Ofertas Amazon
[INFO] [DISCOVERY] Test End-to-End → Família ❤️
[INFO] [DISCOVERY] Test End-to-End → Promoções Tech
[INFO] [DISCOVERY] Test End-to-End → Amigos da Faculdade
...
[INFO] ✓ Discovered and saved 15 groups for connection Test End-to-End
```

### Teste 3: Verificar Banco

```powershell
# Listar grupos descobertos
$groups = Invoke-RestMethod -Method GET -Uri "http://localhost:8000/api/v1/connections/$($conn.id)/groups" -Headers $headers

Write-Host "Grupos descobertos: $($groups.Count)"
$groups | ForEach-Object { Write-Host " - $($_.display_name)" }
```

---

## 🔍 Troubleshooting

### Worker não inicia:
```powershell
docker-compose logs worker --tail=50
# Ver se há erros de import ou sintaxe
```

### QR não gera:
```
- Verificar se status mudou para qr_needed
- Ver logs: "Opening WhatsApp Web"
- Aguardar ~10-20s (Playwright lento)
```

### Discovery não roda:
```
- Verificar se conexão está "connected"
- Ver logs do Redis command
- Testar comando manual (Método 2 acima)
```

### Logs não aparecem:
```powershell
# Verificar nível de log
docker-compose exec worker env | grep LOG

# Ver logs em tempo real
docker-compose logs worker -f | Select-String "DISCOVERY|QR|connected"
```

---

## ✅ Critério de Sucesso

**Teste passa quando ver:**

1. ✅ QR gerado e salvo no banco
2. ✅ Log: `✅ <nickname> fully connected!`
3. ✅ Logs: `[DISCOVERY] <nickname> → <grupo1>`, `<grupo2>`, etc.
4. ✅ API retorna lista de grupos descobertos

**EM ORDEM**, sem erros intermediários.

---

## 📊 Logs Completos Esperados

```
[INFO] === Starting WhatsApp Worker ===
[INFO] ✓ Redis connected
[INFO] ✓ Playwright gateway started
[INFO] ✓ Redis subscriber ready
[INFO] === Worker Ready ===
[INFO] Starting main loop...
[INFO] Redis command listener started

# Criar conexão
[INFO] 📝 NEW_CONNECTION: Test End-to-End (<uuid>)
[INFO] login_cycle() will process this connection

# Login cycle processa
[INFO] 📱 Opening WhatsApp Web for Test End-to-End
[INFO] ✓ WhatsApp Web opened for Test End-to-End
[INFO] ✓ QR code generated for Test End-to-End

# Escanear QR
[INFO] 📲 QR scanned for Test End-to-End, connecting...
[INFO] ✅ Test End-to-End fully connected!

# Discovery
[INFO] Received command: DISCOVER_GROUPS
[INFO] Scrolling to load all groups...
[INFO] Found 45 chat items, extracting groups...
[INFO] [DISCOVERY] Test End-to-End → Grupo 1
[INFO] [DISCOVERY] Test End-to-End → Grupo 2
...
[INFO] ✓ Discovered and saved 15 groups for connection Test End-to-End
```

---

## 🚀 Próximos Passos (se tudo funcionar)

1. ✅ Validar que sessão persiste após restart
2. ✅ Testar múltiplas conexões simultâneas
3. ✅ Implementar auto-discovery periódico (opcional)
4. ✅ Adicionar Group Discovery ao painel frontend

---

**Última atualização:** 01/12/2024 21:15  
**Commit:** `b06ccfd` - Critical fixes + discovery logging
