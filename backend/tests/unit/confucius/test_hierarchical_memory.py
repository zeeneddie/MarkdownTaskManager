"""Unit tests for HierarchicalMemory."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.confucius.memory.hierarchical import HierarchicalMemory
from app.confucius.memory.types import (
    SessionMemory,
    EntryMemory,
    RunnableMemory,
    RelevantMemory,
)
from app.confucius.memory.compressor import CompressionResult
from app.confucius.config import ConfuciusConfig


class TestHierarchicalMemoryInit:
    """Tests for HierarchicalMemory initialization."""

    def test_init_default(self):
        """Test default initialization."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)

        assert memory.config == config
        assert memory.repository is None
        assert memory.compressor is not None
        assert memory.note_taker is not None
        assert memory._current_session is None
        assert len(memory._entries) == 0
        assert len(memory._runnables) == 0

    def test_init_with_repository(self):
        """Test initialization with repository."""
        config = ConfuciusConfig()
        mock_repo = MagicMock()

        memory = HierarchicalMemory(config, repository=mock_repo)

        assert memory.repository == mock_repo


class TestSessionOperations:
    """Tests for session operations."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory for testing."""
        config = ConfuciusConfig()
        return HierarchicalMemory(config)

    @pytest.mark.asyncio
    async def test_create_session(self, memory):
        """Test creating a new session."""
        session = await memory.create_session("test-project")

        assert session is not None
        assert session.project_id == "test-project"
        assert session.session_id is not None
        assert memory.current_session == session

    @pytest.mark.asyncio
    async def test_create_session_with_id(self, memory):
        """Test creating session with specific ID."""
        session = await memory.create_session("test-project", "my-session-id")

        assert session.session_id == "my-session-id"

    @pytest.mark.asyncio
    async def test_load_session_creates_new(self, memory):
        """Test load_session creates new when not found."""
        session = await memory.load_session("new-session", "test-project")

        assert session is not None
        assert session.session_id == "new-session"

    @pytest.mark.asyncio
    async def test_load_session_from_repository(self):
        """Test loading existing session from repository."""
        config = ConfuciusConfig()
        mock_repo = AsyncMock()
        existing_session = SessionMemory.create("test-project")
        mock_repo.get_session.return_value = existing_session

        memory = HierarchicalMemory(config, repository=mock_repo)
        session = await memory.load_session(existing_session.session_id, "test-project")

        assert session == existing_session
        mock_repo.get_session.assert_called_once()

    def test_current_session_property(self, memory):
        """Test current_session property."""
        assert memory.current_session is None

    @pytest.mark.asyncio
    async def test_current_session_after_create(self, memory):
        """Test current_session after creating."""
        session = await memory.create_session("test-project")
        assert memory.current_session == session


class TestEntryOperations:
    """Tests for entry operations."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory with session."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)
        # Create session synchronously for fixture
        memory._current_session = SessionMemory.create("test-project")
        return memory

    @pytest.mark.asyncio
    async def test_create_entry(self, memory):
        """Test creating an entry."""
        entry_id = await memory.create_entry(
            task="Analyze code patterns",
            context={"files": ["test.py"], "type": "analysis"},
        )

        assert entry_id is not None
        assert entry_id in memory._entries

    @pytest.mark.asyncio
    async def test_create_entry_no_session(self):
        """Test creating entry without session raises error."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)

        with pytest.raises(ValueError, match="No active session"):
            await memory.create_entry("task", {})

    @pytest.mark.asyncio
    async def test_get_entry(self, memory):
        """Test getting an entry."""
        entry_id = await memory.create_entry("Test task", {})

        entry = memory.get_entry(entry_id)

        assert entry is not None
        assert entry.task == "Test task"

    @pytest.mark.asyncio
    async def test_get_entry_not_found(self, memory):
        """Test getting non-existent entry."""
        entry = memory.get_entry("non-existent")
        assert entry is None

    @pytest.mark.asyncio
    async def test_complete_entry(self, memory):
        """Test completing an entry."""
        entry_id = await memory.create_entry("Test task", {})

        await memory.complete_entry(
            entry_id=entry_id,
            quality_score=0.92,
            results_summary="Analysis complete",
            extensions_called=["Felix", "Quinn"],
            iterations_used=2,
        )

        entry = memory.get_entry(entry_id)
        assert entry.quality_score == 0.92
        assert entry.completed_at is not None
        assert entry.extensions_called == ["Felix", "Quinn"]
        assert entry.iterations_used == 2

    @pytest.mark.asyncio
    async def test_complete_entry_not_found(self, memory):
        """Test completing non-existent entry (should not raise)."""
        await memory.complete_entry(
            entry_id="non-existent",
            quality_score=0.9,
            results_summary="Test",
            extensions_called=[],
            iterations_used=1,
        )
        # Should complete without error


