"""
Week 93: Version Tracker Tests

Comprehensive tests for MarQedVersionTracker:
- Snapshot creation and retrieval
- Content-addressed deduplication
- History chain tracking
- Diff calculation
- Action linking
- Cleanup and statistics
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.harness.adapters.version_tracker import (
    MarQedVersionTracker,
    _calculate_content_hash,
    _estimate_tokens,
    _deep_diff,
)
from app.harness.core.protocols import ContextSnapshot, ContextDiff


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestUtilityFunctions:
    """Tests for helper functions."""

    def test_calculate_content_hash_consistent(self):
        """Same content should produce same hash."""
        content = {"system": "You are an assistant", "task": "Help user"}
        hash1 = _calculate_content_hash(content)
        hash2 = _calculate_content_hash(content)
        assert hash1 == hash2

    def test_calculate_content_hash_different_content(self):
        """Different content should produce different hashes."""
        content1 = {"system": "You are an assistant"}
        content2 = {"system": "You are a helper"}
        hash1 = _calculate_content_hash(content1)
        hash2 = _calculate_content_hash(content2)
        assert hash1 != hash2

    def test_calculate_content_hash_order_independent(self):
        """Hash should be independent of key order."""
        content1 = {"a": 1, "b": 2}
        content2 = {"b": 2, "a": 1}
        hash1 = _calculate_content_hash(content1)
        hash2 = _calculate_content_hash(content2)
        assert hash1 == hash2

    def test_estimate_tokens_basic(self):
        """Token estimation should work for basic content."""
        content = {"text": "Hello world"}
        tokens = _estimate_tokens(content)
        assert tokens > 0

    def test_estimate_tokens_larger_content(self):
        """Larger content should have more tokens."""
        small = {"text": "Hi"}
        large = {"text": "Hello world, this is a much longer text string!"}
        small_tokens = _estimate_tokens(small)
        large_tokens = _estimate_tokens(large)
        assert large_tokens > small_tokens

    def test_deep_diff_added(self):
        """Deep diff should detect added keys."""
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        added, removed, modified = _deep_diff(old, new)
        assert "b" in added
        assert added["b"] == 2
        assert len(removed) == 0
        assert len(modified) == 0

    def test_deep_diff_removed(self):
        """Deep diff should detect removed keys."""
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        added, removed, modified = _deep_diff(old, new)
        assert "b" in removed
        assert removed["b"] == 2
        assert len(added) == 0
        assert len(modified) == 0

    def test_deep_diff_modified(self):
        """Deep diff should detect modified values."""
        old = {"a": 1}
        new = {"a": 2}
        added, removed, modified = _deep_diff(old, new)
        assert "a" in modified
        assert modified["a"]["old"] == 1
        assert modified["a"]["new"] == 2
        assert len(added) == 0
        assert len(removed) == 0

    def test_deep_diff_nested(self):
        """Deep diff should handle nested dictionaries."""
        old = {"config": {"level": 1, "mode": "test"}}
        new = {"config": {"level": 2, "mode": "test"}}
        added, removed, modified = _deep_diff(old, new)
        assert "config" in modified
        assert "nested_changes" in modified["config"]


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================

class TestVersionTrackerInit:
    """Tests for VersionTracker initialization."""

    def test_init_default(self):
        """Default initialization should work."""
        tracker = MarQedVersionTracker()
        assert tracker._initialized is True
        assert tracker.use_postgres is False
        assert tracker.max_snapshots_per_session == 1000

    def test_init_custom_config(self):
        """Custom configuration should be applied."""
        tracker = MarQedVersionTracker(
            max_snapshots_per_session=50,
            enable_compression=True,
        )
        assert tracker.max_snapshots_per_session == 50
        assert tracker.enable_compression is True

    def test_health_check(self):
        """Health check should return True when initialized."""
        tracker = MarQedVersionTracker()
        assert tracker.health_check() is True


# =============================================================================
# SNAPSHOT CREATION TESTS
# =============================================================================

class TestSnapshotCreation:
    """Tests for snapshot creation."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_create_snapshot(self, tracker):
        """Should create a basic snapshot."""
        context = {
            "system": "You are an assistant",
            "task": "Help the user",
            "memory": "Previous conversation..."
        }

        snapshot = await tracker.snapshot(
            agent_id="felix",
            session_id="session-123",
            context=context,
        )

        assert snapshot.version_id is not None
        assert snapshot.content_hash is not None
        assert snapshot.agent_id == "felix"
        assert snapshot.session_id == "session-123"
        assert snapshot.layers == context
        assert snapshot.token_count > 0
        assert snapshot.parent_version is None

    @pytest.mark.asyncio
    async def test_create_snapshot_with_metadata(self, tracker):
        """Should create a snapshot with metadata."""
        context = {"system": "Test"}
        metadata = {"action": "code_review", "file": "main.py"}

        snapshot = await tracker.snapshot(
            agent_id="quinn",
            session_id="session-456",
            context=context,
            metadata=metadata,
        )

        assert snapshot.metadata == metadata

    @pytest.mark.asyncio
    async def test_snapshot_parent_chain(self, tracker):
        """Snapshots in same session should form parent chain."""
        context1 = {"version": 1}
        context2 = {"version": 2}

        snapshot1 = await tracker.snapshot("felix", "session-1", context1)
        snapshot2 = await tracker.snapshot("felix", "session-1", context2)

        assert snapshot1.parent_version is None
        assert snapshot2.parent_version == snapshot1.version_id

    @pytest.mark.asyncio
    async def test_snapshot_deduplication(self, tracker):
        """Same content should return same snapshot (deduplication)."""
        context = {"system": "Test", "task": "Same content"}

        snapshot1 = await tracker.snapshot("felix", "session-1", context)
        snapshot2 = await tracker.snapshot("quinn", "session-2", context)

        # Should return same snapshot (deduplicated)
        assert snapshot1.version_id == snapshot2.version_id
        assert snapshot1.content_hash == snapshot2.content_hash

    @pytest.mark.asyncio
    async def test_snapshot_timestamp(self, tracker):
        """Snapshot should have valid timestamp."""
        snapshot = await tracker.snapshot("felix", "session-1", {"test": True})

        assert isinstance(snapshot.timestamp, datetime)
        # Should be recent (within last minute)
        assert (datetime.now(timezone.utc) - snapshot.timestamp).total_seconds() < 60


