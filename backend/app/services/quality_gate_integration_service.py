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

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
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
                "timestamp": datetime.utcnow().isoformat()
            },
            comment=f"Gate {'PASSED' if gate_result.passed else 'FAILED'} for {workflow_type}"
        )

        self.db.add(history_entry)
        await self.db.commit()

    def clear_cache(self) -> None:
        """Clear the config cache (call after config updates)"""
        self._config_cache = None
        self._workflow_rules_cache.clear()


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
