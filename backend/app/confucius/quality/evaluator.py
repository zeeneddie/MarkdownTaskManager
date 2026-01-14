"""
Quality Gate Evaluator for Confucius Orchestrator.

Evaluates agent output against domain-specific quality rules
and determines if output meets quality gates for the PIV loop.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .rules import (
    QualityRule,
    RuleResult,
    RuleViolation,
    DomainRuleSet,
    Severity,
    QualityDimension,
    get_rules_for_domain,
    DOMAIN_RULE_SETS,
)

logger = logging.getLogger(__name__)


class GateDecision(str, Enum):
    """Quality gate decision outcomes."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"  # Passed with warnings


@dataclass
class DimensionScore:
    """Score for a single quality dimension."""
    dimension: QualityDimension
    score: float
    weight_sum: float
    rule_count: int
    violations: List[RuleViolation] = field(default_factory=list)

    @property
    def weighted_average(self) -> float:
        """Weighted average score for this dimension."""
        return self.score / self.weight_sum if self.weight_sum > 0 else 0.0


@dataclass
class EvaluationResult:
    """Result of quality gate evaluation."""
    entry_id: str
    agent_name: str
    domain: str
    decision: GateDecision
    overall_score: float
    threshold: float
    passed_rules: int
    failed_rules: int
    total_rules: int
    dimension_scores: Dict[str, DimensionScore]
    all_violations: List[RuleViolation]
    critical_violations: List[RuleViolation]
    rule_results: List[RuleResult]
    iteration: int
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    feedback_for_retry: Optional[str] = None

    @property
    def pass_rate(self) -> float:
        """Percentage of rules passed."""
        return self.passed_rules / self.total_rules if self.total_rules > 0 else 0.0

    @property
    def has_critical(self) -> bool:
        """Check if there are critical violations."""
        return len(self.critical_violations) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entry_id": self.entry_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "decision": self.decision.value,
            "overall_score": round(self.overall_score, 3),
            "threshold": self.threshold,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "total_rules": self.total_rules,
            "pass_rate": round(self.pass_rate, 3),
            "has_critical": self.has_critical,
            "dimension_scores": {
                dim: {
                    "score": round(ds.score, 3),
                    "weighted_average": round(ds.weighted_average, 3),
                    "rule_count": ds.rule_count,
                    "violation_count": len(ds.violations),
                }
                for dim, ds in self.dimension_scores.items()
            },
            "violations": [v.to_dict() for v in self.all_violations],
            "critical_violations": [v.to_dict() for v in self.critical_violations],
            "iteration": self.iteration,
            "evaluated_at": self.evaluated_at.isoformat(),
            "feedback_for_retry": self.feedback_for_retry,
        }


