"""
Quality Scoring Rules for Confucius Orchestrator.

Domain-specific rules for evaluating agent output quality.
Each rule evaluates a specific dimension of quality and contributes
to the overall quality score.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging
import re

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Dimensions of quality evaluation."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    ACTIONABILITY = "actionability"
    CONSISTENCY = "consistency"
    CLARITY = "clarity"
    COVERAGE = "coverage"


class Severity(str, Enum):
    """Severity levels for quality issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RuleViolation:
    """A single rule violation."""
    rule_id: str
    dimension: QualityDimension
    severity: Severity
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""
    rule_id: str
    dimension: QualityDimension
    passed: bool
    score: float  # 0.0 - 1.0
    weight: float
    violations: List[RuleViolation] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_score(self) -> float:
        """Score weighted by rule importance."""
        return self.score * self.weight


@dataclass
class DomainRuleSet:
    """Collection of rules for a specific domain."""
    domain: str
    rules: List["QualityRule"]
    default_threshold: float = 0.85

    def get_total_weight(self) -> float:
        """Get total weight of all rules."""
        return sum(r.weight for r in self.rules)


class QualityRule(ABC):
    """
    Abstract base class for quality rules.

    Each rule evaluates a specific aspect of quality and returns
    a score between 0.0 and 1.0.
    """

    def __init__(
        self,
        rule_id: str,
        dimension: QualityDimension,
        weight: float = 1.0,
        description: str = "",
    ):
        self.rule_id = rule_id
        self.dimension = dimension
        self.weight = weight
        self.description = description

    @abstractmethod
    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        """
        Evaluate the output against this rule.

        Args:
            output: The agent output to evaluate
            context: Additional context for evaluation

        Returns:
            RuleResult with score and violations
        """
        pass

    def _create_result(
        self,
        passed: bool,
        score: float,
        violations: List[RuleViolation] = None,
        details: Dict[str, Any] = None,
    ) -> RuleResult:
        """Helper to create RuleResult."""
        return RuleResult(
            rule_id=self.rule_id,
            dimension=self.dimension,
            passed=passed,
            score=score,
            weight=self.weight,
            violations=violations or [],
            details=details or {},
        )


# =============================================================================
# GENERIC RULES (Apply to all domains)
# =============================================================================

class CompletenessRule(QualityRule):
    """Check if output contains all required fields."""

    def __init__(self, required_fields: List[str], weight: float = 1.5):
        super().__init__(
            rule_id="completeness_required_fields",
            dimension=QualityDimension.COMPLETENESS,
            weight=weight,
            description="Checks for presence of required output fields",
        )
        self.required_fields = required_fields

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        violations = []
        missing = []

        for field in self.required_fields:
            if field not in output or output[field] is None:
                missing.append(field)
                violations.append(RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.ERROR,
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Ensure the output includes '{field}'",
                ))
            elif isinstance(output[field], (list, dict, str)) and len(output[field]) == 0:
                violations.append(RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.WARNING,
                    message=f"Field '{field}' is empty",
                    suggestion=f"Provide content for '{field}'",
                ))

        present = len(self.required_fields) - len(missing)
        score = present / len(self.required_fields) if self.required_fields else 1.0

        return self._create_result(
            passed=len(missing) == 0,
            score=score,
            violations=violations,
            details={"missing_fields": missing, "present_fields": present},
        )


class NonEmptyOutputRule(QualityRule):
    """Check that output is not empty or trivial."""

    def __init__(self, min_content_length: int = 10, weight: float = 1.0):
        super().__init__(
            rule_id="non_empty_output",
            dimension=QualityDimension.COMPLETENESS,
            weight=weight,
            description="Ensures output contains meaningful content",
        )
        self.min_content_length = min_content_length

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        # Check if output has meaningful content
        content_str = str(output)
        content_length = len(content_str)

        if content_length < self.min_content_length:
            return self._create_result(
                passed=False,
                score=0.0,
                violations=[RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.CRITICAL,
                    message=f"Output too short ({content_length} chars, min {self.min_content_length})",
                    suggestion="Provide more detailed output",
                )],
                details={"content_length": content_length},
            )

        # Scale score based on content richness
        score = min(1.0, content_length / (self.min_content_length * 10))

        return self._create_result(
            passed=True,
            score=score,
            details={"content_length": content_length},
        )


