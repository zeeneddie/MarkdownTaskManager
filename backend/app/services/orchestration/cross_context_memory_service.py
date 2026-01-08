"""
Cross-Context Memory Service - Week 107 (AO-QW-2)

Persistent memory between agent runs/sessions via files.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- Preserves facts, goals, decisions, and progress across contexts
- Enables resilient restart after context loss
- Supports multiple memory scopes (session, task, project, global)

Key Features:
- File-based persistence (survives context window resets)
- Scoped memory (session, task, project, global)
- Goal tracking with completion status
- Decision logging with rationale
- Automatic memory cleanup and expiration
- Memory compression for large datasets
"""

import json
import hashlib
import shutil
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Set, Union
from contextlib import contextmanager


class MemoryScope(str, Enum):
    """Scope levels for memory storage."""
    SESSION = "session"      # Single conversation/session
    TASK = "task"           # Single task across sessions
    PROJECT = "project"     # Project-wide memory
    GLOBAL = "global"       # Cross-project memory


class MemoryType(str, Enum):
    """Types of memory entries."""
    FACT = "fact"           # Discovered or stated facts
    GOAL = "goal"           # Active goals/objectives
    DECISION = "decision"   # Made decisions with rationale
    PROGRESS = "progress"   # Progress markers
    CONTEXT = "context"     # Context information
    CHECKPOINT = "checkpoint"  # Recovery checkpoints
    LEARNING = "learning"   # Lessons learned


