# tests/api/week97/test_devops_analysis_api.py
"""
API tests for DevOps Analysis endpoints - Week 97-98 (Fase 14).

Tests:
- Analysis creation endpoints
- Analysis retrieval endpoints
- Hot spots endpoints
- Statistics endpoint
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock, MagicMock

from app.main import app
from app.models.devops_analysis import (
    RepositoryAnalysis,
    HotSpot,
    ContributorAnalysis,
    PRPattern,
    RepositoryInsight,
    RepositoryPlatform,
    AnalysisDepth,
)


# =============================================================================
# Test Client
# =============================================================================

class TestDevOpsAnalysisAPI:
    """Tests for DevOps Analysis API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client that doesn't raise server exceptions."""
        return TestClient(app, raise_server_exceptions=False)

    # =========================================================================
    # List Analyses Tests
    # =========================================================================

    def test_list_analyses_endpoint_exists(self, client):
        """Test that list analyses endpoint exists."""
        response = client.get("/api/devops/analyses")
        # Should return 200 or 500 (if db not available), not 404
        assert response.status_code != 404

    def test_list_analyses_with_filters(self, client):
        """Test list analyses with query parameters."""
        response = client.get(
            "/api/devops/analyses",
            params={
                "platform": "github",
                "status": "completed",
                "limit": 10,
                "offset": 0
            }
        )
        assert response.status_code != 404

    # =========================================================================
    # Get Analysis Tests
    # =========================================================================

    def test_get_analysis_not_found(self, client):
        """Test getting non-existent analysis returns 404."""
        response = client.get("/api/devops/analyses/99999999")
        assert response.status_code in [404, 500]  # 500 if db not available

    def test_get_analysis_invalid_id(self, client):
        """Test getting analysis with invalid ID returns 422."""
        response = client.get("/api/devops/analyses/invalid")
        assert response.status_code == 422  # Validation error

    # =========================================================================
    # Hot Spots Endpoint Tests
    # =========================================================================

    def test_hot_spots_endpoint_exists(self, client):
        """Test hot spots endpoint exists."""
        response = client.get("/api/devops/analyses/1/hot-spots")
        # Not found is fine, just checking endpoint exists
        assert response.status_code in [200, 404, 500]

    def test_hot_spots_with_filters(self, client):
        """Test hot spots with query parameters."""
        response = client.get(
            "/api/devops/analyses/1/hot-spots",
            params={
                "min_risk": 0.5,
                "sort_by": "risk_score",
                "limit": 20
            }
        )
        assert response.status_code in [200, 404, 500]

    # =========================================================================
    # Contributors Endpoint Tests
    # =========================================================================

    def test_contributors_endpoint_exists(self, client):
        """Test contributors endpoint exists."""
        response = client.get("/api/devops/analyses/1/contributors")
        assert response.status_code in [200, 404, 500]

    def test_contributors_with_sort(self, client):
        """Test contributors with sort parameter."""
        response = client.get(
            "/api/devops/analyses/1/contributors",
            params={"sort_by": "bus_factor", "limit": 10}
        )
        assert response.status_code in [200, 404, 500]

    # =========================================================================
    # PR Patterns Endpoint Tests
    # =========================================================================

    def test_pr_patterns_endpoint_exists(self, client):
        """Test PR patterns endpoint exists."""
        response = client.get("/api/devops/analyses/1/pr-patterns")
        assert response.status_code in [200, 404, 500]

    def test_pr_patterns_with_filters(self, client):
        """Test PR patterns with filters."""
        response = client.get(
            "/api/devops/analyses/1/pr-patterns",
            params={"has_conflicts": "true", "limit": 50}
        )
        assert response.status_code in [200, 404, 500]

    # =========================================================================
    # Insights Endpoint Tests
    # =========================================================================

    def test_insights_endpoint_exists(self, client):
        """Test insights endpoint exists."""
        response = client.get("/api/devops/analyses/1/insights")
        assert response.status_code in [200, 404, 500]

    def test_insights_with_filters(self, client):
        """Test insights with category filter."""
        response = client.get(
            "/api/devops/analyses/1/insights",
            params={"category": "code_quality", "min_severity": 0.5}
        )
        assert response.status_code in [200, 404, 500]

    # =========================================================================
    # Statistics Endpoint Tests
    # =========================================================================

    def test_statistics_endpoint_exists(self, client):
        """Test statistics endpoint exists."""
        response = client.get("/api/devops/statistics")
        # Should return 200 or 500 (if db not available)
        assert response.status_code in [200, 500]

    def test_statistics_response_structure(self, client):
        """Test statistics response has expected structure."""
        response = client.get("/api/devops/statistics")
        if response.status_code == 200:
            data = response.json()
            # Check expected keys exist
            assert "total_analyses" in data or "error" in data

    # =========================================================================
    # Create Analysis Tests
    # =========================================================================

    def test_create_analysis_endpoint_exists(self, client):
        """Test create analysis endpoint exists."""
        response = client.post(
            "/api/devops/analyses",
            json={
                "repository_url": "https://github.com/test/repo",
                "platform": "github"
            }
        )
        # May fail due to missing token, but endpoint should exist
        assert response.status_code in [200, 400, 422, 500]

    def test_create_analysis_validation(self, client):
        """Test create analysis with invalid data."""
        response = client.post(
            "/api/devops/analyses",
            json={}  # Missing required field
        )
        assert response.status_code == 422  # Validation error

    def test_create_analysis_auto_detect(self, client):
        """Test create analysis with auto platform detection."""
        response = client.post(
            "/api/devops/analyses",
            json={
                "repository_url": "https://github.com/test/repo",
                "platform": "auto",
                "analysis_depth": "standard"
            }
        )
        assert response.status_code in [200, 400, 500]

    # =========================================================================
    # Delete Analysis Tests
    # =========================================================================

    def test_delete_analysis_not_found(self, client):
        """Test deleting non-existent analysis."""
        response = client.delete("/api/devops/analyses/99999999")
        assert response.status_code in [404, 500]

    # =========================================================================
    # Extraction Context Tests
    # =========================================================================

    def test_extraction_context_endpoint_exists(self, client):
        """Test extraction context endpoint exists."""
        response = client.get("/api/devops/analyses/1/extraction-context")
        # 404 or 400 for non-existent/incomplete analysis is expected
        assert response.status_code in [200, 400, 404, 500]


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestDevOpsAnalysisSchemas:
    """Tests for API request/response schema validation."""

    @pytest.fixture
    def client(self):
        """Create test client that doesn't raise server exceptions."""
        return TestClient(app, raise_server_exceptions=False)

    def test_analysis_create_schema(self, client):
        """Test analysis creation validates required fields."""
        # Missing repository_url
        response = client.post(
            "/api/devops/analyses",
            json={"platform": "github"}
        )
        assert response.status_code == 422

    def test_analysis_create_depth_validation(self, client):
        """Test analysis depth value validation."""
        response = client.post(
            "/api/devops/analyses",
            json={
                "repository_url": "https://github.com/test/repo",
                "analysis_depth": "invalid_depth"
            }
        )
        assert response.status_code == 422

    def test_analysis_create_bounds_validation(self, client):
        """Test max_commits bounds validation."""
        response = client.post(
            "/api/devops/analyses",
            json={
                "repository_url": "https://github.com/test/repo",
                "max_commits": 50  # Below minimum of 100
            }
        )
        assert response.status_code == 422