class SuccessStatusRule(QualityRule):
    """Check that the operation succeeded."""

    def __init__(self, weight: float = 2.0):
        super().__init__(
            rule_id="success_status",
            dimension=QualityDimension.ACCURACY,
            weight=weight,
            description="Checks if the operation completed successfully",
        )

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        success = output.get("success", False)
        error = output.get("error")

        if not success:
            return self._create_result(
                passed=False,
                score=0.0,
                violations=[RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.CRITICAL,
                    message=f"Operation failed: {error or 'Unknown error'}",
                    suggestion="Fix the underlying error and retry",
                )],
                details={"error": error},
            )

        return self._create_result(
            passed=True,
            score=1.0,
            details={"success": True},
        )


class NoErrorsRule(QualityRule):
    """Check for absence of errors in output."""

    def __init__(self, weight: float = 1.5):
        super().__init__(
            rule_id="no_errors",
            dimension=QualityDimension.ACCURACY,
            weight=weight,
            description="Checks that output contains no errors",
        )

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        violations = []

        # Check common error indicators
        error = output.get("error")
        errors = output.get("errors", [])

        if error:
            violations.append(RuleViolation(
                rule_id=self.rule_id,
                dimension=self.dimension,
                severity=Severity.ERROR,
                message=f"Error in output: {error}",
            ))

        for e in errors:
            violations.append(RuleViolation(
                rule_id=self.rule_id,
                dimension=self.dimension,
                severity=Severity.ERROR,
                message=str(e) if not isinstance(e, dict) else e.get("message", str(e)),
            ))

        score = 1.0 if not violations else 0.0

        return self._create_result(
            passed=len(violations) == 0,
            score=score,
            violations=violations,
        )


# =============================================================================
# ARCHITECTURE RULES (Felix domain)
# =============================================================================

class ArchitectureDecisionRule(QualityRule):
    """Check that architecture decisions are documented."""

    def __init__(self, min_decisions: int = 1, weight: float = 1.2):
        super().__init__(
            rule_id="architecture_decisions",
            dimension=QualityDimension.COMPLETENESS,
            weight=weight,
            description="Ensures architecture decisions are documented",
        )
        self.min_decisions = min_decisions

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        decisions = output.get("architecture_decisions", [])
        decisions_count = len(decisions)

        if decisions_count < self.min_decisions:
            return self._create_result(
                passed=False,
                score=decisions_count / self.min_decisions,
                violations=[RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.WARNING,
                    message=f"Only {decisions_count} decisions, expected at least {self.min_decisions}",
                    suggestion="Document key architecture decisions",
                )],
                details={"decisions_count": decisions_count},
            )

        return self._create_result(
            passed=True,
            score=1.0,
            details={"decisions_count": decisions_count},
        )


class ComponentMappingRule(QualityRule):
    """Check that legacy-to-target component mapping exists."""

    def __init__(self, weight: float = 1.3):
        super().__init__(
            rule_id="component_mapping",
            dimension=QualityDimension.COVERAGE,
            weight=weight,
            description="Ensures component mapping is complete",
        )

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        components = output.get("components", {})
        legacy = components.get("legacy", [])
        target = components.get("target", [])
        mappings = components.get("mappings", [])

        violations = []

        if not legacy and not target:
            violations.append(RuleViolation(
                rule_id=self.rule_id,
                dimension=self.dimension,
                severity=Severity.WARNING,
                message="No components identified",
                suggestion="Identify legacy and target components",
            ))

        if legacy and not mappings:
            violations.append(RuleViolation(
                rule_id=self.rule_id,
                dimension=self.dimension,
                severity=Severity.WARNING,
                message="Legacy components exist but no mappings defined",
                suggestion="Map legacy components to target architecture",
            ))

        score = 1.0 if not violations else 0.5

        return self._create_result(
            passed=len(violations) == 0,
            score=score,
            violations=violations,
            details={
                "legacy_count": len(legacy),
                "target_count": len(target),
                "mappings_count": len(mappings),
            },
        )


