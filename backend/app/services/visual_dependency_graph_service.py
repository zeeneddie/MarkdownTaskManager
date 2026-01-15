"""
Visual Dependency Graph Service (E1 - Fase 24).

Extends DependencyGraphService to provide D3.js compatible visualization
with interactive features like zoom, filter, and clustering.

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple

from .dependency_graph_service import (
    DependencyGraphService,
    DependencyGraphResult,
    ModuleNode,
    DependencyEdge,
    DependencyMetrics,
    CircularDependency,
    Language,
)

logger = logging.getLogger(__name__)


class LayoutType(str, Enum):
    """Graph layout algorithm."""
    FORCE_DIRECTED = "force"
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    RADIAL = "radial"
    TREE = "tree"


class NodeShape(str, Enum):
    """Node shape for visualization."""
    CIRCLE = "circle"
    RECTANGLE = "rect"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"


class EdgeStyle(str, Enum):
    """Edge line style."""
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


@dataclass
class VisualNode:
    """Node for D3.js visualization."""
    id: str
    label: str
    group: str  # For clustering
    size: int  # Based on importance
    color: str
    shape: NodeShape = NodeShape.CIRCLE

    # Metrics
    imports_count: int = 0
    imported_by_count: int = 0
    is_external: bool = False
    is_entry_point: bool = False
    is_hub: bool = False
    circular_dependency: bool = False

    # Position (optional, for fixed layouts)
    x: Optional[float] = None
    y: Optional[float] = None
    fx: Optional[float] = None  # Fixed x
    fy: Optional[float] = None  # Fixed y

    # Metadata
    file_path: str = ""
    language: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to D3.js compatible format."""
        result = {
            "id": self.id,
            "label": self.label,
            "group": self.group,
            "size": self.size,
            "color": self.color,
            "shape": self.shape.value,
            "imports": self.imports_count,
            "importedBy": self.imported_by_count,
            "isExternal": self.is_external,
            "isEntryPoint": self.is_entry_point,
            "isHub": self.is_hub,
            "hasCircular": self.circular_dependency,
            "filePath": self.file_path,
            "language": self.language,
        }

        if self.x is not None:
            result["x"] = self.x
        if self.y is not None:
            result["y"] = self.y
        if self.fx is not None:
            result["fx"] = self.fx
        if self.fy is not None:
            result["fy"] = self.fy

        return result


