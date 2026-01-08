"""
Week 72: AnyTool API Tests

Tests for AnyTool Universal Tool Calling REST API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


class TestAnyToolHealthEndpoint:
    """Tests for /api/anytool/health endpoint."""

    def test_health_endpoint_sync(self):
        """Test health check returns expected response."""
        client = TestClient(app)
        response = client.get("/api/anytool/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "anytool"
        assert data["version"] == "1.0.0"
        assert "multi_stage_filtering" in data["features"]


class TestDiscoverEndpoint:
    """Tests for /api/anytool/discover endpoint."""

    def test_discover_valid_request(self):
        """Test discover with valid request."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.discover_tools = AsyncMock(return_value=[
                {
                    "tool": {"id": str(uuid4()), "tool_name": "read_file"},
                    "semantic_score": 0.85,
                    "quality_score": 0.90,
                    "final_score": 0.87
                }
            ])
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/discover",
                json={
                    "query": "read file contents",
                    "max_results": 5
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "read file contents"

    def test_discover_with_context(self):
        """Test discover with context provided."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.discover_tools = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/discover",
                json={
                    "query": "analyze code",
                    "context": {"task_type": "code_analysis", "preferred_category": "code"},
                    "max_results": 10
                }
            )

            assert response.status_code == 200

    def test_discover_empty_results(self):
        """Test discover returns empty list when no tools match."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.discover_tools = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/discover",
                json={
                    "query": "nonexistent tool xyz",
                    "max_results": 5
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_found"] == 0
            assert data["tools"] == []

    def test_discover_invalid_max_results(self):
        """Test discover with invalid max_results."""
        client = TestClient(app)
        response = client.post(
            "/api/anytool/discover",
            json={
                "query": "read file",
                "max_results": 100  # Over limit of 50
            }
        )

        assert response.status_code == 422  # Validation error

    def test_discover_missing_query(self):
        """Test discover without query field."""
        client = TestClient(app)
        response = client.post(
            "/api/anytool/discover",
            json={
                "max_results": 5
            }
        )

        assert response.status_code == 422


class TestExecuteEndpoint:
    """Tests for /api/anytool/execute endpoint."""

    def test_execute_success(self):
        """Test execute with successful tool execution."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.execute_tool = AsyncMock(return_value={
                "status": "success",
                "result": "File contents here",
                "tool_used": "read_file",
                "selection_score": 0.95,
                "failover_attempts": 0,
                "latency_ms": 150
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/execute",
                json={
                    "query": "read file",
                    "params": {"file_path": "/test.txt"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_execute_with_failover(self):
        """Test execute with failover attempts."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.execute_tool = AsyncMock(return_value={
                "status": "success",
                "result": "Success after retry",
                "tool_used": "backup_tool",
                "selection_score": 0.80,
                "failover_attempts": 2,
                "latency_ms": 500
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/execute",
                json={
                    "query": "read file",
                    "params": {"file_path": "/test.txt"},
                    "fallback_enabled": True
                }
            )

            assert response.status_code == 200

    def test_execute_failure(self):
        """Test execute when all tools fail."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.execute_tool = AsyncMock(return_value={
                "status": "failed",
                "error": "All tool execution attempts failed",
                "latency_ms": 1000
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/execute",
                json={
                    "query": "failing operation",
                    "params": {}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"

    def test_execute_with_agent_id(self):
        """Test execute with agent_id specified."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.execute_tool = AsyncMock(return_value={
                "status": "success",
                "result": "Done",
                "latency_ms": 100
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/execute",
                json={
                    "query": "analyze code",
                    "params": {"file": "test.py"},
                    "agent_id": "felix"
                }
            )

            assert response.status_code == 200

    def test_execute_missing_params(self):
        """Test execute without params field."""
        client = TestClient(app)
        response = client.post(
            "/api/anytool/execute",
            json={
                "query": "do something"
            }
        )

        assert response.status_code == 422


class TestReliabilityEndpoint:
    """Tests for /api/anytool/reliability endpoint."""

    def test_reliability_default_hours(self):
        """Test reliability stats with default time period."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_reliability_stats = AsyncMock(return_value={
                "period_hours": 24,
                "tools": {
                    str(uuid4()): {
                        "success": 80,
                        "failed": 20,
                        "total": 100,
                        "success_rate": 0.8
                    }
                },
                "total_executions": 100
            })
            mock_service_class.return_value = mock_service

            response = client.get("/api/anytool/reliability")

            assert response.status_code == 200
            data = response.json()
            assert data["period_hours"] == 24

    def test_reliability_custom_hours(self):
        """Test reliability stats with custom time period."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_reliability_stats = AsyncMock(return_value={
                "period_hours": 48,
                "tools": {},
                "total_executions": 0
            })
            mock_service_class.return_value = mock_service

            response = client.get("/api/anytool/reliability?hours=48")

            assert response.status_code == 200

    def test_reliability_with_tool_id(self):
        """Test reliability stats filtered by tool_id."""
        client = TestClient(app)
        tool_id = uuid4()

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_reliability_stats = AsyncMock(return_value={
                "period_hours": 24,
                "tools": {
                    str(tool_id): {"success": 50, "failed": 5, "success_rate": 0.91}
                },
                "total_executions": 55
            })
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/anytool/reliability?tool_id={tool_id}")

            assert response.status_code == 200

    def test_reliability_invalid_hours(self):
        """Test reliability with invalid hours value."""
        client = TestClient(app)
        response = client.get("/api/anytool/reliability?hours=200")

        assert response.status_code == 422  # Over limit of 168


