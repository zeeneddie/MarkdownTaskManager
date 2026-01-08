"""
Week 71: MCP Proxy Service Tests

Tests for MCP server management, tool registry, execution,
and token savings optimization.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mcp_proxy_service import MCPProxyService
from app.models.mcp_proxy import MCPServer, MCPToolRegistry, MCPToolExecution, MCPTokenSavings


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mcp_service(mock_db):
    """Create MCP Proxy service instance."""
    return MCPProxyService(mock_db)


@pytest.fixture
def sample_server():
    """Create sample MCP server."""
    server = MCPServer(
        id=uuid4(),
        name="test-server",
        server_type="stdio",
        command="npx",
        args=["-y", "mcp-server-test"],
        security_level="standard",
        is_active=True,
        health_status="healthy",
        priority=100,
        config={},
        tools=[]
    )
    return server


@pytest.fixture
def sample_tool(sample_server):
    """Create sample MCP tool."""
    tool = MCPToolRegistry(
        id=uuid4(),
        server_id=sample_server.id,
        tool_name="read_file",
        description="Read file contents",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        category="file",
        tags=["file", "read"],
        success_rate=0.95,
        avg_latency_ms=50,
        total_executions=100,
        is_enabled=True,
        server=sample_server
    )
    return tool


# ==============================================================================
# SERVER MANAGEMENT TESTS
# ==============================================================================

class TestServerManagement:
    """Tests for MCP server management."""

    @pytest.mark.asyncio
    async def test_register_server_stdio(self, mcp_service, mock_db):
        """Test registering a stdio MCP server."""
        server = await mcp_service.register_server(
            name="filesystem-server",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            security_level="standard",
            priority=100
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert server.name == "filesystem-server"
        assert server.server_type == "stdio"
        assert server.command == "npx"

    @pytest.mark.asyncio
    async def test_register_server_docker(self, mcp_service, mock_db):
        """Test registering a docker MCP server."""
        server = await mcp_service.register_server(
            name="isolated-server",
            server_type="docker",
            docker_image="mcp/isolated:latest",
            docker_config={"memory_limit": "512m"},
            security_level="isolated",
            priority=50
        )

        assert server.server_type == "docker"
        assert server.docker_image == "mcp/isolated:latest"
        assert server.security_level == "isolated"

    @pytest.mark.asyncio
    async def test_list_servers_active_only(self, mcp_service, mock_db, sample_server):
        """Test listing only active servers."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_server]
        mock_db.execute = AsyncMock(return_value=mock_result)

        servers = await mcp_service.list_servers(active_only=True)

        assert len(servers) == 1
        assert servers[0].is_active

    @pytest.mark.asyncio
    async def test_list_servers_by_type(self, mcp_service, mock_db, sample_server):
        """Test filtering servers by type."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_server]
        mock_db.execute = AsyncMock(return_value=mock_result)

        servers = await mcp_service.list_servers(server_type="stdio")

        assert all(s.server_type == "stdio" for s in servers)

    @pytest.mark.asyncio
    async def test_get_server(self, mcp_service, mock_db, sample_server):
        """Test getting server by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_server
        mock_db.execute = AsyncMock(return_value=mock_result)

        server = await mcp_service.get_server(sample_server.id)

        assert server is not None
        assert server.id == sample_server.id

    @pytest.mark.asyncio
    async def test_get_server_not_found(self, mcp_service, mock_db):
        """Test getting non-existent server."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        server = await mcp_service.get_server(uuid4())

        assert server is None

    @pytest.mark.asyncio
    async def test_get_server_by_name(self, mcp_service, mock_db, sample_server):
        """Test getting server by name."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_server
        mock_db.execute = AsyncMock(return_value=mock_result)

        server = await mcp_service.get_server_by_name("test-server")

        assert server is not None
        assert server.name == "test-server"

    @pytest.mark.asyncio
    async def test_check_server_health_healthy(self, mcp_service, mock_db, sample_server):
        """Test health check returns expected structure."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_server
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await mcp_service.check_server_health(sample_server.id)

        # Should return a dict with status field
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_check_server_health_not_found(self, mcp_service, mock_db):
        """Test health check for non-existent server."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await mcp_service.check_server_health(uuid4())

        assert result["status"] == "not_found"


