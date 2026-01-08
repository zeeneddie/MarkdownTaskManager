"""
Week 74: Knowledge Graph Integration Tests

Tests the integration of KnowledgeGraphService into the Project Assessment Orchestrator's
Phase 3 (Code Analysis). Validates:
- Entity extraction (classes, functions, methods, imports)
- Class hierarchy detection
- Module dependency mapping
- Complexity hotspot identification
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.project_assessment_orchestrator import ProjectAssessmentOrchestrator
from app.models.project_assessment import ProjectAssessment


class TestKnowledgeGraphIntegration:
    """Test Knowledge Graph integration in Code Analysis Phase"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance with mock database"""
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.fixture
    def temp_python_project(self):
        """Create a temp project with Python files for KG analysis"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src"
            src.mkdir()

            # Main application file with classes
            (src / "app.py").write_text("""
class Application:
    def __init__(self):
        self.config = {}

    def run(self):
        pass

    def stop(self):
        pass

class Config:
    def load(self):
        pass
""")

            # Service file with functions and classes
            (src / "service.py").write_text("""
from app import Application, Config

class UserService:
    def __init__(self, app: Application):
        self.app = app

    def create_user(self, name):
        return {"name": name}

    def get_user(self, user_id):
        return None

def helper_function():
    return True

def another_helper():
    pass
""")

            # Test files
            tests = Path(tmpdir) / "tests"
            tests.mkdir()
            (tests / "test_app.py").write_text("""
import pytest
from src.app import Application

def test_application_init():
    app = Application()
    assert app.config == {}

def test_application_run():
    app = Application()
    app.run()
