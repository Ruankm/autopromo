# Evolution API Setup Guide

**Complete guide for integrating Evolution API (WhatsApp Gateway) with AutoPromo Cloud**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Integration with AutoPromo](#integration-with-autopromo)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

---

## 🎯 Overview

Evolution API is a WhatsApp gateway that allows AutoPromo Cloud to:
- Connect multiple WhatsApp accounts (one per user - multi-tenant)
- Send and receive messages programmatically
- Manage WhatsApp groups
- Handle webhooks for incoming messages

### Key Features
- ✅ Multi-instance support (each user gets their own WhatsApp)
- ✅ QR Code authentication
- ✅ Webhook support for real-time messages
- ✅ Group management
- ✅ Message history
- ✅ PostgreSQL + Redis integration

---

## 🏗️ Architecture

### Services

```
┌─────────────────────────────────────────────────────────────┐
│                    AutoPromo Cloud Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Backend    │  │  Evolution   │  │  PostgreSQL  │      │
│  │   FastAPI    │◄─┤     API      │◄─┤              │      │
│  │   :8000      │  │   :8081      │  │   :5432      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                     ┌──────────────┐                        │
│                     │    Redis     │                        │
│                     │    :6379     │                        │
│                     └──────────────┘                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Database Strategy

**Shared PostgreSQL, Separate Databases:**
- `autopromo_db` - AutoPromo application data
- `evolution_db` - Evolution API instances and messages

**Shared Redis, Separate Indexes:**
- DB 0 - AutoPromo queues and cache
- DB 1 - Evolution API cache

### Network

All services run on the same Docker network: `autopromo-network`

---

## 📦 Installation

### Prerequisites

- Docker & Docker Compose installed
- AutoPromo Cloud repository cloned
- Ports available: 8081 (Evolution API)

### Step 1: Start Infrastructure

The Evolution API is integrated into the main `docker-compose.yml`:

```bash
# Start all services (including Evolution API)
docker compose up -d

# Or start only Evolution API + dependencies
docker compose up -d postgres redis evolution-api
```

### Step 2: Verify Services

```bash
# Check if all containers are running
docker compose ps

# Expected output:
# autopromo-postgres       running
# autopromo-redis          running
# autopromo-evolution-api  running
```

### Step 3: Check Logs

```bash
# Follow Evolution API logs
docker compose logs -f evolution-api

# Expected: "Evolution API is running on port 8080"
```

### Step 4: Test Connection

```bash
# Test if Evolution API is responding
curl http://localhost:8081/

# Expected: {"status":"ok"} or similar
```

---

## ⚙️ Configuration

### Environment Variables

Evolution API configuration is in `.env.evolution` (root directory):

```bash
# Server
SERVER_URL=http://localhost:8081
PORT=8080

# Authentication (CRITICAL - KEEP SECRET!)
AUTHENTICATION_API_KEY=f708f2fc-471f-4511-83c3-701229e766d5

# Database (shared PostgreSQL)
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://autopromo:autopromo_dev_pass@autopromo-postgres:5432/evolution_db

# Redis (shared Redis, DB index 1)
REDIS_ENABLED=true
REDIS_URI=redis://autopromo-redis:6379/1

# QR Code
QRCODE_LIMIT=30

# Instances
INSTANCE_EXPIRATION_TIME=0
DEL_INSTANCE=false
```

### Backend Integration

AutoPromo backend needs these variables in `backend/.env`:

```bash
# Evolution API connection
EVOLUTION_API_BASE_URL=http://localhost:8081
EVOLUTION_API_TOKEN=f708f2fc-471f-4511-83c3-701229e766d5
```

**IMPORTANT**: The `EVOLUTION_API_TOKEN` must match `AUTHENTICATION_API_KEY` in `.env.evolution`!

### Changing Credentials

To change the API key:

1. Edit `.env.evolution`:
   ```bash
   AUTHENTICATION_API_KEY=your-new-secure-key-here
   ```

2. Edit `backend/.env`:
   ```bash
   EVOLUTION_API_TOKEN=your-new-secure-key-here
   ```

3. Restart Evolution API:
   ```bash
   docker compose restart evolution-api
   ```

---

## 🧪 Testing

### Automated Test Script

We provide a Python script to test the complete flow:

```bash
# From project root
cd backend
python scripts/setup_evolution_instance.py

# Or with uv
uv run python scripts/setup_evolution_instance.py
```

**What it does:**
1. ✅ Tests connection to Evolution API
2. ✅ Creates a WhatsApp instance named "AutoPromo_Main"
3. ✅ Generates QR Code
4. ✅ Saves QR Code as `qrcode_whatsapp.png`
5. ✅ Provides next steps instructions

### Manual Testing

#### 1. Create Instance

```bash
curl -X POST http://localhost:8081/instance/create \
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "TestInstance",
    "token": "test-token-123",
    "qrcode": true
  }'
```

#### 2. Get QR Code

```bash
curl http://localhost:8081/instance/connect/TestInstance \
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5"
```

#### 3. Check Connection Status

```bash
curl http://localhost:8081/instance/connectionState/TestInstance \
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5"
```

Expected states:
- `close` - Not connected
- `connecting` - Waiting for QR scan
- `open` - Connected!

#### 4. Send Test Message

```bash
curl -X POST http://localhost:8081/message/sendText/TestInstance \
  -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5511999999999",
    "text": "Hello from AutoPromo!"
  }'
