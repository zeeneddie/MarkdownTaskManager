"""
Week 75: Graph Persistence Service Tests

Comprehensive tests for the GraphPersistenceService.
Tests cover entity management, impact analysis, coupling metrics,
snapshots, and graph export functionality.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.graph_persistence_service import GraphPersistenceService
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
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create a GraphPersistenceService instance with mock db."""
    return GraphPersistenceService(mock_db)


@pytest.fixture
def sample_entity():
    """Create a sample code entity."""
    entity = CodeGraphEntity(
        id=uuid4(),
        project_id=1,
        entity_type="class",
        name="UserService",
        qualified_name="app.services.UserService",
        file_path="app/services/user_service.py",
        start_line=10,
        end_line=100,
        docstring="Service for user operations",
        signature="class UserService:",
        entity_data={"decorators": ["@injectable"]},
        metrics={"lines": 90, "complexity": 5},
        hash="abc123"
    )
    entity.created_at = datetime.now(timezone.utc)
    entity.last_synced = datetime.now(timezone.utc)
    return entity


@pytest.fixture
def sample_relation(sample_entity):
    """Create a sample code relation."""
    target_id = uuid4()
    relation = CodeGraphRelation(
        id=uuid4(),
        project_id=1,
        source_entity_id=sample_entity.id,
        target_entity_id=target_id,
        relation_type="imports",
        relation_data={"alias": None},
        weight=1.0
    )
    relation.created_at = datetime.now(timezone.utc)
    return relation


# =============================================================================
# ENTITY MANAGEMENT TESTS
# =============================================================================

