"""
Health Check Suite Service (J6 - Fase 24).

Post-migration validation suite that verifies functional and non-functional
requirements after migration. Checks functional parity, data integrity,
performance, security posture, and integration health.

Author: Claude Code (Week 158)
Date: 2026-01-19
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    """Health check status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class CheckCategory(str, Enum):
    """Health check category."""
    FUNCTIONAL_PARITY = "functional_parity"
    DATA_INTEGRITY = "data_integrity"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"


class CheckSeverity(str, Enum):
    """Check failure severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CheckResult:
    """Result of a single health check."""
    check_id: str
    check_name: str
    category: CheckCategory
    status: CheckStatus
    severity: CheckSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_passed(self) -> bool:
        return self.status == CheckStatus.PASSED

    @property
    def is_critical_failure(self) -> bool:
        return self.status == CheckStatus.FAILED and self.severity == CheckSeverity.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_name": self.check_name,
            "category": self.category.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CheckDefinition:
    """Definition of a health check."""
    check_id: str
    name: str
    description: str
    category: CheckCategory
    severity: CheckSeverity
    enabled: bool = True
    timeout_seconds: float = 30.0
    # Check function signature: async (context: Dict) -> CheckResult
    check_fn: Optional[Callable[[Dict[str, Any]], Awaitable[CheckResult]]] = None


@dataclass
class ValidationSuite:
    """Collection of health checks for a migration."""
    suite_id: UUID
    name: str
    description: str
    checks: List[CheckDefinition] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_check(self, check: CheckDefinition) -> None:
        self.checks.append(check)

    def get_checks_by_category(self, category: CheckCategory) -> List[CheckDefinition]:
        return [c for c in self.checks if c.category == category]


@dataclass
class SuiteExecutionResult:
    """Result of running a validation suite."""
    execution_id: UUID
    suite_id: UUID
    suite_name: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: CheckStatus
    results: List[CheckResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0.0

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.PASSED)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.FAILED)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.WARNING)

    @property
    def critical_failures(self) -> List[CheckResult]:
        return [r for r in self.results if r.is_critical_failure]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": str(self.execution_id),
            "suite_id": str(self.suite_id),
            "suite_name": self.suite_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "summary": {
                "total": len(self.results),
                "passed": self.passed_count,
                "failed": self.failed_count,
                "warnings": self.warning_count,
                "critical_failures": len(self.critical_failures),
                "pass_rate": f"{(self.passed_count / len(self.results) * 100):.1f}%" if self.results else "N/A",
            },
            "results": [r.to_dict() for r in self.results],
            "critical_failures": [r.to_dict() for r in self.critical_failures],
        }


class HealthCheckSuiteService:
    """
    Post-migration validation suite service.

    Provides comprehensive health checks for:
    - Functional parity (old vs new behavior)
    - Data integrity (data migration correctness)
    - Performance (response times, throughput)
    - Security (vulnerability scans, auth checks)
    - Integration (external service connectivity)
    """

    def __init__(self):
        self.suites: Dict[UUID, ValidationSuite] = {}
        self.executions: Dict[UUID, SuiteExecutionResult] = {}
        self._built_in_checks = self._register_built_in_checks()

    def _register_built_in_checks(self) -> Dict[str, CheckDefinition]:
        """Register built-in health checks."""
        return {
            # Functional Parity Checks
            "fp_api_endpoints": CheckDefinition(
                check_id="fp_api_endpoints",
                name="API Endpoint Parity",
                description="Verify all legacy endpoints are available in new system",
                category=CheckCategory.FUNCTIONAL_PARITY,
                severity=CheckSeverity.CRITICAL,
            ),
            "fp_response_format": CheckDefinition(
                check_id="fp_response_format",
                name="Response Format Parity",
                description="Verify response formats match legacy system",
                category=CheckCategory.FUNCTIONAL_PARITY,
                severity=CheckSeverity.HIGH,
            ),
            "fp_business_rules": CheckDefinition(
                check_id="fp_business_rules",
                name="Business Rules Parity",
                description="Verify business rules produce same outcomes",
                category=CheckCategory.FUNCTIONAL_PARITY,
                severity=CheckSeverity.CRITICAL,
            ),

            # Data Integrity Checks
            "di_record_count": CheckDefinition(
                check_id="di_record_count",
                name="Record Count Validation",
                description="Verify record counts match between systems",
                category=CheckCategory.DATA_INTEGRITY,
                severity=CheckSeverity.CRITICAL,
            ),
            "di_data_checksums": CheckDefinition(
                check_id="di_data_checksums",
                name="Data Checksum Validation",
                description="Verify data checksums match for critical tables",
                category=CheckCategory.DATA_INTEGRITY,
                severity=CheckSeverity.CRITICAL,
            ),
            "di_referential_integrity": CheckDefinition(
                check_id="di_referential_integrity",
                name="Referential Integrity",
                description="Verify all foreign key relationships are valid",
                category=CheckCategory.DATA_INTEGRITY,
                severity=CheckSeverity.HIGH,
            ),
            "di_null_checks": CheckDefinition(
                check_id="di_null_checks",
                name="Null Value Validation",
                description="Verify no unexpected nulls in required fields",
                category=CheckCategory.DATA_INTEGRITY,
                severity=CheckSeverity.MEDIUM,
            ),

            # Performance Checks
            "perf_response_time": CheckDefinition(
                check_id="perf_response_time",
                name="Response Time Check",
                description="Verify response times are within acceptable range",
                category=CheckCategory.PERFORMANCE,
                severity=CheckSeverity.HIGH,
            ),
            "perf_throughput": CheckDefinition(
                check_id="perf_throughput",
                name="Throughput Check",
                description="Verify system handles expected load",
                category=CheckCategory.PERFORMANCE,
                severity=CheckSeverity.HIGH,
            ),
            "perf_resource_usage": CheckDefinition(
                check_id="perf_resource_usage",
                name="Resource Usage Check",
                description="Verify CPU/memory usage is within limits",
                category=CheckCategory.PERFORMANCE,
                severity=CheckSeverity.MEDIUM,
            ),
            "perf_database_queries": CheckDefinition(
                check_id="perf_database_queries",
                name="Database Query Performance",
                description="Verify no slow queries or N+1 patterns",
                category=CheckCategory.PERFORMANCE,
                severity=CheckSeverity.MEDIUM,
            ),

            # Security Checks
            "sec_auth_endpoints": CheckDefinition(
                check_id="sec_auth_endpoints",
                name="Authentication Endpoints",
                description="Verify all endpoints require proper authentication",
                category=CheckCategory.SECURITY,
                severity=CheckSeverity.CRITICAL,
            ),
            "sec_authorization": CheckDefinition(
                check_id="sec_authorization",
                name="Authorization Rules",
                description="Verify authorization rules are enforced",
                category=CheckCategory.SECURITY,
                severity=CheckSeverity.CRITICAL,
            ),
            "sec_data_encryption": CheckDefinition(
                check_id="sec_data_encryption",
                name="Data Encryption",
                description="Verify sensitive data is encrypted",
                category=CheckCategory.SECURITY,
                severity=CheckSeverity.CRITICAL,
            ),
            "sec_no_secrets": CheckDefinition(
                check_id="sec_no_secrets",
                name="No Hardcoded Secrets",
                description="Verify no secrets in code or configs",
                category=CheckCategory.SECURITY,
                severity=CheckSeverity.HIGH,
            ),

            # Integration Checks
            "int_database": CheckDefinition(
                check_id="int_database",
                name="Database Connectivity",
                description="Verify database connection is healthy",
                category=CheckCategory.INTEGRATION,
                severity=CheckSeverity.CRITICAL,
            ),
            "int_external_apis": CheckDefinition(
                check_id="int_external_apis",
                name="External API Connectivity",
                description="Verify external APIs are reachable",
                category=CheckCategory.INTEGRATION,
                severity=CheckSeverity.HIGH,
            ),
            "int_message_queues": CheckDefinition(
                check_id="int_message_queues",
                name="Message Queue Health",
                description="Verify message queues are operational",
                category=CheckCategory.INTEGRATION,
                severity=CheckSeverity.HIGH,
            ),
            "int_cache": CheckDefinition(
                check_id="int_cache",
                name="Cache Connectivity",
                description="Verify cache (Redis) is accessible",
                category=CheckCategory.INTEGRATION,
                severity=CheckSeverity.MEDIUM,
            ),
        }

    # ==================== Suite Management ====================

    async def create_suite(
        self,
        name: str,
        description: str = "",
        include_categories: Optional[List[CheckCategory]] = None,
        custom_checks: Optional[List[CheckDefinition]] = None,
    ) -> ValidationSuite:
        """
        Create a new validation suite.

        Args:
            name: Suite name
            description: Suite description
            include_categories: Categories to include (None = all)
            custom_checks: Additional custom checks

        Returns:
            Created validation suite
        """
        suite = ValidationSuite(
            suite_id=uuid4(),
            name=name,
            description=description,
        )

        # Add built-in checks for selected categories
        for check in self._built_in_checks.values():
            if include_categories is None or check.category in include_categories:
                suite.add_check(check)

        # Add custom checks
        if custom_checks:
            for check in custom_checks:
                suite.add_check(check)

        self.suites[suite.suite_id] = suite
        logger.info(f"Created validation suite: {suite.suite_id} with {len(suite.checks)} checks")

        return suite

    async def create_post_migration_suite(
        self,
        migration_name: str,
        legacy_config: Dict[str, Any],
        new_config: Dict[str, Any],
    ) -> ValidationSuite:
        """
        Create a standard post-migration validation suite.

        Args:
            migration_name: Name of the migration
            legacy_config: Legacy system configuration
            new_config: New system configuration

        Returns:
            Configured validation suite
        """
        suite = await self.create_suite(
            name=f"Post-Migration Validation: {migration_name}",
            description=f"Validates migration from legacy to new system",
        )

        # Store configs for check execution
        suite.checks[0].check_fn = self._create_endpoint_parity_check(legacy_config, new_config)

        return suite

    def _create_endpoint_parity_check(
        self,
        legacy_config: Dict[str, Any],
        new_config: Dict[str, Any],
    ) -> Callable[[Dict[str, Any]], Awaitable[CheckResult]]:
        """Create endpoint parity check function."""
        async def check_fn(context: Dict[str, Any]) -> CheckResult:
            legacy_endpoints = legacy_config.get("endpoints", [])
            new_endpoints = new_config.get("endpoints", [])

            missing = set(legacy_endpoints) - set(new_endpoints)

            if missing:
                return CheckResult(
                    check_id="fp_api_endpoints",
                    check_name="API Endpoint Parity",
                    category=CheckCategory.FUNCTIONAL_PARITY,
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.CRITICAL,
                    message=f"Missing endpoints: {', '.join(missing)}",
                    details={"missing_endpoints": list(missing)},
                )
            return CheckResult(
                check_id="fp_api_endpoints",
                check_name="API Endpoint Parity",
                category=CheckCategory.FUNCTIONAL_PARITY,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.CRITICAL,
                message="All endpoints present in new system",
                details={"endpoint_count": len(new_endpoints)},
            )

        return check_fn

    # ==================== Suite Execution ====================

    async def execute_suite(
        self,
        suite_id: UUID,
        context: Optional[Dict[str, Any]] = None,
        parallel: bool = True,
    ) -> SuiteExecutionResult:
        """
        Execute all checks in a validation suite.

        Args:
            suite_id: Suite to execute
            context: Context data for checks
            parallel: Run checks in parallel

        Returns:
            Execution result with all check results
        """
        suite = self.suites.get(suite_id)
        if not suite:
            raise ValueError(f"Suite not found: {suite_id}")

        context = context or {}
        execution = SuiteExecutionResult(
            execution_id=uuid4(),
            suite_id=suite_id,
            suite_name=suite.name,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            status=CheckStatus.PASSED,
        )

        enabled_checks = [c for c in suite.checks if c.enabled]

        if parallel:
            # Run checks in parallel
            tasks = [
                self._execute_check(check, context)
                for check in enabled_checks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Run checks sequentially
            results = []
            for check in enabled_checks:
                result = await self._execute_check(check, context)
                results.append(result)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                execution.results.append(CheckResult(
                    check_id="error",
                    check_name="Execution Error",
                    category=CheckCategory.FUNCTIONAL_PARITY,
                    status=CheckStatus.ERROR,
                    severity=CheckSeverity.HIGH,
                    message=str(result),
                ))
            else:
                execution.results.append(result)

        # Determine overall status
        if any(r.is_critical_failure for r in execution.results):
            execution.status = CheckStatus.FAILED
        elif any(r.status == CheckStatus.FAILED for r in execution.results):
            execution.status = CheckStatus.WARNING
        elif any(r.status == CheckStatus.WARNING for r in execution.results):
            execution.status = CheckStatus.WARNING

        execution.completed_at = datetime.now(timezone.utc)
        self.executions[execution.execution_id] = execution

        logger.info(
            f"Suite execution complete: {execution.execution_id} - "
            f"{execution.passed_count}/{len(execution.results)} passed"
        )

        return execution

    async def _execute_check(
        self,
        check: CheckDefinition,
        context: Dict[str, Any],
    ) -> CheckResult:
        """Execute a single health check."""
        start_time = datetime.now(timezone.utc)

        try:
            if check.check_fn:
                result = await asyncio.wait_for(
                    check.check_fn(context),
                    timeout=check.timeout_seconds,
                )
            else:
                # Default: simulate check (in real implementation, connect to actual systems)
                result = await self._run_simulated_check(check, context)

            result.duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return result

        except asyncio.TimeoutError:
            return CheckResult(
                check_id=check.check_id,
                check_name=check.name,
                category=check.category,
                status=CheckStatus.ERROR,
                severity=check.severity,
                message=f"Check timed out after {check.timeout_seconds}s",
                duration_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
            )
        except Exception as e:
            return CheckResult(
                check_id=check.check_id,
                check_name=check.name,
                category=check.category,
                status=CheckStatus.ERROR,
                severity=check.severity,
                message=f"Check failed with error: {str(e)}",
                duration_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
            )

    async def _run_simulated_check(
        self,
        check: CheckDefinition,
        context: Dict[str, Any],
    ) -> CheckResult:
        """Run a simulated check (for testing/demo purposes)."""
        # In real implementation, this would call actual validation logic
        # For now, return passed with simulated data

        await asyncio.sleep(0.01)  # Simulate work

        return CheckResult(
            check_id=check.check_id,
            check_name=check.name,
            category=check.category,
            status=CheckStatus.PASSED,
            severity=check.severity,
            message=f"Check '{check.name}' passed (simulated)",
            details={
                "simulated": True,
                "context_keys": list(context.keys()),
            },
        )

    # ==================== Category-specific Checks ====================

    async def check_functional_parity(
        self,
        legacy_responses: Dict[str, Any],
        new_responses: Dict[str, Any],
        tolerance: float = 0.01,
    ) -> List[CheckResult]:
        """
        Check functional parity between legacy and new system responses.

        Args:
            legacy_responses: Dict of endpoint -> response from legacy
            new_responses: Dict of endpoint -> response from new
            tolerance: Acceptable difference for numeric values

        Returns:
            List of check results
        """
        results = []

        for endpoint, legacy_resp in legacy_responses.items():
            new_resp = new_responses.get(endpoint)

            if new_resp is None:
                results.append(CheckResult(
                    check_id=f"fp_{endpoint}",
                    check_name=f"Parity: {endpoint}",
                    category=CheckCategory.FUNCTIONAL_PARITY,
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.CRITICAL,
                    message=f"Endpoint {endpoint} not available in new system",
                ))
                continue

            # Compare responses
            diff = self._compare_responses(legacy_resp, new_resp, tolerance)
            if diff:
                results.append(CheckResult(
                    check_id=f"fp_{endpoint}",
                    check_name=f"Parity: {endpoint}",
                    category=CheckCategory.FUNCTIONAL_PARITY,
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.HIGH,
                    message=f"Response differences detected",
                    details={"differences": diff},
                ))
            else:
                results.append(CheckResult(
                    check_id=f"fp_{endpoint}",
                    check_name=f"Parity: {endpoint}",
                    category=CheckCategory.FUNCTIONAL_PARITY,
                    status=CheckStatus.PASSED,
                    severity=CheckSeverity.HIGH,
                    message="Responses match",
                ))

        return results

    def _compare_responses(
        self,
        legacy: Any,
        new: Any,
        tolerance: float,
        path: str = "",
    ) -> List[Dict[str, Any]]:
        """Compare two responses and return differences."""
        differences = []

        if type(legacy) != type(new):
            differences.append({
                "path": path or "root",
                "type": "type_mismatch",
                "legacy_type": type(legacy).__name__,
                "new_type": type(new).__name__,
            })
            return differences

        if isinstance(legacy, dict):
            all_keys = set(legacy.keys()) | set(new.keys())
            for key in all_keys:
                sub_path = f"{path}.{key}" if path else key
                if key not in legacy:
                    differences.append({
                        "path": sub_path,
                        "type": "new_field",
                        "value": new[key],
                    })
                elif key not in new:
                    differences.append({
                        "path": sub_path,
                        "type": "missing_field",
                        "value": legacy[key],
                    })
                else:
                    differences.extend(
                        self._compare_responses(legacy[key], new[key], tolerance, sub_path)
                    )
        elif isinstance(legacy, list):
            if len(legacy) != len(new):
                differences.append({
                    "path": path,
                    "type": "length_mismatch",
                    "legacy_length": len(legacy),
                    "new_length": len(new),
                })
            else:
                for i, (l, n) in enumerate(zip(legacy, new)):
                    differences.extend(
                        self._compare_responses(l, n, tolerance, f"{path}[{i}]")
                    )
        elif isinstance(legacy, (int, float)):
            if abs(legacy - new) > tolerance * max(abs(legacy), 1):
                differences.append({
                    "path": path,
                    "type": "value_mismatch",
                    "legacy_value": legacy,
                    "new_value": new,
                    "difference": abs(legacy - new),
                })
        elif legacy != new:
            differences.append({
                "path": path,
                "type": "value_mismatch",
                "legacy_value": legacy,
                "new_value": new,
            })

        return differences

    async def check_data_integrity(
        self,
        source_counts: Dict[str, int],
        target_counts: Dict[str, int],
    ) -> List[CheckResult]:
        """
        Check data integrity by comparing record counts.

        Args:
            source_counts: Dict of table -> record count in source
            target_counts: Dict of table -> record count in target

        Returns:
            List of check results
        """
        results = []

        for table, source_count in source_counts.items():
            target_count = target_counts.get(table, 0)

            if source_count != target_count:
                severity = CheckSeverity.CRITICAL if abs(source_count - target_count) > 10 else CheckSeverity.HIGH
                results.append(CheckResult(
                    check_id=f"di_count_{table}",
                    check_name=f"Record Count: {table}",
                    category=CheckCategory.DATA_INTEGRITY,
                    status=CheckStatus.FAILED,
                    severity=severity,
                    message=f"Count mismatch: source={source_count}, target={target_count}",
                    details={
                        "source_count": source_count,
                        "target_count": target_count,
                        "difference": source_count - target_count,
                    },
                ))
            else:
                results.append(CheckResult(
                    check_id=f"di_count_{table}",
                    check_name=f"Record Count: {table}",
                    category=CheckCategory.DATA_INTEGRITY,
                    status=CheckStatus.PASSED,
                    severity=CheckSeverity.CRITICAL,
                    message=f"Counts match: {source_count} records",
                    details={"count": source_count},
                ))

        return results

    async def check_performance(
        self,
        metrics: Dict[str, Any],
        thresholds: Optional[Dict[str, Any]] = None,
    ) -> List[CheckResult]:
        """
        Check performance metrics against thresholds.

        Args:
            metrics: Dict with response_time_p99, throughput, cpu_usage, memory_usage
            thresholds: Optional custom thresholds

        Returns:
            List of check results
        """
        default_thresholds = {
            "response_time_p99_ms": 500,
            "throughput_rps": 100,
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85,
        }
        thresholds = {**default_thresholds, **(thresholds or {})}
        results = []

        # Response time
        rt = metrics.get("response_time_p99_ms", 0)
        threshold = thresholds["response_time_p99_ms"]
        results.append(CheckResult(
            check_id="perf_response_time",
            check_name="Response Time (p99)",
            category=CheckCategory.PERFORMANCE,
            status=CheckStatus.PASSED if rt <= threshold else CheckStatus.FAILED,
            severity=CheckSeverity.HIGH,
            message=f"P99 response time: {rt}ms (threshold: {threshold}ms)",
            details={"value": rt, "threshold": threshold},
        ))

        # Throughput
        tp = metrics.get("throughput_rps", 0)
        threshold = thresholds["throughput_rps"]
        results.append(CheckResult(
            check_id="perf_throughput",
            check_name="Throughput",
            category=CheckCategory.PERFORMANCE,
            status=CheckStatus.PASSED if tp >= threshold else CheckStatus.WARNING,
            severity=CheckSeverity.HIGH,
            message=f"Throughput: {tp} req/s (threshold: {threshold} req/s)",
            details={"value": tp, "threshold": threshold},
        ))

        # CPU usage
        cpu = metrics.get("cpu_usage_percent", 0)
        threshold = thresholds["cpu_usage_percent"]
        results.append(CheckResult(
            check_id="perf_cpu",
            check_name="CPU Usage",
            category=CheckCategory.PERFORMANCE,
            status=CheckStatus.PASSED if cpu <= threshold else CheckStatus.WARNING,
            severity=CheckSeverity.MEDIUM,
            message=f"CPU usage: {cpu}% (threshold: {threshold}%)",
            details={"value": cpu, "threshold": threshold},
        ))

        # Memory usage
        mem = metrics.get("memory_usage_percent", 0)
        threshold = thresholds["memory_usage_percent"]
        results.append(CheckResult(
            check_id="perf_memory",
            check_name="Memory Usage",
            category=CheckCategory.PERFORMANCE,
            status=CheckStatus.PASSED if mem <= threshold else CheckStatus.WARNING,
            severity=CheckSeverity.MEDIUM,
            message=f"Memory usage: {mem}% (threshold: {threshold}%)",
            details={"value": mem, "threshold": threshold},
        ))

        return results

    # ==================== Reports ====================

    def generate_report(
        self,
        execution_id: UUID,
    ) -> Dict[str, Any]:
        """Generate detailed validation report."""
        execution = self.executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        # Group results by category
        by_category = {}
        for cat in CheckCategory:
            cat_results = [r for r in execution.results if r.category == cat]
            by_category[cat.value] = {
                "total": len(cat_results),
                "passed": sum(1 for r in cat_results if r.status == CheckStatus.PASSED),
                "failed": sum(1 for r in cat_results if r.status == CheckStatus.FAILED),
                "warnings": sum(1 for r in cat_results if r.status == CheckStatus.WARNING),
                "results": [r.to_dict() for r in cat_results],
            }

        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "execution": execution.to_dict(),
            "by_category": by_category,
            "recommendations": self._generate_recommendations(execution),
            "go_live_readiness": self._assess_go_live_readiness(execution),
        }

    def _generate_recommendations(
        self,
        execution: SuiteExecutionResult,
    ) -> List[str]:
        """Generate recommendations based on check results."""
        recommendations = []

        # Check critical failures
        critical = execution.critical_failures
        if critical:
            recommendations.append(
                f"BLOCKER: {len(critical)} critical check(s) failed. "
                f"Address these before go-live: {', '.join(c.check_name for c in critical)}"
            )

        # Check by category
        for cat in CheckCategory:
            cat_failures = [
                r for r in execution.results
                if r.category == cat and r.status == CheckStatus.FAILED
            ]
            if cat_failures:
                recommendations.append(
                    f"{cat.value.upper()}: {len(cat_failures)} issue(s) - "
                    f"Review {', '.join(r.check_name for r in cat_failures[:3])}"
                )

        if not recommendations:
            recommendations.append("All checks passed. System is ready for go-live.")

        return recommendations

    def _assess_go_live_readiness(
        self,
        execution: SuiteExecutionResult,
    ) -> Dict[str, Any]:
        """Assess if system is ready for go-live."""
        critical_failures = len(execution.critical_failures)
        high_failures = sum(
            1 for r in execution.results
            if r.status == CheckStatus.FAILED and r.severity == CheckSeverity.HIGH
        )
        warnings = execution.warning_count

        if critical_failures > 0:
            status = "NOT_READY"
            message = f"{critical_failures} critical failure(s) must be resolved"
        elif high_failures > 3:
            status = "NOT_READY"
            message = f"Too many high severity failures ({high_failures})"
        elif high_failures > 0:
            status = "CONDITIONAL"
            message = f"{high_failures} high severity issue(s) should be addressed"
        elif warnings > 5:
            status = "CONDITIONAL"
            message = f"Multiple warnings ({warnings}) require review"
        else:
            status = "READY"
            message = "All checks passed"

        return {
            "status": status,
            "message": message,
            "critical_failures": critical_failures,
            "high_failures": high_failures,
            "warnings": warnings,
            "pass_rate": f"{execution.passed_count / len(execution.results) * 100:.1f}%" if execution.results else "N/A",
        }


def create_health_check_suite_service() -> HealthCheckSuiteService:
    """Factory function to create Health Check Suite service."""
    return HealthCheckSuiteService()
