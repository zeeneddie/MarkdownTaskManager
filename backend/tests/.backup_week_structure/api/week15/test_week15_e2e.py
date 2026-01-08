"""
Week 15 E2E Tests

Tests for Week 15 functionality:
- Project Wizard API
- Scheduler API (enhanced)
- WebSocket connections
- Marcus Agent Integration

Run with: pytest tests/api/week15/test_week15_e2e.py -v
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from uuid import uuid4
import json


# ============================================================================
# PROJECT WIZARD TESTS
# ============================================================================

class TestProjectWizard:
    """Test Project Wizard API endpoints"""

    @pytest.mark.asyncio
    async def test_get_templates(self, client: AsyncClient):
        """Test getting available project templates"""
        response = await client.get("/api/wizard/templates")
        assert response.status_code == 200

        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) >= 4  # web-app, api-service, migration, custom

        # Check template structure
        template = templates[0]
        assert "id" in template
        assert "name" in template
        assert "description" in template
        assert "default_language" in template
        assert "default_workflow" in template
        assert "features" in template

    @pytest.mark.asyncio
    async def test_get_specific_template(self, client: AsyncClient):
        """Test getting a specific template by ID"""
        response = await client.get("/api/wizard/templates/web-app")
        assert response.status_code == 200

        template = response.json()
        assert template["id"] == "web-app"
        assert template["default_language"] == "typescript"
        assert "nextjs" in template.get("default_framework", "")

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, client: AsyncClient):
        """Test getting non-existent template returns 404"""
        response = await client.get("/api/wizard/templates/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_wizard_session(self, client: AsyncClient):
        """Test starting a wizard session"""
        response = await client.post(
            "/api/wizard/start",
            json={"template": "web-app"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert data["template"] == "web-app"
        assert "created_at" in data
        assert data["message"] == "Wizard session started successfully"

    @pytest.mark.asyncio
    async def test_save_wizard_step(self, client: AsyncClient):
        """Test saving wizard step data"""
        # First start a session
        start_response = await client.post(
            "/api/wizard/start",
            json={"template": "api-service"}
        )
        session_id = start_response.json()["session_id"]

        # Save step data
        response = await client.post(
            f"/api/wizard/step/{session_id}",
            json={
                "step_number": 1,
                "data": {
                    "name": "Test Project",
                    "description": "A test project"
                }
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == session_id
        assert data["step_number"] == 1
        assert data["saved"] is True

    @pytest.mark.asyncio
    async def test_complete_wizard(self, client: AsyncClient):
        """Test completing wizard and creating project"""
        unique_name = f"Test API Project {uuid4().hex[:8]}"
        response = await client.post(
            "/api/wizard/complete",
            json={
                "template": "api-service",
                "name": unique_name,
                "description": "A test API service project",
                "language": "python",
                "framework": "fastapi",
                "database": "postgresql",
                "team": [
                    {"name": "John Doe", "role": "developer"},
                    {"name": "Jane Smith", "role": "lead"}
                ],
                "sprintDuration": 2,
                "workingHours": 8,
                "workflow": "spec-kit",
                "qualityGates": "standard",
                "autoAssign": True
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "project_id" in data
        assert data["project_name"] == unique_name
        assert data["workflow"] == "spec-kit"
        assert "agents_assigned" in data
        assert data["quality_gates_enabled"] == 5  # standard = 5 gates

    @pytest.mark.asyncio
    async def test_get_wizard_session(self, client: AsyncClient):
        """Test getting wizard session data"""
        # Start session
        start_response = await client.post(
            "/api/wizard/start",
            json={"template": "migration"}
        )
        session_id = start_response.json()["session_id"]

        # Get session
        response = await client.get(f"/api/wizard/session/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["template"] == "migration"
        assert "created_at" in data
        assert "steps" in data

    @pytest.mark.asyncio
    async def test_delete_wizard_session(self, client: AsyncClient):
        """Test deleting wizard session"""
        # Start session
        start_response = await client.post(
            "/api/wizard/start",
            json={"template": "custom"}
        )
        session_id = start_response.json()["session_id"]

        # Delete session
        response = await client.delete(f"/api/wizard/session/{session_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify session is gone
        get_response = await client.get(f"/api/wizard/session/{session_id}")
        assert get_response.status_code == 404


# ============================================================================
# SCHEDULER TESTS
# ============================================================================

class TestScheduler:
    """Test Scheduler API endpoints"""

    @pytest.mark.asyncio
    async def test_get_scheduler_status(self, client: AsyncClient):
        """Test getting scheduler status"""
        response = await client.get("/api/scheduler/status")
        assert response.status_code == 200

        data = response.json()
        assert "running" in data
        assert "scheduledJobs" in data
        assert "executionRecords" in data

    @pytest.mark.asyncio
    async def test_get_scheduled_jobs(self, client: AsyncClient):
        """Test getting list of scheduled jobs"""
        response = await client.get("/api/scheduler/jobs")
        assert response.status_code == 200

        jobs = response.json()
        assert isinstance(jobs, list)

    @pytest.mark.asyncio
    async def test_schedule_daily_scan(self, client: AsyncClient):
        """Test scheduling a daily maintenance scan"""
        response = await client.post(
            "/api/scheduler/daily",
            json={
                "hour": 2,
                "minute": 30,
                "scope": "full_codebase",
                "focusAreas": ["dependencies", "security"],
                "urgency": "medium"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "jobId" in data
        assert "02:30 UTC" in data["message"]

    @pytest.mark.asyncio
    async def test_schedule_weekly_scan(self, client: AsyncClient):
        """Test scheduling a weekly maintenance scan"""
        response = await client.post(
            "/api/scheduler/weekly",
            json={
                "dayOfWeek": "mon",
                "hour": 3,
                "minute": 0,
                "scope": "full_codebase",
                "focusAreas": ["code_quality", "tech_debt"],
                "urgency": "low"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "jobId" in data
        assert "mon" in data["message"]

    @pytest.mark.asyncio
    async def test_schedule_interval_scan(self, client: AsyncClient):
        """Test scheduling an interval maintenance scan"""
        response = await client.post(
            "/api/scheduler/interval",
            json={
                "intervalType": "hours",
                "intervalValue": 12,
                "scope": "module",
                "focusAreas": ["dependencies"],
                "urgency": "high"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "12 hours" in data["message"]

    @pytest.mark.asyncio
    async def test_get_execution_history(self, client: AsyncClient):
        """Test getting execution history"""
        response = await client.get("/api/scheduler/history?limit=10")
        assert response.status_code == 200

        history = response.json()
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_export_history_json(self, client: AsyncClient):
        """Test exporting history as JSON"""
        response = await client.get("/api/scheduler/export/history?format=json")
        assert response.status_code == 200

        data = response.json()
        assert "export_date" in data
        assert "records" in data
        assert "total_records" in data

    @pytest.mark.asyncio
    async def test_export_history_csv(self, client: AsyncClient):
        """Test exporting history as CSV"""
        response = await client.get("/api/scheduler/export/history?format=csv")
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("text/csv")
        assert "Content-Disposition" in response.headers

    @pytest.mark.asyncio
    async def test_run_immediate_scan(self, client: AsyncClient):
        """Test running an immediate scan"""
        response = await client.post(
            "/api/scheduler/run-now",
            params={
                "scope": "full_codebase",
                "focus_areas": "dependencies,security",
                "urgency": "high"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "execution_id" in data or "message" in data


# ============================================================================
# WEBSOCKET TESTS
# ============================================================================

class TestWebSocket:
    """Test WebSocket API endpoints"""

    @pytest.mark.asyncio
    async def test_websocket_status(self, client: AsyncClient):
        """Test getting WebSocket status"""
        response = await client.get("/api/websocket/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert "connections" in data
        assert "total" in data["connections"]
        assert "maintenance" in data["connections"]
        assert "agents" in data["connections"]
        assert "scheduler" in data["connections"]

    @pytest.mark.asyncio
    async def test_get_active_connections(self, client: AsyncClient):
        """Test getting active WebSocket connections"""
        response = await client.get("/api/websocket/connections")
        assert response.status_code == 200

        data = response.json()
        assert "connections" in data
        assert "total" in data
        assert isinstance(data["connections"], list)


# ============================================================================
# MARCUS AGENT TESTS
# ============================================================================

class TestMarcusAgent:
    """Test Marcus Agent integration endpoints"""

    @pytest.mark.asyncio
    async def test_get_marcus_status(self, client: AsyncClient):
        """Test getting Marcus agent status"""
        response = await client.get("/api/maintenance/marcus/status")
        assert response.status_code == 200

        data = response.json()
        assert data["agent"] == "Marcus"
        assert data["role"] == "Maintenance Specialist"
        assert data["llm"] == "qwen2.5-coder:7b"
        assert "available" in data
        assert "specialties" in data
        assert isinstance(data["specialties"], list)

    @pytest.mark.asyncio
    async def test_run_marcus_scan_dependencies(self, client: AsyncClient):
        """Test running Marcus scan for dependencies"""
        response = await client.post(
            "/api/maintenance/marcus/scan",
            json={
                "scope": "full_codebase",
                "focus_areas": ["dependencies"],
                "urgency": "medium"
            }
        )

        # May return 503 if Ollama is not running
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "scan_id" in data
            assert data["status"] in ["completed", "failed"]
            assert "total_findings" in data
            assert "priority_actions" in data

    @pytest.mark.asyncio
    async def test_run_marcus_scan_security(self, client: AsyncClient):
        """Test running Marcus scan for security"""
        response = await client.post(
            "/api/maintenance/marcus/scan",
            json={
                "scope": "full_codebase",
                "focus_areas": ["security"],
                "urgency": "high"
            }
        )

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_run_marcus_scan_code_quality(self, client: AsyncClient):
        """Test running Marcus scan for code quality"""
        response = await client.post(
            "/api/maintenance/marcus/scan",
            json={
                "scope": "module",
                "focus_areas": ["code_quality", "tech_debt"],
                "urgency": "low",
                "target_path": "app/api"
            }
        )

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_run_marcus_scan_invalid_scope(self, client: AsyncClient):
        """Test Marcus scan with invalid scope"""
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
# MAINTENANCE API TESTS
# ============================================================================

class TestMaintenanceAPI:
    """Test Maintenance API endpoints"""

    @pytest.mark.asyncio
    async def test_run_maintenance_workflow(self, client: AsyncClient):
        """Test running maintenance workflow"""
        response = await client.post(
            "/api/maintenance/run",
            json={
                "project_id": 1,
                "scope": "full_codebase",
                "focus_areas": ["dependencies", "security", "code_quality"],
                "urgency": "medium",
                "auto_fix": {
                    "dependencies": False,
                    "formatting": True,
                    "linting": True
                },
                "use_historical_patterns": True,
                "store_results": True
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "workflow_id" in data
        assert data["project_id"] == 1
        assert data["status"] == "completed"
        assert "technical_debt_reduced" in data
        assert "vulnerabilities_fixed" in data
        assert "dependencies_updated" in data

    @pytest.mark.asyncio
    async def test_run_async_maintenance(self, client: AsyncClient):
        """Test running async maintenance workflow"""
        response = await client.post(
            "/api/maintenance/run-async",
            json={
                "project_id": 2,
                "scope": "module",
                "module_path": "app/services",
                "focus_areas": ["code_quality"],
                "urgency": "low"
            }
        )
        assert response.status_code == 202

        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "check_status_url" in data

    @pytest.mark.asyncio
    async def test_get_maintenance_job_status(self, client: AsyncClient):
        """Test getting maintenance job status"""
        # This uses a placeholder job ID
        response = await client.get("/api/maintenance/jobs/MAINT-JOB-1-123456")

        # May return 404 if job doesn't exist
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_maintenance_history(self, client: AsyncClient):
        """Test getting maintenance history for a project"""
        response = await client.get("/api/maintenance/history/1?limit=5")
        assert response.status_code == 200

        history = response.json()
        assert isinstance(history, list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple Week 15 features"""

    @pytest.mark.asyncio
    async def test_wizard_to_maintenance_flow(self, client: AsyncClient):
        """Test complete flow: create project via wizard, then run maintenance"""
        # 1. Create project via wizard
        wizard_response = await client.post(
            "/api/wizard/complete",
            json={
                "template": "api-service",
                "name": "Integration Test Project",
                "description": "Testing wizard to maintenance flow",
                "language": "python",
                "framework": "fastapi",
                "workflow": "maintenance",
                "qualityGates": "standard",
                "autoAssign": True
            }
        )
        assert wizard_response.status_code == 200
        project_id = wizard_response.json()["project_id"]

        # 2. Run maintenance on the new project
        maintenance_response = await client.post(
            "/api/maintenance/run",
            json={
                "project_id": project_id,
                "scope": "full_codebase",
                "focus_areas": ["dependencies"],
                "urgency": "medium"
            }
        )
        assert maintenance_response.status_code == 200
        assert maintenance_response.json()["project_id"] == project_id

    @pytest.mark.asyncio
    async def test_scheduler_export_formats(self, client: AsyncClient):
        """Test that scheduler export works for both JSON and CSV"""
        # Test JSON export
        json_response = await client.get("/api/scheduler/export/history?format=json")
        assert json_response.status_code == 200
        json_data = json_response.json()
        assert "records" in json_data

        # Test CSV export
        csv_response = await client.get("/api/scheduler/export/history?format=csv")
        assert csv_response.status_code == 200
        assert "text/csv" in csv_response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test API health check endpoint"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
