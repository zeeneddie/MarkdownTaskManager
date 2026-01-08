"""
Tests for MarQedToolRegistry

Week 92: Agent Harness Framework - Tool Registry
Tests for permission-based tool access, rate limiting, and sandbox execution.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from app.harness.adapters.tool_registry import (
    MarQedToolRegistry,
    RateLimiter,
    SandboxExecutor,
    DEFAULT_TOOLS,
    DEFAULT_AGENT_PERMISSIONS,
)
from app.harness.core.protocols import (
    ToolDefinition,
    ToolCallRequest,
    ToolCategory,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def tool_registry():
    """Create a fresh tool registry with defaults."""
    return MarQedToolRegistry()


@pytest.fixture
def empty_registry():
    """Create tool registry without defaults."""
    return MarQedToolRegistry(use_default_tools=False, use_default_permissions=False)


@pytest.fixture
def rate_limiter():
    """Create a fresh rate limiter."""
    return RateLimiter()


@pytest.fixture
def sandbox_executor():
    """Create a sandbox executor."""
    return SandboxExecutor(max_workers=2)


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================

class TestToolRegistryInit:
    """Tests for ToolRegistry initialization."""

    def test_init_with_defaults(self, tool_registry):
        """Test initialization with default tools and permissions."""
        assert tool_registry._initialized is True
        assert tool_registry.health_check() is True
        assert len(tool_registry._tools) == len(DEFAULT_TOOLS)
        assert len(tool_registry._permissions) == len(DEFAULT_AGENT_PERMISSIONS)

    def test_init_without_defaults(self, empty_registry):
        """Test initialization without defaults."""
        assert empty_registry._initialized is True
        assert len(empty_registry._tools) == 0
        assert len(empty_registry._permissions) == 0

    def test_health_check(self, tool_registry):
        """Test health check returns True when initialized."""
        assert tool_registry.health_check() is True

    def test_stats(self, tool_registry):
        """Test statistics gathering."""
        stats = tool_registry.get_stats()
        assert "total_tools" in stats
        assert "enabled_tools" in stats
        assert "agents_configured" in stats
        assert "audit_log_size" in stats
        assert stats["total_tools"] == len(DEFAULT_TOOLS)
        assert stats["agents_configured"] == 10


# =============================================================================
# TOOL REGISTRATION TESTS
# =============================================================================

class TestToolRegistration:
    """Tests for tool registration and management."""

    def test_register_new_tool(self, empty_registry):
        """Test registering a new tool."""
        tool = ToolDefinition(
            name="custom_tool",
            category=ToolCategory.CODE_GENERATE,
            description="A custom test tool",
            parameters={"type": "object", "properties": {}},
            handler="app.custom.handler",
        )

        success = empty_registry.register_tool(tool)
        assert success is True

        retrieved = empty_registry.get_tool("custom_tool")
        assert retrieved is not None
        assert retrieved.name == "custom_tool"

    def test_register_overwrites_existing(self, tool_registry):
        """Test that re-registering overwrites existing tool."""
        original = tool_registry.get_tool("file_read")
        assert original.description == "Read contents of a file"

        new_tool = ToolDefinition(
            name="file_read",
            category=ToolCategory.FILE_READ,
            description="Updated description",
            parameters={},
            handler="new.handler",
        )

        tool_registry.register_tool(new_tool)
        updated = tool_registry.get_tool("file_read")
        assert updated.description == "Updated description"

    def test_unregister_tool(self, tool_registry):
        """Test unregistering a tool."""
        assert tool_registry.get_tool("file_read") is not None

        success = tool_registry.unregister_tool("file_read")
        assert success is True

        assert tool_registry.get_tool("file_read") is None

    def test_unregister_nonexistent_tool(self, tool_registry):
        """Test unregistering a tool that doesn't exist."""
        success = tool_registry.unregister_tool("nonexistent_tool")
        assert success is False

    def test_get_nonexistent_tool(self, tool_registry):
        """Test getting a tool that doesn't exist."""
        tool = tool_registry.get_tool("nonexistent")
        assert tool is None

    def test_list_tools(self, tool_registry):
        """Test listing all tools."""
        tools = tool_registry.list_tools()
        assert len(tools) == len(DEFAULT_TOOLS)

        # Check structure
        file_read = next(t for t in tools if t["name"] == "file_read")
        assert file_read["category"] == "file_read"
        assert "description" in file_read


