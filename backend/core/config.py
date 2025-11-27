"""
Configuração centralizada usando Pydantic Settings.
Lê variáveis de ambiente e fornece validação automática.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Configurações da aplicação AutoPromo Cloud.
    
    Todas as variáveis são lidas do ambiente ou arquivo .env.
    Valores padrão são fornecidos apenas para desenvolvimento.
    """
    
    # Database PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://autopromo:autopromo_dev_pass@localhost:5432/autopromo_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-CHANGE-IN-PRODUCTION-min-32-characters-required"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AutoPromo Cloud"
    
    # Evolution API (WhatsApp Provider)
    EVOLUTION_API_BASE_URL: str = "http://localhost:8080"
    EVOLUTION_API_TOKEN: str = "your-evolution-api-token-here"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    
    # CORS (opcional, para desenvolvimento)
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Instância global de configuração
settings = Settings()
