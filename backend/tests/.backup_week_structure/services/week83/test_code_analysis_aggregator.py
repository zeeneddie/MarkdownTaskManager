"""
Tests for CodeAnalysisAggregatorService - Week 83

Tests:
- TechnologyProfile dataclass
- DependencyProfile dataclass
- ComplexityProfile dataclass
- AggregatedAnalysis generation
- LLM context string generation
- Analysis score calculation
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

from app.services.code_analysis_aggregator_service import (
    CodeAnalysisAggregatorService,
    TechnologyProfile,
    DependencyProfile,
    DocumentationProfile,
    ComplexityProfile,
    AggregatedAnalysis,
    get_aggregator_service,
)


class TestTechnologyProfile:
    """Tests for TechnologyProfile dataclass."""

    def test_create_empty_profile(self):
        """Should create empty technology profile."""
        profile = TechnologyProfile()

        assert profile.primary_stack is None
        assert profile.secondary_stacks == []
        assert profile.database_type is None
        assert profile.total_files == 0
        assert profile.total_loc == 0

    def test_create_full_profile(self):
        """Should create full technology profile."""
        profile = TechnologyProfile(
            primary_stack="python",
            secondary_stacks=["javascript", "typescript"],
            database_type="postgresql",
            languages={"py": 100, "js": 50},
            frameworks=["django", "react"],
            total_files=150,
            total_loc=25000,
        )

        assert profile.primary_stack == "python"
        assert len(profile.secondary_stacks) == 2
        assert profile.database_type == "postgresql"
        assert profile.total_files == 150

    def test_to_dict(self):
        """Should convert to dictionary."""
        profile = TechnologyProfile(
            primary_stack="csharp",
            database_type="sqlserver",
            total_files=500,
            total_loc=100000,
        )

        result = profile.to_dict()

        assert result["primary_stack"] == "csharp"
        assert result["database_type"] == "sqlserver"
        assert result["total_files"] == 500
        assert result["total_loc"] == 100000


class TestDependencyProfile:
    """Tests for DependencyProfile dataclass."""

    def test_create_empty_profile(self):
        """Should create empty dependency profile."""
        profile = DependencyProfile()

        assert profile.module_count == 0
        assert profile.circular_dependencies == 0
        assert profile.coupling_score == 0.0

    def test_create_full_profile(self):
        """Should create full dependency profile."""
        profile = DependencyProfile(
            module_count=50,
            edge_count=120,
            circular_dependencies=3,
            entry_points=["main.py", "app.py"],
            hub_modules=["utils.py", "helpers.py"],
            external_dependencies=25,
            internal_dependencies=95,
            instability_avg=0.45,
            coupling_score=0.6,
        )

        assert profile.module_count == 50
        assert profile.edge_count == 120
        assert profile.circular_dependencies == 3
        assert len(profile.entry_points) == 2
        assert profile.coupling_score == 0.6

    def test_to_dict_limits_lists(self):
        """Should limit list sizes in to_dict."""
        profile = DependencyProfile(
            entry_points=[f"entry_{i}.py" for i in range(20)],
            hub_modules=[f"hub_{i}.py" for i in range(20)],
        )

        result = profile.to_dict()

        assert len(result["entry_points"]) == 10
        assert len(result["hub_modules"]) == 10


class TestComplexityProfile:
    """Tests for ComplexityProfile dataclass."""

    def test_create_empty_profile(self):
        """Should create empty complexity profile."""
        profile = ComplexityProfile()

        assert profile.avg_cyclomatic == 0.0
        assert profile.complexity_rating == "unknown"

    def test_create_full_profile(self):
        """Should create full complexity profile."""
        profile = ComplexityProfile(
            avg_cyclomatic=8.5,
            max_cyclomatic=42,
            total_functions=350,
            high_complexity_count=15,
            complexity_rating="medium",
        )

        assert profile.avg_cyclomatic == 8.5
        assert profile.max_cyclomatic == 42
        assert profile.total_functions == 350
        assert profile.complexity_rating == "medium"


class TestAggregatedAnalysis:
    """Tests for AggregatedAnalysis dataclass."""

    def test_create_analysis(self):
        """Should create aggregated analysis."""
        analysis = AggregatedAnalysis(
            project_id=1,
            repository_path="/opt/projects/myapp",
        )

        assert analysis.project_id == 1
        assert analysis.repository_path == "/opt/projects/myapp"
        assert isinstance(analysis.analysis_timestamp, datetime)

    def test_is_successful_no_errors(self):
        """Should return True when no errors."""
        analysis = AggregatedAnalysis(
            project_id=1,
            repository_path="/test",
            errors=[],
        )

        assert analysis.is_successful is True

    def test_is_successful_with_errors(self):
        """Should return False when errors exist."""
        analysis = AggregatedAnalysis(
            project_id=1,
            repository_path="/test",
            errors=["Stack detection failed"],
        )

        assert analysis.is_successful is False

    def test_analysis_score_basic(self):
        """Should calculate basic analysis score."""
        analysis = AggregatedAnalysis(
            project_id=1,
            repository_path="/test",
            technology=TechnologyProfile(primary_stack="python"),
        )

        score = analysis.analysis_score

        assert score >= 15  # Primary stack detected = 15 points

    def test_analysis_score_full(self):
        """Should calculate full analysis score."""
        analysis = AggregatedAnalysis(
            project_id=1,
            repository_path="/test",
            technology=TechnologyProfile(
                primary_stack="python",
                database_type="postgresql",
            ),
            dependencies=DependencyProfile(
                module_count=10,
                circular_dependencies=0,
            ),
            documentation=DocumentationProfile(
                documented_ratio=0.8,
                readme_exists=True,
            ),
            complexity=ComplexityProfile(
                complexity_rating="low",
            ),
        )

        score = analysis.analysis_score

        # Primary stack (15) + DB (5) + modules (15) + no circular (10) +
        # doc ratio (16) + readme (5) + low complexity (30) = 96
        assert score >= 80

    def test_to_dict(self):
        """Should convert to dictionary."""
        analysis = AggregatedAnalysis(
            project_id=1,
            repository_path="/test",
            duration_ms=1500,
        )

        result = analysis.to_dict()

        assert result["project_id"] == 1
        assert result["repository_path"] == "/test"
        assert result["duration_ms"] == 1500
        assert "analysis_score" in result
        assert "technology" in result
        assert "dependencies" in result

    def test_to_llm_context(self):
        """Should generate LLM context string."""
        analysis = AggregatedAnalysis(
            project_id=1,
            repository_path="/opt/myproject",
            technology=TechnologyProfile(
                primary_stack="python",
                secondary_stacks=["javascript"],
                database_type="postgresql",
                total_files=100,
                total_loc=15000,
            ),
            dependencies=DependencyProfile(
                module_count=30,
                internal_dependencies=50,
                external_dependencies=20,
                circular_dependencies=2,
                coupling_score=0.5,
            ),
            complexity=ComplexityProfile(
                complexity_rating="medium",
                avg_cyclomatic=7.5,
                total_functions=200,
            ),
            documentation=DocumentationProfile(
                documented_ratio=0.6,
                readme_exists=True,
                diagram_count=3,
            ),
        )

        context = analysis.to_llm_context()

        assert "## Code Analysis Summary" in context
        assert "python" in context.lower()
        assert "postgresql" in context
        assert "100" in context  # files
        assert "15,000" in context  # loc
        assert "medium" in context.lower()


class TestCodeAnalysisAggregatorService:
    """Tests for CodeAnalysisAggregatorService."""

    def test_init_service(self):
        """Should initialize service with mock db."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        assert service.db == mock_db
        # stack_service is created on-demand per analysis
        assert service.dependency_service is not None
        assert service.codewiki_service is not None

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_path(self):
        """Should return error for non-existent path."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        result = await service.analyze(
            project_id=1,
            repository_path="/nonexistent/path/12345",
        )

        assert not result.is_successful
        assert any("not found" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_analyze_with_temp_repo(self):
        """Should analyze a temporary directory."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        # Create temp directory with a Python file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file
            py_file = Path(tmpdir) / "main.py"
            py_file.write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")

            # Create a README
            readme = Path(tmpdir) / "README.md"
            readme.write_text("# Test Project\n\nA test project for code analysis.")

            # Mock CodeWiki since it needs DB
            with patch.object(service.codewiki_service, 'create_analysis') as mock_cw:
                mock_analysis = Mock()
                mock_analysis.id = 1
                mock_cw.return_value = mock_analysis

                result = await service.analyze(
                    project_id=1,
                    repository_path=tmpdir,
                    include_codewiki=True,
                )

        assert result.project_id == 1
        assert result.duration_ms > 0

    def test_factory_function(self):
        """Should create service via factory function."""
        mock_db = Mock()
        service = get_aggregator_service(mock_db)

        assert isinstance(service, CodeAnalysisAggregatorService)


