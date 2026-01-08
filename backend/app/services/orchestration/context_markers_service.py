"""
MP-QW-7: Context Markers Service

Emoji markers for visible context status.
Provides quick visual feedback on agent state and progress.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Starter symbols for process identity
- TDD phase indicators (red/green/refactor)
- Role and state markers
- Status line generation
- Marker history tracking

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class MarkerType(Enum):
    """Types of context markers."""
    # Ground rules and setup
    GROUND_RULES_READ = "ground_rules_read"
    CONTEXT_LOADED = "context_loaded"
    ROLE_ACTIVE = "role_active"

    # TDD phases
    TDD_RED = "tdd_red"
    TDD_GREEN = "tdd_green"
    TDD_REFACTOR = "tdd_refactor"

    # Process state
    HYPOTHESIS_PENDING = "hypothesis_pending"
    HYPOTHESIS_VERIFIED = "hypothesis_verified"
    CHECKPOINT = "checkpoint"
    LOOP_ITERATION = "loop_iteration"

    # Errors and warnings
    ERROR_DETECTED = "error_detected"
    WARNING = "warning"
    BLOCKED = "blocked"

    # Actions needed
    REREAD_REQUIRED = "reread_required"
    CLARIFICATION_NEEDED = "clarification_needed"
    HUMAN_INPUT_REQUIRED = "human_input_required"

    # Completion
    STEP_COMPLETE = "step_complete"
    TASK_COMPLETE = "task_complete"
    SUCCESS = "success"


# Emoji mappings for each marker type
MARKER_EMOJIS = {
    MarkerType.GROUND_RULES_READ: "🍀",
    MarkerType.CONTEXT_LOADED: "📚",
    MarkerType.ROLE_ACTIVE: "✅",
    MarkerType.TDD_RED: "🔴",
    MarkerType.TDD_GREEN: "🌱",
    MarkerType.TDD_REFACTOR: "🌀",
    MarkerType.HYPOTHESIS_PENDING: "🔮",
    MarkerType.HYPOTHESIS_VERIFIED: "✨",
    MarkerType.CHECKPOINT: "💾",
    MarkerType.LOOP_ITERATION: "🔄",
    MarkerType.ERROR_DETECTED: "❗",
    MarkerType.WARNING: "⚠️",
    MarkerType.BLOCKED: "🚫",
    MarkerType.REREAD_REQUIRED: "♻️",
    MarkerType.CLARIFICATION_NEEDED: "❓",
    MarkerType.HUMAN_INPUT_REQUIRED: "👤",
    MarkerType.STEP_COMPLETE: "☑️",
    MarkerType.TASK_COMPLETE: "🎉",
    MarkerType.SUCCESS: "🏆",
}

# Descriptions for each marker type
MARKER_DESCRIPTIONS = {
    MarkerType.GROUND_RULES_READ: "Ground rules have been read and understood",
    MarkerType.CONTEXT_LOADED: "Context has been loaded into session",
    MarkerType.ROLE_ACTIVE: "Agent role is active and ready",
    MarkerType.TDD_RED: "TDD Red phase - writing failing test",
    MarkerType.TDD_GREEN: "TDD Green phase - making test pass",
    MarkerType.TDD_REFACTOR: "TDD Refactor phase - improving code",
    MarkerType.HYPOTHESIS_PENDING: "Hypothesis stated, awaiting verification",
    MarkerType.HYPOTHESIS_VERIFIED: "Hypothesis has been verified",
    MarkerType.CHECKPOINT: "Checkpoint created",
    MarkerType.LOOP_ITERATION: "Processing loop iteration",
    MarkerType.ERROR_DETECTED: "Error has been detected",
    MarkerType.WARNING: "Warning condition present",
    MarkerType.BLOCKED: "Progress is blocked",
    MarkerType.REREAD_REQUIRED: "Re-reading context required",
    MarkerType.CLARIFICATION_NEEDED: "Clarification from user needed",
    MarkerType.HUMAN_INPUT_REQUIRED: "Human input required to proceed",
    MarkerType.STEP_COMPLETE: "Current step is complete",
    MarkerType.TASK_COMPLETE: "Task is complete",
    MarkerType.SUCCESS: "Successfully completed goal",
}


@dataclass
class ContextMarker:
    """A single context marker."""
    id: UUID
    type: MarkerType
    emoji: str
    description: str
    active: bool
    set_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None


@dataclass
class MarkerChange:
    """Record of a marker change."""
    marker_type: MarkerType
    action: str  # "set" or "clear"
    timestamp: datetime
    reason: Optional[str] = None


@dataclass
class ContextState:
    """Complete context state for a session."""
    session_id: UUID
    markers: Dict[MarkerType, ContextMarker]
    history: List[MarkerChange]
    created_at: datetime
    updated_at: datetime


class ContextMarkersService:
    """
    Service for managing visual context markers.

    Implements the "Starter Symbol" pattern - using emojis and visual
    markers to indicate process state and provide quick feedback.
    """

    def __init__(self):
        self._states: Dict[UUID, ContextState] = {}

    def set_marker(
        self,
        session_id: UUID,
        marker_type: MarkerType,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_seconds: Optional[int] = None
    ) -> ContextMarker:
        """
        Set a context marker.

        Args:
            session_id: The session to set marker for
            marker_type: Type of marker to set
            reason: Optional reason for setting
            metadata: Optional metadata
            expires_in_seconds: Auto-expire after N seconds

        Returns:
            The created/updated ContextMarker
        """
        state = self._get_or_create_state(session_id)
        now = datetime.utcnow()

        # Calculate expiration if specified
        expires_at = None
        if expires_in_seconds:
            from datetime import timedelta
            expires_at = now + timedelta(seconds=expires_in_seconds)

        marker = ContextMarker(
            id=uuid4(),
            type=marker_type,
            emoji=MARKER_EMOJIS.get(marker_type, "❔"),
            description=MARKER_DESCRIPTIONS.get(marker_type, "Unknown marker"),
            active=True,
            set_at=now,
            metadata=metadata or {},
            expires_at=expires_at,
        )

        state.markers[marker_type] = marker
        state.updated_at = now

        # Record history
        state.history.append(MarkerChange(
            marker_type=marker_type,
            action="set",
            timestamp=now,
            reason=reason,
        ))

        logger.debug(f"Set marker {marker_type.value} ({marker.emoji}) for session {session_id}")
        return marker

    def clear_marker(
        self,
        session_id: UUID,
        marker_type: MarkerType,
        reason: Optional[str] = None
    ) -> bool:
        """
        Clear a context marker.

        Args:
            session_id: The session
            marker_type: Type of marker to clear
            reason: Optional reason for clearing

        Returns:
            True if marker was cleared, False if not found
        """
        state = self._states.get(session_id)
        if not state:
            return False

        if marker_type not in state.markers:
            return False

        marker = state.markers[marker_type]
        marker.active = False

        now = datetime.utcnow()
        state.updated_at = now

        # Record history
        state.history.append(MarkerChange(
            marker_type=marker_type,
            action="clear",
            timestamp=now,
            reason=reason,
        ))

        # Remove from active markers
        del state.markers[marker_type]

        logger.debug(f"Cleared marker {marker_type.value} for session {session_id}")
        return True

    def get_active_markers(self, session_id: UUID) -> List[ContextMarker]:
        """Get all active markers for a session."""
        state = self._states.get(session_id)
        if not state:
            return []

        # Filter out expired markers
        now = datetime.utcnow()
        active_markers = []
        expired_types = []

        for marker_type, marker in state.markers.items():
            if marker.expires_at and marker.expires_at < now:
                expired_types.append(marker_type)
            elif marker.active:
                active_markers.append(marker)

        # Clean up expired markers
        for marker_type in expired_types:
            self.clear_marker(session_id, marker_type, "expired")

        return active_markers

    def get_status_line(self, session_id: UUID, separator: str = "") -> str:
        """
        Get a status line string of active markers.

        Args:
            session_id: The session
            separator: Separator between emojis (default: none)

        Returns:
            String of emojis representing active markers
        """
        markers = self.get_active_markers(session_id)

        # Sort by type for consistent ordering
        markers.sort(key=lambda m: m.type.value)

        return separator.join(m.emoji for m in markers)

    def get_marker_history(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
        marker_type: Optional[MarkerType] = None
    ) -> List[MarkerChange]:
        """
        Get marker change history.

        Args:
            session_id: The session
            limit: Maximum number of entries to return
            marker_type: Filter by specific marker type

        Returns:
            List of MarkerChange entries
        """
        state = self._states.get(session_id)
        if not state:
            return []

        history = state.history

        if marker_type:
            history = [h for h in history if h.marker_type == marker_type]

        # Sort by timestamp descending
        history = sorted(history, key=lambda h: h.timestamp, reverse=True)

        if limit:
            history = history[:limit]

        return history

    def has_marker(self, session_id: UUID, marker_type: MarkerType) -> bool:
        """Check if a specific marker is active."""
        state = self._states.get(session_id)
        if not state:
            return False

        if marker_type not in state.markers:
            return False

        marker = state.markers[marker_type]

        # Check expiration
        if marker.expires_at and marker.expires_at < datetime.utcnow():
            self.clear_marker(session_id, marker_type, "expired")
            return False

        return marker.active

    def set_tdd_phase(self, session_id: UUID, phase: str) -> ContextMarker:
        """
        Convenience method to set TDD phase marker.

        Args:
            session_id: The session
            phase: "red", "green", or "refactor"

        Returns:
            The set marker
        """
        # Clear any existing TDD markers
        for tdd_type in (MarkerType.TDD_RED, MarkerType.TDD_GREEN, MarkerType.TDD_REFACTOR):
            self.clear_marker(session_id, tdd_type)

        # Set new phase
        phase_map = {
            "red": MarkerType.TDD_RED,
            "green": MarkerType.TDD_GREEN,
            "refactor": MarkerType.TDD_REFACTOR,
        }

        marker_type = phase_map.get(phase.lower())
        if not marker_type:
            raise ValueError(f"Unknown TDD phase: {phase}")

        return self.set_marker(session_id, marker_type, reason=f"TDD phase: {phase}")

    def get_tdd_phase(self, session_id: UUID) -> Optional[str]:
        """Get current TDD phase if any."""
        if self.has_marker(session_id, MarkerType.TDD_RED):
            return "red"
        if self.has_marker(session_id, MarkerType.TDD_GREEN):
            return "green"
        if self.has_marker(session_id, MarkerType.TDD_REFACTOR):
            return "refactor"
        return None

    def clear_all_markers(self, session_id: UUID, reason: Optional[str] = None) -> int:
        """
        Clear all markers for a session.

        Returns:
            Number of markers cleared
        """
        state = self._states.get(session_id)
        if not state:
            return 0

        count = len(state.markers)
        marker_types = list(state.markers.keys())

        for marker_type in marker_types:
            self.clear_marker(session_id, marker_type, reason or "clear_all")

        return count

    def get_context_summary(self, session_id: UUID) -> Dict[str, Any]:
        """Get a summary of the context state."""
        state = self._states.get(session_id)
        if not state:
            return {
                "session_id": str(session_id),
                "active_markers": 0,
                "status_line": "",
                "tdd_phase": None,
                "has_errors": False,
                "needs_input": False,
            }

        markers = self.get_active_markers(session_id)

        return {
            "session_id": str(session_id),
            "active_markers": len(markers),
            "status_line": self.get_status_line(session_id),
            "tdd_phase": self.get_tdd_phase(session_id),
            "has_errors": any(m.type in (MarkerType.ERROR_DETECTED, MarkerType.BLOCKED) for m in markers),
            "needs_input": any(m.type in (MarkerType.CLARIFICATION_NEEDED, MarkerType.HUMAN_INPUT_REQUIRED) for m in markers),
            "markers": [
                {
                    "type": m.type.value,
                    "emoji": m.emoji,
                    "description": m.description,
                    "set_at": m.set_at.isoformat(),
                }
                for m in markers
            ],
        }

    def get_available_markers(self) -> List[Dict[str, str]]:
        """Get list of all available marker types."""
        return [
            {
                "type": mt.value,
                "emoji": MARKER_EMOJIS.get(mt, "❔"),
                "description": MARKER_DESCRIPTIONS.get(mt, ""),
            }
            for mt in MarkerType
        ]

    def _get_or_create_state(self, session_id: UUID) -> ContextState:
        """Get or create context state for a session."""
        if session_id not in self._states:
            now = datetime.utcnow()
            self._states[session_id] = ContextState(
                session_id=session_id,
                markers={},
                history=[],
                created_at=now,
                updated_at=now,
            )
        return self._states[session_id]