@dataclass
class VisualEdge:
    """Edge for D3.js visualization."""
    source: str
    target: str
    weight: float = 1.0
    style: EdgeStyle = EdgeStyle.SOLID
    color: str = "#999"
    label: str = ""
    is_circular: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to D3.js compatible format."""
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "style": self.style.value,
            "color": self.color,
            "label": self.label,
            "isCircular": self.is_circular,
        }


@dataclass
class Cluster:
    """Node cluster for grouping."""
    id: str
    name: str
    nodes: List[str] = field(default_factory=list)
    color: str = "#666"
    is_expanded: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "nodes": self.nodes,
            "color": self.color,
            "expanded": self.is_expanded,
            "nodeCount": len(self.nodes),
        }


@dataclass
class VisualGraphConfig:
    """Configuration for visual graph."""
    layout: LayoutType = LayoutType.FORCE_DIRECTED
    show_external: bool = False
    show_labels: bool = True
    cluster_by: str = "directory"  # directory, language, none
    min_connections: int = 0  # Filter nodes with fewer connections
    highlight_circular: bool = True
    max_nodes: int = 500

    # Force simulation params
    force_strength: float = -300
    link_distance: int = 100
    collision_radius: int = 30

    # Colors
    node_colors: Dict[str, str] = field(default_factory=lambda: {
        "python": "#3776ab",
        "javascript": "#f7df1e",
        "typescript": "#3178c6",
        "go": "#00add8",
        "java": "#007396",
        "csharp": "#68217a",
        "rust": "#dea584",
        "ruby": "#cc342d",
        "php": "#777bb4",
        "default": "#69b3a2",
        "external": "#999",
    })


@dataclass
class VisualDependencyGraph:
    """Complete visual dependency graph."""
    nodes: List[VisualNode]
    edges: List[VisualEdge]
    clusters: List[Cluster]
    config: VisualGraphConfig
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_d3_format(self) -> Dict[str, Any]:
        """Convert to D3.js compatible JSON format."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "links": [e.to_dict() for e in self.edges],
            "clusters": [c.to_dict() for c in self.clusters],
            "config": {
                "layout": self.config.layout.value,
                "showLabels": self.config.show_labels,
                "highlightCircular": self.config.highlight_circular,
                "forceStrength": self.config.force_strength,
                "linkDistance": self.config.link_distance,
                "collisionRadius": self.config.collision_radius,
            },
            "metadata": self.metadata,
        }

    def to_cytoscape_format(self) -> Dict[str, Any]:
        """Convert to Cytoscape.js compatible format."""
        elements = []

        # Add nodes
        for node in self.nodes:
            elements.append({
                "data": {
                    "id": node.id,
                    "label": node.label,
                    "parent": node.group if node.group != "root" else None,
                    **node.to_dict(),
                },
                "classes": " ".join([
                    node.language,
                    "hub" if node.is_hub else "",
                    "circular" if node.circular_dependency else "",
                ]).strip(),
            })

        # Add edges
        for edge in self.edges:
            elements.append({
                "data": {
                    "id": f"{edge.source}->{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                    "weight": edge.weight,
                },
                "classes": "circular" if edge.is_circular else "",
            })

        return {
            "elements": elements,
            "style": self._cytoscape_style(),
            "layout": {
                "name": "cose" if self.config.layout == LayoutType.FORCE_DIRECTED else self.config.layout.value,
            },
        }

    def _cytoscape_style(self) -> List[Dict[str, Any]]:
        """Generate Cytoscape.js style array."""
        return [
            {
                "selector": "node",
                "style": {
                    "label": "data(label)",
                    "background-color": "data(color)",
                    "width": "data(size)",
                    "height": "data(size)",
                },
            },
            {
                "selector": "edge",
                "style": {
                    "width": 2,
                    "line-color": "#ccc",
                    "target-arrow-color": "#ccc",
                    "target-arrow-shape": "triangle",
                    "curve-style": "bezier",
                },
            },
            {
                "selector": ".circular",
                "style": {
                    "line-color": "#e74c3c",
                    "target-arrow-color": "#e74c3c",
                },
            },
            {
                "selector": ".hub",
                "style": {
                    "border-width": 3,
                    "border-color": "#f39c12",
                },
            },
        ]

    def to_graphviz_dot(self) -> str:
        """Convert to Graphviz DOT format."""
        lines = ["digraph Dependencies {"]
        lines.append('    rankdir=LR;')
        lines.append('    node [shape=box, style=filled];')

        # Add clusters (subgraphs)
        for cluster in self.clusters:
            if cluster.nodes:
                lines.append(f'    subgraph cluster_{cluster.id.replace("/", "_")} {{')
                lines.append(f'        label="{cluster.name}";')
                lines.append(f'        color="{cluster.color}";')
                for node_id in cluster.nodes:
                    lines.append(f'        "{node_id}";')
                lines.append('    }')

        # Add nodes with colors
        for node in self.nodes:
            attrs = f'fillcolor="{node.color}", label="{node.label}"'
            if node.is_hub:
                attrs += ', penwidth=3'
            lines.append(f'    "{node.id}" [{attrs}];')

        # Add edges
        for edge in self.edges:
            style = "dashed" if edge.is_circular else "solid"
            color = "red" if edge.is_circular else "black"
            lines.append(f'    "{edge.source}" -> "{edge.target}" [style={style}, color={color}];')

        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Convert to Mermaid diagram format."""
        lines = ["graph LR"]

        # Add nodes with styling
        for node in self.nodes:
            shape_start, shape_end = "(", ")"
            if node.shape == NodeShape.RECTANGLE:
                shape_start, shape_end = "[", "]"
            elif node.shape == NodeShape.DIAMOND:
                shape_start, shape_end = "{", "}"

            lines.append(f'    {self._mermaid_id(node.id)}{shape_start}"{node.label}"{shape_end}')

        # Add edges
        for edge in self.edges:
            arrow = "-->" if not edge.is_circular else "-..->"
            lines.append(f'    {self._mermaid_id(edge.source)} {arrow} {self._mermaid_id(edge.target)}')

        return "\n".join(lines)

    def _mermaid_id(self, node_id: str) -> str:
        """Convert node ID to valid Mermaid ID."""
        return node_id.replace("/", "_").replace(".", "_").replace("-", "_")


class VisualDependencyGraphService:
    """
    Service for generating visual dependency graphs.

    Extends DependencyGraphService with D3.js/Cytoscape.js
    compatible output formats and visualization features.
    """

    def __init__(self, dependency_service: Optional[DependencyGraphService] = None):
        """Initialize service."""
        self.dependency_service = dependency_service or DependencyGraphService()

    def generate_visual_graph(
        self,
        project_path: Path,
        config: Optional[VisualGraphConfig] = None,
    ) -> VisualDependencyGraph:
        """
        Generate visual dependency graph.

        Args:
            project_path: Path to analyze
            config: Visualization configuration

        Returns:
            Visual graph ready for D3.js/Cytoscape.js
        """
        config = config or VisualGraphConfig()

        # Get dependency graph from base service
        dep_result = self.dependency_service.analyze_directory(str(project_path))

        # Convert to visual format
        return self._convert_to_visual(dep_result, config)

    def _convert_to_visual(
        self,
        dep_result: DependencyGraphResult,
        config: VisualGraphConfig,
    ) -> VisualDependencyGraph:
        """Convert DependencyGraphResult to visual format."""
        # Get circular dependency nodes
        circular_nodes = set()
        for cd in dep_result.circular_dependencies:
            circular_nodes.update(cd.cycle)

        # Build visual nodes
        visual_nodes = []
        node_to_cluster: Dict[str, str] = {}

        # Get nodes from modules dict
        nodes = dep_result.modules.values()

        for node in nodes:
            # Calculate import/imported_by counts
            import_count = len(node.imports)
            imported_by_count = len(node.imported_by)

            # Determine if external (no file_path or external import)
            is_external = not node.file_path or node.file_path.startswith("<")

            # Skip external if configured
            if is_external and not config.show_external:
                continue

            # Filter by connection count
            total_connections = import_count + imported_by_count
            if total_connections < config.min_connections:
                continue

            # Determine cluster
            if config.cluster_by == "directory":
                cluster = str(Path(node.file_path).parent) if node.file_path else "root"
            elif config.cluster_by == "language":
                cluster = node.language.value if isinstance(node.language, Language) else str(node.language)
            else:
                cluster = "root"

            node_to_cluster[node.name] = cluster

            # Determine color
            lang = node.language.value if isinstance(node.language, Language) else str(node.language)
            if is_external:
                color = config.node_colors.get("external", "#999")
            else:
                color = config.node_colors.get(lang, config.node_colors["default"])

            # Calculate size based on importance
            size = 10 + min(total_connections * 2, 40)

            # Check if hub (high connectivity)
            is_hub = total_connections > 10

            visual_nodes.append(VisualNode(
                id=node.name,
                label=Path(node.name).stem if "/" in node.name else node.name,
                group=cluster,
                size=size,
                color=color,
                imports_count=import_count,
                imported_by_count=imported_by_count,
                is_external=is_external,
                is_entry_point=imported_by_count == 0 and import_count > 0,
                is_hub=is_hub,
                circular_dependency=node.name in circular_nodes,
                file_path=node.file_path,
                language=lang,
            ))

        # Limit nodes if too many
        if len(visual_nodes) > config.max_nodes:
            # Keep most connected nodes
            visual_nodes.sort(
                key=lambda n: n.imports_count + n.imported_by_count,
                reverse=True,
            )
            visual_nodes = visual_nodes[:config.max_nodes]
            included_nodes = {n.id for n in visual_nodes}
        else:
            included_nodes = {n.id for n in visual_nodes}

        # Build visual edges
        visual_edges = []
        circular_edges = set()

        # Track circular edges
        for cd in dep_result.circular_dependencies:
            for i, node in enumerate(cd.nodes):
                next_node = cd.nodes[(i + 1) % len(cd.nodes)]
                circular_edges.add((node, next_node))

        for edge in dep_result.edges:
            # Only include edges for included nodes
            if edge.source not in included_nodes or edge.target not in included_nodes:
                continue

            is_circular = (edge.source, edge.target) in circular_edges
            color = "#e74c3c" if is_circular else "#999"
            style = EdgeStyle.DASHED if is_circular else EdgeStyle.SOLID

            visual_edges.append(VisualEdge(
                source=edge.source,
                target=edge.target,
                weight=1.0,
                style=style,
                color=color,
                is_circular=is_circular,
            ))

        # Build clusters
        clusters_dict: Dict[str, List[str]] = defaultdict(list)
        for node in visual_nodes:
            clusters_dict[node.group].append(node.id)

        clusters = [
            Cluster(
                id=cluster_id,
                name=Path(cluster_id).name if "/" in cluster_id else cluster_id,
                nodes=nodes,
                color=self._cluster_color(cluster_id),
            )
            for cluster_id, nodes in clusters_dict.items()
        ]

        # Build metadata
        metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "project_path": dep_result.project_path if dep_result.project_path else "",
            "total_modules": len(dep_result.modules),
            "total_edges": len(dep_result.edges),
            "circular_dependencies": len(dep_result.circular_dependencies),
            "languages": [lang.value if isinstance(lang, Language) else str(lang) for lang in dep_result.languages_detected],
            "metrics": {
                "avg_imports": dep_result.metrics.average_imports_per_module,
                "max_imports": dep_result.metrics.max_imports,
                "entry_points": dep_result.metrics.entry_points,
                "hub_modules": dep_result.metrics.hub_modules,
            },
        }

        return VisualDependencyGraph(
            nodes=visual_nodes,
            edges=visual_edges,
            clusters=clusters,
            config=config,
            metadata=metadata,
        )

    def _cluster_color(self, cluster_id: str) -> str:
        """Generate consistent color for cluster."""
        # Simple hash-based color
        hash_val = hash(cluster_id)
        hue = (hash_val % 360)
        return f"hsl({hue}, 60%, 70%)"

    def export_d3_json(
        self,
        visual_graph: VisualDependencyGraph,
        output_path: Path,
    ) -> None:
        """Export graph to D3.js JSON file."""
        data = visual_graph.to_d3_format()
        output_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Exported D3 graph to {output_path}")

    def export_cytoscape_json(
        self,
        visual_graph: VisualDependencyGraph,
        output_path: Path,
    ) -> None:
        """Export graph to Cytoscape.js JSON file."""
        data = visual_graph.to_cytoscape_format()
        output_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Exported Cytoscape graph to {output_path}")

    def export_dot(
        self,
        visual_graph: VisualDependencyGraph,
        output_path: Path,
    ) -> None:
        """Export graph to Graphviz DOT file."""
        dot_content = visual_graph.to_graphviz_dot()
        output_path.write_text(dot_content)
        logger.info(f"Exported DOT graph to {output_path}")

    def export_mermaid(
        self,
        visual_graph: VisualDependencyGraph,
        output_path: Path,
    ) -> None:
        """Export graph to Mermaid markdown file."""
        mermaid_content = visual_graph.to_mermaid()
        content = f"```mermaid\n{mermaid_content}\n```"
        output_path.write_text(content)
        logger.info(f"Exported Mermaid graph to {output_path}")

    def get_subgraph(
        self,
        visual_graph: VisualDependencyGraph,
        center_node: str,
        depth: int = 2,
    ) -> VisualDependencyGraph:
        """
        Extract subgraph centered on a node.

        Args:
            visual_graph: Full visual graph
            center_node: Node to center on
            depth: How many hops to include

        Returns:
            Subgraph centered on the node
        """
        # BFS to find nodes within depth
        included_nodes = {center_node}
        current_level = {center_node}

        for _ in range(depth):
            next_level = set()
            for node_id in current_level:
                # Find connected nodes
                for edge in visual_graph.edges:
                    if edge.source == node_id:
                        next_level.add(edge.target)
                    if edge.target == node_id:
                        next_level.add(edge.source)
            included_nodes.update(next_level)
            current_level = next_level

        # Filter nodes and edges
        filtered_nodes = [n for n in visual_graph.nodes if n.id in included_nodes]
        filtered_edges = [
            e for e in visual_graph.edges
            if e.source in included_nodes and e.target in included_nodes
        ]

        # Rebuild clusters
        clusters_dict: Dict[str, List[str]] = defaultdict(list)
        for node in filtered_nodes:
            clusters_dict[node.group].append(node.id)

        clusters = [
            Cluster(id=cid, name=Path(cid).name if "/" in cid else cid, nodes=nodes)
            for cid, nodes in clusters_dict.items()
        ]

        return VisualDependencyGraph(
            nodes=filtered_nodes,
            edges=filtered_edges,
            clusters=clusters,
            config=visual_graph.config,
            metadata={
                **visual_graph.metadata,
                "subgraph": True,
                "center_node": center_node,
                "depth": depth,
            },
        )

    def highlight_path(
        self,
        visual_graph: VisualDependencyGraph,
        source: str,
        target: str,
    ) -> Optional[List[str]]:
        """
        Find and highlight dependency path between two nodes.

        Args:
            visual_graph: Visual graph
            source: Source node ID
            target: Target node ID

        Returns:
            List of node IDs in the path, or None if no path exists
        """
        # Build adjacency list
        adj: Dict[str, List[str]] = defaultdict(list)
        for edge in visual_graph.edges:
            adj[edge.source].append(edge.target)

        # BFS for shortest path
        visited = {source}
        queue = [(source, [source])]

        while queue:
            current, path = queue.pop(0)

            if current == target:
                return path

            for neighbor in adj[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None


def create_visual_dependency_graph_service() -> VisualDependencyGraphService:
    """Factory function to create Visual Dependency Graph service."""
    return VisualDependencyGraphService()