# =============================================================================
# PERMISSION TESTS
# =============================================================================

class TestPermissions:
    """Tests for tool permissions."""

    def test_get_tools_for_agent_felix(self, tool_registry):
        """Test getting tools for Felix (Feature Architect)."""
        tools = tool_registry.get_tools_for_agent("felix")
        tool_names = [t.name for t in tools]

        # Felix should have these
        assert "file_read" in tool_names
        assert "code_generate" in tool_names

        # Felix should not have these
        assert "file_delete" not in tool_names
        assert "code_execute" not in tool_names

    def test_get_tools_for_agent_betty(self, tool_registry):
        """Test getting tools for Betty (Bug Hunter - has code_execute)."""
        tools = tool_registry.get_tools_for_agent("betty")
        tool_names = [t.name for t in tools]

        # Betty can execute code for debugging
        assert "code_execute" in tool_names
        assert "file_read" in tool_names

    def test_get_tools_for_unknown_agent(self, tool_registry):
        """Test getting tools for unknown agent."""
        tools = tool_registry.get_tools_for_agent("unknown_agent")
        # Unknown agents get all tools (permissive default)
        assert len(tools) == len(DEFAULT_TOOLS)

    @pytest.mark.asyncio
    async def test_can_use_tool_allowed(self, tool_registry):
        """Test can_use_tool for allowed tool."""
        can_use = await tool_registry.can_use_tool("felix", "file_read")
        assert can_use is True

    @pytest.mark.asyncio
    async def test_can_use_tool_denied(self, tool_registry):
        """Test can_use_tool for denied tool."""
        can_use = await tool_registry.can_use_tool("felix", "file_delete")
        assert can_use is False

    @pytest.mark.asyncio
    async def test_can_use_tool_nonexistent(self, tool_registry):
        """Test can_use_tool for nonexistent tool."""
        can_use = await tool_registry.can_use_tool("felix", "nonexistent_tool")
        assert can_use is False

    def test_set_agent_permissions(self, empty_registry):
        """Test setting agent permissions."""
        # Register a tool first
        tool = ToolDefinition(
            name="test_tool",
            category=ToolCategory.CODE_GENERATE,
            description="Test",
            parameters={},
            handler="test",
        )
        empty_registry.register_tool(tool)

        # Set permissions
        empty_registry.set_agent_permissions(
            agent_id="test_agent",
            allowed=["test_tool"],
            denied=[],
            requires_approval=[],
        )

        tools = empty_registry.get_tools_for_agent("test_agent")
        assert len(tools) == 1
        assert tools[0].name == "test_tool"

    def test_quinn_readonly_permissions(self, tool_registry):
        """Test Quinn (Quality Inspector) has read-only permissions."""
        tools = tool_registry.get_tools_for_agent("quinn")
        tool_names = [t.name for t in tools]

        # Quinn should have read-only tools
        assert "file_read" in tool_names
        assert "code_analyze" in tool_names
        assert "security_scan" in tool_names

        # Quinn should not have write tools
        assert "file_write" not in tool_names
        assert "file_delete" not in tool_names


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================

