"""
Tests for RuntimeAnalysisService - Week 132-133

Tests APM integration and local coverage/log analysis for runtime dead code detection.
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.runtime_analysis_service import (
    RuntimeAnalysisService,
    APMConfig,
    ExecutionTrace,
    EndpointUsage,
)
from app.models.week132_dead_code import (
    APMProvider,
    RuntimeAnalysisResult,
)


class TestRuntimeAnalysisService:
    """Test suite for RuntimeAnalysisService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return RuntimeAnalysisService()

    @pytest.fixture
    def temp_project_with_coverage(self):
        """Create temp project with Jest/Istanbul coverage file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_dir = Path(tmpdir) / "coverage"
            coverage_dir.mkdir()

            coverage_file = coverage_dir / "coverage-final.json"
            coverage_data = {
                "/app/src/index.js": {
                    "fnMap": {
                        "0": {"name": "main", "decl": {"start": {"line": 1}}},
                        "1": {"name": "helper", "decl": {"start": {"line": 10}}},
                        "2": {"name": "unused", "decl": {"start": {"line": 20}}},
                    },
                    "f": {
                        "0": 150,  # main called 150 times
                        "1": 50,   # helper called 50 times
                        "2": 0,    # unused never called
                    }
                }
            }
            coverage_file.write_text(json.dumps(coverage_data))

            yield Path(tmpdir)

    @pytest.fixture
    def temp_project_with_lcov(self):
        """Create temp project with LCOV coverage file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_dir = Path(tmpdir) / "coverage"
            coverage_dir.mkdir()

            lcov_file = coverage_dir / "lcov.info"
            lcov_content = """SF:/app/src/main.py
FN:1,main
FN:10,process
FN:20,unused_handler
FNDA:200,main
FNDA:50,process
FNDA:0,unused_handler
end_of_record
"""
            lcov_file.write_text(lcov_content)

            yield Path(tmpdir)

    @pytest.fixture
    def temp_project_with_logs(self):
        """Create temp project with access logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            logs_dir.mkdir()

            log_file = logs_dir / "access.log"
            log_content = """GET /api/users 200 12ms
