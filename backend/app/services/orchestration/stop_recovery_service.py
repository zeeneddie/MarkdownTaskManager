"""
MP-QW-8: Stop & Recovery Service

Emergency halt when agent goes off-rails.
Prevent context contamination and enable clean recovery.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Immediate stop on divergence
- Context contamination prevention
- Recovery options (checkpoint, clean restart, ask-don't-tell)
- Stop event history and learning

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class StopReason(Enum):
    """Reasons for triggering a stop."""
    DIVERGENCE_DETECTED = "divergence_detected"
    CONTEXT_CONTAMINATION = "context_contamination"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    HYPOTHESIS_VIOLATED = "hypothesis_violated"
    SCOPE_CREEP = "scope_creep"
    USER_REQUESTED = "user_requested"
    MAX_ITERATIONS = "max_iterations"
    ERROR_LOOP = "error_loop"
    ANTIPATTERN_DETECTED = "antipattern_detected"
    TIMEOUT = "timeout"


class RecoveryType(Enum):
    """Types of recovery actions."""
    RESTART_CLEAN = "restart_clean"
    RESTORE_CHECKPOINT = "restore_checkpoint"
    ASK_DONT_TELL = "ask_dont_tell"
    ROLLBACK_CHANGES = "rollback_changes"
    SWITCH_APPROACH = "switch_approach"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    REDUCE_SCOPE = "reduce_scope"


class StopEventStatus(Enum):
    """Status of a stop event."""
    ACTIVE = "active"
    RECOVERING = "recovering"
    RECOVERED = "recovered"
    ESCALATED = "escalated"


@dataclass
class RecoveryOption:
    """A recovery option for a stop event."""
    type: RecoveryType
    description: str
    command: Optional[str]
    recommended: bool
    confidence: float  # 0-1
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class RecoveryResult:
    """Result of executing a recovery action."""
    success: bool
    recovery_type: RecoveryType
    message: str
    new_checkpoint: Optional[str] = None
    changes_reverted: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StopEvent:
    """An emergency stop event."""
    id: UUID
    session_id: UUID
    reason: StopReason
    severity: str  # "warning", "error", "critical"
    details: str
    context: Dict[str, Any]
    checkpoint_id: Optional[UUID]
    checkpoint_ref: Optional[str]  # Git ref or similar
    recovery_options: List[RecoveryOption]
    status: StopEventStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    recovery_result: Optional[RecoveryResult] = None
    contaminated_files: List[str] = field(default_factory=list)
    contaminated_context: List[str] = field(default_factory=list)


@dataclass
class SessionState:
    """State of a session for stop/recovery purposes."""
    session_id: UUID
    active: bool
    last_checkpoint: Optional[str]
    stop_count: int
    current_stop: Optional[UUID]
    contamination_level: float  # 0-1
    recovery_history: List[UUID]


class StopRecoveryService:
    """
    Service for emergency stop and recovery.

    Implements the "Stop" pattern - keeping your finger on the stop
    button to halt agents quickly when they deviate, preventing
    context contamination.
    """

    # Severity mapping for stop reasons
    REASON_SEVERITY = {
        StopReason.USER_REQUESTED: "warning",
        StopReason.TIMEOUT: "warning",
        StopReason.MAX_ITERATIONS: "warning",
        StopReason.DIVERGENCE_DETECTED: "error",
        StopReason.SCOPE_CREEP: "error",
        StopReason.QUALITY_GATE_FAILED: "error",
        StopReason.HYPOTHESIS_VIOLATED: "error",
        StopReason.ANTIPATTERN_DETECTED: "error",
        StopReason.CONTEXT_CONTAMINATION: "critical",
        StopReason.ERROR_LOOP: "critical",
    }

    def __init__(self):
        self._stop_events: Dict[UUID, StopEvent] = {}
        self._session_states: Dict[UUID, SessionState] = {}
        self._session_stops: Dict[UUID, List[UUID]] = {}  # session_id -> stop_event_ids
        self._callbacks: Dict[str, List[Callable]] = {
            "on_stop": [],
            "on_recovery": [],
            "on_escalate": [],
        }

    def trigger_stop(
        self,
        session_id: UUID,
        reason: StopReason,
        details: str,
        context: Optional[Dict[str, Any]] = None,
        checkpoint_id: Optional[UUID] = None,
        checkpoint_ref: Optional[str] = None,
        contaminated_files: Optional[List[str]] = None,
        contaminated_context: Optional[List[str]] = None
    ) -> StopEvent:
        """
        Trigger an emergency stop.

        Args:
            session_id: The session to stop
            reason: Why we're stopping
            details: Human-readable explanation
            context: Additional context
            checkpoint_id: ID of last known good checkpoint
            checkpoint_ref: Git ref or similar for checkpoint
            contaminated_files: Files that may be contaminated
            contaminated_context: Context items that may be contaminated

        Returns:
            Created StopEvent
        """
        now = datetime.now(timezone.utc)
        severity = self.REASON_SEVERITY.get(reason, "error")

        # Generate recovery options
        recovery_options = self._generate_recovery_options(reason, checkpoint_ref)

        stop_event = StopEvent(
            id=uuid4(),
            session_id=session_id,
            reason=reason,
            severity=severity,
            details=details,
            context=context or {},
            checkpoint_id=checkpoint_id,
            checkpoint_ref=checkpoint_ref,
            recovery_options=recovery_options,
            status=StopEventStatus.ACTIVE,
            created_at=now,
            contaminated_files=contaminated_files or [],
            contaminated_context=contaminated_context or [],
        )

        self._stop_events[stop_event.id] = stop_event

        # Update session state
        if session_id not in self._session_stops:
            self._session_stops[session_id] = []
        self._session_stops[session_id].append(stop_event.id)

        self._update_session_state(session_id, stop_event)

        # Trigger callbacks
        self._trigger_callback("on_stop", stop_event)

        logger.warning(
            f"STOP triggered for session {session_id}: {reason.value} - {details}"
        )

        return stop_event

    def get_recovery_options(self, stop_event_id: UUID) -> List[RecoveryOption]:
        """Get available recovery options for a stop event."""
        event = self._stop_events.get(stop_event_id)
        if not event:
            raise ValueError(f"Stop event {stop_event_id} not found")

        return event.recovery_options

    def execute_recovery(
        self,
        stop_event_id: UUID,
        recovery_type: RecoveryType,
        params: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """
        Execute a recovery action.

        Args:
            stop_event_id: The stop event to recover from
            recovery_type: Type of recovery to execute
            params: Additional parameters for recovery

        Returns:
            RecoveryResult indicating success/failure
        """
        event = self._stop_events.get(stop_event_id)
        if not event:
            raise ValueError(f"Stop event {stop_event_id} not found")

        if event.status == StopEventStatus.RECOVERED:
            raise ValueError(f"Stop event {stop_event_id} already recovered")

        event.status = StopEventStatus.RECOVERING

        # Execute recovery based on type
        result = self._execute_recovery_action(event, recovery_type, params or {})

        if result.success:
            event.status = StopEventStatus.RECOVERED
            event.resolved_at = datetime.now(timezone.utc)
            event.recovery_result = result

            # Update session state
            session_state = self._session_states.get(event.session_id)
            if session_state:
                session_state.current_stop = None
                session_state.recovery_history.append(event.id)
                if result.new_checkpoint:
                    session_state.last_checkpoint = result.new_checkpoint

            # Trigger callback
            self._trigger_callback("on_recovery", event, result)

            logger.info(f"Recovery successful for stop event {stop_event_id}: {recovery_type.value}")
        else:
            event.status = StopEventStatus.ACTIVE
            logger.error(f"Recovery failed for stop event {stop_event_id}: {result.message}")

        return result

    def prevent_context_contamination(
        self,
        session_id: UUID,
        contaminated_items: List[str]
    ) -> Dict[str, Any]:
        """
        Prevent context contamination by marking items as tainted.

        Args:
            session_id: The session
            contaminated_items: Items to mark as contaminated

        Returns:
            Summary of contamination prevention actions
        """
        session_state = self._get_or_create_session_state(session_id)

        # Update contamination level
        session_state.contamination_level = min(
            1.0,
            session_state.contamination_level + (len(contaminated_items) * 0.1)
        )

        actions = []
        for item in contaminated_items:
            actions.append({
                "item": item,
                "action": "marked_contaminated",
                "recommendation": "exclude_from_context"
            })

        result = {
            "session_id": str(session_id),
            "items_marked": len(contaminated_items),
            "contamination_level": session_state.contamination_level,
            "actions": actions,
            "recommendation": self._get_contamination_recommendation(session_state.contamination_level)
        }

        logger.info(f"Marked {len(contaminated_items)} items as contaminated for session {session_id}")
        return result

    def get_stop_history(
        self,
        session_id: UUID,
        include_resolved: bool = True
    ) -> List[StopEvent]:
        """Get stop event history for a session."""
        stop_ids = self._session_stops.get(session_id, [])
        events = [self._stop_events[sid] for sid in stop_ids if sid in self._stop_events]

        if not include_resolved:
            events = [e for e in events if e.status != StopEventStatus.RECOVERED]

        return sorted(events, key=lambda e: e.created_at, reverse=True)

    def get_active_stop(self, session_id: UUID) -> Optional[StopEvent]:
        """Get the active stop event for a session, if any."""
        session_state = self._session_states.get(session_id)
        if session_state and session_state.current_stop:
            return self._stop_events.get(session_state.current_stop)
        return None

    def escalate_stop(self, stop_event_id: UUID, reason: str) -> StopEvent:
        """Escalate a stop event to human review."""
        event = self._stop_events.get(stop_event_id)
        if not event:
            raise ValueError(f"Stop event {stop_event_id} not found")

        event.status = StopEventStatus.ESCALATED
        event.context["escalation_reason"] = reason
        event.context["escalated_at"] = datetime.now(timezone.utc).isoformat()

        self._trigger_callback("on_escalate", event, reason)

        logger.warning(f"Stop event {stop_event_id} escalated: {reason}")
        return event

    def set_checkpoint(self, session_id: UUID, checkpoint_ref: str) -> None:
        """Set a checkpoint for a session."""
        session_state = self._get_or_create_session_state(session_id)
        session_state.last_checkpoint = checkpoint_ref
        logger.info(f"Checkpoint set for session {session_id}: {checkpoint_ref}")

    def get_session_state(self, session_id: UUID) -> Optional[SessionState]:
        """Get session state."""
        return self._session_states.get(session_id)

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for stop/recovery events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _generate_recovery_options(
        self,
        reason: StopReason,
        checkpoint_ref: Optional[str]
    ) -> List[RecoveryOption]:
        """Generate recovery options based on stop reason."""
        options = []

        # Always offer ask-don't-tell
        options.append(RecoveryOption(
            type=RecoveryType.ASK_DONT_TELL,
            description="Clarify the goal before proceeding",
            command=None,
            recommended=(reason == StopReason.DIVERGENCE_DETECTED),
            confidence=0.7,
        ))

        # Checkpoint recovery if available
        if checkpoint_ref:
            options.append(RecoveryOption(
                type=RecoveryType.RESTORE_CHECKPOINT,
                description=f"Restore to checkpoint: {checkpoint_ref}",
                command=f"git checkout {checkpoint_ref}",
                recommended=(reason in (StopReason.CONTEXT_CONTAMINATION, StopReason.ERROR_LOOP)),
                confidence=0.85,
            ))

        # Rollback changes
        options.append(RecoveryOption(
            type=RecoveryType.ROLLBACK_CHANGES,
            description="Undo recent changes",
            command="git reset --hard HEAD~1",
            recommended=(reason == StopReason.QUALITY_GATE_FAILED),
            confidence=0.75,
        ))

        # Clean restart
        options.append(RecoveryOption(
            type=RecoveryType.RESTART_CLEAN,
            description="Start fresh with clean context",
            command=None,
            recommended=(reason == StopReason.CONTEXT_CONTAMINATION),
            confidence=0.8,
        ))

        # Switch approach
        if reason in (StopReason.MAX_ITERATIONS, StopReason.ERROR_LOOP):
            options.append(RecoveryOption(
                type=RecoveryType.SWITCH_APPROACH,
                description="Try a different approach to the problem",
                command=None,
                recommended=True,
                confidence=0.7,
            ))

        # Reduce scope
        if reason == StopReason.SCOPE_CREEP:
            options.append(RecoveryOption(
                type=RecoveryType.REDUCE_SCOPE,
                description="Focus on core requirements only",
                command=None,
                recommended=True,
                confidence=0.85,
            ))

        # Human escalation
        options.append(RecoveryOption(
            type=RecoveryType.ESCALATE_TO_HUMAN,
            description="Escalate to human for decision",
            command=None,
            recommended=(reason == StopReason.ANTIPATTERN_DETECTED),
            confidence=0.6,
            prerequisites=["Human availability"],
        ))

        return sorted(options, key=lambda o: (o.recommended, o.confidence), reverse=True)

    def _execute_recovery_action(
        self,
        event: StopEvent,
        recovery_type: RecoveryType,
        params: Dict[str, Any]
    ) -> RecoveryResult:
        """Execute a specific recovery action."""
        if recovery_type == RecoveryType.RESTART_CLEAN:
            return RecoveryResult(
                success=True,
                recovery_type=recovery_type,
                message="Clean restart initiated - context cleared",
                new_checkpoint=None,
            )

        elif recovery_type == RecoveryType.RESTORE_CHECKPOINT:
            checkpoint = params.get("checkpoint") or event.checkpoint_ref
            if not checkpoint:
                return RecoveryResult(
                    success=False,
                    recovery_type=recovery_type,
                    message="No checkpoint available for restore",
                )
            return RecoveryResult(
                success=True,
                recovery_type=recovery_type,
                message=f"Restored to checkpoint: {checkpoint}",
                new_checkpoint=checkpoint,
            )

        elif recovery_type == RecoveryType.ROLLBACK_CHANGES:
            changes = len(event.contaminated_files)
            return RecoveryResult(
                success=True,
                recovery_type=recovery_type,
                message=f"Rolled back {changes} contaminated changes",
                changes_reverted=changes,
            )

        elif recovery_type == RecoveryType.ASK_DONT_TELL:
            return RecoveryResult(
                success=True,
                recovery_type=recovery_type,
                message="Switching to ask-don't-tell mode - awaiting clarification",
            )

        elif recovery_type == RecoveryType.SWITCH_APPROACH:
            return RecoveryResult(
                success=True,
                recovery_type=recovery_type,
                message="Ready to try alternative approach",
            )

        elif recovery_type == RecoveryType.REDUCE_SCOPE:
            return RecoveryResult(
                success=True,
                recovery_type=recovery_type,
                message="Scope reduced to core requirements",
            )

        elif recovery_type == RecoveryType.ESCALATE_TO_HUMAN:
            return RecoveryResult(
                success=True,
                recovery_type=recovery_type,
                message="Escalated to human - awaiting response",
            )

        return RecoveryResult(
            success=False,
            recovery_type=recovery_type,
            message=f"Unknown recovery type: {recovery_type}",
        )

    def _update_session_state(self, session_id: UUID, stop_event: StopEvent) -> None:
        """Update session state after a stop."""
        state = self._get_or_create_session_state(session_id)
        state.stop_count += 1
        state.current_stop = stop_event.id

        # Increase contamination based on severity
        severity_impact = {"warning": 0.1, "error": 0.25, "critical": 0.5}
        state.contamination_level = min(
            1.0,
            state.contamination_level + severity_impact.get(stop_event.severity, 0.2)
        )

    def _get_or_create_session_state(self, session_id: UUID) -> SessionState:
        """Get or create session state."""
        if session_id not in self._session_states:
            self._session_states[session_id] = SessionState(
                session_id=session_id,
                active=True,
                last_checkpoint=None,
                stop_count=0,
                current_stop=None,
                contamination_level=0.0,
                recovery_history=[],
            )
        return self._session_states[session_id]

    def _get_contamination_recommendation(self, level: float) -> str:
        """Get recommendation based on contamination level."""
        if level >= 0.8:
            return "CRITICAL: Start fresh session immediately"
        elif level >= 0.5:
            return "HIGH: Consider clean restart"
        elif level >= 0.3:
            return "MODERATE: Restore to last checkpoint"
        else:
            return "LOW: Continue with caution"

    def _trigger_callback(self, event: str, *args) -> None:
        """Trigger callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.warning(f"Callback failed for {event}: {e}")