class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limiter_no_limit(self, rate_limiter):
        """Test rate limiter when no limit is set."""
        assert rate_limiter.check("agent", "tool") is True

    def test_rate_limiter_within_limit(self, rate_limiter):
        """Test rate limiter within limits."""
        rate_limiter.set_limit("agent", "tool", limit=5, window_seconds=60)

        # Make 4 calls (under limit)
        for _ in range(4):
            assert rate_limiter.check("agent", "tool") is True
            rate_limiter.record("agent", "tool")

        # 5th call should still be allowed
        assert rate_limiter.check("agent", "tool") is True

    def test_rate_limiter_exceeds_limit(self, rate_limiter):
        """Test rate limiter when limit is exceeded."""
        rate_limiter.set_limit("agent", "tool", limit=3, window_seconds=60)

        # Make 3 calls
        for _ in range(3):
            rate_limiter.record("agent", "tool")

        # 4th call should be denied
        assert rate_limiter.check("agent", "tool") is False

    def test_rate_limiter_window_expiry(self, rate_limiter):
        """Test that rate limit resets after window expires."""
        rate_limiter.set_limit("agent", "tool", limit=2, window_seconds=1)

        # Make 2 calls
        rate_limiter.record("agent", "tool")
        rate_limiter.record("agent", "tool")

        assert rate_limiter.check("agent", "tool") is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        assert rate_limiter.check("agent", "tool") is True

    def test_get_remaining_calls(self, rate_limiter):
        """Test getting remaining calls."""
        rate_limiter.set_limit("agent", "tool", limit=5, window_seconds=60)

        assert rate_limiter.get_remaining("agent", "tool") == 5

        rate_limiter.record("agent", "tool")
        rate_limiter.record("agent", "tool")

        assert rate_limiter.get_remaining("agent", "tool") == 3

    def test_rate_limit_isolation(self, rate_limiter):
        """Test that rate limits are isolated per agent/tool."""
        rate_limiter.set_limit("agent1", "tool", limit=2, window_seconds=60)
        rate_limiter.set_limit("agent2", "tool", limit=2, window_seconds=60)

        # Exhaust agent1's limit
        rate_limiter.record("agent1", "tool")
        rate_limiter.record("agent1", "tool")

        # agent2 should still have quota
        assert rate_limiter.check("agent1", "tool") is False
        assert rate_limiter.check("agent2", "tool") is True

    @pytest.mark.asyncio
    async def test_tool_registry_rate_limit(self, tool_registry):
        """Test rate limiting in tool registry."""
        # Betty has code_execute with rate limit of 5
        tool_registry.set_rate_limit("betty", "code_execute", limit=2, window_seconds=60)

        # First two should pass rate limit check
        can_use_1 = await tool_registry.can_use_tool("betty", "code_execute")
        assert can_use_1 is True

        # Simulate using the tool
        tool_registry._rate_limiter.record("betty", "code_execute")
        tool_registry._rate_limiter.record("betty", "code_execute")

        # Third should fail
        can_use_2 = await tool_registry.can_use_tool("betty", "code_execute")
        assert can_use_2 is False


# =============================================================================
# TOOL EXECUTION TESTS
# =============================================================================

class TestToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_execute_allowed_tool(self, tool_registry):
        """Test executing an allowed tool."""
        request = ToolCallRequest(
            tool_name="file_read",
            agent_id="felix",
            session_id="test-session",
            parameters={"path": "/tmp/test.txt"},
        )

        result = await tool_registry.execute_tool(request)

        # Should succeed (with mock result since handler doesn't exist)
        assert result.success is True
        assert result.result is not None
        assert result.result.get("mock") is True
        assert result.audit_id is not None

    @pytest.mark.asyncio
    async def test_execute_denied_tool(self, tool_registry):
        """Test executing a denied tool."""
        request = ToolCallRequest(
            tool_name="file_delete",
            agent_id="felix",  # Felix can't delete files
            session_id="test-session",
            parameters={"path": "/tmp/test.txt"},
        )

        result = await tool_registry.execute_tool(request)

        assert result.success is False
        assert "Permission denied" in result.error

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, tool_registry):
        """Test executing a nonexistent tool."""
        request = ToolCallRequest(
            tool_name="nonexistent_tool",
            agent_id="felix",
            session_id="test-session",
            parameters={},
        )

        result = await tool_registry.execute_tool(request)

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_requires_approval(self, tool_registry):
        """Test executing a tool that requires approval."""
        # Miguel needs approval for file_delete (which is in requires_approval AND allowed for him to request)
        # First, set up permissions where tool is allowed but requires approval
        tool_registry.set_agent_permissions(
            agent_id="approval_test_agent",
            allowed=["file_delete"],
            denied=[],
            requires_approval=["file_delete"],
        )

        request = ToolCallRequest(
            tool_name="file_delete",
            agent_id="approval_test_agent",
            session_id="test-session",
            parameters={"path": "/tmp/test.txt"},
        )

        result = await tool_registry.execute_tool(request)

        assert result.success is False
        assert "requires approval" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execution_records_rate_limit(self, tool_registry):
        """Test that tool execution records rate limit."""
        tool_registry.set_rate_limit("felix", "file_read", limit=2, window_seconds=60)

        request = ToolCallRequest(
            tool_name="file_read",
            agent_id="felix",
            session_id="test-session",
            parameters={"path": "/tmp/test.txt"},
        )

        # Execute twice
        await tool_registry.execute_tool(request)
        await tool_registry.execute_tool(request)

        # Third should fail due to rate limit
        result = await tool_registry.execute_tool(request)
        assert result.success is False
        assert "Permission denied" in result.error


# =============================================================================
# TOOL SCHEMA TESTS
# =============================================================================

class TestToolSchema:
    """Tests for OpenAI-compatible tool schema generation."""

    def test_get_tool_schema(self, tool_registry):
        """Test generating tool schema for agent."""
        schema = tool_registry.get_tool_schema("felix")

        assert "tools" in schema
        assert len(schema["tools"]) > 0

        # Check structure
        first_tool = schema["tools"][0]
        assert first_tool["type"] == "function"
        assert "function" in first_tool
        assert "name" in first_tool["function"]
        assert "description" in first_tool["function"]
        assert "parameters" in first_tool["function"]

    def test_schema_only_includes_allowed_tools(self, tool_registry):
        """Test that schema only includes allowed tools."""
        schema = tool_registry.get_tool_schema("quinn")
        tool_names = [t["function"]["name"] for t in schema["tools"]]

        # Quinn should have security_scan
        assert "security_scan" in tool_names

        # Quinn should not have file_write
        assert "file_write" not in tool_names


# =============================================================================
# AUDIT LOG TESTS
# =============================================================================

class TestAuditLog:
    """Tests for audit logging."""

    @pytest.mark.asyncio
    async def test_audit_log_created(self, tool_registry):
        """Test that audit log entries are created."""
        request = ToolCallRequest(
            tool_name="file_read",
            agent_id="felix",
            session_id="test-session",
            parameters={"path": "/tmp/test.txt"},
        )

        await tool_registry.execute_tool(request)

        log = tool_registry.get_audit_log(limit=10)
        assert len(log) > 0
        assert log[-1]["agent_id"] == "felix"
        assert log[-1]["tool_name"] == "file_read"

    @pytest.mark.asyncio
    async def test_audit_log_filter_by_agent(self, tool_registry):
        """Test filtering audit log by agent."""
        # Create entries for different agents
        await tool_registry.execute_tool(ToolCallRequest(
            tool_name="file_read", agent_id="felix", session_id="s1", parameters={}
        ))
        await tool_registry.execute_tool(ToolCallRequest(
            tool_name="file_read", agent_id="marcus", session_id="s2", parameters={}
        ))

        log = tool_registry.get_audit_log(agent_id="felix", limit=100)
        assert all(entry["agent_id"] == "felix" for entry in log)

    @pytest.mark.asyncio
    async def test_audit_log_filter_by_tool(self, tool_registry):
        """Test filtering audit log by tool."""
        await tool_registry.execute_tool(ToolCallRequest(
            tool_name="file_read", agent_id="felix", session_id="s1", parameters={}
        ))
        await tool_registry.execute_tool(ToolCallRequest(
            tool_name="code_generate", agent_id="felix", session_id="s1", parameters={"language": "python", "specification": "test"}
        ))

        log = tool_registry.get_audit_log(tool_name="file_read", limit=100)
        assert all(entry["tool_name"] == "file_read" for entry in log)


