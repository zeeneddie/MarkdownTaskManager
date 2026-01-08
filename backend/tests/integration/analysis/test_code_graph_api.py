"""
Week 75: Code Graph API Tests

Tests for the Code Graph REST API endpoints.
Covers sync, entity operations, impact analysis, coupling, snapshots, and export.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.models.code_graph import (
    CodeGraphEntity,
    CodeGraphRelation,
    CodeGraphSnapshot,
    CodeGraphImpactCache,
    CodeGraphModuleCoupling
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def sample_entity_id():
    """Generate a sample entity UUID."""
    return uuid4()


@pytest.fixture
def sample_entity(sample_entity_id):
    """Create a sample code entity."""
    entity = CodeGraphEntity(
        id=sample_entity_id,
        project_id=1,
        entity_type="class",
        name="TestService",
        qualified_name="app.services.TestService",
        file_path="app/services/test_service.py",
        start_line=10,
        end_line=100,
        docstring="Test service class",
        signature="class TestService:",
        entity_data={},
        metrics={"lines": 90},
        hash="abc123"
    )
    return entity


@pytest.fixture
async def async_client(mock_db):
    """Create async test client with mocked database."""
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# =============================================================================
# SYNC ENDPOINT TESTS
# =============================================================================

class TestSyncEndpoint:
    """Tests for POST /api/code-graph/sync."""

    @pytest.mark.asyncio
    async def test_sync_invalid_path(self, async_client, mock_db):
        """Test sync with invalid repository path."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.sync_project_graph',
                   return_value={"error": "Repository path not found"}):
            response = await async_client.post(
                "/api/code-graph/sync",
                json={
                    "project_id": 1,
                    "repo_path": "/nonexistent/path",
                    "languages": ["python"]
                }
            )

            assert response.status_code == 400
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_sync_success(self, async_client, mock_db):
        """Test successful sync operation."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.sync_project_graph',
                   return_value={
                       "success": True,
                       "project_id": 1,
                       "repo_path": "/valid/path",
                       "entities_added": 50,
                       "entities_updated": 10,
                       "relations_added": 100,
                       "files_processed": 20
                   }):
            response = await async_client.post(
                "/api/code-graph/sync",
                json={
                    "project_id": 1,
                    "repo_path": "/valid/path",
                    "languages": ["python"]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["entities_added"] == 50


# =============================================================================
# ENTITY ENDPOINT TESTS
# =============================================================================

class TestEntityEndpoints:
    """Tests for entity CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_get_entity_not_found(self, async_client, mock_db):
        """Test GET /api/code-graph/entities/{entity_id} with non-existent entity."""
        entity_id = uuid4()
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_entity_by_id',
                   return_value=None):
            response = await async_client.get(f"/api/code-graph/entities/{entity_id}")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_entity_success(self, async_client, mock_db, sample_entity):
        """Test GET /api/code-graph/entities/{entity_id} with existing entity."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_entity_by_id',
                   return_value=sample_entity.to_dict()):
            response = await async_client.get(f"/api/code-graph/entities/{sample_entity.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "TestService"

    @pytest.mark.asyncio
    async def test_search_entities(self, async_client, mock_db, sample_entity):
        """Test GET /api/code-graph/projects/{project_id}/entities with search."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.search_entities',
                   return_value=[sample_entity.to_dict()]):
            response = await async_client.get(
                "/api/code-graph/projects/1/entities",
                params={"query": "Test", "entity_type": "class", "limit": 50}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "TestService"

    @pytest.mark.asyncio
    async def test_get_entities_by_file(self, async_client, mock_db, sample_entity):
        """Test GET /api/code-graph/projects/{project_id}/files/{file_path}/entities."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_entities_by_file',
                   return_value=[sample_entity.to_dict()]):
            response = await async_client.get(
                "/api/code-graph/projects/1/files/app/services/test_service.py/entities"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1


# =============================================================================
# IMPACT ANALYSIS ENDPOINT TESTS
# =============================================================================

class TestImpactAnalysisEndpoints:
    """Tests for impact analysis endpoints."""

    @pytest.mark.asyncio
    async def test_get_impact_analysis(self, async_client, mock_db, sample_entity_id):
        """Test GET /api/code-graph/impact/{entity_id}."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_impact_analysis',
                   return_value={
                       "entity_id": str(sample_entity_id),
                       "affected_entities": [{"id": str(uuid4()), "name": "AffectedClass"}],
                       "affected_files": ["affected.py"],
                       "impact_score": 0.75,
                       "depth": 3,
                       "from_cache": False
                   }):
            response = await async_client.get(
                f"/api/code-graph/impact/{sample_entity_id}",
                params={"project_id": 1, "max_depth": 5}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["impact_score"] == 0.75

    @pytest.mark.asyncio
    async def test_get_dependencies(self, async_client, mock_db, sample_entity_id):
        """Test GET /api/code-graph/dependencies/{entity_id}."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_direct_dependencies',
                   return_value={
                       "entity_id": str(sample_entity_id),
                       "dependencies": [{"id": str(uuid4()), "name": "DepClass"}],
                       "count": 1
                   }):
            response = await async_client.get(
                f"/api/code-graph/dependencies/{sample_entity_id}",
                params={"project_id": 1}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1

    @pytest.mark.asyncio
    async def test_get_dependents(self, async_client, mock_db, sample_entity_id):
        """Test GET /api/code-graph/dependents/{entity_id}."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_dependents',
                   return_value={
                       "entity_id": str(sample_entity_id),
                       "dependents": [],
                       "count": 0
                   }):
            response = await async_client.get(
                f"/api/code-graph/dependents/{sample_entity_id}",
                params={"project_id": 1}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0


# =============================================================================
# CIRCULAR DEPENDENCY ENDPOINT TESTS
# =============================================================================

class TestCircularDependencyEndpoints:
    """Tests for circular dependency detection."""

    @pytest.mark.asyncio
    async def test_detect_no_cycles(self, async_client, mock_db):
        """Test GET /api/code-graph/projects/{project_id}/circular-dependencies with no cycles."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.detect_circular_dependencies',
                   return_value={
                       "project_id": 1,
                       "cycles_found": 0,
                       "cycles": []
                   }):
            response = await async_client.get("/api/code-graph/projects/1/circular-dependencies")

            assert response.status_code == 200
            data = response.json()
            assert data["cycles_found"] == 0

    @pytest.mark.asyncio
    async def test_detect_cycles_found(self, async_client, mock_db):
        """Test circular dependency detection with cycles present."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.detect_circular_dependencies',
                   return_value={
                       "project_id": 1,
                       "cycles_found": 2,
                       "cycles": [
                           {"entities": ["A", "B", "A"]},
                           {"entities": ["C", "D", "E", "C"]}
                       ]
                   }):
            response = await async_client.get("/api/code-graph/projects/1/circular-dependencies")

            assert response.status_code == 200
            data = response.json()
            assert data["cycles_found"] == 2