class TestComplexityRating:
    """Tests for complexity rating calculation."""

    def test_calculate_coupling_score_empty(self):
        """Should return 0 for empty metrics."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        # Create empty metrics mock
        metrics = Mock()
        metrics.total_modules = 0
        metrics.afferent_coupling_avg = 0
        metrics.efferent_coupling_avg = 0
        metrics.circular_dependencies = 0
        metrics.hub_modules = []

        score = service._calculate_coupling_score(metrics)

        assert score == 0.0

    def test_calculate_coupling_score_high(self):
        """Should return high score for highly coupled code."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        metrics = Mock()
        metrics.total_modules = 10
        metrics.afferent_coupling_avg = 8.0
        metrics.efferent_coupling_avg = 8.0
        metrics.circular_dependencies = 5
        metrics.hub_modules = ["a", "b", "c", "d", "e"]  # 50% are hubs

        score = service._calculate_coupling_score(metrics)

        assert score >= 0.5  # High coupling

    def test_build_complexity_profile_low(self):
        """Should build low complexity profile."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        metrics = Mock()
        metrics.avg_cyclomatic = 3.0
        metrics.max_cyclomatic = 8
        metrics.total_functions = 100
        metrics.high_complexity_count = 2

        profile = service._build_complexity_profile(metrics)

        assert profile.complexity_rating == "low"

    def test_build_complexity_profile_high(self):
        """Should build high complexity profile."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        metrics = Mock()
        metrics.avg_cyclomatic = 15.0
        metrics.max_cyclomatic = 50
        metrics.total_functions = 100
        metrics.high_complexity_count = 25

        profile = service._build_complexity_profile(metrics)

        assert profile.complexity_rating == "high"

    def test_build_complexity_profile_critical(self):
        """Should build critical complexity profile."""
        mock_db = Mock()
        service = CodeAnalysisAggregatorService(mock_db)

        metrics = Mock()
        metrics.avg_cyclomatic = 25.0
        metrics.max_cyclomatic = 100
        metrics.total_functions = 50
        metrics.high_complexity_count = 40

        profile = service._build_complexity_profile(metrics)

        assert profile.complexity_rating == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
