"""
Week 50: Quality Gate Evaluation API Tests

Tests for:
- GET /api/quality/gate/{workflow_type}/config
- POST /api/quality/gate/{workflow_type}/evaluate
- GET /api/quality/gate/status
- GET /api/quality/gate/workflow-types
"""
import pytest
from httpx import AsyncClient


class TestQualityGateWorkflowTypes:
    """Tests for /api/quality/gate/workflow-types endpoint."""

    @pytest.mark.asyncio
    async def test_get_workflow_types_returns_all_types(self, client: AsyncClient):
        """Should return all 8 workflow types."""
        response = await client.get("/api/quality/gate/workflow-types")

        assert response.status_code == 200
        data = response.json()

        assert "workflow_types" in data
        assert len(data["workflow_types"]) == 8

        # Check all expected types are present
        type_names = [wt["type"] for wt in data["workflow_types"]]
        expected = ["NEW_FEATURE", "MAINTENANCE", "BUG", "QUALITY_AUDIT",
                   "MIGRATION", "REFACTORING", "DOCUMENTATION", "HOTFIX"]

        for expected_type in expected:
            assert expected_type in type_names

    @pytest.mark.asyncio
    async def test_workflow_types_have_phases(self, client: AsyncClient):
        """Each workflow type should have validation phases."""
        response = await client.get("/api/quality/gate/workflow-types")

        assert response.status_code == 200
        data = response.json()

        for wt in data["workflow_types"]:
            assert "type" in wt
            assert "phases" in wt
            assert "description" in wt
            assert len(wt["phases"]) > 0

    @pytest.mark.asyncio
    async def test_new_feature_has_all_phases(self, client: AsyncClient):
        """NEW_FEATURE should have all 5 validation phases."""
        response = await client.get("/api/quality/gate/workflow-types")

        data = response.json()
        new_feature = next(wt for wt in data["workflow_types"] if wt["type"] == "NEW_FEATURE")

        expected_phases = ["linting", "type_check", "style", "unit_tests", "e2e_tests"]
        assert new_feature["phases"] == expected_phases


