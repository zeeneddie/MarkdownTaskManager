"""
Tests for MarQedContextManager

Week 91: Agent Harness Framework
Tests for 3-layer context management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.harness.adapters.context_manager import MarQedContextManager, MemoryEntry


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def context_manager():
    """Create a fresh context manager with defaults."""
    return MarQedContextManager()


@pytest.fixture
def empty_context_manager():
    """Create context manager without default contexts."""
    return MarQedContextManager(use_default_contexts=False)


@pytest.fixture
def session_id():
    """Standard session ID for tests."""
    return "test-session-123"


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================

class TestContextManagerInit:
    """Tests for ContextManager initialization."""

    def test_init_with_defaults(self, context_manager):
        """Test initialization with default contexts."""
        assert context_manager._initialized is True
        assert context_manager.health_check() is True
        # Should have 10 default agents
        assert len(context_manager._system_contexts) == 10

    def test_init_without_defaults(self, empty_context_manager):
        """Test initialization without default contexts."""
        assert empty_context_manager._initialized is True
        assert len(empty_context_manager._system_contexts) == 0

    def test_health_check(self, context_manager):
        """Test health check returns True when initialized."""
        assert context_manager.health_check() is True

    def test_stats(self, context_manager):
        """Test statistics gathering."""
        stats = context_manager.get_stats()
        assert "system_contexts" in stats
        assert "active_sessions" in stats
        assert "total_memories" in stats
        assert "total_memory_tokens" in stats
        assert stats["system_contexts"] == 10


# =============================================================================
# SYSTEM CONTEXT TESTS
# =============================================================================

class TestSystemContext:
    """Tests for system context management."""

    @pytest.mark.asyncio
    async def test_get_default_system_context(self, context_manager):
        """Test getting default system context for known agent."""
        layer = await context_manager.get_system_context("felix")
        assert layer is not None
        assert layer.content["role"] == "Feature Architect"
        assert "System design" in layer.content["capabilities"]

    @pytest.mark.asyncio
    async def test_get_unknown_agent_context(self, context_manager):
        """Test getting context for unknown agent returns None."""
        layer = await context_manager.get_system_context("unknown_agent")
        assert layer is None

    @pytest.mark.asyncio
    async def test_set_custom_system_context(self, empty_context_manager):
        """Test setting custom system context."""
        await empty_context_manager.set_system_context(
            agent_id="custom_agent",
            context={
                "role": "Custom Agent",
                "capabilities": ["custom_task"],
                "rules": ["always be helpful"],
            }
        )

        layer = await empty_context_manager.get_system_context("custom_agent")
        assert layer is not None
        assert layer.content["role"] == "Custom Agent"
        assert layer.priority == 100  # System context has highest priority

    @pytest.mark.asyncio
    async def test_override_default_context(self, context_manager):
        """Test overriding default system context."""
        original = await context_manager.get_system_context("felix")
        assert original.content["role"] == "Feature Architect"

        # Override
        await context_manager.set_system_context(
            agent_id="felix",
            context={
                "role": "Senior Feature Architect",
                "capabilities": ["Advanced system design"],
            }
        )

        updated = await context_manager.get_system_context("felix")
        assert updated.content["role"] == "Senior Feature Architect"

    def test_list_agents(self, context_manager):
        """Test listing all agents with contexts."""
        agents = context_manager.list_agents()
        assert len(agents) == 10

        # Check structure
        felix = next(a for a in agents if a["agent_id"] == "felix")
        assert felix["role"] == "Feature Architect"
        assert "token_count" in felix
        assert "llm" in felix

    def test_get_agent_context_summary(self, context_manager):
        """Test getting agent context summary."""
        summary = context_manager.get_agent_context_summary("quinn")
        assert summary is not None
        assert summary["agent_id"] == "quinn"
        assert summary["role"] == "Quality Inspector"
        assert "Security audits" in summary["capabilities"]


# =============================================================================
# TASK CONTEXT TESTS
# =============================================================================

class TestTaskContext:
    """Tests for task context management."""

    @pytest.mark.asyncio
    async def test_set_task_context(self, context_manager, session_id):
        """Test setting task context."""
        await context_manager.set_task_context(
            session_id=session_id,
            context={
                "task": "Implement user authentication",
                "requirements": ["OAuth2", "MFA"],
            }
        )

        # Verify by resolving context
        resolved = await context_manager.resolve_context("felix", session_id)
        assert "user authentication" in resolved.task.lower()
        assert "task" in resolved.layers_used

    @pytest.mark.asyncio
    async def test_task_context_with_ttl(self, context_manager, session_id):
        """Test task context with TTL."""
        await context_manager.set_task_context(
            session_id=session_id,
            context={"task": "Short-lived task"},
            ttl_seconds=3600  # 1 hour
        )

        layer = context_manager._task_contexts.get(session_id)
        assert layer is not None
        assert layer.ttl_seconds == 3600

    @pytest.mark.asyncio
    async def test_clear_task_context(self, context_manager, session_id):
        """Test clearing task context."""
        await context_manager.set_task_context(
            session_id=session_id,
            context={"task": "Some task"}
        )

        await context_manager.clear_task_context(session_id)

        assert session_id not in context_manager._task_contexts

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, context_manager):
        """Test handling multiple sessions."""
        await context_manager.set_task_context(
            session_id="session-1",
            context={"task": "Task 1"}
        )
        await context_manager.set_task_context(
            session_id="session-2",
            context={"task": "Task 2"}
        )

        stats = context_manager.get_stats()
        assert stats["active_sessions"] == 2


# =============================================================================
# MEMORY TESTS
# =============================================================================

class TestMemory:
    """Tests for memory management."""

    @pytest.mark.asyncio
    async def test_add_memory(self, context_manager, session_id):
        """Test adding memory."""
        memory_id = await context_manager.add_memory(
            session_id=session_id,
            observation="User prefers JWT tokens over session cookies",
            tags=["preference", "auth"],
            priority=7
        )

        assert memory_id is not None
        assert len(memory_id) == 8  # UUID[:8]

        memories = context_manager._memories.get(session_id)
        assert len(memories) == 1
        assert memories[0].content == "User prefers JWT tokens over session cookies"
        assert memories[0].priority == 7

    @pytest.mark.asyncio
    async def test_add_multiple_memories(self, context_manager, session_id):
        """Test adding multiple memories."""
        await context_manager.add_memory(session_id, "Memory 1", priority=5)
        await context_manager.add_memory(session_id, "Memory 2", priority=8)
        await context_manager.add_memory(session_id, "Memory 3", priority=3)

        memories = context_manager._memories.get(session_id)
        assert len(memories) == 3

    @pytest.mark.asyncio
    async def test_memory_in_resolved_context(self, context_manager, session_id):
        """Test that memories appear in resolved context."""
        await context_manager.add_memory(
            session_id=session_id,
            observation="Important observation",
            priority=10
        )

        resolved = await context_manager.resolve_context("felix", session_id)
        assert "Important observation" in resolved.memory

    @pytest.mark.asyncio
    async def test_memory_priority_ordering(self, context_manager, session_id):
        """Test that higher priority memories are included first."""
        for i in range(5):
            await context_manager.add_memory(
                session_id=session_id,
                observation=f"Low priority memory {i}",
                priority=1
            )

        await context_manager.add_memory(
            session_id=session_id,
            observation="HIGH PRIORITY MEMORY",
            priority=10
        )

        # Resolve with limited budget
        resolved = await context_manager.resolve_context(
            "felix", session_id, token_budget=500
        )

        # High priority should be included
        assert "HIGH PRIORITY MEMORY" in resolved.memory


# =============================================================================
# CONTEXT RESOLUTION TESTS
# =============================================================================

class TestContextResolution:
    """Tests for context resolution."""

    @pytest.mark.asyncio
    async def test_resolve_system_only(self, context_manager, session_id):
        """Test resolving context with only system layer."""
        resolved = await context_manager.resolve_context("felix", session_id)

        assert resolved.system  # Has content
        assert "Feature Architect" in resolved.system
        assert "system" in resolved.layers_used
        assert resolved.context_hash  # Has hash

    @pytest.mark.asyncio
    async def test_resolve_all_layers(self, context_manager, session_id):
        """Test resolving context with all layers."""
        await context_manager.set_task_context(
            session_id=session_id,
            context={"task": "Build API"}
        )
        await context_manager.add_memory(
            session_id=session_id,
            observation="Use REST conventions"
        )

        resolved = await context_manager.resolve_context("felix", session_id)

        assert resolved.system
        assert resolved.task
        assert resolved.memory
        assert "system" in resolved.layers_used
        assert "task" in resolved.layers_used
        assert any("memory" in layer for layer in resolved.layers_used)

    @pytest.mark.asyncio
    async def test_token_budget_enforcement(self, context_manager, session_id):
        """Test that token budget is enforced."""
        # Add lots of content
        await context_manager.set_task_context(
            session_id=session_id,
            context={"task": "x" * 10000}  # Large task
        )

        resolved = await context_manager.resolve_context(
            "felix", session_id, token_budget=500
        )

        assert resolved.truncated is True
        assert resolved.total_tokens <= 500

    @pytest.mark.asyncio
    async def test_unknown_agent_default_context(self, context_manager, session_id):
        """Test resolution for unknown agent uses default."""
        resolved = await context_manager.resolve_context("unknown_agent", session_id)

        assert "unknown_agent" in resolved.system.lower()
        assert "system_default" in resolved.layers_used

    @pytest.mark.asyncio
    async def test_context_hash_changes(self, context_manager, session_id):
        """Test that context hash changes when content changes."""
        resolved1 = await context_manager.resolve_context("felix", session_id)

        await context_manager.add_memory(session_id, "New observation")

        resolved2 = await context_manager.resolve_context("felix", session_id)

        assert resolved1.context_hash != resolved2.context_hash


# =============================================================================
# MEMORY COMPRESSION TESTS
# =============================================================================

class TestMemoryCompression:
    """Tests for memory compression."""

    @pytest.mark.asyncio
    async def test_compress_memory_empty(self, context_manager, session_id):
        """Test compression on empty session."""
        tokens_saved = await context_manager.compress_memory(session_id)
        assert tokens_saved == 0

    @pytest.mark.asyncio
    async def test_compress_memory_few_entries(self, context_manager, session_id):
        """Test compression with few entries (should not compress)."""
        for i in range(5):
            await context_manager.add_memory(session_id, f"Memory {i}")

        tokens_saved = await context_manager.compress_memory(session_id)
        assert tokens_saved == 0  # Not enough to compress

    @pytest.mark.asyncio
    async def test_compress_memory_many_entries(self, context_manager, session_id):
        """Test compression with many entries."""
        for i in range(20):
            await context_manager.add_memory(
                session_id,
                f"Memory entry {i} with some content",
                priority=i % 10  # Varying priorities
            )

        original_count = len(context_manager._memories[session_id])
        tokens_saved = await context_manager.compress_memory(session_id, compression_ratio=0.2)

        new_count = len(context_manager._memories[session_id])

        assert tokens_saved > 0
        assert new_count < original_count

    @pytest.mark.asyncio
    async def test_compression_keeps_high_priority(self, context_manager, session_id):
        """Test that compression keeps high priority memories."""
        # Add low priority
        for i in range(15):
            await context_manager.add_memory(session_id, f"Low priority {i}", priority=1)

        # Add high priority
        await context_manager.add_memory(session_id, "CRITICAL MEMORY", priority=10)

        await context_manager.compress_memory(session_id, compression_ratio=0.1)

        # Check that critical memory is still there
        memories = context_manager._memories[session_id]
        critical = next((m for m in memories if m.content == "CRITICAL MEMORY"), None)
        assert critical is not None


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================

class TestSessionManagement:
    """Tests for session management."""

    @pytest.mark.asyncio
    async def test_clear_session(self, context_manager, session_id):
        """Test clearing entire session."""
        await context_manager.set_task_context(session_id, {"task": "Test"})
        await context_manager.add_memory(session_id, "Memory 1")
        await context_manager.add_memory(session_id, "Memory 2")

        await context_manager.clear_session(session_id)

        assert session_id not in context_manager._task_contexts
        assert session_id not in context_manager._memories

    @pytest.mark.asyncio
    async def test_session_isolation(self, context_manager):
        """Test that sessions are isolated."""
        await context_manager.set_task_context("session-a", {"task": "Task A"})
        await context_manager.add_memory("session-a", "Memory A")

        await context_manager.set_task_context("session-b", {"task": "Task B"})
        await context_manager.add_memory("session-b", "Memory B")

        resolved_a = await context_manager.resolve_context("felix", "session-a")
        resolved_b = await context_manager.resolve_context("felix", "session-b")

        assert "Task A" in resolved_a.task
        assert "Memory A" in resolved_a.memory

        assert "Task B" in resolved_b.task
        assert "Memory B" in resolved_b.memory


# =============================================================================
# AGENT-SPECIFIC TESTS
# =============================================================================

class TestAgentContexts:
    """Tests for agent-specific contexts."""

    @pytest.mark.asyncio
    async def test_all_default_agents_have_context(self, context_manager):
        """Test all 10 default agents have system contexts."""
        expected_agents = [
            "felix", "marcus", "quinn", "betty", "eliza",
            "diana", "tessa", "miguel", "peter", "paul"
        ]

        for agent_id in expected_agents:
            layer = await context_manager.get_system_context(agent_id)
            assert layer is not None, f"Missing context for {agent_id}"
            assert layer.content.get("role"), f"Missing role for {agent_id}"
            assert layer.content.get("capabilities"), f"Missing capabilities for {agent_id}"
            assert layer.content.get("rules"), f"Missing rules for {agent_id}"
            assert layer.content.get("ethics"), f"Missing ethics for {agent_id}"

    @pytest.mark.asyncio
    async def test_agent_llm_assignment(self, context_manager):
        """Test agents have correct LLM assignments."""
        llm_assignments = {
            "felix": "qwen2.5-coder:7b",
            "quinn": "deepseek-r1",
            "betty": "codellama",
            "diana": "mistral",
        }

        for agent_id, expected_llm in llm_assignments.items():
            layer = await context_manager.get_system_context(agent_id)
            assert layer.content.get("llm") == expected_llm

    @pytest.mark.asyncio
    async def test_peter_product_owner_context(self, context_manager):
        """Test Peter's Product Owner context."""
        layer = await context_manager.get_system_context("peter")

        assert layer.content["role"] == "Product Owner"
        assert "INVEST" in str(layer.content["rules"])
        assert "Business analysis" in layer.content["capabilities"]

    @pytest.mark.asyncio
    async def test_tessa_test_engineer_context(self, context_manager):
        """Test Tessa's Test Engineer context."""
        layer = await context_manager.get_system_context("tessa")

        assert layer.content["role"] == "Test Engineer"
        assert "Unit tests" in layer.content["capabilities"]
        assert "E2E tests" in layer.content["capabilities"]