class TestEntityManagement:
    """Tests for entity CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_entity_by_id_found(self, service, mock_db, sample_entity):
        """Test retrieving an entity by ID when it exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_entity
        mock_db.execute.return_value = mock_result

        result = await service.get_entity_by_id(sample_entity.id)

        assert result is not None
        assert result["name"] == "UserService"
        assert result["entity_type"] == "class"

    @pytest.mark.asyncio
    async def test_get_entity_by_id_not_found(self, service, mock_db):
        """Test retrieving an entity that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_entity_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_search_entities(self, service, mock_db, sample_entity):
        """Test searching entities by query."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_entity]
        mock_db.execute.return_value = mock_result

        result = await service.search_entities(
            project_id=1,
            query="User",
            entity_type="class",
            limit=10
        )

        assert len(result) == 1
        assert result[0]["name"] == "UserService"

    @pytest.mark.asyncio
    async def test_search_entities_empty(self, service, mock_db):
        """Test searching entities with no results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.search_entities(
            project_id=1,
            query="NonExistent"
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_entities_by_file(self, service, mock_db, sample_entity):
        """Test getting all entities in a file."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_entity]
        mock_db.execute.return_value = mock_result

        result = await service.get_entities_by_file(
            project_id=1,
            file_path="app/services/user_service.py"
        )

        assert len(result) == 1
        assert result[0]["file_path"] == "app/services/user_service.py"

    @pytest.mark.asyncio
    async def test_search_entities_with_limit(self, service, mock_db, sample_entity):
        """Test that search respects limit parameter."""
        entities = [sample_entity for _ in range(5)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = entities[:3]
        mock_db.execute.return_value = mock_result

        result = await service.search_entities(
            project_id=1,
            query="User",
            limit=3
        )

        assert len(result) == 3


# =============================================================================
# GRAPH SYNC TESTS
# =============================================================================

class TestGraphSync:
    """Tests for graph synchronization."""

    @pytest.mark.asyncio
    async def test_sync_project_graph_invalid_path(self, service):
        """Test sync with invalid repository path."""
        result = await service.sync_project_graph(
            project_id=1,
            repo_path="/nonexistent/path"
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_sync_project_graph_with_error_result(self, service, mock_db):
        """Test sync returns error from KnowledgeGraphService."""
        with patch('app.services.graph_persistence_service.KnowledgeGraphService') as MockKG:
            mock_kg = MagicMock()
            mock_kg.build_graph.return_value = {
                "error": "Repository path does not exist"
            }
            MockKG.return_value = mock_kg

            result = await service.sync_project_graph(
                project_id=1,
                repo_path="/invalid/path"
            )

            assert "error" in result


# =============================================================================
# IMPACT ANALYSIS TESTS
# =============================================================================

class TestImpactAnalysis:
    """Tests for impact analysis functionality."""

    @pytest.mark.asyncio
    async def test_get_impact_analysis_from_cache(self, service, mock_db, sample_entity):
        """Test getting impact analysis from cache."""
        cache_entry = CodeGraphImpactCache(
            id=uuid4(),
            project_id=1,
            entity_id=sample_entity.id,
            impact_type="transitive",
            affected_entities=[{"id": str(uuid4()), "name": "AffectedClass"}],
            affected_files=["affected.py"],
            impact_score=0.75,
            depth=3,
            cache_valid_until=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = cache_entry
        mock_db.execute.return_value = mock_result

        result = await service.get_impact_analysis(
            project_id=1,
            entity_id=sample_entity.id
        )

        assert result["from_cache"] is True
        assert len(result["affected_entities"]) == 1

    @pytest.mark.asyncio
    async def test_get_direct_dependencies(self, service, mock_db, sample_entity):
        """Test getting direct dependencies of an entity."""
        target_entity = CodeGraphEntity(
            id=uuid4(),
            project_id=1,
            entity_type="class",
            name="DependencyClass",
            qualified_name="deps.DependencyClass",
            file_path="deps.py",
            start_line=1,
            end_line=50
        )
        target_entity.created_at = datetime.now(timezone.utc)
        target_entity.last_synced = datetime.now(timezone.utc)

        relation = CodeGraphRelation(
            id=uuid4(),
            project_id=1,
            source_entity_id=sample_entity.id,
            target_entity_id=target_entity.id,
            relation_type="imports"
        )
        relation.target_entity = target_entity
        relation.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [relation]
        mock_db.execute.return_value = mock_result

        result = await service.get_direct_dependencies(
            project_id=1,
            entity_id=sample_entity.id
        )

        assert "dependencies" in result
        assert result["count"] >= 0

    @pytest.mark.asyncio
    async def test_get_dependents(self, service, mock_db, sample_entity):
        """Test getting entities that depend on this entity."""
        source_entity = CodeGraphEntity(
            id=uuid4(),
            project_id=1,
            entity_type="class",
            name="DependentClass",
            qualified_name="app.DependentClass",
            file_path="app.py",
            start_line=1,
            end_line=50
        )
        source_entity.created_at = datetime.now(timezone.utc)
        source_entity.last_synced = datetime.now(timezone.utc)

        relation = CodeGraphRelation(
            id=uuid4(),
            project_id=1,
            source_entity_id=source_entity.id,
            target_entity_id=sample_entity.id,
            relation_type="imports"
        )
        relation.source_entity = source_entity
        relation.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [relation]
        mock_db.execute.return_value = mock_result

        result = await service.get_dependents(
            project_id=1,
            entity_id=sample_entity.id
        )

        assert "dependents" in result
        assert result["count"] >= 0


# =============================================================================
# CIRCULAR DEPENDENCY TESTS
# =============================================================================

class TestCircularDependencies:
    """Tests for circular dependency detection."""

    @pytest.mark.asyncio
    async def test_detect_no_circular_dependencies(self, service, mock_db):
        """Test detection when no circular dependencies exist."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.detect_circular_dependencies(project_id=1)

        assert result["cycles_found"] == 0
        assert result["cycles"] == []

    @pytest.mark.asyncio
    async def test_detect_circular_dependencies_found(self, service, mock_db):
        """Test detection when circular dependencies exist."""
        entity_a_id = uuid4()
        entity_b_id = uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (str(entity_a_id), str(entity_b_id), "imports"),
            (str(entity_b_id), str(entity_a_id), "imports")
        ]
        mock_db.execute.return_value = mock_result

        result = await service.detect_circular_dependencies(project_id=1)

        assert result["project_id"] == 1
        assert "cycles_found" in result


# =============================================================================
# MODULE COUPLING TESTS
# =============================================================================

class TestModuleCoupling:
    """Tests for module coupling analysis."""

    @pytest.mark.asyncio
    async def test_get_module_coupling_empty(self, service, mock_db):
        """Test coupling metrics with no data."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_module_coupling(project_id=1)

        assert result["total_modules"] == 0
        assert result["couplings"] == []

    @pytest.mark.asyncio
    async def test_get_module_coupling_with_data(self, service, mock_db):
        """Test coupling metrics with coupling data."""
        coupling = CodeGraphModuleCoupling(
            id=uuid4(),
            project_id=1,
            source_module="app.services",
            target_module="app.models",
            coupling_count=15,
            coupling_type="import"
        )
        coupling.created_at = datetime.now(timezone.utc)
        coupling.updated_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [coupling]
        mock_db.execute.return_value = mock_result

        result = await service.get_module_coupling(
            project_id=1,
            sort_by="coupling_count"
        )

        assert len(result["couplings"]) == 1
        assert result["total_coupling_strength"] == 15

    @pytest.mark.asyncio
    async def test_get_highly_coupled_modules(self, service, mock_db):
        """Test getting modules above coupling threshold."""
        coupling = CodeGraphModuleCoupling(
            id=uuid4(),
            project_id=1,
            source_module="app.services",
            target_module="app.models",
            coupling_count=25,
            coupling_type="import"
        )
        coupling.created_at = datetime.now(timezone.utc)
        coupling.updated_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [coupling]
        mock_db.execute.return_value = mock_result

        result = await service.get_highly_coupled_modules(
            project_id=1,
            threshold=10
        )

        assert len(result) == 1
        assert result[0]["coupling_count"] == 25


# =============================================================================
# SNAPSHOT TESTS
# =============================================================================

class TestSnapshots:
    """Tests for graph snapshot functionality."""

    @pytest.mark.asyncio
    async def test_get_snapshots(self, service, mock_db):
        """Test retrieving snapshots for a project."""
        snapshot = CodeGraphSnapshot(
            id=uuid4(),
            project_id=1,
            snapshot_name="v1.0",
            git_commit="abc123",
            entity_count=50,
            relation_count=100,
            file_count=10,
            summary_stats={"classes": 20, "functions": 30}
        )
        snapshot.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snapshot]
        mock_db.execute.return_value = mock_result

        result = await service.get_snapshots(project_id=1, limit=10)

        assert len(result) == 1
        assert result[0]["snapshot_name"] == "v1.0"

    @pytest.mark.asyncio
    async def test_compare_snapshots(self, service, mock_db):
        """Test comparing two snapshots."""
        snapshot1 = CodeGraphSnapshot(
            id=uuid4(),
            project_id=1,
            snapshot_name="v1.0",
            entity_count=50,
            relation_count=100,
            file_count=10,
            summary_stats={"classes": 20}
        )
        snapshot1.created_at = datetime.now(timezone.utc)

        snapshot2 = CodeGraphSnapshot(
            id=uuid4(),
            project_id=1,
            snapshot_name="v2.0",
            entity_count=60,
            relation_count=120,
            file_count=12,
            summary_stats={"classes": 25}
        )
        snapshot2.created_at = datetime.now(timezone.utc)

        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = snapshot1
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = snapshot2

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        result = await service.compare_snapshots(
            snapshot_id_1=snapshot1.id,
            snapshot_id_2=snapshot2.id
        )

        assert result["total_entity_change"] == 10
        assert result["total_relation_change"] == 20
        assert result["total_file_change"] == 2

    @pytest.mark.asyncio
    async def test_compare_snapshots_not_found(self, service, mock_db):
        """Test comparing snapshots when one doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.compare_snapshots(
            snapshot_id_1=uuid4(),
            snapshot_id_2=uuid4()
        )

        assert "error" in result


# =============================================================================
# GRAPH EXPORT TESTS
# =============================================================================

class TestGraphExport:
    """Tests for graph export functionality."""

    @pytest.mark.asyncio
    async def test_export_d3_format(self, service, mock_db, sample_entity):
        """Test exporting graph in D3.js format."""
        target_entity = CodeGraphEntity(
            id=uuid4(),
            project_id=1,
            entity_type="class",
            name="TargetClass",
            qualified_name="target.TargetClass",
            file_path="target.py",
            start_line=1,
            end_line=50
        )
        target_entity.created_at = datetime.now(timezone.utc)
        target_entity.last_synced = datetime.now(timezone.utc)

        relation = CodeGraphRelation(
            id=uuid4(),
            project_id=1,
            source_entity_id=sample_entity.id,
            target_entity_id=target_entity.id,
            relation_type="imports"
        )
        relation.created_at = datetime.now(timezone.utc)

        mock_entities = MagicMock()
        mock_entities.scalars.return_value.all.return_value = [sample_entity, target_entity]

        mock_relations = MagicMock()
        mock_relations.scalars.return_value.all.return_value = [relation]

        mock_db.execute.side_effect = [mock_entities, mock_relations]

        result = await service.export_graph_for_visualization(
            project_id=1,
            format="d3"
        )

        assert "nodes" in result
        assert "links" in result
        assert len(result["nodes"]) == 2

    @pytest.mark.asyncio
    async def test_export_dot_format(self, service, mock_db, sample_entity):
        """Test exporting graph in DOT format."""
        target_entity = CodeGraphEntity(
            id=uuid4(),
            project_id=1,
            entity_type="function",
            name="target_func",
            qualified_name="target.target_func",
            file_path="target.py",
            start_line=1,
            end_line=10
        )
        target_entity.created_at = datetime.now(timezone.utc)
        target_entity.last_synced = datetime.now(timezone.utc)

        relation = CodeGraphRelation(
            id=uuid4(),
            project_id=1,
            source_entity_id=sample_entity.id,
            target_entity_id=target_entity.id,
            relation_type="calls"
        )
        relation.created_at = datetime.now(timezone.utc)

        mock_entities = MagicMock()
        mock_entities.scalars.return_value.all.return_value = [sample_entity, target_entity]

        mock_relations = MagicMock()
        mock_relations.scalars.return_value.all.return_value = [relation]

        mock_db.execute.side_effect = [mock_entities, mock_relations]

        result = await service.export_graph_for_visualization(
            project_id=1,
            format="dot"
        )

        assert "dot" in result
        assert "digraph" in result["dot"]
        assert "UserService" in result["dot"]


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_self_referencing_entity(self, service, mock_db, sample_entity):
        """Test handling of self-referencing entities."""
        self_relation = CodeGraphRelation(
            id=uuid4(),
            project_id=1,
            source_entity_id=sample_entity.id,
            target_entity_id=sample_entity.id,
            relation_type="calls"
        )
        self_relation.source_entity = sample_entity
        self_relation.target_entity = sample_entity
        self_relation.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [self_relation]
        mock_db.execute.return_value = mock_result

        result = await service.get_direct_dependencies(
            project_id=1,
            entity_id=sample_entity.id
        )

        assert "dependencies" in result

    @pytest.mark.asyncio
    async def test_entity_with_none_dates(self, service, mock_db):
        """Test entity handling when dates are None."""
        entity = CodeGraphEntity(
            id=uuid4(),
            project_id=1,
            entity_type="module",
            name="test_module",
            qualified_name="test.module",
            file_path="test/module.py",
            start_line=None,
            end_line=None,
            entity_data={},
            metrics={}
        )
        entity.created_at = None
        entity.last_synced = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entity
        mock_db.execute.return_value = mock_result

        result = await service.get_entity_by_id(entity.id)

        assert result is not None
        assert result["name"] == "test_module"

    @pytest.mark.asyncio
    async def test_empty_coupling_data(self, service, mock_db):
        """Test module coupling with no coupling data."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_module_coupling(project_id=999)

        assert result["total_modules"] == 0
        assert result["total_connections"] == 0
        assert result["average_coupling"] == 0.0

    @pytest.mark.asyncio
    async def test_snapshot_with_empty_stats(self, service, mock_db):
        """Test snapshot with empty summary_stats."""
        snapshot = CodeGraphSnapshot(
            id=uuid4(),
            project_id=1,
            snapshot_name="empty",
            entity_count=0,
            relation_count=0,
            file_count=0,
            summary_stats=None
        )
        snapshot.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snapshot]
        mock_db.execute.return_value = mock_result

        result = await service.get_snapshots(project_id=1)

        assert len(result) == 1
        assert result[0]["summary_stats"] == {} or result[0]["summary_stats"] is None