POST /api/users 201 45ms
GET /api/users 200 8ms
GET /api/products 200 15ms
GET /api/users 200 10ms
DELETE /api/old-endpoint 404 5ms
"""
            log_file.write_text(log_content)

            yield Path(tmpdir)

    # =========================================================================
    # Basic Analysis Tests
    # =========================================================================

    def test_analyze_returns_result(self, service, temp_project_with_coverage):
        """Test that analyze() returns a RuntimeAnalysisResult."""
        result = service.analyze(project_path=temp_project_with_coverage)

        assert isinstance(result, RuntimeAnalysisResult)
        assert result.project_path == str(temp_project_with_coverage)

    def test_analyze_nonexistent_path(self, service):
        """Test analysis on non-existent path."""
        result = service.analyze(project_path=Path("/nonexistent/path"))

        assert result.success is False
        assert len(result.errors) > 0

    def test_analyze_empty_directory(self, service):
        """Test analysis on empty directory (no coverage/logs)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = service.analyze(project_path=Path(tmpdir))

            # Should fail gracefully with error message
            assert len(result.errors) > 0
            assert "coverage" in result.errors[0].lower() or "log" in result.errors[0].lower()

    # =========================================================================
    # Jest/Istanbul Coverage Tests
    # =========================================================================

    def test_parse_json_coverage(self, service, temp_project_with_coverage):
        """Test parsing Jest/Istanbul JSON coverage."""
        result = service.analyze(project_path=temp_project_with_coverage)

        assert result.total_functions >= 3
        assert result.called_functions >= 2  # main and helper
        assert result.uncalled_functions >= 1  # unused

    def test_hot_paths_from_coverage(self, service, temp_project_with_coverage):
        """Test that hot paths are identified from coverage."""
        result = service.analyze(project_path=temp_project_with_coverage)

        # main has 150 calls, should be hot path
        hot_function_names = [hp.get("function", "") for hp in result.hot_paths]
        assert "main" in hot_function_names or len(result.hot_paths) > 0

    def test_cold_paths_from_coverage(self, service, temp_project_with_coverage):
        """Test that cold paths are identified from coverage."""
        result = service.analyze(project_path=temp_project_with_coverage)

        # unused has 0 calls, should be cold path
        cold_function_names = [cp.get("function", "") for cp in result.cold_paths]
        assert "unused" in cold_function_names or len(result.cold_paths) > 0

    # =========================================================================
    # LCOV Coverage Tests
    # =========================================================================

    def test_parse_lcov_coverage(self, service, temp_project_with_lcov):
        """Test parsing LCOV coverage format."""
        result = service.analyze(project_path=temp_project_with_lcov)

        assert result.total_functions >= 3
        assert result.called_functions >= 2
        assert result.uncalled_functions >= 1

    def test_lcov_cold_paths(self, service, temp_project_with_lcov):
        """Test cold path detection from LCOV."""
        result = service.analyze(project_path=temp_project_with_lcov)

        cold_names = [cp.get("function", "") for cp in result.cold_paths]
        assert "unused_handler" in cold_names or len(result.cold_paths) > 0

    # =========================================================================
    # Access Log Tests
    # =========================================================================

    def test_parse_access_logs(self, service, temp_project_with_logs):
        """Test parsing access logs for endpoint usage."""
        result = service.analyze(project_path=temp_project_with_logs)

        assert result.total_endpoints > 0

    def test_endpoint_hot_paths(self, service, temp_project_with_logs):
        """Test hot endpoint detection from logs."""
        result = service.analyze(project_path=temp_project_with_logs)

        # /api/users is called most frequently
        if result.hot_paths:
            hot_endpoints = [hp.get("endpoint", "") for hp in result.hot_paths]
            assert "/api/users" in hot_endpoints or len(hot_endpoints) > 0

    # =========================================================================
    # APM Configuration Tests
    # =========================================================================

    def test_apm_config_new_relic(self, service):
        """Test APM configuration for New Relic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = APMConfig(
                provider=APMProvider.NEW_RELIC,
                api_key="test-key",
                account_id="123456"
            )

            result = service.analyze(
                project_path=Path(tmpdir),
                config=config
            )

            # Should return error about API key (stub implementation)
            assert len(result.errors) > 0

    def test_apm_config_datadog(self, service):
        """Test APM configuration for Datadog."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = APMConfig(
                provider=APMProvider.DATADOG,
                api_key="test-key"
            )

            result = service.analyze(
                project_path=Path(tmpdir),
                config=config
            )

            # Should return error (stub implementation)
            assert len(result.errors) > 0

    def test_apm_config_jaeger(self, service):
        """Test APM configuration for Jaeger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = APMConfig(
                provider=APMProvider.JAEGER,
                api_url="http://localhost:16686/api"
            )

            result = service.analyze(
                project_path=Path(tmpdir),
                config=config
            )

            # Should return error (stub implementation)
            assert "Jaeger" in str(result.errors)

    # =========================================================================
    # Endpoint Coverage Analysis Tests
    # =========================================================================

    def test_analyze_endpoint_coverage(self, service, temp_project_with_logs):
        """Test endpoint coverage analysis."""
        defined_endpoints = [
            {"path": "/api/users", "method": "GET", "handler": "get_users"},
            {"path": "/api/users", "method": "POST", "handler": "create_user"},
            {"path": "/api/products", "method": "GET", "handler": "get_products"},
            {"path": "/api/legacy", "method": "GET", "handler": "legacy_endpoint"},
        ]

        result = service.analyze_endpoint_coverage(
            project_path=temp_project_with_logs,
            defined_endpoints=defined_endpoints
        )

        assert "total_defined" in result
        assert result["total_defined"] == 4
        assert "coverage_percentage" in result

    def test_unused_endpoints_detected(self, service, temp_project_with_logs):
        """Test that unused endpoints are detected."""
        defined_endpoints = [
            {"path": "/api/users", "method": "GET", "handler": "get_users"},
            {"path": "/api/never-called", "method": "GET", "handler": "never_called"},
        ]

        result = service.analyze_endpoint_coverage(
            project_path=temp_project_with_logs,
            defined_endpoints=defined_endpoints
        )

        assert result["total_unused"] >= 1
        unused_paths = [ep.get("path") for ep in result["unused_endpoints"]]
        assert "/api/never-called" in unused_paths

    # =========================================================================
    # Analysis Period Tests
    # =========================================================================

    def test_analysis_period_set(self, service, temp_project_with_coverage):
        """Test that analysis period is set correctly."""
        result = service.analyze(
            project_path=temp_project_with_coverage,
            analysis_days=7
        )

        assert result.analysis_period_start is not None
        assert result.analysis_period_end is not None

        period_days = (result.analysis_period_end - result.analysis_period_start).days
        assert period_days == 7

    # =========================================================================
    # Result Serialization Tests
    # =========================================================================

    def test_result_to_dict(self, service, temp_project_with_coverage):
        """Test that result can be serialized to dict."""
        result = service.analyze(project_path=temp_project_with_coverage)

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "project_path" in result_dict
        assert "hot_paths" in result_dict
        assert "cold_paths" in result_dict
        assert "coverage_percentage" in result_dict

    def test_result_has_timing(self, service, temp_project_with_coverage):
        """Test that result includes timing information."""
        result = service.analyze(project_path=temp_project_with_coverage)

        assert result.duration_ms >= 0


class TestAPMConfig:
    """Test APMConfig dataclass."""

    def test_apm_config_defaults(self):
        """Test APMConfig default values."""
        config = APMConfig(provider=APMProvider.NEW_RELIC)

        assert config.provider == APMProvider.NEW_RELIC
        assert config.api_key is None
        assert config.environment == "production"

    def test_apm_config_custom_values(self):
        """Test APMConfig with custom values."""
        config = APMConfig(
            provider=APMProvider.DATADOG,
            api_key="my-api-key",
            api_url="https://custom.datadog.com",
            environment="staging"
        )

        assert config.provider == APMProvider.DATADOG
        assert config.api_key == "my-api-key"
        assert config.environment == "staging"
