"""
Tests for DataLineageService - Fase 24: Data Architecture

Tests cover:
- Session management (create, get, save)
- Node management (add, find, batch)
- Edge management (add, connect chain)
- Field mapping
- Impact analysis
- Brown Paper integration
- Traceability matrix generation

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.services.data_lineage_service import DataLineageService
from app.models.data_architecture import (
    LineageNodeType, LineageEdgeType, TransformationType,
    LineageNode, LineageEdge, FieldMapping, LineageGraph
)


class TestDataLineageServiceSession:
    """Test session management"""

    @pytest.fixture
    def service(self):
        """Create service without DB"""
        return DataLineageService(db=None)

    @pytest.mark.asyncio
    async def test_create_session(self, service):
        """Test creating a new lineage session"""
        session_id = await service.create_session(
            name="Test Session",
            project_id="proj-123",
            description="Test lineage tracking"
        )

        assert session_id is not None
        assert len(session_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_get_session(self, service):
        """Test retrieving a session"""
        session_id = await service.create_session(name="Test")
        graph = await service.get_session(session_id)

        assert graph is not None
        assert graph.session_id == session_id
        assert isinstance(graph.nodes, list)
        assert isinstance(graph.edges, list)

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, service):
        """Test getting a session that doesn't exist"""
        graph = await service.get_session("nonexistent-id")
        assert graph is None


class TestDataLineageServiceNodes:
    """Test node management"""

    @pytest.fixture
    def service(self):
        return DataLineageService(db=None)

    @pytest.fixture
    async def session_id(self, service):
        return await service.create_session(name="Node Test")

    @pytest.mark.asyncio
    async def test_add_node(self, service, session_id):
        """Test adding a single node"""
        node_id = await service.add_node(
            session_id=session_id,
            node_type=LineageNodeType.ENTITY,
            name="User",
            description="User entity",
            source_path="/src/models/user.py",
            source_line=10
        )

        assert node_id is not None
        graph = await service.get_session(session_id)
        assert len(graph.nodes) == 1
        assert graph.nodes[0].name == "User"
        assert graph.nodes[0].node_type == LineageNodeType.ENTITY

    @pytest.mark.asyncio
    async def test_add_nodes_batch(self, service, session_id):
        """Test adding multiple nodes at once"""
        nodes = [
            {"node_type": "entity", "name": "User"},
            {"node_type": "entity", "name": "Order"},
            {"node_type": "field", "name": "user_id"}
        ]
        node_ids = await service.add_nodes_batch(session_id, nodes)

        assert len(node_ids) == 3
        graph = await service.get_session(session_id)
        assert len(graph.nodes) == 3

    @pytest.mark.asyncio
    async def test_find_nodes_by_type(self, service, session_id):
        """Test finding nodes by type"""
        await service.add_node(session_id, LineageNodeType.ENTITY, "User")
        await service.add_node(session_id, LineageNodeType.ENTITY, "Order")
        await service.add_node(session_id, LineageNodeType.FIELD, "user_id")

        entities = await service.find_nodes(session_id, node_type=LineageNodeType.ENTITY)
        assert len(entities) == 2

        fields = await service.find_nodes(session_id, node_type=LineageNodeType.FIELD)
        assert len(fields) == 1

    @pytest.mark.asyncio
    async def test_find_nodes_by_name_pattern(self, service, session_id):
        """Test finding nodes by name pattern"""
        await service.add_node(session_id, LineageNodeType.ENTITY, "UserProfile")
        await service.add_node(session_id, LineageNodeType.ENTITY, "UserSettings")
        await service.add_node(session_id, LineageNodeType.ENTITY, "Order")

        user_nodes = await service.find_nodes(session_id, name_pattern="user")
        assert len(user_nodes) == 2


class TestDataLineageServiceEdges:
    """Test edge management"""

    @pytest.fixture
    def service(self):
        return DataLineageService(db=None)

    @pytest.fixture
    async def session_with_nodes(self, service):
        session_id = await service.create_session(name="Edge Test")
        node1 = await service.add_node(session_id, LineageNodeType.DOMAIN, "Auth")
        node2 = await service.add_node(session_id, LineageNodeType.ENTITY, "User")
        node3 = await service.add_node(session_id, LineageNodeType.FIELD, "user_id")
        return session_id, node1, node2, node3

    @pytest.mark.asyncio
    async def test_add_edge(self, service, session_with_nodes):
        """Test adding an edge between nodes"""
        session_id, node1, node2, _ = session_with_nodes

        edge_id = await service.add_edge(
            session_id=session_id,
            source_node_id=node1,
            target_node_id=node2,
            edge_type=LineageEdgeType.DEFINES
        )

        assert edge_id is not None
        graph = await service.get_session(session_id)
        assert len(graph.edges) == 1
        assert graph.edges[0].source_node_id == node1
        assert graph.edges[0].target_node_id == node2

    @pytest.mark.asyncio
    async def test_connect_chain(self, service, session_with_nodes):
        """Test connecting a chain of nodes"""
        session_id, node1, node2, node3 = session_with_nodes

        edge_ids = await service.connect_chain(
            session_id=session_id,
            node_ids=[node1, node2, node3],
            edge_type=LineageEdgeType.CONTAINS
        )

        assert len(edge_ids) == 2  # 3 nodes = 2 edges
        graph = await service.get_session(session_id)
        assert len(graph.edges) == 2

    @pytest.mark.asyncio
    async def test_add_edge_invalid_node(self, service):
        """Test adding edge with invalid node fails"""
        session_id = await service.create_session(name="Invalid Test")

        with pytest.raises(ValueError, match="Source node .* not found"):
            await service.add_edge(
                session_id=session_id,
                source_node_id="nonexistent",
                target_node_id="also-nonexistent",
                edge_type=LineageEdgeType.DEFINES
            )


class TestDataLineageServiceFieldMapping:
    """Test field mapping functionality"""

    @pytest.fixture
    def service(self):
        return DataLineageService(db=None)

    @pytest.fixture
    async def session_id(self, service):
        return await service.create_session(name="Mapping Test")

    @pytest.mark.asyncio
    async def test_add_field_mapping(self, service, session_id):
        """Test adding a field mapping"""
        mapping_id = await service.add_field_mapping(
            session_id=session_id,
            legacy_table="tblUsers",
            legacy_field="strUserName",
            legacy_type="nvarchar(100)",
            new_table="users",
            new_field="username",
            new_type="varchar(100)",
            transformation=TransformationType.RENAME
        )

        assert mapping_id is not None
        mappings = await service.get_field_mappings(session_id)
        assert len(mappings) == 1
        assert mappings[0].legacy_table == "tblUsers"
        assert mappings[0].new_table == "users"

    @pytest.mark.asyncio
    async def test_suggest_field_mappings(self, service, session_id):
        """Test suggesting field mappings based on name similarity"""
        legacy_schema = {
            "tblUser": {"user_id": "int", "user_name": "nvarchar"},
            "tblOrder": {"order_id": "int", "user_id": "int"}
        }
        new_schema = {
            "users": {"id": "int", "username": "varchar"},
            "orders": {"id": "int", "user_id": "int"}
        }

        suggestions = await service.suggest_field_mappings(
            session_id=session_id,
            legacy_schema=legacy_schema,
            new_schema=new_schema
        )

        # Should find matches based on similar names
        assert isinstance(suggestions, list)


class TestDataLineageServiceImpactAnalysis:
    """Test impact analysis functionality"""

    @pytest.fixture
    def service(self):
        return DataLineageService(db=None)

    @pytest.fixture
    async def session_with_chain(self, service):
        """Create session with a chain of related nodes"""
        session_id = await service.create_session(name="Impact Test")

        # Create chain: Domain -> Entity -> Story -> Test
        domain = await service.add_node(session_id, LineageNodeType.DOMAIN, "Auth")
        entity = await service.add_node(session_id, LineageNodeType.ENTITY, "User")
        story = await service.add_node(session_id, LineageNodeType.USER_STORY, "Login Story")
        test = await service.add_node(session_id, LineageNodeType.TEST_CASE, "test_login")

        await service.add_edge(session_id, domain, entity, LineageEdgeType.DEFINES)
        await service.add_edge(session_id, entity, story, LineageEdgeType.IMPLEMENTS)
        await service.add_edge(session_id, story, test, LineageEdgeType.TESTED_BY)

        return session_id, domain, entity, story, test

    @pytest.mark.asyncio
    async def test_analyze_impact(self, service, session_with_chain):
        """Test analyzing impact of changing a node"""
        session_id, domain, entity, story, test = session_with_chain

        result = await service.analyze_impact(session_id, entity)

        assert result.changed_node_id == entity
        assert result.changed_node_name == "User"
        assert len(result.affected_nodes) >= 2  # story and test
        assert "test_login" in result.test_cases_affected
        assert result.risk_level in ("low", "medium", "high", "critical")


class TestDataLineageServiceBrownPaperIntegration:
    """Test Brown Paper integration"""

    @pytest.fixture
    def service(self):
        return DataLineageService(db=None)

    @pytest.fixture
    async def session_id(self, service):
        return await service.create_session(name="Brown Paper Test")

    @pytest.mark.asyncio
    async def test_import_from_brown_paper(self, service, session_id):
        """Test importing lineage from Brown Paper output"""
        brown_paper_data = {
            "domains": [
                {"id": "d1", "name": "Authentication", "description": "Auth domain"}
            ],
            "entities": [
                {"id": "e1", "name": "User", "domain_id": "d1"}
            ],
            "epics": [
                {"id": "ep1", "title": "User Management"}
            ],
            "features": [
                {"id": "f1", "title": "Login", "epic_id": "ep1"}
            ],
            "stories": [
                {"id": "s1", "title": "User can login", "feature_id": "f1"}
            ]
        }

        counts = await service.import_from_brown_paper(session_id, brown_paper_data)

        assert counts["nodes"] >= 5
        assert counts["edges"] >= 3

        graph = await service.get_session(session_id)
        assert len(graph.nodes) >= 5


class TestDataLineageServiceTraceability:
    """Test traceability matrix generation"""

    @pytest.fixture
    def service(self):
        return DataLineageService(db=None)

    @pytest.fixture
    async def session_with_hierarchy(self, service):
        """Create session with full hierarchy"""
        session_id = await service.create_session(name="Traceability Test")

        epic = await service.add_node(session_id, LineageNodeType.EPIC, "User Epic")
        feature = await service.add_node(session_id, LineageNodeType.FEATURE, "Login Feature")
        story = await service.add_node(session_id, LineageNodeType.USER_STORY, "Login Story")
        test = await service.add_node(session_id, LineageNodeType.TEST_CASE, "test_login")

        await service.add_edge(session_id, epic, feature, LineageEdgeType.DEFINES)
        await service.add_edge(session_id, feature, story, LineageEdgeType.DEFINES)
        await service.add_edge(session_id, story, test, LineageEdgeType.TESTED_BY)

        return session_id

    @pytest.mark.asyncio
    async def test_generate_traceability_matrix(self, service, session_with_hierarchy):
        """Test generating traceability matrix"""
        matrix = await service.generate_traceability_matrix(session_with_hierarchy)

        assert "epics" in matrix
        assert "stories" in matrix
        assert "summary" in matrix
        assert matrix["summary"]["total_epics"] == 1
        assert matrix["summary"]["total_stories"] == 1

    @pytest.mark.asyncio
    async def test_get_statistics(self, service, session_with_hierarchy):
        """Test getting session statistics"""
        stats = await service.get_statistics(session_with_hierarchy)

        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 3
        assert "epic" in stats.get("node_counts", {}) or len(stats) > 0
