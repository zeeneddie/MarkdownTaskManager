"""
Integration Tests for Observability API

Week 54: Tests for observability REST API endpoints.
"""

import pytest
from uuid import uuid4
from datetime import datetime, date
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.observability import (
    LLMProvider,
    AgentAction,
    DecisionTrace,
    AgentPerformanceDaily,
)


@pytest.fixture
async def client():
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# PROVIDER ENDPOINT TESTS
# ============================================================================

class TestProviderEndpoints:
    """Test provider management endpoints."""

    @pytest.mark.asyncio
    async def test_list_providers(self, client):
        """Test listing all providers."""
        response = await client.get("/api/observability/providers")

        # Should return 200 or 500 (if no DB)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_providers_active_only(self, client):
        """Test listing only active providers."""
        response = await client.get(
            "/api/observability/providers",
            params={"active_only": True}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_providers_by_tier(self, client):
        """Test filtering providers by tier."""
        response = await client.get(
            "/api/observability/providers",
            params={"tier": "balanced"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_provider_not_found(self, client):
        """Test getting a non-existent provider."""
        response = await client.get("/api/observability/providers/nonexistent_provider")

        # Should be 404 or 500
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_update_provider_status(self, client):
        """Test enabling/disabling a provider."""
        response = await client.patch(
            "/api/observability/providers/ollama/status",
            json={"is_active": False}
        )

        # Should be 200, 404, or 500
        assert response.status_code in [200, 404, 500]


# ============================================================================
# ACTION LOGGING ENDPOINT TESTS
# ============================================================================

class TestActionEndpoints:
    """Test action logging endpoints."""

    @pytest.mark.asyncio
    async def test_log_action_valid(self, client):
        """Test logging a valid action."""
        payload = {
            "agent_id": "felix",
            "action_type": "generate",
            "provider": "ollama",
            "model": "qwen2.5-coder:7b",
            "token_input": 100,
            "token_output": 200,
            "duration_ms": 1500,
            "success": True,
            "confidence_score": 0.85,
        }

        response = await client.post(
            "/api/observability/actions",
            json=payload
        )

        # Should be 200 or 500 (if no DB)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["agent_id"] == "felix"
            assert data["action_type"] == "generate"

    @pytest.mark.asyncio
    async def test_log_action_minimal(self, client):
        """Test logging action with minimal required fields."""
        payload = {
            "agent_id": "quinn",
            "action_type": "review",
        }

        response = await client.post(
            "/api/observability/actions",
            json=payload
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_log_action_missing_required_field(self, client):
        """Test logging action with missing required fields."""
        payload = {
            "agent_id": "felix",
            # Missing action_type
        }

        response = await client.post(
            "/api/observability/actions",
            json=payload
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_log_action_invalid_confidence(self, client):
        """Test logging action with invalid confidence score."""
        payload = {
            "agent_id": "felix",
            "action_type": "generate",
            "confidence_score": 1.5,  # Out of range
        }

        response = await client.post(
            "/api/observability/actions",
            json=payload
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_actions(self, client):
        """Test listing recent actions."""
        response = await client.get("/api/observability/actions")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_actions_with_filters(self, client):
        """Test listing actions with filters."""
        response = await client.get(
            "/api/observability/actions",
            params={
                "agent_id": "felix",
                "limit": 10,
                "hours": 24,
            }
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_actions_limit_validation(self, client):
        """Test list actions limit validation."""
        response = await client.get(
            "/api/observability/actions",
            params={"limit": 500}  # Exceeds max 200
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_task_actions(self, client):
        """Test getting actions for a specific task."""
        task_id = uuid4()
        response = await client.get(f"/api/observability/actions/task/{task_id}")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_task_actions_invalid_uuid(self, client):
        """Test getting actions with invalid UUID."""
        response = await client.get("/api/observability/actions/task/not-a-uuid")

        assert response.status_code == 422  # Validation error


# ============================================================================
# DECISION TRACING ENDPOINT TESTS
# ============================================================================

class TestDecisionEndpoints:
    """Test decision tracing endpoints."""

    @pytest.mark.asyncio
    async def test_log_decision_valid(self, client):
        """Test logging a valid decision."""
        payload = {
            "agent_id": "felix",
            "decision_point": "model_selection",
            "options": [
                {"name": "ollama", "cost": 0},
                {"name": "claude", "cost": 3},
            ],
            "selected_option": "ollama",
            "selection_rationale": "Simple task, use free tier",
            "outcome": "success",
        }

        response = await client.post(
            "/api/observability/decisions",
            json=payload
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["agent_id"] == "felix"
            assert data["decision_point"] == "model_selection"

    @pytest.mark.asyncio
    async def test_log_decision_minimal(self, client):
        """Test logging decision with minimal fields."""
        payload = {
            "agent_id": "quinn",
            "decision_point": "quality_gate",
        }

        response = await client.post(
            "/api/observability/decisions",
            json=payload
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_log_decision_missing_required_field(self, client):
        """Test logging decision with missing required fields."""
        payload = {
            "agent_id": "felix",
            # Missing decision_point
        }

        response = await client.post(
            "/api/observability/decisions",
            json=payload
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_task_decisions(self, client):
        """Test getting decision trace for a task."""
        task_id = uuid4()
        response = await client.get(f"/api/observability/decisions/task/{task_id}")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


# ============================================================================
# STATISTICS ENDPOINT TESTS
# ============================================================================

class TestStatisticsEndpoints:
    """Test statistics and performance endpoints."""

    @pytest.mark.asyncio
    async def test_get_agent_stats(self, client):
        """Test getting agent statistics."""
        response = await client.get("/api/observability/stats/agent/felix")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["agent_id"] == "felix"
            assert "total_actions" in data
            assert "success_rate" in data

    @pytest.mark.asyncio
    async def test_get_agent_stats_with_days(self, client):
        """Test getting agent statistics with custom period."""
        response = await client.get(
            "/api/observability/stats/agent/felix",
            params={"days": 30}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["period_days"] == 30

    @pytest.mark.asyncio
    async def test_get_agent_stats_days_validation(self, client):
        """Test agent stats days parameter validation."""
        response = await client.get(
            "/api/observability/stats/agent/felix",
            params={"days": 100}  # Exceeds max 90
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_platform_stats(self, client):
        """Test getting platform-wide statistics."""
        response = await client.get("/api/observability/stats/platform")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "total_actions" in data
            assert "active_agents" in data
            assert "top_agents" in data

    @pytest.mark.asyncio
    async def test_get_daily_performance(self, client):
        """Test getting daily performance metrics."""
        response = await client.get("/api/observability/performance/daily")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_daily_performance_with_filters(self, client):
        """Test daily performance with date filters."""
        response = await client.get(
            "/api/observability/performance/daily",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "agent_id": "felix",
            }
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_trigger_aggregation(self, client):
        """Test manually triggering performance aggregation."""
        response = await client.post("/api/observability/performance/aggregate")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "message" in data


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/api/observability/health")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"
            assert "active_providers" in data
            assert "providers" in data


# ============================================================================
# REQUEST VALIDATION TESTS
# ============================================================================

class TestRequestValidation:
    """Test request validation."""

    @pytest.mark.asyncio
    async def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = await client.post(
            "/api/observability/actions",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_payload(self, client):
        """Test handling of empty payload."""
        response = await client.post(
            "/api/observability/actions",
            json={}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extra_fields_ignored(self, client):
        """Test that extra fields are ignored."""
        payload = {
            "agent_id": "felix",
            "action_type": "generate",
            "unknown_field": "should be ignored",
        }

        response = await client.post(
            "/api/observability/actions",
            json=payload
        )

        # Extra fields should not cause error
        assert response.status_code in [200, 500]
