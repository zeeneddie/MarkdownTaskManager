import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, Base
from app.models.item import Item
from app.models.sprint import Sprint
from app.models.user import User

# Test database URL - use environment variable or default
# When running in Docker: db:5432, when running locally: localhost:5433
import os
import socket

def _get_default_test_db_url():
    """Detect if running in Docker or locally and return appropriate URL."""
    # Check if 'db' hostname resolves (we're in Docker)
    try:
        socket.gethostbyname('db')
        return "postgresql+asyncpg://user:password@db:5432/project_manager_test"
    except socket.gaierror:
        # Running locally, use localhost with external port
        return "postgresql+asyncpg://user:password@localhost:5433/project_manager_test"

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", _get_default_test_db_url())

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test function"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    from sqlalchemy import text

    # Drop all objects with CASCADE to handle views and FK constraints
    async with test_engine.begin() as conn:
        # Drop all views first
        await conn.execute(text("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public')
                LOOP
                    EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        # Drop all tables with CASCADE
        await conn.execute(text("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Cleanup after test - drop all with CASCADE
    async with test_engine.begin() as conn:
        await conn.execute(text("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public')
                LOOP
                    EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        await conn.execute(text("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user"""
    from app.crud import user as user_crud

    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }

    user = await user_crud.create_user(db_session, user_data)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user):
    """Get authentication headers for test requests"""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }

    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_epic(db_session: AsyncSession):
    """Create a test epic"""
    from app.crud import item as item_crud
    from app.models.item import ItemType

    epic_data = {
        "id": "EPIC-001",
        "type": ItemType.EPIC,
        "title": "Test Epic",
        "status": "PLANNED",
        "priority": "HIGH"
    }

    epic = await item_crud.create_item(db_session, epic_data)
    return epic


@pytest.fixture
async def test_feature(db_session: AsyncSession, test_epic):
    """Create a test feature"""
    from app.crud import item as item_crud
    from app.models.item import ItemType

    feature_data = {
        "id": "FEAT-001",
        "type": ItemType.FEATURE,
        "parent_id": test_epic.id,
        "title": "Test Feature",
        "status": "PLANNED"
    }

    feature = await item_crud.create_item(db_session, feature_data)
    return feature


@pytest.fixture
async def test_story(db_session: AsyncSession, test_feature):
    """Create a test story"""
    from app.crud import item as item_crud
    from app.models.item import ItemType

    story_data = {
        "id": "STORY-001",
        "type": ItemType.STORY,
        "parent_id": test_feature.id,
        "title": "Test Story",
        "status": "BACKLOG",
        "sp": 5
    }

    story = await item_crud.create_item(db_session, story_data)
    return story


@pytest.fixture
async def test_sprint(db_session: AsyncSession):
    """Create a test sprint"""
    from app.crud import sprint as sprint_crud
    from datetime import datetime, timedelta, timezone

    sprint_data = {
        "name": "Sprint 1",
        "start_date": datetime.now(timezone.utc),
        "end_date": datetime.now(timezone.utc) + timedelta(days=14),
        "goal": "Test sprint goal",
        "status": "PLANNED"
    }

    sprint = await sprint_crud.create_sprint(db_session, sprint_data)
    return sprint


@pytest.fixture
def sync_test_client():
    """Create a synchronous test client for simple tests.

    This fixture is used for tests that mock service classes directly
    and don't need actual database interactions.
    """
    return TestClient(app)


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for mocked API tests.

    This fixture is used for API tests that mock service classes
    and don't need actual database interactions.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db_session():
    """Create a mock database session for unit tests.

    This fixture is used for service unit tests that need to mock
    database interactions without actual database connections.
    """
    from unittest.mock import AsyncMock, MagicMock

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.delete = MagicMock()

    return mock_session
