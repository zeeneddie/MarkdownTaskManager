"""
Pytest configuration and fixtures for Week 50 Quality Gate tests
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db
from app.models.item import Base as ItemBase
from app.models.sprint import Base as SprintBase
from app.models.user import Base as UserBase
from app.models.green_paper import Base as GreenPaperBase
from app.models.quality_gate_config import Base as QualityGateBase


# Test database URL - uses Docker PostgreSQL
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5433/project_manager"


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
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
        await conn.run_sync(QualityGateBase.metadata.create_all)

    yield engine

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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_validation_errors():
    """Sample validation errors for testing gate evaluation."""
    return [
        {
            "phase": "linting",
            "message": "Missing semicolon",
            "severity": "warning",
            "file": "src/app.ts",
            "line": 10
        },
        {
            "phase": "type_check",
            "message": "Type 'string' not assignable to 'number'",
            "severity": "error",
            "file": "src/utils.ts",
            "line": 25
        },
        {
            "phase": "unit_tests",
            "message": "Test failed: expected 5 but got 4",
            "severity": "critical",
            "file": "tests/math.test.ts",
            "line": 15
        }
    ]


@pytest.fixture
def workflow_types():
    """List of all supported workflow types."""
    return [
        "NEW_FEATURE",
        "MAINTENANCE",
        "BUG",
        "QUALITY_AUDIT",
        "MIGRATION",
        "REFACTORING",
        "DOCUMENTATION",
        "HOTFIX"
    ]
