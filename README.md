# 🚀 AutoPromo Cloud

**High-Frequency Trading (HFT) SaaS para Marketing de Afiliados**

AutoPromo Cloud é uma plataforma SaaS que automatiza a ingestão, processamento e redistribuição de ofertas de afiliados em alta frequência, respeitando limites de taxa para evitar banimentos (Anti-Spam Compliance).

## 📋 Visão Geral

O sistema ingere milhares de ofertas por minuto de múltiplas fontes (WhatsApp, Telegram, APIs), deduplica, filtra, troca links para monetização com suas tags de afiliado, e redistribui para seus canais proprietários de forma controlada.

### Principais Funcionalidades

- ⚡ **Ingestão de Alta Performance**: < 100ms de latência
- 🔄 **Deduplicação Inteligente**: Cache Redis com SHA-256
- 💰 **Monetização Automática**: Troca de links para tags de afiliado (Amazon, Magalu, Mercado Livre)
- 🎯 **Multi-tenant SaaS**: Isolamento completo entre usuários
- 🛡️ **Anti-Ban Compliance**: Rate limiting e janelas de horário configuráveis
- 📊 **Analytics**: Histórico de preços e métricas de envio

## 🏗️ Arquitetura

```
Fontes Externas → n8n Gateway → FastAPI Backend → Redis/PostgreSQL → Dispatcher → n8n → Messaging APIs
```

**Componentes**:
- **Backend**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL 16 + Redis 7
- **Frontend**: Next.js 15 + Tailwind CSS + Shadcn/UI
- **Gateway**: n8n (webhooks e automação)
- **Infra**: Docker Compose

Veja o diagrama completo em [`docs/architecture.mermaid`](./docs/architecture.mermaid).

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.12+ (para desenvolvimento local)
- Node.js 20+ (para frontend)

### 1. Subir a Infraestrutura Base

```bash
# Subir apenas PostgreSQL, Redis e Adminer (dev)
docker-compose --profile dev up -d

# OU subir com n8n incluído (full stack)
docker-compose --profile full up -d
```

**Serviços disponíveis**:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Adminer (DB UI): `http://localhost:8080`
- n8n (se profile full): `http://localhost:5678` (user: `admin`, pass: `autopromo123`)

### 2. Verificar Status

```bash
docker-compose ps
```

### 3. Acessar Adminer (PostgreSQL UI)

Acesse `http://localhost:8080`:
- **Sistema**: PostgreSQL
- **Servidor**: postgres
- **Usuário**: autopromo
- **Senha**: autopromo_dev_pass
- **Base de dados**: autopromo_db

## 📁 Estrutura do Projeto

```
autopromo/
├── backend/          # FastAPI application (FASE 1+)
│   ├── api/          # Endpoints REST
│   ├── services/     # Lógica de negócio
│   ├── repositories/ # Camada de dados
│   ├── workers/      # Worker & Dispatcher
│   ├── schemas/      # Pydantic models
│   └── core/         # Config, database, redis
├── frontend/         # Next.js application (FASE 5+)
├── infra/            # Scripts de infraestrutura
├── docs/             # Documentação técnica
│   ├── specs.md              # Especificação completa
│   ├── architecture.mermaid  # Diagrama de arquitetura
│   ├── api_contract.md       # Contratos de API
│   └── todo.md               # Checklist de implementação
├── docker-compose.yml
└── README.md
```

## 📖 Documentação

- **[Especificação Técnica](./docs/specs.md)**: Visão completa do sistema, princípios e stack
- **[Arquitetura](./docs/architecture.mermaid)**: Diagrama de fluxo de dados
- **[API Contract](./docs/api_contract.md)**: Endpoints, schemas e Redis keys
- **[Todo](./docs/todo.md)**: Checklist de implementação por fase

## 🔄 Fases de Implementação

- **FASE 0**: ✅ Setup & Artifacts (VOCÊ ESTÁ AQUI)
- **FASE 1**: 🔨 Fundação do Backend
- **FASE 2**: 📥 Ingestão & Deduplicação
- **FASE 3**: 🧠 Processador & Workers
- **FASE 4**: 🚦 Dispatcher & SaaS Rules
- **FASE 5**: 💻 Frontend MVP
- **FASE 6**: 🧪 Testes & Hardening

## 🛠️ Desenvolvimento

### Backend (FASE 1+)

```bash
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (FASE 5+)

```bash
cd frontend
npm install
npm run dev
```

## 🔐 Segurança Multi-Tenant

> [!CAUTION]
> **Princípio Crítico**: Todo código DEVE garantir isolamento entre usuários. Toda query ao Postgres e toda chave Redis relacionada a negócio DEVE incluir `user_id`.

## 📝 Princípios do MVP

- **Zero Criatividade**: Não inventar ofertas
- **Zero Alucinação**: Não adivinhar preços ou dados
- **Performance Total**: Latência < 100ms no endpoint de ingestão

## 🤝 Contribuindo

Este projeto está em desenvolvimento ativo. Siga o checklist em [`docs/todo.md`](./docs/todo.md).

## 📄 Licença

Proprietary - AutoPromo Cloud © 2025

---

**Status Atual**: FASE 0 Completo ✅  
**Próximo Passo**: FASE 1 - Fundação do Backend
