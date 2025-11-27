"""
Redis client wrapper assíncrono.
Gerencia conexões e operações comuns (filas, cache, dedup, rate limit).
"""
import redis.asyncio as redis
from typing import Optional
from .config import settings


class RedisClient:
    """Cliente Redis assíncrono singleton."""
    
    _instance: Optional['RedisClient'] = None
    _redis: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Estabelece conexão com Redis."""
        if self._redis is None:
            self._redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
    
    async def disconnect(self):
        """Fecha conexão com Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    @property
    def client(self) -> redis.Redis:
        """Retorna instância do cliente Redis."""
        if self._redis is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._redis


# Instância global
redis_client = RedisClient()


async def get_redis() -> redis.Redis:
    """
    Dependency para obter cliente Redis.
    Usar como: redis: Redis = Depends(get_redis)
    """
    return redis_client.client
