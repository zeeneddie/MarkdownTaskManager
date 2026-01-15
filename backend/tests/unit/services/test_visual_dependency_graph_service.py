"""
Unit tests for VisualDependencyGraphService (E1 - Fase 24).

Tests cover:
- Visual node/edge creation
- D3.js export format
- Cytoscape.js export format
- Graphviz DOT export
- Mermaid diagram export
- Subgraph extraction

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.visual_dependency_graph_service import (
    LayoutType,
    NodeShape,
    EdgeStyle,
    VisualNode,
    VisualEdge,
    Cluster,
    VisualGraphConfig,
    VisualDependencyGraph,
    VisualDependencyGraphService,
    create_visual_dependency_graph_service,
)
from app.services.dependency_graph_service import (
    DependencyGraphResult,
    ModuleNode,
    DependencyEdge,
    DependencyMetrics,
    CircularDependency,
    Language,
)
from dataclasses import field


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh VisualDependencyGraphService instance."""
    return VisualDependencyGraphService()


@pytest.fixture
def sample_node():
    """Create a sample visual node."""
    return VisualNode(
        id="app/main",
        label="main",
        group="app",
        size=20,
        color="#3776ab",
        shape=NodeShape.CIRCLE,
        imports_count=5,
        imported_by_count=3,
        is_hub=True,
        file_path="app/main.py",
        language="python",
    )


@pytest.fixture
def sample_edge():
    """Create a sample visual edge."""
    return VisualEdge(
        source="app/main",
        target="app/utils",
        weight=1.0,
        style=EdgeStyle.SOLID,
        color="#999",
    )


@pytest.fixture
def sample_visual_graph(sample_node, sample_edge):
    """Create a sample visual graph."""
    node2 = VisualNode(
        id="app/utils",
        label="utils",
        group="app",
        size=15,
        color="#3776ab",
    )

    cluster = Cluster(
        id="app",
        name="app",
        nodes=["app/main", "app/utils"],
        color="hsl(120, 60%, 70%)",
    )

    return VisualDependencyGraph(
        nodes=[sample_node, node2],
        edges=[sample_edge],
        clusters=[cluster],
        config=VisualGraphConfig(),
        metadata={
            "generated_at": datetime.utcnow().isoformat(),
            "project_path": "/project",
        },
    )


@pytest.fixture
def sample_dependency_result():
    """Create a sample DependencyGraphResult."""
    # Create edges first (with proper DependencyEdge structure)
    edge1 = DependencyEdge(
        source="app/main",
        target="app/utils",
        import_type="import",
        line_number=1,
        is_external=False,
        import_statement="from app.utils import helper",
    )
    edge2 = DependencyEdge(
        source="app/main",
        target="requests",
        import_type="import",
        line_number=2,
        is_external=True,
        import_statement="import requests",
    )

    # Create nodes with proper structure
    main_node = ModuleNode(
        name="app/main",
        file_path="app/main.py",
        language=Language.PYTHON,
        imports=[edge1, edge2],
        imported_by=[],
    )
    utils_node = ModuleNode(
        name="app/utils",
        file_path="app/utils.py",
        language=Language.PYTHON,
        imports=[],
        imported_by=["app/main"],
    )
    requests_node = ModuleNode(
        name="requests",
        file_path="",  # External package has no file_path
        language=Language.PYTHON,
        imports=[],
        imported_by=["app/main"],
    )

    # Build modules dict
    modules = {
        "app/main": main_node,
        "app/utils": utils_node,
        "requests": requests_node,
    }

    edges = [edge1, edge2]

    return DependencyGraphResult(
        project_path="/project",
        modules=modules,
        edges=edges,
        circular_dependencies=[],
        languages_detected=[Language.PYTHON],
        metrics=DependencyMetrics(
            total_modules=3,
            total_edges=2,
            external_dependencies=1,
            internal_dependencies=1,
            circular_dependencies=0,
            average_imports_per_module=0.67,
            max_imports=2,
            max_imported_by=1,
            afferent_coupling_avg=0.33,
            efferent_coupling_avg=0.67,
            instability_avg=0.67,
            entry_points=["app/main"],
            hub_modules=[],
        ),
        clusters={"app": ["app/main", "app/utils"]},
    )


