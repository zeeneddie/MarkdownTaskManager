import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import get_db, Base
from app.models.item import Item
from app.models.sprint import Sprint
from app.models.user import User

# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost/project_manager_test"

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


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
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
    from datetime import datetime, timedelta

    sprint_data = {
        "name": "Sprint 1",
        "start_date": datetime.utcnow(),
        "end_date": datetime.utcnow() + timedelta(days=14),
        "goal": "Test sprint goal",
        "status": "PLANNED"
    }

    sprint = await sprint_crud.create_sprint(db_session, sprint_data)
    return sprint