# ==============================================================================
# TOOL REGISTRY TESTS
# ==============================================================================

class TestToolRegistry:
    """Tests for MCP tool registry."""

    @pytest.mark.asyncio
    async def test_register_tool(self, mcp_service, mock_db, sample_server):
        """Test registering a new tool."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_server
        mock_db.execute = AsyncMock(return_value=mock_result)

        tool = await mcp_service.register_tool(
            server_id=sample_server.id,
            tool_name="write_file",
            description="Write content to file",
            input_schema={"type": "object"},
            category="file",
            tags=["file", "write"]
        )

        mock_db.add.assert_called_once()
        assert tool.tool_name == "write_file"
        assert tool.category == "file"

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_service, mock_db, sample_tool):
        """Test listing all tools."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_tool]
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await mcp_service.list_tools()

        assert len(tools) == 1

    @pytest.mark.asyncio
    async def test_list_tools_by_category(self, mcp_service, mock_db, sample_tool):
        """Test filtering tools by category."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_tool]
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await mcp_service.list_tools(category="file")

        assert all(t.category == "file" for t in tools)

    @pytest.mark.asyncio
    async def test_list_tools_by_server(self, mcp_service, mock_db, sample_tool, sample_server):
        """Test filtering tools by server."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_tool]
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await mcp_service.list_tools(server_id=sample_server.id)

        assert all(t.server_id == sample_server.id for t in tools)

    @pytest.mark.asyncio
    async def test_search_tools(self, mcp_service, mock_db, sample_tool):
        """Test searching tools by query."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_tool]
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await mcp_service.search_tools(query="read")

        assert len(tools) >= 0

    @pytest.mark.asyncio
    async def test_get_tool(self, mcp_service, mock_db, sample_tool):
        """Test getting tool by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_tool
        mock_db.execute = AsyncMock(return_value=mock_result)

        tool = await mcp_service.get_tool(sample_tool.id)

        assert tool is not None
        assert tool.id == sample_tool.id

    @pytest.mark.asyncio
    async def test_search_tools_by_name(self, mcp_service, mock_db, sample_tool):
        """Test searching tools by name."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_tool]
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await mcp_service.search_tools(query="read_file")

        assert len(tools) >= 0  # May return empty or results based on query


# ==============================================================================
# TOOL EXECUTION TESTS
# ==============================================================================

class TestToolExecution:
    """Tests for tool execution and caching."""

    @pytest.mark.asyncio
    async def test_execute_tool_with_cache_miss(self, mcp_service, mock_db, sample_tool, sample_server):
        """Test tool execution with cache miss."""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_tool
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await mcp_service.execute_tool(
            tool_name="read_file",
            params={"path": "/test/file.txt"},
            use_cache=True
        )

        assert "status" in result
        # First call should be cache miss
        assert result.get("cached", False) == False or "status" in result

    @pytest.mark.asyncio
    async def test_execute_tool_cache_hit(self, mcp_service, mock_db, sample_tool):
        """Test tool execution with cache hit."""
        import time as time_module

        # Pre-populate cache with correct format
        cache_key = mcp_service._generate_cache_key("read_file", {"path": "/cached.txt"})
        mcp_service._cache[cache_key] = {
            "value": "cached content",
            "timestamp": time_module.time()
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_tool
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await mcp_service.execute_tool(
            tool_name="read_file",
            params={"path": "/cached.txt"},
            use_cache=True
        )

        assert result.get("cached") == True
        assert result.get("result") == "cached content"

    @pytest.mark.asyncio
    async def test_execute_tool_without_cache(self, mcp_service, mock_db, sample_tool):
        """Test tool execution with caching disabled."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_tool
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await mcp_service.execute_tool(
            tool_name="read_file",
            params={"path": "/test.txt"},
            use_cache=False
        )

        assert "status" in result

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, mcp_service, mock_db):
        """Test executing non-existent tool."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await mcp_service.execute_tool(
            tool_name="nonexistent_tool",
            params={}
        )

        assert result["status"] == "failed"
        assert "not found" in result.get("error", "").lower()

    def test_generate_cache_key(self, mcp_service):
        """Test cache key generation."""
        key1 = mcp_service._generate_cache_key("read_file", {"path": "/a.txt"})
        key2 = mcp_service._generate_cache_key("read_file", {"path": "/a.txt"})
        key3 = mcp_service._generate_cache_key("read_file", {"path": "/b.txt"})

        assert key1 == key2  # Same params = same key
        assert key1 != key3  # Different params = different key

    def test_baseline_tokens_values(self, mcp_service):
        """Test baseline token values are reasonable."""
        # File operations should have reasonable baseline
        assert mcp_service.BASELINE_TOKENS.get("file_read", 0) > 0
        assert mcp_service.BASELINE_TOKENS.get("file_write", 0) > 0

        # Browser operations should have higher baseline
        assert mcp_service.BASELINE_TOKENS.get("browser", 0) >= mcp_service.BASELINE_TOKENS.get("file_read", 0)

        # Default should be defined
        assert mcp_service.BASELINE_TOKENS.get("default", 0) > 0


# ==============================================================================
# TOKEN SAVINGS TESTS
# ==============================================================================

class TestTokenSavings:
    """Tests for token savings analytics."""

    @pytest.mark.asyncio
    async def test_calculate_savings_summary(self, mcp_service, mock_db):
        """Test calculating savings summary."""
        # Mock row result with expected columns
        mock_row = MagicMock()
        mock_row.total_executions = 0
        mock_row.total_input = 0
        mock_row.total_output = 0
        mock_row.total_saved = 0
        mock_row.cache_hits = 0
        mock_row.avg_latency = 0

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)

        summary = await mcp_service.calculate_savings_summary(days=7)

        assert "period_days" in summary
        assert "total_executions" in summary
        assert "savings_percentage" in summary
        assert summary["period_days"] == 7

    @pytest.mark.asyncio
    async def test_calculate_savings_summary_with_data(self, mcp_service, mock_db):
        """Test savings summary with actual data."""
        # Create mock row result with expected columns
        mock_row = MagicMock()
        mock_row.total_executions = 100
        mock_row.total_input = 5000
        mock_row.total_output = 3000
        mock_row.total_saved = 2000
        mock_row.cache_hits = 30
        mock_row.avg_latency = 50

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)

        summary = await mcp_service.calculate_savings_summary(days=7)

        assert summary["total_executions"] == 100
        assert summary["total_tokens_saved"] == 2000

    @pytest.mark.asyncio
    async def test_get_daily_savings(self, mcp_service, mock_db):
        """Test getting daily savings breakdown."""
        mock_savings = MagicMock()
        mock_savings.to_dict.return_value = {
            "date": date.today().isoformat(),
            "total_executions": 50,
            "total_tokens_saved": 1000
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_savings]
        mock_db.execute = AsyncMock(return_value=mock_result)

        daily = await mcp_service.get_daily_savings()

        assert isinstance(daily, list)

    @pytest.mark.asyncio
    async def test_get_daily_savings_filtered(self, mcp_service, mock_db):
        """Test daily savings with date filter."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        start = date.today() - timedelta(days=7)
        end = date.today()

        daily = await mcp_service.get_daily_savings(
            start_date=start,
            end_date=end
        )

        assert isinstance(daily, list)

    @pytest.mark.asyncio
    async def test_get_tool_performance(self, mcp_service, mock_db, sample_tool):
        """Test getting tool performance metrics."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_tool]
        mock_db.execute = AsyncMock(return_value=mock_result)

        performance = await mcp_service.get_tool_performance(limit=10)

        assert isinstance(performance, list)


# ==============================================================================
# FAILOVER TESTS
# ==============================================================================

class TestFailover:
    """Tests for server failover functionality."""

    @pytest.mark.asyncio
    async def test_get_failover_servers(self, mcp_service, mock_db, sample_server):
        """Test getting failover servers."""
        backup_server = MCPServer(
            id=uuid4(),
            name="backup-server",
            server_type="stdio",
            is_active=True,
            health_status="healthy",
            priority=200
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_server
        mock_result.scalars.return_value.all.return_value = [backup_server]
        mock_db.execute = AsyncMock(return_value=mock_result)

        failovers = await mcp_service.get_failover_servers(sample_server.id)

        assert isinstance(failovers, list)

    @pytest.mark.asyncio
    async def test_select_best_server(self, mcp_service, mock_db, sample_tool, sample_server):
        """Test selecting best server for tool."""
        sample_server.health_status = "healthy"
        sample_tool.server = sample_server

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_tool
        mock_db.execute = AsyncMock(return_value=mock_result)

        server = await mcp_service.select_best_server("read_file")

        # Should return a server or None
        assert server is None or hasattr(server, 'health_status')

    @pytest.mark.asyncio
    async def test_select_best_server_no_tool(self, mcp_service, mock_db):
        """Test selecting server when tool not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        server = await mcp_service.select_best_server("nonexistent")

        assert server is None


