"""
Week 15 Standalone Tests

Tests that don't require database connection.
Run with: pytest tests/api/week15/test_week15_standalone.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """Create test client without database dependency"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# PROJECT WIZARD TESTS
# ============================================================================

class TestProjectWizardStandalone:
    """Test Project Wizard API endpoints (no database)"""

    @pytest.mark.asyncio
    async def test_get_templates(self, client: AsyncClient):
        """Test getting available project templates"""
        response = await client.get("/api/wizard/templates")
        assert response.status_code == 200

        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) == 4  # web-app, api-service, migration, custom

        # Verify template IDs
        template_ids = [t["id"] for t in templates]
        assert "web-app" in template_ids
        assert "api-service" in template_ids
        assert "migration" in template_ids
        assert "custom" in template_ids

    @pytest.mark.asyncio
    async def test_get_web_app_template(self, client: AsyncClient):
        """Test getting web-app template"""
        response = await client.get("/api/wizard/templates/web-app")
        assert response.status_code == 200

        template = response.json()
        assert template["id"] == "web-app"
        assert template["name"] == "Web Application"
        assert template["default_language"] == "typescript"
        assert template["default_framework"] == "nextjs"
        assert template["default_workflow"] == "spec-kit"

    @pytest.mark.asyncio
    async def test_get_api_service_template(self, client: AsyncClient):
        """Test getting api-service template"""
        response = await client.get("/api/wizard/templates/api-service")
        assert response.status_code == 200

        template = response.json()
        assert template["id"] == "api-service"
        assert template["default_language"] == "python"
        assert template["default_framework"] == "fastapi"

    @pytest.mark.asyncio
    async def test_get_migration_template(self, client: AsyncClient):
        """Test getting migration template"""
        response = await client.get("/api/wizard/templates/migration")
        assert response.status_code == 200

        template = response.json()
        assert template["id"] == "migration"
        assert template["default_language"] == "csharp"
        assert template["default_workflow"] == "bmad"

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, client: AsyncClient):
        """Test 404 for non-existent template"""
        response = await client.get("/api/wizard/templates/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_wizard_session(self, client: AsyncClient):
        """Test starting wizard session"""
        response = await client.post(
            "/api/wizard/start",
            json={"template": "web-app"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert data["template"] == "web-app"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_wizard_session_lifecycle(self, client: AsyncClient):
        """Test complete wizard session lifecycle"""
        # Start session
        start = await client.post("/api/wizard/start", json={"template": "api-service"})
        assert start.status_code == 200
        session_id = start.json()["session_id"]

        # Save step
        step = await client.post(
            f"/api/wizard/step/{session_id}",
            json={"step_number": 1, "data": {"name": "Test"}}
        )
        assert step.status_code == 200
        assert step.json()["saved"] is True

        # Get session
        get = await client.get(f"/api/wizard/session/{session_id}")
        assert get.status_code == 200
        assert get.json()["template"] == "api-service"

        # Delete session
        delete = await client.delete(f"/api/wizard/session/{session_id}")
        assert delete.status_code == 200

        # Verify deleted
        verify = await client.get(f"/api/wizard/session/{session_id}")
        assert verify.status_code == 404


# ============================================================================
# SCHEDULER TESTS
# ============================================================================

class TestSchedulerStandalone:
    """Test Scheduler API endpoints"""

    @pytest.mark.asyncio
    async def test_get_scheduler_status(self, client: AsyncClient):
        """Test scheduler status endpoint"""
        response = await client.get("/api/scheduler/status")
        assert response.status_code == 200

        data = response.json()
        assert "running" in data
        assert "scheduledJobs" in data
        assert "executionRecords" in data

    @pytest.mark.asyncio
    async def test_get_jobs(self, client: AsyncClient):
        """Test getting scheduled jobs"""
        response = await client.get("/api/scheduler/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_history(self, client: AsyncClient):
        """Test getting execution history"""
        response = await client.get("/api/scheduler/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_export_json(self, client: AsyncClient):
        """Test JSON export"""
        response = await client.get("/api/scheduler/export/history?format=json")
        assert response.status_code == 200

        data = response.json()
        assert "export_date" in data
        assert "records" in data

    @pytest.mark.asyncio
    async def test_export_csv(self, client: AsyncClient):
        """Test CSV export"""
        response = await client.get("/api/scheduler/export/history?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")


# ============================================================================
# WEBSOCKET TESTS
# ============================================================================

class TestWebSocketStandalone:
    """Test WebSocket status endpoints"""

    @pytest.mark.asyncio
    async def test_websocket_status(self, client: AsyncClient):
        """Test WebSocket status"""
        response = await client.get("/api/websocket/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert "connections" in data
        assert "total" in data["connections"]

    @pytest.mark.asyncio
    async def test_websocket_connections(self, client: AsyncClient):
        """Test WebSocket connections list"""
        response = await client.get("/api/websocket/connections")
        assert response.status_code == 200

        data = response.json()
        assert "connections" in data
        assert "total" in data


# ============================================================================
# MARCUS AGENT TESTS
# ============================================================================

class TestMarcusStandalone:
    """Test Marcus agent endpoints"""

    @pytest.mark.asyncio
    async def test_marcus_status(self, client: AsyncClient):
        """Test Marcus agent status"""
        response = await client.get("/api/maintenance/marcus/status")
        assert response.status_code == 200

        data = response.json()
        assert data["agent"] == "Marcus"
        assert data["role"] == "Maintenance Specialist"
        assert data["llm"] == "qwen2.5-coder:7b"
        assert "available" in data
        assert "specialties" in data

    @pytest.mark.asyncio
    async def test_marcus_scan_validation(self, client: AsyncClient):
        """Test Marcus scan validation (invalid scope)"""
        response = await client.post(
            "/api/maintenance/marcus/scan",
            json={
                "scope": "invalid_scope",
                "focus_areas": ["dependencies"],
                "urgency": "medium"
            }
        )
        assert response.status_code == 422  # Validation error


# ============================================================================
# HEALTH CHECK
# ============================================================================

class TestHealthCheck:
    """Test health endpoints"""

    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        """Test API health check"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
