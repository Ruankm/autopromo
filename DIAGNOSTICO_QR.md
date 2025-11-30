# 🔍 Diagnóstico: QR Code Não Aparece (TODAS as Versões)

## 📸 Screenshot do Problema

![QR Code não renderiza](C:/Users/Ruan/.gemini/antigravity/brain/6e33604f-2459-448f-9931-035fe4c4aee2/uploaded_image_1764270640972.png)

**Sintoma:** Tela mostra "Scan the QR code with your WhatsApp Web" mas QR não renderiza.

---

## 🧠 Raciocínio Lógico

Se o problema acontece em **TODAS** as versões testadas:
- ❌ v2.2.3
- ❌ v2.1.0
- ❌ v1.7.4
- ❌ v2.2.0

**Conclusão:** NÃO é bug de versão específica = é problema **AMBIENTAL**.

---

## 🔎 Possíveis Causas Comuns

### 1️⃣ **DNS/Network no Container**
**Sintoma:** Baileys não consegue resolver `web.whatsapp.com`  
**Test:**
```bash
docker exec evolution_api ping web.whatsapp.com
docker exec evolution_api nslookup web.whatsapp.com
```

**Solução:** Configurar DNS fixo no Docker (1.1.1.1, 8.8.8.8)

---

### 2️⃣ **Firewall/Antivírus Bloqueando**
**Sintoma:** Conexão WebSocket bloqueada  
**Test:**
```bash
docker exec evolution_api curl -v https://web.whatsapp.com
```

**Solução:** Adicionar exceção no firewall/antivírus

---

### 3️⃣ **CONFIG_SESSION_PHONE_VERSION Incorreta**
**Sintoma:** WhatsApp rejeita a versão  
**Valor Atual:** `2.3000.1023204200`

**Test:** Verificar versão real do WhatsApp Web:
1. Abrir https://web.whatsapp.com no navegador
2. F12 > Console > digitar: `window.Debug.VERSION`

**Solução:** Usar versão EXATA do WhatsApp Web atual

---

### 4️⃣ **Porta/Network Mode**
**Sintoma:** Container não acessa internet corretamente  
**Config Atual:** Bridge network

**Test:**
```bash
docker exec evolution_api curl -I https://google.com
```

**Solução:** Testar com `network_mode: host`

---

### 5️⃣ **Problema de Permissões/Volumes**
**Sintoma:** Baileys não consegue salvar sessão  
**Test:**
```bash
docker exec evolution_api ls -la /evolution/instances
docker exec evolution_api ls -la /evolution/store
```

**Solução:** Verificar permissões dos volumes

---

### 6️⃣ **Proxy/VPN Interferindo**
**Sintoma:** Tráfego HTTPS interceptado  
**Test:** Desabilitar VPN/Proxy temporariamente

**Solução:** Configurar `NO_PROXY` ou desativar proxy

---

## 🔧 Plano de Ação Diagnóstico

### PASSO 1: Verificar Conectividade WhatsApp
```bash
docker exec evolution_api ping -c 4 web.whatsapp.com
docker exec evolution_api curl -I https://web.whatsapp.com
```

### PASSO 2: Verificar DNS
```bash
docker exec evolution_api cat /etc/resolv.conf
docker exec evolution_api nslookup web.whatsapp.com
```

### PASSO 3: Verificar Logs Durante Criação
```bash
docker logs evolution_api -f
# (Criar instância no Manager e observar)
```

### PASSO 4: Testar com DNS Fixo
```yaml
# docker-compose.evolution.yml
evolution-api:
  dns:
    - 1.1.1.1
    - 8.8.8.8
```

### PASSO 5: Testar com Host Network
```yaml
evolution-api:
  network_mode: host
  # Remove ports: e networks:
```

---

## 📊 Checklist de Diagnóstico

- [ ] Container consegue pingar `web.whatsapp.com`?
- [ ] Container consegue curl `https://web.whatsapp.com`?
- [ ] DNS está configurado corretamente?
- [ ] Firewall do Windows está bloqueando?
- [ ] Antivírus está bloqueando?
- [ ] Há proxy/VPN ativo?
- [ ] CONFIG_SESSION_PHONE_VERSION está correta?
- [ ] Volumes têm permissões corretas?
- [ ] Logs mostram erro específico?

---

## 🎯 Próximos Passos

**EXECUTAR AGORA:**
1. Verificar logs durante criação de instância
2. Testar conectividade WhatsApp do container
3. Verificar DNS
4. Aplicar correção baseada no resultado

**Aguardando resultado dos testes...**
