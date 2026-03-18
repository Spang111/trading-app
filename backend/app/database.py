"""
Database configuration (async SQLAlchemy 2.0).
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings


database_url = settings.DATABASE_URL.strip()
if "postgresql+asyncpg://postgresql://" in database_url:
    raise ValueError("DATABASE_URL has a nested scheme. Use: postgresql+asyncpg://user:pass@host:port/db")

# Async engine for PostgreSQL via asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Declarative base
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Yield an async DB session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize tables (development only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
