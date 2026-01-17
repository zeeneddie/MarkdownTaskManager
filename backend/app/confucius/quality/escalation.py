"""
Escalation Service for Confucius Orchestrator.

Handles escalation when quality gates cannot be met within
the allowed iterations. Provides fallback strategies, human
escalation, and alternative resolution paths.
"""

from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import json

from .evaluator import EvaluationResult, GateDecision
from .iteration import IterationContext, IterationStatus

logger = logging.getLogger(__name__)


class EscalationType(str, Enum):
    """Types of escalation actions."""
    HUMAN_REVIEW = "human_review"  # Escalate to human
    FALLBACK_AGENT = "fallback_agent"  # Try different agent
    PARTIAL_ACCEPTANCE = "partial_acceptance"  # Accept with limitations
    DECOMPOSITION = "decomposition"  # Break into smaller tasks
    COUNCIL_REVIEW = "council_review"  # Multi-agent review
    ABORT = "abort"  # Abort task


class EscalationPriority(str, Enum):
    """Priority levels for escalations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EscalationTicket:
    """Represents an escalation case."""
    ticket_id: str
    entry_id: str
    agent_name: str
    escalation_type: EscalationType
    priority: EscalationPriority
    reason: str
    context: Dict[str, Any]
    best_attempt: Optional[Dict[str, Any]] = None
    best_score: float = 0.0
    iterations_attempted: int = 0
    violations_summary: List[Dict[str, Any]] = field(default_factory=list)
    recommended_action: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "entry_id": self.entry_id,
            "agent_name": self.agent_name,
            "escalation_type": self.escalation_type.value,
            "priority": self.priority.value,
            "reason": self.reason,
            "best_score": round(self.best_score, 3),
            "iterations_attempted": self.iterations_attempted,
            "violations_count": len(self.violations_summary),
            "recommended_action": self.recommended_action,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution": self.resolution,
            "resolved_by": self.resolved_by,
        }


@dataclass
class EscalationDecision:
    """Decision on how to handle escalation."""
    escalation_type: EscalationType
    priority: EscalationPriority
    action: str
    fallback_agent: Optional[str] = None
    sub_tasks: Optional[List[str]] = None
    accept_with_conditions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_type": self.escalation_type.value,
            "priority": self.priority.value,
            "action": self.action,
            "fallback_agent": self.fallback_agent,
            "sub_tasks": self.sub_tasks,
            "accept_with_conditions": self.accept_with_conditions,
        }


# Type for escalation handler callback
EscalationHandler = Callable[[EscalationTicket], Awaitable[Dict[str, Any]]]


class EscalationService:
    """
    Manages escalation when quality gates fail.

    Provides strategies for handling failed iterations including
    human escalation, fallback agents, and partial acceptance.

    Example:
    ```python
    escalation = EscalationService()

    # Register handlers
    escalation.register_handler(
        EscalationType.HUMAN_REVIEW,
        notify_human_handler,
    )

    # Handle escalation
    decision = await escalation.escalate(
        iter_context=context,
        last_evaluation=evaluation,
    )
    ```
    """

    # Fallback agent mappings
    FALLBACK_AGENTS: Dict[str, List[str]] = {
        "Felix": ["Quinn", "Marcus"],  # Architecture -> Quality, Maintenance
        "Quinn": ["Marcus", "Tessa"],  # Quality -> Maintenance, Testing
        "Eliza": ["Miguel", "Felix"],  # Estimation -> Metrics, Architecture
        "Diana": ["Felix", "Quinn"],  # Documentation -> Architecture, Quality
        "Marcus": ["Felix", "Quinn"],  # Maintenance -> Architecture, Quality
        "Miguel": ["Eliza", "Quinn"],  # Metrics -> Estimation, Quality
        "Tessa": ["Quinn", "Marcus"],  # Testing -> Quality, Maintenance
        "Peter": ["Betty", "Paul"],  # Product -> Business, Planning
        "Paul": ["Peter", "Eliza"],  # Planning -> Product, Estimation
        "Betty": ["Peter", "Paul"],  # Business -> Product, Planning
        "Vicky": ["Diana", "Peter"],  # Design -> Documentation, Product
    }

    def __init__(
        self,
        partial_acceptance_threshold: float = 0.7,
        decomposition_threshold: float = 0.5,
    ):
        """
        Initialize escalation service.

        Args:
            partial_acceptance_threshold: Score above which partial accept is allowed
            decomposition_threshold: Score below which decomposition is recommended
        """
        self._partial_threshold = partial_acceptance_threshold
        self._decomposition_threshold = decomposition_threshold
        self._handlers: Dict[EscalationType, EscalationHandler] = {}
        self._tickets: Dict[str, EscalationTicket] = {}
        self._ticket_counter = 0

    def register_handler(
        self,
        escalation_type: EscalationType,
        handler: EscalationHandler,
    ) -> None:
        """
        Register handler for escalation type.

        Args:
            escalation_type: Type of escalation
            handler: Async handler function
        """
        self._handlers[escalation_type] = handler
        logger.info(f"Registered handler for {escalation_type.value}")

    async def escalate(
        self,
        iter_context: IterationContext,
        last_evaluation: Optional[EvaluationResult] = None,
    ) -> EscalationDecision:
        """
        Handle escalation from failed iteration loop.

        Args:
            iter_context: Iteration context with all attempts
            last_evaluation: Last evaluation result

        Returns:
            EscalationDecision with recommended action
        """
        # Analyze failure patterns
        analysis = self._analyze_failure(iter_context, last_evaluation)

        # Determine escalation type and priority
        escalation_type = self._determine_escalation_type(analysis)
        priority = self._determine_priority(analysis)

        # Create ticket
        ticket = self._create_ticket(
            iter_context=iter_context,
            last_evaluation=last_evaluation,
            escalation_type=escalation_type,
            priority=priority,
            analysis=analysis,
        )

        # Execute handler if registered
        handler_result = None
        if escalation_type in self._handlers:
            try:
                handler_result = await self._handlers[escalation_type](ticket)
            except Exception as e:
                logger.error(f"Escalation handler error: {e}")

        # Build decision
        decision = self._build_decision(
            escalation_type=escalation_type,
            priority=priority,
            analysis=analysis,
            iter_context=iter_context,
            handler_result=handler_result,
        )

        logger.info(
            f"Escalated {iter_context.entry_id}: "
            f"type={escalation_type.value}, priority={priority.value}"
        )

        return decision

    def _analyze_failure(
        self,
        iter_context: IterationContext,
        last_evaluation: Optional[EvaluationResult],
    ) -> Dict[str, Any]:
        """Analyze failure patterns from iterations."""
        analysis = {
            "iterations": iter_context.current_iteration,
            "max_iterations": iter_context.max_iterations,
            "agent": iter_context.agent_name,
            "best_score": 0.0,
            "score_trend": "unknown",
            "common_violations": [],
            "has_critical": False,
            "dimension_weaknesses": [],
        }

        # Analyze all attempts
        scores = []
        all_violations = []

        for attempt in iter_context.attempts:
            if attempt.evaluation:
                scores.append(attempt.evaluation.overall_score)
                analysis["best_score"] = max(
                    analysis["best_score"],
                    attempt.evaluation.overall_score,
                )
                all_violations.extend(
                    [v.to_dict() for v in attempt.evaluation.all_violations]
                )
                if attempt.evaluation.has_critical:
                    analysis["has_critical"] = True

        # Determine score trend
        if len(scores) >= 2:
            if scores[-1] > scores[0]:
                analysis["score_trend"] = "improving"
            elif scores[-1] < scores[0]:
                analysis["score_trend"] = "declining"
            else:
                analysis["score_trend"] = "stable"

        # Find common violations
        violation_counts: Dict[str, int] = {}
        for v in all_violations:
            rule_id = v.get("rule_id", "unknown")
            violation_counts[rule_id] = violation_counts.get(rule_id, 0) + 1

        analysis["common_violations"] = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Identify weak dimensions
        if last_evaluation:
            for dim, score in last_evaluation.dimension_scores.items():
                if score.weighted_average < 0.6:
                    analysis["dimension_weaknesses"].append(dim)

        return analysis

    def _determine_escalation_type(
        self,
        analysis: Dict[str, Any],
    ) -> EscalationType:
        """Determine appropriate escalation type."""
        best_score = analysis.get("best_score", 0.0)
        has_critical = analysis.get("has_critical", False)
        score_trend = analysis.get("score_trend", "unknown")

        # Critical issues require human review
        if has_critical:
            return EscalationType.HUMAN_REVIEW

        # Very low score suggests decomposition
        if best_score < self._decomposition_threshold:
            return EscalationType.DECOMPOSITION

        # Improving but not enough - try fallback agent
        if score_trend == "improving" and best_score < 0.8:
            return EscalationType.FALLBACK_AGENT

        # Close to threshold - partial acceptance
        if best_score >= self._partial_threshold:
            return EscalationType.PARTIAL_ACCEPTANCE

        # Default to council review
        return EscalationType.COUNCIL_REVIEW

    def _determine_priority(
        self,
        analysis: Dict[str, Any],
    ) -> EscalationPriority:
        """Determine escalation priority."""
        has_critical = analysis.get("has_critical", False)
        best_score = analysis.get("best_score", 0.0)
        iterations = analysis.get("iterations", 0)

        if has_critical:
            return EscalationPriority.CRITICAL

        if best_score < 0.3:
            return EscalationPriority.HIGH

        if iterations >= 3 and best_score < 0.7:
            return EscalationPriority.MEDIUM

        return EscalationPriority.LOW

    def _create_ticket(
        self,
        iter_context: IterationContext,
        last_evaluation: Optional[EvaluationResult],
        escalation_type: EscalationType,
        priority: EscalationPriority,
        analysis: Dict[str, Any],
    ) -> EscalationTicket:
        """Create escalation ticket."""
        self._ticket_counter += 1
        ticket_id = f"ESC-{self._ticket_counter:05d}"

        # Get best attempt
        best_attempt = None
        best_score = 0.0
        for attempt in iter_context.attempts:
            if attempt.evaluation and attempt.output:
                if attempt.evaluation.overall_score > best_score:
                    best_score = attempt.evaluation.overall_score
                    best_attempt = attempt.output

        # Summarize violations
        violations_summary = []
        if last_evaluation:
            for v in last_evaluation.all_violations[:10]:
                violations_summary.append(v.to_dict())

        ticket = EscalationTicket(
            ticket_id=ticket_id,
            entry_id=iter_context.entry_id,
            agent_name=iter_context.agent_name,
            escalation_type=escalation_type,
            priority=priority,
            reason=self._build_reason(analysis),
            context={
                "original_task": iter_context.original_task,
                "analysis": analysis,
            },
            best_attempt=best_attempt,
            best_score=best_score,
            iterations_attempted=iter_context.current_iteration,
            violations_summary=violations_summary,
            recommended_action=self._recommend_action(escalation_type, analysis),
        )

        self._tickets[ticket_id] = ticket
        return ticket

    def _build_reason(self, analysis: Dict[str, Any]) -> str:
        """Build human-readable escalation reason."""
        parts = [
            f"Quality gate failed after {analysis['iterations']} iterations",
            f"Best score achieved: {analysis['best_score']:.2f}",
        ]

        if analysis.get("has_critical"):
            parts.append("Contains critical violations")

        if analysis.get("dimension_weaknesses"):
            parts.append(f"Weak dimensions: {', '.join(analysis['dimension_weaknesses'])}")

        return ". ".join(parts)

    def _recommend_action(
        self,
        escalation_type: EscalationType,
        analysis: Dict[str, Any],
    ) -> str:
        """Generate recommended action."""
        if escalation_type == EscalationType.HUMAN_REVIEW:
            return "Review output manually and address critical violations"

        if escalation_type == EscalationType.FALLBACK_AGENT:
            agent = analysis.get("agent", "")
            fallbacks = self.FALLBACK_AGENTS.get(agent, [])
            if fallbacks:
                return f"Try with fallback agent: {fallbacks[0]}"
            return "Try with alternative agent"

        if escalation_type == EscalationType.DECOMPOSITION:
            return "Break task into smaller sub-tasks"

        if escalation_type == EscalationType.PARTIAL_ACCEPTANCE:
            return "Accept output with documented limitations"

        if escalation_type == EscalationType.COUNCIL_REVIEW:
            return "Submit for multi-agent council review"

        return "Manual intervention required"

    def _build_decision(
        self,
        escalation_type: EscalationType,
        priority: EscalationPriority,
        analysis: Dict[str, Any],
        iter_context: IterationContext,
        handler_result: Optional[Dict[str, Any]],
    ) -> EscalationDecision:
        """Build escalation decision."""
        decision = EscalationDecision(
            escalation_type=escalation_type,
            priority=priority,
            action=self._recommend_action(escalation_type, analysis),
        )

        # Add type-specific details
        if escalation_type == EscalationType.FALLBACK_AGENT:
            fallbacks = self.FALLBACK_AGENTS.get(iter_context.agent_name, [])
            decision.fallback_agent = fallbacks[0] if fallbacks else None

        elif escalation_type == EscalationType.DECOMPOSITION:
            decision.sub_tasks = self._suggest_sub_tasks(
                iter_context.original_task,
                analysis,
            )

        elif escalation_type == EscalationType.PARTIAL_ACCEPTANCE:
            decision.accept_with_conditions = self._build_acceptance_conditions(
                analysis,
            )

        return decision

    def _suggest_sub_tasks(
        self,
        task: str,
        analysis: Dict[str, Any],
    ) -> List[str]:
        """Suggest sub-tasks for decomposition."""
        sub_tasks = []

        # Based on weak dimensions, suggest focused sub-tasks
        weaknesses = analysis.get("dimension_weaknesses", [])

        if "completeness" in weaknesses:
            sub_tasks.append(f"Gather complete requirements for: {task[:50]}...")

        if "accuracy" in weaknesses:
            sub_tasks.append(f"Validate assumptions for: {task[:50]}...")

        if "coverage" in weaknesses:
            sub_tasks.append(f"Identify all components affected by: {task[:50]}...")

        # Default decomposition
        if not sub_tasks:
            sub_tasks = [
                f"Analyze scope for: {task[:50]}...",
                f"Implement core functionality for: {task[:50]}...",
                f"Validate and document: {task[:50]}...",
            ]

        return sub_tasks

    def _build_acceptance_conditions(
        self,
        analysis: Dict[str, Any],
    ) -> List[str]:
        """Build conditions for partial acceptance."""
        conditions = []

        weaknesses = analysis.get("dimension_weaknesses", [])

        for weakness in weaknesses:
            conditions.append(f"Limited {weakness} - manual review required")

        if analysis.get("common_violations"):
            top_violation = analysis["common_violations"][0][0]
            conditions.append(f"Known issue: {top_violation}")

        conditions.append(f"Best score achieved: {analysis['best_score']:.2f}")

        return conditions

    def get_ticket(self, ticket_id: str) -> Optional[EscalationTicket]:
        """Get ticket by ID."""
        return self._tickets.get(ticket_id)

    def get_open_tickets(self) -> List[EscalationTicket]:
        """Get all unresolved tickets."""
        return [t for t in self._tickets.values() if t.resolved_at is None]

    async def resolve_ticket(
        self,
        ticket_id: str,
        resolution: str,
        resolved_by: str,
    ) -> bool:
        """
        Mark ticket as resolved.

        Args:
            ticket_id: Ticket to resolve
            resolution: Resolution description
            resolved_by: Who resolved it

        Returns:
            True if resolved, False if not found
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return False

        ticket.resolved_at = datetime.now(timezone.utc)
        ticket.resolution = resolution
        ticket.resolved_by = resolved_by

        logger.info(f"Resolved escalation {ticket_id}: {resolution}")
        return True

    def get_escalation_stats(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        tickets = list(self._tickets.values())

        if not tickets:
            return {
                "total_tickets": 0,
                "open_tickets": 0,
                "resolved_tickets": 0,
                "by_type": {},
                "by_priority": {},
            }

        by_type: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        resolved = 0

        for ticket in tickets:
            by_type[ticket.escalation_type.value] = (
                by_type.get(ticket.escalation_type.value, 0) + 1
            )
            by_priority[ticket.priority.value] = (
                by_priority.get(ticket.priority.value, 0) + 1
            )
            if ticket.resolved_at:
                resolved += 1

        return {
            "total_tickets": len(tickets),
            "open_tickets": len(tickets) - resolved,
            "resolved_tickets": resolved,
            "by_type": by_type,
            "by_priority": by_priority,
        }


def create_escalation_service(
    partial_threshold: float = 0.7,
) -> EscalationService:
    """
    Factory function to create escalation service.

    Args:
        partial_threshold: Threshold for partial acceptance

    Returns:
        Configured EscalationService
    """
    return EscalationService(
        partial_acceptance_threshold=partial_threshold,
    )
