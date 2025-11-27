# 🔧 SOLUÇÃO TEMPORÁRIA - Redis Desabilitado

## ⚠️ Problema Identificado

Evolution API não consegue conectar ao Redis, causando erro:
```
ERROR [Redis] redis disconnected
```

Isso impede a geração do QR Code.

## ✅ Solução Aplicada

**Desabilitei Redis temporariamente** em `.env.evolution`:

```bash
REDIS_ENABLED=false
```

**Por que isso funciona**:
- Redis é opcional para Evolution API
- QR Code pode ser gerado sem Redis
- Funcionalidades afetadas: cache de mensagens (não crítico para teste)

## 🚀 TESTE AGORA

```bash
cd C:\Users\Ruan\Desktop\autopromo\backend
python scripts\setup_evolution_instance.py
```

**Deve funcionar agora!**

## 🔄 Para Re-habilitar Redis Depois

Quando o QR Code funcionar, podemos investigar o problema do Redis.

Possíveis causas:
1. Versão incompatível da biblioteca Redis
2. Formato da URI incorreto
3. Timeout de conexão

**Mas por enquanto, não precisamos de Redis para conectar o WhatsApp!**

---

**Status**: Evolution API reiniciado sem Redis  
**Próximo passo**: Executar script de QR Code
