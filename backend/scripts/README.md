# Debug Scripts - README

## 🔍 debug_whatsapp_connection.py

**Propósito:** Testar isoladamente ConnectionPool + status_checker sem mexer no Worker

### Como Usar:

1. **Listar conexões existentes:**
```bash
docker-compose exec backend python -c "
from core.database import AsyncSessionLocal
from models.whatsapp_connection import WhatsAppConnection
from sqlalchemy import select
import asyncio

async def list_connections():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WhatsAppConnection))
        print('\nConexões disponíveis:')
        print('-' * 60)
        for c in result.scalars().all():
            print(f'{c.id} | {c.nickname:20} | {c.status}')
        print('-' * 60)

asyncio.run(list_connections())
"
```

2. **Rodar debug com uma conexão:**
```bash
docker-compose exec backend python scripts/debug_whatsapp_connection.py <UUID>
```

### O Que Ele Faz:

✅ Inicializa ConnectionPool  
✅ Abre WhatsApp Web (persistent context)  
✅ Detecta status via DOM (`qr_needed`, `connecting`, `connected`, `error`)  
✅ Mantém aba aberta por 5 minutos  
✅ Re-checa status a cada 10s  
✅ Atualiza banco se status mudar  
✅ Fecha gracefully

### Cenários de Teste:

**Cenário 1: QR Needed → Connected**
```bash
# 1. Rode o script
docker-compose exec backend python scripts/debug_whatsapp_connection.py <UUID>

# 2. Output esperado:
# [DEBUG] DOM Status: 📱 QR (qr_needed)
# [INFO] Mantendo aba aberta por 5 minutos...

# 3. Escaneie QR no celular

# 4. Após ~10-20s você verá:
# [2/30] Status mudou: qr_needed → connected ✅
# [✓] Status atualizado no banco!
```

**Cenário 2: Já Conectado**
```bash
# Se sessão persistiu, você verá direto:
# [DEBUG] DOM Status: ✅ Conectado (connected)
```

**Cenário 3: Erro / Seletores Quebrados**
```bash
# [DEBUG] DOM Status: ❌ Erro (error)
# Indica que seletores DOM precisam ajuste
```

### Vantagens:

🎯 **Zero risco** - Não mexe no Worker  
🔍 **Isolado** - Testa apenas ConnectionPool + status_checker  
⏱️ **Rápido** - Feedback imediato  
📊 **Observável** - Logs claros do que está acontecendo  

### Próximos Passos:

Quando este script funcionar (qr_needed → connected):

1. ✅ **Validado:** ConnectionPool funciona
2. ✅ **Validado:** status_checker detecta corretamente  
3. ✅ **Validado:** Session persiste

**Aí sim** podemos integrar no Worker com confiança!

---

## 🔮 Futuros Scripts

- `debug_group_discovery.py` - Listar grupos de uma conexão
- `debug_send_message.py` - Enviar mensagem de teste
- `validate_all_connections.py` - Checar status de todas as conexões