# =============================================================================
# SANDBOX EXECUTION TESTS
# =============================================================================

class TestSandboxExecution:
    """Tests for sandbox execution."""

    @pytest.mark.asyncio
    async def test_sandbox_timeout(self, sandbox_executor):
        """Test sandbox timeout handling."""

        def slow_function():
            time.sleep(10)
            return "done"

        with pytest.raises(TimeoutError):
            await sandbox_executor.execute(slow_function, (), {}, timeout_seconds=1)

    @pytest.mark.asyncio
    async def test_sandbox_success(self, sandbox_executor):
        """Test successful sandbox execution."""

        def fast_function(x, y):
            return x + y

        result = await sandbox_executor.execute(
            fast_function, (2, 3), {}, timeout_seconds=5
        )
        assert result == 5

    def test_sandbox_cleanup(self, sandbox_executor):
        """Test sandbox cleanup."""
        sandbox_executor.shutdown()
        # Should not raise


# =============================================================================
# AGENT-SPECIFIC TESTS
# =============================================================================

class TestAgentSpecificPermissions:
    """Tests for agent-specific tool configurations."""

    @pytest.mark.asyncio
    async def test_miguel_database_access(self, tool_registry):
        """Test Miguel (Migration Architect) has database access."""
        can_read = await tool_registry.can_use_tool("miguel", "database_read")
        can_write = await tool_registry.can_use_tool("miguel", "database_write")

        assert can_read is True
        assert can_write is True

    @pytest.mark.asyncio
    async def test_peter_limited_access(self, tool_registry):
        """Test Peter (Product Owner) has limited tool access."""
        tools = tool_registry.get_tools_for_agent("peter")
        tool_names = [t.name for t in tools]

        # Peter should have read access
        assert "file_read" in tool_names
        assert "api_internal" in tool_names

        # Peter should not have write access
        assert "file_write" not in tool_names
        assert "code_execute" not in tool_names

    @pytest.mark.asyncio
    async def test_tessa_test_execution(self, tool_registry):
        """Test Tessa (Test Engineer) can execute code."""
        can_execute = await tool_registry.can_use_tool("tessa", "code_execute")
        assert can_execute is True

    @pytest.mark.asyncio
    async def test_diana_documentation_tools(self, tool_registry):
        """Test Diana (Documentation Writer) has appropriate tools."""
        tools = tool_registry.get_tools_for_agent("diana")
        tool_names = [t.name for t in tools]

        assert "file_read" in tool_names
        assert "file_write" in tool_names
        assert "code_generate" in tool_names

        # Diana should not have DB access
        assert "database_read" not in tool_names


# =============================================================================
# INTEGRATION WITH CONSTRAINT MANAGER TESTS
# =============================================================================

class TestConstraintManagerIntegration:
    """Tests for integration with ConstraintManager."""

    @pytest.mark.asyncio
    async def test_constraint_manager_blocks_action(self):
        """Test that constraint manager can block tool usage."""
        # Create mock constraint manager
        mock_constraint = AsyncMock()
        mock_result = Mock()
        mock_result.allowed = False
        mock_constraint.check_action.return_value = mock_result

        registry = MarQedToolRegistry(constraint_manager=mock_constraint)

        can_use = await registry.can_use_tool("felix", "file_read")
        assert can_use is False

    @pytest.mark.asyncio
    async def test_constraint_manager_allows_action(self):
        """Test that constraint manager can allow tool usage."""
        mock_constraint = AsyncMock()
        mock_result = Mock()
        mock_result.allowed = True
        mock_constraint.check_action.return_value = mock_result

        registry = MarQedToolRegistry(constraint_manager=mock_constraint)

        can_use = await registry.can_use_tool("felix", "file_read")
        assert can_use is True
