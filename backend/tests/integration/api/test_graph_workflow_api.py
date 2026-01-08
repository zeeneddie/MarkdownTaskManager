"""
Tests for Graph Workflow API - Week 88

Tests for API endpoints:
- POST /api/graph-workflow/impact-analysis
- POST /api/graph-workflow/dependency-check
- POST /api/graph-workflow/coupling-metrics
- POST /api/graph-workflow/test-coverage-map
- POST /api/graph-workflow/enhancement-scope
- POST /api/graph-workflow/sync-and-document
- POST /api/graph-workflow/workflow-context
- GET endpoints for quick access
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Test health endpoint."""

    def test_health_check(self):
        """Test health endpoint returns service info."""
        response = client.get("/api/graph-workflow/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "graph-workflow"
        assert data["version"] == "week-88"
        assert "endpoints" in data
        assert "workflow_integrations" in data
        assert len(data["workflow_integrations"]) >= 7


class TestImpactAnalysisAPI:
    """Test impact analysis API endpoints."""

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_impact_analysis_post(self, mock_get_service):
        """Test POST /api/graph-workflow/impact-analysis."""
        mock_service = MagicMock()
        mock_service.graph_impact_analysis = AsyncMock(return_value={
            "workflow_type": "NEW_FEATURE",
            "project_id": 1,
            "changes_analyzed": 2,
            "affected_entities": [],
            "affected_files": [],
            "impact_summary": {
                "total_affected": 5,
                "direct_impact": 3,
                "transitive_impact": 2,
                "max_depth_reached": 2
            },
            "risk_assessment": {
                "level": "low",
                "score": 15.0,
                "factors": []
            },
            "recommendations": []
        })
        mock_get_service.return_value = mock_service

        response = client.post("/api/graph-workflow/impact-analysis", json={
            "project_id": 1,
            "changes": ["UserService", "AuthService"],
            "workflow_type": "NEW_FEATURE",
            "max_depth": 5
        })

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "NEW_FEATURE"
        assert data["changes_analyzed"] == 2
        assert data["impact_summary"]["total_affected"] == 5

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_new_feature_impact_get(self, mock_get_service):
        """Test GET /api/graph-workflow/new-feature/{project_id}/impact."""
        mock_service = MagicMock()
        mock_service.graph_impact_analysis = AsyncMock(return_value={
            "workflow_type": "NEW_FEATURE",
            "project_id": 1,
            "changes_analyzed": 1,
            "affected_entities": [],
            "affected_files": [],
            "impact_summary": {"total_affected": 3},
            "risk_assessment": {"level": "low"},
            "recommendations": []
        })
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/graph-workflow/new-feature/1/impact",
            params={"changes": "UserService,AuthService"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "NEW_FEATURE"

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_maintenance_impact_get(self, mock_get_service):
        """Test GET /api/graph-workflow/maintenance/{project_id}/impact."""
        mock_service = MagicMock()
        mock_service.graph_impact_analysis = AsyncMock(return_value={
            "workflow_type": "MAINTENANCE",
            "project_id": 1,
        })
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/graph-workflow/maintenance/1/impact",
            params={"changes": "ConfigService"}
        )

        assert response.status_code == 200


class TestDependencyCheckAPI:
    """Test dependency check API endpoints."""

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_dependency_check_post(self, mock_get_service):
        """Test POST /api/graph-workflow/dependency-check."""
        mock_service = MagicMock()
        mock_service.graph_dependency_check = AsyncMock(return_value={
            "workflow_type": "BUG",
            "project_id": 1,
            "entity_name": "buggy_function",
            "entity_found": True,
            "entity": {"id": str(uuid4()), "name": "buggy_function"},
            "upstream_dependencies": [{"name": "helper"}],
            "downstream_dependents": [{"name": "caller"}],
            "circular_dependencies": [],
            "investigation_hints": ["Check parameter handling"]
        })
        mock_get_service.return_value = mock_service

        response = client.post("/api/graph-workflow/dependency-check", json={
            "project_id": 1,
            "entity_name": "buggy_function"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "BUG"
        assert data["entity_found"] is True
        assert len(data["upstream_dependencies"]) == 1

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_bug_dependencies_get(self, mock_get_service):
        """Test GET /api/graph-workflow/bug/{project_id}/dependencies/{entity_name}."""
        mock_service = MagicMock()
        mock_service.graph_dependency_check = AsyncMock(return_value={
            "workflow_type": "BUG",
            "entity_found": True,
        })
        mock_get_service.return_value = mock_service

        response = client.get("/api/graph-workflow/bug/1/dependencies/broken_func")

        assert response.status_code == 200


class TestCouplingMetricsAPI:
    """Test coupling metrics API endpoints."""

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_coupling_metrics_post(self, mock_get_service):
        """Test POST /api/graph-workflow/coupling-metrics."""
        mock_service = MagicMock()
        mock_service.graph_coupling_metrics = AsyncMock(return_value={
            "workflow_type": "QUALITY_AUDIT",
            "project_id": 1,
            "coupling_summary": {
                "total_modules": 10,
                "total_connections": 25,
                "average_coupling": 5.0
            },
            "high_coupling_modules": [],
            "circular_dependencies": [],
            "quality_score": 85,
            "improvement_suggestions": []
        })
        mock_get_service.return_value = mock_service

        response = client.post("/api/graph-workflow/coupling-metrics", json={
            "project_id": 1,
            "coupling_threshold": 10
        })

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "QUALITY_AUDIT"
        assert data["quality_score"] == 85

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_quality_coupling_get(self, mock_get_service):
        """Test GET /api/graph-workflow/quality/{project_id}/coupling."""
        mock_service = MagicMock()
        mock_service.graph_coupling_metrics = AsyncMock(return_value={
            "workflow_type": "QUALITY_AUDIT",
            "quality_score": 90
        })
        mock_get_service.return_value = mock_service

        response = client.get("/api/graph-workflow/quality/1/coupling")

        assert response.status_code == 200


class TestTestCoverageMapAPI:
    """Test test coverage map API endpoints."""

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_coverage_map_post(self, mock_get_service):
        """Test POST /api/graph-workflow/test-coverage-map."""
        mock_service = MagicMock()
        mock_service.graph_test_coverage_map = AsyncMock(return_value={
            "workflow_type": "TESTING",
            "project_id": 1,
            "test_files": ["test_user.py", "test_auth.py"],
            "tested_entities": [{"name": "UserService"}],
            "untested_entities": [{"name": "PaymentService"}],
            "coverage_summary": {
                "total_entities": 100,
                "tested_count": 60,
                "untested_count": 40,
                "coverage_percentage": 60.0
            },
            "test_priorities": [
                {"entity_name": "PaymentService", "priority_score": 100}
            ]
        })
        mock_get_service.return_value = mock_service

        response = client.post("/api/graph-workflow/test-coverage-map", json={
            "project_id": 1
        })

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "TESTING"
        assert data["coverage_summary"]["coverage_percentage"] == 60.0

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_testing_coverage_get(self, mock_get_service):
        """Test GET /api/graph-workflow/testing/{project_id}/coverage."""
        mock_service = MagicMock()
        mock_service.graph_test_coverage_map = AsyncMock(return_value={
            "workflow_type": "TESTING"
        })
        mock_get_service.return_value = mock_service

        response = client.get("/api/graph-workflow/testing/1/coverage")

        assert response.status_code == 200


class TestEnhancementScopeAPI:
    """Test enhancement scope API endpoints."""

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_enhancement_scope_post(self, mock_get_service):
        """Test POST /api/graph-workflow/enhancement-scope."""
        mock_service = MagicMock()
        mock_service.graph_enhancement_scope = AsyncMock(return_value={
            "workflow_type": "ENHANCEMENT",
            "project_id": 1,
            "feature_name": "payment_v2",
            "scope_analysis": {
                "entities_in_scope": [{"name": "PaymentService"}],
                "files_affected": ["payment.py"],
                "modules_affected": ["payments"]
            },
            "dependency_analysis": {
                "upstream_count": 3,
                "downstream_count": 5,
                "cross_module_dependencies": []
            },
            "risk_assessment": {
                "level": "medium",
                "score": 35,
                "factors": []
            },
            "enhancement_plan": [
                {"step": 1, "action": "Write Tests First"}
            ]
        })
        mock_get_service.return_value = mock_service

        response = client.post("/api/graph-workflow/enhancement-scope", json={
            "project_id": 1,
            "feature_name": "payment_v2"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "ENHANCEMENT"
        assert data["feature_name"] == "payment_v2"
        assert data["risk_assessment"]["level"] == "medium"

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_enhancement_scope_get(self, mock_get_service):
        """Test GET /api/graph-workflow/enhancement/{project_id}/scope."""
        mock_service = MagicMock()
        mock_service.graph_enhancement_scope = AsyncMock(return_value={
            "workflow_type": "ENHANCEMENT"
        })
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/graph-workflow/enhancement/1/scope",
            params={"feature_name": "new_feature"}
        )

        assert response.status_code == 200


class TestSyncAndDocumentAPI:
    """Test sync and document API endpoint."""

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_sync_and_document_post(self, mock_get_service):
        """Test POST /api/graph-workflow/sync-and-document."""
        mock_service = MagicMock()
        mock_service.sync_and_document = AsyncMock(return_value={
            "project_id": 1,
            "repo_path": "/path/to/repo",
            "graph_sync": {
                "success": True,
                "entities_added": 50,
                "relations_added": 100
            },
            "codewiki_analysis": {
                "analysis_id": 1,
                "status": "completed",
                "total_modules": 10,
                "total_files": 50,
                "languages": ["python"]
            }
        })
        mock_get_service.return_value = mock_service

        response = client.post("/api/graph-workflow/sync-and-document", json={
            "project_id": 1,
            "repo_path": "/path/to/repo"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["graph_sync"]["success"] is True
        assert data["codewiki_analysis"]["status"] == "completed"


class TestWorkflowContextAPI:
    """Test workflow context API endpoint."""

    @patch("app.api.graph_workflow.get_graph_workflow_service")
    def test_workflow_context_post(self, mock_get_service):
        """Test POST /api/graph-workflow/workflow-context."""
        mock_service = MagicMock()
        mock_service.get_workflow_context = AsyncMock(return_value={
            "project_id": 1,
            "workflow_type": "QUALITY_AUDIT",
            "graph_context": {
                "total_entities": 100,
                "total_relations": 200,
                "coupling": {"total_modules": 10}
            },
            "codewiki_context": {
                "analysis_id": 1,
                "overview": "Project overview..."
            }
        })
        mock_get_service.return_value = mock_service

        response = client.post("/api/graph-workflow/workflow-context", json={
            "project_id": 1,
            "workflow_type": "QUALITY_AUDIT",
            "agent_name": "quinn"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "QUALITY_AUDIT"
        assert "graph_context" in data
        assert "codewiki_context" in data


class TestStatisticsAPI:
    """Test statistics endpoint."""

    def test_get_statistics(self):
        """Test GET /api/graph-workflow/statistics/{project_id}."""
        mock_service = MagicMock()
        mock_service.get_project_statistics = AsyncMock(return_value={
            "project_id": 1,
            "total_entities": 100,
            "total_relations": 200,
            "total_files": 50,
            "entity_counts": {"class": 30, "function": 70},
            "top_referenced_entities": []
        })

        # Patch GraphPersistenceService where it's imported in the endpoint
        with patch(
            "app.services.graph_persistence_service.GraphPersistenceService",
            return_value=mock_service
        ):
            response = client.get("/api/graph-workflow/statistics/1")

        assert response.status_code == 200


class TestRequestValidation:
    """Test request validation."""

    def test_impact_analysis_missing_project_id(self):
        """Test impact analysis requires project_id."""
        response = client.post("/api/graph-workflow/impact-analysis", json={
            "changes": ["UserService"]
        })

        assert response.status_code == 422

    def test_impact_analysis_missing_changes(self):
        """Test impact analysis requires changes."""
        response = client.post("/api/graph-workflow/impact-analysis", json={
            "project_id": 1
        })

        assert response.status_code == 422

    def test_dependency_check_missing_entity_name(self):
        """Test dependency check requires entity_name."""
        response = client.post("/api/graph-workflow/dependency-check", json={
            "project_id": 1
        })

        assert response.status_code == 422

    def test_enhancement_scope_missing_feature_name(self):
        """Test enhancement scope requires feature_name."""
        response = client.post("/api/graph-workflow/enhancement-scope", json={
            "project_id": 1
        })

        assert response.status_code == 422

    def test_sync_document_missing_repo_path(self):
        """Test sync-and-document requires repo_path."""
        response = client.post("/api/graph-workflow/sync-and-document", json={
            "project_id": 1
        })

        assert response.status_code == 422
