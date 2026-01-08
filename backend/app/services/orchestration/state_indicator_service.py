"""
State Indicator Pattern Service - Week 107 (AO-QW-3)

Track position within a process using symbols and keywords.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- Starter Symbols provide visual feedback on progress
- State tracking enables checkpoint recovery
- Resilient restart capability after context loss

Standard Markers:
- CURRENT_STATE: Where we are in the process
- COMPLETED: What has been done
- PENDING: What remains to be done
- ITERATION: Current loop iteration
- Phase indicators (TDD, refactoring, etc.)

Features:
- Emoji-based state visualization
- Markdown-formatted state files
- Automatic state persistence
- State history tracking
- Phase-specific indicators (TDD, refactoring, etc.)
"""

import json
import re
from enum import Enum
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set


class StatePhase(str, Enum):
    """Standard phases in development processes."""
    # TDD Phases
    RED = "red"                    # Writing failing test
    GREEN = "green"                # Making test pass
    REFACTOR = "refactor"          # Improving code

    # Development Phases
    ANALYSIS = "analysis"          # Analyzing requirements
    DESIGN = "design"              # Designing solution
    IMPLEMENTATION = "implementation"  # Writing code
    TESTING = "testing"            # Running tests
    REVIEW = "review"              # Code review
    DEPLOYMENT = "deployment"      # Deploying

    # Status Phases
    BLOCKED = "blocked"            # Waiting on something
    ERROR = "error"                # Error occurred
    COMPLETE = "complete"          # Phase complete
    IDLE = "idle"                  # Not actively working


class StateMarker(str, Enum):
    """Emoji markers for state indication."""
    # Progress markers
    CURRENT = ""              # Current position
    COMPLETED = ""             # Completed items
    PENDING = ""               # Pending items
    IN_PROGRESS = ""           # Work in progress
    BLOCKED = ""               # Blocked by issue

    # Status markers
    SUCCESS = ""               # Success/pass
    FAILURE = ""               # Failure/fail
    WARNING = ""               # Warning
    ERROR = ""                # Error

    # Phase markers (TDD)
    RED = ""                  # TDD red phase
    GREEN = ""                 # TDD green phase
    REFACTOR = ""              # Refactoring

    # Activity markers
    READING = ""               # Reading/researching
    WRITING = ""               # Writing code
    TESTING = ""               # Testing
    REVIEWING = ""             # Reviewing
    THINKING = ""              # Planning/thinking
    DEPLOYING = ""             # Deploying

    # Context markers
    GROUND_RULES = ""         # Ground rules loaded
    ROLE_ACTIVE = ""           # Role/persona active
    RE_READ = ""              # Re-read required
    CHECKPOINT = ""            # Checkpoint created


@dataclass
class StateEntry:
    """
    A state entry with timestamp and metadata.

    Records a specific state at a point in time,
    enabling history tracking and rollback.
    """
    state: str
    phase: StatePhase
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())
    description: str = ""
    markers: List[StateMarker] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def format(self) -> str:
        """Format state entry for display."""
        marker_str = ' '.join([m.value for m in self.markers])
        return f"{marker_str} {self.state}: {self.description}"


