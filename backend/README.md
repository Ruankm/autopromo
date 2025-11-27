# AutoPromo Backend - Guia Rápido

## Setup Completo

### 1. Instalar Dependências

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install fastapi uvicorn[standard] sqlalchemy alembic asyncpg redis pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-multipart httpx
```

### 2. Configurar Ambiente

Copie `.env.example` para `.env`:

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

Edite `.env` conforme necessário (as configurações padrão funcionam com o docker-compose da raiz).

### 3. Subir Infraestrutura

Na raiz do projeto:

```bash
docker compose up -d postgres redis
```

### 4. Rodar Migrations

```bash
# Aplicar todas as migrations
alembic upgrade head

# Reverter última migration (se necessário)
alembic downgrade -1

# Ver histórico
alembic history
```

### 5. Rodar Servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## Estrutura do Projeto

```
backend/
├── api/                  # Endpoints REST
│   ├── __init__.py
│   └── auth.py          # Autenticação (register, login)
├── core/                 # Configuração central
│   ├── config.py        # Pydantic Settings
│   ├── database.py      # SQLAlchemy async setup
│   ├── redis_client.py  # Redis wrapper
│   └── security.py      # JWT & password hashing
├── models/               # SQLAlchemy models
│   ├── user.py
│   ├── affiliate_tag.py
│   ├── group.py
│   ├── offer.py
│   ├── price_history.py
│   └── send_log.py
├── schemas/              # Pydantic schemas
│   ├── user.py
│   ├── affiliate_tag.py
│   └── group.py
├── services/             # Lógica de negócio (futuro)
├── repositories/         # Camada de dados (futuro)
├── workers/              # Workers & Dispatcher (FASE 3-4)
├── alembic/              # Migrations
│   ├── versions/
│   │   └── 001_initial.py
│   └── env.py
├── main.py               # Entry point FastAPI
├── alembic.ini           # Configuração Alembic
└── pyproject.toml        # Dependências
```

## Endpoints Disponíveis (FASE 1)

### Autenticação

- `POST /api/v1/users/register` - Criar conta
  ```json
  {
    "email": "user@example.com",
    "password": "MinhaS3nh@123"
  }
  ```

- `POST /api/v1/users/login` - Login
  ```json
  {
    "email": "user@example.com",
    "password": "MinhaS3nh@123"
  }
  ```
  Retorna JWT token + dados do usuário

## Próximas Fases

- **FASE 2**: Ingestão & Deduplicação
- **FASE 3**: Processador & Workers
- **FASE 4**: Dispatcher & SaaS Rules
- **FASE 5**: Frontend MVP
- **FASE 6**: Testes & Hardening
