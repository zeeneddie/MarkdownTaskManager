"""Unit tests for Confucius memory types."""

import pytest
from datetime import datetime
from app.confucius.memory.types import (
    MemoryScope,
    MemoryNode,
    SessionMemory,
    EntryMemory,
    RunnableMemory,
    RelevantMemory,
)


class TestMemoryScope:
    """Tests for MemoryScope enum."""

    def test_scope_values(self):
        """Test scope enum values."""
        assert MemoryScope.SESSION.value == "session"
        assert MemoryScope.ENTRY.value == "entry"
        assert MemoryScope.RUNNABLE.value == "runnable"


class TestMemoryNode:
    """Tests for MemoryNode dataclass."""

    def test_create_node(self):
        """Test creating a memory node."""
        node = MemoryNode.create(
            scope=MemoryScope.SESSION,
            content={"key": "value"},
            metadata={"source": "test"},
        )

        assert node.id is not None
        assert node.scope == MemoryScope.SESSION
        assert node.content == {"key": "value"}
        assert node.metadata == {"source": "test"}
        assert isinstance(node.created_at, datetime)
        assert node.parent_id is None
        assert node.children_ids == []
        assert node.relevance_score == 1.0
        assert node.compressed is False

    def test_create_node_with_parent(self):
        """Test creating a child node."""
        parent = MemoryNode.create(MemoryScope.SESSION, {"parent": True})
        child = MemoryNode.create(
            scope=MemoryScope.ENTRY,
            content={"child": True},
            parent_id=parent.id,
        )

        assert child.parent_id == parent.id


class TestSessionMemory:
    """Tests for SessionMemory dataclass."""

    def test_create_session(self):
        """Test creating a session."""
        session = SessionMemory.create("project-123")

        assert session.session_id is not None
        assert session.project_id == "project-123"
        assert session.insights == []
        assert session.patterns == []
        assert session.decisions == []
        assert session.preferences == {}

    def test_add_insight(self):
        """Test adding an insight."""
        session = SessionMemory.create("project-123")
        session.add_insight({"type": "performance", "detail": "Slow query detected"})

        assert len(session.insights) == 1
        assert session.insights[0]["type"] == "performance"
        assert "added_at" in session.insights[0]

    def test_add_pattern(self):
        """Test adding a pattern."""
        session = SessionMemory.create("project-123")
        session.add_pattern({"name": "ADO leak", "files": ["declaratie.asp"]})

        assert len(session.patterns) == 1
        assert session.patterns[0]["name"] == "ADO leak"

    def test_add_decision(self):
        """Test adding a decision."""
        session = SessionMemory.create("project-123")
        session.add_decision({"choice": "use async/await", "reason": "Better performance"})

        assert len(session.decisions) == 1
        assert session.decisions[0]["choice"] == "use async/await"

    def test_to_dict(self):
        """Test serialization."""
        session = SessionMemory.create("project-123")
        session.add_insight({"key": "value"})

        data = session.to_dict()

        assert data["session_id"] == session.session_id
        assert data["project_id"] == "project-123"
        assert len(data["insights"]) == 1


class TestEntryMemory:
    """Tests for EntryMemory dataclass."""

    def test_create_entry(self):
        """Test creating an entry."""
        entry = EntryMemory.create("session-123", "Analyze legacy code")

        assert entry.entry_id is not None
        assert entry.session_id == "session-123"
        assert entry.task == "Analyze legacy code"
        assert entry.quality_score == 0.0
        assert entry.completed_at is None

    def test_complete_entry(self):
        """Test completing an entry."""
        entry = EntryMemory.create("session-123", "Analyze code")
        entry.complete(0.92, "Found 5 issues, all resolved")

        assert entry.quality_score == 0.92
        assert entry.results_summary == "Found 5 issues, all resolved"
        assert entry.completed_at is not None

    def test_add_runnable(self):
        """Test linking a runnable."""
        entry = EntryMemory.create("session-123", "Test task")
        entry.add_runnable("runnable-1")
        entry.add_runnable("runnable-2")

        assert entry.runnable_ids == ["runnable-1", "runnable-2"]


class TestRunnableMemory:
    """Tests for RunnableMemory dataclass."""

    def test_create_runnable(self):
        """Test creating a runnable."""
        runnable = RunnableMemory.create("entry-123", "Felix")

        assert runnable.runnable_id is not None
        assert runnable.entry_id == "entry-123"
        assert runnable.extension_name == "Felix"
        assert runnable.success is True

    def test_complete_runnable_success(self):
        """Test completing a successful runnable."""
        runnable = RunnableMemory.create("entry-123", "Quinn")
        runnable.complete(
            output_data={"findings": 3},
            output_summary="Found 3 quality issues",
            duration_ms=1500,
            success=True,
        )

        assert runnable.output_data == {"findings": 3}
        assert runnable.output_summary == "Found 3 quality issues"
        assert runnable.duration_ms == 1500
        assert runnable.success is True
        assert runnable.error_message is None

    def test_complete_runnable_failure(self):
        """Test completing a failed runnable."""
        runnable = RunnableMemory.create("entry-123", "Marcus")
        runnable.complete(
            output_data={},
            output_summary="",
            duration_ms=500,
            success=False,
            error_message="Connection timeout",
        )

        assert runnable.success is False
        assert runnable.error_message == "Connection timeout"


class TestRelevantMemory:
    """Tests for RelevantMemory container."""

    def test_empty_check(self):
        """Test empty check."""
        relevant = RelevantMemory()
        assert relevant.is_empty() is True

        relevant.session_insights.append({"key": "value"})
        assert relevant.is_empty() is False

    def test_to_context(self):
        """Test conversion to context."""
        relevant = RelevantMemory()
        relevant.session_insights = [{"insight": "test"}]
        relevant.session_patterns = [{"pattern": "ADO leak"}]

        entry = EntryMemory.create("session", "Previous task")
        entry.complete(0.85, "Good result")
        relevant.related_entries = [entry]

        context = relevant.to_context()

        assert len(context["previous_insights"]) == 1
        assert len(context["known_patterns"]) == 1
        assert len(context["related_tasks"]) == 1
        assert context["related_tasks"][0]["score"] == 0.85
