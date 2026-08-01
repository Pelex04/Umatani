"""
Shared test fixtures.

Uses an in-memory SQLite database via aiosqlite for fast, isolated test
runs. Production uses PostgreSQL — schema-level Postgres-specific types
(UUID, INET, JSONB) are exercised separately in CI against a real
Postgres service container (see .github/workflows), but the async
SQLAlchemy session/repository/service logic under test here is
database-agnostic by design.
"""
import os
import uuid
from collections.abc import AsyncGenerator

# Must be set before any app module imports app.core.config (settings are
# cached via lru_cache on first access).
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/umatani_test"
)
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-only-secret-key-not-used-in-production-1234567890"
)
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("STORAGE_BACKEND", "local")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.modules.auth.models import EmailVerificationToken, PasswordResetToken, RefreshToken, User, UserRole, UserStatus  # noqa: F401
from app.modules.businesses.models import Business, PortfolioItem, Service  # noqa: F401
from app.modules.reviews.models import Review, ReviewPhoto, ReviewReply  # noqa: F401
from app.modules.support.models import Report, SupportTicket  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.schools.models import School, SchoolStatus
from app.shared.audit import AuditLog  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def app_client(
    db_session: AsyncSession, tmp_path
) -> AsyncGenerator[AsyncClient, None]:
    # Import app lazily so env vars set by conftest take effect first.
    from app.main import app
    from app.modules.media.deps import get_storage
    from app.modules.media.storage import LocalStorageBackend

    app.state.limiter.reset()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    def override_get_storage() -> LocalStorageBackend:
        return LocalStorageBackend(base_dir=str(tmp_path / "media"))

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Minimal valid 1x1 PNG, used as sample "real" image content in upload tests.
SAMPLE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    admin = User(
        id=uuid.uuid4(),
        email="admin@umatani.app",
        hashed_password=hash_password("AdminPass123"),
        full_name="Platform Admin",
        role=UserRole.ADMIN,
        status=UserStatus.VERIFIED,
        school_id=None,
    )
    db_session.add(admin)
    await db_session.flush()
    await db_session.commit()
    return admin


@pytest_asyncio.fixture
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    token = create_access_token(str(admin_user.id), admin_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def approved_school(db_session: AsyncSession) -> School:
    school = School(
        id=uuid.uuid4(),
        name="Malawi University of Business and Applied Sciences",
        country="Malawi",
        city="Blantyre",
        email_domain="mubas.ac.mw",
        status=SchoolStatus.APPROVED,
        is_active=True,
    )
    db_session.add(school)
    await db_session.flush()
    await db_session.commit()
    return school


@pytest_asyncio.fixture
async def active_category(db_session: AsyncSession) -> Category:
    cat = Category(
        id=uuid.uuid4(),
        name="Graphic Design",
        slug="graphic-design",
        description="Visual design services",
        is_active=True,
        display_order=0,
    )
    db_session.add(cat)
    await db_session.flush()
    await db_session.commit()
    return cat


@pytest_asyncio.fixture
async def verified_owner(db_session: AsyncSession, approved_school: School) -> User:
    """A fully-verified business owner — can create a business profile."""
    owner = User(
        id=uuid.uuid4(),
        email="owner@mubas.ac.mw",
        hashed_password=hash_password("OwnerPass123"),
        full_name="Business Owner",
        role=UserRole.BUSINESS_OWNER,
        status=UserStatus.VERIFIED,
        school_id=approved_school.id,
    )
    db_session.add(owner)
    await db_session.flush()
    await db_session.commit()
    return owner


@pytest_asyncio.fixture
def verified_owner_headers(verified_owner: User) -> dict[str, str]:
    token = create_access_token(str(verified_owner.id), verified_owner.role)
    return {"Authorization": f"Bearer {token}"}
