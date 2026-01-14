"""Unit tests for ConfuciusOrchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.confucius.orchestrator import (
    ConfuciusOrchestrator,
    OrchestratorState,
    ExecutionResult,
    HierarchicalMemoryManager,
    ExtensionRouter,
)
from app.confucius.config import ConfuciusConfig
from app.confucius.extensions.base import BaseAgentExtension, ExtensionMetadata


class MockExtension(BaseAgentExtension):
    """Mock extension for testing."""

    def __init__(self, name: str = "MockAgent", return_value: dict = None, match_score: float = 0.8):
        super().__init__(ExtensionMetadata(
            name=name,
            description=f"Mock {name}",
            capabilities=["test"],
            domains=["test"],
            priority=1,
        ))
        self.return_value = return_value or {"result": "success"}
        self._match_score = match_score

    async def execute(self, task: str, context: dict) -> dict:
        return self.return_value

    def matches_task(self, task: str, context: dict) -> float:
        return self._match_score


class TestOrchestratorState:
    """Tests for OrchestratorState enum."""

    def test_state_values(self):
        """Test state enum values."""
        assert OrchestratorState.IDLE.value == "idle"
        assert OrchestratorState.EXECUTING.value == "executing"
        assert OrchestratorState.COMPLETED.value == "completed"
        assert OrchestratorState.FAILED.value == "failed"


class TestExecutionResult:
    """Tests for ExecutionResult."""

    def test_result_creation(self):
        """Test creating an execution result."""
        result = ExecutionResult(
            success=True,
            output={"data": "test"},
            quality_score=0.92,
            iterations_used=1,
            extensions_called=["Felix", "Quinn"],
        )

        assert result.success is True
        assert result.quality_score == 0.92
        assert len(result.extensions_called) == 2

    def test_result_to_dict(self):
        """Test result serialization."""
        result = ExecutionResult(
            success=True,
            output={"key": "value"},
            quality_score=0.85,
            iterations_used=2,
            extensions_called=["Felix"],
            entry_id="entry-123",
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["quality_score"] == 0.85
        assert data["iterations_used"] == 2
        assert data["entry_id"] == "entry-123"


class TestHierarchicalMemoryManager:
    """Tests for HierarchicalMemoryManager."""

    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager for testing."""
        config = ConfuciusConfig.minimal()
        return HierarchicalMemoryManager(config)

    @pytest.mark.asyncio
    async def test_create_session(self, memory_manager):
        """Test creating a session."""
        session = await memory_manager.create_session("project-123")

        assert session.session_id is not None
        assert session.project_id == "project-123"

    @pytest.mark.asyncio
    async def test_create_entry(self, memory_manager):
        """Test creating an entry."""
        await memory_manager.create_session("project-123")
        entry_id = await memory_manager.create_entry("Test task", {"context": "data"})

        assert entry_id is not None
        assert entry_id in memory_manager._entries

    @pytest.mark.asyncio
    async def test_create_entry_without_session(self, memory_manager):
        """Test creating entry without session raises error."""
        with pytest.raises(ValueError, match="No active session"):
            await memory_manager.create_entry("Test", {})

    @pytest.mark.asyncio
    async def test_update_runnable(self, memory_manager):
        """Test recording a runnable."""
        await memory_manager.create_session("project-123")
        entry_id = await memory_manager.create_entry("Test", {})

        runnable_id = await memory_manager.update_runnable(
            entry_id=entry_id,
            extension_name="Felix",
            output={"analysis": "done"},
            duration_ms=1000,
        )

        assert runnable_id is not None
        assert runnable_id in memory_manager._runnables
        assert runnable_id in memory_manager._entries[entry_id].runnable_ids

    @pytest.mark.asyncio
    async def test_complete_entry(self, memory_manager):
        """Test completing an entry."""
        await memory_manager.create_session("project-123")
        entry_id = await memory_manager.create_entry("Test", {})

        await memory_manager.complete_entry(
            entry_id=entry_id,
            quality_score=0.88,
            results_summary="All good",
            extensions_called=["Felix"],
            iterations_used=1,
        )

        entry = memory_manager._entries[entry_id]
        assert entry.quality_score == 0.88
        assert entry.completed_at is not None

    @pytest.mark.asyncio
    async def test_add_insight(self, memory_manager):
        """Test adding an insight."""
        await memory_manager.create_session("project-123")

        await memory_manager.add_insight({"type": "performance", "detail": "Slow query"})

        assert len(memory_manager._current_session.insights) == 1

    @pytest.mark.asyncio
    async def test_get_relevant(self, memory_manager):
        """Test getting relevant memory."""
        await memory_manager.create_session("project-123")
        await memory_manager.add_insight({"key": "value"})

        relevant = await memory_manager.get_relevant({"task": "test"}, ["Felix"])

        assert len(relevant.session_insights) == 1

    def test_get_state(self, memory_manager):
        """Test getting memory state."""
        state = memory_manager.get_state()

        assert "session_id" in state
        assert "entries_count" in state
        assert state["entries_count"] == 0