# =============================================================================
# SNAPSHOT RETRIEVAL TESTS
# =============================================================================

class TestSnapshotRetrieval:
    """Tests for snapshot retrieval."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_get_snapshot_by_id(self, tracker):
        """Should retrieve snapshot by version ID."""
        original = await tracker.snapshot("felix", "session-1", {"test": True})

        retrieved = await tracker.get_snapshot(original.version_id)

        assert retrieved is not None
        assert retrieved.version_id == original.version_id
        assert retrieved.content_hash == original.content_hash

    @pytest.mark.asyncio
    async def test_get_snapshot_not_found(self, tracker):
        """Should return None for non-existent version ID."""
        retrieved = await tracker.get_snapshot("non-existent-id")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_snapshot_by_hash(self, tracker):
        """Should retrieve snapshot by content hash."""
        original = await tracker.snapshot("felix", "session-1", {"test": True})

        retrieved = await tracker.get_by_hash(original.content_hash)

        assert retrieved is not None
        assert retrieved.version_id == original.version_id

    @pytest.mark.asyncio
    async def test_get_snapshot_by_hash_not_found(self, tracker):
        """Should return None for non-existent hash."""
        retrieved = await tracker.get_by_hash("non-existent-hash")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_latest_snapshot(self, tracker):
        """Should get most recent snapshot for session."""
        await tracker.snapshot("felix", "session-1", {"version": 1})
        await tracker.snapshot("felix", "session-1", {"version": 2})
        latest = await tracker.snapshot("felix", "session-1", {"version": 3})

        retrieved = await tracker.get_latest_snapshot("session-1")

        assert retrieved.version_id == latest.version_id

    @pytest.mark.asyncio
    async def test_get_latest_snapshot_no_session(self, tracker):
        """Should return None for session with no snapshots."""
        retrieved = await tracker.get_latest_snapshot("non-existent-session")
        assert retrieved is None


# =============================================================================
# HISTORY TESTS
# =============================================================================

class TestHistoryTracking:
    """Tests for history tracking."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_session_history(self, tracker):
        """Should track history for a session."""
        await tracker.snapshot("felix", "session-1", {"v": 1})
        await tracker.snapshot("felix", "session-1", {"v": 2})
        await tracker.snapshot("felix", "session-1", {"v": 3})

        history = await tracker.get_history("session-1")

        assert len(history) == 3
        # Should be newest first
        assert history[0].layers["v"] == 3
        assert history[2].layers["v"] == 1

    @pytest.mark.asyncio
    async def test_session_history_limit(self, tracker):
        """Should respect limit parameter."""
        for i in range(10):
            await tracker.snapshot("felix", "session-1", {"v": i})

        history = await tracker.get_history("session-1", limit=5)

        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_agent_history(self, tracker):
        """Should track history for an agent across sessions."""
        await tracker.snapshot("felix", "session-1", {"v": 1})
        await tracker.snapshot("felix", "session-2", {"v": 2})
        await tracker.snapshot("quinn", "session-3", {"v": 3})  # Different agent

        history = await tracker.get_agent_history("felix")

        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_snapshot_chain(self, tracker):
        """Should build parent chain from snapshot."""
        await tracker.snapshot("felix", "session-1", {"v": 1})
        await tracker.snapshot("felix", "session-1", {"v": 2})
        final = await tracker.snapshot("felix", "session-1", {"v": 3})

        chain = await tracker.get_snapshot_chain(final.version_id)

        assert len(chain) == 3
        # Should be oldest to newest
        assert chain[0].layers["v"] == 1
        assert chain[2].layers["v"] == 3


