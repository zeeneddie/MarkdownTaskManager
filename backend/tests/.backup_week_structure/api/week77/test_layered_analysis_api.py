"""
API Tests for Week 77: Layered Analysis Pipeline

Tests cover:
- Session management endpoints
- Analysis execution endpoints
- Reporting endpoints
- Dashboard endpoint
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app


client = TestClient(app)


# Sample code for testing
SAMPLE_VBSCRIPT = '''
<%
userId = Request.QueryString("id")
sql = "SELECT * FROM users WHERE id = " & userId
Response.Write sql
%>
'''

SAMPLE_SP = '''
CREATE PROCEDURE usp_Test
AS
BEGIN
    SELECT GETDATE()
END
'''


class TestSessionEndpoints:
    """Tests for session management endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('app.api.layered_analysis.get_db') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock_session

    def test_create_session(self, mock_db):
        """Test creating a new analysis session."""
        project_id = str(uuid4())

        with patch('app.services.layered_analysis_service.LayeredAnalysisService.create_session') as mock_create:
            mock_session = MagicMock()
            mock_session.id = uuid4()
            mock_session.project_id = uuid4()
            mock_session.name = "Test Session"
            mock_session.status = "created"
            mock_session.created_at = MagicMock()
            mock_session.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_create.return_value = mock_session

            response = client.post(
                "/api/layered-analysis/sessions",
                json={
                    "project_id": project_id,
                    "name": "Test Session",
                    "description": "Test description"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["name"] == "Test Session"
            assert data["status"] == "created"

    def test_create_session_invalid_name(self, mock_db):
        """Test creating session with invalid name."""
        response = client.post(
            "/api/layered-analysis/sessions",
            json={
                "project_id": str(uuid4()),
                "name": ""  # Empty name
            }
        )

        assert response.status_code == 422  # Validation error

    def test_list_sessions(self, mock_db):
        """Test listing analysis sessions."""
        with patch('app.services.layered_analysis_service.LayeredAnalysisService.list_sessions') as mock_list:
            mock_list.return_value = [
                {
                    "id": str(uuid4()),
                    "project_id": str(uuid4()),
                    "name": "Session 1",
                    "status": "completed",
                    "current_layer": 4,
                    "created_at": "2024-01-01T00:00:00"
                }
            ]

            response = client.get("/api/layered-analysis/sessions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Session 1"

    def test_list_sessions_with_filters(self, mock_db):
        """Test listing sessions with filters."""
        with patch('app.services.layered_analysis_service.LayeredAnalysisService.list_sessions') as mock_list:
            mock_list.return_value = []

            project_id = str(uuid4())
            response = client.get(
                f"/api/layered-analysis/sessions?project_id={project_id}&status=completed"
            )

            assert response.status_code == 200

    def test_get_session(self, mock_db):
        """Test getting session details."""
        session_id = str(uuid4())

        with patch('app.services.layered_analysis_service.LayeredAnalysisService.get_session') as mock_get:
            mock_get.return_value = {
                "id": session_id,
                "name": "Test Session",
                "status": "completed",
                "layers": {}
            }

            response = client.get(f"/api/layered-analysis/sessions/{session_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == session_id

    def test_get_session_not_found(self, mock_db):
        """Test getting non-existent session."""
        session_id = str(uuid4())

        with patch('app.services.layered_analysis_service.LayeredAnalysisService.get_session') as mock_get:
            mock_get.return_value = None

            response = client.get(f"/api/layered-analysis/sessions/{session_id}")

            assert response.status_code == 404

    def test_get_session_summary(self, mock_db):
        """Test getting session summary."""
        session_id = str(uuid4())

        with patch('app.services.layered_analysis_service.LayeredAnalysisService.get_session_summary') as mock_summary:
            mock_summary.return_value = {
                "session_id": session_id,
                "name": "Test",
                "status": "completed",
                "metrics": {"improvement_count": 5}
            }

            response = client.get(f"/api/layered-analysis/sessions/{session_id}/summary")

            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data


class TestAnalysisEndpoints:
    """Tests for analysis execution endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('app.api.layered_analysis.get_db') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock_session

    def test_run_full_analysis(self, mock_db):
        """Test running full analysis."""
        session_id = str(uuid4())

        with patch('app.services.layered_analysis_service.LayeredAnalysisService.run_full_analysis') as mock_run:
            mock_run.return_value = {
                "session_id": session_id,
                "status": "completed",
                "layers": {
                    "vbscript": {"total_lines": 100},
                    "stored_procedures": {"procedure_count": 5},
                    "swot": {"weaknesses": []},
                    "improvement_plan": {"items": []}
                }
            }

            response = client.post(
                f"/api/layered-analysis/sessions/{session_id}/analyze",
                json={
                    "vbscript_code": SAMPLE_VBSCRIPT,
                    "sp_code": SAMPLE_SP,
                    "team_size": 2
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "layers" in data

    def test_run_single_layer(self, mock_db):
        """Test running single layer analysis."""
        session_id = str(uuid4())

        with patch('app.services.layered_analysis_service.LayeredAnalysisService.run_single_layer') as mock_run:
            mock_run.return_value = {
                "total_lines": 50,
                "security_findings": []
            }

            response = client.post(
                f"/api/layered-analysis/sessions/{session_id}/layer",
                json={
                    "layer": 1,
                    "code": SAMPLE_VBSCRIPT
                }
            )

            assert response.status_code == 200

    def test_run_single_layer_invalid(self, mock_db):
        """Test running invalid layer."""
        session_id = str(uuid4())

        response = client.post(
            f"/api/layered-analysis/sessions/{session_id}/layer",
            json={
                "layer": 5,  # Invalid layer
                "code": "test"
            }
        )

        assert response.status_code == 422  # Validation error


class TestImprovementEndpoints:
    """Tests for improvement management endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('app.api.layered_analysis.get_db') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock_session

    def test_update_improvement_status(self, mock_db):
        """Test updating improvement status."""
        item_id = str(uuid4())

        with patch('app.services.layered_analysis_service.LayeredAnalysisService.update_improvement_status') as mock_update:
            mock_update.return_value = {
                "id": item_id,
                "status": "in_progress"
            }

            response = client.patch(
                f"/api/layered-analysis/improvements/{item_id}",
                json={"status": "in_progress"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "in_progress"

    def test_update_improvement_invalid_status(self, mock_db):
        """Test updating with invalid status."""
        item_id = str(uuid4())

        response = client.patch(
            f"/api/layered-analysis/improvements/{item_id}",
            json={"status": "invalid_status"}
        )

        assert response.status_code == 422


class TestReportingEndpoints:
    """Tests for reporting endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('app.api.layered_analysis.get_db') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock_session

    def test_generate_executive_summary(self, mock_db):
        """Test generating executive summary."""
        session_id = str(uuid4())

        with patch('app.services.layered_reporting_service.LayeredReportingService.generate_executive_summary') as mock_gen:
            mock_gen.return_value = {
                "report_id": str(uuid4()),
                "type": "executive_summary",
                "format": "html",
                "content": "<html>Report</html>"
            }

            response = client.post(
                f"/api/layered-analysis/sessions/{session_id}/reports",
                json={
                    "report_type": "executive_summary",
                    "format": "html"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "executive_summary"

    def test_generate_technical_report(self, mock_db):
        """Test generating technical report."""
        session_id = str(uuid4())

        with patch('app.services.layered_reporting_service.LayeredReportingService.generate_technical_report') as mock_gen:
            mock_gen.return_value = {
                "report_id": str(uuid4()),
                "type": "technical_deep_dive",
                "format": "markdown",
                "content": "# Technical Report"
            }

            response = client.post(
                f"/api/layered-analysis/sessions/{session_id}/reports",
                json={
                    "report_type": "technical_deep_dive",
                    "include_code_samples": True
                }
            )

            assert response.status_code == 200

    def test_generate_improvement_backlog(self, mock_db):
        """Test generating improvement backlog."""
        session_id = str(uuid4())

        with patch('app.services.layered_reporting_service.LayeredReportingService.generate_improvement_backlog') as mock_gen:
            mock_gen.return_value = {
                "report_id": str(uuid4()),
                "type": "improvement_backlog",
                "format": "csv",
                "content": "ID,Title,Priority\n1,Fix Bug,High",
                "item_count": 1
            }

            response = client.post(
                f"/api/layered-analysis/sessions/{session_id}/reports",
                json={
                    "report_type": "improvement_backlog",
                    "format": "csv"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["item_count"] == 1

    def test_generate_migration_roadmap(self, mock_db):
        """Test generating migration roadmap."""
        session_id = str(uuid4())

        with patch('app.services.layered_reporting_service.LayeredReportingService.generate_migration_roadmap') as mock_gen:
            mock_gen.return_value = {
                "report_id": str(uuid4()),
                "type": "migration_roadmap",
                "roadmap": {"phases": []},
                "content": "# Roadmap"
            }

            response = client.post(
                f"/api/layered-analysis/sessions/{session_id}/reports",
                json={
                    "report_type": "migration_roadmap",
                    "team_size": 5
                }
            )

            assert response.status_code == 200

    def test_list_reports(self, mock_db):
        """Test listing reports."""
        session_id = str(uuid4())

        with patch('app.services.layered_reporting_service.LayeredReportingService.list_reports') as mock_list:
            mock_list.return_value = [
                {
                    "id": str(uuid4()),
                    "type": "executive_summary",
                    "format": "html",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]

            response = client.get(f"/api/layered-analysis/sessions/{session_id}/reports")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    def test_get_report(self, mock_db):
        """Test getting specific report."""
        report_id = str(uuid4())

        with patch('app.services.layered_reporting_service.LayeredReportingService.get_report') as mock_get:
            mock_get.return_value = {
                "id": report_id,
                "type": "executive_summary",
                "content": "Report content"
            }

            response = client.get(f"/api/layered-analysis/reports/{report_id}")

            assert response.status_code == 200

    def test_get_report_not_found(self, mock_db):
        """Test getting non-existent report."""
        report_id = str(uuid4())

        with patch('app.services.layered_reporting_service.LayeredReportingService.get_report') as mock_get:
            mock_get.return_value = None

            response = client.get(f"/api/layered-analysis/reports/{report_id}")

            assert response.status_code == 404


class TestQuickAnalysisEndpoints:
    """Tests for quick analysis endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('app.api.layered_analysis.get_db') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock_session

    def test_analyze_vbscript_quick(self, mock_db):
        """Test quick VBScript analysis."""
        with patch('app.services.vbscript_analyzer_service.VBScriptAnalyzerService.analyze') as mock_analyze:
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {
                "total_lines": 10,
                "security_findings": [],
                "complexity_score": 5
            }
            mock_analyze.return_value = mock_result

            response = client.post(
                "/api/layered-analysis/analyze/vbscript",
                params={"code": SAMPLE_VBSCRIPT}
            )

            assert response.status_code == 200

    def test_analyze_sp_quick(self, mock_db):
        """Test quick stored procedure analysis."""
        with patch('app.services.stored_procedure_analyzer_service.StoredProcedureAnalyzerService.analyze') as mock_analyze:
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {
                "procedures": [],
                "total_lines": 10
            }
            mock_analyze.return_value = mock_result

            response = client.post(
                "/api/layered-analysis/analyze/stored-procedure",
                params={"code": SAMPLE_SP}
            )

            assert response.status_code == 200


class TestDashboardEndpoint:
    """Tests for dashboard endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('app.api.layered_analysis.get_db') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock_session

    def test_get_dashboard_data(self, mock_db):
        """Test getting dashboard data."""
        with patch('app.services.layered_analysis_service.LayeredAnalysisService.list_sessions') as mock_list:
            mock_list.return_value = [
                {"id": str(uuid4()), "status": "completed"},
                {"id": str(uuid4()), "status": "completed"},
                {"id": str(uuid4()), "status": "failed"}
            ]

            response = client.get("/api/layered-analysis/dashboard")

            assert response.status_code == 200
            data = response.json()
            assert "statistics" in data
            assert "recent_sessions" in data
            assert "layer_info" in data

    def test_dashboard_statistics(self, mock_db):
        """Test dashboard statistics calculation."""
        with patch('app.services.layered_analysis_service.LayeredAnalysisService.list_sessions') as mock_list:
            mock_list.return_value = [
                {"id": str(uuid4()), "status": "completed"},
                {"id": str(uuid4()), "status": "running"},
                {"id": str(uuid4()), "status": "failed"}
            ]

            response = client.get("/api/layered-analysis/dashboard")

            assert response.status_code == 200
            data = response.json()
            stats = data["statistics"]
            assert stats["total_sessions"] == 3
            assert stats["completed"] == 1
            assert stats["in_progress"] == 1
            assert stats["failed"] == 1
