"""
Tests for Dead Code Analysis API - Week 132-133

Tests API endpoints for dead code detection, runtime analysis, and coverage.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.dead_code import (
    DeadCodeItemType,
    RemovalRisk,
    APMProvider,
    CoverageSource,
)


@pytest.fixture
def temp_project():
    """Create a temporary project with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Python file
        py_file = Path(tmpdir) / "app.py"
        py_file.write_text('''
def used_function():
    return 42

def _unused_function():
    pass
''')

        # Create coverage file
        coverage_dir = Path(tmpdir) / "coverage"
        coverage_dir.mkdir()
        coverage_file = coverage_dir / "coverage-final.json"
        coverage_data = {
            "app.py": {
                "fnMap": {"0": {"name": "used_function"}, "1": {"name": "_unused_function"}},
                "f": {"0": 100, "1": 0},
                "s": {"0": 100, "1": 0},
                "b": {}
            }
        }
        coverage_file.write_text(json.dumps(coverage_data))

        yield tmpdir


class TestDeadCodeDetectionAPI:
    """Tests for dead code detection endpoints."""

    @pytest.mark.asyncio
    async def test_detect_dead_code(self, temp_project):
        """Test POST /api/dead-code/detect endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/detect",
                json={
                    "project_path": temp_project,
                    "confidence_threshold": 0.3
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "dead_code_count" in data
            assert "project_path" in data

    @pytest.mark.asyncio
    async def test_detect_with_language_filter(self, temp_project):
        """Test detection with language filter."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/detect",
                json={
                    "project_path": temp_project,
                    "include_languages": ["python"]
                }
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_detect_nonexistent_path(self):
        """Test detection with non-existent path."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/detect",
                json={"project_path": "/nonexistent/path"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    @pytest.mark.asyncio
    async def test_generate_cleanup_script(self, temp_project):
        """Test POST /api/dead-code/detect/cleanup-script endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/detect/cleanup-script",
                json={"project_path": temp_project},
                params={"safe_only": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert "script" in data
            assert "items_count" in data

    @pytest.mark.asyncio
    async def test_get_dead_code_analysis(self):
        """Test GET /api/dead-code/detect/{project_id} endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/dead-code/detect/test-project-id")

            assert response.status_code == 200
            data = response.json()
            assert "project_id" in data


class TestRuntimeAnalysisAPI:
    """Tests for runtime analysis endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_runtime(self, temp_project):
        """Test POST /api/dead-code/runtime/analyze endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/runtime/analyze",
                json={
                    "project_path": temp_project,
                    "analysis_days": 30
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "project_path" in data

    @pytest.mark.asyncio
    async def test_analyze_with_apm_provider(self, temp_project):
        """Test runtime analysis with APM provider."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/runtime/analyze",
                json={
                    "project_path": temp_project,
                    "apm_provider": "new_relic",
                    "api_key": "test-key"
                }
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_endpoint_coverage(self, temp_project):
        """Test POST /api/dead-code/runtime/endpoint-coverage endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/runtime/endpoint-coverage",
                params={"project_path": temp_project},
                json=[
                    {"path": "/api/users", "method": "GET", "handler": "get_users"},
                    {"path": "/api/products", "method": "GET", "handler": "get_products"}
                ]
            )

            assert response.status_code == 200
            data = response.json()
            assert "total_defined" in data

    @pytest.mark.asyncio
    async def test_get_runtime_analysis(self):
        """Test GET /api/dead-code/runtime/{project_id} endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/dead-code/runtime/test-project-id")

            assert response.status_code == 200


class TestCoverageAnalysisAPI:
    """Tests for coverage analysis endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_coverage(self, temp_project):
        """Test POST /api/dead-code/coverage/analyze endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/coverage/analyze",
                json={
                    "project_path": temp_project,
                    "include_file_details": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "line_coverage_percentage" in data or "errors" in data

    @pytest.mark.asyncio
    async def test_analyze_with_thresholds(self, temp_project):
        """Test coverage analysis with custom thresholds."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/coverage/analyze",
                json={
                    "project_path": temp_project,
                    "line_threshold": 90.0,
                    "branch_threshold": 80.0,
                    "function_threshold": 85.0
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "threshold_check" in data

    @pytest.mark.asyncio
    async def test_check_thresholds(self, temp_project):
        """Test POST /api/dead-code/coverage/check-thresholds endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/coverage/check-thresholds",
                json={
                    "project_path": temp_project,
                    "line_threshold": 50.0
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "project_path" in data

    @pytest.mark.asyncio
    async def test_get_coverage_analysis(self):
        """Test GET /api/dead-code/coverage/{project_id} endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/dead-code/coverage/test-project-id")

            assert response.status_code == 200


class TestCombinedAnalysisAPI:
    """Tests for combined analysis endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_combined(self, temp_project):
        """Test POST /api/dead-code/analyze/combined endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/analyze/combined",
                json={
                    "project_path": temp_project,
                    "include_static": True,
                    "include_runtime": True,
                    "include_coverage": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "analysis_id" in data
            assert "summary" in data

    @pytest.mark.asyncio
    async def test_combined_static_only(self, temp_project):
        """Test combined analysis with static only."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/analyze/combined",
                json={
                    "project_path": temp_project,
                    "include_static": True,
                    "include_runtime": False,
                    "include_coverage": False
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "static_analysis" in data
            assert "runtime_analysis" not in data or data["runtime_analysis"] is None

    @pytest.mark.asyncio
    async def test_combined_cross_validation(self, temp_project):
        """Test combined analysis with cross-validation."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/analyze/combined",
                json={
                    "project_path": temp_project,
                    "include_static": True,
                    "include_runtime": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            # Cross-validation should be present when both static and runtime are included
            if data.get("static_analysis") and data.get("runtime_analysis"):
                assert "cross_validation" in data

    @pytest.mark.asyncio
    async def test_get_analysis_summary(self):
        """Test GET /api/dead-code/summary/{project_id} endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/dead-code/summary/test-project-id")

            assert response.status_code == 200


class TestRequestValidation:
    """Tests for request validation."""

    @pytest.mark.asyncio
    async def test_missing_project_path(self):
        """Test request without project_path."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/detect",
                json={}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_confidence_threshold(self):
        """Test request with invalid confidence threshold."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/detect",
                json={
                    "project_path": "/tmp/test",
                    "confidence_threshold": 1.5  # Invalid: > 1.0
                }
            )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_analysis_days(self):
        """Test request with invalid analysis_days."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/dead-code/runtime/analyze",
                json={
                    "project_path": "/tmp/test",
                    "analysis_days": 500  # Invalid: > 365
                }
            )

            assert response.status_code == 422