# =============================================================================
# DIFF TESTS
# =============================================================================

class TestDiffCalculation:
    """Tests for diff calculation."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_diff_basic(self, tracker):
        """Should calculate diff between two versions."""
        s1 = await tracker.snapshot("felix", "session-1", {"a": 1, "b": 2})
        s2 = await tracker.snapshot("felix", "session-1", {"a": 1, "c": 3})

        diff = await tracker.diff(s1.version_id, s2.version_id)

        assert diff.from_version == s1.version_id
        assert diff.to_version == s2.version_id
        assert "c" in diff.added
        assert "b" in diff.removed

    @pytest.mark.asyncio
    async def test_diff_token_delta(self, tracker):
        """Should calculate token delta."""
        s1 = await tracker.snapshot("felix", "session-1", {"text": "short"})
        s2 = await tracker.snapshot("felix", "session-1", {"text": "a much longer text"})

        diff = await tracker.diff(s1.version_id, s2.version_id)

        assert diff.token_delta != 0

    @pytest.mark.asyncio
    async def test_diff_not_found(self, tracker):
        """Should raise error for non-existent version."""
        s1 = await tracker.snapshot("felix", "session-1", {"a": 1})

        with pytest.raises(ValueError, match="Snapshot not found"):
            await tracker.diff(s1.version_id, "non-existent")


# =============================================================================
# RESTORE TESTS
# =============================================================================

class TestRestore:
    """Tests for context restoration."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_restore(self, tracker):
        """Should restore context from version."""
        original_context = {"system": "Test", "task": "Help"}
        snapshot = await tracker.snapshot("felix", "session-1", original_context)

        restored = await tracker.restore(snapshot.version_id)

        assert restored == original_context

    @pytest.mark.asyncio
    async def test_restore_returns_copy(self, tracker):
        """Restored context should be a copy, not reference."""
        original_context = {"system": "Test"}
        snapshot = await tracker.snapshot("felix", "session-1", original_context)

        restored = await tracker.restore(snapshot.version_id)
        restored["system"] = "Modified"

        # Original should be unchanged
        snapshot_check = await tracker.get_snapshot(snapshot.version_id)
        assert snapshot_check.layers["system"] == "Test"

    @pytest.mark.asyncio
    async def test_restore_not_found(self, tracker):
        """Should raise error for non-existent version."""
        with pytest.raises(ValueError, match="Snapshot not found"):
            await tracker.restore("non-existent")


# =============================================================================
# ACTION LINKING TESTS
# =============================================================================

