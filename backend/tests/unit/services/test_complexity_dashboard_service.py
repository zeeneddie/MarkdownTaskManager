"""
Unit tests for ComplexityDashboardService - A5 (Fase 24).

Tests cover:
- File complexity analysis
- Module aggregation
- Health status calculation
- Hotspot detection
- Trend tracking
- Recommendation generation

Author: Claude Code (Week 158)
Date: 2026-01-19
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from app.services.complexity_dashboard_service import (
    ModuleHealthStatus,
    TrendDirection,
    FileComplexity,
    ModuleComplexity,
    ComplexitySnapshot,
    ComplexityTrend,
    ComplexityDashboardResult,
    ComplexityDashboardService,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh ComplexityDashboardService instance."""
    return ComplexityDashboardService()


@pytest.fixture
def file_complexity():
    """Create a sample FileComplexity."""
    return FileComplexity(
        file_path="src/utils.py",
        cyclomatic_complexity=15,
        cognitive_complexity=12,
        lines_of_code=200,
        function_count=10,
        max_function_complexity=8,
        high_complexity_functions=["complex_function"]
    )


@pytest.fixture
def module_complexity():
    """Create a sample ModuleComplexity."""
    return ModuleComplexity(
        module_path="src/utils",
        module_name="utils",
        file_count=5,
        total_lines=1000,
        total_cyclomatic=50,
        total_cognitive=40,
        total_functions=30,
        max_file_complexity=20,
        max_function_complexity=15,
        files=[],
        hotspot_files=["complex_file.py"]
    )


@pytest.fixture
def temp_project():
    """Create a temporary project directory with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()
        utils_dir = src_dir / "utils"
        utils_dir.mkdir()

        # Create Python files
        (src_dir / "main.py").write_text("""
def main():
    x = 1
    if x > 0:
        print("positive")
    else:
        print("negative")
""")

        (utils_dir / "helpers.py").write_text("""
def helper_one():
    return 1

def helper_two():
    return 2