class TestRunnableOperations:
    """Tests for runnable operations."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory with session."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)
        memory._current_session = SessionMemory.create("test-project")
        return memory

    @pytest.mark.asyncio
    async def test_update_runnable(self, memory):
        """Test recording runnable execution."""
        entry_id = await memory.create_entry("Test task", {})

        runnable_id = await memory.update_runnable(
            entry_id=entry_id,
            extension_name="Felix",
            output={"findings": 5, "patterns": ["singleton"]},
            duration_ms=1500,
        )

        assert runnable_id is not None
        assert runnable_id in memory._runnables

    @pytest.mark.asyncio
    async def test_update_runnable_links_to_entry(self, memory):
        """Test that runnable is linked to entry."""
        entry_id = await memory.create_entry("Test task", {})

        runnable_id = await memory.update_runnable(
            entry_id=entry_id,
            extension_name="Felix",
            output={"result": "ok"},
            duration_ms=100,
        )

        entry = memory.get_entry(entry_id)
        assert runnable_id in entry.runnable_ids

    @pytest.mark.asyncio
    async def test_update_runnable_with_error(self, memory):
        """Test recording runnable with error."""
        entry_id = await memory.create_entry("Test task", {})

        runnable_id = await memory.update_runnable(
            entry_id=entry_id,
            extension_name="Felix",
            output={"error": "Timeout occurred"},
            duration_ms=5000,
        )

        runnable = memory._runnables[runnable_id]
        assert runnable.success is False
        assert runnable.error_message == "Timeout occurred"


class TestRetrievalOperations:
    """Tests for memory retrieval."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory with session and data."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)
        session = SessionMemory.create("test-project")
        session.add_insight({"type": "pattern", "detail": "ADO connections"})
        session.add_pattern({"name": "Cleanup", "description": "Use try/finally"})
        memory._current_session = session
        return memory

    @pytest.mark.asyncio
    async def test_get_relevant_no_session(self):
        """Test get_relevant without session."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)

        relevant = await memory.get_relevant({}, [])

        assert isinstance(relevant, RelevantMemory)
        assert len(relevant.session_insights) == 0

    @pytest.mark.asyncio
    async def test_get_relevant_with_session(self, memory):
        """Test get_relevant with active session."""
        relevant = await memory.get_relevant(
            task_context={"task": "Analyze ADO leaks"},
            extensions=["Felix"],
        )

        assert len(relevant.session_insights) > 0
        assert len(relevant.session_patterns) > 0

    @pytest.mark.asyncio
    async def test_get_relevant_includes_entries(self, memory):
        """Test get_relevant includes completed entries."""
        # Add completed entry
        entry_id = await memory.create_entry("Test task", {})
        await memory.complete_entry(
            entry_id=entry_id,
            quality_score=0.9,
            results_summary="Done",
            extensions_called=["Felix"],
            iterations_used=1,
        )

        relevant = await memory.get_relevant({}, [])

        assert len(relevant.related_entries) > 0

    @pytest.mark.asyncio
    async def test_get_compressed_context(self, memory):
        """Test context compression."""
        context = {
            "task": "Important task",
            "code": "def test(): pass",
            "metadata": "x" * 1000,
        }

        result = await memory.get_compressed_context(
            context=context,
            target_tokens=100,
            preserve_keys=["task"],
        )

        assert isinstance(result, CompressionResult)
        assert "task" in result.kept_keys


class TestInsightOperations:
    """Tests for insight/pattern/decision operations."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory with session."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)
        memory._current_session = SessionMemory.create("test-project")
        return memory

    @pytest.mark.asyncio
    async def test_add_insight(self, memory):
        """Test adding an insight."""
        await memory.add_insight({
            "type": "discovery",
            "detail": "Found unused variables",
        })

        assert len(memory._current_session.insights) == 1
        assert memory._current_session.insights[0]["type"] == "discovery"

    @pytest.mark.asyncio
    async def test_add_insight_no_session(self):
        """Test adding insight without session (should not raise)."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)

        await memory.add_insight({"type": "test"})
        # Should complete without error

    @pytest.mark.asyncio
    async def test_add_pattern(self, memory):
        """Test adding a pattern."""
        await memory.add_pattern({
            "name": "Resource Cleanup",
            "description": "Always use try/finally",
            "examples": ["connection.asp"],
        })

        assert len(memory._current_session.patterns) == 1
        assert memory._current_session.patterns[0]["name"] == "Resource Cleanup"

    @pytest.mark.asyncio
    async def test_add_decision(self, memory):
        """Test adding a decision."""
        await memory.add_decision({
            "choice": "Use singleton pattern",
            "rationale": "Only need one instance",
        })

        assert len(memory._current_session.decisions) == 1


class TestStateOperations:
    """Tests for state and statistics."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory with session."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)
        memory._current_session = SessionMemory.create("test-project")
        return memory

    def test_get_state_no_session(self):
        """Test get_state without session."""
        config = ConfuciusConfig()
        memory = HierarchicalMemory(config)

        state = memory.get_state()

        assert state["session_id"] is None
        assert state["entries_count"] == 0

    def test_get_state_with_session(self, memory):
        """Test get_state with session."""
        state = memory.get_state()

        assert state["session_id"] is not None
        assert state["project_id"] == "test-project"
        assert state["entries_count"] == 0
        assert state["runnables_count"] == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, memory):
        """Test getting statistics."""
        stats = await memory.get_stats()

        assert "session_id" in stats
        assert "entries_count" in stats
        assert "notes" in stats

    @pytest.mark.asyncio
    async def test_get_stats_with_repository(self):
        """Test getting statistics with repository."""
        config = ConfuciusConfig()
        mock_repo = AsyncMock()
        mock_repo.get_stats.return_value = {"sessions": 5, "entries": 20}

        memory = HierarchicalMemory(config, repository=mock_repo)
        memory._current_session = SessionMemory.create("test-project")

        stats = await memory.get_stats()

        assert "database" in stats
        assert stats["database"]["sessions"] == 5