```

---

## 🔗 Integration with AutoPromo

### Backend Client

Evolution API client is already implemented in:
- `backend/services/providers/whatsapp_evolution.py`

**Usage example:**

```python
from services.providers.whatsapp_evolution import EvolutionAPIClient

# Create client
client = EvolutionAPIClient(
    api_url="http://localhost:8081",
    api_key="f708f2fc-471f-4511-83c3-701229e766d5",
    instance_name="user_instance_123"
)

# Create instance
await client.create_instance()

# Get QR Code
qr_code = await client.get_qr_code()

# Check status
status = await client.get_connection_status()

# Fetch groups
groups = await client.fetch_all_groups()
```

### API Endpoints

AutoPromo exposes WhatsApp management via:
- `POST /api/v1/whatsapp/connect` - Connect WhatsApp (generates QR)
- `GET /api/v1/whatsapp/status` - Check connection status
- `POST /api/v1/whatsapp/discover-groups` - Import WhatsApp groups
- `DELETE /api/v1/whatsapp/disconnect` - Disconnect WhatsApp

See `backend/api/whatsapp.py` for implementation.

### Frontend

WhatsApp connection page:
- `frontend/app/dashboard/whatsapp/page.tsx`

Features:
- QR Code display
- Connection status polling
- Group discovery
- Disconnect button

---

## 🔧 Troubleshooting

### Evolution API not starting

**Symptom**: Container exits immediately

**Check logs**:
```bash
docker compose logs evolution-api
```

**Common issues**:
1. Database connection failed
   - Solution: Ensure PostgreSQL is running and healthy
   - Check: `docker compose ps postgres`

2. Redis connection failed
   - Solution: Ensure Redis is running
   - Check: `docker compose ps redis`

3. Port 8081 already in use
   - Solution: Change port in `docker-compose.yml`:
     ```yaml
     ports:
       - "8082:8080"  # Use 8082 instead
     ```
   - Update `.env.evolution`: `SERVER_URL=http://localhost:8082`

### QR Code not generating

**Symptom**: Script runs but no QR Code

**Solutions**:
1. Check if instance already exists:
   ```bash
   curl http://localhost:8081/instance/fetchInstances \
     -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5"
   ```

2. Delete existing instance:
   ```bash
   curl -X DELETE http://localhost:8081/instance/delete/AutoPromo_Main \
     -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5"
   ```

3. Try again:
   ```bash
   python backend/scripts/setup_evolution_instance.py
   ```

### Connection timeout

**Symptom**: "Failed to connect" errors

**Solutions**:
1. Verify Evolution API is running:
   ```bash
   docker compose ps evolution-api
   ```

2. Check if port is accessible:
   ```bash
   curl http://localhost:8081/
   ```

3. Check firewall/antivirus blocking port 8081

### Database errors

**Symptom**: "Database connection failed"

**Solutions**:
1. Check PostgreSQL logs:
   ```bash
   docker compose logs postgres
   ```

2. Verify database exists:
   ```bash
   docker exec -it autopromo-postgres psql -U autopromo -c "\l"
   ```

3. Create database manually if needed:
   ```bash
   docker exec -it autopromo-postgres psql -U autopromo -c "CREATE DATABASE evolution_db;"
   ```

---

## 🚀 Production Deployment

### Security Checklist

- [ ] Change `AUTHENTICATION_API_KEY` to a strong random value
- [ ] Use HTTPS for `SERVER_URL`
- [ ] Set `AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=false`
- [ ] Enable webhook authentication
- [ ] Use environment-specific `.env` files
- [ ] Don't commit `.env` files to git

### Recommended Changes for Production

1. **Strong API Key**:
   ```bash
   # Generate with:
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **HTTPS URL**:
   ```bash
   SERVER_URL=https://evolution.yourdomain.com
   ```

3. **Separate Database Server** (optional):
   ```bash
   DATABASE_CONNECTION_URI=postgresql://user:pass@prod-db-server:5432/evolution_db
   ```

4. **Redis with Password** (optional):
   ```bash
   REDIS_URI=redis://:password@redis-server:6379/1
   ```

5. **Enable Webhooks**:
   ```bash
   WEBHOOK_GLOBAL_ENABLED=true
   WEBHOOK_GLOBAL_URL=https://yourdomain.com/api/v1/webhook/whatsapp
   ```

---

## 📚 Additional Resources

- [Evolution API Documentation](https://doc.evolution-api.com/)
- [Evolution API GitHub](https://github.com/EvolutionAPI/evolution-api)
- [AutoPromo Architecture](../docs/architecture.mermaid)
- [Multi-Tenant Guide](../ARQUITETURA_MULTI_TENANT.md)

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker compose logs evolution-api`
2. Review this guide's troubleshooting section
3. Check Evolution API GitHub issues
4. Review AutoPromo backend logs

---

**Last Updated**: 2025-11-26  
**Evolution API Version**: v2.1.1  
**AutoPromo Version**: 1.0.0
