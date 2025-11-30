"""
AutoPromo Backend API - Main Application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL: Load .env BEFORE any other imports
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
print(f"[STARTUP] Loading .env from: {env_path}")
print(f"[STARTUP] .env exists: {env_path.exists()}")
print(f"[STARTUP] EVOLUTION_API_TOKEN: {'LOADED' if os.getenv('EVOLUTION_API_TOKEN') else 'EMPTY!'}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.redis_client import redis_client
from api import (
    auth_router, 
    webhooks_router, 
    groups_router, 
    tags_router, 
    dashboard_router,
    whatsapp_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia lifecycle da aplicação.
    - Startup: conecta ao Redis
    - Shutdown: desconecta do Redis
    """
    # Startup
    await redis_client.connect()
    print("[OK] Redis connected")
    
    yield
    
    # Shutdown
    await redis_client.disconnect()
    print("[SHUTDOWN] Redis disconnected")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-Frequency Trading SaaS for Affiliate Marketing",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend Next.js default
        "http://localhost:3002",  # Frontend Next.js fallback
        *settings.BACKEND_CORS_ORIGINS  # Outros origens do .env
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks_router, prefix=settings.API_V1_PREFIX)
app.include_router(groups_router, prefix=settings.API_V1_PREFIX)
app.include_router(tags_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(whatsapp_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "AutoPromo Cloud API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }
