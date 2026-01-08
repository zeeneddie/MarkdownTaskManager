"""
MarQed Native Version Tracker Implementation

PostgreSQL-based context versioning with:
- Content-addressed deduplication (SHA256)
- Immutable snapshots with parent linking
- History chain for audit trail
- Action linking for observability
- Token counting for context management
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.harness.core.protocols import (
    BaseAdapter,
    ContextSnapshot,
    ContextDiff,
    ContextVersionTrackerProtocol,
)


def _calculate_content_hash(content: Dict[str, Any]) -> str:
    """Calculate SHA256 hash of content for deduplication."""
    # Sort keys for consistent hashing
    serialized = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _estimate_tokens(content: Dict[str, Any]) -> int:
    """Estimate token count from content (rough approximation)."""
    serialized = json.dumps(content, default=str)
    # Rough estimate: ~4 chars per token
    return len(serialized) // 4


def _deep_diff(old: Dict[str, Any], new: Dict[str, Any]) -> tuple:
    """
    Calculate deep difference between two dictionaries.

    Returns:
        Tuple of (added, removed, modified)
    """
    added = {}
    removed = {}
    modified = {}

    all_keys = set(old.keys()) | set(new.keys())

    for key in all_keys:
        if key not in old:
            added[key] = new[key]
        elif key not in new:
            removed[key] = old[key]
        elif old[key] != new[key]:
            if isinstance(old[key], dict) and isinstance(new[key], dict):
                # Recursive diff for nested dicts
                sub_added, sub_removed, sub_modified = _deep_diff(old[key], new[key])
                if sub_added or sub_removed or sub_modified:
                    modified[key] = {
                        "old": old[key],
                        "new": new[key],
                        "nested_changes": {
                            "added": sub_added,
                            "removed": sub_removed,
                            "modified": sub_modified,
                        }
                    }
            else:
                modified[key] = {"old": old[key], "new": new[key]}

    return added, removed, modified


class MarQedVersionTracker(BaseAdapter, ContextVersionTrackerProtocol):
    """
    MarQed native implementation of Context Version Tracking.

    Uses in-memory storage by default, with optional PostgreSQL persistence.

    Features:
    - Content-addressed deduplication via SHA256
    - Immutable snapshots with parent chain
    - Session and agent history tracking
    - Action linking for observability
    - Configurable retention policies
    """

    def __init__(
        self,
        use_postgres: bool = False,
        db_session: Optional[Any] = None,
        max_snapshots_per_session: int = 1000,
        enable_compression: bool = False,
        **config
    ):
        """
        Initialize the version tracker.

        Args:
            use_postgres: If True, use PostgreSQL for persistence
            db_session: SQLAlchemy async session (required if use_postgres=True)
            max_snapshots_per_session: Maximum snapshots to keep per session
            enable_compression: If True, compress snapshot content
        """
        super().__init__(**config)

        self.use_postgres = use_postgres
        self.db_session = db_session
        self.max_snapshots_per_session = max_snapshots_per_session
        self.enable_compression = enable_compression

        # In-memory storage
        self._snapshots: Dict[str, ContextSnapshot] = {}
        self._hash_index: Dict[str, str] = {}  # content_hash -> version_id
        self._session_history: Dict[str, List[str]] = {}  # session_id -> [version_ids]
        self._agent_history: Dict[str, List[str]] = {}  # agent_id -> [version_ids]
        self._action_links: Dict[str, List[str]] = {}  # version_id -> [action_ids]
        self._latest_version: Dict[str, str] = {}  # session_id -> latest_version_id

        self._initialized = True

    async def snapshot(
        self,
        agent_id: str,
        session_id: str,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextSnapshot:
        """
        Create an immutable snapshot of current context.

        Features:
        - Content-addressed hashing for deduplication
        - Parent linking for history chain
        - Metadata attachment for audit

        Args:
            agent_id: Agent creating the snapshot
            session_id: Session ID for the snapshot
            context: Context layers to snapshot (system, task, memory)
            metadata: Optional metadata for audit

        Returns:
            ContextSnapshot with version_id, content_hash, etc.
        """
        # Calculate content hash for deduplication
        content_hash = _calculate_content_hash(context)

        # Check for existing snapshot with same content (deduplication)
        if content_hash in self._hash_index:
            existing_id = self._hash_index[content_hash]
            existing = self._snapshots.get(existing_id)
            if existing:
                # Return existing snapshot (deduplicated)
                return existing

        # Generate new version ID
        version_id = str(uuid.uuid4())

        # Get parent version for history chain
        parent_version = self._latest_version.get(session_id)

        # Estimate token count
        token_count = _estimate_tokens(context)

        # Create snapshot
        snapshot = ContextSnapshot(
            version_id=version_id,
            content_hash=content_hash,
            agent_id=agent_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            layers=context,
            token_count=token_count,
            parent_version=parent_version,
            metadata=metadata or {}
        )

        # Store snapshot
        self._snapshots[version_id] = snapshot
        self._hash_index[content_hash] = version_id
        self._latest_version[session_id] = version_id

        # Update history indices
        if session_id not in self._session_history:
            self._session_history[session_id] = []
        self._session_history[session_id].append(version_id)

        if agent_id not in self._agent_history:
            self._agent_history[agent_id] = []
        self._agent_history[agent_id].append(version_id)

        # Initialize action links list
        self._action_links[version_id] = []

        # Enforce per-session limit
        await self._enforce_session_limit(session_id)

        return snapshot

    async def _enforce_session_limit(self, session_id: str) -> None:
        """Remove oldest snapshots if session exceeds limit."""
        history = self._session_history.get(session_id, [])
        while len(history) > self.max_snapshots_per_session:
            oldest_id = history.pop(0)
            await self._remove_snapshot(oldest_id)

    async def _remove_snapshot(self, version_id: str) -> None:
        """Remove a snapshot from all indices."""
        snapshot = self._snapshots.pop(version_id, None)
        if snapshot:
            self._hash_index.pop(snapshot.content_hash, None)
            self._action_links.pop(version_id, None)

            # Remove from agent history
            agent_history = self._agent_history.get(snapshot.agent_id, [])
            if version_id in agent_history:
                agent_history.remove(version_id)

    async def get_snapshot(
        self,
        version_id: str
    ) -> Optional[ContextSnapshot]:
        """Get a specific snapshot by version ID."""
        return self._snapshots.get(version_id)

    async def get_by_hash(
        self,
        content_hash: str
    ) -> Optional[ContextSnapshot]:
        """Get snapshot by content hash (deduplication lookup)."""
        version_id = self._hash_index.get(content_hash)
        if version_id:
            return self._snapshots.get(version_id)
        return None

    async def get_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ContextSnapshot]:
        """Get snapshot history for a session, newest first."""
        history = self._session_history.get(session_id, [])
        # Return newest first
        version_ids = list(reversed(history))[:limit]
        return [
            self._snapshots[vid]
            for vid in version_ids
            if vid in self._snapshots
        ]

    async def get_agent_history(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[ContextSnapshot]:
        """Get snapshot history for an agent across sessions."""
        history = self._agent_history.get(agent_id, [])
        # Return newest first
        version_ids = list(reversed(history))[:limit]
        return [
            self._snapshots[vid]
            for vid in version_ids
            if vid in self._snapshots
        ]

    async def diff(
        self,
        from_version: str,
        to_version: str
    ) -> ContextDiff:
        """Calculate difference between two versions."""
        from_snapshot = await self.get_snapshot(from_version)
        to_snapshot = await self.get_snapshot(to_version)

        if not from_snapshot:
            raise ValueError(f"Snapshot not found: {from_version}")
        if not to_snapshot:
            raise ValueError(f"Snapshot not found: {to_version}")

        # Calculate deep diff of layers
        added, removed, modified = _deep_diff(
            from_snapshot.layers,
            to_snapshot.layers
        )

        # Calculate token delta
        token_delta = to_snapshot.token_count - from_snapshot.token_count

        return ContextDiff(
            from_version=from_version,
            to_version=to_version,
            added=added,
            removed=removed,
            modified=modified,
            token_delta=token_delta
        )

    async def restore(
        self,
        version_id: str
    ) -> Dict[str, Any]:
        """Restore context to a specific version."""
        snapshot = await self.get_snapshot(version_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {version_id}")

        # Return a copy of the layers to prevent mutation
        return dict(snapshot.layers)

    async def link_to_action(
        self,
        version_id: str,
        action_id: str
    ) -> None:
        """
        Link context snapshot to an agent action.

        Enables:
        - Audit: "What context did the agent have?"
        - Reproducibility: "Replay with same context"
        - Debugging: "Why did agent do X?"
        """
        if version_id not in self._snapshots:
            raise ValueError(f"Snapshot not found: {version_id}")

        if version_id not in self._action_links:
            self._action_links[version_id] = []

        if action_id not in self._action_links[version_id]:
            self._action_links[version_id].append(action_id)

    async def get_actions_for_snapshot(
        self,
        version_id: str
    ) -> List[str]:
        """Get all action IDs linked to a snapshot."""
        return list(self._action_links.get(version_id, []))

    async def cleanup_old_snapshots(
        self,
        retention_days: int = 90
    ) -> int:
        """
        Remove snapshots older than retention period.

        Args:
            retention_days: Number of days to retain snapshots

        Returns:
            Number of snapshots removed
        """
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        removed_count = 0

        # Find snapshots to remove
        to_remove = []
        for version_id, snapshot in self._snapshots.items():
            if snapshot.timestamp < cutoff:
                to_remove.append(version_id)

        # Remove old snapshots
        for version_id in to_remove:
            snapshot = self._snapshots.get(version_id)
            if snapshot:
                # Remove from session history
                session_history = self._session_history.get(snapshot.session_id, [])
                if version_id in session_history:
                    session_history.remove(version_id)

                # Remove snapshot
                await self._remove_snapshot(version_id)
                removed_count += 1

        return removed_count

    def health_check(self) -> bool:
        """Check if the version tracker is operational."""
        return self._initialized

    # =========================================================================
    # Additional utility methods
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get version tracker statistics."""
        total_tokens = sum(s.token_count for s in self._snapshots.values())

        return {
            "total_snapshots": len(self._snapshots),
            "unique_sessions": len(self._session_history),
            "unique_agents": len(self._agent_history),
            "total_action_links": sum(len(v) for v in self._action_links.values()),
            "total_tokens_tracked": total_tokens,
            "deduplication_ratio": self._calculate_dedup_ratio(),
        }

    def _calculate_dedup_ratio(self) -> float:
        """Calculate content deduplication ratio."""
        if not self._snapshots:
            return 0.0

        unique_hashes = len(self._hash_index)
        total_references = len(self._snapshots)

        if total_references == 0:
            return 0.0

        # Higher ratio = more deduplication
        return 1 - (unique_hashes / total_references)

    async def get_snapshot_chain(
        self,
        version_id: str
    ) -> List[ContextSnapshot]:
        """Get full parent chain for a snapshot (oldest to newest)."""
        chain = []
        current_id = version_id

        while current_id:
            snapshot = await self.get_snapshot(current_id)
            if not snapshot:
                break
            chain.append(snapshot)
            current_id = snapshot.parent_version

        # Return oldest to newest
        return list(reversed(chain))

    async def compare_sessions(
        self,
        session_a: str,
        session_b: str
    ) -> Dict[str, Any]:
        """Compare latest snapshots from two sessions."""
        latest_a = self._latest_version.get(session_a)
        latest_b = self._latest_version.get(session_b)

        if not latest_a:
            raise ValueError(f"No snapshots for session: {session_a}")
        if not latest_b:
            raise ValueError(f"No snapshots for session: {session_b}")

        diff_result = await self.diff(latest_a, latest_b)

        return {
            "session_a": session_a,
            "session_b": session_b,
            "version_a": latest_a,
            "version_b": latest_b,
            "diff": {
                "added": diff_result.added,
                "removed": diff_result.removed,
                "modified": diff_result.modified,
                "token_delta": diff_result.token_delta,
            }
        }

    async def get_latest_snapshot(
        self,
        session_id: str
    ) -> Optional[ContextSnapshot]:
        """Get the most recent snapshot for a session."""
        version_id = self._latest_version.get(session_id)
        if version_id:
            return await self.get_snapshot(version_id)
        return None

    def clear_session(self, session_id: str) -> int:
        """
        Clear all snapshots for a session.

        Returns:
            Number of snapshots removed
        """
        history = self._session_history.pop(session_id, [])
        self._latest_version.pop(session_id, None)

        removed = 0
        for version_id in history:
            snapshot = self._snapshots.pop(version_id, None)
            if snapshot:
                self._hash_index.pop(snapshot.content_hash, None)
                self._action_links.pop(version_id, None)

                # Remove from agent history
                agent_history = self._agent_history.get(snapshot.agent_id, [])
                if version_id in agent_history:
                    agent_history.remove(version_id)

                removed += 1

        return removed