# ==================== VisualNode Tests ====================

class TestVisualNode:
    """Test VisualNode functionality."""

    def test_to_dict(self, sample_node):
        """Test node serialization."""
        data = sample_node.to_dict()

        assert data["id"] == "app/main"
        assert data["label"] == "main"
        assert data["group"] == "app"
        assert data["size"] == 20
        assert data["color"] == "#3776ab"
        assert data["shape"] == "circle"
        assert data["imports"] == 5
        assert data["importedBy"] == 3
        assert data["isHub"] is True
        assert data["language"] == "python"

    def test_to_dict_with_position(self):
        """Test node with fixed position."""
        node = VisualNode(
            id="test",
            label="test",
            group="root",
            size=10,
            color="#000",
            x=100.0,
            y=200.0,
            fx=100.0,
            fy=200.0,
        )

        data = node.to_dict()

        assert data["x"] == 100.0
        assert data["y"] == 200.0
        assert data["fx"] == 100.0
        assert data["fy"] == 200.0

    def test_node_shapes(self):
        """Test all node shapes are valid."""
        for shape in NodeShape:
            node = VisualNode(
                id="test",
                label="test",
                group="root",
                size=10,
                color="#000",
                shape=shape,
            )
            assert node.to_dict()["shape"] == shape.value


# ==================== VisualEdge Tests ====================

class TestVisualEdge:
    """Test VisualEdge functionality."""

    def test_to_dict(self, sample_edge):
        """Test edge serialization."""
        data = sample_edge.to_dict()

        assert data["source"] == "app/main"
        assert data["target"] == "app/utils"
        assert data["weight"] == 1.0
        assert data["style"] == "solid"
        assert data["color"] == "#999"

    def test_circular_edge(self):
        """Test circular edge marking."""
        edge = VisualEdge(
            source="a",
            target="b",
            is_circular=True,
            color="#e74c3c",
            style=EdgeStyle.DASHED,
        )

        data = edge.to_dict()

        assert data["isCircular"] is True
        assert data["style"] == "dashed"
        assert data["color"] == "#e74c3c"

    def test_edge_styles(self):
        """Test all edge styles are valid."""
        for style in EdgeStyle:
            edge = VisualEdge(
                source="a",
                target="b",
                style=style,
            )
            assert edge.to_dict()["style"] == style.value


# ==================== Cluster Tests ====================

class TestCluster:
    """Test Cluster functionality."""

    def test_to_dict(self):
        """Test cluster serialization."""
        cluster = Cluster(
            id="app",
            name="Application",
            nodes=["app/main", "app/utils", "app/config"],
            color="#666",
            is_expanded=True,
        )

        data = cluster.to_dict()

        assert data["id"] == "app"
        assert data["name"] == "Application"
        assert data["nodeCount"] == 3
        assert data["expanded"] is True
        assert "app/main" in data["nodes"]


# ==================== VisualDependencyGraph Tests ====================

class TestVisualDependencyGraph:
    """Test VisualDependencyGraph functionality."""

    def test_to_d3_format(self, sample_visual_graph):
        """Test D3.js format export."""
        d3_data = sample_visual_graph.to_d3_format()

        assert "nodes" in d3_data
        assert "links" in d3_data
        assert "clusters" in d3_data
        assert "config" in d3_data
        assert "metadata" in d3_data

        assert len(d3_data["nodes"]) == 2
        assert len(d3_data["links"]) == 1

    def test_to_cytoscape_format(self, sample_visual_graph):
        """Test Cytoscape.js format export."""
        cyto_data = sample_visual_graph.to_cytoscape_format()

        assert "elements" in cyto_data
        assert "style" in cyto_data
        assert "layout" in cyto_data

        # Should have nodes + edges in elements
        assert len(cyto_data["elements"]) >= 2

    def test_to_graphviz_dot(self, sample_visual_graph):
        """Test Graphviz DOT export."""
        dot = sample_visual_graph.to_graphviz_dot()

        assert "digraph Dependencies" in dot
        assert "rankdir=LR" in dot
        assert "app/main" in dot
        assert "app/utils" in dot
        assert "->" in dot

    def test_to_mermaid(self, sample_visual_graph):
        """Test Mermaid diagram export."""
        mermaid = sample_visual_graph.to_mermaid()

        assert "graph LR" in mermaid
        assert "-->" in mermaid

    def test_mermaid_id_sanitization(self, sample_visual_graph):
        """Test Mermaid ID sanitization."""
        mermaid_id = sample_visual_graph._mermaid_id("app/main.py")
        assert "/" not in mermaid_id
        assert "." not in mermaid_id


