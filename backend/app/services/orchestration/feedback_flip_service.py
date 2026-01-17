"""
MP-M-1: Feedback Flip Service

Refocus AI from implementation to evaluation mode.
Enables role switching between implementing and critiquing code.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Toggle between implementation and evaluation modes
- Structured code evaluation with criteria
- Finding and recommendation tracking
- Evaluation summaries and insights

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class FlipMode(Enum):
    """Modes of operation for the AI agent."""
    IMPLEMENT = "implement"   # Normal: AI writes code
    EVALUATE = "evaluate"     # Flipped: AI reviews/critiques
    SUGGEST = "suggest"       # AI suggests improvements only
    COMPARE = "compare"       # AI compares multiple solutions


class FindingSeverity(Enum):
    """Severity of evaluation findings."""
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class FindingCategory(Enum):
    """Category of evaluation findings."""
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    READABILITY = "readability"
    TESTABILITY = "testability"
    ARCHITECTURE = "architecture"
    STYLE = "style"


@dataclass
class Finding:
    """A single finding from an evaluation."""
    id: UUID
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    location: Optional[str] = None  # File/line reference
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class EvaluationCriterion:
    """A criterion for evaluation."""
    name: str
    description: str
    weight: float = 1.0  # Importance weight
    threshold: Optional[float] = None  # Minimum acceptable score


@dataclass
class Evaluation:
    """Result of evaluating content."""
    id: UUID
    session_id: UUID
    target: str
    content_hash: str
    criteria: List[EvaluationCriterion]
    findings: List[Finding]
    recommendations: List[str]
    scores: Dict[str, float]  # Criterion name -> score (0-100)
    overall_score: float
    evaluated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlipSession:
    """A session for feedback flip operations."""
    id: UUID
    task_id: str
    mode: FlipMode
    target_description: str
    criteria: List[EvaluationCriterion]
    evaluations: List[Evaluation]
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    mode_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EvaluationSummary:
    """Summary of all evaluations in a session."""
    session_id: UUID
    evaluation_count: int
    average_score: float
    score_trend: str  # "improving", "stable", "declining"
    common_issues: List[Dict[str, Any]]
    top_recommendations: List[str]
    criteria_performance: Dict[str, float]
    findings_by_severity: Dict[FindingSeverity, int]
    findings_by_category: Dict[FindingCategory, int]


class FeedbackFlipService:
    """
    Service for switching AI between implementation and evaluation modes.

    The "Feedback Flip" pattern recognizes that AI can be more effective
    when periodically switching from implementing to evaluating code.
    This helps catch issues early and maintains code quality.
    """

    # Default evaluation criteria
    DEFAULT_CRITERIA = [
        EvaluationCriterion("correctness", "Code produces correct results", 2.0, 70.0),
        EvaluationCriterion("readability", "Code is easy to read and understand", 1.5),
        EvaluationCriterion("maintainability", "Code is easy to modify and extend", 1.5),
        EvaluationCriterion("performance", "Code performs efficiently", 1.0),
        EvaluationCriterion("security", "Code follows security best practices", 1.5, 60.0),
        EvaluationCriterion("testability", "Code is easy to test", 1.0),
    ]

    def __init__(self):
        self._sessions: Dict[UUID, FlipSession] = {}
        self._evaluations: Dict[UUID, Evaluation] = {}
        self._evaluation_callbacks: List[Callable[[Evaluation], None]] = []

    def start_session(
        self,
        task_id: str,
        target_description: str,
        criteria: Optional[List[EvaluationCriterion]] = None,
        initial_mode: FlipMode = FlipMode.IMPLEMENT,
        context: Optional[Dict[str, Any]] = None
    ) -> FlipSession:
        """
        Start a new feedback flip session.

        Args:
            task_id: Identifier for the task being worked on
            target_description: Description of what's being evaluated
            criteria: Evaluation criteria (defaults to standard criteria)
            initial_mode: Starting mode
            context: Additional context

        Returns:
            Created FlipSession
        """
        now = datetime.now(timezone.utc)

        session = FlipSession(
            id=uuid4(),
            task_id=task_id,
            mode=initial_mode,
            target_description=target_description,
            criteria=criteria or self.DEFAULT_CRITERIA.copy(),
            evaluations=[],
            context=context or {},
            created_at=now,
            updated_at=now,
            mode_history=[{
                "mode": initial_mode.value,
                "timestamp": now.isoformat(),
                "reason": "session_start"
            }]
        )

        self._sessions[session.id] = session
        logger.info(f"Started feedback flip session {session.id} for task {task_id} in {initial_mode.value} mode")

        return session

    def flip_mode(
        self,
        session_id: UUID,
        new_mode: FlipMode,
        reason: Optional[str] = None
    ) -> FlipSession:
        """
        Flip the session to a new mode.

        Args:
            session_id: The session to flip
            new_mode: The new mode to switch to
            reason: Optional reason for the flip

        Returns:
            Updated FlipSession
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        old_mode = session.mode
        session.mode = new_mode
        session.updated_at = datetime.now(timezone.utc)

        session.mode_history.append({
            "mode": new_mode.value,
            "from_mode": old_mode.value,
            "timestamp": session.updated_at.isoformat(),
            "reason": reason or "manual_flip"
        })

        logger.info(f"Flipped session {session_id} from {old_mode.value} to {new_mode.value}")

        return session

    def submit_for_evaluation(
        self,
        session_id: UUID,
        content: str,
        target: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Evaluation:
        """
        Submit content for evaluation.

        Args:
            session_id: The session
            content: Content to evaluate (code, design, etc.)
            target: Specific target being evaluated
            metadata: Additional metadata

        Returns:
            Evaluation results
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Auto-flip to evaluate mode if needed
        if session.mode == FlipMode.IMPLEMENT:
            self.flip_mode(session_id, FlipMode.EVALUATE, "auto_flip_for_evaluation")

        # Generate content hash for deduplication
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Perform evaluation (simulated - in real implementation, this would use LLM)
        findings = self._analyze_content(content, session.criteria)
        scores = self._calculate_scores(findings, session.criteria)
        recommendations = self._generate_recommendations(findings)

        overall_score = self._calculate_overall_score(scores, session.criteria)

        evaluation = Evaluation(
            id=uuid4(),
            session_id=session_id,
            target=target or session.target_description,
            content_hash=content_hash,
            criteria=session.criteria,
            findings=findings,
            recommendations=recommendations,
            scores=scores,
            overall_score=overall_score,
            evaluated_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )

        self._evaluations[evaluation.id] = evaluation
        session.evaluations.append(evaluation)
        session.updated_at = evaluation.evaluated_at

        # Notify callbacks
        for callback in self._evaluation_callbacks:
            try:
                callback(evaluation)
            except Exception as e:
                logger.error(f"Evaluation callback failed: {e}")

        logger.info(f"Completed evaluation {evaluation.id} for session {session_id}: score={overall_score:.1f}")

        return evaluation

    def get_evaluation_summary(self, session_id: UUID) -> EvaluationSummary:
        """
        Get a summary of all evaluations in a session.

        Args:
            session_id: The session

        Returns:
            EvaluationSummary with aggregated insights
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        evaluations = session.evaluations

        if not evaluations:
            return EvaluationSummary(
                session_id=session_id,
                evaluation_count=0,
                average_score=0.0,
                score_trend="stable",
                common_issues=[],
                top_recommendations=[],
                criteria_performance={},
                findings_by_severity={s: 0 for s in FindingSeverity},
                findings_by_category={c: 0 for c in FindingCategory}
            )

        # Calculate metrics
        scores = [e.overall_score for e in evaluations]
        average_score = sum(scores) / len(scores)

        # Determine trend
        if len(scores) >= 3:
            recent = sum(scores[-3:]) / 3
            earlier = sum(scores[:len(scores)//2 + 1]) / (len(scores)//2 + 1)
            if recent > earlier + 5:
                trend = "improving"
            elif recent < earlier - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Aggregate findings
        findings_by_severity: Dict[FindingSeverity, int] = {s: 0 for s in FindingSeverity}
        findings_by_category: Dict[FindingCategory, int] = {c: 0 for c in FindingCategory}
        issue_counts: Dict[str, int] = {}

        for evaluation in evaluations:
            for finding in evaluation.findings:
                findings_by_severity[finding.severity] += 1
                findings_by_category[finding.category] += 1
                issue_key = f"{finding.category.value}:{finding.title}"
                issue_counts[issue_key] = issue_counts.get(issue_key, 0) + 1

        # Top issues
        common_issues = [
            {"issue": key, "count": count}
            for key, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:5]
        ]

        # Aggregate recommendations
        all_recs: Dict[str, int] = {}
        for evaluation in evaluations:
            for rec in evaluation.recommendations:
                all_recs[rec] = all_recs.get(rec, 0) + 1
        top_recommendations = [
            rec for rec, _ in sorted(all_recs.items(), key=lambda x: -x[1])[:5]
        ]

        # Criteria performance
        criteria_scores: Dict[str, List[float]] = {}
        for evaluation in evaluations:
            for name, score in evaluation.scores.items():
                if name not in criteria_scores:
                    criteria_scores[name] = []
                criteria_scores[name].append(score)

        criteria_performance = {
            name: sum(scores) / len(scores)
            for name, scores in criteria_scores.items()
        }

        return EvaluationSummary(
            session_id=session_id,
            evaluation_count=len(evaluations),
            average_score=average_score,
            score_trend=trend,
            common_issues=common_issues,
            top_recommendations=top_recommendations,
            criteria_performance=criteria_performance,
            findings_by_severity=findings_by_severity,
            findings_by_category=findings_by_category
        )

    def get_session(self, session_id: UUID) -> Optional[FlipSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_evaluation(self, evaluation_id: UUID) -> Optional[Evaluation]:
        """Get an evaluation by ID."""
        return self._evaluations.get(evaluation_id)

    def get_mode_for_session(self, session_id: UUID) -> Optional[FlipMode]:
        """Get the current mode for a session."""
        session = self._sessions.get(session_id)
        return session.mode if session else None

    def should_flip(self, session_id: UUID) -> Dict[str, Any]:
        """
        Determine if the session should flip modes.

        Returns a recommendation with reasoning.
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"should_flip": False, "reason": "Session not found"}

        # Check recent evaluations
        if session.mode == FlipMode.IMPLEMENT:
            # Suggest flipping to evaluate after significant work
            if len(session.evaluations) == 0:
                return {
                    "should_flip": True,
                    "suggested_mode": FlipMode.EVALUATE.value,
                    "reason": "No evaluations yet - time to review implemented work"
                }

        elif session.mode == FlipMode.EVALUATE:
            if session.evaluations:
                last_eval = session.evaluations[-1]
                if last_eval.overall_score >= 80:
                    return {
                        "should_flip": True,
                        "suggested_mode": FlipMode.IMPLEMENT.value,
                        "reason": f"High score ({last_eval.overall_score:.1f}) - ready to continue implementing"
                    }
                elif len([f for f in last_eval.findings if f.severity == FindingSeverity.CRITICAL]) > 0:
                    return {
                        "should_flip": False,
                        "reason": "Critical issues found - continue evaluation"
                    }

        return {"should_flip": False, "reason": "Current mode is appropriate"}

    def register_evaluation_callback(self, callback: Callable[[Evaluation], None]) -> None:
        """Register a callback to be called after each evaluation."""
        self._evaluation_callbacks.append(callback)

    def compare_evaluations(
        self,
        evaluation_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Compare multiple evaluations.

        Args:
            evaluation_ids: IDs of evaluations to compare

        Returns:
            Comparison results
        """
        evaluations = [self._evaluations.get(eid) for eid in evaluation_ids]
        evaluations = [e for e in evaluations if e is not None]

        if len(evaluations) < 2:
            raise ValueError("Need at least 2 evaluations to compare")

        # Find best/worst
        sorted_evals = sorted(evaluations, key=lambda e: e.overall_score, reverse=True)
        best = sorted_evals[0]
        worst = sorted_evals[-1]

        # Compare criteria
        criteria_comparison = {}
        for criterion in evaluations[0].criteria:
            scores = [e.scores.get(criterion.name, 0) for e in evaluations]
            criteria_comparison[criterion.name] = {
                "min": min(scores),
                "max": max(scores),
                "spread": max(scores) - min(scores),
                "scores": scores
            }

        return {
            "evaluation_count": len(evaluations),
            "best": {
                "id": str(best.id),
                "score": best.overall_score,
                "target": best.target
            },
            "worst": {
                "id": str(worst.id),
                "score": worst.overall_score,
                "target": worst.target
            },
            "score_range": best.overall_score - worst.overall_score,
            "criteria_comparison": criteria_comparison,
            "recommendation": self._generate_comparison_recommendation(best, worst)
        }

    def _analyze_content(
        self,
        content: str,
        criteria: List[EvaluationCriterion]
    ) -> List[Finding]:
        """
        Analyze content and generate findings.

        Note: In production, this would use LLM analysis.
        This is a simplified heuristic implementation.
        """
        findings: List[Finding] = []

        # Simple heuristic analysis
        lines = content.split('\n')

        # Check for long functions/methods
        in_function = False
        function_lines = 0
        for i, line in enumerate(lines):
            if 'def ' in line or 'function ' in line or 'fn ' in line:
                in_function = True
                function_lines = 0
            elif in_function:
                function_lines += 1
                if function_lines > 50:
                    findings.append(Finding(
                        id=uuid4(),
                        category=FindingCategory.MAINTAINABILITY,
                        severity=FindingSeverity.MAJOR,
                        title="Long function detected",
                        description=f"Function exceeds 50 lines (around line {i})",
                        location=f"line {i}",
                        suggestion="Consider breaking into smaller functions",
                        auto_fixable=False
                    ))
                    in_function = False

        # Check for TODO/FIXME
        for i, line in enumerate(lines):
            if 'TODO' in line or 'FIXME' in line:
                findings.append(Finding(
                    id=uuid4(),
                    category=FindingCategory.MAINTAINABILITY,
                    severity=FindingSeverity.INFO,
                    title="TODO/FIXME comment found",
                    description=line.strip(),
                    location=f"line {i + 1}",
                    auto_fixable=False
                ))

        # Check for hardcoded values
        import re
        for i, line in enumerate(lines):
            # Look for hardcoded strings that might be config
            if re.search(r'(password|secret|key|token)\s*=\s*["\']', line, re.I):
                findings.append(Finding(
                    id=uuid4(),
                    category=FindingCategory.SECURITY,
                    severity=FindingSeverity.CRITICAL,
                    title="Potential hardcoded secret",
                    description=f"Possible hardcoded secret at line {i + 1}",
                    location=f"line {i + 1}",
                    suggestion="Move to environment variable or secrets manager",
                    auto_fixable=False
                ))

        # Check for deeply nested code
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        if max_indent > 24:  # More than 6 levels of indentation
            findings.append(Finding(
                id=uuid4(),
                category=FindingCategory.READABILITY,
                severity=FindingSeverity.MAJOR,
                title="Deeply nested code",
                description=f"Code has {max_indent // 4} levels of nesting",
                suggestion="Consider early returns or extracting functions",
                auto_fixable=False
            ))

        return findings

    def _calculate_scores(
        self,
        findings: List[Finding],
        criteria: List[EvaluationCriterion]
    ) -> Dict[str, float]:
        """Calculate scores for each criterion based on findings."""
        scores = {}

        # Start with perfect scores
        for criterion in criteria:
            scores[criterion.name] = 100.0

        # Deduct based on findings
        severity_deductions = {
            FindingSeverity.INFO: 2,
            FindingSeverity.MINOR: 5,
            FindingSeverity.MAJOR: 15,
            FindingSeverity.CRITICAL: 30
        }

        category_to_criterion = {
            FindingCategory.CORRECTNESS: "correctness",
            FindingCategory.PERFORMANCE: "performance",
            FindingCategory.MAINTAINABILITY: "maintainability",
            FindingCategory.SECURITY: "security",
            FindingCategory.READABILITY: "readability",
            FindingCategory.TESTABILITY: "testability",
            FindingCategory.ARCHITECTURE: "maintainability",
            FindingCategory.STYLE: "readability"
        }

        for finding in findings:
            criterion_name = category_to_criterion.get(finding.category)
            if criterion_name and criterion_name in scores:
                deduction = severity_deductions.get(finding.severity, 5)
                scores[criterion_name] = max(0, scores[criterion_name] - deduction)

        return scores

    def _calculate_overall_score(
        self,
        scores: Dict[str, float],
        criteria: List[EvaluationCriterion]
    ) -> float:
        """Calculate weighted overall score."""
        total_weight = sum(c.weight for c in criteria if c.name in scores)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(
            scores.get(c.name, 0) * c.weight
            for c in criteria
            if c.name in scores
        )

        return weighted_sum / total_weight

    def _generate_recommendations(self, findings: List[Finding]) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []

        # Group by category
        by_category: Dict[FindingCategory, List[Finding]] = {}
        for finding in findings:
            if finding.category not in by_category:
                by_category[finding.category] = []
            by_category[finding.category].append(finding)

        # Generate category-specific recommendations
        if FindingCategory.SECURITY in by_category:
            critical = [f for f in by_category[FindingCategory.SECURITY]
                       if f.severity == FindingSeverity.CRITICAL]
            if critical:
                recommendations.append("URGENT: Address critical security issues before proceeding")

        if FindingCategory.MAINTAINABILITY in by_category:
            if len(by_category[FindingCategory.MAINTAINABILITY]) > 3:
                recommendations.append("Consider refactoring to improve maintainability")

        if FindingCategory.READABILITY in by_category:
            recommendations.append("Review code structure for better readability")

        # Add specific suggestions from findings
        for finding in findings:
            if finding.suggestion and finding.suggestion not in recommendations:
                if finding.severity in (FindingSeverity.MAJOR, FindingSeverity.CRITICAL):
                    recommendations.append(finding.suggestion)

        return recommendations[:10]  # Limit to top 10

    def _generate_comparison_recommendation(
        self,
        best: Evaluation,
        worst: Evaluation
    ) -> str:
        """Generate recommendation based on comparison."""
        diff = best.overall_score - worst.overall_score

        if diff < 10:
            return "Solutions are comparable in quality"
        elif diff < 25:
            return f"Best solution ({best.target}) shows moderate improvement over alternatives"
        else:
            return f"Best solution ({best.target}) is significantly better - consider adopting its approach"
