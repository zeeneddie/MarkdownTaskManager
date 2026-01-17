"""
Quality Gate Integration Service

Week 50: Integrates Quality Gates Configuration with Validation Workflows

This service:
1. Reads quality gate config from database
2. Converts workflow rules to ValidationConfig
3. Provides gate pass/fail evaluation
4. Logs validation results to history

Author: Claude Code (Week 50 Day 1)
Date: 2025-11-24
"""

from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.quality_gate_config import (
    QualityGateConfig,
    QualityCategoryConfig,
    QualityWorkflowRules,
    QualityConfigHistory,
    ChangeType,
    EntityType
)
from app.services.validation_pipeline_service import (
    ValidationConfig,
    ValidationPhase,
    ValidationResult
)

logger = logging.getLogger(__name__)


# ============================================================================
# WORK TYPE TO VALIDATION PHASE MAPPING
# ============================================================================

WORK_TYPE_PHASES: Dict[str, List[ValidationPhase]] = {
    "NEW_FEATURE": [
        ValidationPhase.LINTING,
        ValidationPhase.TYPE_CHECK,
        ValidationPhase.STYLE,
        ValidationPhase.UNIT_TESTS,
        ValidationPhase.E2E_TESTS
    ],
    "MAINTENANCE": [
        ValidationPhase.LINTING,
        ValidationPhase.TYPE_CHECK,
        ValidationPhase.UNIT_TESTS
    ],
    "BUG": [
        ValidationPhase.LINTING,
        ValidationPhase.UNIT_TESTS,
        ValidationPhase.E2E_TESTS
    ],
    "QUALITY_AUDIT": [
        ValidationPhase.LINTING,
        ValidationPhase.TYPE_CHECK,
        ValidationPhase.STYLE
    ],
    "MIGRATION": [
        ValidationPhase.E2E_TESTS
    ],
    "REFACTORING": [
        ValidationPhase.LINTING,
        ValidationPhase.TYPE_CHECK,
        ValidationPhase.STYLE,
        ValidationPhase.UNIT_TESTS
    ],
    "DOCUMENTATION": [
        ValidationPhase.LINTING
    ],
    "HOTFIX": [
        ValidationPhase.LINTING,
        ValidationPhase.UNIT_TESTS
    ]
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class QualityGateResult:
    """Result of quality gate evaluation"""
    passed: bool
    workflow_type: str
    blocking_issues: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    coverage_met: bool
    coverage_actual: Optional[float]
    coverage_required: int
    validation_result: Optional[ValidationResult]
    gate_config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "workflow_type": self.workflow_type,
            "blocking_issues": self.blocking_issues,
            "blocking_count": len(self.blocking_issues),
            "warnings": self.warnings,
            "warning_count": len(self.warnings),
            "coverage": {
                "met": self.coverage_met,
                "actual": self.coverage_actual,
                "required": self.coverage_required
            },
            "gate_config": self.gate_config
        }


# ============================================================================
# SERVICE CLASS
# ============================================================================

