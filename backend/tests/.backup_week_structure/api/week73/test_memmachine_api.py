"""
Week 73: MemMachine API Tests

Tests for MemMachine Agent Memory REST API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app


class TestMemMachineHealthEndpoint:
    """Tests for /api/memmachine/health endpoint."""

    def test_health_endpoint(self):
        """Test health check returns expected response."""
        client = TestClient(app)
        response = client.get("/api/memmachine/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "memmachine"
        assert data["version"] == "1.0.0"
        assert "conversation_history" in data["features"]


class TestSessionEndpoints:
    """Tests for session management endpoints."""

    def test_create_session(self):
        """Test creating a new session."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_session = AsyncMock(return_value={
                "id": str(uuid4()),
                "agent_id": "felix",
                "project_id": None,
                "context": {"task": "test"},
                "created_at": "2024-01-01T00:00:00",
                "last_activity": "2024-01-01T00:00:00",
                "message_count": 0,
                "memory_count": 0,
                "status": "active"
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/memmachine/sessions",
                json={
                    "agent_id": "felix",
                    "context": {"task": "test"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "felix"
            assert data["status"] == "active"

    def test_end_session(self):
        """Test ending a session."""
        client = TestClient(app)
        session_id = str(uuid4())

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.end_session = AsyncMock(return_value={
                "session_id": session_id,
                "status": "completed",
                "duration_seconds": 120.5
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                f"/api/memmachine/sessions/{session_id}/end",
                json={"summary": "Test session completed"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"

    def test_get_session(self):
        """Test getting session details."""
        client = TestClient(app)
        session_id = str(uuid4())

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_session = AsyncMock(return_value={
                "id": session_id,
                "agent_id": "felix",
                "status": "active"
            })
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/memmachine/sessions/{session_id}")

            assert response.status_code == 200

    def test_get_nonexistent_session(self):
        """Test getting nonexistent session."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_session = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            response = client.get("/api/memmachine/sessions/nonexistent")

            assert response.status_code == 404


class TestMemoryStorageEndpoints:
    """Tests for memory storage endpoints."""

    def test_store_memory(self):
        """Test storing a memory."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.store_memory = AsyncMock(return_value={
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "agent_id": "felix",
                "content": "Test memory",
                "memory_type": "fact",
                "priority": "medium",
                "tags": [],
                "metadata": {},
                "created_at": "2024-01-01T00:00:00",
                "access_count": 0
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/memmachine/memories",
                json={
                    "session_id": str(uuid4()),
                    "agent_id": "felix",
                    "content": "Test memory",
                    "memory_type": "fact"
                }
            )

            assert response.status_code == 200

    def test_store_conversation(self):
        """Test storing a conversation message."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.store_conversation = AsyncMock(return_value={
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "agent_id": "felix",
                "content": "Hello",
                "memory_type": "conversation",
                "metadata": {"role": "user"}
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/memmachine/conversations",
                json={
                    "session_id": str(uuid4()),
                    "agent_id": "felix",
                    "role": "user",
                    "content": "Hello"
                }
            )

            assert response.status_code == 200


class TestMemoryRetrievalEndpoints:
    """Tests for memory retrieval endpoints."""

    def test_get_agent_memories(self):
        """Test getting agent memories."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_agent_memories = AsyncMock(return_value=[
                {"id": str(uuid4()), "content": "Memory 1"},
                {"id": str(uuid4()), "content": "Memory 2"}
            ])
            mock_service_class.return_value = mock_service

            response = client.get("/api/memmachine/memories/felix")

            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "felix"
            assert data["count"] == 2

    def test_get_conversation_history(self):
        """Test getting conversation history."""
        client = TestClient(app)
        session_id = str(uuid4())

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_conversation_history = AsyncMock(return_value=[
                {"content": "Hello", "metadata": {"role": "user"}},
                {"content": "Hi there!", "metadata": {"role": "assistant"}}
            ])
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/memmachine/conversations/{session_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2

    def test_search_memories(self):
        """Test searching memories."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.search_memories = AsyncMock(return_value=[
                {"content": "Python is great", "relevance": 0.85}
            ])
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/memmachine/search",
                json={
                    "agent_id": "felix",
                    "query": "Python"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "Python"


class TestLearningEndpoints:
    """Tests for learning endpoints."""

    def test_learn_fact(self):
        """Test learning a fact."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.learn_fact = AsyncMock(return_value={
                "id": str(uuid4()),
                "content": "The codebase uses FastAPI",
                "memory_type": "fact"
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/memmachine/learn",
                json={
                    "agent_id": "felix",
                    "session_id": str(uuid4()),
                    "fact": "The codebase uses FastAPI",
                    "source": "code_analysis",
                    "confidence": 0.95
                }
            )

            assert response.status_code == 200

    def test_store_preference(self):
        """Test storing a preference."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.store_preference = AsyncMock(return_value={
                "id": str(uuid4()),
                "content": "language: python",
                "memory_type": "preference"
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/memmachine/preferences",
                json={
                    "agent_id": "felix",
                    "session_id": str(uuid4()),
                    "preference_key": "language",
                    "preference_value": "python"
                }
            )

            assert response.status_code == 200

    def test_get_preferences(self):
        """Test getting preferences."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_preferences = AsyncMock(return_value={
                "language": "python",
                "verbosity": "high"
            })
            mock_service_class.return_value = mock_service

            response = client.get("/api/memmachine/preferences/felix")

            assert response.status_code == 200
            data = response.json()
            assert data["preferences"]["language"] == "python"


