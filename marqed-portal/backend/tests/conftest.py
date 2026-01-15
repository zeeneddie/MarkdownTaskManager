"""
Pytest configuration and fixtures for MarQed.ai Client Portal tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.tenant import Tenant, TenantStatus, SubscriptionTier
from app.models.user import User, TenantUser, UserRole

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/marqed_portal_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Company",
        subdomain="test",
        status=TenantStatus.ACTIVE,
        subscription_tier=SubscriptionTier.PROFESSIONAL,
        monthly_fp_allocation=100,
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_tenant_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
) -> TenantUser:
    """Create test tenant-user association."""
    tenant_user = TenantUser(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(tenant_user)
    await db_session.commit()
    await db_session.refresh(tenant_user)
    return tenant_user


@pytest.fixture
def auth_headers(test_user: User, test_tenant: Tenant) -> dict:
    """Create authorization headers with JWT token."""
    token = create_access_token({
        "sub": test_user.id,
        "email": test_user.email,
        "tenant_id": test_tenant.id,
        "roles": ["admin"],
    })
    return {"Authorization": f"Bearer {token}"}