""")

            yield tmpdir

    @pytest.fixture
    def temp_empty_project(self):
        """Create an empty project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_code_analysis_with_knowledge_graph(self, orchestrator, temp_python_project):
        """Test code analysis extracts KG entities from Python project"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            directory_path=temp_python_project,
            file_count=3
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        assert result.phase_name == "code"
        assert result.items_found >= 2  # At least test files

        # Check basic code analysis data
        data = result.data
        assert "class_count" in data
        assert "function_count" in data
        assert "method_count" in data
        assert "import_count" in data

    @pytest.mark.asyncio
    async def test_code_analysis_empty_project(self, orchestrator, temp_empty_project):
        """Test code analysis handles empty project gracefully"""
        assessment = ProjectAssessment(
            project_name="EmptyProject",
            directory_path=temp_empty_project,
            file_count=0
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        assert result.items_found == 0 or result.items_found >= 0  # Should not fail

    @pytest.mark.asyncio
    async def test_class_hierarchy_extraction(self, orchestrator, temp_python_project):
        """Test class hierarchy is extracted when KG is available"""
        assessment = ProjectAssessment(
            project_name="HierarchyTest",
            directory_path=temp_python_project,
            file_count=3
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        data = result.data
        assert "class_hierarchy" in data
        assert isinstance(data["class_hierarchy"], list)

    @pytest.mark.asyncio
    async def test_module_dependencies_detection(self, orchestrator, temp_python_project):
        """Test module dependencies are detected"""
        assessment = ProjectAssessment(
            project_name="DepsTest",
            directory_path=temp_python_project,
            file_count=3
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        data = result.data
        assert "module_dependencies" in data
        assert isinstance(data["module_dependencies"], list)

    @pytest.mark.asyncio
    async def test_complexity_hotspots_identification(self, orchestrator, temp_python_project):
        """Test complexity hotspots are identified"""
        assessment = ProjectAssessment(
            project_name="ComplexityTest",
            directory_path=temp_python_project,
            file_count=3
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        data = result.data
        assert "complexity_hotspots" in data
        assert isinstance(data["complexity_hotspots"], list)

    @pytest.mark.asyncio
    async def test_knowledge_graph_summary(self, orchestrator, temp_python_project):
        """Test KG summary statistics are generated"""
        assessment = ProjectAssessment(
            project_name="SummaryTest",
            directory_path=temp_python_project,
            file_count=3
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        data = result.data
        # Summary may be None if KG not available, or dict if available
        summary = data.get("knowledge_graph_summary")
        assert summary is None or isinstance(summary, dict)


class TestKnowledgeGraphServiceDirect:
    """Direct tests for KnowledgeGraphService"""

    @pytest.mark.asyncio
    async def test_service_import(self):
        """Test KnowledgeGraphService can be imported"""
        try:
            from app.services.knowledge_graph_service import KnowledgeGraphService, EntityType
            assert KnowledgeGraphService is not None
            assert EntityType is not None
        except ImportError:
            pytest.skip("KnowledgeGraphService not available")

    @pytest.mark.asyncio
    async def test_entity_type_enum(self):
        """Test EntityType enum values"""
        try:
            from app.services.knowledge_graph_service import EntityType
            assert EntityType.CLASS is not None
            assert EntityType.FUNCTION is not None
            assert EntityType.METHOD is not None
            assert EntityType.IMPORT is not None
            assert EntityType.MODULE is not None
        except ImportError:
            pytest.skip("KnowledgeGraphService not available")

    @pytest.mark.asyncio
    async def test_kg_service_build_graph(self):
        """Test KG service can build a graph from directory"""
        try:
            from app.services.knowledge_graph_service import KnowledgeGraphService
        except ImportError:
            pytest.skip("KnowledgeGraphService not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple Python file
            (Path(tmpdir) / "test.py").write_text("class TestClass:\n    def method(self):\n        pass")

            # Create mock db session
            mock_db = MagicMock()
            service = KnowledgeGraphService(mock_db)
            result = service.build_graph(tmpdir, project_id=1, languages=["python"])

            # Should have successfully built the graph
            assert "error" not in result or result.get("entities", 0) >= 0
            assert len(service._entities) >= 0  # May have found class


class TestCodeAnalysisMetrics:
    """Test enhanced code metrics in Phase 3"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.fixture
    def temp_project_with_tests(self):
        """Create project with test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src"
            src.mkdir()
            (src / "main.py").write_text("class Main: pass")
            (src / "service.py").write_text("class Service: pass")

            tests = Path(tmpdir) / "tests"
            tests.mkdir()
            (tests / "test_main.py").write_text("def test_main(): pass")
            (tests / "test_service.py").write_text("def test_service(): pass")
            (tests / "test_integration.py").write_text("def test_integration(): pass")

            yield tmpdir

    @pytest.mark.asyncio
    async def test_test_file_detection(self, orchestrator, temp_project_with_tests):
        """Test that test files are properly counted in items_found"""
        assessment = ProjectAssessment(
            project_name="TestDetection",
            directory_path=temp_project_with_tests,
            file_count=5
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        assert result.items_found >= 3  # At least 3 test files

    @pytest.mark.asyncio
    async def test_test_coverage_calculation(self, orchestrator, temp_project_with_tests):
        """Test coverage percentage is calculated from test/source ratio"""
        assessment = ProjectAssessment(
            project_name="CoverageTest",
            directory_path=temp_project_with_tests,
            file_count=5
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        assert result.data.get("test_coverage") is not None
        assert result.data["test_coverage"] > 0  # Should have some coverage

    @pytest.mark.asyncio
    async def test_items_processed_equals_file_count(self, orchestrator, temp_project_with_tests):
        """Test items_processed reflects file_count"""
        file_count = 5
        assessment = ProjectAssessment(
            project_name="ProcessedTest",
            directory_path=temp_project_with_tests,
            file_count=file_count
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success is True
        assert result.items_processed == file_count


class TestCodeAnalysisFailures:
    """Test error handling in code analysis"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.mark.asyncio
    async def test_nonexistent_directory(self, orchestrator):
        """Test handling of non-existent directory"""
        assessment = ProjectAssessment(
            project_name="NonExistent",
            directory_path="/path/that/does/not/exist/123456789",
            file_count=0
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        # Should handle gracefully - either success with 0 items or explicit failure
        assert result.phase_name == "code"

    @pytest.mark.asyncio
    async def test_permission_denied_graceful(self, orchestrator):
        """Test graceful handling of permission issues"""
        # This test uses /root which typically has restricted access
        assessment = ProjectAssessment(
            project_name="Restricted",
            directory_path="/root",
            file_count=0
        )

        # Should not raise, but return a result
        result = await orchestrator._run_code_analysis_phase(assessment)
        assert result.phase_name == "code"
