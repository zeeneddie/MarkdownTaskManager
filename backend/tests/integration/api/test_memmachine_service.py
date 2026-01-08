"""
Week 73: MemMachine Agent Memory Service Tests

Tests for persistent agent memory with:
- Session management
- Memory storage and retrieval
- Conversation history
- Fact learning
- Preference storage
- Memory compression and cleanup
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.memmachine_service import (
    MemMachineService,
    MemoryType,
    MemoryPriority
)


class TestMemoryTypeConstants:
    """Tests for MemoryType enumeration."""

    def test_conversation_type(self):
        assert MemoryType.CONVERSATION == "conversation"

    def test_fact_type(self):
        assert MemoryType.FACT == "fact"

    def test_preference_type(self):
        assert MemoryType.PREFERENCE == "preference"

    def test_skill_type(self):
        assert MemoryType.SKILL == "skill"

    def test_context_type(self):
        assert MemoryType.CONTEXT == "context"

    def test_task_type(self):
        assert MemoryType.TASK == "task"


class TestMemoryPriorityConstants:
    """Tests for MemoryPriority enumeration."""

    def test_critical_priority(self):
        assert MemoryPriority.CRITICAL == "critical"

    def test_high_priority(self):
        assert MemoryPriority.HIGH == "high"

    def test_medium_priority(self):
        assert MemoryPriority.MEDIUM == "medium"

    def test_low_priority(self):
        assert MemoryPriority.LOW == "low"

    def test_ephemeral_priority(self):
        assert MemoryPriority.EPHEMERAL == "ephemeral"


class TestMemMachineServiceInit:
    """Tests for MemMachineService initialization."""

    def test_init_creates_service(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)
        assert service.db == mock_db
        assert isinstance(service._session_cache, dict)
        assert isinstance(service._memory_cache, dict)
        assert isinstance(service._compression_queue, list)

    def test_retention_periods_exist(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)
        assert MemoryPriority.CRITICAL in service.RETENTION_PERIODS
        assert service.RETENTION_PERIODS[MemoryPriority.CRITICAL] is None  # Never expires
        assert service.RETENTION_PERIODS[MemoryPriority.HIGH] == 720
        assert service.RETENTION_PERIODS[MemoryPriority.MEDIUM] == 168

    def test_compression_threshold_exists(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)
        assert service.MAX_CONVERSATION_LENGTH == 100
        assert service.COMPRESSION_THRESHOLD == 1000


class TestSessionManagement:
    """Tests for session management."""

    @pytest.mark.asyncio
    async def test_create_session(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(
            agent_id="felix",
            project_id=uuid4(),
            context={"task": "code_review"}
        )

        assert "id" in session
        assert session["agent_id"] == "felix"
        assert session["status"] == "active"
        assert session["message_count"] == 0

    @pytest.mark.asyncio
    async def test_create_session_without_context(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="quinn")

        assert session["agent_id"] == "quinn"
        assert session["context"] == {}
        assert session["project_id"] is None

    @pytest.mark.asyncio
    async def test_end_session(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        # Create session first
        session = await service.create_session(agent_id="felix")
        session_id = session["id"]

        # End session
        result = await service.end_session(session_id, summary="Test completed")

        assert result["status"] == "completed"
        assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_end_nonexistent_session(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        result = await service.end_session("nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_get_session(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        # Create session first
        created = await service.create_session(agent_id="felix")
        session_id = created["id"]

        # Get session
        session = await service.get_session(session_id)

        assert session is not None
        assert session["id"] == session_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.get_session("nonexistent")
        assert session is None


class TestMemoryStorage:
    """Tests for memory storage."""

    @pytest.mark.asyncio
    async def test_store_memory(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="The user prefers Python",
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH
        )

        assert "id" in memory
        assert memory["content"] == "The user prefers Python"
        assert memory["memory_type"] == MemoryType.FACT
        assert memory["priority"] == MemoryPriority.HIGH

    @pytest.mark.asyncio
    async def test_store_memory_with_tags(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Test memory",
            tags=["python", "coding"]
        )

        assert memory["tags"] == ["python", "coding"]

    @pytest.mark.asyncio
    async def test_store_memory_with_metadata(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Test memory",
            metadata={"source": "code_review"}
        )

        assert memory["metadata"]["source"] == "code_review"

    @pytest.mark.asyncio
    async def test_store_memory_updates_session_count(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")
        session_id = session["id"]

        await service.store_memory(
            session_id=session_id,
            agent_id="felix",
            content="Memory 1"
        )
        await service.store_memory(
            session_id=session_id,
            agent_id="felix",
            content="Memory 2"
        )

        updated_session = await service.get_session(session_id)
        assert updated_session["memory_count"] == 2

    @pytest.mark.asyncio
    async def test_store_conversation(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_conversation(
            session_id=session["id"],
            agent_id="felix",
            role="user",
            content="Hello, can you help me?"
        )

        assert memory["memory_type"] == MemoryType.CONVERSATION
        assert memory["metadata"]["role"] == "user"


class TestMemoryRetrieval:
    """Tests for memory retrieval."""

    @pytest.mark.asyncio
    async def test_get_agent_memories(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        # Store some memories
        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Memory 1",
            memory_type=MemoryType.FACT
        )
        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Memory 2",
            memory_type=MemoryType.FACT
        )

        # Retrieve
        memories = await service.get_agent_memories(agent_id="felix")

        assert len(memories) >= 2

    @pytest.mark.asyncio
    async def test_get_agent_memories_by_type(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Fact memory",
            memory_type=MemoryType.FACT
        )
        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Preference memory",
            memory_type=MemoryType.PREFERENCE
        )

        facts = await service.get_agent_memories(
            agent_id="felix",
            memory_types=[MemoryType.FACT]
        )

        assert all(m["memory_type"] == MemoryType.FACT for m in facts)

    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")
        session_id = session["id"]

        await service.store_conversation(
            session_id=session_id,
            agent_id="felix",
            role="user",
            content="Hello"
        )
        await service.store_conversation(
            session_id=session_id,
            agent_id="felix",
            role="assistant",
            content="Hi there!"
        )

        history = await service.get_conversation_history(session_id)

        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_search_memories(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="The user loves Python programming"
        )
        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="The project uses JavaScript"
        )

        results = await service.search_memories(
            agent_id="felix",
            query="Python programming"
        )

        assert len(results) >= 1
        assert "relevance" in results[0]


class TestMemoryManagement:
    """Tests for memory management."""

    @pytest.mark.asyncio
    async def test_forget_memory(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Test memory"
        )

        result = await service.forget_memory(memory["id"])

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_forget_nonexistent_memory(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        result = await service.forget_memory("nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_compress_memories_below_threshold(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        # Store fewer than threshold
        for i in range(10):
            await service.store_conversation(
                session_id=session["id"],
                agent_id="felix",
                role="user",
                content=f"Message {i}"
            )

        result = await service.compress_memories(
            agent_id="felix",
            memory_type=MemoryType.CONVERSATION
        )

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        result = await service.cleanup_expired()

        assert result["status"] == "success"
        assert "removed_count" in result


class TestLearning:
    """Tests for fact learning."""

    @pytest.mark.asyncio
    async def test_learn_fact(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.learn_fact(
            agent_id="felix",
            session_id=session["id"],
            fact="The codebase uses FastAPI",
            source="code_analysis",
            confidence=0.95
        )

        assert memory["memory_type"] == MemoryType.FACT
        assert memory["metadata"]["confidence"] == 0.95
        assert memory["metadata"]["source"] == "code_analysis"

    @pytest.mark.asyncio
    async def test_learn_fact_high_confidence_priority(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.learn_fact(
            agent_id="felix",
            session_id=session["id"],
            fact="High confidence fact",
            source="test",
            confidence=0.95
        )

        assert memory["priority"] == MemoryPriority.HIGH

    @pytest.mark.asyncio
    async def test_learn_fact_low_confidence_priority(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.learn_fact(
            agent_id="felix",
            session_id=session["id"],
            fact="Low confidence fact",
            source="test",
            confidence=0.5
        )

        assert memory["priority"] == MemoryPriority.LOW


class TestPreferences:
    """Tests for preference storage."""

    @pytest.mark.asyncio
    async def test_store_preference(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_preference(
            agent_id="felix",
            session_id=session["id"],
            preference_key="output_format",
            preference_value="markdown"
        )

        assert memory["memory_type"] == MemoryType.PREFERENCE
        assert memory["priority"] == MemoryPriority.HIGH

    @pytest.mark.asyncio
    async def test_get_preferences(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        await service.store_preference(
            agent_id="felix",
            session_id=session["id"],
            preference_key="language",
            preference_value="python"
        )
        await service.store_preference(
            agent_id="felix",
            session_id=session["id"],
            preference_key="verbosity",
            preference_value="high"
        )

        preferences = await service.get_preferences(agent_id="felix")

        assert "language" in preferences
        assert preferences["language"] == "python"


class TestStatistics:
    """Tests for statistics and status."""

    @pytest.mark.asyncio
    async def test_get_agent_stats(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Test memory"
        )

        stats = await service.get_agent_stats(agent_id="felix")

        assert stats["agent_id"] == "felix"
        assert "total_memories" in stats
        assert "by_type" in stats
        assert "by_priority" in stats

    @pytest.mark.asyncio
    async def test_get_system_status(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        status = await service.get_system_status()

        assert status["status"] == "healthy"
        assert "total_sessions" in status
        assert "total_memories" in status
        assert "features" in status
        assert status["version"] == "1.0.0"


class TestExpirationHandling:
    """Tests for memory expiration."""

    @pytest.mark.asyncio
    async def test_memory_expires_at_set(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Test",
            priority=MemoryPriority.LOW  # Has expiration
        )

        assert memory["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_critical_memory_never_expires(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        memory = await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Critical info",
            priority=MemoryPriority.CRITICAL
        )

        assert memory["expires_at"] is None


class TestPriorityFiltering:
    """Tests for priority-based filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_minimum_priority(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Low priority",
            priority=MemoryPriority.LOW
        )
        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="High priority",
            priority=MemoryPriority.HIGH
        )

        high_only = await service.get_agent_memories(
            agent_id="felix",
            min_priority=MemoryPriority.HIGH
        )

        assert all(m["priority"] in [MemoryPriority.HIGH, MemoryPriority.CRITICAL] for m in high_only)


class TestTagFiltering:
    """Tests for tag-based filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_tags(self):
        mock_db = MagicMock()
        service = MemMachineService(mock_db)

        session = await service.create_session(agent_id="felix")

        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="Python memory",
            tags=["python", "backend"]
        )
        await service.store_memory(
            session_id=session["id"],
            agent_id="felix",
            content="JavaScript memory",
            tags=["javascript", "frontend"]
        )

        python_memories = await service.get_agent_memories(
            agent_id="felix",
            tags=["python"]
        )

        assert all("python" in m.get("tags", []) for m in python_memories)