class TestMemoryManagementEndpoints:
    """Tests for memory management endpoints."""

    def test_delete_memory(self):
        """Test deleting a memory."""
        client = TestClient(app)
        memory_id = str(uuid4())

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.forget_memory = AsyncMock(return_value={
                "status": "success",
                "message": f"Memory {memory_id} deleted"
            })
            mock_service_class.return_value = mock_service

            response = client.delete(f"/api/memmachine/memories/{memory_id}")

            assert response.status_code == 200

    def test_delete_nonexistent_memory(self):
        """Test deleting nonexistent memory."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.forget_memory = AsyncMock(return_value={
                "status": "error",
                "message": "Memory not found"
            })
            mock_service_class.return_value = mock_service

            response = client.delete("/api/memmachine/memories/nonexistent")

            assert response.status_code == 404

    def test_compress_memories(self):
        """Test compressing memories."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.compress_memories = AsyncMock(return_value={
                "status": "success",
                "compressed_count": 50,
                "remaining_count": 51
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/memmachine/compress",
                json={
                    "agent_id": "felix",
                    "memory_type": "conversation"
                }
            )

            assert response.status_code == 200

    def test_cleanup_expired(self):
        """Test cleaning up expired memories."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.cleanup_expired = AsyncMock(return_value={
                "status": "success",
                "removed_count": 10
            })
            mock_service_class.return_value = mock_service

            response = client.post("/api/memmachine/cleanup")

            assert response.status_code == 200


class TestStatisticsEndpoints:
    """Tests for statistics endpoints."""

    def test_get_agent_stats(self):
        """Test getting agent stats."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_agent_stats = AsyncMock(return_value={
                "agent_id": "felix",
                "total_memories": 100,
                "by_type": {"fact": 50, "preference": 20},
                "by_priority": {"high": 30, "medium": 50}
            })
            mock_service_class.return_value = mock_service

            response = client.get("/api/memmachine/stats/felix")

            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "felix"

    def test_get_system_status(self):
        """Test getting system status."""
        client = TestClient(app)

        with patch("app.api.memmachine.MemMachineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_system_status = AsyncMock(return_value={
                "status": "healthy",
                "total_sessions": 10,
                "active_sessions": 3,
                "total_memories": 500,
                "unique_agents": 5,
                "features": ["conversation_history"],
                "version": "1.0.0"
            })
            mock_service_class.return_value = mock_service

            response = client.get("/api/memmachine/status")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
