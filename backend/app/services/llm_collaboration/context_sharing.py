"""
Context Sharing Service - B12 (Fase 24)

Real-time context sharing between concurrent agents.

Extends CrossContextMemoryService (Week 107) with:
- Real-time publish/subscribe for concurrent agents
- Context namespacing per collaboration session
- Conflict resolution for concurrent updates
- Context compression for large payloads
- TTL-based auto-cleanup

Version: 1.0.0
"""

import json
import logging
import hashlib
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class ContextScope(str, Enum):
    """Scope levels for shared context."""
    SESSION = "session"       # Single collaboration session
    TASK = "task"             # Single task within session
    AGENT = "agent"           # Agent-specific context
    GLOBAL = "global"         # Cross-session context


class ContextPriority(str, Enum):
    """Priority for context entries (affects conflict resolution)."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStrategy(str, Enum):
    """Strategy for resolving concurrent updates."""
    LAST_WRITE_WINS = "last_write_wins"   # Most recent update wins
    FIRST_WRITE_WINS = "first_write_wins" # First update preserved
    MERGE = "merge"                        # Attempt to merge
    PRIORITY = "priority"                  # Higher priority wins
    REJECT = "reject"                      # Reject conflicting writes


@dataclass
class ContextEntry:
    """
    A single context entry shared between agents.

    Attributes:
        key: Unique key within namespace
        value: The context data
        scope: Scope level
        priority: Entry priority
        owner_agent: Which agent created this
        session_id: Which session this belongs to
        version: Version number for conflict detection
        created_at: Creation timestamp
        updated_at: Last update timestamp
        expires_at: Optional expiration
        subscribers: Agents subscribed to updates
    """
    key: str
    value: Any
    scope: ContextScope
    priority: ContextPriority = ContextPriority.NORMAL
    owner_agent: Optional[str] = None
    session_id: Optional[UUID] = None
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    subscribers: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "priority": self.priority.value,
            "owner_agent": self.owner_agent,
            "session_id": str(self.session_id) if self.session_id else None,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "subscribers": list(self.subscribers),
            "metadata": self.metadata
        }


@dataclass
class ContextUpdate:
    """Notification of a context update."""
    entry: ContextEntry
    update_type: str  # "created", "updated", "deleted"
    previous_value: Any = None
    updated_by: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ContextSharingService:
    """
    Real-time context sharing between collaborating agents.

    Features:
    - Namespace isolation per session
    - Pub/sub for context updates
    - Conflict resolution strategies
    - TTL-based auto-cleanup
    - Context snapshots for recovery

    Usage:
        service = ContextSharingService()

        # Share context
        service.set_context(
            session_id=session.session_id,
            key="analysis_results",
            value={"findings": [...]},
            owner_agent="felix",
            scope=ContextScope.SESSION
        )

        # Subscribe to updates
        service.subscribe(
            session_id=session.session_id,
            key="analysis_results",
            agent_id="quinn",
            callback=handle_update
        )

        # Get context
        results = service.get_context(
            session_id=session.session_id,
            key="analysis_results"
        )
    """

    def __init__(
        self,
        default_ttl_seconds: int = 3600,
        conflict_strategy: ConflictStrategy = ConflictStrategy.LAST_WRITE_WINS,
        max_context_size_bytes: int = 10 * 1024 * 1024  # 10MB
    ):
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.conflict_strategy = conflict_strategy
        self.max_context_size = max_context_size_bytes

        # Context storage: namespace -> key -> ContextEntry
        self._context: Dict[str, Dict[str, ContextEntry]] = defaultdict(dict)

        # Subscribers: namespace -> key -> {agent_id: callback}
        self._subscribers: Dict[str, Dict[str, Dict[str, Callable]]] = defaultdict(
            lambda: defaultdict(dict)
        )

        # Lock for thread safety
        self._lock = threading.RLock()

        # Snapshots for recovery
        self._snapshots: Dict[str, Dict[str, Any]] = {}

        logger.info("ContextSharingService initialized")

    def _make_namespace(
        self,
        session_id: Optional[UUID],
        scope: ContextScope
    ) -> str:
        """Create namespace string from session and scope."""
        if scope == ContextScope.GLOBAL:
            return "global"
        if session_id is None:
            return f"anonymous:{scope.value}"
        return f"{session_id}:{scope.value}"

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes."""
        try:
            return len(json.dumps(value, default=str).encode('utf-8'))
        except (TypeError, ValueError):
            return 0

    def _resolve_conflict(
        self,
        existing: ContextEntry,
        new_value: Any,
        new_priority: ContextPriority
    ) -> bool:
        """
        Resolve conflict between existing and new value.

        Returns True if new value should be accepted.
        """
        if self.conflict_strategy == ConflictStrategy.LAST_WRITE_WINS:
            return True

        if self.conflict_strategy == ConflictStrategy.FIRST_WRITE_WINS:
            return False

        if self.conflict_strategy == ConflictStrategy.PRIORITY:
            priority_order = [ContextPriority.LOW, ContextPriority.NORMAL,
                           ContextPriority.HIGH, ContextPriority.CRITICAL]
            return priority_order.index(new_priority) >= priority_order.index(existing.priority)

        if self.conflict_strategy == ConflictStrategy.REJECT:
            return False

        # MERGE strategy - attempt to merge if both are dicts
        if self.conflict_strategy == ConflictStrategy.MERGE:
            return True  # Will be merged in set_context

        return True

    def set_context(
        self,
        key: str,
        value: Any,
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION,
        owner_agent: Optional[str] = None,
        priority: ContextPriority = ContextPriority.NORMAL,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextEntry:
        """
        Set or update a context entry.

        Args:
            key: Unique key within namespace
            value: The context data
            session_id: Session this belongs to
            scope: Scope level
            owner_agent: Which agent is setting this
            priority: Entry priority
            ttl_seconds: Time to live (None = default)
            metadata: Additional metadata

        Returns:
            The created/updated ContextEntry
        """
        # Check size limit
        size = self._estimate_size(value)
        if size > self.max_context_size:
            raise ValueError(
                f"Context value exceeds max size: {size} > {self.max_context_size}"
            )

        namespace = self._make_namespace(session_id, scope)
        expires_at = None
        if ttl_seconds is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        elif self.default_ttl:
            expires_at = datetime.now(timezone.utc) + self.default_ttl

        with self._lock:
            existing = self._context[namespace].get(key)
            update_type = "created"
            previous_value = None

            if existing:
                update_type = "updated"
                previous_value = existing.value

                # Check conflict resolution
                if not self._resolve_conflict(existing, value, priority):
                    logger.debug(f"Context update rejected for {key} by conflict strategy")
                    return existing

                # Handle merge strategy
                if (self.conflict_strategy == ConflictStrategy.MERGE and
                    isinstance(existing.value, dict) and isinstance(value, dict)):
                    merged = {**existing.value, **value}
                    value = merged

                # Update existing entry
                existing.value = value
                existing.priority = priority
                existing.version += 1
                existing.updated_at = datetime.now(timezone.utc)
                if expires_at:
                    existing.expires_at = expires_at
                if metadata:
                    existing.metadata.update(metadata)

                entry = existing
            else:
                # Create new entry
                entry = ContextEntry(
                    key=key,
                    value=value,
                    scope=scope,
                    priority=priority,
                    owner_agent=owner_agent,
                    session_id=session_id,
                    expires_at=expires_at,
                    metadata=metadata or {}
                )
                self._context[namespace][key] = entry

            # Notify subscribers
            self._notify_subscribers(
                namespace, key, entry, update_type, previous_value, owner_agent
            )

        logger.debug(f"Context {update_type}: {namespace}/{key} by {owner_agent}")
        return entry

    def get_context(
        self,
        key: str,
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION,
        default: Any = None
    ) -> Any:
        """
        Get a context value.

        Returns the value or default if not found/expired.
        """
        namespace = self._make_namespace(session_id, scope)

        with self._lock:
            entry = self._context[namespace].get(key)
            if entry is None:
                return default
            if entry.is_expired():
                del self._context[namespace][key]
                return default
            return entry.value

    def get_entry(
        self,
        key: str,
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION
    ) -> Optional[ContextEntry]:
        """Get the full context entry (including metadata)."""
        namespace = self._make_namespace(session_id, scope)

        with self._lock:
            entry = self._context[namespace].get(key)
            if entry and entry.is_expired():
                del self._context[namespace][key]
                return None
            return entry

    def delete_context(
        self,
        key: str,
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION,
        deleted_by: Optional[str] = None
    ) -> bool:
        """
        Delete a context entry.

        Returns True if entry existed and was deleted.
        """
        namespace = self._make_namespace(session_id, scope)

        with self._lock:
            entry = self._context[namespace].get(key)
            if entry is None:
                return False

            del self._context[namespace][key]

            # Notify subscribers of deletion
            self._notify_subscribers(
                namespace, key, entry, "deleted", entry.value, deleted_by
            )

        logger.debug(f"Context deleted: {namespace}/{key} by {deleted_by}")
        return True

    def list_context(
        self,
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION,
        prefix: Optional[str] = None
    ) -> List[str]:
        """
        List all context keys in a namespace.

        Args:
            session_id: Session to list context for
            scope: Scope level
            prefix: Optional key prefix filter

        Returns:
            List of keys
        """
        namespace = self._make_namespace(session_id, scope)

        with self._lock:
            keys = list(self._context[namespace].keys())
            if prefix:
                keys = [k for k in keys if k.startswith(prefix)]

            # Filter out expired entries
            valid_keys = []
            for key in keys:
                entry = self._context[namespace].get(key)
                if entry and not entry.is_expired():
                    valid_keys.append(key)
            return valid_keys

    def get_all_context(
        self,
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION
    ) -> Dict[str, Any]:
        """
        Get all context values in a namespace.

        Returns dict of key -> value.
        """
        namespace = self._make_namespace(session_id, scope)
        result = {}

        with self._lock:
            for key, entry in self._context[namespace].items():
                if not entry.is_expired():
                    result[key] = entry.value

        return result

    def subscribe(
        self,
        key: str,
        agent_id: str,
        callback: Callable[[ContextUpdate], None],
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION
    ) -> bool:
        """
        Subscribe to updates for a context key.

        Args:
            key: Key to subscribe to (or "*" for all keys)
            agent_id: Agent subscribing
            callback: Function to call on updates
            session_id: Session context
            scope: Scope level

        Returns:
            True if subscription was added
        """
        namespace = self._make_namespace(session_id, scope)

        with self._lock:
            self._subscribers[namespace][key][agent_id] = callback

            # Add to entry's subscriber list
            if key != "*":
                entry = self._context[namespace].get(key)
                if entry:
                    entry.subscribers.add(agent_id)

        logger.debug(f"Agent {agent_id} subscribed to {namespace}/{key}")
        return True

    def unsubscribe(
        self,
        key: str,
        agent_id: str,
        session_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION
    ) -> bool:
        """Unsubscribe from updates for a context key."""
        namespace = self._make_namespace(session_id, scope)

        with self._lock:
            if agent_id in self._subscribers[namespace][key]:
                del self._subscribers[namespace][key][agent_id]

                # Remove from entry's subscriber list
                if key != "*":
                    entry = self._context[namespace].get(key)
                    if entry:
                        entry.subscribers.discard(agent_id)

                logger.debug(f"Agent {agent_id} unsubscribed from {namespace}/{key}")
                return True
        return False

    def _notify_subscribers(
        self,
        namespace: str,
        key: str,
        entry: ContextEntry,
        update_type: str,
        previous_value: Any,
        updated_by: Optional[str]
    ) -> None:
        """Notify all subscribers of a context update."""
        update = ContextUpdate(
            entry=entry,
            update_type=update_type,
            previous_value=previous_value,
            updated_by=updated_by
        )

        # Notify specific key subscribers
        for agent_id, callback in self._subscribers[namespace][key].items():
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Error notifying {agent_id} of {key} update: {e}")

        # Notify wildcard subscribers
        for agent_id, callback in self._subscribers[namespace]["*"].items():
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Error notifying {agent_id} of * update: {e}")

    def create_snapshot(
        self,
        session_id: UUID,
        snapshot_id: Optional[str] = None
    ) -> str:
        """
        Create a snapshot of session context for recovery.

        Returns snapshot ID.
        """
        if snapshot_id is None:
            snapshot_id = hashlib.sha256(
                f"{session_id}:{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16]

        snapshot_data = {}
        for scope in ContextScope:
            namespace = self._make_namespace(session_id, scope)
            with self._lock:
                snapshot_data[scope.value] = {
                    key: entry.to_dict()
                    for key, entry in self._context[namespace].items()
                    if not entry.is_expired()
                }

        self._snapshots[snapshot_id] = {
            "session_id": str(session_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": snapshot_data
        }

        logger.info(f"Created snapshot {snapshot_id} for session {session_id}")
        return snapshot_id

    def restore_snapshot(
        self,
        snapshot_id: str,
        session_id: Optional[UUID] = None
    ) -> bool:
        """
        Restore context from a snapshot.

        Args:
            snapshot_id: ID of snapshot to restore
            session_id: Override session ID (use original if None)

        Returns:
            True if restore succeeded
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False

        target_session = session_id or UUID(snapshot["session_id"])

        with self._lock:
            for scope_value, entries in snapshot["data"].items():
                scope = ContextScope(scope_value)
                namespace = self._make_namespace(target_session, scope)

                for key, entry_data in entries.items():
                    # Recreate entry (simplified - ignoring some metadata)
                    self.set_context(
                        key=key,
                        value=entry_data["value"],
                        session_id=target_session,
                        scope=scope,
                        owner_agent=entry_data.get("owner_agent"),
                        priority=ContextPriority(entry_data.get("priority", "normal"))
                    )

        logger.info(f"Restored snapshot {snapshot_id} to session {target_session}")
        return True

    def cleanup_expired(self) -> int:
        """
        Remove expired context entries.

        Returns count of removed entries.
        """
        removed = 0

        with self._lock:
            for namespace in list(self._context.keys()):
                for key in list(self._context[namespace].keys()):
                    entry = self._context[namespace][key]
                    if entry.is_expired():
                        del self._context[namespace][key]
                        removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} expired context entries")
        return removed

    def clear_session(self, session_id: UUID) -> int:
        """
        Clear all context for a session.

        Returns count of removed entries.
        """
        removed = 0

        with self._lock:
            for scope in ContextScope:
                if scope == ContextScope.GLOBAL:
                    continue  # Don't clear global context

                namespace = self._make_namespace(session_id, scope)
                removed += len(self._context[namespace])
                self._context[namespace].clear()
                self._subscribers[namespace].clear()

        logger.info(f"Cleared {removed} context entries for session {session_id}")
        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Get context sharing statistics."""
        with self._lock:
            total_entries = sum(
                len(entries) for entries in self._context.values()
            )
            total_subscribers = sum(
                len(subs)
                for ns_subs in self._subscribers.values()
                for subs in ns_subs.values()
            )

            return {
                "total_namespaces": len(self._context),
                "total_entries": total_entries,
                "total_subscribers": total_subscribers,
                "total_snapshots": len(self._snapshots),
                "namespaces": list(self._context.keys())
            }


# Singleton instance
_context_service: Optional[ContextSharingService] = None


def get_context_sharing_service() -> ContextSharingService:
    """Get or create singleton ContextSharingService."""
    global _context_service
    if _context_service is None:
        _context_service = ContextSharingService()
    return _context_service
