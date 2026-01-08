"""
Week 70 Integration Tests - Migration Analyzer API E2E Tests

Tests the MigrationAnalyzer API endpoints with real database.
All tests use the actual API through httpx AsyncClient.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


# ============================================================================
# HEALTH CHECK TEST
# ============================================================================

class TestMigrationAPIHealth:
    """Basic API health tests."""

    @pytest.mark.asyncio
    async def test_api_health(self):
        """Test API health endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")
        assert response.status_code == 200


# ============================================================================
# CREATE ANALYSIS TESTS
# ============================================================================

class TestCreateAnalysis:
    """Test POST /api/migration/analyze"""

    @pytest.mark.asyncio
    async def test_create_analysis_success(self):
        """Test successful analysis creation."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_create_analysis_minimal(self):
        """Test analysis with minimal parameters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/minimal-test",
                    "target_stack": "react"
                }
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_analysis_missing_repo_path(self):
        """Test analysis creation without required repo_path."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/migration/analyze",
                json={
                    "target_stack": "dotnet8"
                }
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_analysis_empty_body(self):
        """Test analysis creation with empty body."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_list_analyses(self):
        """Test listing analyses."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/migration/analyses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_analyses_with_limit(self):
        """Test listing analyses with limit parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/migration/analyses?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_list_analyses_with_offset(self):
        """Test listing analyses with offset parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/migration/analyses?offset=0&limit=10")
        assert response.status_code == 200


# ============================================================================
# GET ANALYSIS TESTS
# ============================================================================

class TestGetAnalysis:
    """Test GET /api/migration/analyses/{analysis_id}"""

    @pytest.mark.asyncio
    async def test_get_analysis_invalid_id(self):
        """Test getting analysis with invalid ID format."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/migration/analyses/not-a-uuid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self):
        """Test getting non-existent analysis."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_run_analysis_invalid_id(self):
        """Test running analysis with invalid ID."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/migration/analyses/invalid/run")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_run_analysis_not_found(self):
        """Test running non-existent analysis."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_get_modules_not_found(self):
        """Test getting modules for non-existent analysis - returns empty list or 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_get_patterns_not_found(self):
        """Test getting patterns for non-existent analysis - returns empty list or 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_get_recommendations_not_found(self):
        """Test getting recommendations for non-existent analysis - returns empty list or 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_get_risks_not_found(self):
        """Test getting risks for non-existent analysis - returns empty list or 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_get_summary_not_found(self):
        """Test getting summary for non-existent analysis."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/migration/analyses/00000000-0000-0000-0000-000000000000/summary"
            )
        assert response.status_code == 404


# ============================================================================
# E2E WORKFLOW TESTS
# ============================================================================

class TestE2EWorkflow:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    async def test_create_and_list(self):
        """Test create analysis and then list."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create
            create_response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/e2e-test",
                    "target_stack": "dotnet8"
                }
            )
            assert create_response.status_code == 200
            created = create_response.json()
            created_id = created["id"]

            # List and verify our analysis is included
            list_response = await client.get("/api/migration/analyses?limit=100")
            assert list_response.status_code == 200
            analyses = list_response.json()
            ids = [a["id"] for a in analyses]
            assert created_id in ids

    @pytest.mark.asyncio
    async def test_create_and_get(self):
        """Test create and then get analysis."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create
            create_response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/get-test",
                    "target_stack": "react"
                }
            )
            assert create_response.status_code == 200
            created_id = create_response.json()["id"]

            # Get
            get_response = await client.get(f"/api/migration/analyses/{created_id}")
            assert get_response.status_code == 200
            retrieved = get_response.json()
            assert retrieved["id"] == created_id
            assert retrieved["repo_name"] == "get-test"

    @pytest.mark.asyncio
    async def test_create_get_modules(self):
        """Test create analysis then get modules."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create
            create_response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/modules-test",
                    "target_stack": "dotnet8"
                }
            )
            assert create_response.status_code == 200
            analysis_id = create_response.json()["id"]

            # Get modules (should be empty for new analysis)
            modules_response = await client.get(
                f"/api/migration/analyses/{analysis_id}/modules"
            )
            assert modules_response.status_code == 200
            modules = modules_response.json()
            assert isinstance(modules, list)

    @pytest.mark.asyncio
    async def test_create_get_patterns(self):
        """Test create analysis then get patterns."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create
            create_response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/patterns-test",
                    "target_stack": "dotnet8"
                }
            )
            assert create_response.status_code == 200
            analysis_id = create_response.json()["id"]

            # Get patterns
            patterns_response = await client.get(
                f"/api/migration/analyses/{analysis_id}/patterns"
            )
            assert patterns_response.status_code == 200


# ============================================================================
# TARGET CONFIGURATION TESTS
# ============================================================================

class TestTargetConfigurations:
    """Test various target stack configurations."""

    @pytest.mark.asyncio
    async def test_dotnet8_target(self):
        """Test .NET 8 target stack."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_react_target(self):
        """Test React target stack."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/react-test",
                    "target_stack": "react"
                }
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_vue3_target(self):
        """Test Vue 3 target stack."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/vue3-test",
                    "target_stack": "vue3"
                }
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_spring_boot_target(self):
        """Test Spring Boot target stack."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_postgresql_target(self):
        """Test PostgreSQL target database."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/pg-test",
                    "target_stack": "dotnet8",
                    "target_db": "postgresql"
                }
            )
        assert response.status_code == 200
        assert response.json()["target_db"] == "postgresql"

    @pytest.mark.asyncio
    async def test_mysql_target(self):
        """Test MySQL target database."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async def test_no_database_target(self):
        """Test analysis without database target."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/migration/analyze",
                json={
                    "repo_path": "/tmp/no-db-test",
                    "target_stack": "react"
                }
            )
        assert response.status_code == 200
