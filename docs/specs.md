# AutoPromo Cloud - Especificação Técnica

## Visão Geral

**AutoPromo Cloud** é um SaaS de "High-Frequency Trading" (HFT) para marketing de afiliados que automatiza o processo de:
- Ingestão de milhares de ofertas por minuto (WhatsApp/Telegram/APIs)
- Deduplicação e filtragem inteligente
- Troca de links para monetização (Amazon, Magalu, Mercado Livre, etc)
- Redistribuição controlada para canais proprietários
- Compliance anti-spam com rate limiting rigoroso

## Princípios do MVP (V1)

> [!IMPORTANT]
> **Zero Criatividade**: Não inventar ofertas nem modificar significativamente o texto original.

> [!IMPORTANT]
> **Zero Alucinação**: Se preço ou dado não for claro, não adivinhar nem inventar.

> [!IMPORTANT]
> **Performance Total**: Latência de ingestão < 200ms (ideal: <100ms).

**Objetivo V1**: Copiar ofertas existentes, higienizar minimamente, trocar links para tags de afiliado e reenfileirar para envio.

## Stack Tecnológica (Imutável)

### Backend
- **Core**: Python 3.12+
- **Gestão de Pacotes**: uv ou poetry
- **API Framework**: FastAPI (async/await obrigatório)
- **Database (Relacional)**: PostgreSQL 16+
  - Driver: asyncpg
  - ORM: SQLAlchemy 2.x (modo declarativo moderno)
  - Migrações: Alembic
- **Database (Cache/Hot)**: Redis 7+
  - Filas (List/Streams)
  - Deduplicação (SET com NX)
  - Rate Limiting

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/UI
- **Icons**: Lucide React

### Infraestrutura
- **Docker & Docker Compose**: Orquestração local de todos os serviços

## Arquitetura Multi-Tenant

O sistema é **multi-tenant SaaS**:
- Vários afiliados usam a mesma infraestrutura
- **Regra Crítica**: NUNCA retornar, ler ou enfileirar dados de outro usuário
- Toda chave Redis relacionada a negócio deve incluir `user_id`
- Toda query ao Postgres deve filtrar por `user_id`

## Endpoints Principais (Resumo)

Veja [api_contract.md](./api_contract.md) para especificações completas.

### Core
- `POST /api/v1/webhook/whatsapp` - Webhook Evolution API (WhatsApp)
- `POST /api/v1/webhook/telegram` - Webhook Telegram Bot API
- `POST /api/v1/users/register` - Registro de usuário
- `POST /api/v1/users/login` - Autenticação (retorna JWT)
- `GET /api/v1/users/me` - Dados do usuário autenticado
- `PATCH /api/v1/users/me` - Atualizar configurações

### Gestão de Tags & Grupos
- `GET|POST|DELETE /api/v1/tags` - Gerenciar tags de afiliado
- `GET|POST /api/v1/groups/sources` - Gerenciar grupos-fonte
- `GET|POST /api/v1/groups/destinations` - Gerenciar grupos-destino

### Dashboard
- `GET /api/v1/dashboard/stats` - Estatísticas (fila, enviados, etc)
- `GET /api/v1/offers/recent` - Ofertas recentes

## Entidades de Negócio

1. **Usuário** (afiliado SaaS)
2. **Grupos-Fonte** (origem das promoções)
3. **Grupos-Destino** (onde o afiliado posta)
4. **Configurações do Usuário** (janela de horário, delays, limites)
5. **Tags de Afiliado por Loja** (monetização)
6. **Oferta** (cada mensagem candidata a envio)
7. **Histórico de Preço** (analytics)
8. **Logs de Envio** (auditoria e deduplicação)

## Módulos Principais

### 1. Módulo de Webhooks - "The Entry Point"

**Endpoints**:
- `POST /api/v1/webhook/whatsapp` - Recebe mensagens da Evolution API
- `POST /api/v1/webhook/telegram` - Recebe updates do Telegram Bot API

**Fluxo**:
1. Evolution API / Telegram Bot envia webhook diretamente para FastAPI
2. Endpoint extrai `user_id` (via header `X-User-ID` ou mapeamento interno)
3. Normaliza payload para formato interno
4. Chama serviço de ingestão (deduplicação + enfileiramento)

**Lógica de Deduplicação**:

1. Normalizar texto (lowercase, remover espaços extras)
2. Extrair URL canônica
3. Criar hash: `SHA-256(user_id + canonical_url + cleaned_text_snippet)`
4. Atomic Lock Redis: `SET ingestion_dedup:{hash} 1 EX 600 NX`
   - Se retornar `None` → duplicado → HTTP 200 e descartar
   - Se retornar `"OK"` → novo → continuar
5. Serializar JSON normalizado
6. `RPUSH queue:ingestion`
7. Retornar HTTP 200 imediatamente

**SLA**: Resposta em < 100ms

### 2. Worker de Processamento - "The Brain"

**Trigger**: Loop infinito com `BLPOP queue:ingestion`

**Pipeline de Transformação**:

1. **Unshorten**: Resolver URLs encurtadas (bit.ly, amzn.to) via HTTP HEAD
2. **Parser de Loja & Produto**:
   - Identificar loja (amazon, magalu, mercadolivre)
   - Extrair ID de produto (ASIN, MLB, etc) com regex
   - Criar `product_unique_id` (ex: "AMZN-B08XYZ")
3. **Price Engine**:
   - Se houver preço no texto → parsear e salvar em `price_history`
   - Se não houver → registrar sem inventar
4. **Monetização**:
   - Buscar tag do usuário para a loja detectada em `affiliate_tags`
   - Se não houver tag → usar link original (fail-safe)
   - Se houver → reconstruir URL com tag de afiliado
5. **Quality Gate**:
   - Blacklist por usuário
   - Janela de repetição 24h (consultar `send_logs`)
6. **Enfileiramento**:
   - Para cada grupo destino ativo do usuário
   - Criar `PostableOffer`
   - `RPUSH queue:dispatch:user:{user_id}`

### 3. Dispatcher Service - "The Traffic Controller"

**Mecanismo**: Loop infinito em Round-Robin sobre todos os users ativos

**Para cada user_id**:

1. **Verificar Janelas de Envio**:
   - Ler `config_json` do usuário (window_start, window_end, min_delay_seconds)
   - Se fora da janela → não desenfileirar (mensagens acumulam)

2. **Consumir Fila**: `LPOP queue:dispatch:user:{user_id}`

3. **Rate Limiter (Anti-Ban)**:
   - Redis key: `last_sent:user:{user_id}:group:{group_id}`
   - Se `(NOW - last_sent) < min_delay_seconds` → recolocar ou pular
   - Se liberado:
     - Chamar Provider Client (Evolution API / Telegram Bot) via código Python
     - Gravar `send_log` em Postgres
     - Atualizar Redis `last_sent`

4. **Error Handling**:
   - Em caso de erro → logar
   - Opcional: `queue:retry` com contador

## Esquema de Banco de Dados

Veja [api_contract.md](./api_contract.md) para detalhes completos dos schemas.

### Tabelas Principais

- `users` - Usuários do SaaS
- `affiliate_tags` - Tags de afiliado por loja
- `group_sources` - Grupos-fonte (origem das promoções)
- `group_destinations` - Grupos-destino (onde posta)
- `offers` - Ofertas processadas
- `price_history` - Histórico de preços
- `send_logs` - Log de envios

## Roadmap de Fases

- **FASE 0**: Setup & Memory Artifacts
- **FASE 1**: Fundação do Backend
- **FASE 2**: Ingestão & Deduplicação
- **FASE 3**: Processador & Workers
- **FASE 4**: Dispatcher & SaaS Rules
- **FASE 5**: Frontend MVP
- **FASE 6**: Testes & Hardening

## Integrações Futuras (Opcional)

### n8n (Laboratório)
- **Uso**: Ferramenta visual para prototipagem rápida de fluxos
- **Não é dependência core**: Toda lógica está em código Python
- **Casos de uso**: Testes de novos provedores, workflows experimentais

### IA (V2 - Ganchos Preparados)
- IA para copywriting de "Super Ofertas" (Claude/Gemini)
- IA para classificação de nicho quando regras simples falharem
- **Nota**: IA é opcional, usada com parcimônia (não é dependência obrigatória)
- **Implementação**: Via `services/ai_service.py`, não via n8n

## Princípios de Implementação

> [!CAUTION]
> **Multi-tenant Security**: Todo código DEVE garantir isolamento entre usuários. Uma query sem filtro de `user_id` é uma vulnerabilidade crítica.

- **Comentários**: Todo código complexo em Português explicando o raciocínio
- **Tratamento de Erro**: Workers NUNCA devem crashar por mensagem malformada
- **Tipagem**: Type hints do Python em todas as funções
- **Documentação**: Atualizar docs/ a cada fase concluída
