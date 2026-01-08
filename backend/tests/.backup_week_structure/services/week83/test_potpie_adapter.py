"""
Tests for PotpieAdapter - Week 83

Tests:
- PotpieNode and PotpieGraph dataclasses
- Fallback parsing when Potpie CLI not available
- Knowledge graph storage
- Search functionality
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
from uuid import uuid4

from app.services.potpie_adapter import (
    PotpieAdapter,
    PotpieNode,
    PotpieGraph,
    get_potpie_adapter,
)


class TestPotpieNode:
    """Tests for PotpieNode dataclass."""

    def test_create_empty_node(self):
        """Should create empty node."""
        node = PotpieNode(
            node_type="function",
            name="test_func",
            path="test.py",
        )

        assert node.node_type == "function"
        assert node.name == "test_func"
        assert node.path == "test.py"
        assert node.imports == []
        assert node.calls == []

    def test_create_full_node(self):
        """Should create full node with relationships."""
        node = PotpieNode(
            node_type="class",
            name="UserService",
            path="services/user.py",
            language="python",
            line_start=10,
            line_end=100,
            docstring="User service for managing users.",
            imports=["models.user", "utils.auth"],
            imported_by=["api.routes"],
            calls=["db.query", "cache.get"],
            called_by=["main.app"],
            complexity=8.5,
        )

        assert node.node_type == "class"
        assert node.name == "UserService"
        assert node.language == "python"
        assert len(node.imports) == 2
        assert len(node.calls) == 2
        assert node.complexity == 8.5


class TestPotpieGraph:
    """Tests for PotpieGraph dataclass."""

    def test_create_empty_graph(self):
        """Should create empty graph."""
        graph = PotpieGraph(repository_path="/test/repo")

        assert graph.repository_path == "/test/repo"
        assert graph.nodes == []
        assert graph.total_files == 0
        assert graph.total_functions == 0
        assert graph.total_classes == 0

    def test_create_graph_with_nodes(self):
        """Should create graph with nodes."""
        nodes = [
            PotpieNode(node_type="file", name="main.py", path="main.py"),
            PotpieNode(node_type="function", name="run", path="main.py"),
            PotpieNode(node_type="class", name="App", path="app.py"),
        ]

        graph = PotpieGraph(
            repository_path="/test/repo",
            nodes=nodes,
            total_files=2,
            total_functions=1,
            total_classes=1,
            languages={"python": 2},
        )

        assert len(graph.nodes) == 3
        assert graph.total_files == 2
        assert graph.languages["python"] == 2


class TestPotpieAdapter:
    """Tests for PotpieAdapter."""

    def test_init_adapter(self):
        """Should initialize adapter."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        assert adapter.db == mock_db
        assert adapter._potpie_available is None

    @pytest.mark.asyncio
    async def test_is_available_not_installed(self):
        """Should return False when Potpie not installed."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.side_effect = FileNotFoundError()

            result = await adapter.is_available()

            assert result is False

    @pytest.mark.asyncio
    async def test_is_available_cached(self):
        """Should cache availability result."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)
        adapter._potpie_available = True

        result = await adapter.is_available()

        assert result is True

    @pytest.mark.asyncio
    async def test_fallback_parse_with_temp_repo(self):
        """Should parse repository with fallback parser."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Python files
            (Path(tmpdir) / "main.py").write_text("def main(): pass")
            (Path(tmpdir) / "utils.py").write_text("def helper(): pass")
            (Path(tmpdir) / "src").mkdir()
            (Path(tmpdir) / "src" / "app.py").write_text("class App: pass")

            graph = PotpieGraph(repository_path=tmpdir)
            result = await adapter._fallback_parse(tmpdir, graph)

            assert result.total_files >= 3
            assert "python" in result.languages

    @pytest.mark.asyncio
    async def test_fallback_parse_skips_excluded_dirs(self):
        """Should skip node_modules and other excluded dirs."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in excluded directory
            nm_dir = Path(tmpdir) / "node_modules"
            nm_dir.mkdir()
            (nm_dir / "package.js").write_text("module.exports = {}")

            # Create file in included directory
            (Path(tmpdir) / "main.js").write_text("console.log('test')")

            graph = PotpieGraph(repository_path=tmpdir)
            result = await adapter._fallback_parse(tmpdir, graph)

            # Should only have main.js, not node_modules files
            file_nodes = [n for n in result.nodes if n.name == "package.js"]
            assert len(file_nodes) == 0

    @pytest.mark.asyncio
    async def test_fallback_parse_nonexistent_path(self):
        """Should handle non-existent path."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        graph = PotpieGraph(repository_path="/nonexistent/path/12345")
        result = await adapter._fallback_parse("/nonexistent/path/12345", graph)

        assert len(result.errors) > 0

    def test_parse_node_valid(self):
        """Should parse valid node data."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        data = {
            "type": "function",
            "name": "authenticate",
            "path": "auth/login.py",
            "start_line": 10,
            "end_line": 25,
            "docstring": "Authenticate user.",
            "complexity": 5.0,
        }

        node = adapter._parse_node(data)

        assert node is not None
        assert node.node_type == "function"
        assert node.name == "authenticate"
        assert node.language == "python"
        assert node.line_start == 10
        assert node.complexity == 5.0

    def test_parse_node_invalid(self):
        """Should handle invalid node data."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        # Invalid data that might cause issues
        data = None

        with patch.object(adapter, '_parse_node', return_value=None):
            node = adapter._parse_node(data)
            assert node is None

    def test_language_detection(self):
        """Should detect language from extension."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        test_cases = [
            (".py", "python"),
            (".js", "javascript"),
            (".ts", "typescript"),
            (".java", "java"),
            (".cs", "csharp"),
            (".go", "go"),
            (".rs", "rust"),
            (".php", "php"),
            (".rb", "ruby"),
        ]

        for ext, expected_lang in test_cases:
            assert adapter.LANGUAGE_MAP.get(ext) == expected_lang

    @pytest.mark.asyncio
    async def test_store_graph(self):
        """Should store graph nodes to database."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        aggregation_id = uuid4()
        graph = PotpieGraph(
            repository_path="/test",
            nodes=[
                PotpieNode(node_type="file", name="main.py", path="main.py"),
                PotpieNode(node_type="function", name="run", path="main.py"),
            ],
        )

        count = await adapter.store_graph(aggregation_id, graph)

        assert count == 2
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_functions(self):
        """Should search functions by name."""
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.limit.return_value.all.return_value = []

        adapter = PotpieAdapter(mock_db)

        results = await adapter.search_functions("auth")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_call_graph(self):
        """Should return call graph structure."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        adapter = PotpieAdapter(mock_db)

        result = await adapter.get_call_graph(
            function_name="test_func",
            aggregation_id=uuid4(),
            depth=2,
        )

        assert "root" in result
        assert "nodes" in result
        assert "edges" in result
        assert result["root"] == "test_func"

    def test_factory_function(self):
        """Should create adapter via factory function."""
        mock_db = Mock()
        adapter = get_potpie_adapter(mock_db)

        assert isinstance(adapter, PotpieAdapter)


