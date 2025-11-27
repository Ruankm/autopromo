"""
Database setup com SQLAlchemy 2.x (async).
Configuração de engine, session factory e base declarativa.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings

# Engine assíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Colocar True para debug SQL
    future=True,
    pool_pre_ping=True,
)

# Session factory assíncrona
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base declarativa para models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency para obter sessão de banco de dados.
    Usar como: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
