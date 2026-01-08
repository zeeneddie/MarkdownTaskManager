"""
Week 71: MCP Proxy API Test Fixtures

Provides test client without database dependency since API tests mock the service.
"""

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.database import get_db


@pytest.fixture
def mock_db_session():
    """Mock database session for tests that need it."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
async def client(mock_db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client without database dependency.

    MCP Proxy API tests mock the service layer, so no real DB needed.
    Overrides get_db to provide a mock session.
    """
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
