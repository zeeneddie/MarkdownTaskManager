"""
API tests for Week 131 Research endpoints.

Tests for background job detection, load estimation, and documentation rule extraction APIs.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_project():
    """Create a temporary project directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create sample files for testing
        (project_path / "BatchJob.vb").write_text("""
        Public Class BatchJob
            Private Sub Timer_Elapsed(sender As Object, e As ElapsedEventArgs)
                ProcessData()
            End Sub
        End Class
        """)

        (project_path / "web.config").write_text("""<?xml version="1.0"?>
        <configuration>
            <connectionStrings>
                <add name="Main" connectionString="Server=db;Max Pool Size=100" />
            </connectionStrings>
            <system.web>
                <sessionState mode="InProc" timeout="20" />
            </system.web>
        </configuration>
        """)

        (project_path / "rules.md").write_text("""
        # Business Rules

        Rule: All users must authenticate before checkout.
        Business Rule: Orders must have valid customer ID.

        IF payment fails THEN notify customer.
        """)

        yield str(project_path)


class TestBackgroundJobsAPI:
    """Tests for background jobs detection API."""

    def test_analyze_background_jobs_success(self, client, temp_project):
        """Test successful background job analysis."""
        response = client.post(
            "/api/research/background-jobs/analyze",
            json={"project_path": temp_project}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "jobs" in data
        assert "total_jobs" in data

    def test_analyze_background_jobs_nonexistent_path(self, client):
        """Test analysis with non-existent path."""
        response = client.post(
            "/api/research/background-jobs/analyze",
            json={"project_path": "/nonexistent/path/xyz123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0

    def test_analyze_background_jobs_with_extensions(self, client, temp_project):
        """Test analysis with specific extensions filter."""
        response = client.post(
            "/api/research/background-jobs/analyze",
            json={
                "project_path": temp_project,
                "include_extensions": [".vb", ".cs"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestLoadEstimationAPI:
    """Tests for load estimation API."""

    def test_analyze_load_estimation_success(self, client, temp_project):
        """Test successful load estimation analysis."""
        response = client.post(
            "/api/research/load-estimation/analyze",
            json={"project_path": temp_project}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connection_pools" in data
        assert "estimated_concurrent_users" in data

    def test_analyze_load_estimation_nonexistent_path(self, client):
        """Test load estimation with non-existent path."""
        response = client.post(
            "/api/research/load-estimation/analyze",
            json={"project_path": "/nonexistent/path/xyz123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_analyze_load_estimation_with_sql(self, client, temp_project):
        """Test load estimation with SQL analysis enabled."""
        response = client.post(
            "/api/research/load-estimation/analyze",
            json={
                "project_path": temp_project,
                "include_sql_analysis": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestDocumentationRulesAPI:
    """Tests for documentation rule extraction API."""

    def test_extract_documentation_rules_success(self, client, temp_project):
        """Test successful documentation rule extraction."""
        response = client.post(
            "/api/research/documentation-rules/extract",
            json={"project_path": temp_project}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rules" in data
        assert "total_rules" in data

    def test_extract_documentation_rules_nonexistent_path(self, client):
        """Test extraction with non-existent path."""
        response = client.post(
            "/api/research/documentation-rules/extract",
            json={"project_path": "/nonexistent/path/xyz123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_extract_with_code_rules_correlation(self, client, temp_project):
        """Test extraction with code rules for correlation."""
        code_rules = [
            {"rule_id": "BR-001", "natural_language": "Orders require customer"}
        ]
        response = client.post(
            "/api/research/documentation-rules/extract",
            json={
                "project_path": temp_project,
                "code_rules": code_rules
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestResearchSummaryAPI:
    """Tests for combined research summary API."""

    def test_get_summary_all_analyses(self, client, temp_project):
        """Test getting summary of all research analyses."""
        # First run all analyses
        client.post(
            "/api/research/background-jobs/analyze",
            json={"project_path": temp_project}
        )
        client.post(
            "/api/research/load-estimation/analyze",
            json={"project_path": temp_project}
        )
        client.post(
            "/api/research/documentation-rules/extract",
            json={"project_path": temp_project}
        )

        # Get summary
        response = client.get(f"/api/research/summary/{temp_project.replace('/', '_')}")
        assert response.status_code in [200, 404]  # 404 if not stored in DB
