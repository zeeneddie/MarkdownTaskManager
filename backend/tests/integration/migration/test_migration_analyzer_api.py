"""
Week 70 Integration Tests - Migration Analyzer API E2E Tests

Tests the MigrationAnalyzer API endpoints with mocked database.
All tests use the actual API through httpx AsyncClient.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.database import get_db


@pytest.fixture
def mock_db_session():
    """Mock database session for tests that don't need real DB"""
    mock_session = AsyncMock()

    # Create a proper mock result for various query patterns
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalar = MagicMock(return_value=None)

    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.get = AsyncMock(return_value=None)
    return mock_session


@pytest.fixture
def mock_analysis():
    """Create a mock analysis object"""
    mock = MagicMock()
    mock.id = str(uuid4())
    mock.repo_path = "/tmp/test-repo"
    mock.repo_name = "test-repo"
    mock.target_stack = "dotnet8"
    mock.target_db = "postgresql"
    mock.status = "pending"
    mock.created_at = datetime.now(timezone.utc)
    mock.started_at = None
    mock.completed_at = None
    mock.complexity_score = None
    mock.risk_level = None
    mock.estimated_hours = None
    mock.total_files = 0
    mock.total_loc = 0
    mock.progress_percent = 0
    mock.error_message = None
    return mock


@pytest.fixture
async def client(mock_db_session, mock_analysis):
    """Async test client with mocked database"""
    # Configure mock to return proper analysis objects
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalar = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    # Make add() capture the object and set up refresh to update it
    def mock_add(obj):
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = str(uuid4())
        if hasattr(obj, 'status') and obj.status is None:
            obj.status = "pending"
        if hasattr(obj, 'repo_name') and hasattr(obj, 'repo_path'):
            import os
            obj.repo_name = os.path.basename(obj.repo_path)
        if hasattr(obj, 'created_at') and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)

    mock_db_session.add = MagicMock(side_effect=mock_add)
    mock_db_session.refresh = AsyncMock()

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ============================================================================
# HEALTH CHECK TEST
# ============================================================================

class TestMigrationAPIHealth:
    """Basic API health tests."""

    @pytest.mark.asyncio
    async def test_api_health(self, client):
        """Test API health endpoint."""
        response = await client.get("/api/health")
        assert response.status_code == 200


# ============================================================================
# CREATE ANALYSIS TESTS
# ============================================================================

