"""
Iteration Controller for Confucius Orchestrator.

Manages the Plan-Implement-Validate (PIV) loop with quality-based
retry logic, iteration tracking, and improvement strategies.
"""

from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import asyncio

from .evaluator import (
    QualityGateEvaluator,
    EvaluationResult,
    GateDecision,
)

logger = logging.getLogger(__name__)


class IterationStatus(str, Enum):
    """Status of an iteration cycle."""
    PENDING = "pending"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ESCALATED = "escalated"


class ImprovementStrategy(str, Enum):
    """Strategies for improving on retry."""
    FEEDBACK_BASED = "feedback_based"  # Use violation feedback
    PROMPT_REFINEMENT = "prompt_refinement"  # Refine the prompt
    CONTEXT_ENRICHMENT = "context_enrichment"  # Add more context
    DECOMPOSITION = "decomposition"  # Break into sub-tasks
    AGENT_SWITCH = "agent_switch"  # Try different agent


@dataclass
class IterationAttempt:
    """Record of a single iteration attempt."""
    iteration: int
    status: IterationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    evaluation: Optional[EvaluationResult] = None
    strategy_used: Optional[ImprovementStrategy] = None
    error: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        """Duration in milliseconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "strategy_used": self.strategy_used.value if self.strategy_used else None,
            "error": self.error,
            "evaluation_score": self.evaluation.overall_score if self.evaluation else None,
        }


@dataclass
class IterationContext:
    """Context maintained across iterations."""
    entry_id: str
    agent_name: str
    original_task: str
    original_context: Dict[str, Any]
    max_iterations: int = 3
    current_iteration: int = 0
    attempts: List[IterationAttempt] = field(default_factory=list)
    accumulated_feedback: List[str] = field(default_factory=list)
    final_result: Optional[Dict[str, Any]] = None
    final_status: IterationStatus = IterationStatus.PENDING

    def add_feedback(self, feedback: str) -> None:
        """Add feedback from failed iteration."""
        self.accumulated_feedback.append(feedback)

    def get_enriched_context(self) -> Dict[str, Any]:
        """Get context enriched with iteration history."""
        ctx = self.original_context.copy()
        ctx["iteration"] = self.current_iteration
        ctx["max_iterations"] = self.max_iterations
        ctx["previous_feedback"] = self.accumulated_feedback
        ctx["attempt_count"] = len(self.attempts)
        return ctx

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "agent_name": self.agent_name,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "attempts": [a.to_dict() for a in self.attempts],
            "accumulated_feedback_count": len(self.accumulated_feedback),
            "final_status": self.final_status.value,
        }


# Type for agent execution function
AgentExecutor = Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]

# Type for progress callback
ProgressCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]


class IterationController:
    """
    Controls the PIV (Plan-Implement-Validate) iteration loop.

    Manages retry logic, quality evaluation, and improvement strategies
    to achieve quality gates within allowed iterations.

    Example:
    ```python
    controller = IterationController(
        evaluator=QualityGateEvaluator(),
        max_iterations=3,
    )

    result = await controller.run_with_quality_gate(
        task="Analyze architecture",
        context={"domain": "architecture"},
        agent_executor=felix_extension.execute,
        entry_id="task-123",
        agent_name="Felix",
    )
    ```
    """

    def __init__(
        self,
        evaluator: QualityGateEvaluator,
        max_iterations: int = 3,
        base_delay_ms: int = 100,
        improvement_strategy: ImprovementStrategy = ImprovementStrategy.FEEDBACK_BASED,
    ):
        """
        Initialize iteration controller.

        Args:
            evaluator: Quality gate evaluator
            max_iterations: Maximum retry attempts
            base_delay_ms: Base delay between retries
            improvement_strategy: Default improvement strategy
        """
        self._evaluator = evaluator
        self._max_iterations = max_iterations
        self._base_delay_ms = base_delay_ms
        self._default_strategy = improvement_strategy
        self._progress_callback: Optional[ProgressCallback] = None

    def set_progress_callback(self, callback: ProgressCallback) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback

    async def run_with_quality_gate(
        self,
        task: str,
        context: Dict[str, Any],
        agent_executor: AgentExecutor,
        entry_id: str,
        agent_name: str,
        threshold_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute task with quality gate validation and retry loop.

        Args:
            task: Task description
            context: Task context
            agent_executor: Async function to execute task
            entry_id: Unique task ID
            agent_name: Name of executing agent
            threshold_override: Override quality threshold

        Returns:
            Final output or best attempt output
        """
        iter_context = IterationContext(
            entry_id=entry_id,
            agent_name=agent_name,
            original_task=task,
            original_context=context,
            max_iterations=self._max_iterations,
        )

        await self._emit_progress("iteration_started", {
            "entry_id": entry_id,
            "agent_name": agent_name,
            "max_iterations": self._max_iterations,
        })

        while iter_context.current_iteration < self._max_iterations:
            iter_context.current_iteration += 1

            attempt = await self._run_iteration(
                iter_context,
                agent_executor,
                threshold_override,
            )

            if attempt.status == IterationStatus.SUCCEEDED:
                iter_context.final_status = IterationStatus.SUCCEEDED
                iter_context.final_result = attempt.output
                break

            elif attempt.status == IterationStatus.FAILED:
                # Add feedback for next iteration
                if attempt.evaluation and attempt.evaluation.feedback_for_retry:
                    iter_context.add_feedback(attempt.evaluation.feedback_for_retry)

                # Check if we should continue
                if iter_context.current_iteration >= self._max_iterations:
                    iter_context.final_status = IterationStatus.ESCALATED
                    iter_context.final_result = self._get_best_attempt(iter_context)
                    break

                # Apply delay before retry
                delay = self._calculate_delay(iter_context.current_iteration)
                await asyncio.sleep(delay / 1000)

        await self._emit_progress("iteration_completed", {
            "entry_id": entry_id,
            "final_status": iter_context.final_status.value,
            "total_iterations": iter_context.current_iteration,
        })

        return self._build_final_result(iter_context)

    async def _run_iteration(
        self,
        iter_context: IterationContext,
        agent_executor: AgentExecutor,
        threshold_override: Optional[float],
    ) -> IterationAttempt:
        """Run a single iteration of the PIV loop."""
        attempt = IterationAttempt(
            iteration=iter_context.current_iteration,
            status=IterationStatus.IMPLEMENTING,
            started_at=datetime.now(timezone.utc),
        )
        iter_context.attempts.append(attempt)

        # Determine improvement strategy for retries
        strategy = None
        if iter_context.current_iteration > 1:
            strategy = self._select_strategy(iter_context)
            attempt.strategy_used = strategy

        await self._emit_progress("iteration_executing", {
            "iteration": iter_context.current_iteration,
            "strategy": strategy.value if strategy else None,
        })

        try:
            # Prepare context based on strategy
            enriched_context = self._apply_strategy(
                iter_context.get_enriched_context(),
                strategy,
                iter_context,
            )

            # Execute agent
            attempt.status = IterationStatus.IMPLEMENTING
            output = await agent_executor(iter_context.original_task, enriched_context)
            attempt.output = output

            # Validate output
            attempt.status = IterationStatus.VALIDATING
            evaluation = self._evaluator.evaluate(
                output=output,
                context=enriched_context,
                entry_id=iter_context.entry_id,
                agent_name=iter_context.agent_name,
                iteration=iter_context.current_iteration,
                threshold_override=threshold_override,
            )
            attempt.evaluation = evaluation

            await self._emit_progress("iteration_evaluated", {
                "iteration": iter_context.current_iteration,
                "score": evaluation.overall_score,
                "decision": evaluation.decision.value,
                "violations": len(evaluation.all_violations),
            })

            # Determine success
            if evaluation.decision in [GateDecision.PASS, GateDecision.WARN]:
                attempt.status = IterationStatus.SUCCEEDED
                logger.info(
                    f"Iteration {iter_context.current_iteration} succeeded: "
                    f"score={evaluation.overall_score:.2f}"
                )
            else:
                attempt.status = IterationStatus.FAILED
                logger.warning(
                    f"Iteration {iter_context.current_iteration} failed: "
                    f"score={evaluation.overall_score:.2f}"
                )

        except Exception as e:
            logger.error(f"Iteration {iter_context.current_iteration} error: {e}")
            attempt.status = IterationStatus.FAILED
            attempt.error = str(e)

        attempt.completed_at = datetime.now(timezone.utc)
        return attempt

    def _select_strategy(
        self,
        iter_context: IterationContext,
    ) -> ImprovementStrategy:
        """Select improvement strategy based on failure patterns."""
        if not iter_context.attempts:
            return self._default_strategy

        last_attempt = iter_context.attempts[-1]

        # If last attempt had critical violations, try decomposition
        if last_attempt.evaluation and last_attempt.evaluation.has_critical:
            return ImprovementStrategy.DECOMPOSITION

        # If score was close to threshold, try prompt refinement
        if last_attempt.evaluation:
            score = last_attempt.evaluation.overall_score
            threshold = last_attempt.evaluation.threshold
            if score > threshold * 0.9:  # Within 10% of threshold
                return ImprovementStrategy.PROMPT_REFINEMENT

        # Default to feedback-based
        return self._default_strategy

    def _apply_strategy(
        self,
        context: Dict[str, Any],
        strategy: Optional[ImprovementStrategy],
        iter_context: IterationContext,
    ) -> Dict[str, Any]:
        """Apply improvement strategy to context."""
        if not strategy:
            return context

        ctx = context.copy()

        if strategy == ImprovementStrategy.FEEDBACK_BASED:
            # Include all previous feedback
            ctx["improvement_feedback"] = iter_context.accumulated_feedback
            ctx["improvement_strategy"] = "address_feedback"

        elif strategy == ImprovementStrategy.PROMPT_REFINEMENT:
            # Add prompt hints based on weaknesses
            ctx["prompt_refinement"] = True
            ctx["focus_areas"] = self._identify_weak_areas(iter_context)

        elif strategy == ImprovementStrategy.CONTEXT_ENRICHMENT:
            # Request more detailed analysis
            ctx["detail_level"] = "high"
            ctx["include_explanations"] = True

        elif strategy == ImprovementStrategy.DECOMPOSITION:
            # Mark for sub-task decomposition
            ctx["decompose_task"] = True
            ctx["sub_task_mode"] = True

        return ctx

    def _identify_weak_areas(
        self,
        iter_context: IterationContext,
    ) -> List[str]:
        """Identify weak quality dimensions from attempts."""
        weak_areas = []

        for attempt in iter_context.attempts:
            if attempt.evaluation:
                for dim, score in attempt.evaluation.dimension_scores.items():
                    if score.weighted_average < 0.7:
                        weak_areas.append(dim)

        return list(set(weak_areas))

    def _calculate_delay(self, iteration: int) -> int:
        """Calculate delay before retry (exponential backoff)."""
        return self._base_delay_ms * (2 ** (iteration - 1))

    def _get_best_attempt(
        self,
        iter_context: IterationContext,
    ) -> Optional[Dict[str, Any]]:
        """Get best output from all attempts."""
        best_score = -1.0
        best_output = None

        for attempt in iter_context.attempts:
            if attempt.evaluation and attempt.output:
                if attempt.evaluation.overall_score > best_score:
                    best_score = attempt.evaluation.overall_score
                    best_output = attempt.output

        return best_output

    def _build_final_result(
        self,
        iter_context: IterationContext,
    ) -> Dict[str, Any]:
        """Build final result from iteration context."""
        final_output = iter_context.final_result or {}

        return {
            **final_output,
            "_iteration_metadata": {
                "entry_id": iter_context.entry_id,
                "agent_name": iter_context.agent_name,
                "final_status": iter_context.final_status.value,
                "total_iterations": iter_context.current_iteration,
                "max_iterations": self._max_iterations,
                "attempts_summary": [a.to_dict() for a in iter_context.attempts],
                "feedback_accumulated": len(iter_context.accumulated_feedback),
            },
        }

    async def _emit_progress(
        self,
        event: str,
        data: Dict[str, Any],
    ) -> None:
        """Emit progress event via callback."""
        if self._progress_callback:
            try:
                await self._progress_callback(event, data)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")


def create_iteration_controller(
    evaluator: Optional[QualityGateEvaluator] = None,
    max_iterations: int = 3,
) -> IterationController:
    """
    Factory function to create iteration controller.

    Args:
        evaluator: Quality evaluator (created if not provided)
        max_iterations: Maximum iterations

    Returns:
        Configured IterationController
    """
    from .evaluator import create_evaluator

    if evaluator is None:
        evaluator = create_evaluator()

    return IterationController(
        evaluator=evaluator,
        max_iterations=max_iterations,
    )