class TestSuggestionsEndpoint:
    """Tests for /api/anytool/suggestions endpoint."""

    def test_suggestions_basic(self):
        """Test getting tool suggestions."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_tool_suggestions = AsyncMock(return_value=[
                {"tool_name": "popular_tool", "usage_count": 100, "success_rate": 0.95},
                {"tool_name": "another_tool", "usage_count": 50, "success_rate": 0.90}
            ])
            mock_service_class.return_value = mock_service

            response = client.get("/api/anytool/suggestions?task_type=code_analysis")

            assert response.status_code == 200
            data = response.json()
            assert data["task_type"] == "code_analysis"

    def test_suggestions_with_agent(self):
        """Test suggestions filtered by agent."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_tool_suggestions = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = client.get(
                "/api/anytool/suggestions?task_type=file_operations&agent_id=felix"
            )

            assert response.status_code == 200

    def test_suggestions_custom_limit(self):
        """Test suggestions with custom limit."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_tool_suggestions = AsyncMock(return_value=[
                {"tool_name": "tool1", "usage_count": 10, "success_rate": 0.9}
            ])
            mock_service_class.return_value = mock_service

            response = client.get("/api/anytool/suggestions?task_type=test&limit=1")

            assert response.status_code == 200

    def test_suggestions_missing_task_type(self):
        """Test suggestions without required task_type."""
        client = TestClient(app)
        response = client.get("/api/anytool/suggestions")

        assert response.status_code == 422


class TestFeedbackEndpoint:
    """Tests for /api/anytool/feedback endpoint."""

    def test_feedback_positive(self):
        """Test submitting positive feedback."""
        client = TestClient(app)
        tool_id = uuid4()

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.learn_from_feedback = AsyncMock(return_value={
                "status": "success",
                "tool_name": "test_tool",
                "new_success_rate": 0.92
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/feedback",
                json={
                    "tool_id": str(tool_id),
                    "feedback": "Great tool, worked perfectly",
                    "rating": 5
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_feedback_negative(self):
        """Test submitting negative feedback."""
        client = TestClient(app)
        tool_id = uuid4()

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.learn_from_feedback = AsyncMock(return_value={
                "status": "success",
                "tool_name": "test_tool",
                "new_success_rate": 0.85
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/feedback",
                json={
                    "tool_id": str(tool_id),
                    "feedback": "Tool failed on my request",
                    "rating": 1
                }
            )

            assert response.status_code == 200

    def test_feedback_tool_not_found(self):
        """Test feedback for non-existent tool."""
        client = TestClient(app)
        tool_id = uuid4()

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.learn_from_feedback = AsyncMock(return_value={
                "status": "error",
                "message": "Tool not found"
            })
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/anytool/feedback",
                json={
                    "tool_id": str(tool_id),
                    "feedback": "Test",
                    "rating": 3
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"

    def test_feedback_invalid_rating(self):
        """Test feedback with invalid rating."""
        client = TestClient(app)
        tool_id = uuid4()
        response = client.post(
            "/api/anytool/feedback",
            json={
                "tool_id": str(tool_id),
                "feedback": "Test",
                "rating": 10  # Invalid - should be 1-5
            }
        )

        assert response.status_code == 422

    def test_feedback_invalid_uuid(self):
        """Test feedback with invalid tool_id."""
        client = TestClient(app)
        response = client.post(
            "/api/anytool/feedback",
            json={
                "tool_id": "not-a-uuid",
                "feedback": "Test",
                "rating": 3
            }
        )

        assert response.status_code == 422


class TestStatusEndpoint:
    """Tests for /api/anytool/status endpoint."""

    def test_status_healthy(self):
        """Test status when system is healthy."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_system_status = AsyncMock(return_value={
                "status": "healthy",
                "servers": {"total": 5, "active": 4, "healthy": 3},
                "tools": {"total": 50, "enabled": 45},
                "reliability_24h": {"period_hours": 24, "tools": {}, "total_executions": 0},
                "features": ["multi_stage_filtering", "semantic_search"],
                "version": "1.0.0"
            })
            mock_service_class.return_value = mock_service

            response = client.get("/api/anytool/status")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_status_degraded(self):
        """Test status when system is degraded."""
        client = TestClient(app)

        with patch("app.api.anytool.AnyToolService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_system_status = AsyncMock(return_value={
                "status": "degraded",
                "servers": {"total": 5, "active": 1, "healthy": 0},
                "tools": {"total": 50, "enabled": 10},
                "reliability_24h": {"period_hours": 24, "tools": {}, "total_executions": 0},
                "features": [],
                "version": "1.0.0"
            })
            mock_service_class.return_value = mock_service

            response = client.get("/api/anytool/status")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
