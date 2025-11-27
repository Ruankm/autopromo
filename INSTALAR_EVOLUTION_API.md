# 🚀 GUIA COMPLETO - Instalar Evolution API

## ✅ O QUE VOCÊ PRECISA

Você **NÃO TEM** Evolution API instalada. Vamos instalar agora!

---

## 📦 OPÇÃO 1: Instalar via Docker (MAIS FÁCIL)

### Passo 1: Editar o arquivo de configuração

Abra o arquivo que acabei de criar:
```
C:\Users\Ruan\Desktop\autopromo\docker-compose.evolution.yml
```

**MUDE ESTA LINHA**:
```yaml
AUTHENTICATION_API_KEY: SUA_SENHA_SECRETA_AQUI_12345
```

**Para algo como**:
```yaml
AUTHENTICATION_API_KEY: autopromo_evolution_key_2024
```

⚠️ **IMPORTANTE**: Guarde esta senha! Você vai precisar dela!

---

### Passo 2: Criar a network Docker

```cmd
docker network create autopromo_network
```

Se der erro "network already exists", tudo bem! Continue.

---

### Passo 3: Subir a Evolution API

```cmd
cd C:\Users\Ruan\Desktop\autopromo
docker compose -f docker-compose.evolution.yml up -d
```

**Aguarde ~30 segundos** e teste:

```cmd
curl http://localhost:8080
```

Deve retornar algo como:
```json
{"status":"ok","version":"2.x.x"}
```

---

## 🔑 SUAS CREDENCIAIS

Depois de subir a Evolution API, suas credenciais serão:

### URL Base:
```
http://localhost:8080
```

### API Key:
```
autopromo_evolution_key_2024
```
(ou a senha que você colocou no arquivo)

---

## 🎯 TESTAR NO AUTOPROMO

1. Acesse: `http://localhost:3000/dashboard/whatsapp`
2. Clique em "Conectar WhatsApp"
3. Quando pedir:
   - **URL**: `http://localhost:8080`
   - **API Key**: `autopromo_evolution_key_2024`
4. Escaneie o QR Code com seu WhatsApp
5. Aguarde conexão
6. Clique em "Descobrir Grupos"

---

## 📦 OPÇÃO 2: Usar Evolution API Online (Mais Avançado)

Se você quiser usar um servidor online:

1. **Deploy no Render/Railway/Heroku**
2. Configure as variáveis de ambiente
3. Obtenha a URL pública (ex: `https://sua-api.onrender.com`)
4. Use essa URL no AutoPromo

---

## ⚠️ TROUBLESHOOTING

### Erro: "network autopromo_network not found"
```cmd
docker network create autopromo_network
```

### Erro: "port 8080 already in use"
Mude a porta no `docker-compose.evolution.yml`:
```yaml
ports:
  - "8081:8080"  # Mudou de 8080 para 8081
```

E use `http://localhost:8081` como URL

### Verificar se está rodando:
```cmd
docker ps
```

Deve mostrar `evolution_api` na lista.

---

## 🎯 PRÓXIMOS PASSOS

1. **Edite** `docker-compose.evolution.yml` (mude a senha)
2. **Crie** a network: `docker network create autopromo_network`
3. **Suba** a API: `docker compose -f docker-compose.evolution.yml up -d`
4. **Teste**: `curl http://localhost:8080`
5. **Conecte** no AutoPromo: `http://localhost:3000/dashboard/whatsapp`

---

**Comece editando o arquivo agora!** 🚀