# =============================================================================
# MODULE COUPLING ENDPOINT TESTS
# =============================================================================

class TestModuleCouplingEndpoints:
    """Tests for module coupling endpoints."""

    @pytest.mark.asyncio
    async def test_get_module_coupling(self, async_client, mock_db):
        """Test GET /api/code-graph/projects/{project_id}/coupling."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_module_coupling',
                   return_value={
                       "project_id": 1,
                       "total_modules": 5,
                       "total_connections": 10,
                       "total_coupling_strength": 50,
                       "average_coupling": 5.0,
                       "couplings": [
                           {"source_module": "app.services", "target_module": "app.models", "coupling_count": 20}
                       ]
                   }):
            response = await async_client.get(
                "/api/code-graph/projects/1/coupling",
                params={"sort_by": "coupling_count"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_modules"] == 5

    @pytest.mark.asyncio
    async def test_get_highly_coupled_modules(self, async_client, mock_db):
        """Test GET /api/code-graph/projects/{project_id}/coupling/high."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_highly_coupled_modules',
                   return_value=[
                       {"source_module": "app.services", "target_module": "app.models", "coupling_count": 25}
                   ]):
            response = await async_client.get(
                "/api/code-graph/projects/1/coupling/high",
                params={"threshold": 10}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["coupling_count"] == 25


# =============================================================================
# SNAPSHOT ENDPOINT TESTS
# =============================================================================

class TestSnapshotEndpoints:
    """Tests for snapshot endpoints."""

    @pytest.mark.asyncio
    async def test_create_snapshot(self, async_client, mock_db):
        """Test POST /api/code-graph/snapshots."""
        snapshot_id = uuid4()
        with patch('app.services.graph_persistence_service.GraphPersistenceService.create_snapshot',
                   return_value={
                       "id": str(snapshot_id),
                       "project_id": 1,
                       "snapshot_name": "v1.0",
                       "git_commit": "abc123",
                       "entity_count": 50,
                       "relation_count": 100,
                       "file_count": 10,
                       "summary_stats": {},
                       "created_at": datetime.now(timezone.utc).isoformat()
                   }):
            response = await async_client.post(
                "/api/code-graph/snapshots",
                json={
                    "project_id": 1,
                    "snapshot_name": "v1.0",
                    "git_commit": "abc123"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["snapshot_name"] == "v1.0"

    @pytest.mark.asyncio
    async def test_get_snapshots(self, async_client, mock_db):
        """Test GET /api/code-graph/projects/{project_id}/snapshots."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_snapshots',
                   return_value=[{
                       "id": str(uuid4()),
                       "project_id": 1,
                       "snapshot_name": "v1.0",
                       "git_commit": "abc123",
                       "entity_count": 50,
                       "relation_count": 100,
                       "file_count": 10,
                       "summary_stats": {},
                       "created_at": datetime.now(timezone.utc).isoformat()
                   }]):
            response = await async_client.get(
                "/api/code-graph/projects/1/snapshots",
                params={"limit": 10}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_compare_snapshots(self, async_client, mock_db):
        """Test GET /api/code-graph/snapshots/compare."""
        snapshot_id_1 = uuid4()
        snapshot_id_2 = uuid4()
        with patch('app.services.graph_persistence_service.GraphPersistenceService.compare_snapshots',
                   return_value={
                       "snapshot_1": {"id": str(snapshot_id_1), "entity_count": 50},
                       "snapshot_2": {"id": str(snapshot_id_2), "entity_count": 60},
                       "entity_changes": {},
                       "relation_changes": {},
                       "total_entity_change": 10,
                       "total_relation_change": 20,
                       "total_file_change": 2
                   }):
            response = await async_client.get(
                "/api/code-graph/snapshots/compare",
                params={
                    "snapshot_id_1": str(snapshot_id_1),
                    "snapshot_id_2": str(snapshot_id_2)
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_entity_change"] == 10

    @pytest.mark.asyncio
    async def test_compare_snapshots_not_found(self, async_client, mock_db):
        """Test snapshot comparison with non-existent snapshots."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.compare_snapshots',
                   return_value={"error": "Snapshot not found"}):
            response = await async_client.get(
                "/api/code-graph/snapshots/compare",
                params={
                    "snapshot_id_1": str(uuid4()),
                    "snapshot_id_2": str(uuid4())
                }
            )

            assert response.status_code == 404


# =============================================================================
# STATISTICS & EXPORT ENDPOINT TESTS
# =============================================================================

class TestStatisticsEndpoints:
    """Tests for statistics and export endpoints."""

    @pytest.mark.asyncio
    async def test_get_project_statistics(self, async_client, mock_db):
        """Test GET /api/code-graph/projects/{project_id}/statistics."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.get_project_statistics',
                   return_value={
                       "project_id": 1,
                       "total_entities": 100,
                       "total_relations": 200,
                       "total_files": 20,
                       "entity_counts": {"class": 30, "function": 50, "module": 20},
                       "relation_counts": {"imports": 100, "calls": 80, "extends": 20},
                       "top_referenced_entities": []
                   }):
            response = await async_client.get("/api/code-graph/projects/1/statistics")

            assert response.status_code == 200
            data = response.json()
            assert data["total_entities"] == 100

    @pytest.mark.asyncio
    async def test_export_d3_format(self, async_client, mock_db):
        """Test GET /api/code-graph/projects/{project_id}/export with D3 format."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.export_graph_for_visualization',
                   return_value={
                       "nodes": [{"id": "1", "name": "TestClass", "type": "class"}],
                       "links": [{"source": "1", "target": "2", "type": "imports"}]
                   }):
            response = await async_client.get(
                "/api/code-graph/projects/1/export",
                params={"format": "d3"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "links" in data

    @pytest.mark.asyncio
    async def test_export_dot_format(self, async_client, mock_db):
        """Test GET /api/code-graph/projects/{project_id}/export with DOT format."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.export_graph_for_visualization',
                   return_value={
                       "dot": "digraph G { A -> B; }"
                   }):
            response = await async_client.get(
                "/api/code-graph/projects/1/export",
                params={"format": "dot"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "dot" in data


# =============================================================================
# CACHE MANAGEMENT ENDPOINT TESTS
# =============================================================================

class TestCacheEndpoints:
    """Tests for cache management endpoints."""

    @pytest.mark.asyncio
    async def test_invalidate_project_cache(self, async_client, mock_db):
        """Test DELETE /api/code-graph/projects/{project_id}/cache."""
        with patch('app.services.graph_persistence_service.GraphPersistenceService.invalidate_cache',
                   return_value=5):
            response = await async_client.delete("/api/code-graph/projects/1/cache")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["cache_entries_invalidated"] == 5

    @pytest.mark.asyncio
    async def test_invalidate_entity_cache(self, async_client, mock_db):
        """Test DELETE /api/code-graph/cache/{entity_id}."""
        entity_id = uuid4()
        with patch('app.services.graph_persistence_service.GraphPersistenceService.invalidate_cache',
                   return_value=1):
            response = await async_client.delete(
                f"/api/code-graph/cache/{entity_id}",
                params={"project_id": 1}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["cache_entries_invalidated"] == 1