# =============================================================================
# QUALITY RULES (Quinn domain)
# =============================================================================

class CriticalIssuesRule(QualityRule):
    """Check for absence of critical security/quality issues."""

    def __init__(self, weight: float = 2.5):
        super().__init__(
            rule_id="no_critical_issues",
            dimension=QualityDimension.ACCURACY,
            weight=weight,
            description="Ensures no critical issues are present",
        )

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        security_issues = output.get("security_issues", [])
        findings = output.get("findings", [])

        critical_count = 0
        violations = []

        for issue in security_issues:
            severity = issue.get("severity", "").lower()
            if severity == "critical":
                critical_count += 1
                violations.append(RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.CRITICAL,
                    message=f"Critical security issue: {issue.get('description', 'Unknown')}",
                    location=issue.get("location"),
                ))

        for finding in findings:
            severity = finding.get("severity", "").lower()
            if severity == "critical":
                critical_count += 1
                violations.append(RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.CRITICAL,
                    message=f"Critical finding: {finding.get('message', 'Unknown')}",
                    location=finding.get("location"),
                ))

        return self._create_result(
            passed=critical_count == 0,
            score=1.0 if critical_count == 0 else 0.0,
            violations=violations,
            details={"critical_count": critical_count},
        )


class QualityScoreThresholdRule(QualityRule):
    """Check that quality score meets threshold."""

    def __init__(self, threshold: float = 0.85, weight: float = 1.5):
        super().__init__(
            rule_id="quality_score_threshold",
            dimension=QualityDimension.ACCURACY,
            weight=weight,
            description=f"Quality score must be >= {threshold}",
        )
        self.threshold = threshold

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        quality_score = output.get("quality_score", 0.0)

        passed = quality_score >= self.threshold

        if not passed:
            return self._create_result(
                passed=False,
                score=quality_score / self.threshold,
                violations=[RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.WARNING,
                    message=f"Quality score {quality_score:.2f} below threshold {self.threshold}",
                    suggestion="Address quality findings to improve score",
                )],
                details={"quality_score": quality_score, "threshold": self.threshold},
            )

        return self._create_result(
            passed=True,
            score=1.0,
            details={"quality_score": quality_score},
        )


# =============================================================================
# ESTIMATION RULES (Eliza domain)
# =============================================================================

class EstimationConfidenceRule(QualityRule):
    """Check that estimation has sufficient confidence."""

    def __init__(self, min_confidence: float = 0.6, weight: float = 1.2):
        super().__init__(
            rule_id="estimation_confidence",
            dimension=QualityDimension.ACCURACY,
            weight=weight,
            description=f"Estimation confidence must be >= {min_confidence}",
        )
        self.min_confidence = min_confidence

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        confidence = output.get("confidence", 0.0)

        passed = confidence >= self.min_confidence

        if not passed:
            return self._create_result(
                passed=False,
                score=confidence / self.min_confidence,
                violations=[RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.WARNING,
                    message=f"Confidence {confidence:.2f} below minimum {self.min_confidence}",
                    suggestion="Gather more information to improve confidence",
                )],
                details={"confidence": confidence},
            )

        return self._create_result(
            passed=True,
            score=1.0,
            details={"confidence": confidence},
        )


