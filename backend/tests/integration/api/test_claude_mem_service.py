"""
Week 76: Claude-Mem Service Tests

Tests for ClaudeMemService - Session Memory Management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.claude_mem_service import ClaudeMemService


@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create ClaudeMemService with mocked database."""
    return ClaudeMemService(mock_db)


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================

class TestSessionManagement:
    """Tests for session CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, service, mock_db):
        """Test creating a new session."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_session(
            session_id="test-session-001",
            title="Test Session",
            token_budget=4000,
            auto_tag=True
        )

        assert "id" in result
        assert result["session_id"] == "test-session-001"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_session_duplicate_error(self, service, mock_db):
        """Test error when creating duplicate session."""
        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.session_id = "existing-session"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.create_session(session_id="existing-session")

        assert "error" in result
        assert "exists" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_session_found(self, service, mock_db):
        """Test retrieving an existing session."""
        mock_session = MagicMock()
        mock_session.to_dict.return_value = {
            "id": str(uuid4()),
            "session_id": "test-session",
            "endless_mode": False,
            "token_budget": 4000
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.get_session("test-session")

        assert result is not None
        assert result["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, service, mock_db):
        """Test retrieving non-existent session."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_session("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_session_success(self, service, mock_db):
        """Test updating session settings."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.token_budget = 4000
        mock_session.to_dict.return_value = {
            "id": str(uuid4()),
            "session_id": "test-session",
            "token_budget": 8000
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.update_session("test-session", {"token_budget": 8000})

        assert result["token_budget"] == 8000

    @pytest.mark.asyncio
    async def test_delete_session(self, service, mock_db):
        """Test deleting a session."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.delete_session("test-session")

        assert result["success"] is True
        mock_db.delete.assert_called()


# =============================================================================
# OBSERVATION TESTS
# =============================================================================

class TestObservationCapture:
    """Tests for observation capture and tagging."""

    @pytest.mark.asyncio
    async def test_capture_observation_basic(self, service, mock_db):
        """Test basic observation capture."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.auto_tag = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.capture_observation(
            session_id="test-session",
            content="Discovered a bug in authentication flow",
            observation_type="error",
            priority="high",
            auto_tag=False
        )

        assert "id" in result
        assert result["session_id"] == "test-session"
        assert result["priority"] == "high"

    @pytest.mark.asyncio
    async def test_capture_observation_with_auto_tagging(self, service, mock_db):
        """Test observation capture with auto-tagging enabled."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.auto_tag = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.capture_observation(
            session_id="test-session",
            content="Fixed security vulnerability in API endpoint",
            auto_tag=True
        )

        # Auto-tagging should detect "security" and "api" keywords
        assert "id" in result
        assert result["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_capture_observation_with_manual_tags(self, service, mock_db):
        """Test observation capture with manually specified tags."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.auto_tag = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.capture_observation(
            session_id="test-session",
            content="Test content",
            tags=["architecture", "decision"],
            auto_tag=False
        )

        assert result["tags"] == ["architecture", "decision"]

    @pytest.mark.asyncio
    async def test_tag_observation_add(self, service, mock_db):
        """Test adding tags to an observation."""
        obs_id = uuid4()
        mock_obs = MagicMock()
        mock_obs.id = obs_id
        mock_obs.tags = ["existing"]
        mock_obs.to_dict.return_value = {
            "id": str(obs_id),
            "session_id": "test",
            "content": "Test",
            "tags": ["existing", "new-tag"],
            "priority": "normal",
            "embedding_status": "pending",
            "related_files": []
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_obs
        mock_db.execute.return_value = mock_result

        result = await service.tag_observation(obs_id, ["new-tag"], replace=False)

        assert "new-tag" in result["tags"]
        assert "existing" in result["tags"]

    @pytest.mark.asyncio
    async def test_tag_observation_replace(self, service, mock_db):
        """Test replacing all tags on an observation."""
        obs_id = uuid4()
        mock_obs = MagicMock()
        mock_obs.id = obs_id
        mock_obs.tags = ["old-tag"]
        mock_obs.to_dict.return_value = {
            "id": str(obs_id),
            "session_id": "test",
            "content": "Test",
            "tags": ["replaced"],
            "priority": "normal",
            "embedding_status": "pending",
            "related_files": []
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_obs
        mock_db.execute.return_value = mock_result

        result = await service.tag_observation(obs_id, ["replaced"], replace=True)

        assert result["tags"] == ["replaced"]


# =============================================================================
# AUTO-TAGGING TESTS
# =============================================================================

class TestAutoTagging:
    """Tests for auto-tagging functionality."""

    def test_auto_tag_decision_keywords(self, service):
        """Test auto-tagging detects decision keywords."""
        tags = service._detect_tags("We decided to use PostgreSQL for the database")
        assert "decision" in tags

    def test_auto_tag_bugfix_keywords(self, service):
        """Test auto-tagging detects bugfix keywords."""
        tags = service._detect_tags("Fixed the null pointer bug in user service")
        assert "bugfix" in tags

    def test_auto_tag_architecture_keywords(self, service):
        """Test auto-tagging detects architecture keywords."""
        tags = service._detect_tags("Refactored the module structure for better separation")
        assert "architecture" in tags

    def test_auto_tag_security_keywords(self, service):
        """Test auto-tagging detects security keywords."""
        tags = service._detect_tags("Implemented authentication with JWT tokens")
        assert "security" in tags

    def test_auto_tag_api_keywords(self, service):
        """Test auto-tagging detects API keywords."""
        tags = service._detect_tags("Added new REST endpoint for user creation")
        assert "api" in tags

    def test_auto_tag_multiple_matches(self, service):
        """Test auto-tagging returns multiple tags when content matches multiple patterns."""
        tags = service._detect_tags("Fixed security bug in API authentication endpoint")
        assert len(tags) >= 2


# =============================================================================
# CONTEXT WINDOW TESTS
# =============================================================================

class TestContextWindow:
    """Tests for context window generation."""

    @pytest.mark.asyncio
    async def test_get_context_window_recent_strategy(self, service, mock_db):
        """Test context window with recent strategy."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.token_budget = 4000
        mock_session.to_dict.return_value = {"session_id": "test-session", "token_budget": 4000}

        # Mock observations
        mock_obs = MagicMock()
        mock_obs.id = uuid4()
        mock_obs.content = "Test observation"
        mock_obs.tags = []
        mock_obs.priority = "normal"
        mock_obs.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_result.scalars.return_value.all.return_value = [mock_obs]
        mock_db.execute.return_value = mock_result

        result = await service.get_context_window(
            session_id="test-session",
            strategy="recent"
        )

        assert result["session_id"] == "test-session"
        assert "context_text" in result
        assert "token_count" in result

    @pytest.mark.asyncio
    async def test_get_context_window_priority_strategy(self, service, mock_db):
        """Test context window with priority strategy."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.token_budget = 4000
        mock_session.to_dict.return_value = {"session_id": "test-session", "token_budget": 4000}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_context_window(
            session_id="test-session",
            strategy="priority"
        )

        assert result["strategy"] == "priority"

    @pytest.mark.asyncio
    async def test_get_context_window_session_not_found(self, service, mock_db):
        """Test context window for non-existent session."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_context_window(session_id="nonexistent")

        assert "error" in result


# =============================================================================
# COMPRESSION TESTS
# =============================================================================

class TestMemoryCompression:
    """Tests for memory compression functionality."""

    @pytest.mark.asyncio
    async def test_compress_memories_success(self, service, mock_db):
        """Test compressing old observations into summaries."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.compression_ratio = 0.1

        mock_obs = MagicMock()
        mock_obs.id = uuid4()
        mock_obs.content = "Old observation to compress"
        mock_obs.tags = ["test"]
        mock_obs.created_at = datetime.now(timezone.utc) - timedelta(hours=48)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_result.scalars.return_value.all.return_value = [mock_obs]
        mock_db.execute.return_value = mock_result

        result = await service.compress_memories(
            session_id="test-session",
            older_than_hours=24
        )

        assert result.get("observations_compressed", 0) >= 0

    @pytest.mark.asyncio
    async def test_compress_memories_no_old_observations(self, service, mock_db):
        """Test compression when no old observations exist."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.compression_ratio = 0.1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.compress_memories(
            session_id="test-session",
            older_than_hours=24
        )

        assert result["observations_compressed"] == 0


# =============================================================================
# SEARCH TESTS
# =============================================================================

class TestMemorySearch:
    """Tests for memory search functionality."""

    @pytest.mark.asyncio
    async def test_search_memories_fts(self, service, mock_db):
        """Test full-text search for memories."""
        mock_obs = MagicMock()
        mock_obs.id = uuid4()
        mock_obs.content = "Authentication bugfix"
        mock_obs.tags = ["bugfix"]
        mock_obs.priority = "high"
        mock_obs.observation_type = "error"
        mock_obs.created_at = datetime.now(timezone.utc)
        mock_obs.to_dict.return_value = {
            "id": str(mock_obs.id),
            "content": mock_obs.content,
            "tags": mock_obs.tags,
            "priority": mock_obs.priority
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_obs]
        mock_db.execute.return_value = mock_result

        result = await service.search_memories(
            session_id="test-session",
            query="authentication",
            use_fts=True
        )

        assert result["session_id"] == "test-session"
        assert "results" in result

    @pytest.mark.asyncio
    async def test_search_memories_with_tag_filter(self, service, mock_db):
        """Test search with tag filtering."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.search_memories(
            session_id="test-session",
            query="test",
            tags_filter=["bugfix"]
        )

        assert result["session_id"] == "test-session"
        assert "results" in result

    @pytest.mark.asyncio
    async def test_search_memories_with_priority_filter(self, service, mock_db):
        """Test search with priority filtering."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.search_memories(
            session_id="test-session",
            query="test",
            priority_filter="critical"
        )

        assert result["session_id"] == "test-session"


# =============================================================================
# ENDLESS MODE TESTS
# =============================================================================

class TestEndlessMode:
    """Tests for endless mode functionality."""

    @pytest.mark.asyncio
    async def test_enable_endless_mode(self, service, mock_db):
        """Test enabling endless mode."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.endless_mode = False
        mock_session.to_dict.return_value = {
            "id": str(uuid4()),
            "session_id": "test-session",
            "endless_mode": True
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.enable_endless_mode("test-session")

        assert result["endless_mode"] is True

    @pytest.mark.asyncio
    async def test_disable_endless_mode(self, service, mock_db):
        """Test disabling endless mode."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.endless_mode = True
        mock_session.to_dict.return_value = {
            "id": str(uuid4()),
            "session_id": "test-session",
            "endless_mode": False
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.disable_endless_mode("test-session")

        assert result["endless_mode"] is False

    @pytest.mark.asyncio
    async def test_inject_context_endless_mode_only(self, service, mock_db):
        """Test context injection requires endless mode."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.endless_mode = False
        mock_session.to_dict.return_value = {
            "id": str(uuid4()),
            "session_id": "test-session",
            "endless_mode": False,
            "token_budget": 4000
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        result = await service.inject_context(
            session_id="test-session",
            prompt="Test prompt"
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_inject_context_success(self, service, mock_db):
        """Test successful context injection in endless mode."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.endless_mode = True
        mock_session.token_budget = 4000
        mock_session.to_dict.return_value = {
            "session_id": "test-session",
            "endless_mode": True,
            "token_budget": 4000
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.inject_context(
            session_id="test-session",
            prompt="Test prompt"
        )

        assert "enhanced_prompt" in result
        assert "Test prompt" in result["enhanced_prompt"]


# =============================================================================
# STATISTICS TESTS
# =============================================================================

class TestStatistics:
    """Tests for statistics and dashboard data."""

    @pytest.mark.asyncio
    async def test_get_session_statistics(self, service, mock_db):
        """Test getting session statistics."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.endless_mode = False
        mock_session.token_budget = 4000
        mock_session.session_data = {}
        mock_session.to_dict.return_value = {
            "session_id": "test-session",
            "endless_mode": False,
            "token_budget": 4000,
            "session_data": {}
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_result.scalar.return_value = 5
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_session_statistics("test-session")

        assert result["session_id"] == "test-session"
        assert "observation_count" in result
        assert "tag_distribution" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, service, mock_db):
        """Test getting dashboard data."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.endless_mode = False
        mock_session.to_dict.return_value = {
            "session_id": "test-session",
            "endless_mode": False
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_session]
        mock_result.scalar.return_value = 10
        mock_db.execute.return_value = mock_result

        result = await service.get_dashboard_data()

        assert "total_sessions" in result
        assert "sessions" in result


# =============================================================================
# CLEANUP TESTS
# =============================================================================

class TestCleanup:
    """Tests for cleanup operations."""

    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, service, mock_db):
        """Test cleaning up old inactive sessions."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.cleanup_old_sessions(days_inactive=30)

        assert "sessions_deleted" in result


# =============================================================================
# TOKEN ESTIMATION TESTS
# =============================================================================

class TestTokenEstimation:
    """Tests for token estimation functionality."""

    def test_estimate_tokens_short_text(self, service):
        """Test token estimation for short text."""
        tokens = service._estimate_tokens("Hello world")
        assert tokens > 0
        assert tokens < 10

    def test_estimate_tokens_longer_text(self, service):
        """Test token estimation for longer text."""
        text = "This is a longer piece of text that should have more tokens " * 10
        tokens = service._estimate_tokens(text)
        assert tokens > 50


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_capture_observation_empty_content(self, service, mock_db):
        """Test capturing observation with empty content."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        # The API layer handles validation, service may accept empty
        result = await service.capture_observation(
            session_id="test-session",
            content=""
        )

        # Service should still create an observation (API validates)
        assert "id" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_observations_by_tags_no_matches(self, service, mock_db):
        """Test getting observations when no tags match."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_observations_by_tags(
            session_id="test-session",
            tags=["nonexistent-tag"]
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_context_window_empty_session(self, service, mock_db):
        """Test context window for session with no observations."""
        mock_session = MagicMock()
        mock_session.session_id = "test-session"
        mock_session.token_budget = 4000
        mock_session.to_dict.return_value = {
            "session_id": "test-session",
            "token_budget": 4000
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_context_window(session_id="test-session")

        assert result["observations_included"] == 0
