"""
MP-L-2: All Paths Prototyping Service

Build multiple variations, test all, pick best.
Systematic exploration of implementation alternatives.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Create and track multiple implementation variations
- Run tests on all variations
- Evaluate and compare variations
- Select winner based on criteria
- Archive learnings for future reference

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Status of a prototyping session."""
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    EVALUATING = "evaluating"
    COMPARING = "comparing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariationStatus(Enum):
    """Status of a variation."""
    DRAFT = "draft"
    IMPLEMENTING = "implementing"
    READY = "ready"
    TESTING = "testing"
    EVALUATED = "evaluated"
    WINNER = "winner"
    REJECTED = "rejected"


class EvaluatorType(Enum):
    """Type of evaluator for criteria."""
    AUTOMATED = "automated"  # Tests, linting, metrics
    LLM = "llm"             # LLM-based evaluation
    HUMAN = "human"         # Human review required
    HYBRID = "hybrid"       # Combination


@dataclass
class EvaluationCriterion:
    """A criterion for evaluating variations."""
    name: str
    description: str
    weight: float  # 0-1, weights should sum to 1
    evaluator: EvaluatorType
    threshold: Optional[float] = None  # Minimum acceptable score
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResults:
    """Results from running tests."""
    passed: int
    failed: int
    skipped: int
    errors: int
    coverage: Optional[float] = None
    duration_seconds: float = 0.0
    details: List[Dict[str, Any]] = field(default_factory=list)
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Variation:
    """A single implementation variation."""
    id: UUID
    session_id: UUID
    index: int
    approach_description: str
    implementation: Optional[str]  # Code or path to code
    status: VariationStatus
    test_results: Optional[TestResults]
    evaluation_scores: Dict[str, float]  # criterion name -> score
    total_score: float
    strengths: List[str]
    weaknesses: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Learning:
    """A learning/insight from the prototyping process."""
    id: UUID
    session_id: UUID
    variation_id: Optional[UUID]
    category: str  # "approach", "pattern", "pitfall", "insight"
    content: str
    applicability: str  # When this learning applies
    created_at: datetime


@dataclass
class ComparisonReport:
    """Report comparing all variations."""
    session_id: UUID
    variations_compared: int
    winner: Optional[Variation]
    runner_ups: List[Variation]
    score_breakdown: Dict[str, Dict[str, float]]  # variation_id -> criterion -> score
    criteria_summary: Dict[str, Dict[str, Any]]  # criterion -> stats
    recommendation: str
    generated_at: datetime


