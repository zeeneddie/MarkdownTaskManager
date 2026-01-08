# Quality Gate Stability Integration
# Integrates Resource Leak Detection with Quality Gate evaluation
#
# Week 145-146: Adds stability analysis as a quality gate check
# for legacy code migration workflows.
#
# Provides:
# 1. Stability thresholds for quality gate evaluation
# 2. Blocking conditions based on critical/high findings
# 3. Integration with existing quality gate infrastructure

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .brown_paper_integration import (
    BrownPaperStabilityIntegration,
    StabilityIntegrationResult,
    get_brown_paper_stability_integration,
)
from .types import SeverityLevel, StabilityCategory

logger = logging.getLogger(__name__)


class StabilityGateStatus(Enum):
    """Status of stability gate evaluation."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StabilityThresholds:
    """Configurable thresholds for stability quality gate."""

    # Maximum allowed findings by severity
    max_critical: int = 0  # Critical findings block by default
    max_high: int = 5
    max_medium: int = 20
    max_low: int = 50

    # Minimum stability score (0-100)
    min_score: int = 60

    # Maximum risk level allowed
    max_risk_level: str = "medium"  # low, medium, high, critical

    # Category-specific limits (optional)
    category_limits: Dict[str, int] = field(default_factory=dict)

    # Blocking categories (findings in these categories always block)
    blocking_categories: List[str] = field(
        default_factory=lambda: [
            StabilityCategory.SQL_PERFORMANCE.value,  # SQL injection risk
            StabilityCategory.EXCEPTION_HANDLING.value,  # Error swallowing
        ]
    )


@dataclass
class StabilityGateResult:
    """Result of stability quality gate evaluation."""

    status: StabilityGateStatus
    stability_result: Optional[StabilityIntegrationResult] = None

    # Blocking findings
    blocking_issues: List[Dict[str, Any]] = field(default_factory=list)

    # Non-blocking warnings
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    # Summary metrics
    stability_score: int = 100
    risk_level: str = "low"

    # Threshold checks
    critical_exceeded: bool = False
    high_exceeded: bool = False
    score_below_threshold: bool = False
    risk_level_exceeded: bool = False

    # Message explaining result
    message: str = ""

    # Analysis metadata
    evaluated_at: Optional[datetime] = None
    evaluation_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "passed": self.status == StabilityGateStatus.PASSED,
            "stability_score": self.stability_score,
            "risk_level": self.risk_level,
            "blocking_issues": self.blocking_issues,
            "blocking_count": len(self.blocking_issues),
            "warnings": self.warnings,
            "warning_count": len(self.warnings),
            "threshold_checks": {
                "critical_exceeded": self.critical_exceeded,
                "high_exceeded": self.high_exceeded,
                "score_below_threshold": self.score_below_threshold,
                "risk_level_exceeded": self.risk_level_exceeded,
            },
            "message": self.message,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "evaluation_time_ms": self.evaluation_time_ms,
            "stability_result": (
                self.stability_result.to_dict() if self.stability_result else None
            ),
        }


# Default thresholds for different workflow types
WORKFLOW_STABILITY_THRESHOLDS: Dict[str, StabilityThresholds] = {
    "NEW_FEATURE": StabilityThresholds(
        max_critical=0,
        max_high=3,
        max_medium=15,
        min_score=70,
        max_risk_level="medium",
    ),
    "MIGRATION": StabilityThresholds(
        max_critical=2,  # Migration may have legacy issues
        max_high=10,
        max_medium=50,
        min_score=50,
        max_risk_level="high",
    ),
    "BUG": StabilityThresholds(
        max_critical=0,
        max_high=5,
        max_medium=20,
        min_score=60,
        max_risk_level="medium",
    ),
    "MAINTENANCE": StabilityThresholds(
        max_critical=1,
        max_high=8,
        max_medium=30,
        min_score=55,
        max_risk_level="high",
    ),
    "REFACTORING": StabilityThresholds(
        max_critical=0,
        max_high=3,
        max_medium=10,
        min_score=75,
        max_risk_level="low",
    ),
    "HOTFIX": StabilityThresholds(
        max_critical=0,
        max_high=2,
        max_medium=10,
        min_score=70,
        max_risk_level="medium",
    ),
    "DEFAULT": StabilityThresholds(),
}


class StabilityQualityGateService:
    """
    Evaluates stability analysis results against quality gate thresholds.

    Usage:
        service = StabilityQualityGateService()

        # Run analysis and evaluation together
        result = await service.evaluate_project(
            project_path="/path/to/project",
            project_name="LegacyApp",
            workflow_type="MIGRATION"
        )

        # Or evaluate existing stability result
        result = service.evaluate_stability_result(
            stability_result=existing_result,
            workflow_type="MIGRATION"
        )

        if result.status == StabilityGateStatus.PASSED:
            print("Quality gate passed!")
        else:
            print(f"Gate failed: {result.message}")
    """

    def __init__(self):
        """Initialize the quality gate service."""
        self._stability_integration = get_brown_paper_stability_integration()

    def get_thresholds(
        self,
        workflow_type: str,
        custom_thresholds: Optional[StabilityThresholds] = None
    ) -> StabilityThresholds:
        """Get thresholds for a workflow type."""
        if custom_thresholds:
            return custom_thresholds
        return WORKFLOW_STABILITY_THRESHOLDS.get(
            workflow_type,
            WORKFLOW_STABILITY_THRESHOLDS["DEFAULT"]
        )

    async def evaluate_project(
        self,
        project_path: str,
        project_name: str,
        workflow_type: str = "DEFAULT",
        project_id: int = 0,
        custom_thresholds: Optional[StabilityThresholds] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> StabilityGateResult:
        """
        Run stability analysis and evaluate against quality gate.

        Args:
            project_path: Root path of the project
            project_name: Name of the project
            workflow_type: Type of workflow (for threshold selection)
            project_id: Optional project ID
            custom_thresholds: Optional custom thresholds
            exclude_patterns: Patterns to exclude from analysis

        Returns:
            StabilityGateResult with pass/fail status
        """
        import time
        start_time = time.time()

        # Run stability analysis
        stability_result = await self._stability_integration.analyze_for_brown_paper(
            project_path=project_path,
            project_name=project_name,
            project_id=project_id,
            exclude_patterns=exclude_patterns,
        )

        # Evaluate against thresholds
        result = self.evaluate_stability_result(
            stability_result=stability_result,
            workflow_type=workflow_type,
            custom_thresholds=custom_thresholds,
        )

        result.evaluation_time_ms = int((time.time() - start_time) * 1000)
        result.evaluated_at = datetime.utcnow()

        return result

    def evaluate_stability_result(
        self,
        stability_result: StabilityIntegrationResult,
        workflow_type: str = "DEFAULT",
        custom_thresholds: Optional[StabilityThresholds] = None,
    ) -> StabilityGateResult:
        """
        Evaluate an existing stability result against thresholds.

        Args:
            stability_result: Result from stability analysis
            workflow_type: Type of workflow
            custom_thresholds: Optional custom thresholds

        Returns:
            StabilityGateResult with evaluation
        """
        thresholds = self.get_thresholds(workflow_type, custom_thresholds)

        blocking_issues = []
        warnings = []
        messages = []

        # Check critical findings
        critical_exceeded = stability_result.critical_count > thresholds.max_critical
        if critical_exceeded:
            blocking_issues.append({
                "type": "threshold_exceeded",
                "check": "critical_findings",
                "actual": stability_result.critical_count,
                "threshold": thresholds.max_critical,
                "message": f"Critical findings ({stability_result.critical_count}) exceed threshold ({thresholds.max_critical})",
            })
            messages.append(f"Critical findings exceeded: {stability_result.critical_count}/{thresholds.max_critical}")

        # Check high findings
        high_exceeded = stability_result.high_count > thresholds.max_high
        if high_exceeded:
            blocking_issues.append({
                "type": "threshold_exceeded",
                "check": "high_findings",
                "actual": stability_result.high_count,
                "threshold": thresholds.max_high,
                "message": f"High severity findings ({stability_result.high_count}) exceed threshold ({thresholds.max_high})",
            })
            messages.append(f"High findings exceeded: {stability_result.high_count}/{thresholds.max_high}")

        # Check medium findings (warning only)
        if stability_result.medium_count > thresholds.max_medium:
            warnings.append({
                "type": "threshold_exceeded",
                "check": "medium_findings",
                "actual": stability_result.medium_count,
                "threshold": thresholds.max_medium,
                "message": f"Medium severity findings ({stability_result.medium_count}) exceed threshold ({thresholds.max_medium})",
            })

        # Check stability score
        score_below_threshold = stability_result.stability_score < thresholds.min_score
        if score_below_threshold:
            blocking_issues.append({
                "type": "score_below_threshold",
                "check": "stability_score",
                "actual": stability_result.stability_score,
                "threshold": thresholds.min_score,
                "message": f"Stability score ({stability_result.stability_score}) below threshold ({thresholds.min_score})",
            })
            messages.append(f"Score below threshold: {stability_result.stability_score}/{thresholds.min_score}")

        # Check risk level
        risk_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        actual_risk = risk_levels.get(stability_result.risk_level, 0)
        max_risk = risk_levels.get(thresholds.max_risk_level, 1)
        risk_level_exceeded = actual_risk > max_risk

        if risk_level_exceeded:
            blocking_issues.append({
                "type": "risk_level_exceeded",
                "check": "risk_level",
                "actual": stability_result.risk_level,
                "threshold": thresholds.max_risk_level,
                "message": f"Risk level ({stability_result.risk_level}) exceeds maximum ({thresholds.max_risk_level})",
            })
            messages.append(f"Risk level exceeded: {stability_result.risk_level} > {thresholds.max_risk_level}")

        # Check blocking categories
        for category, count in stability_result.category_breakdown.items():
            if category in thresholds.blocking_categories and count > 0:
                blocking_issues.append({
                    "type": "blocking_category",
                    "check": "category",
                    "category": category,
                    "count": count,
                    "message": f"Findings in blocking category: {category} ({count} issues)",
                })
                messages.append(f"Blocking category: {category} ({count})")

        # Check category limits
        for category, limit in thresholds.category_limits.items():
            actual = stability_result.category_breakdown.get(category, 0)
            if actual > limit:
                blocking_issues.append({
                    "type": "category_limit_exceeded",
                    "check": "category_limit",
                    "category": category,
                    "actual": actual,
                    "threshold": limit,
                    "message": f"Category {category} findings ({actual}) exceed limit ({limit})",
                })
                messages.append(f"Category {category} exceeded: {actual}/{limit}")

        # Add top issues from analysis as warnings for visibility
        for issue in stability_result.top_issues[:5]:
            warnings.append({
                "type": "top_issue",
                "file": issue["file_path"],
                "line": issue["line_number"],
                "category": issue["category"],
                "severity": issue["severity"],
                "message": issue["description"],
            })

        # Determine final status
        if blocking_issues:
            status = StabilityGateStatus.FAILED
            message = f"Quality gate FAILED: {'; '.join(messages)}"
        elif warnings:
            status = StabilityGateStatus.WARNING
            message = f"Quality gate passed with warnings ({len(warnings)} warnings)"
        else:
            status = StabilityGateStatus.PASSED
            message = f"Quality gate passed (score: {stability_result.stability_score}, risk: {stability_result.risk_level})"

        return StabilityGateResult(
            status=status,
            stability_result=stability_result,
            blocking_issues=blocking_issues,
            warnings=warnings,
            stability_score=stability_result.stability_score,
            risk_level=stability_result.risk_level,
            critical_exceeded=critical_exceeded,
            high_exceeded=high_exceeded,
            score_below_threshold=score_below_threshold,
            risk_level_exceeded=risk_level_exceeded,
            message=message,
        )


# Module-level singleton
_gate_service_instance: Optional[StabilityQualityGateService] = None


def get_stability_quality_gate_service() -> StabilityQualityGateService:
    """Get or create the stability quality gate service singleton."""
    global _gate_service_instance
    if _gate_service_instance is None:
        _gate_service_instance = StabilityQualityGateService()
    return _gate_service_instance
