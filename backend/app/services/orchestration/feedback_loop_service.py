"""
MP-QW-3: Feedback Loop Autonomy Service

Enable autonomous iteration with success metrics.
Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Define success criteria (tests pass, coverage X%, UI match, etc.)
- Track iterations toward success
- Automatic success detection
- Progress reporting

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class CriterionType(Enum):
    """Types of success criteria."""
    TESTS_PASS = "tests_pass"
    COVERAGE_MINIMUM = "coverage_minimum"
    COVERAGE_TARGET = "coverage_target"
    UI_MATCH = "ui_match"
    LINT_PASS = "lint_pass"
    BUILD_SUCCESS = "build_success"
    NO_ERRORS = "no_errors"
    PERFORMANCE_TARGET = "performance_target"
    CUSTOM = "custom"


class LoopStatus(Enum):
    """Status of a feedback loop."""
    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    CANCELLED = "cancelled"


@dataclass
class SuccessCriterion:
    """A single success criterion to be met."""
    id: UUID
    type: CriterionType
    name: str
    target: str  # e.g., "80%" for coverage, "true" for tests
    current_value: Optional[str] = None
    met: bool = False
    last_checked: Optional[datetime] = None
    check_count: int = 0


@dataclass
class IterationResult:
    """Result of a single iteration."""
    iteration_number: int
    timestamp: datetime
    criteria_results: Dict[UUID, bool]  # criterion_id -> met
    overall_success: bool
    duration_ms: Optional[int] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopProgress:
    """Progress summary for a feedback loop."""
    loop_id: UUID
    status: LoopStatus
    current_iteration: int
    max_iterations: int
    criteria_met: int
    criteria_total: int
    percent_complete: float
    estimated_remaining: Optional[int] = None  # iterations
    last_iteration: Optional[IterationResult] = None


@dataclass
class FeedbackLoop:
    """A feedback loop for autonomous iteration."""
    id: UUID
    task_id: str
    description: str
    success_criteria: List[SuccessCriterion]
    max_iterations: int
    current_iteration: int
    status: LoopStatus
    iteration_results: List[IterationResult]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeedbackLoopService:
    """
    Service for managing autonomous feedback loops.

    Enables agents to iterate autonomously until success criteria are met,
    with configurable limits and progress tracking.
    """

    def __init__(self):
        self._loops: Dict[UUID, FeedbackLoop] = {}
        self._task_loops: Dict[str, UUID] = {}  # task_id -> active loop_id
        self._callbacks: Dict[str, List[Callable]] = {
            "on_iteration": [],
            "on_success": [],
            "on_failure": [],
            "on_max_reached": [],
        }

    def create_loop(
        self,
        task_id: str,
        description: str,
        criteria: List[Dict[str, Any]],
        max_iterations: int = 10,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackLoop:
        """
        Create a new feedback loop with success criteria.

        Args:
            task_id: Identifier for the task being iterated
            description: Human-readable description of the goal
            criteria: List of criterion definitions
            max_iterations: Maximum iterations before giving up
            metadata: Optional metadata

        Returns:
            Created FeedbackLoop
        """
        # Parse criteria into SuccessCriterion objects
        success_criteria = []
        for c in criteria:
            criterion = SuccessCriterion(
                id=uuid4(),
                type=CriterionType(c.get("type", "custom")),
                name=c.get("name", "Unnamed criterion"),
                target=str(c.get("target", "true")),
            )
            success_criteria.append(criterion)

        now = datetime.now(timezone.utc)
        loop = FeedbackLoop(
            id=uuid4(),
            task_id=task_id,
            description=description,
            success_criteria=success_criteria,
            max_iterations=max_iterations,
            current_iteration=0,
            status=LoopStatus.CREATED,
            iteration_results=[],
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        self._loops[loop.id] = loop
        self._task_loops[task_id] = loop.id

        logger.info(f"Created feedback loop {loop.id} for task {task_id} with {len(success_criteria)} criteria")
        return loop

    def start_loop(self, loop_id: UUID) -> FeedbackLoop:
        """Start a feedback loop (change status to RUNNING)."""
        loop = self._get_loop(loop_id)
        if loop.status != LoopStatus.CREATED:
            raise ValueError(f"Loop {loop_id} is not in CREATED status")

        loop.status = LoopStatus.RUNNING
        loop.updated_at = datetime.now(timezone.utc)

        logger.info(f"Started feedback loop {loop_id}")
        return loop

    def record_iteration(
        self,
        loop_id: UUID,
        results: Dict[str, Any],
        duration_ms: Optional[int] = None,
        notes: Optional[str] = None
    ) -> IterationResult:
        """
        Record an iteration result.

        Args:
            loop_id: The feedback loop ID
            results: Dict mapping criterion names/ids to current values
            duration_ms: Optional duration of this iteration
            notes: Optional notes about this iteration

        Returns:
            IterationResult for this iteration
        """
        loop = self._get_loop(loop_id)

        if loop.status not in (LoopStatus.CREATED, LoopStatus.RUNNING):
            raise ValueError(f"Loop {loop_id} is not active (status: {loop.status})")

        # Start if not already running
        if loop.status == LoopStatus.CREATED:
            loop.status = LoopStatus.RUNNING

        loop.current_iteration += 1
        now = datetime.now(timezone.utc)

        # Update criteria with results
        criteria_results: Dict[UUID, bool] = {}
        for criterion in loop.success_criteria:
            # Look up result by name or id
            value = results.get(criterion.name) or results.get(str(criterion.id))
            if value is not None:
                criterion.current_value = str(value)
                criterion.met = self._check_criterion_met(criterion, value)
                criterion.last_checked = now
                criterion.check_count += 1
            criteria_results[criterion.id] = criterion.met

        # Check if all criteria met
        all_met = all(c.met for c in loop.success_criteria)

        # Create iteration result
        iteration_result = IterationResult(
            iteration_number=loop.current_iteration,
            timestamp=now,
            criteria_results=criteria_results,
            overall_success=all_met,
            duration_ms=duration_ms,
            notes=notes,
        )
        loop.iteration_results.append(iteration_result)
        loop.updated_at = now

        # Trigger callbacks
        self._trigger_callback("on_iteration", loop, iteration_result)

        # Check loop completion
        if all_met:
            loop.status = LoopStatus.SUCCEEDED
            loop.completed_at = now
            self._trigger_callback("on_success", loop)
            logger.info(f"Feedback loop {loop_id} succeeded after {loop.current_iteration} iterations")
        elif loop.current_iteration >= loop.max_iterations:
            loop.status = LoopStatus.MAX_ITERATIONS_REACHED
            loop.completed_at = now
            self._trigger_callback("on_max_reached", loop)
            logger.warning(f"Feedback loop {loop_id} reached max iterations ({loop.max_iterations})")

        return iteration_result

    def check_success(self, loop_id: UUID) -> bool:
        """Check if all success criteria are met."""
        loop = self._get_loop(loop_id)
        return all(c.met for c in loop.success_criteria)

    def should_continue(self, loop_id: UUID) -> bool:
        """Check if the loop should continue iterating."""
        loop = self._get_loop(loop_id)

        if loop.status == LoopStatus.SUCCEEDED:
            return False
        if loop.status in (LoopStatus.FAILED, LoopStatus.CANCELLED, LoopStatus.MAX_ITERATIONS_REACHED):
            return False
        if loop.current_iteration >= loop.max_iterations:
            return False

        return True

    def get_progress(self, loop_id: UUID) -> LoopProgress:
        """Get progress summary for a feedback loop."""
        loop = self._get_loop(loop_id)

        criteria_met = sum(1 for c in loop.success_criteria if c.met)
        criteria_total = len(loop.success_criteria)

        # Calculate percent complete based on criteria met
        percent_complete = (criteria_met / criteria_total * 100) if criteria_total > 0 else 0

        # Estimate remaining iterations based on progress trend
        estimated_remaining = None
        if loop.current_iteration > 0 and not self.check_success(loop_id):
            # Simple estimate: assume linear progress
            if criteria_met > 0:
                avg_iterations_per_criterion = loop.current_iteration / criteria_met
                remaining_criteria = criteria_total - criteria_met
                estimated_remaining = int(avg_iterations_per_criterion * remaining_criteria)
            else:
                estimated_remaining = loop.max_iterations - loop.current_iteration

        return LoopProgress(
            loop_id=loop_id,
            status=loop.status,
            current_iteration=loop.current_iteration,
            max_iterations=loop.max_iterations,
            criteria_met=criteria_met,
            criteria_total=criteria_total,
            percent_complete=percent_complete,
            estimated_remaining=estimated_remaining,
            last_iteration=loop.iteration_results[-1] if loop.iteration_results else None,
        )

    def get_loop(self, loop_id: UUID) -> Optional[FeedbackLoop]:
        """Get a feedback loop by ID."""
        return self._loops.get(loop_id)

    def get_loop_by_task(self, task_id: str) -> Optional[FeedbackLoop]:
        """Get the active feedback loop for a task."""
        loop_id = self._task_loops.get(task_id)
        if loop_id:
            return self._loops.get(loop_id)
        return None

    def cancel_loop(self, loop_id: UUID, reason: Optional[str] = None) -> FeedbackLoop:
        """Cancel a feedback loop."""
        loop = self._get_loop(loop_id)

        if loop.status in (LoopStatus.SUCCEEDED, LoopStatus.FAILED, LoopStatus.CANCELLED):
            raise ValueError(f"Loop {loop_id} is already completed")

        loop.status = LoopStatus.CANCELLED
        loop.completed_at = datetime.now(timezone.utc)
        loop.updated_at = loop.completed_at
        if reason:
            loop.metadata["cancel_reason"] = reason

        logger.info(f"Cancelled feedback loop {loop_id}: {reason}")
        return loop

    def fail_loop(self, loop_id: UUID, reason: str) -> FeedbackLoop:
        """Mark a feedback loop as failed."""
        loop = self._get_loop(loop_id)

        loop.status = LoopStatus.FAILED
        loop.completed_at = datetime.now(timezone.utc)
        loop.updated_at = loop.completed_at
        loop.metadata["failure_reason"] = reason

        self._trigger_callback("on_failure", loop)
        logger.error(f"Feedback loop {loop_id} failed: {reason}")
        return loop

    def get_all_loops(self, status: Optional[LoopStatus] = None) -> List[FeedbackLoop]:
        """Get all feedback loops, optionally filtered by status."""
        loops = list(self._loops.values())
        if status:
            loops = [l for l in loops if l.status == status]
        return sorted(loops, key=lambda l: l.created_at, reverse=True)

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for loop events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _get_loop(self, loop_id: UUID) -> FeedbackLoop:
        """Get a loop or raise ValueError."""
        loop = self._loops.get(loop_id)
        if not loop:
            raise ValueError(f"Feedback loop {loop_id} not found")
        return loop

    def _check_criterion_met(self, criterion: SuccessCriterion, value: Any) -> bool:
        """Check if a criterion is met based on its type and target."""
        target = criterion.target
        str_value = str(value).lower()

        if criterion.type == CriterionType.TESTS_PASS:
            return str_value in ("true", "pass", "passed", "1", "yes")

        elif criterion.type == CriterionType.BUILD_SUCCESS:
            return str_value in ("true", "success", "passed", "1", "yes")

        elif criterion.type == CriterionType.LINT_PASS:
            return str_value in ("true", "pass", "passed", "1", "yes", "0")  # 0 = no errors

        elif criterion.type == CriterionType.NO_ERRORS:
            return str_value in ("true", "0", "none", "no")

        elif criterion.type in (CriterionType.COVERAGE_MINIMUM, CriterionType.COVERAGE_TARGET):
            try:
                # Parse percentage values
                current = float(str_value.replace("%", ""))
                target_val = float(target.replace("%", ""))
                return current >= target_val
            except (ValueError, AttributeError):
                return False

        elif criterion.type == CriterionType.PERFORMANCE_TARGET:
            try:
                # Assume lower is better (e.g., response time)
                current = float(str_value)
                target_val = float(target)
                return current <= target_val
            except (ValueError, AttributeError):
                return False

        elif criterion.type == CriterionType.UI_MATCH:
            # For UI match, expect a similarity score 0-100
            try:
                similarity = float(str_value)
                threshold = float(target) if target else 95.0
                return similarity >= threshold
            except (ValueError, AttributeError):
                return str_value == target

        else:  # CUSTOM
            # For custom criteria, do string comparison
            return str_value == target.lower()

    def _trigger_callback(self, event: str, *args) -> None:
        """Trigger callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.warning(f"Callback failed for {event}: {e}")