class TestActionLinking:
    """Tests for action linking."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_link_action(self, tracker):
        """Should link action to snapshot."""
        snapshot = await tracker.snapshot("felix", "session-1", {"test": True})

        await tracker.link_to_action(snapshot.version_id, "action-001")

        actions = await tracker.get_actions_for_snapshot(snapshot.version_id)
        assert "action-001" in actions

    @pytest.mark.asyncio
    async def test_link_multiple_actions(self, tracker):
        """Should link multiple actions to same snapshot."""
        snapshot = await tracker.snapshot("felix", "session-1", {"test": True})

        await tracker.link_to_action(snapshot.version_id, "action-001")
        await tracker.link_to_action(snapshot.version_id, "action-002")
        await tracker.link_to_action(snapshot.version_id, "action-003")

        actions = await tracker.get_actions_for_snapshot(snapshot.version_id)
        assert len(actions) == 3

    @pytest.mark.asyncio
    async def test_link_action_dedupe(self, tracker):
        """Should not duplicate action links."""
        snapshot = await tracker.snapshot("felix", "session-1", {"test": True})

        await tracker.link_to_action(snapshot.version_id, "action-001")
        await tracker.link_to_action(snapshot.version_id, "action-001")  # Duplicate

        actions = await tracker.get_actions_for_snapshot(snapshot.version_id)
        assert len(actions) == 1

    @pytest.mark.asyncio
    async def test_link_action_not_found(self, tracker):
        """Should raise error for non-existent snapshot."""
        with pytest.raises(ValueError, match="Snapshot not found"):
            await tracker.link_to_action("non-existent", "action-001")


# =============================================================================
# CLEANUP TESTS
# =============================================================================

class TestCleanup:
    """Tests for cleanup functionality."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots(self, tracker):
        """Should remove old snapshots."""
        # Create a snapshot
        snapshot = await tracker.snapshot("felix", "session-1", {"old": True})

        # Manually set timestamp to old date
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=100)
        tracker._snapshots[snapshot.version_id] = ContextSnapshot(
            version_id=snapshot.version_id,
            content_hash=snapshot.content_hash,
            agent_id=snapshot.agent_id,
            session_id=snapshot.session_id,
            timestamp=old_timestamp,
            layers=snapshot.layers,
            token_count=snapshot.token_count,
            parent_version=snapshot.parent_version,
            metadata=snapshot.metadata,
        )

        removed = await tracker.cleanup_old_snapshots(retention_days=90)

        assert removed == 1
        assert await tracker.get_snapshot(snapshot.version_id) is None

    @pytest.mark.asyncio
    async def test_cleanup_keeps_recent(self, tracker):
        """Should keep recent snapshots."""
        snapshot = await tracker.snapshot("felix", "session-1", {"recent": True})

        removed = await tracker.cleanup_old_snapshots(retention_days=90)

        assert removed == 0
        assert await tracker.get_snapshot(snapshot.version_id) is not None

    @pytest.mark.asyncio
    async def test_clear_session(self, tracker):
        """Should clear all snapshots for a session."""
        await tracker.snapshot("felix", "session-1", {"v": 1})
        await tracker.snapshot("felix", "session-1", {"v": 2})
        await tracker.snapshot("felix", "session-2", {"v": 3})  # Different session

        removed = tracker.clear_session("session-1")

        assert removed == 2
        history = await tracker.get_history("session-1")
        assert len(history) == 0

        # session-2 should still exist
        history2 = await tracker.get_history("session-2")
        assert len(history2) == 1

    @pytest.mark.asyncio
    async def test_session_limit_enforcement(self, tracker):
        """Should enforce max snapshots per session."""
        tracker.max_snapshots_per_session = 5

        # Create more than limit
        for i in range(10):
            await tracker.snapshot("felix", "session-1", {"v": i})

        history = await tracker.get_history("session-1")
        assert len(history) == 5


# =============================================================================
# STATISTICS TESTS
# =============================================================================

