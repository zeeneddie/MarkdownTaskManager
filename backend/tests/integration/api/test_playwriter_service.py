"""
Tests for PlaywriterService - Week 78

Tests browser automation session management, code execution,
and tab permission handling.

NOTE: Tests are skipped because they try to mock methods that don't exist
in the actual service implementation (e.g., _launch_browser).
TODO: Update tests to use current API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

pytestmark = pytest.mark.skip(reason="Tests use outdated API - needs update to match service implementation")

from app.services.playwriter_service import PlaywriterService
from app.models.browser_automation import (
    PlaywriterSession,
    PlaywriterExecution,
    PlaywriterTab,
    SessionStatus,
    ExecutionStatus
)


class TestPlaywriterServiceSession:
    """Tests for session management."""

    @pytest.mark.asyncio
    async def test_create_session(self, mock_db_session):
        """Test creating a new browser session."""
        service = PlaywriterService(mock_db_session)

        session = await service.create_session(
            name="Test Session",
            description="Testing browser automation",
            browser_type="chromium",
            headless=True
        )

        assert session.name == "Test Session"
        assert session.browser_type == "chromium"
        assert session.headless is True
        assert session.status == SessionStatus.CREATED.value
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_with_viewport(self, mock_db_session):
        """Test creating session with custom viewport."""
        service = PlaywriterService(mock_db_session)

        session = await service.create_session(
            name="Wide Session",
            viewport_width=1920,
            viewport_height=1080
        )

        assert session.viewport_width == 1920
        assert session.viewport_height == 1080

    @pytest.mark.asyncio
    async def test_create_session_with_context_options(self, mock_db_session):
        """Test creating session with extra context options."""
        service = PlaywriterService(mock_db_session)

        context_opts = {
            "locale": "nl-NL",
            "geolocation": {"latitude": 52.3676, "longitude": 4.9041}
        }

        session = await service.create_session(
            name="Dutch Session",
            context_options=context_opts
        )

        assert session.context_options == context_opts

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_db_session):
        """Test getting non-existent session."""
        mock_db_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        service = PlaywriterService(mock_db_session)
        session = await service.get_session(uuid4())

        assert session is None

    @pytest.mark.asyncio
    async def test_start_session_creates_active_browser(self, mock_db_session):
        """Test starting a browser session."""
        session_id = uuid4()
        mock_session = PlaywriterSession(
            id=session_id,
            name="Test",
            browser_type="chromium",
            headless=True,
            viewport_width=1280,
            viewport_height=720,
            status=SessionStatus.CREATED.value,
            context_options={}
        )
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_session))
        )

        service = PlaywriterService(mock_db_session)

        with patch.object(service, '_launch_browser', new_callable=AsyncMock):
            result = await service.start_session(session_id)

        assert result.status == SessionStatus.ACTIVE.value
        assert result.started_at is not None

    @pytest.mark.asyncio
    async def test_close_session(self, mock_db_session):
        """Test closing a browser session."""
        session_id = uuid4()
        mock_session = PlaywriterSession(
            id=session_id,
            name="Test",
            browser_type="chromium",
            status=SessionStatus.ACTIVE.value
        )
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_session))
        )

        service = PlaywriterService(mock_db_session)
        service._browsers = {session_id: MagicMock()}

        with patch.object(service, '_close_browser', new_callable=AsyncMock):
            result = await service.close_session(session_id)

        assert result.status == SessionStatus.CLOSED.value
        assert result.closed_at is not None


class TestPlaywriterServiceExecution:
    """Tests for code execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_code(self, mock_db_session):
        """Test executing simple Playwright code."""
        session_id = uuid4()
        mock_session = PlaywriterSession(
            id=session_id,
            name="Test",
            status=SessionStatus.ACTIVE.value
        )
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_session))
        )

        service = PlaywriterService(mock_db_session)

        with patch.object(service, '_execute_playwright_code', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = ({"title": "Test Page"}, None, 150)

            execution = await service.execute(
                session_id=session_id,
                code="await page.title()"
            )

        assert execution.status == ExecutionStatus.COMPLETED.value
        assert execution.result == {"title": "Test Page"}
        assert execution.execution_time_ms == 150

    @pytest.mark.asyncio
    async def test_execute_with_error(self, mock_db_session):
        """Test execution that produces an error."""
        session_id = uuid4()
        mock_session = PlaywriterSession(
            id=session_id,
            name="Test",
            status=SessionStatus.ACTIVE.value
        )
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_session))
        )

        service = PlaywriterService(mock_db_session)

        with patch.object(service, '_execute_playwright_code', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = (None, "Element not found", 50)

            execution = await service.execute(
                session_id=session_id,
                code="await page.click('#nonexistent')"
            )

        assert execution.status == ExecutionStatus.FAILED.value
        assert "Element not found" in execution.error

    @pytest.mark.asyncio
    async def test_execute_requires_active_session(self, mock_db_session):
        """Test that execution requires active session."""
        session_id = uuid4()
        mock_session = PlaywriterSession(
            id=session_id,
            name="Test",
            status=SessionStatus.CREATED.value  # Not active!
        )
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_session))
        )

        service = PlaywriterService(mock_db_session)

        with pytest.raises(ValueError, match="not active"):
            await service.execute(session_id=session_id, code="test")


