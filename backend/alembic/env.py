"""
Alembic migration environment.

Imports every module's models so `alembic revision --autogenerate`
detects the full schema. As new modules are added, add their model
imports below — this is the single place that must be kept in sync.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import get_settings
from app.core.database import Base

# --- Import all ORM models so Base.metadata is fully populated ---
from app.modules.auth.models import EmailVerificationToken, RefreshToken, User  # noqa: F401
from app.modules.businesses.models import Business, PortfolioItem, Service  # noqa: F401
from app.modules.reviews.models import Review, ReviewPhoto, ReviewReply  # noqa: F401
from app.modules.support.models import Report, SupportTicket  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.schools.models import School  # noqa: F401
from app.shared.audit import AuditLog  # noqa: F401

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