class TestCleanupOperations:
    """Tests for cleanup operations."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory."""
        config = ConfuciusConfig()
        return HierarchicalMemory(config)

    def test_clear_cache(self, memory):
        """Test clearing caches."""
        memory._entries["test"] = MagicMock()
        memory._runnables["test"] = MagicMock()

        memory.clear_cache()

        assert len(memory._entries) == 0
        assert len(memory._runnables) == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_data_no_repo(self, memory):
        """Test cleanup without repository."""
        deleted = await memory.cleanup_old_data()

        assert deleted["entries"] == 0
        assert deleted["runnables"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_data_with_repo(self):
        """Test cleanup with repository."""
        config = ConfuciusConfig()
        mock_repo = AsyncMock()
        mock_repo.cleanup_old_entries.return_value = 5
        mock_repo.cleanup_old_runnables.return_value = 10

        memory = HierarchicalMemory(config, repository=mock_repo)

        deleted = await memory.cleanup_old_data()

        assert deleted["entries"] == 5
        assert deleted["runnables"] == 10


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def memory(self):
        """Create HierarchicalMemory."""
        config = ConfuciusConfig()
        return HierarchicalMemory(config)

    def test_summarize_context(self, memory):
        """Test context summarization."""
        context = {"task": "test", "code": "x", "file": "y", "extra": "z"}

        summary = memory._summarize_context(context)

        assert "4 keys" in summary
        assert "task" in summary

    def test_summarize_context_many_keys(self, memory):
        """Test context summarization with many keys."""
        context = {f"key{i}": f"value{i}" for i in range(10)}

        summary = memory._summarize_context(context)

        assert "10 keys" in summary
        assert "..." in summary

    def test_summarize_output(self, memory):
        """Test output summarization."""
        output = {"findings": 5, "patterns": ["x", "y"]}

        summary = memory._summarize_output(output)

        assert "2 keys" in summary

    def test_summarize_output_with_error(self, memory):
        """Test output summarization with error."""
        output = {"error": "Something failed"}

        summary = memory._summarize_output(output)

        assert "Error:" in summary
        assert "Something failed" in summary


class TestWithRepository:
    """Tests for repository integration."""

    @pytest.mark.asyncio
    async def test_create_session_persists(self):
        """Test that session creation persists to repository."""
        config = ConfuciusConfig()
        mock_repo = AsyncMock()

        memory = HierarchicalMemory(config, repository=mock_repo)
        await memory.create_session("test-project")

        mock_repo.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_entry_persists(self):
        """Test that entry creation persists to repository."""
        config = ConfuciusConfig()
        mock_repo = AsyncMock()

        memory = HierarchicalMemory(config, repository=mock_repo)
        memory._current_session = SessionMemory.create("test-project")

        await memory.create_entry("Test task", {})

        mock_repo.save_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_runnable_persists(self):
        """Test that runnable update persists to repository."""
        config = ConfuciusConfig()
        mock_repo = AsyncMock()

        memory = HierarchicalMemory(config, repository=mock_repo)
        memory._current_session = SessionMemory.create("test-project")

        entry_id = await memory.create_entry("Test task", {})
        await memory.update_runnable(entry_id, "Felix", {"result": "ok"}, 100)

        assert mock_repo.save_runnable.called

    @pytest.mark.asyncio
    async def test_complete_entry_records_note(self):
        """Test that high-quality completion records note."""
        config = ConfuciusConfig()
        mock_note_taker = AsyncMock()
        mock_note_taker.auto_record_threshold = 0.7

        memory = HierarchicalMemory(config, note_taker=mock_note_taker)
        memory._current_session = SessionMemory.create("test-project")

        entry_id = await memory.create_entry("Test task", {})
        await memory.complete_entry(
            entry_id=entry_id,
            quality_score=0.92,  # Above threshold
            results_summary="Great results",
            extensions_called=["Felix"],
            iterations_used=1,
        )

        mock_note_taker.record.assert_called_once()
