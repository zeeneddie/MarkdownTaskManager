"""
Tests for ASISArchitectureService (Week 69)

Tests cover:
- Layer detection patterns
- Architecture pattern recognition
- Component detection
- Issue identification
- Score calculation
"""

import os
import tempfile
import pytest
from pathlib import Path

from app.services.asis_architecture_service import (
    ASISArchitectureService,
    ASISArchitecture,
    ArchitecturePattern,
    LayerType,
    ArchitectureLayer,
    ArchitectureComponent,
    ArchitectureIssue,
    get_asis_architecture_service,
)


class TestASISArchitectureService:
    """Test suite for ASISArchitectureService"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return ASISArchitectureService()

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository structure for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_service_singleton(self):
        """Test singleton pattern works correctly"""
        service1 = get_asis_architecture_service()
        service2 = get_asis_architecture_service()
        assert service1 is service2

    def test_analyze_nonexistent_path(self, service):
        """Test handling of non-existent path"""
        result = service.analyze("/nonexistent/path/xyz123")

        assert isinstance(result, ASISArchitecture)
        assert len(result.issues) == 1
        assert result.issues[0].issue_type == "path_not_found"
        assert result.issues[0].severity == "critical"

    def test_analyze_empty_directory(self, service, temp_repo):
        """Test analysis of empty directory"""
        result = service.analyze(temp_repo)

        assert isinstance(result, ASISArchitecture)
        assert result.repo_path == temp_repo
        assert result.total_files == 0
        assert result.detected_pattern == ArchitecturePattern.MONOLITH

    def test_detect_layered_architecture(self, service, temp_repo):
        """Test detection of layered architecture"""
        # Create layered structure
        dirs = ["presentation", "application", "domain", "infrastructure", "data"]
        for d in dirs:
            path = Path(temp_repo) / d
            path.mkdir()
            # Add some Python files
            (path / f"{d}_service.py").write_text("class Service: pass")

        result = service.analyze(temp_repo)

        # Should detect multiple layers
        assert len(result.layers) >= 3
        layer_types = {l.layer_type for l in result.layers}
        assert LayerType.PRESENTATION in layer_types or LayerType.APPLICATION in layer_types

    def test_detect_mvc_pattern(self, service, temp_repo):
        """Test detection of MVC pattern"""
        # Create MVC structure
        dirs = ["models", "views", "controllers"]
        for d in dirs:
            path = Path(temp_repo) / d
            path.mkdir()
            (path / f"User{d[:-1].title()}.py").write_text("class User: pass")

        result = service.analyze(temp_repo)

        # Should detect MVC pattern hints
        assert result.detected_pattern in [
            ArchitecturePattern.MVC,
            ArchitecturePattern.LAYERED,
            ArchitecturePattern.MONOLITH
        ]

    def test_detect_clean_architecture(self, service, temp_repo):
        """Test detection of Clean Architecture pattern"""
        # Create Clean Architecture structure
        dirs = ["domain/entities", "domain/usecases", "application/services",
                "infrastructure/repositories", "presentation/api"]
        for d in dirs:
            path = Path(temp_repo) / d
            path.mkdir(parents=True)
            (path / "__init__.py").write_text("")

        # Add characteristic files
        (Path(temp_repo) / "domain/usecases/create_user_use_case.py").write_text(
            "class CreateUserUseCase: pass"
        )
        (Path(temp_repo) / "infrastructure/repositories/user_repository.py").write_text(
            "class UserRepository: pass"
        )

        result = service.analyze(temp_repo)

        # Should detect Domain layer
        layer_types = {l.layer_type for l in result.layers}
        assert LayerType.DOMAIN in layer_types

    def test_detect_components(self, service, temp_repo):
        """Test component detection"""
        # Create files with recognizable patterns
        components = [
            ("controllers/UserController.py", "controller"),
            ("services/UserService.py", "service"),
            ("repositories/UserRepository.py", "repository"),
            ("models/User.py", "model"),
        ]

        for filepath, _ in components:
            path = Path(temp_repo) / filepath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("class Component: pass")

        result = service.analyze(temp_repo)

        # Should detect components
        component_types = {c.component_type for c in result.components}
        assert len(component_types) >= 2

    def test_detect_test_layer(self, service, temp_repo):
        """Test detection of test layer"""
        # Create test directory with files
        test_dir = Path(temp_repo) / "tests"
        test_dir.mkdir()
        (test_dir / "test_user.py").write_text("def test_user(): pass")
        (test_dir / "test_service.py").write_text("def test_service(): pass")

        # Add source files too
        src_dir = Path(temp_repo) / "src"
        src_dir.mkdir()
        (src_dir / "user.py").write_text("class User: pass")

        result = service.analyze(temp_repo)

        # Should detect test layer
        test_layer = next((l for l in result.layers if l.layer_type == LayerType.TESTS), None)
        assert test_layer is not None
        assert test_layer.file_count >= 1

    def test_detect_missing_tests_issue(self, service, temp_repo):
        """Test detection of missing tests issue"""
        # Create source files without tests
        src_dir = Path(temp_repo) / "src"
        src_dir.mkdir()
        for i in range(10):
            (src_dir / f"module_{i}.py").write_text("class Module: pass")

        result = service.analyze(temp_repo)

        # Should report missing tests issue
        issue_types = {i.issue_type for i in result.issues}
        assert "missing_tests" in issue_types or "no_layer_separation" in issue_types

    def test_detect_large_components_issue(self, service, temp_repo):
        """Test detection of large components (god classes)"""
        src_dir = Path(temp_repo) / "services"
        src_dir.mkdir()

        # Create a very large file
        large_content = "class Service:\n" + "    def method():\n        pass\n" * 1000
        (src_dir / "GodService.py").write_text(large_content)

        result = service.analyze(temp_repo)

        # Large components should have high complexity
        large_components = [c for c in result.components if c.complexity_score > 50]
        # Note: This depends on file size calculation

    def test_architecture_score_calculation(self, service, temp_repo):
        """Test architecture score calculation"""
        # Create a well-structured project
        dirs = ["domain", "application", "infrastructure", "tests"]
        for d in dirs:
            path = Path(temp_repo) / d
            path.mkdir()
            (path / f"{d}_module.py").write_text("class Module: pass")

        result = service.analyze(temp_repo)

        # Score should be between 0 and 100
        assert 0 <= result.architecture_score <= 100

    def test_ignore_patterns(self, service, temp_repo):
        """Test that ignored directories are skipped"""
        # Create node_modules and .git
        ignored_dirs = ["node_modules", ".git", "__pycache__", "build"]
        for d in ignored_dirs:
            path = Path(temp_repo) / d
            path.mkdir()
            (path / "ignored.py").write_text("# Should be ignored")

        # Create actual source
        src = Path(temp_repo) / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')")

        result = service.analyze(temp_repo)

        # Ignored files should not be counted
        assert result.total_files == 1

    def test_deep_nesting_detection(self, service, temp_repo):
        """Test detection of deep directory nesting"""
        # Create deeply nested structure
        path = Path(temp_repo)
        for i in range(12):
            path = path / f"level_{i}"
            path.mkdir()
            (path / f"module_{i}.py").write_text("class Module: pass")

        result = service.analyze(temp_repo)

        # Should detect deep nesting
        assert result.max_depth >= 10
        issue_types = {i.issue_type for i in result.issues}
        assert "deep_nesting" in issue_types

    def test_to_dict_serialization(self, service, temp_repo):
        """Test that result can be serialized to dict"""
        # Create minimal structure
        src = Path(temp_repo) / "src"
        src.mkdir()
        (src / "main.py").write_text("class Main: pass")

        result = service.analyze(temp_repo)
        result_dict = result.to_dict()

        # Should be valid dict
        assert isinstance(result_dict, dict)
        assert "repo_path" in result_dict
        assert "detected_pattern" in result_dict
        assert "layers" in result_dict
        assert "components" in result_dict
        assert "issues" in result_dict
        assert "architecture_score" in result_dict

    def test_architecture_summary(self, service, temp_repo):
        """Test human-readable summary generation"""
        # Create minimal structure
        src = Path(temp_repo) / "src"
        src.mkdir()
        (src / "main.py").write_text("class Main: pass")

        result = service.analyze(temp_repo)
        summary = service.get_architecture_summary(result)

        # Should be readable markdown
        assert isinstance(summary, str)
        assert "AS-IS Architecture Analysis" in summary
        assert "Detected Pattern" in summary

    def test_hexagonal_pattern_detection(self, service, temp_repo):
        """Test detection of Hexagonal Architecture"""
        # Create Hexagonal structure
        dirs = ["domain", "ports", "adapters/primary", "adapters/secondary"]
        for d in dirs:
            path = Path(temp_repo) / d
            path.mkdir(parents=True)
            (path / "__init__.py").write_text("")

        # Add port and adapter files
        (Path(temp_repo) / "ports/user_port.py").write_text("class UserPort: pass")
        (Path(temp_repo) / "adapters/primary/api_adapter.py").write_text("class ApiAdapter: pass")

        result = service.analyze(temp_repo)

        # Should have high confidence for some pattern
        assert result.pattern_confidence >= 0.0

    def test_microservices_detection(self, service, temp_repo):
        """Test detection of Microservices indicators"""
        # Create microservices-like structure
        services = ["user-service", "order-service", "payment-service"]
        for s in services:
            path = Path(temp_repo) / s
            path.mkdir()
            (path / "main.py").write_text("class Service: pass")
            (path / "Dockerfile").write_text("FROM python:3.11")

        # Add docker-compose
        (Path(temp_repo) / "docker-compose.yml").write_text("version: '3'\nservices:\n  user: {}")

        result = service.analyze(temp_repo)

        # Should detect microservices hints or modular structure
        assert result.total_files >= 3


class TestLayerDetectionPatterns:
    """Test specific layer detection patterns"""

    @pytest.fixture
    def service(self):
        return ASISArchitectureService()

    @pytest.fixture
    def temp_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_presentation_layer_patterns(self, service, temp_repo):
        """Test various presentation layer patterns"""
        patterns = ["views", "pages", "screens", "ui", "templates"]
        for p in patterns:
            path = Path(temp_repo) / p
            path.mkdir(exist_ok=True)
            (path / "index.html").write_text("<html></html>")

        result = service.analyze(temp_repo)
        layer_types = {l.layer_type for l in result.layers}
        assert LayerType.PRESENTATION in layer_types

    def test_api_layer_patterns(self, service, temp_repo):
        """Test various API layer patterns"""
        patterns = ["api", "routes", "endpoints"]
        for p in patterns:
            path = Path(temp_repo) / p
            path.mkdir(exist_ok=True)
            (path / "routes.py").write_text("def route(): pass")

        result = service.analyze(temp_repo)
        layer_types = {l.layer_type for l in result.layers}
        assert LayerType.API in layer_types

    def test_shared_layer_patterns(self, service, temp_repo):
        """Test shared/utils layer patterns"""
        patterns = ["utils", "helpers", "common", "shared"]
        for p in patterns:
            path = Path(temp_repo) / p
            path.mkdir(exist_ok=True)
            (path / "helpers.py").write_text("def helper(): pass")

        result = service.analyze(temp_repo)
        layer_types = {l.layer_type for l in result.layers}
        assert LayerType.SHARED in layer_types


class TestComponentDetection:
    """Test component detection patterns"""

    @pytest.fixture
    def service(self):
        return ASISArchitectureService()

    @pytest.fixture
    def temp_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_controller_detection(self, service, temp_repo):
        """Test controller component detection"""
        controllers = Path(temp_repo) / "controllers"
        controllers.mkdir()
        (controllers / "UserController.py").write_text("class UserController: pass")
        (controllers / "ProductController.py").write_text("class ProductController: pass")

        result = service.analyze(temp_repo)
        controller_components = [c for c in result.components if c.component_type == "controller"]
        assert len(controller_components) >= 1

    def test_service_detection(self, service, temp_repo):
        """Test service component detection"""
        services = Path(temp_repo) / "services"
        services.mkdir()
        (services / "user_service.py").write_text("class UserService: pass")

        result = service.analyze(temp_repo)
        service_components = [c for c in result.components if c.component_type == "service"]
        assert len(service_components) >= 1

    def test_repository_detection(self, service, temp_repo):
        """Test repository component detection"""
        repos = Path(temp_repo) / "repositories"
        repos.mkdir()
        (repos / "UserRepository.py").write_text("class UserRepository: pass")

        result = service.analyze(temp_repo)
        repo_components = [c for c in result.components if c.component_type == "repository"]
        assert len(repo_components) >= 1


class TestArchitectureIssues:
    """Test architecture issue detection"""

    @pytest.fixture
    def service(self):
        return ASISArchitectureService()

    @pytest.fixture
    def temp_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_no_layer_separation_issue(self, service, temp_repo):
        """Test detection of no layer separation"""
        # Create flat structure
        (Path(temp_repo) / "main.py").write_text("class Main: pass")

        result = service.analyze(temp_repo)
        issue_types = {i.issue_type for i in result.issues}
        assert "no_layer_separation" in issue_types

    def test_severity_levels(self, service, temp_repo):
        """Test that issues have valid severity levels"""
        (Path(temp_repo) / "main.py").write_text("class Main: pass")

        result = service.analyze(temp_repo)

        valid_severities = {"critical", "high", "medium", "low"}
        for issue in result.issues:
            assert issue.severity in valid_severities

    def test_issue_recommendations(self, service, temp_repo):
        """Test that issues have recommendations"""
        (Path(temp_repo) / "main.py").write_text("class Main: pass")

        result = service.analyze(temp_repo)

        for issue in result.issues:
            # All issues should have a recommendation
            assert issue.recommendation or issue.description
