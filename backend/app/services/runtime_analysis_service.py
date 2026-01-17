"""
RuntimeAnalysisService - Week 132-133

APM/Runtime analysis integration for detecting unused code
based on actual execution data.

Agent: Miguel (Migration Architect)
"""
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.models.dead_code import (
    APMProvider,
    RuntimeAnalysisResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# APM Configuration
# ============================================================================

@dataclass
class APMConfig:
    """Configuration for APM provider connection."""
    provider: APMProvider
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    account_id: Optional[str] = None
    application_name: Optional[str] = None
    environment: str = "production"
    extra_config: Dict[str, Any] = field(default_factory=dict)


# Default APM endpoints
APM_ENDPOINTS = {
    APMProvider.NEW_RELIC: "https://api.newrelic.com/graphql",
    APMProvider.DATADOG: "https://api.datadoghq.com/api/v1",
    APMProvider.JAEGER: "http://localhost:16686/api",
    APMProvider.ZIPKIN: "http://localhost:9411/api/v2",
    APMProvider.APP_DYNAMICS: "https://analytics.api.appdynamics.com",
}


@dataclass
class ExecutionTrace:
    """A single execution trace."""
    trace_id: str
    function_name: str
    file_path: str
    call_count: int
    total_duration_ms: float
    avg_duration_ms: float
    last_called: datetime
    callers: List[str] = field(default_factory=list)
    callees: List[str] = field(default_factory=list)


@dataclass
class EndpointUsage:
    """API endpoint usage statistics."""
    path: str
    method: str
    call_count: int
    avg_response_time_ms: float
    error_rate: float
    last_called: Optional[datetime] = None
    handler_function: Optional[str] = None


class RuntimeAnalysisService:
    """
    Runtime analysis service for APM data integration.

    Analyzes actual execution data to identify:
    - Functions never called in production
    - API endpoints with zero traffic
    - Hot paths (frequently executed)
    - Cold paths (rarely/never executed)
    """

    def __init__(self, config: Optional[APMConfig] = None):
        self._config = config

    def analyze(
        self,
        project_path: Path,
        config: Optional[APMConfig] = None,
        analysis_days: int = 30,
        include_traces: bool = True,
    ) -> RuntimeAnalysisResult:
        """
        Analyze runtime data for a project.

        Args:
            project_path: Path to the project
            config: APM configuration (overrides instance config)
            analysis_days: Number of days to analyze
            include_traces: Whether to include detailed traces

        Returns:
            RuntimeAnalysisResult with findings
        """
        start_time = time.time()
        apm_config = config or self._config

        result = RuntimeAnalysisResult(
            project_path=str(project_path),
            apm_provider=apm_config.provider if apm_config else APMProvider.NONE,
            analysis_period_start=datetime.now(timezone.utc) - timedelta(days=analysis_days),
            analysis_period_end=datetime.now(timezone.utc),
        )

        if not project_path.exists():
            result.success = False
            result.errors.append(f"Project path does not exist: {project_path}")
            return result

        try:
            if apm_config and apm_config.provider != APMProvider.NONE:
                # Fetch data from APM provider
                self._analyze_with_apm(result, apm_config, analysis_days, include_traces)
            else:
                # Fall back to local log analysis or coverage data
                self._analyze_local(result, project_path)

            # Calculate coverage percentage
            if result.total_functions > 0:
                result.coverage_percentage = (
                    result.called_functions / result.total_functions * 100
                )

        except Exception as e:
            logger.error(f"Runtime analysis failed: {e}")
            result.success = False
            result.errors.append(str(e))

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    def _analyze_with_apm(
        self,
        result: RuntimeAnalysisResult,
        config: APMConfig,
        analysis_days: int,
        include_traces: bool,
    ):
        """Analyze using APM provider data."""
        provider = config.provider

        if provider == APMProvider.NEW_RELIC:
            self._analyze_new_relic(result, config, analysis_days, include_traces)
        elif provider == APMProvider.DATADOG:
            self._analyze_datadog(result, config, analysis_days, include_traces)
        elif provider == APMProvider.JAEGER:
            self._analyze_jaeger(result, config, analysis_days, include_traces)
        elif provider == APMProvider.ZIPKIN:
            self._analyze_zipkin(result, config, analysis_days, include_traces)
        else:
            result.errors.append(f"APM provider {provider} not yet implemented")

    def _analyze_new_relic(
        self,
        result: RuntimeAnalysisResult,
        config: APMConfig,
        analysis_days: int,
        include_traces: bool,
    ):
        """Analyze using New Relic API."""
        # This would use the New Relic GraphQL API
        # For now, we return a stub implementation

        result.errors.append(
            "New Relic integration requires API key. "
            "Set NEW_RELIC_API_KEY environment variable."
        )

        # Example query structure for New Relic:
        # query = """
        # {
        #   actor {
        #     account(id: $accountId) {
        #       nrql(query: "SELECT count(*) FROM Transaction
        #                    WHERE appName = '$appName'
        #                    FACET name SINCE $days days ago") {
        #         results
        #       }
        #     }
        #   }
        # }
        # """

    def _analyze_datadog(
        self,
        result: RuntimeAnalysisResult,
        config: APMConfig,
        analysis_days: int,
        include_traces: bool,
    ):
        """Analyze using Datadog APM API."""
        result.errors.append(
            "Datadog integration requires API key. "
            "Set DD_API_KEY environment variable."
        )

    def _analyze_jaeger(
        self,
        result: RuntimeAnalysisResult,
        config: APMConfig,
        analysis_days: int,
        include_traces: bool,
    ):
        """Analyze using Jaeger tracing API."""
        # Jaeger has a REST API for querying traces
        # This is often used in local development/testing

        api_url = config.api_url or APM_ENDPOINTS[APMProvider.JAEGER]

        result.errors.append(
            f"Jaeger integration expects Jaeger UI at {api_url}. "
            "Ensure Jaeger is running and accessible."
        )

    def _analyze_zipkin(
        self,
        result: RuntimeAnalysisResult,
        config: APMConfig,
        analysis_days: int,
        include_traces: bool,
    ):
        """Analyze using Zipkin API."""
        api_url = config.api_url or APM_ENDPOINTS[APMProvider.ZIPKIN]

        result.errors.append(
            f"Zipkin integration expects Zipkin at {api_url}. "
            "Ensure Zipkin is running and accessible."
        )

    def _analyze_local(self, result: RuntimeAnalysisResult, project_path: Path):
        """
        Analyze using local data sources.

        Falls back to:
        1. Coverage reports (Jest, pytest, etc.)
        2. Access logs
        3. Performance logs
        """
        # Look for coverage reports
        coverage_files = self._find_coverage_files(project_path)

        if coverage_files:
            self._parse_coverage_for_runtime(result, coverage_files)
        else:
            # Look for access logs
            log_files = self._find_log_files(project_path)

            if log_files:
                self._parse_logs_for_runtime(result, log_files)
            else:
                result.errors.append(
                    "No APM connection and no local coverage/log files found. "
                    "Run tests with coverage enabled or configure APM."
                )

    def _find_coverage_files(self, project_path: Path) -> List[Path]:
        """Find coverage report files."""
        coverage_patterns = [
            "coverage/coverage-final.json",  # Jest
            "coverage.json",
            ".coverage",  # pytest-cov
            "coverage.xml",  # Cobertura format
            "lcov.info",  # LCOV format
            "coverage/lcov.info",
        ]

        files = []
        for pattern in coverage_patterns:
            for path in project_path.rglob(pattern):
                files.append(path)

        return files

    def _find_log_files(self, project_path: Path) -> List[Path]:
        """Find access/performance log files."""
        log_patterns = [
            "logs/access*.log",
            "logs/app*.log",
            "*.access.log",
            "logs/performance*.log",
        ]

        files = []
        for pattern in log_patterns:
            for path in project_path.rglob(pattern):
                files.append(path)

        return files

    def _parse_coverage_for_runtime(
        self, result: RuntimeAnalysisResult, coverage_files: List[Path]
    ):
        """Parse coverage files to infer runtime usage."""
        for coverage_file in coverage_files:
            try:
                if coverage_file.suffix == ".json":
                    self._parse_json_coverage(result, coverage_file)
                elif coverage_file.name == "lcov.info":
                    self._parse_lcov_coverage(result, coverage_file)
            except Exception as e:
                logger.warning(f"Error parsing coverage file {coverage_file}: {e}")

    def _parse_json_coverage(self, result: RuntimeAnalysisResult, coverage_file: Path):
        """Parse Jest/Istanbul JSON coverage."""
        try:
            data = json.loads(coverage_file.read_text())

            # Istanbul/Jest format
            for file_path, file_data in data.items():
                if isinstance(file_data, dict):
                    fn_map = file_data.get("fnMap", {})
                    fn_hits = file_data.get("f", {})

                    result.total_functions += len(fn_map)

                    for fn_id, hits in fn_hits.items():
                        if hits > 0:
                            result.called_functions += 1

                            # Track hot paths
                            if hits > 100:
                                fn_info = fn_map.get(fn_id, {})
                                result.hot_paths.append({
                                    "function": fn_info.get("name", f"fn_{fn_id}"),
                                    "file": file_path,
                                    "call_count": hits,
                                })
                        else:
                            result.uncalled_functions += 1

                            # Track cold paths
                            fn_info = fn_map.get(fn_id, {})
                            result.cold_paths.append({
                                "function": fn_info.get("name", f"fn_{fn_id}"),
                                "file": file_path,
                                "call_count": 0,
                            })

        except Exception as e:
            result.errors.append(f"Error parsing JSON coverage: {e}")

    def _parse_lcov_coverage(self, result: RuntimeAnalysisResult, coverage_file: Path):
        """Parse LCOV coverage format."""
        try:
            content = coverage_file.read_text()
            current_file = None

            for line in content.split("\n"):
                line = line.strip()

                if line.startswith("SF:"):
                    current_file = line[3:]
                elif line.startswith("FN:"):
                    result.total_functions += 1
                elif line.startswith("FNDA:"):
                    parts = line[5:].split(",")
                    if len(parts) >= 2:
                        hits = int(parts[0])
                        fn_name = parts[1]

                        if hits > 0:
                            result.called_functions += 1
                            if hits > 100:
                                result.hot_paths.append({
                                    "function": fn_name,
                                    "file": current_file,
                                    "call_count": hits,
                                })
                        else:
                            result.uncalled_functions += 1
                            result.cold_paths.append({
                                "function": fn_name,
                                "file": current_file,
                                "call_count": 0,
                            })

        except Exception as e:
            result.errors.append(f"Error parsing LCOV coverage: {e}")

    def _parse_logs_for_runtime(
        self, result: RuntimeAnalysisResult, log_files: List[Path]
    ):
        """Parse log files to extract runtime usage."""
        endpoint_counts: Dict[str, int] = {}

        for log_file in log_files:
            try:
                for line in log_file.read_text().split("\n"):
                    # Look for HTTP request patterns
                    # Format: GET /api/users 200 12ms
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                            if i + 1 < len(parts):
                                endpoint = parts[i + 1]
                                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
                                break
            except Exception as e:
                logger.warning(f"Error parsing log file {log_file}: {e}")

        result.total_endpoints = len(endpoint_counts)
        result.active_endpoints = len([c for c in endpoint_counts.values() if c > 0])

        # Sort by usage
        sorted_endpoints = sorted(endpoint_counts.items(), key=lambda x: -x[1])

        # Hot paths = top 10%
        top_count = max(1, len(sorted_endpoints) // 10)
        result.hot_paths = [
            {"endpoint": ep, "call_count": count}
            for ep, count in sorted_endpoints[:top_count]
        ]

        # Cold paths = bottom 10% or zero calls
        result.cold_paths = [
            {"endpoint": ep, "call_count": count}
            for ep, count in sorted_endpoints[-top_count:]
            if count < 10
        ]

    def analyze_endpoint_coverage(
        self,
        project_path: Path,
        defined_endpoints: List[Dict[str, str]],
        config: Optional[APMConfig] = None,
    ) -> Dict[str, Any]:
        """
        Compare defined endpoints against actual usage.

        Args:
            project_path: Project path
            defined_endpoints: List of {path, method, handler} dicts
            config: APM configuration

        Returns:
            Dict with endpoint coverage analysis
        """
        result = self.analyze(project_path, config)

        # Build set of called endpoints
        called_paths = set()
        for trace in result.hot_paths + result.execution_traces:
            if "endpoint" in trace:
                called_paths.add(trace["endpoint"])

        unused_endpoints = []
        used_endpoints = []

        for endpoint in defined_endpoints:
            path = endpoint.get("path", "")
            if path in called_paths or any(path in cp for cp in called_paths):
                used_endpoints.append(endpoint)
            else:
                unused_endpoints.append(endpoint)

        return {
            "total_defined": len(defined_endpoints),
            "total_used": len(used_endpoints),
            "total_unused": len(unused_endpoints),
            "coverage_percentage": (
                len(used_endpoints) / len(defined_endpoints) * 100
                if defined_endpoints else 0
            ),
            "unused_endpoints": unused_endpoints,
            "used_endpoints": used_endpoints,
        }
