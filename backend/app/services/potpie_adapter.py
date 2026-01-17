"""
Potpie Knowledge Graph Adapter - Week 83

Adapter for integrating with Potpie for code knowledge graph generation.
Potpie provides:
- Code structure analysis
- Function/class relationship mapping
- Cross-file dependency tracking
- Semantic code understanding

Reference: github.com/potpie-ai/potpie

This adapter:
1. Converts Potpie output to our internal format
2. Stores results in PotpieKnowledgeGraphEntry
3. Provides query interface for semantic code search
"""

import asyncio
import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.code_analysis import PotpieKnowledgeGraphEntry, CodeAnalysisAggregation

logger = logging.getLogger(__name__)


@dataclass
class PotpieNode:
    """Parsed node from Potpie output."""
    node_type: str  # file, class, function, method, variable
    name: str
    path: str
    language: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    docstring: Optional[str] = None

    # Relationships
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)

    # Metrics
    complexity: Optional[float] = None


@dataclass
class PotpieGraph:
    """Complete knowledge graph from Potpie analysis."""
    repository_path: str
    nodes: List[PotpieNode] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Statistics
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    languages: Dict[str, int] = field(default_factory=dict)

    # Errors during parsing
    errors: List[str] = field(default_factory=list)


class PotpieAdapter:
    """
    Adapter for Potpie code knowledge graph.

    Provides:
    - Repository analysis via Potpie CLI
    - Knowledge graph parsing and storage
    - Semantic code search queries

    Usage:
        adapter = PotpieAdapter(db)
        graph = await adapter.analyze_repository("/path/to/repo")

        # Store results
        await adapter.store_graph(aggregation_id, graph)

        # Query
        results = await adapter.search_functions("authenticate")
    """

    # Node type mappings
    NODE_TYPE_MAP = {
        "file": "file",
        "class": "class",
        "function": "function",
        "method": "function",
        "module": "module",
        "variable": "variable",
        "import": "import",
    }

    # Language detection by extension
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
    }

    def __init__(self, db: Session):
        """Initialize Potpie adapter."""
        self.db = db
        self._potpie_available = None

    async def is_available(self) -> bool:
        """Check if Potpie CLI is installed and available."""
        if self._potpie_available is not None:
            return self._potpie_available

        try:
            result = await asyncio.create_subprocess_exec(
                "potpie", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            self._potpie_available = result.returncode == 0
        except FileNotFoundError:
            self._potpie_available = False
        except Exception as e:
            logger.warning(f"Error checking Potpie availability: {e}")
            self._potpie_available = False

        return self._potpie_available

    async def analyze_repository(
        self,
        repository_path: str,
        include_tests: bool = False,
        max_depth: int = 10,
    ) -> PotpieGraph:
        """
        Analyze repository with Potpie to generate knowledge graph.

        Args:
            repository_path: Path to repository
            include_tests: Whether to include test files
            max_depth: Maximum directory depth to traverse

        Returns:
            PotpieGraph with all parsed nodes
        """
        graph = PotpieGraph(repository_path=repository_path)

        # Check if Potpie is available
        if not await self.is_available():
            logger.warning("Potpie CLI not available, using fallback parser")
            return await self._fallback_parse(repository_path, graph)

        try:
            # Run Potpie analysis
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                output_file = f.name

            cmd = [
                "potpie", "analyze",
                repository_path,
                "--output", output_file,
                "--format", "json",
                "--depth", str(max_depth),
            ]

            if not include_tests:
                cmd.extend(["--exclude", "**/test*", "--exclude", "**/*_test.*"])

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                graph.errors.append(f"Potpie analysis failed: {error_msg}")
                return await self._fallback_parse(repository_path, graph)

            # Parse output
            with open(output_file, "r") as f:
                data = json.load(f)

            graph = self._parse_potpie_output(data, repository_path)

        except Exception as e:
            logger.exception(f"Error running Potpie: {e}")
            graph.errors.append(f"Potpie error: {str(e)}")
            return await self._fallback_parse(repository_path, graph)

        return graph

    def _parse_potpie_output(self, data: Dict[str, Any], repo_path: str) -> PotpieGraph:
        """Parse Potpie JSON output into PotpieGraph."""
        graph = PotpieGraph(repository_path=repo_path)

        # Parse nodes from Potpie format
        for node_data in data.get("nodes", []):
            node = self._parse_node(node_data)
            if node:
                graph.nodes.append(node)

                # Update statistics
                if node.node_type == "file":
                    graph.total_files += 1
                elif node.node_type == "function":
                    graph.total_functions += 1
                elif node.node_type == "class":
                    graph.total_classes += 1

                if node.language:
                    graph.languages[node.language] = graph.languages.get(node.language, 0) + 1

        # Parse edges (relationships)
        for edge_data in data.get("edges", []):
            self._apply_edge(graph, edge_data)

        return graph

    def _parse_node(self, data: Dict[str, Any]) -> Optional[PotpieNode]:
        """Parse a single node from Potpie output."""
        try:
            node_type = self.NODE_TYPE_MAP.get(
                data.get("type", "").lower(),
                data.get("type", "unknown")
            )

            path = data.get("path", "")
            extension = Path(path).suffix if path else ""
            language = self.LANGUAGE_MAP.get(extension)

            return PotpieNode(
                node_type=node_type,
                name=data.get("name", ""),
                path=path,
                language=language,
                line_start=data.get("start_line"),
                line_end=data.get("end_line"),
                docstring=data.get("docstring"),
                complexity=data.get("complexity"),
            )
        except Exception as e:
            logger.warning(f"Error parsing node: {e}")
            return None

    def _apply_edge(self, graph: PotpieGraph, edge: Dict[str, Any]) -> None:
        """Apply edge (relationship) to nodes in graph."""
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type", "").lower()

        if not source or not target:
            return

        # Find source and target nodes
        source_node = next((n for n in graph.nodes if n.name == source or n.path == source), None)
        target_node = next((n for n in graph.nodes if n.name == target or n.path == target), None)

        if source_node and target_node:
            if edge_type in ("imports", "import"):
                source_node.imports.append(target)
                target_node.imported_by.append(source)
            elif edge_type in ("calls", "call"):
                source_node.calls.append(target)
                target_node.called_by.append(source)

    async def _fallback_parse(
        self,
        repository_path: str,
        graph: PotpieGraph
    ) -> PotpieGraph:
        """
        Fallback parser when Potpie is not available.

        Uses basic file system traversal and pattern matching.
        """
        logger.info("Using fallback parser for knowledge graph generation")

        repo_path = Path(repository_path)
        if not repo_path.exists():
            graph.errors.append(f"Repository path not found: {repository_path}")
            return graph

        # Traverse files
        for ext, language in self.LANGUAGE_MAP.items():
            for file_path in repo_path.rglob(f"*{ext}"):
                # Skip common excluded patterns
                path_str = str(file_path)
                if any(skip in path_str for skip in [
                    "node_modules", ".git", "__pycache__", "venv", ".venv",
                    "dist", "build", ".next", "vendor"
                ]):
                    continue

                relative_path = str(file_path.relative_to(repo_path))

                # Create file node
                file_node = PotpieNode(
                    node_type="file",
                    name=file_path.name,
                    path=relative_path,
                    language=language,
                )

                # Count lines
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = len(f.readlines())
                    file_node.line_end = lines
                except Exception:
                    pass

                graph.nodes.append(file_node)
                graph.total_files += 1
                graph.languages[language] = graph.languages.get(language, 0) + 1

        return graph

    async def store_graph(
        self,
        aggregation_id: UUID,
        graph: PotpieGraph
    ) -> int:
        """
        Store knowledge graph nodes in database.

        Args:
            aggregation_id: UUID of CodeAnalysisAggregation
            graph: PotpieGraph to store

        Returns:
            Number of nodes stored
        """
        count = 0

        for node in graph.nodes:
            entry = PotpieKnowledgeGraphEntry(
                aggregation_id=aggregation_id,
                node_type=node.node_type,
                node_name=node.name,
                node_path=node.path,
                language=node.language,
                line_start=node.line_start,
                line_end=node.line_end,
                complexity=node.complexity,
                imports=node.imports,
                imported_by=node.imported_by,
                calls=node.calls,
                called_by=node.called_by,
                docstring=node.docstring,
            )
            self.db.add(entry)
            count += 1

        self.db.commit()
        return count

    async def search_functions(
        self,
        query: str,
        aggregation_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[PotpieKnowledgeGraphEntry]:
        """
        Search for functions by name pattern.

        Args:
            query: Name pattern to search
            aggregation_id: Limit to specific aggregation
            limit: Maximum results

        Returns:
            List of matching knowledge graph entries
        """
        q = self.db.query(PotpieKnowledgeGraphEntry).filter(
            PotpieKnowledgeGraphEntry.node_type == "function",
            PotpieKnowledgeGraphEntry.node_name.ilike(f"%{query}%")
        )

        if aggregation_id:
            q = q.filter(PotpieKnowledgeGraphEntry.aggregation_id == aggregation_id)

        return q.limit(limit).all()

    async def get_call_graph(
        self,
        function_name: str,
        aggregation_id: UUID,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get call graph for a function.

        Args:
            function_name: Name of function
            aggregation_id: Aggregation UUID
            depth: Depth of call graph to retrieve

        Returns:
            Dict with nodes and edges for visualization
        """
        nodes = []
        edges = []
        visited = set()

        async def traverse(name: str, current_depth: int):
            if current_depth > depth or name in visited:
                return

            visited.add(name)

            entry = self.db.query(PotpieKnowledgeGraphEntry).filter(
                PotpieKnowledgeGraphEntry.aggregation_id == aggregation_id,
                PotpieKnowledgeGraphEntry.node_name == name,
                PotpieKnowledgeGraphEntry.node_type == "function"
            ).first()

            if not entry:
                return

            nodes.append({
                "id": str(entry.id),
                "name": entry.node_name,
                "type": entry.node_type,
                "path": entry.node_path,
            })

            for called in (entry.calls or []):
                edges.append({
                    "source": entry.node_name,
                    "target": called,
                    "type": "calls"
                })
                await traverse(called, current_depth + 1)

        await traverse(function_name, 0)

        return {
            "root": function_name,
            "nodes": nodes,
            "edges": edges,
            "depth": depth,
        }


def get_potpie_adapter(db: Session) -> PotpieAdapter:
    """Factory function for PotpieAdapter."""
    return PotpieAdapter(db)