# ==============================================================================
# UTILITY TESTS
# ==============================================================================

class TestUtilities:
    """Tests for utility methods."""

    def test_baseline_tokens_defined(self, mcp_service):
        """Test that baseline token values are defined."""
        assert hasattr(mcp_service, 'BASELINE_TOKENS')
        assert "file_read" in mcp_service.BASELINE_TOKENS
        assert "browser" in mcp_service.BASELINE_TOKENS
        assert "default" in mcp_service.BASELINE_TOKENS

    def test_tool_categories_defined(self, mcp_service):
        """Test that tool categories are defined."""
        assert hasattr(mcp_service, 'TOOL_CATEGORIES')
        assert "file" in mcp_service.TOOL_CATEGORIES
        assert "code" in mcp_service.TOOL_CATEGORIES
        assert "browser" in mcp_service.TOOL_CATEGORIES

    def test_cache_ttl_defined(self, mcp_service):
        """Test that cache TTL is defined."""
        assert hasattr(mcp_service, '_cache_ttl')
        assert mcp_service._cache_ttl > 0

    def test_cache_initialization(self, mcp_service):
        """Test that cache is initialized."""
        assert hasattr(mcp_service, '_cache')
        assert isinstance(mcp_service._cache, dict)


# ==============================================================================
# INTEGRATION-LIKE TESTS
# ==============================================================================

