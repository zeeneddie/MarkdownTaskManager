"""
Pytest configuration and fixtures for Week 11 tests
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
from app.main import app
from app.database import get_db
from app.models.item import Base as ItemBase
from app.models.sprint import Base as SprintBase
from app.models.user import Base as UserBase
from app.models.green_paper import Base as GreenPaperBase


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_project_manager"


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(ItemBase.metadata.create_all)
        await conn.run_sync(SprintBase.metadata.create_all)
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(GreenPaperBase.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(GreenPaperBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(SprintBase.metadata.drop_all)
        await conn.run_sync(ItemBase.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """Create test HTTP client with database session override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