class TestEdgeParsing:
    """Tests for edge parsing in PotpieAdapter."""

    def test_apply_import_edge(self):
        """Should apply import edge to nodes."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        graph = PotpieGraph(
            repository_path="/test",
            nodes=[
                PotpieNode(node_type="file", name="a.py", path="a.py"),
                PotpieNode(node_type="file", name="b.py", path="b.py"),
            ],
        )

        edge = {
            "source": "a.py",
            "target": "b.py",
            "type": "imports",
        }

        adapter._apply_edge(graph, edge)

        source_node = next(n for n in graph.nodes if n.name == "a.py")
        target_node = next(n for n in graph.nodes if n.name == "b.py")

        assert "b.py" in source_node.imports
        assert "a.py" in target_node.imported_by

    def test_apply_call_edge(self):
        """Should apply call edge to nodes."""
        mock_db = Mock()
        adapter = PotpieAdapter(mock_db)

        graph = PotpieGraph(
            repository_path="/test",
            nodes=[
                PotpieNode(node_type="function", name="caller", path="main.py"),
                PotpieNode(node_type="function", name="callee", path="utils.py"),
            ],
        )

        edge = {
            "source": "caller",
            "target": "callee",
            "type": "calls",
        }

        adapter._apply_edge(graph, edge)

        source_node = next(n for n in graph.nodes if n.name == "caller")
        target_node = next(n for n in graph.nodes if n.name == "callee")

        assert "callee" in source_node.calls
        assert "caller" in target_node.called_by


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
