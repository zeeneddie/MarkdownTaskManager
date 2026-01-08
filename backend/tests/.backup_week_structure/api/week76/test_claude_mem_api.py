"""
Week 76: Claude-Mem API Tests

Tests for Claude-Mem REST API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient


@pytest.fixture
def mock_service():
    """Create mock ClaudeMemService."""
    with patch('app.api.claude_mem.ClaudeMemService') as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


# =============================================================================
# SESSION ENDPOINT TESTS
# =============================================================================

class TestSessionEndpoints:
    """Tests for session CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions - success."""
        session_id = str(uuid4())
        mock_service.create_session.return_value = {
            "id": session_id,
            "session_id": "test-session-001",
            "project_id": None,
            "title": "Test Session",
            "endless_mode": False,
            "token_budget": 4000,
            "compression_ratio": 0.1,
            "auto_tag": True,
            "session_data": {},
            "last_activity": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.post("/api/claude-mem/sessions", json={
            "session_id": "test-session-001",
            "title": "Test Session",
            "token_budget": 4000
        })

        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "test-session-001"

    @pytest.mark.asyncio
    async def test_create_session_duplicate_error(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions - duplicate error."""
        mock_service.create_session.return_value = {
            "error": "Session already exists"
        }

        response = test_client.post("/api/claude-mem/sessions", json={
            "session_id": "existing-session"
        })

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_session_success(self, test_client, mock_service):
        """Test GET /api/claude-mem/sessions/{session_id} - success."""
        session_id = str(uuid4())
        mock_service.get_session.return_value = {
            "id": session_id,
            "session_id": "test-session",
            "project_id": None,
            "title": "Test Session",
            "endless_mode": False,
            "token_budget": 4000,
            "compression_ratio": 0.1,
            "auto_tag": True,
            "session_data": {},
            "last_activity": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.get("/api/claude-mem/sessions/test-session")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, test_client, mock_service):
        """Test GET /api/claude-mem/sessions/{session_id} - not found."""
        mock_service.get_session.return_value = None

        response = test_client.get("/api/claude-mem/sessions/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_session_success(self, test_client, mock_service):
        """Test PATCH /api/claude-mem/sessions/{session_id} - success."""
        session_id = str(uuid4())
        mock_service.update_session.return_value = {
            "id": session_id,
            "session_id": "test-session",
            "project_id": None,
            "title": "Updated Title",
            "endless_mode": False,
            "token_budget": 8000,
            "compression_ratio": 0.1,
            "auto_tag": True,
            "session_data": {},
            "last_activity": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.patch("/api/claude-mem/sessions/test-session", json={
            "title": "Updated Title",
            "token_budget": 8000
        })

        assert response.status_code == 200
        data = response.json()
        assert data["token_budget"] == 8000

    @pytest.mark.asyncio
    async def test_delete_session_success(self, test_client, mock_service):
        """Test DELETE /api/claude-mem/sessions/{session_id} - success."""
        mock_service.delete_session.return_value = {
            "success": True,
            "session_id": "test-session"
        }

        response = test_client.delete("/api/claude-mem/sessions/test-session")

        assert response.status_code == 200


# =============================================================================
# ENDLESS MODE ENDPOINT TESTS
# =============================================================================

class TestEndlessModeEndpoints:
    """Tests for endless mode endpoints."""

    @pytest.mark.asyncio
    async def test_enable_endless_mode(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions/{session_id}/endless/enable."""
        session_id = str(uuid4())
        mock_service.enable_endless_mode.return_value = {
            "id": session_id,
            "session_id": "test-session",
            "project_id": None,
            "title": None,
            "endless_mode": True,
            "token_budget": 4000,
            "compression_ratio": 0.1,
            "auto_tag": True,
            "session_data": {},
            "last_activity": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/endless/enable")

        assert response.status_code == 200
        data = response.json()
        assert data["endless_mode"] is True

    @pytest.mark.asyncio
    async def test_disable_endless_mode(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions/{session_id}/endless/disable."""
        session_id = str(uuid4())
        mock_service.disable_endless_mode.return_value = {
            "id": session_id,
            "session_id": "test-session",
            "project_id": None,
            "title": None,
            "endless_mode": False,
            "token_budget": 4000,
            "compression_ratio": 0.1,
            "auto_tag": True,
            "session_data": {},
            "last_activity": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/endless/disable")

        assert response.status_code == 200
        data = response.json()
        assert data["endless_mode"] is False


# =============================================================================
# OBSERVATION ENDPOINT TESTS
# =============================================================================

class TestObservationEndpoints:
    """Tests for observation capture endpoints."""

    @pytest.mark.asyncio
    async def test_capture_observation_success(self, test_client, mock_service):
        """Test POST /api/claude-mem/observe - success."""
        obs_id = str(uuid4())
        mock_service.capture_observation.return_value = {
            "id": obs_id,
            "session_id": "test-session",
            "content": "Test observation",
            "tags": ["test"],
            "priority": "normal",
            "observation_type": "insight",
            "source_context": None,
            "related_files": [],
            "embedding_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.post("/api/claude-mem/observe", json={
            "session_id": "test-session",
            "content": "Test observation",
            "observation_type": "insight"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_capture_observation_with_priority(self, test_client, mock_service):
        """Test POST /api/claude-mem/observe with priority."""
        obs_id = str(uuid4())
        mock_service.capture_observation.return_value = {
            "id": obs_id,
            "session_id": "test-session",
            "content": "Critical bug found",
            "tags": ["bugfix"],
            "priority": "critical",
            "observation_type": "error",
            "source_context": None,
            "related_files": [],
            "embedding_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.post("/api/claude-mem/observe", json={
            "session_id": "test-session",
            "content": "Critical bug found",
            "observation_type": "error",
            "priority": "critical"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "critical"

    @pytest.mark.asyncio
    async def test_tag_observation_success(self, test_client, mock_service):
        """Test PATCH /api/claude-mem/observations/{id}/tags."""
        obs_id = uuid4()
        mock_service.tag_observation.return_value = {
            "id": str(obs_id),
            "session_id": "test-session",
            "content": "Test",
            "tags": ["new-tag", "another"],
            "priority": "normal",
            "observation_type": "insight",
            "source_context": None,
            "related_files": [],
            "embedding_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = test_client.patch(f"/api/claude-mem/observations/{obs_id}/tags", json={
            "tags": ["new-tag", "another"],
            "replace": False
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_observations_by_tags(self, test_client, mock_service):
        """Test GET /api/claude-mem/sessions/{session_id}/observations."""
        mock_service.get_observations_by_tags.return_value = [
            {"id": str(uuid4()), "content": "Test", "tags": ["bugfix"]}
        ]

        response = test_client.get("/api/claude-mem/sessions/test-session/observations?tags=bugfix")

        assert response.status_code == 200


# =============================================================================
# CONTEXT WINDOW ENDPOINT TESTS
# =============================================================================

class TestContextWindowEndpoints:
    """Tests for context window endpoints."""

    @pytest.mark.asyncio
    async def test_get_context_window_success(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions/{session_id}/context."""
        context_id = str(uuid4())
        mock_service.get_context_window.return_value = {
            "session_id": "test-session",
            "context_text": "## Session Context\n\nTest observation",
            "token_count": 50,
            "token_budget": 4000,
            "observations_included": 1,
            "summaries_included": 0,
            "strategy": "recent",
            "context_id": context_id
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/context", json={
            "strategy": "recent",
            "include_summaries": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert "context_text" in data

    @pytest.mark.asyncio
    async def test_get_context_window_priority_strategy(self, test_client, mock_service):
        """Test context window with priority strategy."""
        context_id = str(uuid4())
        mock_service.get_context_window.return_value = {
            "session_id": "test-session",
            "context_text": "## Session Context\n\n[Critical] Test",
            "token_count": 50,
            "token_budget": 4000,
            "observations_included": 1,
            "summaries_included": 0,
            "strategy": "priority",
            "context_id": context_id
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/context", json={
            "strategy": "priority"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["strategy"] == "priority"


# =============================================================================
# SEARCH ENDPOINT TESTS
# =============================================================================

class TestSearchEndpoints:
    """Tests for search endpoints."""

    @pytest.mark.asyncio
    async def test_search_memories_success(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions/{session_id}/search."""
        mock_service.search_memories.return_value = {
            "session_id": "test-session",
            "query": "authentication",
            "results_count": 2,
            "results": [
                {"id": str(uuid4()), "content": "Auth bug fixed"},
                {"id": str(uuid4()), "content": "Auth improvement"}
            ]
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/search", json={
            "query": "authentication",
            "use_fts": True,
            "limit": 20
        })

        assert response.status_code == 200
        data = response.json()
        assert data["results_count"] == 2

    @pytest.mark.asyncio
    async def test_search_memories_with_filters(self, test_client, mock_service):
        """Test search with tag and priority filters."""
        mock_service.search_memories.return_value = {
            "session_id": "test-session",
            "query": "bug",
            "results_count": 1,
            "results": [{"id": str(uuid4()), "content": "Bug found"}]
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/search", json={
            "query": "bug",
            "tags_filter": ["bugfix"],
            "priority_filter": "high"
        })

        assert response.status_code == 200


# =============================================================================
# COMPRESSION ENDPOINT TESTS
# =============================================================================

class TestCompressionEndpoints:
    """Tests for compression endpoints."""

    @pytest.mark.asyncio
    async def test_compress_memories_success(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions/{session_id}/compress."""
        mock_service.compress_memories.return_value = {
            "session_id": "test-session",
            "observations_compressed": 10,
            "summaries_created": 2,
            "tokens_saved": 500
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/compress", json={
            "older_than_hours": 24
        })

        assert response.status_code == 200
        data = response.json()
        assert data["observations_compressed"] == 10


# =============================================================================
# INJECT CONTEXT ENDPOINT TESTS
# =============================================================================

class TestInjectContextEndpoints:
    """Tests for context injection endpoints."""

    @pytest.mark.asyncio
    async def test_inject_context_success(self, test_client, mock_service):
        """Test POST /api/claude-mem/sessions/{session_id}/inject."""
        mock_service.inject_context.return_value = {
            "session_id": "test-session",
            "original_prompt": "Help me debug this issue",
            "enhanced_prompt": "[Context]\nPrevious debug session...\n\n[User Prompt]\nHelp me debug this issue",
            "context_tokens": 100
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/inject", json={
            "prompt": "Help me debug this issue"
        })

        assert response.status_code == 200
        data = response.json()
        assert "enhanced_prompt" in data

    @pytest.mark.asyncio
    async def test_inject_context_endless_mode_required(self, test_client, mock_service):
        """Test inject context fails when endless mode not enabled."""
        mock_service.inject_context.return_value = {
            "error": "Endless mode not enabled for this session"
        }

        response = test_client.post("/api/claude-mem/sessions/test-session/inject", json={
            "prompt": "Test prompt"
        })

        assert response.status_code == 400


# =============================================================================
# STATISTICS ENDPOINT TESTS
# =============================================================================

class TestStatisticsEndpoints:
    """Tests for statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_session_statistics_success(self, test_client, mock_service):
        """Test GET /api/claude-mem/sessions/{session_id}/statistics."""
        mock_service.get_session_statistics.return_value = {
            "session_id": "test-session",
            "session_data": {},
            "observation_count": 50,
            "summary_count": 5,
            "total_tokens_estimated": 2500,
            "tag_distribution": {"bugfix": 10, "feature": 20},
            "priority_distribution": {"normal": 40, "high": 10},
            "type_distribution": {"insight": 30, "decision": 20},
            "endless_mode": False,
            "token_budget": 4000
        }

        response = test_client.get("/api/claude-mem/sessions/test-session/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["observation_count"] == 50

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, test_client, mock_service):
        """Test GET /api/claude-mem/dashboard."""
        mock_service.get_dashboard_data.return_value = {
            "project_id": None,
            "total_sessions": 5,
            "endless_sessions": 2,
            "total_observations": 100,
            "sessions": [
                {"session_id": "session-1", "endless_mode": False},
                {"session_id": "session-2", "endless_mode": True}
            ]
        }

        response = test_client.get("/api/claude-mem/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 5


# =============================================================================
# CLEANUP ENDPOINT TESTS
# =============================================================================

class TestCleanupEndpoints:
    """Tests for cleanup endpoints."""

    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, test_client, mock_service):
        """Test DELETE /api/claude-mem/cleanup."""
        mock_service.cleanup_old_sessions.return_value = {
            "deleted_sessions": 3,
            "days_inactive": 30
        }

        response = test_client.delete("/api/claude-mem/cleanup?days_inactive=30")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_sessions"] == 3


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestValidation:
    """Tests for request validation."""

    @pytest.mark.asyncio
    async def test_invalid_token_budget_too_low(self, test_client, mock_service):
        """Test validation rejects token budget below minimum."""
        response = test_client.post("/api/claude-mem/sessions", json={
            "session_id": "test",
            "token_budget": 100  # Below minimum of 500
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_token_budget_too_high(self, test_client, mock_service):
        """Test validation rejects token budget above maximum."""
        response = test_client.post("/api/claude-mem/sessions", json={
            "session_id": "test",
            "token_budget": 50000  # Above maximum of 32000
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_priority_value(self, test_client, mock_service):
        """Test validation rejects invalid priority value."""
        response = test_client.post("/api/claude-mem/observe", json={
            "session_id": "test",
            "content": "Test",
            "priority": "invalid"  # Not in allowed values
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_strategy_value(self, test_client, mock_service):
        """Test validation rejects invalid strategy value."""
        response = test_client.post("/api/claude-mem/sessions/test/context", json={
            "strategy": "invalid"  # Not in allowed values
        })

        assert response.status_code == 422