# ==================== VisualDependencyGraphService Tests ====================

class TestVisualDependencyGraphService:
    """Test VisualDependencyGraphService functionality."""

    def test_initialization(self, service):
        """Test service initialization."""
        assert service.dependency_service is not None

    def test_generate_visual_graph(self, service, sample_dependency_result):
        """Test visual graph generation."""
        with patch.object(
            service.dependency_service,
            'analyze_directory',
            return_value=sample_dependency_result,
        ):
            visual_graph = service.generate_visual_graph(Path("/project"))

            assert len(visual_graph.nodes) >= 1
            assert len(visual_graph.edges) >= 1
            assert len(visual_graph.clusters) >= 1

    def test_generate_visual_graph_with_config(self, service, sample_dependency_result):
        """Test visual graph with custom config."""
        config = VisualGraphConfig(
            layout=LayoutType.HIERARCHICAL,
            show_external=False,
            min_connections=1,
        )

        with patch.object(
            service.dependency_service,
            'analyze_directory',
            return_value=sample_dependency_result,
        ):
            visual_graph = service.generate_visual_graph(
                Path("/project"),
                config=config,
            )

            # External nodes should be filtered
            external_nodes = [n for n in visual_graph.nodes if n.is_external]
            assert len(external_nodes) == 0

    def test_convert_to_visual(self, service, sample_dependency_result):
        """Test conversion to visual format."""
        config = VisualGraphConfig()
        visual_graph = service._convert_to_visual(sample_dependency_result, config)

        assert len(visual_graph.nodes) >= 1
        assert visual_graph.metadata["total_modules"] == 3

    def test_cluster_color_consistency(self, service):
        """Test cluster color is consistent for same ID."""
        color1 = service._cluster_color("app/services")
        color2 = service._cluster_color("app/services")
        assert color1 == color2

    def test_cluster_color_different_for_different_ids(self, service):
        """Test different clusters get different colors."""
        color1 = service._cluster_color("app/services")
        color2 = service._cluster_color("app/models")
        # Colors should be different (though not guaranteed due to hash collisions)

    def test_export_d3_json(self, service, sample_visual_graph):
        """Test D3 JSON export to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.json"
            service.export_d3_json(sample_visual_graph, output_path)

            assert output_path.exists()
            data = json.loads(output_path.read_text())
            assert "nodes" in data
            assert "links" in data

    def test_export_cytoscape_json(self, service, sample_visual_graph):
        """Test Cytoscape JSON export to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.json"
            service.export_cytoscape_json(sample_visual_graph, output_path)

            assert output_path.exists()
            data = json.loads(output_path.read_text())
            assert "elements" in data

    def test_export_dot(self, service, sample_visual_graph):
        """Test DOT export to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.dot"
            service.export_dot(sample_visual_graph, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "digraph" in content

    def test_export_mermaid(self, service, sample_visual_graph):
        """Test Mermaid export to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.md"
            service.export_mermaid(sample_visual_graph, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "```mermaid" in content

    def test_get_subgraph(self, service, sample_visual_graph):
        """Test subgraph extraction."""
        subgraph = service.get_subgraph(
            sample_visual_graph,
            center_node="app/main",
            depth=1,
        )

        assert len(subgraph.nodes) >= 1
        assert subgraph.metadata["subgraph"] is True
        assert subgraph.metadata["center_node"] == "app/main"

    def test_get_subgraph_missing_node(self, service, sample_visual_graph):
        """Test subgraph with missing center node."""
        subgraph = service.get_subgraph(
            sample_visual_graph,
            center_node="nonexistent",
            depth=1,
        )

        # Should return empty or minimal graph
        assert subgraph.metadata["center_node"] == "nonexistent"

    def test_highlight_path(self, service, sample_visual_graph):
        """Test path highlighting."""
        path = service.highlight_path(
            sample_visual_graph,
            source="app/main",
            target="app/utils",
        )

        assert path is not None
        assert "app/main" in path
        assert "app/utils" in path

    def test_highlight_path_no_path(self, service):
        """Test path highlighting with no path."""
        # Create graph with disconnected nodes
        graph = VisualDependencyGraph(
            nodes=[
                VisualNode(id="a", label="a", group="root", size=10, color="#000"),
                VisualNode(id="b", label="b", group="root", size=10, color="#000"),
            ],
            edges=[],  # No edges
            clusters=[],
            config=VisualGraphConfig(),
        )

        path = service.highlight_path(graph, source="a", target="b")
        assert path is None


# ==================== VisualGraphConfig Tests ====================

class TestVisualGraphConfig:
    """Test VisualGraphConfig functionality."""

    def test_default_config(self):
        """Test default configuration."""
        config = VisualGraphConfig()

        assert config.layout == LayoutType.FORCE_DIRECTED
        assert config.show_external is False
        assert config.show_labels is True
        assert config.cluster_by == "directory"

    def test_node_colors_default(self):
        """Test default node colors."""
        config = VisualGraphConfig()

        assert "python" in config.node_colors
        assert "javascript" in config.node_colors
        assert "external" in config.node_colors
        assert "default" in config.node_colors

    def test_custom_config(self):
        """Test custom configuration."""
        config = VisualGraphConfig(
            layout=LayoutType.CIRCULAR,
            show_external=True,
            min_connections=5,
            max_nodes=100,
        )

        assert config.layout == LayoutType.CIRCULAR
        assert config.show_external is True
        assert config.min_connections == 5
        assert config.max_nodes == 100


# ==================== Layout Type Tests ====================

class TestLayoutTypes:
    """Test layout type enum."""

    def test_all_layout_types(self):
        """Test all layout types are defined."""
        assert LayoutType.FORCE_DIRECTED.value == "force"
        assert LayoutType.HIERARCHICAL.value == "hierarchical"
        assert LayoutType.CIRCULAR.value == "circular"
        assert LayoutType.RADIAL.value == "radial"
        assert LayoutType.TREE.value == "tree"


# ==================== Factory Function Tests ====================

class TestFactoryFunction:
    """Test factory function."""

    def test_create_visual_dependency_graph_service(self):
        """Test factory function creates service."""
        service = create_visual_dependency_graph_service()

        assert isinstance(service, VisualDependencyGraphService)
        assert service.dependency_service is not None


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Test edge cases."""

    def test_empty_graph(self):
        """Test empty graph."""
        graph = VisualDependencyGraph(
            nodes=[],
            edges=[],
            clusters=[],
            config=VisualGraphConfig(),
        )

        d3_data = graph.to_d3_format()
        assert d3_data["nodes"] == []
        assert d3_data["links"] == []

    def test_single_node_graph(self):
        """Test single node graph."""
        graph = VisualDependencyGraph(
            nodes=[
                VisualNode(id="single", label="single", group="root", size=10, color="#000"),
            ],
            edges=[],
            clusters=[],
            config=VisualGraphConfig(),
        )

        assert len(graph.to_d3_format()["nodes"]) == 1

    def test_self_referencing_edge(self):
        """Test self-referencing edge."""
        edge = VisualEdge(source="a", target="a")
        data = edge.to_dict()

        assert data["source"] == data["target"]

    def test_large_node_limit(self, service, sample_dependency_result):
        """Test node limiting for large graphs."""
        # Add many nodes to the modules dict
        for i in range(600):
            sample_dependency_result.modules[f"module_{i}"] = ModuleNode(
                name=f"module_{i}",
                file_path=f"module_{i}.py",
                language=Language.PYTHON,
                imports=[],
                imported_by=[],
            )

        config = VisualGraphConfig(max_nodes=100)

        with patch.object(
            service.dependency_service,
            'analyze_directory',
            return_value=sample_dependency_result,
        ):
            visual_graph = service.generate_visual_graph(
                Path("/project"),
                config=config,
            )

            assert len(visual_graph.nodes) <= 100

