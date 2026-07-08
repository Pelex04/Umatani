"""
Database session management.

Uses SQLAlchemy 2.0 async engine with connection pooling suited to a
serverless/managed-Postgres deployment (Supabase). Sessions are provided
via FastAPI dependency injection and always closed after the request,
regardless of outcome.
"""
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        # Supabase's pooler runs pgbouncer in transaction mode, which swaps
        # the underlying backend Postgres connection between queries. asyncpg
        # names prepared statements sequentially per connection object
        # (__asyncpg_stmt_0__, _1__, ...), so two pooled sessions can collide
        # on the same backend connection and raise DuplicatePreparedStatementError.
        # Disabling the cache alone isn't enough — statement names still need
        # to be globally unique, not just uncached.
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per-request.

    Rolls back on any unhandled exception to avoid leaving the connection
    in a dirty transaction state, and always closes the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