class QualityGateIntegrationService:
    """
    Integrates Quality Gates Configuration with Validation Pipeline.

    Usage:
        service = QualityGateIntegrationService(db_session)

        # Get validation config for a workflow
        config = await service.get_validation_config("NEW_FEATURE")

        # Evaluate gate pass/fail
        result = await service.evaluate_gate("NEW_FEATURE", validation_result)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._config_cache: Optional[QualityGateConfig] = None
        self._workflow_rules_cache: Dict[str, QualityWorkflowRules] = {}

    async def get_active_config(self) -> Optional[QualityGateConfig]:
        """Get the active quality gate configuration"""
        if self._config_cache:
            return self._config_cache

        result = await self.db.execute(
            select(QualityGateConfig)
            .options(
                selectinload(QualityGateConfig.categories),
                selectinload(QualityGateConfig.workflow_rules),
                selectinload(QualityGateConfig.checks)
            )
            .where(QualityGateConfig.is_active == True)
            .limit(1)
        )
        config = result.scalar_one_or_none()
        self._config_cache = config
        return config

    async def get_workflow_rules(self, workflow_type: str) -> Optional[QualityWorkflowRules]:
        """Get workflow rules for a specific workflow type"""
        if workflow_type in self._workflow_rules_cache:
            return self._workflow_rules_cache[workflow_type]

        config = await self.get_active_config()
        if not config:
            return None

        for rule in config.workflow_rules:
            if rule.workflow_type == workflow_type:
                self._workflow_rules_cache[workflow_type] = rule
                return rule

        return None

    async def get_validation_config(self, workflow_type: str) -> ValidationConfig:
        """
        Convert workflow rules to ValidationConfig for the validation pipeline.

        Args:
            workflow_type: e.g., "NEW_FEATURE", "BUG", "MAINTENANCE"

        Returns:
            ValidationConfig with rules from quality gate config
        """
        rules = await self.get_workflow_rules(workflow_type)

        # Get phases for this workflow type
        phases = WORK_TYPE_PHASES.get(workflow_type, [ValidationPhase.LINTING])

        if rules:
            # Add E2E if required
            if rules.e2e_required and ValidationPhase.E2E_TESTS not in phases:
                phases.append(ValidationPhase.E2E_TESTS)

            return ValidationConfig(
                phases=phases,
                max_iterations=rules.max_iterations,
                stop_on_first_failure=rules.stop_on_first_failure,
                required_coverage=rules.required_coverage,
                regression_test_required=rules.regression_required
            )

        # Default config if no rules found
        return ValidationConfig(
            phases=phases,
            max_iterations=3,
            stop_on_first_failure=True,
            required_coverage=80
        )

    async def evaluate_gate(
        self,
        workflow_type: str,
        validation_result: ValidationResult
    ) -> QualityGateResult:
        """
        Evaluate if validation result passes the quality gate.

        Args:
            workflow_type: The workflow type being validated
            validation_result: Result from validation pipeline

        Returns:
            QualityGateResult with pass/fail and details
        """
        rules = await self.get_workflow_rules(workflow_type)
        blocking_issues = []
        warnings = []

        if not rules:
            # No rules configured - use defaults
            rules_dict = {
                "blocking_severities": ["critical"],
                "required_coverage": 80,
                "e2e_required": False,
                "regression_required": False
            }
        else:
            rules_dict = {
                "blocking_severities": rules.blocking_severities or ["critical"],
                "required_coverage": rules.required_coverage,
                "e2e_required": rules.e2e_required,
                "regression_required": rules.regression_required
            }

        blocking_severities = set(rules_dict["blocking_severities"])

        # Check each phase result for blocking issues
        for phase_result in validation_result.phases:
            for error in phase_result.errors:
                if error.severity in blocking_severities:
                    blocking_issues.append({
                        "phase": phase_result.phase.value,
                        "message": error.message,
                        "severity": error.severity,
                        "file": error.file,
                        "line": error.line
                    })
                else:
                    warnings.append({
                        "phase": phase_result.phase.value,
                        "message": error.message,
                        "severity": error.severity,
                        "file": error.file,
                        "line": error.line
                    })

        # Check coverage requirement
        coverage_met = True
        coverage_actual = validation_result.coverage_percent
        coverage_required = rules_dict["required_coverage"]

        if coverage_actual is not None and coverage_required > 0:
            if coverage_actual < coverage_required:
                coverage_met = False
                blocking_issues.append({
                    "phase": "coverage",
                    "message": f"Coverage {coverage_actual:.1f}% below required {coverage_required}%",
                    "severity": "critical",
                    "file": None,
                    "line": None
                })

        # Check E2E requirement
        if rules_dict["e2e_required"]:
            e2e_passed = any(
                p.phase == ValidationPhase.E2E_TESTS and p.passed
                for p in validation_result.phases
            )
            if not e2e_passed:
                blocking_issues.append({
                    "phase": "e2e",
                    "message": "E2E tests required but did not pass",
                    "severity": "critical",
                    "file": None,
                    "line": None
                })

        # Determine final pass/fail
        passed = len(blocking_issues) == 0 and validation_result.success

        return QualityGateResult(
            passed=passed,
            workflow_type=workflow_type,
            blocking_issues=blocking_issues,
            warnings=warnings,
            coverage_met=coverage_met,
            coverage_actual=coverage_actual,
            coverage_required=coverage_required,
            validation_result=validation_result,
            gate_config=rules_dict
        )

    async def log_gate_result(
        self,
        workflow_type: str,
        gate_result: QualityGateResult,
        task_id: Optional[str] = None
    ) -> None:
        """Log the gate result to configuration history"""
        config = await self.get_active_config()
        if not config:
            return

        history_entry = QualityConfigHistory(
            config_id=config.id,
            change_type=ChangeType.WORKFLOW_UPDATE.value,
            entity_type=EntityType.WORKFLOW.value,
            entity_id=workflow_type,
            old_value=None,
            new_value={
                "task_id": task_id,
                "passed": gate_result.passed,
                "blocking_count": len(gate_result.blocking_issues),
                "coverage_actual": gate_result.coverage_actual,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            comment=f"Gate {'PASSED' if gate_result.passed else 'FAILED'} for {workflow_type}"
        )

        self.db.add(history_entry)
        await self.db.commit()

    def clear_cache(self) -> None:
        """Clear the config cache (call after config updates)"""
        self._config_cache = None
        self._workflow_rules_cache.clear()

    async def get_coding_principles_rules(
        self,
        tech_stacks: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get coding principles rules for quality gate checks.

        Week 59+: Loads NASA Power of 10 adapted rules from .standards/stacks/
        These rules are enforced by Quinn during code review.

        Args:
            tech_stacks: List of tech stacks (e.g., ["python", "typescript"])

        Returns:
            List of rule definitions with check_id, rule, threshold, severity
        """
        from app.services.standards_loader_service import get_standards_loader

        loader = get_standards_loader()
        return loader.get_quality_gate_rules(tech_stacks)

    async def evaluate_coding_principles(
        self,
        tech_stacks: List[str],
        code_analysis_result: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Evaluate code against NASA Power of 10 coding principles.

        Args:
            tech_stacks: Project tech stacks
            code_analysis_result: Analysis result with metrics like:
                - max_nesting_depth: int
                - unbounded_loops: int
                - max_function_lines: int
                - assertion_count: int
                - global_variable_count: int
                - unchecked_returns: int

        Returns:
            Tuple of (blocking_issues, warnings)
        """
        rules = await self.get_coding_principles_rules(tech_stacks)
        blocking_issues = []
        warnings = []

        metrics = code_analysis_result.get("metrics", {})

        for rule in rules:
            check_id = rule.get("check_id", "")
            threshold_str = rule.get("threshold", "")
            severity = rule.get("severity", "medium")

            # Parse threshold (e.g., "3", "60 lines", "0", "Warn")
            if threshold_str.lower() in ["warn", "warning"]:
                threshold = None  # Warning only
            else:
                threshold = self._parse_threshold(threshold_str)

            # Match check ID to metric
            violation = self._check_principle_violation(
                check_id, metrics, threshold
            )

            if violation:
                issue = {
                    "phase": "coding_principles",
                    "check_id": check_id,
                    "rule": rule.get("rule", ""),
                    "message": violation["message"],
                    "severity": severity,
                    "actual_value": violation.get("actual"),
                    "threshold": threshold,
                    "stack": rule.get("stack", ""),
                    "file": violation.get("file"),
                    "line": violation.get("line")
                }

                if severity in ["critical", "high"]:
                    blocking_issues.append(issue)
                else:
                    warnings.append(issue)

        return blocking_issues, warnings

    def _parse_threshold(self, threshold_str: str) -> Optional[int]:
        """Parse threshold string to integer value."""
        if not threshold_str:
            return None

        # Extract number from string like "3", "60 lines", "0"
        import re
        match = re.search(r'\d+', str(threshold_str))
        if match:
            return int(match.group())
        return None

    def _check_principle_violation(
        self,
        check_id: str,
        metrics: Dict[str, Any],
        threshold: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a coding principle is violated.

        Returns violation dict if violated, None otherwise.
        """
        # Map check IDs to metrics
        check_mapping = {
            # Universal NASA rules (all stacks)
            "P1": ("max_nesting_depth", "Max nesting depth {actual} exceeds limit {threshold}"),
            "P2": ("unbounded_loops", "Found {actual} unbounded loops"),
            "P3": ("max_function_lines", "Function length {actual} lines exceeds {threshold}"),
            "P4": ("assertion_density", "Assertion density too low: {actual}%"),
            "P5": ("global_variables", "Found {actual} global/module-level variables"),
            "P7": ("linter_errors", "Found {actual} linter errors"),

            # Python specific
            "PY-P1": ("py_max_nesting", "Nesting depth {actual} exceeds {threshold}"),
            "PY-P2": ("py_unbounded_while", "Found {actual} unbounded while loops"),
            "PY-P4": ("py_assert_count", "Missing assertions in critical functions"),
            "PY-P7": ("py_type_errors", "Found {actual} type errors"),

            # TypeScript/JavaScript
            "TS-P1": ("ts_max_nesting", "Nesting depth {actual} exceeds {threshold}"),
            "TS-P2": ("ts_unbounded_loops", "Found {actual} unbounded loops without guards"),
            "TS-P4": ("ts_strict_violations", "Found {actual} strict mode violations"),
            "TS-P7": ("ts_eslint_errors", "Found {actual} ESLint errors"),

            # C# specific
            "CS-P1": ("cs_max_nesting", "Nesting depth {actual} exceeds {threshold}"),
            "CS-P4": ("cs_null_checks", "Missing null checks: {actual}"),
            "CS-P5": ("cs_static_fields", "Found {actual} mutable static fields"),

            # Java specific
            "JV-P1": ("java_max_nesting", "Nesting depth {actual} exceeds {threshold}"),
            "JV-P4": ("java_npe_risk", "NPE risk in {actual} locations"),
            "JV-OPT": ("java_optional_get", "Found {actual} unchecked Optional.get() calls"),

            # Go specific
            "GO-P1": ("go_max_nesting", "Nesting depth {actual} exceeds {threshold}"),
            "GO-P2": ("go_unbounded_for", "Found {actual} unbounded for loops"),
            "GO-P4": ("go_unchecked_err", "Found {actual} unchecked error returns"),
            "GO-CTX": ("go_ctx_missing", "Context not propagated in {actual} functions"),

            # React specific
            "RCT-HOOK": ("react_hook_order", "Hook order violations: {actual}"),
            "RCT-P2": ("react_missing_cleanup", "Missing effect cleanup: {actual}"),
            "RCT-KEY": ("react_missing_keys", "Missing keys in lists: {actual}"),

            # Vue specific
            "VUE-P1": ("vue_template_complexity", "Template complexity too high: {actual}"),
            "VUE-PERF": ("vue_vfor_without_key", "v-for without :key: {actual}"),

            # Angular specific
            "ANG-P1": ("angular_template_nesting", "Template nesting {actual} exceeds {threshold}"),
            "ANG-RX": ("angular_rx_no_unsubscribe", "RxJS without unsubscribe: {actual}"),
        }

        if check_id not in check_mapping:
            return None

        metric_key, message_template = check_mapping[check_id]
        actual = metrics.get(metric_key)

        if actual is None:
            return None

        # Check violation
        if threshold is not None:
            if actual > threshold:
                return {
                    "message": message_template.format(actual=actual, threshold=threshold),
                    "actual": actual
                }
        elif actual > 0:
            # For "0" threshold checks
            return {
                "message": message_template.format(actual=actual, threshold=0),
                "actual": actual
            }

        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_validation_config_for_workflow(
    db: AsyncSession,
    workflow_type: str
) -> ValidationConfig:
    """
    Convenience function to get validation config for a workflow type.

    Usage:
        config = await get_validation_config_for_workflow(db, "NEW_FEATURE")
        result = await validator.validate(code, config)
    """
    service = QualityGateIntegrationService(db)
    return await service.get_validation_config(workflow_type)


async def evaluate_quality_gate(
    db: AsyncSession,
    workflow_type: str,
    validation_result: ValidationResult
) -> QualityGateResult:
    """
    Convenience function to evaluate a quality gate.

    Usage:
        result = await evaluate_quality_gate(db, "BUG", validation_result)
        if result.passed:
            # proceed with deployment
        else:
            # handle blocking issues
    """
    service = QualityGateIntegrationService(db)
    return await service.evaluate_gate(workflow_type, validation_result)


async def evaluate_coding_principles(
    db: AsyncSession,
    tech_stacks: List[str],
    code_analysis_result: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convenience function to evaluate coding principles.

    Week 59+: NASA Power of 10 adapted rules loaded from .standards/stacks/

    Usage:
        blocking, warnings = await evaluate_coding_principles(
            db,
            ["python", "typescript"],
            {"metrics": {"max_nesting_depth": 4, "unbounded_loops": 2}}
        )

        if blocking:
            print(f"Blocking issues: {len(blocking)}")
            for issue in blocking:
                print(f"  [{issue['check_id']}] {issue['message']}")

    Args:
        db: Database session
        tech_stacks: List of tech stacks (e.g., ["python", "typescript"])
        code_analysis_result: Dict with "metrics" key containing analysis metrics

    Returns:
        Tuple of (blocking_issues, warnings)
    """
    service = QualityGateIntegrationService(db)
    return await service.evaluate_coding_principles(tech_stacks, code_analysis_result)


def get_coding_principles_rules_sync(tech_stacks: List[str]) -> List[Dict[str, Any]]:
    """
    Synchronous function to get coding principles rules.

    Useful for non-async contexts like report generation.

    Usage:
        rules = get_coding_principles_rules_sync(["python"])
        for rule in rules:
            print(f"{rule['check_id']}: {rule['rule']} (severity: {rule['severity']})")

    Args:
        tech_stacks: List of tech stacks

    Returns:
        List of rule definitions
    """
    from app.services.standards_loader_service import get_standards_loader
    loader = get_standards_loader()
    return loader.get_quality_gate_rules(tech_stacks)