class TestExtensionRouter:
    """Tests for ExtensionRouter."""

    @pytest.fixture
    def router(self):
        """Create a router for testing."""
        config = ConfuciusConfig.minimal()
        return ExtensionRouter(config)

    def test_register_extension(self, router):
        """Test registering an extension."""
        ext = MockExtension("Felix")
        router.register(ext)

        assert "Felix" in router.list_extensions()
        assert router.get_extension("Felix") == ext

    def test_get_nonexistent_extension(self, router):
        """Test getting non-existent extension."""
        assert router.get_extension("NonExistent") is None

    @pytest.mark.asyncio
    async def test_route_task(self, router):
        """Test routing a task."""
        ext1 = MockExtension("Felix", match_score=0.8)
        ext2 = MockExtension("Quinn", match_score=0.5)
        ext3 = MockExtension("Diana", match_score=0.1)  # Below threshold

        router.register(ext1)
        router.register(ext2)
        router.register(ext3)

        extensions = await router.route("test task", {})

        # Diana should be filtered out (below min_match_score of 0.3)
        assert len(extensions) == 2
        assert extensions[0].name == "Felix"  # Higher score first

    @pytest.mark.asyncio
    async def test_route_with_requested_extensions(self, router):
        """Test routing with specific extensions requested."""
        ext1 = MockExtension("Felix")
        ext2 = MockExtension("Quinn")

        router.register(ext1)
        router.register(ext2)

        extensions = await router.route("test", {}, requested_extensions=["Quinn"])

        assert len(extensions) == 1
        assert extensions[0].name == "Quinn"


class TestConfuciusOrchestrator:
    """Tests for ConfuciusOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator for testing."""
        config = ConfuciusConfig.minimal()
        return ConfuciusOrchestrator(config)

    def test_initial_state(self, orchestrator):
        """Test initial state."""
        assert orchestrator.state == OrchestratorState.IDLE

    def test_register_extension(self, orchestrator):
        """Test registering an extension."""
        ext = MockExtension("Felix")
        orchestrator.register_extension(ext)

        assert "Felix" in orchestrator.list_extensions()
        assert ext._orchestrator == orchestrator

    @pytest.mark.asyncio
    async def test_execute_no_extensions(self, orchestrator):
        """Test execution with no matching extensions."""
        ext = MockExtension("Felix", match_score=0.0)
        orchestrator.register_extension(ext)

        result = await orchestrator.execute(
            task="test task",
            context={},
            project_id="project-123",
        )

        assert result.success is False
        assert "No extensions matched" in result.error

    @pytest.mark.asyncio
    async def test_execute_success(self, orchestrator):
        """Test successful execution."""
        ext = MockExtension("Felix", return_value={"analysis": "complete"})
        orchestrator.register_extension(ext)

        result = await orchestrator.execute(
            task="analyze code",
            context={"files": []},
            project_id="project-123",
        )

        assert result.entry_id is not None
        assert "Felix" in result.extensions_called
        assert result.iterations_used >= 1

    @pytest.mark.asyncio
    async def test_execute_with_session_id(self, orchestrator):
        """Test execution with existing session."""
        ext = MockExtension("Felix")
        orchestrator.register_extension(ext)

        result = await orchestrator.execute(
            task="test",
            context={},
            project_id="project-123",
            session_id="session-456",
        )

        assert result.entry_id is not None

    @pytest.mark.asyncio
    async def test_execute_multiple_extensions(self, orchestrator):
        """Test execution with multiple extensions."""
        ext1 = MockExtension("Felix", return_value={"arch": "done"})
        ext2 = MockExtension("Quinn", return_value={"quality": "done"})

        orchestrator.register_extension(ext1)
        orchestrator.register_extension(ext2)

        result = await orchestrator.execute(
            task="analyze",
            context={},
            project_id="project-123",
        )

        assert len(result.extensions_called) == 2

    @pytest.mark.asyncio
    async def test_execute_with_requested_extensions(self, orchestrator):
        """Test execution with specific extensions."""
        ext1 = MockExtension("Felix")
        ext2 = MockExtension("Quinn")

        orchestrator.register_extension(ext1)
        orchestrator.register_extension(ext2)

        result = await orchestrator.execute(
            task="test",
            context={},
            project_id="project-123",
            requested_extensions=["Quinn"],
        )

        assert result.extensions_called == ["Quinn"]

    @pytest.mark.asyncio
    async def test_execute_streaming(self, orchestrator):
        """Test streaming execution."""
        ext = MockExtension("Felix")
        orchestrator.register_extension(ext)

        events = []
        async for event in orchestrator.execute_streaming(
            task="test",
            context={},
            project_id="project-123",
        ):
            events.append(event)

        event_types = [e.type for e in events]
        assert "state" in event_types
        assert "complete" in event_types or "error" in event_types

    def test_get_extension(self, orchestrator):
        """Test getting extension by name."""
        ext = MockExtension("Felix")
        orchestrator.register_extension(ext)

        assert orchestrator.get_extension("Felix") == ext
        assert orchestrator.get_extension("NonExistent") is None


class TestOrchestratorConfig:
    """Tests for orchestrator with different configs."""

    @pytest.mark.asyncio
    async def test_minimal_config(self):
        """Test with minimal config."""
        config = ConfuciusConfig.minimal()
        orchestrator = ConfuciusOrchestrator(config)

        assert orchestrator.config.quality.max_iterations == 1
        assert orchestrator.config.streaming.enabled is False

    @pytest.mark.asyncio
    async def test_default_config(self):
        """Test with default config."""
        config = ConfuciusConfig.default()
        orchestrator = ConfuciusOrchestrator(config)

        assert orchestrator.config.quality.max_iterations == 3
        assert orchestrator.config.streaming.enabled is True