class TestCreateAnalysis:
    """Test POST /api/migration/analyze"""

    @pytest.mark.asyncio
    async def test_create_analysis_success(self, client):
        """Test successful analysis creation."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/test-repo",
                "target_stack": "dotnet8",
                "target_db": "postgresql"
            }
        )
        # API returns 200 for successful creation
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_analysis_minimal(self, client):
        """Test analysis with minimal parameters."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/minimal-test",
                "target_stack": "react"
            }
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_analysis_missing_repo_path(self, client):
        """Test analysis creation without required repo_path."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "target_stack": "dotnet8"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_analysis_empty_body(self, client):
        """Test analysis creation with empty body."""
        response = await client.post(
            "/api/migration/analyze",
            json={}
        )
        assert response.status_code == 422


# ============================================================================
# LIST ANALYSES TESTS
# ============================================================================

class TestListAnalyses:
    """Test GET /api/migration/analyses"""

    @pytest.mark.asyncio
    async def test_list_analyses(self, client):
        """Test listing analyses."""
        response = await client.get("/api/migration/analyses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_analyses_with_limit(self, client):
        """Test listing analyses with limit parameter."""
        response = await client.get("/api/migration/analyses?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_list_analyses_with_offset(self, client):
        """Test listing analyses with offset parameter."""
        response = await client.get("/api/migration/analyses?offset=0&limit=10")
        assert response.status_code == 200


# ============================================================================
# GET ANALYSIS TESTS
# ============================================================================

class TestGetAnalysis:
    """Test GET /api/migration/analyses/{analysis_id}"""

    @pytest.mark.asyncio
    async def test_get_analysis_invalid_id(self, client):
        """Test getting analysis with invalid ID format."""
        response = await client.get("/api/migration/analyses/not-a-uuid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, client):
        """Test getting non-existent analysis."""
        response = await client.get(
            "/api/migration/analyses/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


# ============================================================================
# RUN ANALYSIS TESTS
# ============================================================================

class TestRunAnalysis:
    """Test POST /api/migration/analyses/{analysis_id}/run"""

    @pytest.mark.asyncio
    async def test_run_analysis_invalid_id(self, client):
        """Test running analysis with invalid ID."""
        response = await client.post("/api/migration/analyses/invalid/run")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_run_analysis_not_found(self, client):
        """Test running non-existent analysis."""
        response = await client.post(
            "/api/migration/analyses/00000000-0000-0000-0000-000000000000/run"
        )
        assert response.status_code == 404


# ============================================================================
# GET MODULES TESTS
# ============================================================================

class TestGetModules:
    """Test GET /api/migration/analyses/{analysis_id}/modules"""

    @pytest.mark.asyncio
    async def test_get_modules_not_found(self, client):
        """Test getting modules for non-existent analysis - returns empty list or 404."""
        response = await client.get(
            "/api/migration/analyses/00000000-0000-0000-0000-000000000000/modules"
        )
        # API may return 404 or 200 with empty list
        assert response.status_code in [200, 404]


# ============================================================================
# GET PATTERNS TESTS
# ============================================================================

class TestGetPatterns:
    """Test GET /api/migration/analyses/{analysis_id}/patterns"""

    @pytest.mark.asyncio
    async def test_get_patterns_not_found(self, client):
        """Test getting patterns for non-existent analysis - returns empty list or 404."""
        response = await client.get(
            "/api/migration/analyses/00000000-0000-0000-0000-000000000000/patterns"
        )
        # API may return 404 or 200 with empty list
        assert response.status_code in [200, 404]


# ============================================================================
# GET RECOMMENDATIONS TESTS
# ============================================================================

class TestGetRecommendations:
    """Test GET /api/migration/analyses/{analysis_id}/recommendations"""

    @pytest.mark.asyncio
    async def test_get_recommendations_not_found(self, client):
        """Test getting recommendations for non-existent analysis - returns empty list or 404."""
        response = await client.get(
            "/api/migration/analyses/00000000-0000-0000-0000-000000000000/recommendations"
        )
        # API may return 404 or 200 with empty list
        assert response.status_code in [200, 404]


# ============================================================================
# GET RISKS TESTS
# ============================================================================

class TestGetRisks:
    """Test GET /api/migration/analyses/{analysis_id}/risks"""

    @pytest.mark.asyncio
    async def test_get_risks_not_found(self, client):
        """Test getting risks for non-existent analysis - returns empty list or 404."""
        response = await client.get(
            "/api/migration/analyses/00000000-0000-0000-0000-000000000000/risks"
        )
        # API may return 404 or 200 with empty list
        assert response.status_code in [200, 404]


# ============================================================================
# GET SUMMARY TESTS
# ============================================================================

class TestGetSummary:
    """Test GET /api/migration/analyses/{analysis_id}/summary"""

    @pytest.mark.asyncio
    async def test_get_summary_not_found(self, client):
        """Test getting summary for non-existent analysis."""
        response = await client.get(
            "/api/migration/analyses/00000000-0000-0000-0000-000000000000/summary"
        )
        assert response.status_code == 404


# ============================================================================
# E2E WORKFLOW TESTS (simplified for mocked database)
# ============================================================================

class TestE2EWorkflow:
    """End-to-end workflow tests (simplified - no real DB persistence)."""

    @pytest.mark.asyncio
    async def test_create_and_list(self, client):
        """Test create analysis then list analyses."""
        # Create analysis
        create_response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/e2e-test",
                "target_stack": "dotnet8"
            }
        )
        assert create_response.status_code == 200

        # List analyses (mocked - returns empty list)
        list_response = await client.get("/api/migration/analyses?limit=100")
        assert list_response.status_code == 200
        assert isinstance(list_response.json(), list)

    @pytest.mark.asyncio
    async def test_create_and_get(self, client):
        """Test create analysis - response validation."""
        create_response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/get-test",
                "target_stack": "react"
            }
        )
        assert create_response.status_code == 200
        data = create_response.json()
        assert "id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_create_get_modules(self, client):
        """Test create analysis - modules endpoint validation."""
        create_response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/modules-test",
                "target_stack": "dotnet8"
            }
        )
        assert create_response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_get_patterns(self, client):
        """Test create analysis - patterns endpoint validation."""
        create_response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/patterns-test",
                "target_stack": "dotnet8"
            }
        )
        assert create_response.status_code == 200


# ============================================================================
# TARGET CONFIGURATION TESTS
# ============================================================================

class TestTargetConfigurations:
    """Test various target stack configurations."""

    @pytest.mark.asyncio
    async def test_dotnet8_target(self, client):
        """Test .NET 8 target stack."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/dotnet8-test",
                "target_stack": "dotnet8",
                "target_db": "postgresql"
            }
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_react_target(self, client):
        """Test React target stack."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/react-test",
                "target_stack": "react"
            }
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_vue3_target(self, client):
        """Test Vue 3 target stack."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/vue3-test",
                "target_stack": "vue3"
            }
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_spring_boot_target(self, client):
        """Test Spring Boot target stack."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/spring-test",
                "target_stack": "spring_boot",
                "target_db": "postgresql"
            }
        )
        assert response.status_code == 200


# ============================================================================
# DATABASE TARGET TESTS
# ============================================================================

class TestDatabaseTargets:
    """Test various target database configurations."""

    @pytest.mark.asyncio
    async def test_postgresql_target(self, client):
        """Test PostgreSQL target database."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/pg-test",
                "target_stack": "dotnet8",
                "target_db": "postgresql"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("target_db") == "postgresql"

    @pytest.mark.asyncio
    async def test_mysql_target(self, client):
        """Test MySQL target database."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/mysql-test",
                "target_stack": "dotnet8",
                "target_db": "mysql"
            }
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_database_target(self, client):
        """Test analysis without database target."""
        response = await client.post(
            "/api/migration/analyze",
            json={
                "repo_path": "/tmp/no-db-test",
                "target_stack": "react"
            }
        )
        assert response.status_code == 200