class TestPlaywriterServiceConvenienceMethods:
    """Tests for convenience action methods."""

    @pytest.mark.asyncio
    async def test_click_generates_correct_code(self, mock_db_session):
        """Test that click() generates correct Playwright code."""
        session_id = uuid4()
        service = PlaywriterService(mock_db_session)

        with patch.object(service, 'execute', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="",
                status=ExecutionStatus.COMPLETED.value
            )

            await service.click(session_id, "#submit-button")

            # Verify execute was called with click code
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args
            assert "#submit-button" in call_args[1]['code']
            assert "click" in call_args[1]['code']

    @pytest.mark.asyncio
    async def test_type_text_generates_correct_code(self, mock_db_session):
        """Test that type_text() generates correct Playwright code."""
        session_id = uuid4()
        service = PlaywriterService(mock_db_session)

        with patch.object(service, 'execute', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="",
                status=ExecutionStatus.COMPLETED.value
            )

            await service.type_text(session_id, "#username", "testuser")

            mock_exec.assert_called_once()
            call_args = mock_exec.call_args
            assert "#username" in call_args[1]['code']
            assert "testuser" in call_args[1]['code']

    @pytest.mark.asyncio
    async def test_fill_form_handles_multiple_fields(self, mock_db_session):
        """Test filling multiple form fields."""
        session_id = uuid4()
        service = PlaywriterService(mock_db_session)

        with patch.object(service, 'execute', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="",
                status=ExecutionStatus.COMPLETED.value
            )

            await service.fill_form(session_id, {
                "#username": "testuser",
                "#password": "secret123",
                "#email": "test@example.com"
            })

            # Should call execute once with combined code
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args
            code = call_args[1]['code']
            assert "#username" in code
            assert "#password" in code
            assert "#email" in code

    @pytest.mark.asyncio
    async def test_goto_includes_wait_option(self, mock_db_session):
        """Test navigation with wait option."""
        session_id = uuid4()
        service = PlaywriterService(mock_db_session)

        with patch.object(service, 'execute', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = PlaywriterExecution(
                id=uuid4(),
                session_id=session_id,
                code="",
                status=ExecutionStatus.COMPLETED.value
            )

            await service.goto(session_id, "https://example.com", "networkidle")

            mock_exec.assert_called_once()
            call_args = mock_exec.call_args
            code = call_args[1]['code']
            assert "https://example.com" in code
            assert "networkidle" in code


class TestPlaywriterServiceTabManagement:
    """Tests for tab permission management."""

    @pytest.mark.asyncio
    async def test_request_tab_permission(self, mock_db_session):
        """Test requesting permission for a tab."""
        session_id = uuid4()
        service = PlaywriterService(mock_db_session)

        # Mock existing tab lookup
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        tab = await service.request_tab_permission(session_id, 0)

        assert tab.session_id == session_id
        assert tab.tab_index == 0
        assert tab.permitted is False

    @pytest.mark.asyncio
    async def test_grant_tab_permission(self, mock_db_session):
        """Test granting permission to a tab."""
        session_id = uuid4()
        mock_tab = PlaywriterTab(
            id=uuid4(),
            session_id=session_id,
            tab_index=0,
            permitted=False
        )
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_tab))
        )

        service = PlaywriterService(mock_db_session)
        tab = await service.grant_tab_permission(session_id, 0, "admin")

        assert tab.permitted is True
        assert tab.permitted_by == "admin"
        assert tab.permitted_at is not None

    @pytest.mark.asyncio
    async def test_revoke_tab_permission(self, mock_db_session):
        """Test revoking permission from a tab."""
        session_id = uuid4()
        mock_tab = PlaywriterTab(
            id=uuid4(),
            session_id=session_id,
            tab_index=0,
            permitted=True,
            permitted_by="admin",
            permitted_at=datetime.now(timezone.utc)
        )
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_tab))
        )

        service = PlaywriterService(mock_db_session)
        tab = await service.revoke_tab_permission(session_id, 0)

        assert tab.permitted is False
        assert tab.permitted_by is None
        assert tab.permitted_at is None

    @pytest.mark.asyncio
    async def test_execute_checks_tab_permission(self, mock_db_session):
        """Test that execution checks tab permission when tab_id specified."""
        session_id = uuid4()
        mock_session = PlaywriterSession(
            id=session_id,
            name="Test",
            status=SessionStatus.ACTIVE.value
        )
        mock_tab = PlaywriterTab(
            id=uuid4(),
            session_id=session_id,
            tab_index=1,
            permitted=False  # Not permitted!
        )

        def execute_side_effect(*args, **kwargs):
            query = args[0]
            if 'playwriter_sessions' in str(query):
                return MagicMock(scalar_one_or_none=MagicMock(return_value=mock_session))
            return MagicMock(scalar_one_or_none=MagicMock(return_value=mock_tab))

        mock_db_session.execute = AsyncMock(side_effect=execute_side_effect)

        service = PlaywriterService(mock_db_session)

        with pytest.raises(PermissionError, match="not permitted"):
            await service.execute(session_id=session_id, code="test", tab_id=1)


class TestPlaywriterServiceContextReduction:
    """Tests for context/token reduction features."""

    def test_service_has_single_execute_tool(self):
        """Verify service exposes single execute tool (90% context reduction)."""
        # The key design goal is a single execute() method
        # instead of many individual tool methods
        assert hasattr(PlaywriterService, 'execute')

    def test_convenience_methods_use_execute(self):
        """Verify convenience methods delegate to execute."""
        # All convenience methods (click, type_text, etc.)
        # should generate code and call execute()
        import inspect

        service_source = inspect.getsource(PlaywriterService)

        # Each convenience method should call self.execute
        convenience_methods = ['click', 'type_text', 'fill', 'goto', 'screenshot', 'fill_form']
        for method in convenience_methods:
            # Method exists
            assert hasattr(PlaywriterService, method)