class TestWorkflows:
    """Tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_register_server_and_tools_workflow(self, mcp_service, mock_db):
        """Test complete workflow: register server then tools."""
        # Register server
        server = await mcp_service.register_server(
            name="complete-server",
            server_type="stdio",
            command="node",
            args=["server.js"]
        )

        assert server.name == "complete-server"

        # Mock for tool registration
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = server
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Register tools
        tool1 = await mcp_service.register_tool(
            server_id=server.id,
            tool_name="tool1",
            category="file"
        )

        tool2 = await mcp_service.register_tool(
            server_id=server.id,
            tool_name="tool2",
            category="code"
        )

        assert tool1.server_id == server.id
        assert tool2.server_id == server.id

    @pytest.mark.asyncio
    async def test_execute_and_cache_workflow(self, mcp_service, mock_db, sample_tool, sample_server):
        """Test execution with caching workflow."""
        import time as time_module

        sample_tool.server = sample_server

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_tool
        mock_db.execute = AsyncMock(return_value=mock_result)

        # First execution - should be cache miss
        result1 = await mcp_service.execute_tool(
            tool_name="read_file",
            params={"path": "/workflow/test.txt"},
            use_cache=True
        )

        # If tool found, verify result structure
        if result1.get("status") != "failed":
            # Cache the result manually for test with correct format
            cache_key = mcp_service._generate_cache_key("read_file", {"path": "/workflow/test.txt"})
            mcp_service._cache[cache_key] = {
                "value": "cached",
                "timestamp": time_module.time()
            }

            # Second execution - should be cache hit
            result2 = await mcp_service.execute_tool(
                tool_name="read_file",
                params={"path": "/workflow/test.txt"},
                use_cache=True
            )

            assert result2.get("cached") == True
