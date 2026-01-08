"""
Tests for Playwriter API - Week 78

Tests REST API endpoints for browser automation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.browser_automation import (
    PlaywriterSession,
    PlaywriterExecution,
    PlaywriterTab,
    SessionStatus,
    ExecutionStatus
)


class TestPlaywriterAPISession:
    """Tests for session management endpoints."""

    @pytest.mark.asyncio
    async def test_create_session(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions"""
        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_session = AsyncMock(return_value=PlaywriterSession(
                id=uuid4(),
                name="Test Session",
                description="Test",
                browser_type="chromium",
                headless=True,
                viewport_width=1280,
                viewport_height=720,
                status=SessionStatus.CREATED.value,
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                "/api/playwriter/sessions",
                json={
                    "name": "Test Session",
                    "description": "Test",
                    "browser_type": "chromium",
                    "headless": True
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Session"
            assert data["browser_type"] == "chromium"
            assert data["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_session_validation(self, test_client, mock_db_session):
        """Test session creation validation."""
        response = await test_client.post(
            "/api/playwriter/sessions",
            json={
                "name": "",  # Invalid: empty name
                "browser_type": "invalid_browser"  # Invalid browser type
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_sessions(self, test_client, mock_db_session):
        """Test GET /api/playwriter/sessions"""
        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.list_sessions = AsyncMock(return_value=[
                PlaywriterSession(
                    id=uuid4(),
                    name="Session 1",
                    browser_type="chromium",
                    headless=True,
                    viewport_width=1280,
                    viewport_height=720,
                    status=SessionStatus.ACTIVE.value,
                    created_at=datetime.now(timezone.utc)
                ),
                PlaywriterSession(
                    id=uuid4(),
                    name="Session 2",
                    browser_type="firefox",
                    headless=False,
                    viewport_width=1920,
                    viewport_height=1080,
                    status=SessionStatus.CLOSED.value,
                    created_at=datetime.now(timezone.utc)
                )
            ])

            response = await test_client.get("/api/playwriter/sessions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Session 1"
            assert data[1]["name"] == "Session 2"

    @pytest.mark.asyncio
    async def test_list_sessions_with_status_filter(self, test_client, mock_db_session):
        """Test session listing with status filter."""
        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.list_sessions = AsyncMock(return_value=[])

            response = await test_client.get(
                "/api/playwriter/sessions",
                params={"status": "active"}
            )

            assert response.status_code == 200
            mock_service.list_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session(self, test_client, mock_db_session):
        """Test GET /api/playwriter/sessions/{session_id}"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_session = AsyncMock(return_value=PlaywriterSession(
                id=session_id,
                name="Test Session",
                browser_type="chromium",
                headless=True,
                viewport_width=1280,
                viewport_height=720,
                status=SessionStatus.ACTIVE.value,
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.get(f"/api/playwriter/sessions/{session_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, test_client, mock_db_session):
        """Test getting non-existent session."""
        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_session = AsyncMock(return_value=None)

            response = await test_client.get(f"/api/playwriter/sessions/{uuid4()}")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_session(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions/{id}/start"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.start_session = AsyncMock(return_value=PlaywriterSession(
                id=session_id,
                name="Test",
                browser_type="chromium",
                headless=True,
                viewport_width=1280,
                viewport_height=720,
                status=SessionStatus.ACTIVE.value,
                started_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(f"/api/playwriter/sessions/{session_id}/start")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            assert data["started_at"] is not None

    @pytest.mark.asyncio
    async def test_close_session(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions/{id}/close"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.close_session = AsyncMock(return_value=PlaywriterSession(
                id=session_id,
                name="Test",
                browser_type="chromium",
                headless=True,
                viewport_width=1280,
                viewport_height=720,
                status=SessionStatus.CLOSED.value,
                closed_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(f"/api/playwriter/sessions/{session_id}/close")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "closed"


class TestPlaywriterAPIExecution:
    """Tests for code execution endpoints."""

    @pytest.mark.asyncio
    async def test_execute_code(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions/{id}/execute"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.execute = AsyncMock(return_value=PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="await page.click('#submit')",
                result={"clicked": True},
                status=ExecutionStatus.COMPLETED.value,
                execution_time_ms=150,
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                f"/api/playwriter/sessions/{session_id}/execute",
                json={"code": "await page.click('#submit')"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["result"]["clicked"] is True

    @pytest.mark.asyncio
    async def test_click_action(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions/{id}/click"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.click = AsyncMock(return_value=PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="await page.click('#button')",
                status=ExecutionStatus.COMPLETED.value,
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                f"/api/playwriter/sessions/{session_id}/click",
                json={"selector": "#button"}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_type_action(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions/{id}/type"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.type_text = AsyncMock(return_value=PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="await page.type('#input', 'test')",
                status=ExecutionStatus.COMPLETED.value,
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                f"/api/playwriter/sessions/{session_id}/type",
                json={"selector": "#input", "text": "test"}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_goto_action(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions/{id}/goto"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.goto = AsyncMock(return_value=PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="await page.goto('https://example.com')",
                status=ExecutionStatus.COMPLETED.value,
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                f"/api/playwriter/sessions/{session_id}/goto",
                json={"url": "https://example.com"}
            )

            assert response.status_code == 200


class TestPlaywriterAPITabs:
    """Tests for tab management endpoints."""

    @pytest.mark.asyncio
    async def test_list_tabs(self, test_client, mock_db_session):
        """Test GET /api/playwriter/sessions/{id}/tabs"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_tabs = AsyncMock(return_value=[
                PlaywriterTab(
                    id=uuid4(),
                    session_id=session_id,
                    tab_index=0,
                    url="https://example.com",
                    title="Example",
                    permitted=True,
                    created_at=datetime.now(timezone.utc)
                )
            ])

            response = await test_client.get(f"/api/playwriter/sessions/{session_id}/tabs")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["tab_index"] == 0

    @pytest.mark.asyncio
    async def test_grant_tab_permission(self, test_client, mock_db_session):
        """Test POST /api/playwriter/sessions/{id}/tabs/{index}/grant-permission"""
        session_id = uuid4()

        with patch('app.api.playwriter.PlaywriterService') as MockService:
            mock_service = MockService.return_value
            mock_service.grant_tab_permission = AsyncMock(return_value=PlaywriterTab(
                id=uuid4(),
                session_id=session_id,
                tab_index=0,
                permitted=True,
                permitted_by="admin",
                permitted_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                f"/api/playwriter/sessions/{session_id}/tabs/0/grant-permission",
                json={"granted_by": "admin"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["permitted"] is True
            assert data["permitted_by"] == "admin"


class TestPlaywriterAPIStats:
    """Tests for statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats(self, test_client, mock_db_session):
        """Test GET /api/playwriter/stats"""
        with patch('app.api.playwriter.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db

            # Mock the query results
            mock_db.execute = AsyncMock(side_effect=[
                MagicMock(fetchall=lambda: [("active", 5), ("closed", 10)]),
                MagicMock(scalar=lambda: 100),
                MagicMock(scalar=lambda: 250),
                MagicMock(scalar=lambda: 5)
            ])

            response = await test_client.get("/api/playwriter/stats")

            assert response.status_code == 200