""")

        yield tmpdir


# ==================== FileComplexity Tests ====================

class TestFileComplexity:
    """Test FileComplexity data class."""

    def test_create_file_complexity(self, file_complexity):
        """Test FileComplexity creation."""
        assert file_complexity.file_path == "src/utils.py"
        assert file_complexity.cyclomatic_complexity == 15
        assert file_complexity.lines_of_code == 200

    def test_to_dict(self, file_complexity):
        """Test serialization to dictionary."""
        data = file_complexity.to_dict()

        assert data["file_path"] == "src/utils.py"
        assert data["cyclomatic_complexity"] == 15
        assert data["lines_of_code"] == 200
        assert "high_complexity_functions" in data


# ==================== ModuleComplexity Tests ====================

class TestModuleComplexity:
    """Test ModuleComplexity data class."""

    def test_create_module_complexity(self, module_complexity):
        """Test ModuleComplexity creation."""
        assert module_complexity.module_name == "utils"
        assert module_complexity.file_count == 5

    def test_avg_cyclomatic(self, module_complexity):
        """Test average cyclomatic complexity calculation."""
        # 50 total / 5 files = 10
        assert module_complexity.avg_cyclomatic == 10.0

    def test_avg_cyclomatic_empty(self):
        """Test avg_cyclomatic with no files."""
        module = ModuleComplexity(
            module_path="empty",
            module_name="empty",
            file_count=0,
            total_lines=0,
            total_cyclomatic=0,
            total_cognitive=0,
            total_functions=0,
            max_file_complexity=0,
            max_function_complexity=0
        )
        # Should not divide by zero
        assert module.avg_cyclomatic == 0

    def test_avg_cognitive(self, module_complexity):
        """Test average cognitive complexity calculation."""
        # 40 total / 5 files = 8
        assert module_complexity.avg_cognitive == 8.0

    def test_health_status_healthy(self):
        """Test HEALTHY status for avg < 10."""
        module = ModuleComplexity(
            module_path="",
            module_name="",
            file_count=5,
            total_lines=100,
            total_cyclomatic=25,  # avg = 5
            total_cognitive=20,
            total_functions=10,
            max_file_complexity=10,
            max_function_complexity=5
        )
        assert module.health_status == ModuleHealthStatus.HEALTHY

    def test_health_status_warning(self, module_complexity):
        """Test WARNING status for avg 10-20."""
        # module_complexity has avg = 10
        assert module_complexity.health_status == ModuleHealthStatus.WARNING

    def test_health_status_at_risk(self):
        """Test AT_RISK status for avg 20-30."""
        module = ModuleComplexity(
            module_path="",
            module_name="",
            file_count=5,
            total_lines=100,
            total_cyclomatic=125,  # avg = 25
            total_cognitive=100,
            total_functions=10,
            max_file_complexity=40,
            max_function_complexity=20
        )
        assert module.health_status == ModuleHealthStatus.AT_RISK

    def test_health_status_critical(self):
        """Test CRITICAL status for avg > 30."""
        module = ModuleComplexity(
            module_path="",
            module_name="",
            file_count=5,
            total_lines=100,
            total_cyclomatic=200,  # avg = 40
            total_cognitive=150,
            total_functions=10,
            max_file_complexity=60,
            max_function_complexity=30
        )
        assert module.health_status == ModuleHealthStatus.CRITICAL

    def test_complexity_density(self, module_complexity):
        """Test complexity density calculation."""
        # 50 complexity / 1000 lines * 100 = 5
        assert module_complexity.complexity_density == 5.0

    def test_complexity_density_empty(self):
        """Test complexity density with no lines."""
        module = ModuleComplexity(
            module_path="",
            module_name="",
            file_count=0,
            total_lines=0,
            total_cyclomatic=0,
            total_cognitive=0,
            total_functions=0,
            max_file_complexity=0,
            max_function_complexity=0
        )
        assert module.complexity_density == 0

    def test_to_dict(self, module_complexity):
        """Test serialization to dictionary."""
        data = module_complexity.to_dict()

        assert data["module_name"] == "utils"
        assert data["avg_cyclomatic"] == 10.0
        assert data["health_status"] == "warning"
        assert "files" in data


# ==================== ComplexitySnapshot Tests ====================

class TestComplexitySnapshot:
    """Test ComplexitySnapshot data class."""

    def test_create_snapshot(self):
        """Test snapshot creation."""
        now = datetime.now(timezone.utc)
        snapshot = ComplexitySnapshot(
            timestamp=now,
            total_complexity=100,
            avg_complexity=15.5,
            module_count=10,
            file_count=50,
            hotspot_count=5
        )

        assert snapshot.total_complexity == 100
        assert snapshot.avg_complexity == 15.5

    def test_to_dict(self):
        """Test serialization."""
        snapshot = ComplexitySnapshot(
            timestamp=datetime.now(timezone.utc),
            total_complexity=100,
            avg_complexity=15.5,
            module_count=10,
            file_count=50,
            hotspot_count=5
        )
        data = snapshot.to_dict()

        assert "timestamp" in data
        assert data["total_complexity"] == 100


# ==================== ComplexityTrend Tests ====================

class TestComplexityTrend:
    """Test ComplexityTrend data class."""

    def test_create_trend_improving(self):
        """Test improving trend creation."""
        trend = ComplexityTrend(
            direction=TrendDirection.IMPROVING,
            change_percentage=-10.0,
            snapshots=[]
        )
        assert trend.direction == TrendDirection.IMPROVING

    def test_create_trend_degrading(self):
        """Test degrading trend creation."""
        trend = ComplexityTrend(
            direction=TrendDirection.DEGRADING,
            change_percentage=15.0,
            snapshots=[]
        )
        assert trend.direction == TrendDirection.DEGRADING

    def test_to_dict(self):
        """Test serialization."""
        trend = ComplexityTrend(
            direction=TrendDirection.STABLE,
            change_percentage=0.0,
            snapshots=[]
        )
        data = trend.to_dict()

        assert data["direction"] == "stable"
        assert data["change_percentage"] == 0.0


# ==================== ComplexityDashboardResult Tests ====================

class TestComplexityDashboardResult:
    """Test ComplexityDashboardResult data class."""

    def test_create_result(self, module_complexity):
        """Test result creation with summary calculation."""
        result = ComplexityDashboardResult(
            scan_timestamp=datetime.now(timezone.utc),
            project_path="/project",
            modules=[module_complexity],
            summary={},
            hotspots=[],
            distribution={},
            recommendations=[]
        )

        # Summary should be calculated in __post_init__
        assert result.summary["total_modules"] == 1
        assert result.summary["total_files"] == 5

    def test_summary_calculation(self):
        """Test summary statistics calculation."""
        module1 = ModuleComplexity(
            module_path="m1",
            module_name="m1",
            file_count=3,
            total_lines=300,
            total_cyclomatic=30,
            total_cognitive=25,
            total_functions=15,
            max_file_complexity=15,
            max_function_complexity=10
        )
        module2 = ModuleComplexity(
            module_path="m2",
            module_name="m2",
            file_count=2,
            total_lines=200,
            total_cyclomatic=20,
            total_cognitive=18,
            total_functions=10,
            max_file_complexity=12,
            max_function_complexity=8
        )

        result = ComplexityDashboardResult(
            scan_timestamp=datetime.now(timezone.utc),
            project_path="/project",
            modules=[module1, module2],
            summary={},
            hotspots=[{"file": "test.py"}],
            distribution={"1-5": 3, "6-10": 2},
            recommendations=["Refactor complex module"]
        )

        assert result.summary["total_modules"] == 2
        assert result.summary["total_files"] == 5
        assert result.summary["total_lines"] == 500
        assert result.summary["total_complexity"] == 50
        assert result.summary["hotspot_count"] == 1

    def test_to_dict(self, module_complexity):
        """Test serialization."""
        result = ComplexityDashboardResult(
            scan_timestamp=datetime.now(timezone.utc),
            project_path="/project",
            modules=[module_complexity],
            summary={},
            hotspots=[],
            distribution={},
            recommendations=[]
        )
        data = result.to_dict()

        assert "scan_timestamp" in data
        assert "project_path" in data
        assert "modules" in data
        assert "summary" in data


# ==================== ComplexityDashboardService Tests ====================

class TestComplexityDashboardService:
    """Test ComplexityDashboardService."""

    def test_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert service._history == []

    def test_initialization_with_path(self):
        """Test service initialization with project path."""
        service = ComplexityDashboardService(project_path="/some/path")
        assert service.project_path == "/some/path"

    def test_get_extensions_all_languages(self, service):
        """Test getting extensions for all languages."""
        extensions = service._get_extensions(None)

        assert ".py" in extensions
        assert ".js" in extensions
        assert ".ts" in extensions

    def test_get_extensions_specific_language(self, service):
        """Test getting extensions for specific language."""
        extensions = service._get_extensions(["python"])

        assert ".py" in extensions
        assert ".js" not in extensions

    def test_get_extensions_multiple_languages(self, service):
        """Test getting extensions for multiple languages."""
        extensions = service._get_extensions(["python", "javascript"])

        assert ".py" in extensions
        assert ".js" in extensions
        assert ".jsx" in extensions

    def test_analyze_project_nonexistent_path(self, service):
        """Test analyzing nonexistent path raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            service.analyze_project("/nonexistent/path")

    def test_analyze_project_basic(self, service, temp_project):
        """Test basic project analysis."""
        result = service.analyze_project(temp_project)

        assert result is not None
        assert result.project_path == temp_project
        assert isinstance(result.modules, list)

    def test_analyze_project_filters_excluded_dirs(self, service, temp_project):
        """Test that excluded directories are skipped."""
        # Create node_modules directory
        node_modules = Path(temp_project) / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.js").write_text("// node module")

        result = service.analyze_project(temp_project)

        # Should not include node_modules files
        all_files = []
        for module in result.modules:
            all_files.extend([f.file_path for f in module.files])

        assert not any("node_modules" in f for f in all_files)

    def test_analyze_project_filters_by_language(self, service, temp_project):
        """Test filtering by language."""
        # Create JS file
        (Path(temp_project) / "src" / "app.js").write_text("console.log('test');")

        result = service.analyze_project(temp_project, languages=["python"])

        # Should only have Python files
        all_files = []
        for module in result.modules:
            all_files.extend([f.file_path for f in module.files])

        assert all(f.endswith(".py") for f in all_files if all_files)

    def test_calculate_trend_improving(self, service):
        """Test trend calculation for improving complexity."""
        now = datetime.now(timezone.utc)
        snapshots = [
            ComplexitySnapshot(now - timedelta(days=7), 100, 20.0, 5, 10, 3),
            ComplexitySnapshot(now - timedelta(days=3), 90, 18.0, 5, 10, 2),
            ComplexitySnapshot(now, 80, 16.0, 5, 10, 1),
        ]

        trend = service._calculate_trend(snapshots)

        assert trend.direction == TrendDirection.IMPROVING
        assert trend.change_percentage < 0

    def test_calculate_trend_degrading(self, service):
        """Test trend calculation for degrading complexity."""
        now = datetime.now(timezone.utc)
        snapshots = [
            ComplexitySnapshot(now - timedelta(days=7), 80, 16.0, 5, 10, 1),
            ComplexitySnapshot(now - timedelta(days=3), 90, 18.0, 5, 10, 2),
            ComplexitySnapshot(now, 100, 20.0, 5, 10, 3),
        ]

        trend = service._calculate_trend(snapshots)

        assert trend.direction == TrendDirection.DEGRADING
        assert trend.change_percentage > 0

    def test_calculate_trend_stable(self, service):
        """Test trend calculation for stable complexity."""
        now = datetime.now(timezone.utc)
        snapshots = [
            ComplexitySnapshot(now - timedelta(days=7), 100, 20.0, 5, 10, 2),
            ComplexitySnapshot(now - timedelta(days=3), 101, 20.2, 5, 10, 2),
            ComplexitySnapshot(now, 100, 20.0, 5, 10, 2),
        ]

        trend = service._calculate_trend(snapshots)

        assert trend.direction == TrendDirection.STABLE

    def test_calculate_trend_insufficient_data(self, service):
        """Test trend calculation with insufficient data."""
        now = datetime.now(timezone.utc)
        snapshots = [
            ComplexitySnapshot(now, 100, 20.0, 5, 10, 2),
        ]

        trend = service._calculate_trend(snapshots)

        # With single snapshot, should be stable
        assert trend.direction == TrendDirection.STABLE

    def test_identify_hotspots(self, service):
        """Test hotspot identification."""
        files = [
            FileComplexity("low.py", 5, 4, 50, 3, 3),
            FileComplexity("medium.py", 15, 12, 100, 5, 8),
            FileComplexity("high.py", 30, 25, 150, 8, 20),  # Hotspot
            FileComplexity("critical.py", 50, 45, 200, 10, 30),  # Hotspot
        ]

        hotspots = service._identify_hotspots(files)

        assert len(hotspots) == 2
        hotspot_files = [h["file_path"] for h in hotspots]
        assert "high.py" in hotspot_files
        assert "critical.py" in hotspot_files

    def test_generate_recommendations(self, service):
        """Test recommendation generation."""
        modules = [
            ModuleComplexity("critical", "critical", 5, 500, 200, 150, 20, 50, 35),
            ModuleComplexity("healthy", "healthy", 3, 300, 15, 12, 10, 8, 5),
        ]

        recommendations = service._generate_recommendations(
            modules,
            hotspot_count=3,
            avg_complexity=25.0
        )

        assert len(recommendations) > 0
        assert any("critical" in r.lower() or "refactor" in r.lower() for r in recommendations)

    def test_group_by_module(self, service):
        """Test file grouping by module."""
        files = {
            "src/app/main.py": FileComplexity("src/app/main.py", 10, 8, 100, 5, 6),
            "src/app/utils.py": FileComplexity("src/app/utils.py", 8, 6, 80, 4, 5),
            "src/core/engine.py": FileComplexity("src/core/engine.py", 20, 18, 200, 8, 12),
        }

        modules = service._group_by_module(files, module_depth=2)

        assert len(modules) == 2  # src/app and src/core
        module_names = [m.module_name for m in modules]
        assert "app" in module_names
        assert "core" in module_names

    def test_calculate_distribution(self, service):
        """Test complexity distribution calculation."""
        files = [
            FileComplexity("a.py", 3, 2, 30, 2, 2),   # 1-5
            FileComplexity("b.py", 7, 5, 50, 3, 4),   # 6-10
            FileComplexity("c.py", 12, 10, 80, 4, 8), # 11-15
            FileComplexity("d.py", 25, 20, 150, 7, 15), # 21-30
            FileComplexity("e.py", 55, 45, 300, 12, 30), # 51+
        ]

        distribution = service._calculate_distribution(files)

        assert "1-5" in distribution
        assert "6-10" in distribution
        assert "51+" in distribution

    def test_add_snapshot(self, service):
        """Test adding snapshots to history."""
        snapshot = ComplexitySnapshot(
            datetime.now(timezone.utc),
            100, 20.0, 5, 10, 2
        )

        service.add_snapshot(snapshot)

        assert len(service._history) == 1
        assert service._history[0] == snapshot

    def test_get_history(self, service):
        """Test retrieving history."""
        now = datetime.now(timezone.utc)
        for i in range(5):
            service.add_snapshot(ComplexitySnapshot(
                now - timedelta(days=i),
                100 + i, 20.0 + i, 5, 10, 2
            ))

        history = service.get_history(limit=3)

        assert len(history) == 3