class TestStatistics:
    """Tests for statistics tracking."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_get_statistics(self, tracker):
        """Should return correct statistics."""
        await tracker.snapshot("felix", "session-1", {"v": 1})
        await tracker.snapshot("felix", "session-2", {"v": 2})
        await tracker.snapshot("quinn", "session-3", {"v": 3})

        stats = tracker.get_statistics()

        assert stats["total_snapshots"] == 3
        assert stats["unique_sessions"] == 3
        assert stats["unique_agents"] == 2

    @pytest.mark.asyncio
    async def test_statistics_with_actions(self, tracker):
        """Should track action links in statistics."""
        snapshot = await tracker.snapshot("felix", "session-1", {"test": True})
        await tracker.link_to_action(snapshot.version_id, "action-001")
        await tracker.link_to_action(snapshot.version_id, "action-002")

        stats = tracker.get_statistics()

        assert stats["total_action_links"] == 2

    @pytest.mark.asyncio
    async def test_deduplication_ratio(self, tracker):
        """Should calculate deduplication ratio."""
        # Create same content multiple times (gets deduplicated)
        same_content = {"duplicate": True}
        await tracker.snapshot("felix", "session-1", same_content)
        await tracker.snapshot("quinn", "session-2", same_content)

        # Create different content
        await tracker.snapshot("felix", "session-3", {"unique": True})

        stats = tracker.get_statistics()

        # 2 unique hashes, referenced in snapshots
        assert "deduplication_ratio" in stats


# =============================================================================
# COMPARE SESSIONS TESTS
# =============================================================================

class TestCompareSessions:
    """Tests for session comparison."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_compare_sessions(self, tracker):
        """Should compare latest snapshots from two sessions."""
        await tracker.snapshot("felix", "session-a", {"mode": "dev", "level": 1})
        await tracker.snapshot("quinn", "session-b", {"mode": "prod", "level": 2})

        comparison = await tracker.compare_sessions("session-a", "session-b")

        assert comparison["session_a"] == "session-a"
        assert comparison["session_b"] == "session-b"
        assert "diff" in comparison
        assert "mode" in comparison["diff"]["modified"]

    @pytest.mark.asyncio
    async def test_compare_sessions_not_found(self, tracker):
        """Should raise error for non-existent session."""
        await tracker.snapshot("felix", "session-a", {"test": True})

        with pytest.raises(ValueError, match="No snapshots for session"):
            await tracker.compare_sessions("session-a", "non-existent")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for version tracker workflow."""

    @pytest.fixture
    def tracker(self):
        return MarQedVersionTracker()

    @pytest.mark.asyncio
    async def test_full_workflow(self, tracker):
        """Test complete version tracking workflow."""
        # 1. Create initial snapshot
        s1 = await tracker.snapshot(
            agent_id="felix",
            session_id="workflow-test",
            context={"system": "You are an architect", "task": "Design API"},
            metadata={"action": "start"},
        )

        # 2. Link action
        await tracker.link_to_action(s1.version_id, "action-design-start")

        # 3. Create updated snapshot
        s2 = await tracker.snapshot(
            agent_id="felix",
            session_id="workflow-test",
            context={"system": "You are an architect", "task": "Review design"},
            metadata={"action": "review"},
        )

        # 4. Calculate diff
        diff = await tracker.diff(s1.version_id, s2.version_id)

        # 5. Check history
        history = await tracker.get_history("workflow-test")

        # 6. Get chain
        chain = await tracker.get_snapshot_chain(s2.version_id)

        # 7. Restore old version
        restored = await tracker.restore(s1.version_id)

        # Verify
        assert len(history) == 2
        assert len(chain) == 2
        assert s2.parent_version == s1.version_id
        assert "task" in diff.modified
        assert restored["task"] == "Design API"

    @pytest.mark.asyncio
    async def test_multi_agent_multi_session(self, tracker):
        """Test with multiple agents and sessions."""
        # Felix works on two sessions
        await tracker.snapshot("felix", "session-1", {"task": "Design"})
        await tracker.snapshot("felix", "session-2", {"task": "Build"})

        # Quinn works on one session
        await tracker.snapshot("quinn", "session-3", {"task": "Review"})

        # Check agent histories
        felix_history = await tracker.get_agent_history("felix")
        quinn_history = await tracker.get_agent_history("quinn")

        assert len(felix_history) == 2
        assert len(quinn_history) == 1

        # Check statistics
        stats = tracker.get_statistics()
        assert stats["unique_agents"] == 2
        assert stats["unique_sessions"] == 3