class WorkTypeValidRule(QualityRule):
    """Check that work type is valid for FP methodology."""

    def __init__(self, weight: float = 1.0):
        super().__init__(
            rule_id="work_type_valid",
            dimension=QualityDimension.RELEVANCE,
            weight=weight,
            description="Work type must be FP-applicable",
        )

    def evaluate(self, output: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        work_type = output.get("work_type", "unknown")
        fp_applicable = output.get("fp_applicable", True)

        if work_type == "unknown":
            return self._create_result(
                passed=False,
                score=0.5,
                violations=[RuleViolation(
                    rule_id=self.rule_id,
                    dimension=self.dimension,
                    severity=Severity.WARNING,
                    message="Work type not determined",
                    suggestion="Classify the work type (development, enhancement, etc.)",
                )],
            )

        if not fp_applicable:
            return self._create_result(
                passed=True,  # Not a violation, just informative
                score=0.8,
                details={
                    "work_type": work_type,
                    "fp_applicable": False,
                    "note": "FP not applicable, use alternative method",
                },
            )

        return self._create_result(
            passed=True,
            score=1.0,
            details={"work_type": work_type, "fp_applicable": True},
        )


# =============================================================================
# DOMAIN RULE SETS
# =============================================================================

def get_general_rules() -> List[QualityRule]:
    """Get rules applicable to all domains."""
    return [
        SuccessStatusRule(),
        NoErrorsRule(),
        NonEmptyOutputRule(),
    ]


def get_architecture_rules() -> List[QualityRule]:
    """Get rules for Felix (architecture) domain."""
    return get_general_rules() + [
        ArchitectureDecisionRule(),
        ComponentMappingRule(),
        CompletenessRule(["architecture_decisions", "recommendations", "risks"]),
    ]


def get_quality_rules() -> List[QualityRule]:
    """Get rules for Quinn (quality) domain."""
    return get_general_rules() + [
        CriticalIssuesRule(),
        QualityScoreThresholdRule(),
        CompletenessRule(["findings", "quality_score"]),
    ]


def get_estimation_rules() -> List[QualityRule]:
    """Get rules for Eliza (estimation) domain."""
    return get_general_rules() + [
        EstimationConfidenceRule(),
        WorkTypeValidRule(),
        CompletenessRule(["function_points", "effort_hours"]),
    ]


def get_documentation_rules() -> List[QualityRule]:
    """Get rules for Diana (documentation) domain."""
    return get_general_rules() + [
        CompletenessRule(["content", "format"]),
        NonEmptyOutputRule(min_content_length=100),
    ]


def get_testing_rules() -> List[QualityRule]:
    """Get rules for Tessa (testing) domain."""
    return get_general_rules() + [
        CompletenessRule(["tests_generated", "coverage_percentage"]),
    ]


# Domain rule set mapping
DOMAIN_RULE_SETS: Dict[str, DomainRuleSet] = {
    "architecture": DomainRuleSet(
        domain="architecture",
        rules=get_architecture_rules(),
        default_threshold=0.85,
    ),
    "quality": DomainRuleSet(
        domain="quality",
        rules=get_quality_rules(),
        default_threshold=0.90,  # Higher threshold for quality
    ),
    "estimation": DomainRuleSet(
        domain="estimation",
        rules=get_estimation_rules(),
        default_threshold=0.80,
    ),
    "documentation": DomainRuleSet(
        domain="documentation",
        rules=get_documentation_rules(),
        default_threshold=0.75,
    ),
    "testing": DomainRuleSet(
        domain="testing",
        rules=get_testing_rules(),
        default_threshold=0.80,
    ),
    "general": DomainRuleSet(
        domain="general",
        rules=get_general_rules(),
        default_threshold=0.85,
    ),
}


def get_rules_for_domain(domain: str) -> DomainRuleSet:
    """
    Get rule set for a specific domain.

    Args:
        domain: Domain name (architecture, quality, estimation, etc.)

    Returns:
        DomainRuleSet with applicable rules
    """
    return DOMAIN_RULE_SETS.get(domain.lower(), DOMAIN_RULE_SETS["general"])