class QualityGateEvaluator:
    """
    Evaluates agent output against quality gates.

    The evaluator runs domain-specific rules against agent output
    and produces an evaluation result with:
    - Overall quality score
    - Per-dimension scores
    - All violations found
    - Gate decision (pass/fail/warn)
    - Feedback for retry iterations

    Example:
    ```python
    evaluator = QualityGateEvaluator()
    result = evaluator.evaluate(
        output={"success": True, "function_points": 120},
        context={"domain": "estimation"},
        entry_id="task-123",
        agent_name="Eliza",
        iteration=1,
    )
    if result.decision == GateDecision.FAIL:
        print(f"Failed: {result.feedback_for_retry}")
    ```
    """

    def __init__(
        self,
        default_threshold: float = 0.85,
        warn_threshold: float = 0.90,
    ):
        """
        Initialize evaluator.

        Args:
            default_threshold: Minimum score to pass (default 0.85)
            warn_threshold: Score below which to warn (default 0.90)
        """
        self._default_threshold = default_threshold
        self._warn_threshold = warn_threshold
        self._custom_rules: Dict[str, List[QualityRule]] = {}

    def register_custom_rules(
        self,
        domain: str,
        rules: List[QualityRule],
    ) -> None:
        """
        Register custom rules for a domain.

        Args:
            domain: Domain to add rules to
            rules: List of custom rules
        """
        self._custom_rules[domain] = rules
        logger.info(f"Registered {len(rules)} custom rules for {domain}")

    def evaluate(
        self,
        output: Dict[str, Any],
        context: Dict[str, Any],
        entry_id: str,
        agent_name: str,
        iteration: int = 1,
        threshold_override: Optional[float] = None,
    ) -> EvaluationResult:
        """
        Evaluate output against quality gates.

        Args:
            output: Agent output to evaluate
            context: Context for evaluation
            entry_id: Task entry ID
            agent_name: Name of agent that produced output
            iteration: Current iteration number
            threshold_override: Override default threshold

        Returns:
            EvaluationResult with gate decision
        """
        # Determine domain
        domain = self._determine_domain(output, context, agent_name)

        # Get rules for domain
        rule_set = get_rules_for_domain(domain)
        rules = list(rule_set.rules)

        # Add custom rules if any
        if domain in self._custom_rules:
            rules.extend(self._custom_rules[domain])

        # Determine threshold
        threshold = threshold_override or rule_set.default_threshold

        # Evaluate all rules
        rule_results = self._evaluate_rules(rules, output, context)

        # Calculate scores
        overall_score = self._calculate_overall_score(rule_results)
        dimension_scores = self._calculate_dimension_scores(rule_results)

        # Collect violations
        all_violations = self._collect_violations(rule_results)
        critical_violations = [
            v for v in all_violations if v.severity == Severity.CRITICAL
        ]

        # Count passed/failed
        passed_rules = sum(1 for r in rule_results if r.passed)
        failed_rules = len(rule_results) - passed_rules

        # Make decision
        decision = self._make_decision(
            overall_score,
            threshold,
            critical_violations,
        )

        # Generate feedback for retry
        feedback = None
        if decision == GateDecision.FAIL:
            feedback = self._generate_feedback(
                all_violations,
                dimension_scores,
                overall_score,
                threshold,
            )

        logger.info(
            f"Evaluated {agent_name} output: "
            f"score={overall_score:.2f}, decision={decision.value}, "
            f"passed={passed_rules}/{len(rules)}"
        )

        return EvaluationResult(
            entry_id=entry_id,
            agent_name=agent_name,
            domain=domain,
            decision=decision,
            overall_score=overall_score,
            threshold=threshold,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            total_rules=len(rule_results),
            dimension_scores=dimension_scores,
            all_violations=all_violations,
            critical_violations=critical_violations,
            rule_results=rule_results,
            iteration=iteration,
            feedback_for_retry=feedback,
        )

    def _determine_domain(
        self,
        output: Dict[str, Any],
        context: Dict[str, Any],
        agent_name: str,
    ) -> str:
        """Determine domain from output, context, or agent name."""
        # Check explicit domain
        if "domain" in context:
            return context["domain"]

        # Map agent names to domains
        agent_domains = {
            "Felix": "architecture",
            "Quinn": "quality",
            "Eliza": "estimation",
            "Diana": "documentation",
            "Tessa": "testing",
            "Marcus": "maintenance",
            "Miguel": "metrics",
            "Peter": "product",
            "Paul": "planning",
            "Betty": "business",
            "Vicky": "design",
        }

        return agent_domains.get(agent_name, "general")

    def _evaluate_rules(
        self,
        rules: List[QualityRule],
        output: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[RuleResult]:
        """Evaluate all rules against output."""
        results = []

        for rule in rules:
            try:
                result = rule.evaluate(output, context)
                results.append(result)
            except Exception as e:
                logger.error(f"Rule {rule.rule_id} failed: {e}")
                # Create failed result for error
                results.append(RuleResult(
                    rule_id=rule.rule_id,
                    dimension=rule.dimension,
                    passed=False,
                    score=0.0,
                    weight=rule.weight,
                    violations=[RuleViolation(
                        rule_id=rule.rule_id,
                        dimension=rule.dimension,
                        severity=Severity.ERROR,
                        message=f"Rule evaluation error: {str(e)}",
                    )],
                ))

        return results

    def _calculate_overall_score(
        self,
        results: List[RuleResult],
    ) -> float:
        """Calculate weighted overall score."""
        if not results:
            return 0.0

        total_weighted = sum(r.weighted_score for r in results)
        total_weight = sum(r.weight for r in results)

        return total_weighted / total_weight if total_weight > 0 else 0.0

    def _calculate_dimension_scores(
        self,
        results: List[RuleResult],
    ) -> Dict[str, DimensionScore]:
        """Calculate scores per quality dimension."""
        dimension_data: Dict[str, Dict] = {}

        for result in results:
            dim = result.dimension.value

            if dim not in dimension_data:
                dimension_data[dim] = {
                    "dimension": result.dimension,
                    "weighted_total": 0.0,
                    "weight_sum": 0.0,
                    "rule_count": 0,
                    "violations": [],
                }

            dimension_data[dim]["weighted_total"] += result.weighted_score
            dimension_data[dim]["weight_sum"] += result.weight
            dimension_data[dim]["rule_count"] += 1
            dimension_data[dim]["violations"].extend(result.violations)

        return {
            dim: DimensionScore(
                dimension=data["dimension"],
                score=data["weighted_total"],
                weight_sum=data["weight_sum"],
                rule_count=data["rule_count"],
                violations=data["violations"],
            )
            for dim, data in dimension_data.items()
        }

    def _collect_violations(
        self,
        results: List[RuleResult],
    ) -> List[RuleViolation]:
        """Collect all violations from results."""
        violations = []
        for result in results:
            violations.extend(result.violations)
        return violations

    def _make_decision(
        self,
        score: float,
        threshold: float,
        critical_violations: List[RuleViolation],
    ) -> GateDecision:
        """Make gate decision based on score and violations."""
        # Critical violations always fail
        if critical_violations:
            return GateDecision.FAIL

        # Check threshold
        if score < threshold:
            return GateDecision.FAIL

        # Check warn threshold
        if score < self._warn_threshold:
            return GateDecision.WARN

        return GateDecision.PASS

    def _generate_feedback(
        self,
        violations: List[RuleViolation],
        dimension_scores: Dict[str, DimensionScore],
        score: float,
        threshold: float,
    ) -> str:
        """Generate actionable feedback for retry."""
        parts = [
            f"Quality gate failed (score={score:.2f}, threshold={threshold:.2f})",
            "",
            "Issues to address:",
        ]

        # Group by severity
        critical = [v for v in violations if v.severity == Severity.CRITICAL]
        errors = [v for v in violations if v.severity == Severity.ERROR]
        warnings = [v for v in violations if v.severity == Severity.WARNING]

        if critical:
            parts.append("  CRITICAL:")
            for v in critical[:5]:  # Limit to 5
                parts.append(f"    - {v.message}")
                if v.suggestion:
                    parts.append(f"      Fix: {v.suggestion}")

        if errors:
            parts.append("  ERRORS:")
            for v in errors[:5]:
                parts.append(f"    - {v.message}")
                if v.suggestion:
                    parts.append(f"      Fix: {v.suggestion}")

        if warnings and len(parts) < 15:  # Only if we have room
            parts.append("  WARNINGS:")
            for v in warnings[:3]:
                parts.append(f"    - {v.message}")

        # Add dimension guidance
        weak_dims = [
            (dim, ds)
            for dim, ds in dimension_scores.items()
            if ds.weighted_average < 0.7
        ]

        if weak_dims:
            parts.append("")
            parts.append("Weak dimensions:")
            for dim, ds in weak_dims[:3]:
                parts.append(f"  - {dim}: {ds.weighted_average:.2f}")

        return "\n".join(parts)

    def get_rule_summary(self, domain: str) -> Dict[str, Any]:
        """Get summary of rules for a domain."""
        rule_set = get_rules_for_domain(domain)
        custom = self._custom_rules.get(domain, [])

        return {
            "domain": domain,
            "default_threshold": rule_set.default_threshold,
            "total_rules": len(rule_set.rules) + len(custom),
            "standard_rules": len(rule_set.rules),
            "custom_rules": len(custom),
            "total_weight": rule_set.get_total_weight() + sum(r.weight for r in custom),
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "dimension": r.dimension.value,
                    "weight": r.weight,
                    "description": r.description,
                }
                for r in rule_set.rules
            ],
        }


def create_evaluator(
    threshold: float = 0.85,
    warn_threshold: float = 0.90,
) -> QualityGateEvaluator:
    """
    Factory function to create evaluator instance.

    Args:
        threshold: Pass/fail threshold
        warn_threshold: Warn threshold

    Returns:
        Configured QualityGateEvaluator
    """
    return QualityGateEvaluator(
        default_threshold=threshold,
        warn_threshold=warn_threshold,
    )
