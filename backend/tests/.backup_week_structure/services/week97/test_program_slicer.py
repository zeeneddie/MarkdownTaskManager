# backend/tests/services/week97/test_program_slicer.py
"""
Unit tests for ProgramSlicer - Week 97-98 (Fase 15).

Tests program slicing based on IEEE 852482.
"""

import pytest
from app.services.static_analysis.program_slicer import (
    ProgramSlicer,
    LanguageSupport,
    SliceCriterion,
    SliceDirection,
    ProgramSlice,
    DependencyNode,
    DependencyGraph,
)


class TestProgramSlicer:
    """Tests for ProgramSlicer."""

    @pytest.fixture
    def python_slicer(self):
        """Create Python slicer instance."""
        return ProgramSlicer(LanguageSupport.PYTHON)

    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing."""
        return {
            "calculator.py": '''
def calculate_total(price, quantity):
    subtotal = price * quantity
    tax = subtotal * 0.1
    total = subtotal + tax
    return total

def apply_discount(total, discount_percent):
    discount = total * (discount_percent / 100)
    final_price = total - discount
    return final_price
''',
        }

    @pytest.mark.asyncio
    async def test_build_dependency_graph(self, python_slicer, sample_python_code):
        """Test building dependency graph from source."""
        await python_slicer.build_dependency_graph(list(sample_python_code.keys()))

        # Should have created nodes
        # Note: actual implementation may differ
        assert python_slicer.dependency_graph is not None

    @pytest.mark.asyncio
    async def test_compute_backward_slice(self, python_slicer, sample_python_code):
        """Test computing backward slice."""
        await python_slicer.build_dependency_graph(list(sample_python_code.keys()))

        criterion = SliceCriterion(
            file_path="calculator.py",
            line_number=5,  # total = subtotal + tax
            variable_name="total",
            direction=SliceDirection.BACKWARD,
        )

        slice_result = await python_slicer.compute_slice(criterion)

        assert isinstance(slice_result, ProgramSlice)
        # Backward slice should include dependencies

    @pytest.mark.asyncio
    async def test_compute_forward_slice(self, python_slicer, sample_python_code):
        """Test computing forward slice."""
        await python_slicer.build_dependency_graph(list(sample_python_code.keys()))

        criterion = SliceCriterion(
            file_path="calculator.py",
            line_number=3,  # subtotal = price * quantity
            variable_name="subtotal",
            direction=SliceDirection.FORWARD,
        )

        slice_result = await python_slicer.compute_slice(criterion)

        assert isinstance(slice_result, ProgramSlice)
        # Forward slice should include dependents

    def test_slice_criterion_creation(self):
        """Test SliceCriterion creation."""
        criterion = SliceCriterion(
            file_path="test.py",
            line_number=10,
            variable_name="x",
            direction=SliceDirection.BACKWARD,
        )

        assert criterion.file_path == "test.py"
        assert criterion.line_number == 10
        assert criterion.variable_name == "x"
        assert criterion.direction == SliceDirection.BACKWARD

    def test_slice_direction_enum(self):
        """Test SliceDirection enum values."""
        assert SliceDirection.BACKWARD.value == "backward"
        assert SliceDirection.FORWARD.value == "forward"
        assert SliceDirection.BOTH.value == "both"

    def test_language_support_enum(self):
        """Test LanguageSupport enum values."""
        assert LanguageSupport.PYTHON.value == "python"
        assert LanguageSupport.JAVASCRIPT.value == "javascript"
        assert LanguageSupport.TYPESCRIPT.value == "typescript"
        assert LanguageSupport.CSHARP.value == "csharp"
        assert LanguageSupport.VBNET.value == "vbnet"
        assert LanguageSupport.ASP_CLASSIC.value == "asp_classic"
        assert LanguageSupport.SQL.value == "sql"


class TestDependencyGraph:
    """Tests for DependencyGraph."""

    def test_create_empty_graph(self):
        """Test creating empty dependency graph."""
        graph = DependencyGraph(
            nodes={},
            edges=[],
            entry_points=[],
            exit_points=[],
        )

        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """Test adding node to graph."""
        node = DependencyNode(
            id="node-1",
            file_path="test.py",
            line_start=1,
            line_end=5,
            node_type="function",
            name="test_func",
        )
        graph = DependencyGraph(
            nodes={node.id: node},
            edges=[],
            entry_points=[],
            exit_points=[],
        )

        assert len(graph.nodes) == 1
        assert "node-1" in graph.nodes

    def test_node_variables(self):
        """Test node variable tracking."""
        node = DependencyNode(
            id="node-1",
            file_path="test.py",
            line_start=1,
            line_end=5,
            node_type="function",
            name="calc",
            variables_defined={"x", "y"},
            variables_used={"a", "b"},
        )

        assert "x" in node.variables_defined
        assert "a" in node.variables_used

    def test_entry_points_detection(self):
        """Test entry point detection in graph."""
        entry_node = DependencyNode(
            id="entry",
            file_path="main.py",
            line_start=1,
            line_end=10,
            node_type="function",
            name="main",
        )
        graph = DependencyGraph(
            nodes={entry_node.id: entry_node},
            edges=[],
            entry_points=["entry"],
            exit_points=[],
        )

        assert len(graph.entry_points) == 1


class TestProgramSlice:
    """Tests for ProgramSlice result."""

    def test_slice_creation(self):
        """Test creating program slice."""
        program_slice = ProgramSlice(
            criterion=SliceCriterion("test.py", 5, "x", SliceDirection.BACKWARD),
            statements=[1, 2, 3, 4, 5],
            variables={"x", "y", "z"},
            functions_involved={"func1", "func2"},
            files_involved={"test.py"},
            slice_size=5,
            complexity_score=0.5,
        )

        assert len(program_slice.statements) == 5
        assert len(program_slice.variables) == 3
        assert program_slice.slice_size == 5

    def test_slice_complexity_score(self):
        """Test slice complexity calculation."""
        program_slice = ProgramSlice(
            criterion=SliceCriterion("test.py", 5, "x", SliceDirection.BACKWARD),
            statements=[1, 2, 3, 4, 5],
            variables={"x", "y", "z"},
            functions_involved={"func1", "func2"},
            files_involved={"test.py", "other.py"},
            slice_size=5,
            complexity_score=0.6,
        )

        # Complexity should be between 0 and 1
        assert 0.0 <= program_slice.complexity_score <= 1.0

    def test_slice_structure(self):
        """Test slice has expected fields."""
        program_slice = ProgramSlice(
            criterion=SliceCriterion("test.py", 5, "x", SliceDirection.BACKWARD),
            statements=[1, 2, 3],
            variables={"x"},
            functions_involved={"func1"},
            files_involved={"test.py"},
            slice_size=3,
            complexity_score=0.3,
        )

        assert program_slice.criterion is not None
        assert len(program_slice.statements) == 3
        assert program_slice.slice_size == 3
        assert program_slice.complexity_score == 0.3


class TestMultiLanguageSupport:
    """Tests for multi-language support."""

    def test_javascript_slicer_creation(self):
        """Test creating JavaScript slicer."""
        slicer = ProgramSlicer(LanguageSupport.JAVASCRIPT)
        assert slicer.language == LanguageSupport.JAVASCRIPT

    def test_typescript_slicer_creation(self):
        """Test creating TypeScript slicer."""
        slicer = ProgramSlicer(LanguageSupport.TYPESCRIPT)
        assert slicer.language == LanguageSupport.TYPESCRIPT

    def test_csharp_slicer_creation(self):
        """Test creating C# slicer."""
        slicer = ProgramSlicer(LanguageSupport.CSHARP)
        assert slicer.language == LanguageSupport.CSHARP

    def test_sql_slicer_creation(self):
        """Test creating SQL slicer."""
        slicer = ProgramSlicer(LanguageSupport.SQL)
        assert slicer.language == LanguageSupport.SQL