# ==================== Language Extensions Tests ====================

class TestLanguageExtensions:
    """Test language extension mappings."""

    def test_python_extensions(self, service):
        """Test Python extensions."""
        assert ".py" in service.LANGUAGE_EXTENSIONS["python"]

    def test_javascript_extensions(self, service):
        """Test JavaScript extensions."""
        exts = service.LANGUAGE_EXTENSIONS["javascript"]
        assert ".js" in exts
        assert ".jsx" in exts
        assert ".mjs" in exts

    def test_typescript_extensions(self, service):
        """Test TypeScript extensions."""
        exts = service.LANGUAGE_EXTENSIONS["typescript"]
        assert ".ts" in exts
        assert ".tsx" in exts

    def test_csharp_extensions(self, service):
        """Test C# extensions."""
        assert ".cs" in service.LANGUAGE_EXTENSIONS["csharp"]


# ==================== Excluded Directories Tests ====================

class TestExcludedDirectories:
    """Test excluded directory filtering."""

    def test_common_excludes(self, service):
        """Test common directories are excluded."""
        excludes = service.EXCLUDED_DIRS

        assert "node_modules" in excludes
        assert ".git" in excludes
        assert "__pycache__" in excludes
        assert "venv" in excludes
        assert "build" in excludes


# ==================== Enums Tests ====================

class TestEnums:
    """Test enum values."""

    def test_module_health_status_values(self):
        """Test ModuleHealthStatus enum values."""
        assert ModuleHealthStatus.HEALTHY.value == "healthy"
        assert ModuleHealthStatus.WARNING.value == "warning"
        assert ModuleHealthStatus.AT_RISK.value == "at_risk"
        assert ModuleHealthStatus.CRITICAL.value == "critical"

    def test_trend_direction_values(self):
        """Test TrendDirection enum values."""
        assert TrendDirection.IMPROVING.value == "improving"
        assert TrendDirection.STABLE.value == "stable"
        assert TrendDirection.DEGRADING.value == "degrading"
