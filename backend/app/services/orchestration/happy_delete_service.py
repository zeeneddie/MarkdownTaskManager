"""
MP-QW-4: Happy to Delete Service

Track unproductive iterations and recommend restarts.
Treat AI code as disposable - learn from failures, don't salvage them.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Track iteration productivity
- Detect unproductive patterns (2-3 consecutive = restart)
- Generate restart commands (git reset)
- Learn from restart decisions

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class ProductivityLevel(Enum):
    """Level of productivity for an iteration."""
    PRODUCTIVE = "productive"
    NEUTRAL = "neutral"
    UNPRODUCTIVE = "unproductive"
    REGRESSION = "regression"  # Made things worse


class RestartType(Enum):
    """Type of restart to recommend."""
    SOFT = "soft"          # Undo last few changes
    HARD = "hard"          # Full reset to checkpoint
    BRANCH = "branch"      # Start fresh branch
    RETHINK = "rethink"    # Reconsider approach entirely


@dataclass
class Iteration:
    """A single iteration attempt."""
    number: int
    productive: bool
    productivity_level: ProductivityLevel
    reason: str
    timestamp: datetime
    changes_made: Optional[List[str]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RestartRecommendation:
    """Recommendation for restarting."""
    recommended: bool
    restart_type: RestartType
    command: str
    reason: str
    unproductive_count: int
    confidence: float  # 0-1


@dataclass
class IterationTracker:
    """Tracks iterations for a task."""
    id: UUID
    task_id: str
    description: str
    iterations: List[Iteration]
    unproductive_streak: int
    total_unproductive: int
    restart_count: int
    restart_recommended: bool
    last_checkpoint: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RestartEvent:
    """Record of a restart event."""
    id: UUID
    tracker_id: UUID
    timestamp: datetime
    restart_type: RestartType
    command_used: str
    iterations_discarded: int
    reason: str
    learnings: List[str] = field(default_factory=list)


class HappyDeleteService:
    """
    Service for tracking iteration productivity and recommending restarts.

    The "Happy to Delete" mindset means treating AI-generated code as
    disposable. When iterations become unproductive, it's often better
    to restart fresh than to salvage failed attempts.
    """

    # Configuration
    UNPRODUCTIVE_THRESHOLD = 2  # Consecutive unproductive before soft recommend
    HARD_RESTART_THRESHOLD = 3  # Consecutive unproductive before hard recommend
    REGRESSION_THRESHOLD = 1     # Any regression triggers immediate recommend

    def __init__(self):
        self._trackers: Dict[UUID, IterationTracker] = {}
        self._task_trackers: Dict[str, UUID] = {}  # task_id -> tracker_id
        self._restart_events: Dict[UUID, List[RestartEvent]] = {}

    def create_tracker(
        self,
        task_id: str,
        description: str,
        checkpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IterationTracker:
        """
        Create a new iteration tracker for a task.

        Args:
            task_id: Identifier for the task
            description: What we're trying to accomplish
            checkpoint: Git commit/ref to reset to if needed
            metadata: Optional metadata

        Returns:
            Created IterationTracker
        """
        now = datetime.utcnow()
        tracker = IterationTracker(
            id=uuid4(),
            task_id=task_id,
            description=description,
            iterations=[],
            unproductive_streak=0,
            total_unproductive=0,
            restart_count=0,
            restart_recommended=False,
            last_checkpoint=checkpoint,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        self._trackers[tracker.id] = tracker
        self._task_trackers[task_id] = tracker.id
        self._restart_events[tracker.id] = []

        logger.info(f"Created iteration tracker {tracker.id} for task {task_id}")
        return tracker

    def track_iteration(
        self,
        task_id: str,
        productive: bool,
        reason: str,
        productivity_level: Optional[ProductivityLevel] = None,
        changes_made: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> IterationTracker:
        """
        Track an iteration result.

        Args:
            task_id: The task identifier
            productive: Whether the iteration was productive
            reason: Explanation of why it was/wasn't productive
            productivity_level: More granular productivity assessment
            changes_made: List of files/things changed
            metrics: Optional metrics (tests passed, coverage, etc.)

        Returns:
            Updated IterationTracker
        """
        tracker = self._get_or_create_tracker(task_id)

        # Determine productivity level if not provided
        if productivity_level is None:
            productivity_level = ProductivityLevel.PRODUCTIVE if productive else ProductivityLevel.UNPRODUCTIVE

        iteration = Iteration(
            number=len(tracker.iterations) + 1,
            productive=productive,
            productivity_level=productivity_level,
            reason=reason,
            timestamp=datetime.utcnow(),
            changes_made=changes_made,
            metrics=metrics or {},
        )
        tracker.iterations.append(iteration)
        tracker.updated_at = datetime.utcnow()

        # Update streaks and counts
        if productive and productivity_level == ProductivityLevel.PRODUCTIVE:
            tracker.unproductive_streak = 0
        else:
            tracker.unproductive_streak += 1
            tracker.total_unproductive += 1

        # Check if restart should be recommended
        tracker.restart_recommended = self._should_recommend_restart(tracker, productivity_level)

        if tracker.restart_recommended:
            logger.warning(
                f"Restart recommended for task {task_id}: "
                f"{tracker.unproductive_streak} unproductive iterations"
            )

        return tracker

    def check_restart_recommended(self, task_id: str) -> RestartRecommendation:
        """
        Check if a restart is recommended for a task.

        Returns detailed recommendation including type and command.
        """
        tracker = self._get_tracker_by_task(task_id)
        if not tracker:
            return RestartRecommendation(
                recommended=False,
                restart_type=RestartType.SOFT,
                command="",
                reason="No iteration history found",
                unproductive_count=0,
                confidence=0.0,
            )

        # Determine restart type and command
        restart_type, confidence = self._determine_restart_type(tracker)
        command = self._generate_restart_command(tracker, restart_type)
        reason = self._generate_restart_reason(tracker)

        return RestartRecommendation(
            recommended=tracker.restart_recommended,
            restart_type=restart_type,
            command=command,
            reason=reason,
            unproductive_count=tracker.unproductive_streak,
            confidence=confidence,
        )

    def reset_tracking(
        self,
        task_id: str,
        new_checkpoint: Optional[str] = None,
        learnings: Optional[List[str]] = None
    ) -> IterationTracker:
        """
        Reset tracking after a restart.

        Args:
            task_id: The task identifier
            new_checkpoint: New git ref to use as checkpoint
            learnings: What we learned from the failed attempts

        Returns:
            Reset IterationTracker
        """
        tracker = self._get_tracker_by_task(task_id)
        if not tracker:
            return self.create_tracker(task_id, "Reset task", new_checkpoint)

        # Record the restart event
        restart_event = RestartEvent(
            id=uuid4(),
            tracker_id=tracker.id,
            timestamp=datetime.utcnow(),
            restart_type=self._determine_restart_type(tracker)[0],
            command_used=self._generate_restart_command(tracker, RestartType.HARD),
            iterations_discarded=len(tracker.iterations),
            reason=self._generate_restart_reason(tracker),
            learnings=learnings or [],
        )
        self._restart_events[tracker.id].append(restart_event)

        # Reset the tracker
        tracker.iterations = []
        tracker.unproductive_streak = 0
        tracker.restart_recommended = False
        tracker.restart_count += 1
        tracker.updated_at = datetime.utcnow()

        if new_checkpoint:
            tracker.last_checkpoint = new_checkpoint

        logger.info(f"Reset iteration tracker for task {task_id} (restart #{tracker.restart_count})")
        return tracker

    def get_restart_command(
        self,
        task_id: str,
        restart_type: Optional[RestartType] = None
    ) -> str:
        """
        Get the appropriate restart command for a task.

        Args:
            task_id: The task identifier
            restart_type: Specific restart type, or auto-determine

        Returns:
            Git command string to execute
        """
        tracker = self._get_tracker_by_task(task_id)
        if not tracker:
            return "git status  # No iteration history found"

        if restart_type is None:
            restart_type, _ = self._determine_restart_type(tracker)

        return self._generate_restart_command(tracker, restart_type)

    def get_tracker(self, task_id: str) -> Optional[IterationTracker]:
        """Get the tracker for a task."""
        return self._get_tracker_by_task(task_id)

    def get_restart_history(self, task_id: str) -> List[RestartEvent]:
        """Get restart event history for a task."""
        tracker = self._get_tracker_by_task(task_id)
        if not tracker:
            return []
        return self._restart_events.get(tracker.id, [])

    def get_learnings(self, task_id: str) -> List[str]:
        """Get accumulated learnings from restarts."""
        history = self.get_restart_history(task_id)
        learnings = []
        for event in history:
            learnings.extend(event.learnings)
        return learnings

    def get_statistics(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Get productivity statistics."""
        if task_id:
            tracker = self._get_tracker_by_task(task_id)
            if not tracker:
                return {}
            trackers = [tracker]
        else:
            trackers = list(self._trackers.values())

        total_iterations = sum(len(t.iterations) for t in trackers)
        total_productive = sum(
            sum(1 for i in t.iterations if i.productive)
            for t in trackers
        )
        total_restarts = sum(t.restart_count for t in trackers)

        return {
            "total_tasks": len(trackers),
            "total_iterations": total_iterations,
            "productive_iterations": total_productive,
            "unproductive_iterations": total_iterations - total_productive,
            "productivity_rate": (total_productive / total_iterations * 100) if total_iterations > 0 else 0,
            "total_restarts": total_restarts,
            "restarts_triggered": sum(1 for t in trackers if t.restart_recommended),
        }

    def _get_or_create_tracker(self, task_id: str) -> IterationTracker:
        """Get existing tracker or create new one."""
        tracker = self._get_tracker_by_task(task_id)
        if not tracker:
            tracker = self.create_tracker(task_id, f"Auto-created tracker for {task_id}")
        return tracker

    def _get_tracker_by_task(self, task_id: str) -> Optional[IterationTracker]:
        """Get tracker by task ID."""
        tracker_id = self._task_trackers.get(task_id)
        if tracker_id:
            return self._trackers.get(tracker_id)
        return None

    def _should_recommend_restart(
        self,
        tracker: IterationTracker,
        last_level: ProductivityLevel
    ) -> bool:
        """Determine if restart should be recommended."""
        # Immediate restart on regression
        if last_level == ProductivityLevel.REGRESSION:
            return True

        # Check streak thresholds
        if tracker.unproductive_streak >= self.UNPRODUCTIVE_THRESHOLD:
            return True

        return False

    def _determine_restart_type(self, tracker: IterationTracker) -> tuple[RestartType, float]:
        """Determine the appropriate restart type and confidence."""
        streak = tracker.unproductive_streak

        # Check for regression
        if tracker.iterations and tracker.iterations[-1].productivity_level == ProductivityLevel.REGRESSION:
            return RestartType.HARD, 0.95

        # Based on streak length
        if streak >= self.HARD_RESTART_THRESHOLD:
            # Multiple restarts suggest approach is wrong
            if tracker.restart_count >= 2:
                return RestartType.RETHINK, 0.9
            return RestartType.HARD, 0.85

        if streak >= self.UNPRODUCTIVE_THRESHOLD:
            return RestartType.SOFT, 0.7

        return RestartType.SOFT, 0.5

    def _generate_restart_command(self, tracker: IterationTracker, restart_type: RestartType) -> str:
        """Generate the appropriate git command."""
        checkpoint = tracker.last_checkpoint or "HEAD"
        iterations_to_undo = tracker.unproductive_streak

        if restart_type == RestartType.SOFT:
            return f"git reset --soft HEAD~{iterations_to_undo}"

        elif restart_type == RestartType.HARD:
            if tracker.last_checkpoint:
                return f"git reset --hard {checkpoint}"
            return f"git reset --hard HEAD~{iterations_to_undo}"

        elif restart_type == RestartType.BRANCH:
            branch_name = f"fresh-attempt-{tracker.restart_count + 1}"
            return f"git checkout -b {branch_name} {checkpoint}"

        elif restart_type == RestartType.RETHINK:
            return (
                f"# Rethink the approach before continuing\n"
                f"git stash  # Save current work\n"
                f"git checkout {checkpoint}  # Return to checkpoint\n"
                f"# Consider: What's fundamentally wrong with the approach?"
            )

        return f"git status  # Unknown restart type"

    def _generate_restart_reason(self, tracker: IterationTracker) -> str:
        """Generate human-readable restart reason."""
        if not tracker.iterations:
            return "No iterations recorded"

        last_iteration = tracker.iterations[-1]
        streak = tracker.unproductive_streak

        if last_iteration.productivity_level == ProductivityLevel.REGRESSION:
            return f"Regression detected: {last_iteration.reason}"

        if streak >= self.HARD_RESTART_THRESHOLD:
            return f"{streak} consecutive unproductive iterations - hard reset recommended"

        if streak >= self.UNPRODUCTIVE_THRESHOLD:
            return f"{streak} consecutive unproductive iterations - consider fresh start"

        return f"Recent iteration unproductive: {last_iteration.reason}"