@dataclass
class PrototypingSession:
    """A session for exploring multiple implementation paths."""
    id: UUID
    name: str
    task_description: str
    max_variations: int
    variations: List[Variation]
    evaluation_criteria: List[EvaluationCriterion]
    winner_id: Optional[UUID]
    status: SessionStatus
    learnings: List[Learning]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AllPathsService:
    """
    Service for exploring multiple implementation paths.

    The "All Paths Prototyping" pattern encourages creating multiple
    variations of a solution, testing all of them, and picking the
    best one based on defined criteria.
    """

    DEFAULT_MAX_VARIATIONS = 5
    DEFAULT_CRITERIA = [
        EvaluationCriterion("correctness", "Produces correct results", 0.25, EvaluatorType.AUTOMATED),
        EvaluationCriterion("readability", "Easy to understand", 0.20, EvaluatorType.LLM),
        EvaluationCriterion("performance", "Efficient execution", 0.15, EvaluatorType.AUTOMATED),
        EvaluationCriterion("maintainability", "Easy to modify", 0.20, EvaluatorType.LLM),
        EvaluationCriterion("testability", "Easy to test", 0.20, EvaluatorType.AUTOMATED),
    ]

    def __init__(self):
        self._sessions: Dict[UUID, PrototypingSession] = {}
        self._variations: Dict[UUID, Variation] = {}
        self._learnings: Dict[UUID, Learning] = {}
        self._evaluators: Dict[str, Callable[[str, EvaluationCriterion], float]] = {}

    def create_session(
        self,
        name: str,
        task_description: str,
        criteria: Optional[List[EvaluationCriterion]] = None,
        max_variations: int = DEFAULT_MAX_VARIATIONS,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PrototypingSession:
        """
        Create a new prototyping session.

        Args:
            name: Session name
            task_description: Description of what to build
            criteria: Evaluation criteria (defaults to standard)
            max_variations: Maximum variations to create
            metadata: Additional metadata

        Returns:
            Created PrototypingSession
        """
        now = datetime.now(timezone.utc)

        # Validate and normalize criteria weights
        used_criteria = criteria or self.DEFAULT_CRITERIA.copy()
        total_weight = sum(c.weight for c in used_criteria)
        if total_weight != 1.0:
            for c in used_criteria:
                c.weight = c.weight / total_weight

        session = PrototypingSession(
            id=uuid4(),
            name=name,
            task_description=task_description,
            max_variations=max_variations,
            variations=[],
            evaluation_criteria=used_criteria,
            winner_id=None,
            status=SessionStatus.PLANNING,
            learnings=[],
            created_at=now,
            updated_at=now,
            completed_at=None,
            metadata=metadata or {}
        )

        self._sessions[session.id] = session

        logger.info(f"Created prototyping session '{name}' with max {max_variations} variations")

        return session

    def add_variation(
        self,
        session_id: UUID,
        approach_description: str,
        implementation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Variation:
        """
        Add a new variation to a session.

        Args:
            session_id: Session ID
            approach_description: Description of this approach
            implementation: Optional implementation code/path
            metadata: Additional metadata

        Returns:
            Created Variation
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if len(session.variations) >= session.max_variations:
            raise RuntimeError(f"Maximum variations ({session.max_variations}) reached")

        now = datetime.now(timezone.utc)

        variation = Variation(
            id=uuid4(),
            session_id=session_id,
            index=len(session.variations),
            approach_description=approach_description,
            implementation=implementation,
            status=VariationStatus.DRAFT if not implementation else VariationStatus.READY,
            test_results=None,
            evaluation_scores={},
            total_score=0.0,
            strengths=[],
            weaknesses=[],
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

        session.variations.append(variation)
        session.updated_at = now
        session.status = SessionStatus.IMPLEMENTING

        self._variations[variation.id] = variation

        logger.info(f"Added variation {variation.index} to session {session_id}")

        return variation

    def update_implementation(
        self,
        variation_id: UUID,
        implementation: str,
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None
    ) -> Variation:
        """
        Update a variation's implementation.

        Args:
            variation_id: Variation ID
            implementation: Implementation code/path
            strengths: Known strengths of this approach
            weaknesses: Known weaknesses

        Returns:
            Updated Variation
        """
        variation = self._variations.get(variation_id)
        if not variation:
            raise ValueError(f"Variation {variation_id} not found")

        variation.implementation = implementation
        variation.status = VariationStatus.READY
        variation.updated_at = datetime.now(timezone.utc)

        if strengths:
            variation.strengths = strengths
        if weaknesses:
            variation.weaknesses = weaknesses

        return variation

    def run_tests(
        self,
        variation_id: UUID,
        test_command: Optional[str] = None,
        test_function: Optional[Callable[[], TestResults]] = None
    ) -> TestResults:
        """
        Run tests on a variation.

        Args:
            variation_id: Variation ID
            test_command: Shell command to run tests
            test_function: Python function returning TestResults

        Returns:
            TestResults
        """
        variation = self._variations.get(variation_id)
        if not variation:
            raise ValueError(f"Variation {variation_id} not found")

        variation.status = VariationStatus.TESTING
        variation.updated_at = datetime.now(timezone.utc)

        # Update session status
        session = self._sessions.get(variation.session_id)
        if session:
            session.status = SessionStatus.TESTING
            session.updated_at = datetime.now(timezone.utc)

        if test_function:
            results = test_function()
        else:
            # Simulate test results (in production would run actual tests)
            results = TestResults(
                passed=10,
                failed=0,
                skipped=1,
                errors=0,
                coverage=85.0,
                duration_seconds=5.5
            )

        variation.test_results = results
        variation.updated_at = datetime.now(timezone.utc)

        logger.info(f"Ran tests on variation {variation_id}: {results.passed} passed, {results.failed} failed")

        return results

    def evaluate_variation(
        self,
        variation_id: UUID,
        external_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Evaluate a single variation against criteria.

        Args:
            variation_id: Variation ID
            external_scores: Externally provided scores (e.g., from LLM)

        Returns:
            Dictionary of criterion -> score
        """
        variation = self._variations.get(variation_id)
        if not variation:
            raise ValueError(f"Variation {variation_id} not found")

        session = self._sessions.get(variation.session_id)
        if not session:
            raise ValueError(f"Session not found for variation")

        scores = {}

        for criterion in session.evaluation_criteria:
            if external_scores and criterion.name in external_scores:
                scores[criterion.name] = external_scores[criterion.name]
            elif criterion.evaluator == EvaluatorType.AUTOMATED:
                scores[criterion.name] = self._evaluate_automated(variation, criterion)
            elif criterion.name in self._evaluators:
                impl = variation.implementation or ""
                scores[criterion.name] = self._evaluators[criterion.name](impl, criterion)
            else:
                # Default score for non-automated without external
                scores[criterion.name] = 70.0

        variation.evaluation_scores = scores
        variation.total_score = sum(
            scores.get(c.name, 0) * c.weight
            for c in session.evaluation_criteria
        )
        variation.status = VariationStatus.EVALUATED
        variation.updated_at = datetime.now(timezone.utc)

        logger.info(f"Evaluated variation {variation_id}: total score = {variation.total_score:.1f}")

        return scores

    def evaluate_all(self, session_id: UUID) -> Dict[UUID, Dict[str, float]]:
        """
        Evaluate all variations in a session.

        Args:
            session_id: Session ID

        Returns:
            Dictionary of variation_id -> criterion -> score
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = SessionStatus.EVALUATING
        session.updated_at = datetime.now(timezone.utc)

        results = {}
        for variation in session.variations:
            if variation.status == VariationStatus.READY:
                results[variation.id] = self.evaluate_variation(variation.id)

        return results

    def compare_variations(self, session_id: UUID) -> ComparisonReport:
        """
        Compare all variations and generate a report.

        Args:
            session_id: Session ID

        Returns:
            ComparisonReport with comparison results
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = SessionStatus.COMPARING
        session.updated_at = datetime.now(timezone.utc)

        # Ensure all variations are evaluated
        for variation in session.variations:
            if not variation.evaluation_scores:
                self.evaluate_variation(variation.id)

        # Sort by total score
        sorted_variations = sorted(
            session.variations,
            key=lambda v: v.total_score,
            reverse=True
        )

        winner = sorted_variations[0] if sorted_variations else None
        runner_ups = sorted_variations[1:3] if len(sorted_variations) > 1 else []

        # Build score breakdown
        score_breakdown = {
            str(v.id): v.evaluation_scores
            for v in session.variations
        }

        # Criteria summary
        criteria_summary = {}
        for criterion in session.evaluation_criteria:
            scores = [v.evaluation_scores.get(criterion.name, 0) for v in session.variations]
            criteria_summary[criterion.name] = {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "avg": sum(scores) / len(scores) if scores else 0,
                "weight": criterion.weight
            }

        # Generate recommendation
        if winner:
            score_diff = winner.total_score - (runner_ups[0].total_score if runner_ups else 0)
            if score_diff > 20:
                recommendation = f"Strongly recommend '{winner.approach_description[:50]}' - clear winner"
            elif score_diff > 10:
                recommendation = f"Recommend '{winner.approach_description[:50]}' with notable advantages"
            elif score_diff > 5:
                recommendation = f"Slight preference for '{winner.approach_description[:50]}'"
            else:
                recommendation = "Multiple viable options - consider other factors"
        else:
            recommendation = "No variations to compare"

        report = ComparisonReport(
            session_id=session_id,
            variations_compared=len(session.variations),
            winner=winner,
            runner_ups=runner_ups,
            score_breakdown=score_breakdown,
            criteria_summary=criteria_summary,
            recommendation=recommendation,
            generated_at=datetime.now(timezone.utc)
        )

        logger.info(f"Generated comparison report for session {session_id}")

        return report

    def select_winner(
        self,
        session_id: UUID,
        variation_id: Optional[UUID] = None
    ) -> Variation:
        """
        Select the winning variation.

        Args:
            session_id: Session ID
            variation_id: Specific variation to select (None = auto-select best)

        Returns:
            Selected winner Variation
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if variation_id:
            winner = self._variations.get(variation_id)
            if not winner or winner.session_id != session_id:
                raise ValueError(f"Variation {variation_id} not found in session")
        else:
            # Auto-select highest scoring
            if not session.variations:
                raise RuntimeError("No variations to select from")
            winner = max(session.variations, key=lambda v: v.total_score)

        # Update statuses
        for variation in session.variations:
            if variation.id == winner.id:
                variation.status = VariationStatus.WINNER
            else:
                variation.status = VariationStatus.REJECTED

        session.winner_id = winner.id
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        logger.info(f"Selected winner for session {session_id}: variation {winner.id}")

        return winner

    def add_learning(
        self,
        session_id: UUID,
        content: str,
        category: str = "insight",
        variation_id: Optional[UUID] = None,
        applicability: str = ""
    ) -> Learning:
        """
        Add a learning from the prototyping process.

        Args:
            session_id: Session ID
            content: The learning content
            category: Category (approach, pattern, pitfall, insight)
            variation_id: Optional specific variation
            applicability: When this learning applies

        Returns:
            Created Learning
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        learning = Learning(
            id=uuid4(),
            session_id=session_id,
            variation_id=variation_id,
            category=category,
            content=content,
            applicability=applicability,
            created_at=datetime.now(timezone.utc)
        )

        session.learnings.append(learning)
        self._learnings[learning.id] = learning

        logger.debug(f"Added learning to session {session_id}")

        return learning

    def get_learnings(
        self,
        session_id: Optional[UUID] = None,
        category: Optional[str] = None
    ) -> List[Learning]:
        """
        Get learnings with optional filtering.

        Args:
            session_id: Filter by session
            category: Filter by category

        Returns:
            List of Learning objects
        """
        learnings = list(self._learnings.values())

        if session_id:
            learnings = [l for l in learnings if l.session_id == session_id]

        if category:
            learnings = [l for l in learnings if l.category == category]

        return sorted(learnings, key=lambda l: l.created_at, reverse=True)

    def get_session(self, session_id: UUID) -> Optional[PrototypingSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_variation(self, variation_id: UUID) -> Optional[Variation]:
        """Get a variation by ID."""
        return self._variations.get(variation_id)

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 50
    ) -> List[PrototypingSession]:
        """List sessions with optional filtering."""
        sessions = list(self._sessions.values())

        if status:
            sessions = [s for s in sessions if s.status == status]

        sessions = sorted(sessions, key=lambda s: s.created_at, reverse=True)

        return sessions[:limit]

    def register_evaluator(
        self,
        criterion_name: str,
        evaluator: Callable[[str, EvaluationCriterion], float]
    ) -> None:
        """
        Register a custom evaluator for a criterion.

        Args:
            criterion_name: Name of criterion to evaluate
            evaluator: Function taking (implementation, criterion) -> score
        """
        self._evaluators[criterion_name] = evaluator
        logger.info(f"Registered evaluator for criterion '{criterion_name}'")

    def _evaluate_automated(
        self,
        variation: Variation,
        criterion: EvaluationCriterion
    ) -> float:
        """Perform automated evaluation based on criterion."""
        if criterion.name == "correctness":
            if variation.test_results:
                total = (variation.test_results.passed +
                        variation.test_results.failed +
                        variation.test_results.errors)
                if total > 0:
                    return (variation.test_results.passed / total) * 100
            return 70.0

        elif criterion.name == "performance":
            if variation.test_results:
                # Score based on test duration (faster = better)
                duration = variation.test_results.duration_seconds
                if duration < 1:
                    return 100.0
                elif duration < 5:
                    return 90.0
                elif duration < 10:
                    return 80.0
                elif duration < 30:
                    return 70.0
                else:
                    return 60.0
            return 75.0

        elif criterion.name == "testability":
            if variation.test_results and variation.test_results.coverage:
                return variation.test_results.coverage
            return 70.0

        # Default score for unknown automated criteria
        return 75.0

    def get_session_summary(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get a summary of a prototyping session.

        Args:
            session_id: Session ID

        Returns:
            Summary dictionary
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        variation_summaries = []
        for v in session.variations:
            variation_summaries.append({
                "id": str(v.id),
                "index": v.index,
                "approach": v.approach_description[:100],
                "status": v.status.value,
                "total_score": v.total_score,
                "is_winner": v.id == session.winner_id
            })

        winner = None
        if session.winner_id:
            w = self._variations.get(session.winner_id)
            if w:
                winner = {
                    "id": str(w.id),
                    "approach": w.approach_description,
                    "score": w.total_score,
                    "strengths": w.strengths,
                    "weaknesses": w.weaknesses
                }

        return {
            "session_id": str(session_id),
            "name": session.name,
            "task": session.task_description,
            "status": session.status.value,
            "variation_count": len(session.variations),
            "max_variations": session.max_variations,
            "variations": variation_summaries,
            "winner": winner,
            "learning_count": len(session.learnings),
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
