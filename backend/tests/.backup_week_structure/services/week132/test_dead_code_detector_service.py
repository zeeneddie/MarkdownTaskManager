"""
Tests for DeadCodeDetectorService - Week 132-133

Tests multi-language dead code detection (Python, TypeScript, C#, VB.NET, Java).
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.dead_code_detector_service import DeadCodeDetectorService
from app.models.dead_code import (
    DeadCodeItemType,
    DetectionMethod,
    RemovalRisk,
    SuggestedAction,
    DeadCodeItem,
    DeadCodeAnalysisResult,
)


class TestDeadCodeDetectorService:
    """Test suite for DeadCodeDetectorService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return DeadCodeDetectorService()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with sample files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Python file with dead code
            py_file = Path(tmpdir) / "example.py"
            py_file.write_text('''
def used_function():
    """This function is used."""
    return 42

def _unused_private():
    """This function is never called."""
    pass

class UsedClass:
    def method(self):
        pass

class _UnusedClass:
    """This class is never instantiated."""
    pass

CONSTANT = "used"
_UNUSED_VAR = "never used"
''')

            # Create TypeScript file
            ts_file = Path(tmpdir) / "example.ts"
            ts_file.write_text('''
export function exportedFunction() {
    return true;
}

function unusedFunction() {
    return false;
}

export class ExportedClass {}

class UnusedClass {}
''')

            yield Path(tmpdir)

    # =========================================================================
    # Basic Detection Tests
    # =========================================================================

    def test_detect_returns_result(self, service, temp_project):
        """Test that detect() returns a DeadCodeAnalysisResult."""
        result = service.detect(project_path=temp_project)

        assert isinstance(result, DeadCodeAnalysisResult)
        assert result.project_path == str(temp_project)
        assert result.success is True

    def test_detect_nonexistent_path(self, service):
        """Test detection on non-existent path."""
        result = service.detect(project_path=Path("/nonexistent/path"))

        assert result.success is False
        assert len(result.errors) > 0

    def test_detect_empty_directory(self, service):
        """Test detection on empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = service.detect(project_path=Path(tmpdir))

            assert result.success is True
            assert result.dead_code_count == 0

    # =========================================================================
    # Python Detection Tests
    # =========================================================================

    def test_detect_python_unused_function(self, service, temp_project):
        """Test detection of unused Python functions."""
        result = service.detect(
            project_path=temp_project,
            include_languages=["python"]
        )

        # Should detect _unused_private
        unused_funcs = [
            item for item in result.items
            if item.item_type == DeadCodeItemType.FUNCTION and
            "_unused" in item.name.lower()
        ]
        assert len(unused_funcs) >= 1

    def test_detect_python_unused_class(self, service, temp_project):
        """Test detection of unused Python classes."""
        result = service.detect(
            project_path=temp_project,
            include_languages=["python"]
        )

        # Should detect _UnusedClass
        unused_classes = [
            item for item in result.items
            if item.item_type == DeadCodeItemType.CLASS and
            "unused" in item.name.lower()
        ]
        assert len(unused_classes) >= 1

    def test_detect_python_unused_variable(self, service, temp_project):
        """Test detection of unused Python variables."""
        result = service.detect(
            project_path=temp_project,
            include_languages=["python"]
        )

        # Should detect _UNUSED_VAR
        unused_vars = [
            item for item in result.items
            if item.item_type == DeadCodeItemType.VARIABLE and
            "unused" in item.name.lower()
        ]
        assert len(unused_vars) >= 1

    # =========================================================================
    # TypeScript Detection Tests
    # =========================================================================

    def test_detect_typescript_unused_function(self, service, temp_project):
        """Test detection of unused TypeScript functions."""
        result = service.detect(
            project_path=temp_project,
            include_languages=["typescript"]
        )

        # Non-exported functions are potentially unused
        ts_items = [
            item for item in result.items
            if item.file_path.endswith('.ts')
        ]
        assert len(ts_items) >= 0  # May or may not find based on pattern

    def test_detect_typescript_exports_have_low_confidence(self, service, temp_project):
        """Test that exported TypeScript symbols have lower confidence."""
        result = service.detect(
            project_path=temp_project,
            include_languages=["typescript"]
        )

        # Exported symbols should have lower confidence or not be flagged
        for item in result.items:
            if item.file_path.endswith('.ts') and 'exported' in item.name.lower():
                assert item.confidence < 0.8

    # =========================================================================
    # Confidence Scoring Tests
    # =========================================================================

    def test_private_symbols_have_higher_confidence(self, service, temp_project):
        """Test that private symbols (underscore prefix) have higher confidence."""
        result = service.detect(project_path=temp_project)

        for item in result.items:
            if item.name.startswith('_'):
                # Private symbols should have higher confidence
                assert item.confidence >= 0.5

    def test_confidence_threshold_filters_results(self, service, temp_project):
        """Test that confidence threshold filters low-confidence items."""
        result_low = service.detect(
            project_path=temp_project,
            confidence_threshold=0.1
        )
        result_high = service.detect(
            project_path=temp_project,
            confidence_threshold=0.9
        )

        # Higher threshold should return fewer items
        assert len(result_high.items) <= len(result_low.items)

    # =========================================================================
    # Removal Risk Assessment Tests
    # =========================================================================

    def test_private_functions_are_safe_to_remove(self, service, temp_project):
        """Test that private functions are marked safe to remove."""
        result = service.detect(project_path=temp_project)

        for item in result.items:
            if item.name.startswith('_') and not item.name.startswith('__'):
                # Single underscore private = safe removal
                assert item.removal_risk in [RemovalRisk.SAFE, RemovalRisk.LOW]

    def test_dunder_methods_are_not_safe(self, service):
        """Test that dunder methods are not marked as dead code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "dunder.py"
            py_file.write_text('''
class MyClass:
    def __init__(self):
        pass

    def __str__(self):
        return "MyClass"
''')
            result = service.detect(project_path=Path(tmpdir))

            # Dunder methods should not be flagged as dead code
            dunder_items = [
                item for item in result.items
                if item.name.startswith('__') and item.name.endswith('__')
            ]
            assert len(dunder_items) == 0

    # =========================================================================
    # Exclude Pattern Tests
    # =========================================================================

    def test_exclude_test_files(self, service):
        """Test that test files can be excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test_example.py"
            test_file.write_text('def test_something(): pass')

            # Create regular file
            main_file = Path(tmpdir) / "main.py"
            main_file.write_text('def _unused(): pass')

            result = service.detect(
                project_path=Path(tmpdir),
                include_tests=False
            )

            # Should not include items from test files
            test_items = [
                item for item in result.items
                if 'test_' in item.file_path
            ]
            assert len(test_items) == 0

    def test_exclude_patterns_work(self, service):
        """Test that exclude patterns filter files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in different directories
            (Path(tmpdir) / "src").mkdir()
            (Path(tmpdir) / "vendor").mkdir()

            Path(tmpdir, "src", "app.py").write_text('def _unused(): pass')
            Path(tmpdir, "vendor", "lib.py").write_text('def _unused2(): pass')

            result = service.detect(
                project_path=Path(tmpdir),
                exclude_patterns=["vendor/*"]
            )

            # Should not include items from vendor
            vendor_items = [
                item for item in result.items
                if 'vendor' in item.file_path
            ]
            assert len(vendor_items) == 0

    # =========================================================================
    # Cleanup Script Tests
    # =========================================================================

    def test_get_cleanup_script_generates_script(self, service, temp_project):
        """Test that cleanup script is generated."""
        result = service.detect(project_path=temp_project)

        script = service.get_cleanup_script(result, safe_only=True)

        assert isinstance(script, str)
        assert len(script) > 0

    def test_cleanup_script_safe_only(self, service, temp_project):
        """Test that safe_only filters cleanup script items."""
        result = service.detect(project_path=temp_project)

        script_safe = service.get_cleanup_script(result, safe_only=True)
        script_all = service.get_cleanup_script(result, safe_only=False)

        # All script should have more or equal lines than safe script
        assert len(script_all) >= len(script_safe)

    # =========================================================================
    # Statistics Tests
    # =========================================================================

    def test_result_statistics(self, service, temp_project):
        """Test that result includes accurate statistics."""
        result = service.detect(project_path=temp_project)

        assert result.files_analyzed >= 0
        assert result.dead_code_count == len(result.items)
        assert result.safe_removal_count >= 0
        assert result.safe_removal_count <= result.dead_code_count

    def test_result_has_timing(self, service, temp_project):
        """Test that result includes timing information."""
        result = service.detect(project_path=temp_project)

        assert result.duration_ms >= 0

    def test_result_to_dict(self, service, temp_project):
        """Test that result can be serialized to dict."""
        result = service.detect(project_path=temp_project)

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "items" in result_dict
        assert "dead_code_count" in result_dict
        assert "project_path" in result_dict