class TestQualityGateConfig:
    """Tests for /api/quality/gate/{workflow_type}/config endpoint."""

    @pytest.mark.asyncio
    async def test_get_config_for_valid_workflow(self, client: AsyncClient, workflow_types):
        """Should return config for each valid workflow type."""
        for wt in workflow_types:
            response = await client.get(f"/api/quality/gate/{wt}/config")

            assert response.status_code == 200
            data = response.json()

            assert data["workflow_type"] == wt
            assert "phases" in data
            assert "max_iterations" in data
            assert "blocking_severities" in data

    @pytest.mark.asyncio
    async def test_get_config_invalid_workflow_returns_400(self, client: AsyncClient):
        """Should return 400 for invalid workflow type."""
        response = await client.get("/api/quality/gate/INVALID_TYPE/config")

        assert response.status_code == 400
        assert "Unknown workflow type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_config_has_required_fields(self, client: AsyncClient):
        """Config should have all required fields."""
        response = await client.get("/api/quality/gate/NEW_FEATURE/config")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "workflow_type", "phases", "max_iterations",
            "stop_on_first_failure", "required_coverage",
            "regression_test_required", "blocking_severities", "e2e_required"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestQualityGateStatus:
    """Tests for /api/quality/gate/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_status_returns_all_workflows(self, client: AsyncClient):
        """Should return status for all 8 workflows."""
        response = await client.get("/api/quality/gate/status")

        assert response.status_code == 200
        data = response.json()

        assert "workflows" in data
        assert len(data["workflows"]) == 8
        assert "active_config" in data

    @pytest.mark.asyncio
    async def test_workflow_status_has_required_fields(self, client: AsyncClient):
        """Each workflow status should have required fields."""
        response = await client.get("/api/quality/gate/status")

        data = response.json()

        for workflow in data["workflows"]:
            assert "workflow_type" in workflow
            assert "configured" in workflow
            assert "blocking_severities" in workflow
            assert "required_coverage" in workflow
            assert "e2e_required" in workflow
            assert "phases" in workflow


class TestQualityGateEvaluation:
    """Tests for /api/quality/gate/{workflow_type}/evaluate endpoint."""

    @pytest.mark.asyncio
    async def test_evaluate_with_no_errors_passes(self, client: AsyncClient):
        """Gate should pass when no errors are present."""
        response = await client.post(
            "/api/quality/gate/NEW_FEATURE/evaluate",
            json={
                "errors": [],
                "coverage_percent": 85.0,
                "phases_passed": ["linting", "type_check", "unit_tests"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["passed"] is True
        assert data["blocking_count"] == 0
        assert data["coverage_met"] is True

    @pytest.mark.asyncio
    async def test_evaluate_with_critical_error_fails(self, client: AsyncClient):
        """Gate should fail when critical error is present."""
        response = await client.post(
            "/api/quality/gate/NEW_FEATURE/evaluate",
            json={
                "errors": [
                    {
                        "phase": "unit_tests",
                        "message": "Critical test failure",
                        "severity": "critical"
                    }
                ],
                "coverage_percent": 85.0,
                "phases_passed": ["linting"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["passed"] is False
        assert data["blocking_count"] >= 1

    @pytest.mark.asyncio
    async def test_evaluate_with_low_coverage_fails(self, client: AsyncClient):
        """Gate should fail when coverage is below required."""
        response = await client.post(
            "/api/quality/gate/NEW_FEATURE/evaluate",
            json={
                "errors": [],
                "coverage_percent": 50.0,  # Below 80% requirement
                "phases_passed": ["linting", "type_check"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["passed"] is False
        assert data["coverage_met"] is False
        assert "coverage" in str(data["blocking_issues"]).lower()

    @pytest.mark.asyncio
    async def test_evaluate_warning_does_not_block(self, client: AsyncClient):
        """Warnings should not block gate pass."""
        response = await client.post(
            "/api/quality/gate/NEW_FEATURE/evaluate",
            json={
                "errors": [
                    {
                        "phase": "linting",
                        "message": "Missing semicolon",
                        "severity": "warning"
                    }
                ],
                "coverage_percent": 85.0,
                "phases_passed": ["linting", "type_check", "unit_tests"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["passed"] is True
        assert data["warning_count"] >= 1
        assert data["blocking_count"] == 0

    @pytest.mark.asyncio
    async def test_evaluate_invalid_workflow_returns_400(self, client: AsyncClient):
        """Should return 400 for invalid workflow type."""
        response = await client.post(
            "/api/quality/gate/INVALID/evaluate",
            json={"errors": [], "coverage_percent": 80.0, "phases_passed": []}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_evaluate_returns_workflow_type(self, client: AsyncClient, workflow_types):
        """Response should include the workflow type."""
        for wt in workflow_types:
            response = await client.post(
                f"/api/quality/gate/{wt}/evaluate",
                json={"errors": [], "coverage_percent": 90.0, "phases_passed": []}
            )

            assert response.status_code == 200
            assert response.json()["workflow_type"] == wt


class TestQualityGateIntegration:
    """Integration tests for quality gate workflows."""

    @pytest.mark.asyncio
    async def test_bug_workflow_requires_regression(self, client: AsyncClient):
        """BUG workflow should check regression requirement."""
        # Get config to verify regression is required
        config_response = await client.get("/api/quality/gate/BUG/config")
        config = config_response.json()

        # BUG workflow has regression_required = True in database
        assert config["workflow_type"] == "BUG"

    @pytest.mark.asyncio
    async def test_migration_workflow_requires_e2e(self, client: AsyncClient):
        """MIGRATION workflow should have E2E as critical."""
        response = await client.get("/api/quality/gate/MIGRATION/config")
        config = response.json()

        assert "e2e_tests" in config["phases"]

    @pytest.mark.asyncio
    async def test_documentation_has_minimal_validation(self, client: AsyncClient):
        """DOCUMENTATION should have minimal validation phases."""
        response = await client.get("/api/quality/gate/DOCUMENTATION/config")
        config = response.json()

        # Documentation only needs linting
        assert "linting" in config["phases"]
        assert len(config["phases"]) == 1

    @pytest.mark.asyncio
    async def test_full_evaluation_flow(self, client: AsyncClient):
        """Test complete evaluation flow: config -> evaluate -> verify."""
        # Step 1: Get config
        config_response = await client.get("/api/quality/gate/REFACTORING/config")
        config = config_response.json()

        # Step 2: Evaluate with passing criteria
        eval_response = await client.post(
            "/api/quality/gate/REFACTORING/evaluate",
            json={
                "errors": [],
                "coverage_percent": config["required_coverage"] + 5,  # Above requirement
                "phases_passed": config["phases"]
            }
        )

        # Step 3: Verify pass
        result = eval_response.json()
        assert result["passed"] is True
        assert result["coverage_met"] is True
        assert result["coverage_required"] == config["required_coverage"]