@dataclass
class ProcessState:
    """
    Complete state of a process including history.

    Tracks:
    - Current position in the process
    - Completed, pending, and blocked items
    - Iteration counts for loops
    - State history for debugging
    """
    process_id: str
    current_state: str
    phase: StatePhase = StatePhase.IDLE
    completed: List[str] = field(default_factory=list)
    pending: List[str] = field(default_factory=list)
    blocked: List[str] = field(default_factory=list)
    iterations: Dict[str, int] = field(default_factory=dict)
    total_iterations: Dict[str, int] = field(default_factory=dict)
    history: List[StateEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())
    active_markers: Set[StateMarker] = field(default_factory=set)
    context: Dict[str, Any] = field(default_factory=dict)

    def transition(
        self,
        new_state: str,
        phase: Optional[StatePhase] = None,
        description: str = "",
        markers: Optional[List[StateMarker]] = None,
    ) -> StateEntry:
        """
        Transition to a new state.

        Args:
            new_state: New state identifier
            phase: Optional new phase
            description: Description of transition
            markers: Markers for this state

        Returns:
            The created StateEntry
        """
        # Record history
        entry = StateEntry(
            state=new_state,
            phase=phase or self.phase,
            description=description,
            markers=markers or [],
            context=self.context.copy(),
        )
        self.history.append(entry)

        # Update current state
        old_state = self.current_state
        self.current_state = new_state

        if phase:
            self.phase = phase

        if markers:
            self.active_markers = set(markers)

        # Move old state to completed if not already there
        if old_state and old_state not in self.completed:
            self.completed.append(old_state)

        # Remove new state from pending
        if new_state in self.pending:
            self.pending.remove(new_state)

        self.updated_at = datetime.utcnow()

        return entry

    def mark_completed(self, item: str) -> None:
        """Mark an item as completed."""
        if item not in self.completed:
            self.completed.append(item)
        if item in self.pending:
            self.pending.remove(item)
        if item in self.blocked:
            self.blocked.remove(item)

    def mark_blocked(self, item: str, reason: str = "") -> None:
        """Mark an item as blocked."""
        if item not in self.blocked:
            self.blocked.append(item)
        self.context[f"blocked_{item}_reason"] = reason

    def unblock(self, item: str) -> None:
        """Remove blocked status from an item."""
        if item in self.blocked:
            self.blocked.remove(item)
        self.context.pop(f"blocked_{item}_reason", None)

    def add_pending(self, items: List[str]) -> None:
        """Add items to pending list."""
        for item in items:
            if item not in self.pending and item not in self.completed:
                self.pending.append(item)

    def increment_iteration(self, loop_id: str) -> int:
        """Increment and return iteration count."""
        count = self.iterations.get(loop_id, 0) + 1
        self.iterations[loop_id] = count
        return count

    def set_total_iterations(self, loop_id: str, total: int) -> None:
        """Set expected total iterations for a loop."""
        self.total_iterations[loop_id] = total

    def get_progress_percent(self) -> float:
        """Calculate overall progress percentage."""
        total = len(self.completed) + len(self.pending)
        if total == 0:
            return 0.0
        return (len(self.completed) / total) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "process_id": self.process_id,
            "current_state": self.current_state,
            "phase": self.phase.value,
            "completed": self.completed,
            "pending": self.pending,
            "blocked": self.blocked,
            "iterations": self.iterations,
            "total_iterations": self.total_iterations,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active_markers": [m.value for m in self.active_markers],
            "context": self.context,
            "history": [
                {
                    "state": e.state,
                    "phase": e.phase.value,
                    "timestamp": e.timestamp.isoformat(),
                    "description": e.description,
                    "markers": [m.value for m in e.markers],
                }
                for e in self.history
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessState":
        """Create from dictionary."""
        state = cls(
            process_id=data["process_id"],
            current_state=data["current_state"],
            phase=StatePhase(data["phase"]),
            completed=data.get("completed", []),
            pending=data.get("pending", []),
            blocked=data.get("blocked", []),
            iterations=data.get("iterations", {}),
            total_iterations=data.get("total_iterations", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            context=data.get("context", {}),
        )

        # Parse markers
        state.active_markers = set()
        for marker_value in data.get("active_markers", []):
            try:
                state.active_markers.add(StateMarker(marker_value))
            except ValueError:
                pass

        # Parse history
        for h in data.get("history", []):
            entry = StateEntry(
                state=h["state"],
                phase=StatePhase(h["phase"]),
                timestamp=datetime.fromisoformat(h["timestamp"]),
                description=h.get("description", ""),
            )
            for m_value in h.get("markers", []):
                try:
                    entry.markers.append(StateMarker(m_value))
                except ValueError:
                    pass
            state.history.append(entry)

        return state


class StateIndicatorService:
    """
    State Indicator Service for process state tracking.

    Provides:
    - State file generation and parsing
    - Progress visualization with emoji markers
    - Checkpoint recovery support
    - Phase-specific indicators (TDD, etc.)
    - State history for debugging

    Usage:
        service = StateIndicatorService()

        # Create process state
        state = service.create_state("my_process", [
            "step1", "step2", "step3"
        ])

        # Transition through states
        service.transition(state, "step1", StatePhase.IMPLEMENTATION)
        service.mark_completed(state, "step1")
        service.transition(state, "step2", StatePhase.TESTING)

        # Get visual representation
        visual = service.format_state(state)
        print(visual)

        # Save/restore state
        service.save_state(state)
        restored = service.load_state("my_process")
    """

    # Standard state file patterns
    STATE_PATTERN = re.compile(
        r'(?P<marker>[\U0001F4CD\U00002705\U0001F7E1\U0001F534\U0001F7E2\U0001F504])'
        r'\s*(?P<label>[A-Z_]+):\s*(?P<value>.*)',
        re.UNICODE
    )

    ITERATION_PATTERN = re.compile(
        r'\U0001F504\s*ITERATION\s*\((?P<id>[^)]+)\):\s*(?P<current>\d+)/(?P<total>\d+)'
    )

    def __init__(
        self,
        state_dir: Optional[Path] = None,
        auto_save: bool = True,
    ):
        """
        Initialize State Indicator Service.

        Args:
            state_dir: Directory for state file storage
            auto_save: Automatically save state on changes
        """
        self.state_dir = Path(state_dir) if state_dir else Path(".states")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save = auto_save

        # In-memory state cache
        self._states: Dict[str, ProcessState] = {}

    # === State Creation & Management ===

    def create_state(
        self,
        process_id: str,
        pending_items: Optional[List[str]] = None,
        initial_state: str = "init",
        initial_phase: StatePhase = StatePhase.IDLE,
    ) -> ProcessState:
        """
        Create a new process state.

        Args:
            process_id: Unique identifier for this process
            pending_items: List of items to track
            initial_state: Starting state name
            initial_phase: Starting phase

        Returns:
            The created ProcessState
        """
        state = ProcessState(
            process_id=process_id,
            current_state=initial_state,
            phase=initial_phase,
            pending=pending_items or [],
        )

        self._states[process_id] = state

        if self.auto_save:
            self.save_state(state)

        return state

    def get_state(self, process_id: str) -> Optional[ProcessState]:
        """Get a state by process ID."""
        if process_id in self._states:
            return self._states[process_id]

        # Try loading from file
        return self.load_state(process_id)

    def transition(
        self,
        state: ProcessState,
        new_state: str,
        phase: Optional[StatePhase] = None,
        description: str = "",
        markers: Optional[List[StateMarker]] = None,
    ) -> StateEntry:
        """
        Transition process to a new state.

        Args:
            state: Process state to update
            new_state: New state identifier
            phase: Optional new phase
            description: Description of transition
            markers: Markers for this state

        Returns:
            The created StateEntry
        """
        entry = state.transition(new_state, phase, description, markers)

        if self.auto_save:
            self.save_state(state)

        return entry

    def mark_completed(self, state: ProcessState, item: str) -> None:
        """Mark an item as completed."""
        state.mark_completed(item)
        if self.auto_save:
            self.save_state(state)

    def mark_blocked(
        self,
        state: ProcessState,
        item: str,
        reason: str = "",
    ) -> None:
        """Mark an item as blocked."""
        state.mark_blocked(item, reason)
        if self.auto_save:
            self.save_state(state)

    def unblock(self, state: ProcessState, item: str) -> None:
        """Remove blocked status from an item."""
        state.unblock(item)
        if self.auto_save:
            self.save_state(state)

    def add_pending(self, state: ProcessState, items: List[str]) -> None:
        """Add items to pending list."""
        state.add_pending(items)
        if self.auto_save:
            self.save_state(state)

    # === TDD Phase Helpers ===

    def enter_red_phase(
        self,
        state: ProcessState,
        test_name: str,
    ) -> StateEntry:
        """Enter TDD red phase (writing failing test)."""
        return self.transition(
            state,
            f"red_{test_name}",
            StatePhase.RED,
            f"Writing failing test: {test_name}",
            [StateMarker.RED, StateMarker.TESTING],
        )

    def enter_green_phase(
        self,
        state: ProcessState,
        test_name: str,
    ) -> StateEntry:
        """Enter TDD green phase (making test pass)."""
        return self.transition(
            state,
            f"green_{test_name}",
            StatePhase.GREEN,
            f"Making test pass: {test_name}",
            [StateMarker.GREEN, StateMarker.WRITING],
        )

    def enter_refactor_phase(
        self,
        state: ProcessState,
        description: str = "",
    ) -> StateEntry:
        """Enter refactoring phase."""
        return self.transition(
            state,
            "refactor",
            StatePhase.REFACTOR,
            description or "Refactoring code",
            [StateMarker.REFACTOR, StateMarker.WRITING],
        )

    # === Iteration Tracking ===

    def start_loop(
        self,
        state: ProcessState,
        loop_id: str,
        total_iterations: int,
    ) -> int:
        """
        Start a new loop iteration.

        Args:
            state: Process state
            loop_id: Loop identifier
            total_iterations: Expected total iterations

        Returns:
            Current iteration number (1-based)
        """
        state.set_total_iterations(loop_id, total_iterations)
        iteration = state.increment_iteration(loop_id)

        if self.auto_save:
            self.save_state(state)

        return iteration

    def next_iteration(
        self,
        state: ProcessState,
        loop_id: str,
    ) -> int:
        """
        Advance to next iteration.

        Returns:
            New iteration number
        """
        iteration = state.increment_iteration(loop_id)

        if self.auto_save:
            self.save_state(state)

        return iteration

    def is_loop_complete(
        self,
        state: ProcessState,
        loop_id: str,
    ) -> bool:
        """Check if a loop has completed all iterations."""
        current = state.iterations.get(loop_id, 0)
        total = state.total_iterations.get(loop_id, 0)
        return current >= total

    # === Marker Management ===

    def add_marker(self, state: ProcessState, marker: StateMarker) -> None:
        """Add an active marker."""
        state.active_markers.add(marker)
        if self.auto_save:
            self.save_state(state)

    def remove_marker(self, state: ProcessState, marker: StateMarker) -> None:
        """Remove an active marker."""
        state.active_markers.discard(marker)
        if self.auto_save:
            self.save_state(state)

    def set_markers(self, state: ProcessState, markers: List[StateMarker]) -> None:
        """Set active markers (replaces existing)."""
        state.active_markers = set(markers)
        if self.auto_save:
            self.save_state(state)

    # === State Visualization ===

    def format_state(self, state: ProcessState) -> str:
        """
        Format state as visual markdown.

        Returns:
            Formatted markdown string with state indicators
        """
        lines = []

        # Header
        lines.append("# State Indicator")
        lines.append(f"*Process: {state.process_id}*")
        lines.append(f"*Updated: {state.updated_at.isoformat()}*")
        lines.append("")

        # Active markers
        if state.active_markers:
            marker_str = ' '.join([m.value for m in state.active_markers])
            lines.append(f"**Active:** {marker_str}")
            lines.append("")

        # Current state
        phase_marker = self._get_phase_marker(state.phase)
        lines.append(f"{StateMarker.CURRENT.value} CURRENT_STATE: {state.current_state}")
        lines.append(f"{phase_marker} PHASE: {state.phase.value}")
        lines.append("")

        # Progress
        progress = state.get_progress_percent()
        lines.append(f"**Progress:** {progress:.1f}%")
        lines.append("")

        # Completed items
        if state.completed:
            lines.append(f"{StateMarker.COMPLETED.value} COMPLETED: {state.completed}")
        else:
            lines.append(f"{StateMarker.COMPLETED.value} COMPLETED: []")

        # Pending items
        if state.pending:
            lines.append(f"{StateMarker.PENDING.value} PENDING: {state.pending}")
        else:
            lines.append(f"{StateMarker.PENDING.value} PENDING: []")

        # Blocked items
        if state.blocked:
            lines.append(f"{StateMarker.BLOCKED.value} BLOCKED: {state.blocked}")
            for item in state.blocked:
                reason = state.context.get(f"blocked_{item}_reason", "No reason given")
                lines.append(f"  - {item}: {reason}")

        # Iterations
        if state.iterations:
            lines.append("")
            lines.append("**Iterations:**")
            for loop_id, current in state.iterations.items():
                total = state.total_iterations.get(loop_id, "?")
                lines.append(f"{StateMarker.REFACTOR.value} ITERATION ({loop_id}): {current}/{total}")

        return '\n'.join(lines)

    def format_compact(self, state: ProcessState) -> str:
        """
        Format state as compact single line.

        Useful for status bars or inline display.
        """
        phase_marker = self._get_phase_marker(state.phase)
        markers = ' '.join([m.value for m in state.active_markers])
        progress = state.get_progress_percent()

        return f"{markers} {phase_marker} {state.current_state} ({progress:.0f}%)"

    def _get_phase_marker(self, phase: StatePhase) -> str:
        """Get emoji marker for a phase."""
        phase_markers = {
            StatePhase.RED: StateMarker.RED.value,
            StatePhase.GREEN: StateMarker.GREEN.value,
            StatePhase.REFACTOR: StateMarker.REFACTOR.value,
            StatePhase.ANALYSIS: StateMarker.READING.value,
            StatePhase.DESIGN: StateMarker.THINKING.value,
            StatePhase.IMPLEMENTATION: StateMarker.WRITING.value,
            StatePhase.TESTING: StateMarker.TESTING.value,
            StatePhase.REVIEW: StateMarker.REVIEWING.value,
            StatePhase.DEPLOYMENT: StateMarker.DEPLOYING.value,
            StatePhase.BLOCKED: StateMarker.BLOCKED.value,
            StatePhase.ERROR: StateMarker.ERROR.value,
            StatePhase.COMPLETE: StateMarker.SUCCESS.value,
            StatePhase.IDLE: "",
        }
        return phase_markers.get(phase, "")

    # === Persistence ===

    def save_state(self, state: ProcessState) -> Path:
        """
        Save state to file.

        Returns:
            Path to saved state file
        """
        file_path = self.state_dir / f"{state.process_id}.json"

        with open(file_path, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)

        # Also save markdown version for human readability
        md_path = self.state_dir / f"{state.process_id}.md"
        with open(md_path, 'w') as f:
            f.write(self.format_state(state))

        return file_path

    def load_state(self, process_id: str) -> Optional[ProcessState]:
        """
        Load state from file.

        Returns:
            Loaded ProcessState or None if not found
        """
        file_path = self.state_dir / f"{process_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            state = ProcessState.from_dict(data)
            self._states[process_id] = state
            return state
        except Exception:
            return None

    def delete_state(self, process_id: str) -> bool:
        """
        Delete a state file.

        Returns:
            True if deleted successfully
        """
        self._states.pop(process_id, None)

        json_path = self.state_dir / f"{process_id}.json"
        md_path = self.state_dir / f"{process_id}.md"

        deleted = False
        if json_path.exists():
            json_path.unlink()
            deleted = True
        if md_path.exists():
            md_path.unlink()
            deleted = True

        return deleted

    def list_states(self) -> List[str]:
        """List all saved state process IDs."""
        return [
            f.stem for f in self.state_dir.glob("*.json")
        ]

    # === State File Parsing ===

    def parse_state_file(self, content: str) -> Dict[str, Any]:
        """
        Parse a markdown state file.

        Args:
            content: Markdown content of state file

        Returns:
            Dictionary with parsed state information
        """
        result = {
            "current_state": None,
            "completed": [],
            "pending": [],
            "iterations": {},
        }

        for line in content.split('\n'):
            line = line.strip()

            # Parse standard state lines
            match = self.STATE_PATTERN.match(line)
            if match:
                label = match.group('label')
                value = match.group('value').strip()

                if label == "CURRENT_STATE":
                    result["current_state"] = value
                elif label == "COMPLETED":
                    result["completed"] = self._parse_list(value)
                elif label == "PENDING":
                    result["pending"] = self._parse_list(value)

            # Parse iteration lines
            iter_match = self.ITERATION_PATTERN.match(line)
            if iter_match:
                loop_id = iter_match.group('id')
                current = int(iter_match.group('current'))
                total = int(iter_match.group('total'))
                result["iterations"][loop_id] = {"current": current, "total": total}

        return result

    def _parse_list(self, value: str) -> List[str]:
        """Parse a list value from state file."""
        # Handle Python-style list strings
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            value = value[1:-1]

        if not value:
            return []

        # Split by comma, handling quoted strings
        items = []
        for item in value.split(','):
            item = item.strip().strip("'\"")
            if item:
                items.append(item)

        return items

    # === Checkpoint Support ===

    def create_checkpoint(
        self,
        state: ProcessState,
        checkpoint_id: str,
    ) -> Dict[str, Any]:
        """
        Create a checkpoint for state recovery.

        Returns:
            Checkpoint data that can be restored later
        """
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "created_at": datetime.utcnow().isoformat(),
            "state": state.to_dict(),
        }

        # Save checkpoint file
        checkpoint_path = self.state_dir / f"{state.process_id}_checkpoint_{checkpoint_id}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        # Add marker
        state.active_markers.add(StateMarker.CHECKPOINT)
        if self.auto_save:
            self.save_state(state)

        return checkpoint

    def restore_checkpoint(
        self,
        process_id: str,
        checkpoint_id: str,
    ) -> Optional[ProcessState]:
        """
        Restore state from a checkpoint.

        Returns:
            Restored ProcessState or None if not found
        """
        checkpoint_path = self.state_dir / f"{process_id}_checkpoint_{checkpoint_id}.json"

        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path, 'r') as f:
                checkpoint = json.load(f)

            state = ProcessState.from_dict(checkpoint["state"])
            self._states[process_id] = state

            if self.auto_save:
                self.save_state(state)

            return state
        except Exception:
            return None

    def list_checkpoints(self, process_id: str) -> List[str]:
        """List available checkpoints for a process."""
        pattern = f"{process_id}_checkpoint_*.json"
        checkpoints = []

        for f in self.state_dir.glob(pattern):
            # Extract checkpoint ID from filename
            name = f.stem
            prefix = f"{process_id}_checkpoint_"
            if name.startswith(prefix):
                checkpoints.append(name[len(prefix):])

        return checkpoints