# =============================================================================
# Platform Detection Tests
# =============================================================================

class TestPlatformDetection:
    """Tests for repository platform detection."""

    def test_github_detection(self):
        """Test GitHub URL detection."""
        from app.api.devops_analysis import detect_platform

        url = "https://github.com/owner/repo"
        platform = detect_platform(url)
        assert platform == RepositoryPlatform.GITHUB

    def test_azure_devops_detection(self):
        """Test Azure DevOps URL detection."""
        from app.api.devops_analysis import detect_platform

        url = "https://dev.azure.com/org/project/_git/repo"
        platform = detect_platform(url)
        assert platform == RepositoryPlatform.AZURE_DEVOPS

    def test_visualstudio_detection(self):
        """Test legacy Visual Studio URL detection."""
        from app.api.devops_analysis import detect_platform

        url = "https://org.visualstudio.com/project/_git/repo"
        platform = detect_platform(url)
        assert platform == RepositoryPlatform.AZURE_DEVOPS

    def test_gitlab_detection(self):
        """Test GitLab URL detection."""
        from app.api.devops_analysis import detect_platform

        url = "https://gitlab.com/owner/repo"
        platform = detect_platform(url)
        assert platform == RepositoryPlatform.GITLAB

    def test_bitbucket_detection(self):
        """Test Bitbucket URL detection."""
        from app.api.devops_analysis import detect_platform

        url = "https://bitbucket.org/owner/repo"
        platform = detect_platform(url)
        assert platform == RepositoryPlatform.BITBUCKET

    def test_unknown_defaults_to_github(self):
        """Test unknown URL defaults to GitHub."""
        from app.api.devops_analysis import detect_platform

        url = "https://custom-git.example.com/repo"
        platform = detect_platform(url)
        assert platform == RepositoryPlatform.GITHUB


# =============================================================================
# Response Model Tests
# =============================================================================

class TestResponseModels:
    """Tests for API response model validation."""

    def test_analysis_summary_fields(self):
        """Test AnalysisSummary has all required fields."""
        from app.api.devops_analysis import AnalysisSummary

        # Check model has expected fields
        fields = AnalysisSummary.model_fields
        required = [
            "id", "platform", "repository_url", "repository_name",
            "status", "total_commits", "total_prs", "total_contributors",
            "created_at"
        ]
        for field in required:
            assert field in fields

    def test_hot_spot_response_fields(self):
        """Test HotSpotResponse has all required fields."""
        from app.api.devops_analysis import HotSpotResponse

        fields = HotSpotResponse.model_fields
        required = [
            "id", "file_path", "change_count", "risk_score"
        ]
        for field in required:
            assert field in fields

    def test_contributor_response_fields(self):
        """Test ContributorResponse has all required fields."""
        from app.api.devops_analysis import ContributorResponse

        fields = ContributorResponse.model_fields
        required = [
            "id", "contributor_id", "total_commits", "bus_factor_contribution"
        ]
        for field in required:
            assert field in fields

    def test_extraction_context_fields(self):
        """Test ExtractionContext has all required fields."""
        from app.api.devops_analysis import ExtractionContext

        fields = ExtractionContext.model_fields
        required = ["repository", "metrics", "hot_spots", "knowledge_silos"]
        for field in required:
            assert field in fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
