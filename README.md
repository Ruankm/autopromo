# AutoPromo - WhatsApp Mirroring & Monetization SaaS

Sistema de automação WhatsApp para espelhamento de mensagens com monetização automática de links de afiliados.

## 🚀 Status do Projeto

**MVP em Desenvolvimento** | **31% Completo**

### ✅ Completado

- **Fase 1: Setup & Infrastructure**
  - Playwright 1.56.0 + Chromium
  - Estrutura de diretórios
  - Segurança (whatsapp_sessions/)
  
- **Fase 2: Models & Database**
  - WhatsAppConnection (multi-número)
  - MessageLog (deduplicação connection-scoped)
  - OfferLog (analytics)
  - Migration Alembic aplicada

- **Fase 3: Core Services** (parcial)
  - WhatsAppGateway (interface Protocol)
  - ConnectionPool (persistent contexts + recovery)
  - QueueManager (rate limit duplo)
  - HumanizedSender (typing simulation)

### 🔄 Em Progresso

- MessageMonitor (deduplicação DB + cache)
- PlaywrightGateway (implementação completa)

### 📋 Próximas Fases

- Fase 4: Worker (loop principal)
- Fase 5: API Endpoints
- Fase 6: Mirror Integration
- Fase 7: Testing
- Fase 8: Deploy & Launch

## 🏗️ Arquitetura

```
backend/
├── models/
│   ├── whatsapp_connection.py  # Multi-número por usuário
│   ├── message_log.py           # Deduplicação
│   └── offer_log.py             # Analytics
├── services/
│   └── whatsapp/
│       ├── gateway.py           # Interface abstrata
│       ├── connection_pool.py   # Gerencia contexts Playwright
│       ├── queue_manager.py     # Rate limit duplo
│       └── humanized_sender.py  # Envio simulando humano
└── workers/
    └── whatsapp_worker.py       # (próximo)
```

## 🔑 Features Principais

### Multi-Número
- Cada usuário pode conectar múltiplos números WhatsApp
- Sessões persistentes (QR Code apenas 1x)
- Isolamento completo por conexão

### Deduplicação Inteligente
- Connection-scoped (sem conflitos entre clientes)
- Cache em memória + DB como verdade
- Tripla verificação (message_id + timestamp + hash)

### Rate Limiting Duplo
- **Por grupo:** 6-10 minutos entre mensagens
- **Global:** 30 segundos entre qualquer mensagem da conexão
- Evita comportamento robótico

### Envio Humanizado
- Typing char-by-char (0.03-0.12s por caractere)
- Aguarda preview carregar (2-4s)
- Delays aleatórios
- **Preview de links GARANTIDO**

## 🛠️ Stack Tecnológica

- **Backend:** FastAPI + SQLAlchemy
- **Database:** PostgreSQL
- **Cache:** Redis
- **Automação:** Playwright (persistent contexts)
- **Queue:** Redis pub/sub

## 📦 Instalação

```bash
# Clone
git clone https://github.com/Ruankm/autopromo.git
cd autopromo

# Install dependencies
cd backend
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run migrations
alembic upgrade head
```

## 🧪 Tests

```bash
# Test Playwright
python scripts/test_playwright.py

# Test ConnectionPool
python scripts/test_connection_pool.py
```

## 📊 Roadmap

- [x] Setup Playwright
- [x] Database models
- [x] Core services (gateway, pool, queue, sender)
- [ ] Message monitor
- [ ] Worker implementation
- [ ] API endpoints
- [ ] Testing suite
- [ ] Production deployment

## 🔒 Security

- Sessões WhatsApp não commitadas (`.gitignore`)
- Connection-scoped deduplication
- Encrypted sessions (planejado)
- chmod 700 em whatsapp_sessions/

## 📝 License

MIT

## 👤 Author

Ruan K. Moreira

---

**Última atualização:** 2025-11-30
**Progresso:** Fase 3 de 8 (31%)