@dataclass
class MemoryEntry:
    """
    A single memory entry with metadata.

    Attributes:
        key: Unique identifier within scope
        value: The memory content
        memory_type: Type of memory (fact, goal, decision, etc.)
        scope: Scope level for this memory
        created_at: Creation timestamp
        updated_at: Last update timestamp
        expires_at: Optional expiration timestamp
        tags: Searchable tags
        metadata: Additional metadata
    """
    key: str
    value: Any
    memory_type: MemoryType
    scope: MemoryScope
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "memory_type": self.memory_type.value,
            "scope": self.scope.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            memory_type=MemoryType(data["memory_type"]),
            scope=MemoryScope(data["scope"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Goal:
    """
    An active goal being tracked.

    Goals can be hierarchical with sub-goals and have completion criteria.
    """
    id: str
    description: str
    status: str = "active"  # active, completed, abandoned, blocked
    progress: float = 0.0   # 0.0 to 1.0
    sub_goals: List[str] = field(default_factory=list)
    parent_goal: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    completed_at: Optional[datetime] = None
    completion_criteria: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    def mark_complete(self) -> None:
        """Mark goal as completed."""
        self.status = "completed"
        self.progress = 1.0
        self.completed_at = datetime.utcnow()

    def update_progress(self, progress: float) -> None:
        """Update goal progress (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, progress))
        if self.progress >= 1.0:
            self.mark_complete()


@dataclass
class Decision:
    """
    A recorded decision with rationale.

    Decisions are logged to provide context for future
    sessions and enable rollback if needed.
    """
    id: str
    decision: str
    rationale: str
    alternatives_considered: List[str] = field(default_factory=list)
    made_at: datetime = field(default_factory=lambda: datetime.utcnow())
    context: Dict[str, Any] = field(default_factory=dict)
    reversible: bool = True
    reverted: bool = False
    reverted_at: Optional[datetime] = None
    revert_reason: Optional[str] = None


class CrossContextMemoryService:
    """
    Cross-Context Memory Service for persistent agent memory.

    Provides file-based memory that survives context window resets,
    enabling agents to maintain state across long-running tasks.

    Usage:
        memory = CrossContextMemoryService(
            base_dir="/path/to/memory",
            session_id="session_123"
        )

        # Store and retrieve facts
        memory.store("api_key_location", "config/keys.yaml", MemoryType.FACT)
        location = memory.get("api_key_location")

        # Track goals
        goal = memory.set_goal("Implement authentication", [
            "Create user model",
            "Add JWT support",
            "Write tests"
        ])
        memory.update_goal_progress(goal.id, 0.5)

        # Log decisions
        memory.log_decision(
            "Use FastAPI over Flask",
            rationale="Better async support, OpenAPI integration",
            alternatives=["Flask", "Django"]
        )

        # Get goal file for context injection
        goal_file = memory.get_goal_file()
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        auto_cleanup: bool = True,
        max_entries_per_scope: int = 1000,
    ):
        """
        Initialize Cross-Context Memory Service.

        Args:
            base_dir: Base directory for memory storage
            session_id: Current session identifier
            project_id: Current project identifier
            auto_cleanup: Automatically clean expired entries
            max_entries_per_scope: Maximum entries before compression
        """
        self.base_dir = Path(base_dir) if base_dir else Path(".memory")
        self.session_id = session_id or self._generate_session_id()
        self.project_id = project_id or "default"
        self.auto_cleanup = auto_cleanup
        self.max_entries_per_scope = max_entries_per_scope

        # Ensure directories exist
        self._ensure_directories()

        # In-memory cache for frequently accessed entries
        self._cache: Dict[str, MemoryEntry] = {}
        self._goals: Dict[str, Goal] = {}
        self._decisions: Dict[str, Decision] = {}

        # Load existing state
        self._load_state()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]

    def _ensure_directories(self) -> None:
        """Create required directories."""
        for scope in MemoryScope:
            scope_dir = self._get_scope_dir(scope)
            scope_dir.mkdir(parents=True, exist_ok=True)

    def _get_scope_dir(self, scope: MemoryScope) -> Path:
        """Get directory for a given scope."""
        if scope == MemoryScope.SESSION:
            return self.base_dir / "sessions" / self.session_id
        elif scope == MemoryScope.TASK:
            return self.base_dir / "tasks"
        elif scope == MemoryScope.PROJECT:
            return self.base_dir / "projects" / self.project_id
        else:  # GLOBAL
            return self.base_dir / "global"

    def _get_entry_path(self, key: str, scope: MemoryScope) -> Path:
        """Get file path for a memory entry."""
        safe_key = hashlib.md5(key.encode()).hexdigest()[:16]
        return self._get_scope_dir(scope) / f"{safe_key}.json"

    # === Core Memory Operations ===

    def store(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.FACT,
        scope: MemoryScope = MemoryScope.SESSION,
        tags: Optional[List[str]] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        Store a value in memory.

        Args:
            key: Unique key for this memory
            value: Value to store (must be JSON-serializable)
            memory_type: Type of memory entry
            scope: Scope level for storage
            tags: Searchable tags
            ttl_seconds: Time-to-live in seconds
            metadata: Additional metadata

        Returns:
            The created MemoryEntry
        """
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=memory_type,
            scope=scope,
            tags=tags or [],
            expires_at=expires_at,
            metadata=metadata or {},
        )

        # Store to file
        self._write_entry(entry)

        # Update cache
        cache_key = f"{scope.value}:{key}"
        self._cache[cache_key] = entry

        return entry

    def get(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.SESSION,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a value from memory.

        Args:
            key: Key to look up
            scope: Scope to search in
            default: Default value if not found

        Returns:
            The stored value or default
        """
        # Check cache first
        cache_key = f"{scope.value}:{key}"
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                return entry.value
            else:
                # Clean up expired entry
                self.delete(key, scope)
                return default

        # Load from file
        entry = self._read_entry(key, scope)
        if entry and not entry.is_expired():
            self._cache[cache_key] = entry
            return entry.value

        return default

    def get_entry(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.SESSION,
    ) -> Optional[MemoryEntry]:
        """Get full memory entry with metadata."""
        cache_key = f"{scope.value}:{key}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        return self._read_entry(key, scope)

    def delete(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.SESSION,
    ) -> bool:
        """
        Delete a memory entry.

        Returns:
            True if entry was deleted
        """
        cache_key = f"{scope.value}:{key}"
        self._cache.pop(cache_key, None)

        path = self._get_entry_path(key, scope)
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.SESSION,
    ) -> bool:
        """Check if a key exists in memory."""
        cache_key = f"{scope.value}:{key}"
        if cache_key in self._cache:
            return not self._cache[cache_key].is_expired()

        path = self._get_entry_path(key, scope)
        return path.exists()

    # === Goal Management ===

    def set_goal(
        self,
        description: str,
        completion_criteria: Optional[List[str]] = None,
        parent_goal: Optional[str] = None,
    ) -> Goal:
        """
        Set a new goal to track.

        Args:
            description: Goal description
            completion_criteria: List of criteria for completion
            parent_goal: ID of parent goal if this is a sub-goal

        Returns:
            The created Goal
        """
        goal_id = hashlib.md5(
            f"{description}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:8]

        goal = Goal(
            id=goal_id,
            description=description,
            completion_criteria=completion_criteria or [],
            parent_goal=parent_goal,
        )

        self._goals[goal_id] = goal

        # If this is a sub-goal, link to parent
        if parent_goal and parent_goal in self._goals:
            self._goals[parent_goal].sub_goals.append(goal_id)

        # Persist
        self._save_goals()

        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID."""
        return self._goals.get(goal_id)

    def update_goal_progress(self, goal_id: str, progress: float) -> Optional[Goal]:
        """
        Update goal progress.

        Args:
            goal_id: Goal to update
            progress: New progress value (0.0 to 1.0)

        Returns:
            Updated goal or None
        """
        goal = self._goals.get(goal_id)
        if goal:
            goal.update_progress(progress)
            self._save_goals()
        return goal

    def complete_goal(self, goal_id: str) -> Optional[Goal]:
        """Mark a goal as completed."""
        goal = self._goals.get(goal_id)
        if goal:
            goal.mark_complete()
            self._save_goals()
        return goal

    def get_active_goals(self) -> List[Goal]:
        """Get all active (non-completed) goals."""
        return [g for g in self._goals.values() if g.status == "active"]

    def get_goal_file(self) -> str:
        """
        Generate goal file content for context injection.

        Returns:
            Formatted markdown string with current goals
        """
        lines = ["# Current Goals\n"]

        active_goals = self.get_active_goals()
        if not active_goals:
            lines.append("No active goals.\n")
            return '\n'.join(lines)

        for goal in active_goals:
            status_emoji = self._get_progress_emoji(goal.progress)
            lines.append(f"## {status_emoji} {goal.description}")
            lines.append(f"- Progress: {goal.progress:.0%}")

            if goal.completion_criteria:
                lines.append("- Criteria:")
                for criterion in goal.completion_criteria:
                    lines.append(f"  - [ ] {criterion}")

            if goal.blockers:
                lines.append("- Blockers:")
                for blocker in goal.blockers:
                    lines.append(f"  - {blocker}")

            lines.append("")

        return '\n'.join(lines)

    def _get_progress_emoji(self, progress: float) -> str:
        """Get emoji for progress level."""
        if progress >= 1.0:
            return ""
        elif progress >= 0.75:
            return ""
        elif progress >= 0.5:
            return ""
        elif progress >= 0.25:
            return ""
        else:
            return ""

    # === Decision Logging ===

    def log_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        reversible: bool = True,
    ) -> Decision:
        """
        Log a decision with rationale.

        Args:
            decision: The decision made
            rationale: Why this decision was made
            alternatives: Other options that were considered
            context: Additional context
            reversible: Whether this decision can be undone

        Returns:
            The recorded Decision
        """
        decision_id = hashlib.md5(
            f"{decision}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:8]

        dec = Decision(
            id=decision_id,
            decision=decision,
            rationale=rationale,
            alternatives_considered=alternatives or [],
            context=context or {},
            reversible=reversible,
        )

        self._decisions[decision_id] = dec
        self._save_decisions()

        return dec

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID."""
        return self._decisions.get(decision_id)

    def revert_decision(self, decision_id: str, reason: str) -> Optional[Decision]:
        """
        Mark a decision as reverted.

        Args:
            decision_id: Decision to revert
            reason: Why it's being reverted

        Returns:
            Updated decision or None
        """
        dec = self._decisions.get(decision_id)
        if dec and dec.reversible and not dec.reverted:
            dec.reverted = True
            dec.reverted_at = datetime.utcnow()
            dec.revert_reason = reason
            self._save_decisions()
        return dec

    def get_recent_decisions(self, limit: int = 10) -> List[Decision]:
        """Get most recent decisions."""
        sorted_decisions = sorted(
            self._decisions.values(),
            key=lambda d: d.made_at,
            reverse=True
        )
        return sorted_decisions[:limit]

    # === Batch Operations ===

    def store_batch(
        self,
        entries: List[Dict[str, Any]],
        scope: MemoryScope = MemoryScope.SESSION,
    ) -> List[MemoryEntry]:
        """
        Store multiple entries at once.

        Args:
            entries: List of dicts with key, value, and optional memory_type
            scope: Default scope for all entries

        Returns:
            List of created entries
        """
        results = []
        for entry_dict in entries:
            entry = self.store(
                key=entry_dict["key"],
                value=entry_dict["value"],
                memory_type=MemoryType(entry_dict.get("memory_type", "fact")),
                scope=MemoryScope(entry_dict.get("scope", scope.value)),
                tags=entry_dict.get("tags"),
                metadata=entry_dict.get("metadata"),
            )
            results.append(entry)
        return results

    def search_by_tags(
        self,
        tags: List[str],
        scope: Optional[MemoryScope] = None,
    ) -> List[MemoryEntry]:
        """
        Search for entries by tags.

        Args:
            tags: Tags to search for (OR logic)
            scope: Limit search to specific scope

        Returns:
            List of matching entries
        """
        results = []
        tag_set = set(tags)

        scopes = [scope] if scope else list(MemoryScope)

        for s in scopes:
            scope_dir = self._get_scope_dir(s)
            if not scope_dir.exists():
                continue

            for file_path in scope_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    entry = MemoryEntry.from_dict(data)

                    if not entry.is_expired() and tag_set & set(entry.tags):
                        results.append(entry)
                except Exception:
                    continue

        return results

    def get_all(
        self,
        scope: MemoryScope,
        memory_type: Optional[MemoryType] = None,
    ) -> List[MemoryEntry]:
        """
        Get all entries in a scope.

        Args:
            scope: Scope to retrieve from
            memory_type: Filter by type

        Returns:
            List of entries
        """
        results = []
        scope_dir = self._get_scope_dir(scope)

        if not scope_dir.exists():
            return results

        for file_path in scope_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                entry = MemoryEntry.from_dict(data)

                if entry.is_expired():
                    continue

                if memory_type and entry.memory_type != memory_type:
                    continue

                results.append(entry)
            except Exception:
                continue

        return results

    # === Cleanup & Maintenance ===

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        removed = 0

        for scope in MemoryScope:
            scope_dir = self._get_scope_dir(scope)
            if not scope_dir.exists():
                continue

            for file_path in scope_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    entry = MemoryEntry.from_dict(data)

                    if entry.is_expired():
                        file_path.unlink()
                        removed += 1
                except Exception:
                    continue

        return removed

    def clear_scope(self, scope: MemoryScope) -> int:
        """
        Clear all entries in a scope.

        Returns:
            Number of entries removed
        """
        scope_dir = self._get_scope_dir(scope)
        if not scope_dir.exists():
            return 0

        removed = 0
        for file_path in scope_dir.glob("*.json"):
            file_path.unlink()
            removed += 1

        # Clear cache entries for this scope
        self._cache = {
            k: v for k, v in self._cache.items()
            if not k.startswith(f"{scope.value}:")
        }

        return removed

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        stats = {
            "total_entries": 0,
            "by_scope": {},
            "by_type": {},
            "cache_size": len(self._cache),
            "goals_active": len(self.get_active_goals()),
            "decisions_count": len(self._decisions),
        }

        for scope in MemoryScope:
            scope_dir = self._get_scope_dir(scope)
            if scope_dir.exists():
                count = len(list(scope_dir.glob("*.json")))
                stats["by_scope"][scope.value] = count
                stats["total_entries"] += count

        return stats

    # === Persistence Helpers ===

    def _write_entry(self, entry: MemoryEntry) -> None:
        """Write entry to file."""
        path = self._get_entry_path(entry.key, entry.scope)
        with open(path, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)

    def _read_entry(self, key: str, scope: MemoryScope) -> Optional[MemoryEntry]:
        """Read entry from file."""
        path = self._get_entry_path(key, scope)
        if not path.exists():
            return None

        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return MemoryEntry.from_dict(data)
        except Exception:
            return None

    def _save_goals(self) -> None:
        """Persist goals to file."""
        goals_file = self.base_dir / "goals.json"
        data = {
            goal_id: {
                "id": g.id,
                "description": g.description,
                "status": g.status,
                "progress": g.progress,
                "sub_goals": g.sub_goals,
                "parent_goal": g.parent_goal,
                "created_at": g.created_at.isoformat(),
                "completed_at": g.completed_at.isoformat() if g.completed_at else None,
                "completion_criteria": g.completion_criteria,
                "blockers": g.blockers,
            }
            for goal_id, g in self._goals.items()
        }
        with open(goals_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_goals(self) -> None:
        """Load goals from file."""
        goals_file = self.base_dir / "goals.json"
        if not goals_file.exists():
            return

        try:
            with open(goals_file, 'r') as f:
                data = json.load(f)

            for goal_id, g_data in data.items():
                self._goals[goal_id] = Goal(
                    id=g_data["id"],
                    description=g_data["description"],
                    status=g_data["status"],
                    progress=g_data["progress"],
                    sub_goals=g_data.get("sub_goals", []),
                    parent_goal=g_data.get("parent_goal"),
                    created_at=datetime.fromisoformat(g_data["created_at"]),
                    completed_at=datetime.fromisoformat(g_data["completed_at"]) if g_data.get("completed_at") else None,
                    completion_criteria=g_data.get("completion_criteria", []),
                    blockers=g_data.get("blockers", []),
                )
        except Exception:
            pass

    def _save_decisions(self) -> None:
        """Persist decisions to file."""
        decisions_file = self.base_dir / "decisions.json"
        data = {
            dec_id: {
                "id": d.id,
                "decision": d.decision,
                "rationale": d.rationale,
                "alternatives_considered": d.alternatives_considered,
                "made_at": d.made_at.isoformat(),
                "context": d.context,
                "reversible": d.reversible,
                "reverted": d.reverted,
                "reverted_at": d.reverted_at.isoformat() if d.reverted_at else None,
                "revert_reason": d.revert_reason,
            }
            for dec_id, d in self._decisions.items()
        }
        with open(decisions_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_decisions(self) -> None:
        """Load decisions from file."""
        decisions_file = self.base_dir / "decisions.json"
        if not decisions_file.exists():
            return

        try:
            with open(decisions_file, 'r') as f:
                data = json.load(f)

            for dec_id, d_data in data.items():
                self._decisions[dec_id] = Decision(
                    id=d_data["id"],
                    decision=d_data["decision"],
                    rationale=d_data["rationale"],
                    alternatives_considered=d_data.get("alternatives_considered", []),
                    made_at=datetime.fromisoformat(d_data["made_at"]),
                    context=d_data.get("context", {}),
                    reversible=d_data.get("reversible", True),
                    reverted=d_data.get("reverted", False),
                    reverted_at=datetime.fromisoformat(d_data["reverted_at"]) if d_data.get("reverted_at") else None,
                    revert_reason=d_data.get("revert_reason"),
                )
        except Exception:
            pass

    def _load_state(self) -> None:
        """Load all persisted state."""
        self._load_goals()
        self._load_decisions()

        if self.auto_cleanup:
            self.cleanup_expired()

    # === Context Export ===

    def export_context(
        self,
        include_goals: bool = True,
        include_decisions: bool = True,
        include_recent_facts: int = 20,
    ) -> str:
        """
        Export current memory context as markdown.

        Useful for injecting into new conversation contexts.

        Args:
            include_goals: Include active goals
            include_decisions: Include recent decisions
            include_recent_facts: Number of recent facts to include

        Returns:
            Formatted markdown string
        """
        lines = ["# Cross-Context Memory Export\n"]
        lines.append(f"*Exported at: {datetime.utcnow().isoformat()}*\n")

        if include_goals:
            lines.append(self.get_goal_file())

        if include_decisions:
            lines.append("\n## Recent Decisions\n")
            for dec in self.get_recent_decisions(5):
                status = " (reverted)" if dec.reverted else ""
                lines.append(f"### {dec.decision}{status}")
                lines.append(f"- Rationale: {dec.rationale}")
                if dec.alternatives_considered:
                    lines.append(f"- Alternatives: {', '.join(dec.alternatives_considered)}")
                lines.append("")

        if include_recent_facts:
            lines.append("\n## Recent Facts\n")
            facts = self.get_all(MemoryScope.SESSION, MemoryType.FACT)
            sorted_facts = sorted(facts, key=lambda f: f.created_at, reverse=True)

            for fact in sorted_facts[:include_recent_facts]:
                lines.append(f"- **{fact.key}**: {fact.value}")

        return '\n'.join(lines)


# Context manager for session-scoped memory
@contextmanager
def memory_session(
    base_dir: Optional[Path] = None,
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
):
    """
    Context manager for session-scoped memory.

    Usage:
        with memory_session(project_id="my_project") as memory:
            memory.store("key", "value")
            value = memory.get("key")
    """
    memory = CrossContextMemoryService(
        base_dir=base_dir,
        session_id=session_id,
        project_id=project_id,
    )

    try:
        yield memory
    finally:
        # Cleanup session memory on exit if needed
        pass
