"""
Week 71: MCP Proxy API Tests

Tests for REST API endpoints: servers, tools, execution, analytics.
"""

import pytest
from datetime import date
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_mcp_service():
    """Create mock MCP Proxy service."""
    with patch('app.api.mcp_proxy.MCPProxyService') as MockService:
        service = MagicMock()
        MockService.return_value = service
        yield service


# ==============================================================================
# SERVER ENDPOINT TESTS
# ==============================================================================

class TestServerEndpoints:
    """Tests for MCP server management endpoints."""

    @pytest.mark.asyncio
    async def test_create_server(self, client: AsyncClient, mock_mcp_service):
        """Test POST /api/mcp/servers."""
        mock_server = MagicMock()
        mock_server.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "test-server",
            "server_type": "stdio",
            "command": "npx",
            "args": ["-y", "mcp-server"],
            "security_level": "standard",
            "is_active": True,
            "health_status": "unknown",
            "priority": 100,
            "tool_count": 0,
            "created_at": None
        }

        mock_mcp_service.get_server_by_name = AsyncMock(return_value=None)
        mock_mcp_service.register_server = AsyncMock(return_value=mock_server)

        response = await client.post(
            "/api/mcp/servers",
            json={
                "name": "test-server",
                "server_type": "stdio",
                "command": "npx",
                "args": ["-y", "mcp-server"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-server"
        assert data["server_type"] == "stdio"

    @pytest.mark.asyncio
    async def test_create_server_duplicate(self, client: AsyncClient, mock_mcp_service):
        """Test creating duplicate server returns 400."""
        existing_server = MagicMock()
        mock_mcp_service.get_server_by_name = AsyncMock(return_value=existing_server)

        response = await client.post(
            "/api/mcp/servers",
            json={
                "name": "existing-server",
                "server_type": "stdio",
                "command": "node"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_servers(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/servers."""
        mock_server = MagicMock()
        mock_server.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "server1",
            "server_type": "stdio",
            "command": "node",
            "args": [],
            "security_level": "standard",
            "is_active": True,
            "health_status": "healthy",
            "priority": 100,
            "tool_count": 5,
            "created_at": None
        }

        mock_mcp_service.list_servers = AsyncMock(return_value=[mock_server])

        response = await client.get("/api/mcp/servers")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "server1"

    @pytest.mark.asyncio
    async def test_list_servers_filtered(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/servers with filters."""
        mock_mcp_service.list_servers = AsyncMock(return_value=[])

        response = await client.get(
            "/api/mcp/servers",
            params={"active_only": True, "server_type": "docker"}
        )

        assert response.status_code == 200
        mock_mcp_service.list_servers.assert_called_once_with(
            active_only=True,
            server_type="docker"
        )

    @pytest.mark.asyncio
    async def test_get_server(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/servers/{server_id}."""
        server_id = uuid4()
        mock_server = MagicMock()
        mock_server.to_dict.return_value = {
            "id": str(server_id),
            "name": "my-server",
            "server_type": "stdio",
            "command": "node",
            "args": [],
            "security_level": "standard",
            "is_active": True,
            "health_status": "healthy",
            "priority": 100,
            "tool_count": 3,
            "created_at": None
        }

        mock_mcp_service.get_server = AsyncMock(return_value=mock_server)

        response = await client.get(f"/api/mcp/servers/{server_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(server_id)

    @pytest.mark.asyncio
    async def test_get_server_not_found(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/servers/{server_id} not found."""
        mock_mcp_service.get_server = AsyncMock(return_value=None)

        response = await client.get(f"/api/mcp/servers/{uuid4()}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_check_server_health(self, client: AsyncClient, mock_mcp_service):
        """Test POST /api/mcp/servers/{server_id}/health."""
        server_id = uuid4()
        mock_mcp_service.check_server_health = AsyncMock(return_value={
            "status": "healthy",
            "latency_ms": 50,
            "last_check": "2024-01-01T00:00:00"
        })

        response = await client.post(f"/api/mcp/servers/{server_id}/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_activate_server(self, client: AsyncClient, mock_mcp_service):
        """Test PATCH /api/mcp/servers/{server_id}/activate."""
        server_id = uuid4()
        mock_server = MagicMock()
        mock_server.is_active = True
        mock_server.to_dict.return_value = {
            "id": str(server_id),
            "name": "server",
            "server_type": "stdio",
            "command": "node",
            "args": [],
            "security_level": "standard",
            "is_active": True,
            "health_status": "healthy",
            "priority": 100,
            "tool_count": 0,
            "created_at": None
        }

        mock_mcp_service.get_server = AsyncMock(return_value=mock_server)

        response = await client.patch(
            f"/api/mcp/servers/{server_id}/activate",
            params={"active": True}
        )

        assert response.status_code == 200
        assert response.json()["is_active"] == True

    @pytest.mark.asyncio
    async def test_get_failover_servers(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/servers/{server_id}/failover."""
        server_id = uuid4()
        mock_backup = MagicMock()
        mock_backup.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "backup-server",
            "server_type": "stdio",
            "command": "node",
            "args": [],
            "security_level": "standard",
            "is_active": True,
            "health_status": "healthy",
            "priority": 200,
            "tool_count": 0,
            "created_at": None
        }

        mock_mcp_service.get_failover_servers = AsyncMock(return_value=[mock_backup])

        response = await client.get(f"/api/mcp/servers/{server_id}/failover")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ==============================================================================
# TOOL ENDPOINT TESTS
# ==============================================================================

class TestToolEndpoints:
    """Tests for MCP tool registry endpoints."""

    @pytest.mark.asyncio
    async def test_create_tool(self, client: AsyncClient, mock_mcp_service):
        """Test POST /api/mcp/tools."""
        server_id = uuid4()

        mock_server = MagicMock()
        mock_mcp_service.get_server = AsyncMock(return_value=mock_server)

        mock_tool = MagicMock()
        mock_tool.to_dict.return_value = {
            "id": str(uuid4()),
            "server_id": str(server_id),
            "server_name": "test-server",
            "tool_name": "read_file",
            "description": "Read file contents",
            "category": "file",
            "tags": ["file", "read"],
            "success_rate": 1.0,
            "avg_latency_ms": None,
            "total_executions": 0,
            "is_enabled": True
        }

        mock_mcp_service.register_tool = AsyncMock(return_value=mock_tool)

        response = await client.post(
            "/api/mcp/tools",
            json={
                "server_id": str(server_id),
                "tool_name": "read_file",
                "description": "Read file contents",
                "category": "file",
                "tags": ["file", "read"]
            }
        )

        assert response.status_code == 200
        assert response.json()["tool_name"] == "read_file"

    @pytest.mark.asyncio
    async def test_create_tool_invalid_server(self, client: AsyncClient, mock_mcp_service):
        """Test creating tool with invalid server ID."""
        response = await client.post(
            "/api/mcp/tools",
            json={
                "server_id": "invalid-uuid",
                "tool_name": "test"
            }
        )

        assert response.status_code == 400
        assert "Invalid server_id" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_tool_server_not_found(self, client: AsyncClient, mock_mcp_service):
        """Test creating tool for non-existent server."""
        mock_mcp_service.get_server = AsyncMock(return_value=None)

        response = await client.post(
            "/api/mcp/tools",
            json={
                "server_id": str(uuid4()),
                "tool_name": "test"
            }
        )

        assert response.status_code == 404
        assert "Server not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_tools(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/tools."""
        mock_tool = MagicMock()
        mock_tool.to_dict.return_value = {
            "id": str(uuid4()),
            "server_id": str(uuid4()),
            "server_name": "server1",
            "tool_name": "read_file",
            "description": "Read files",
            "category": "file",
            "tags": [],
            "success_rate": 0.95,
            "avg_latency_ms": 50,
            "total_executions": 100,
            "is_enabled": True
        }

        mock_mcp_service.list_tools = AsyncMock(return_value=[mock_tool])

        response = await client.get("/api/mcp/tools")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_search_tools(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/tools/search."""
        mock_tool = MagicMock()
        mock_tool.to_dict.return_value = {
            "id": str(uuid4()),
            "server_id": str(uuid4()),
            "server_name": "server1",
            "tool_name": "read_file",
            "description": "Read file contents",
            "category": "file",
            "tags": ["file"],
            "success_rate": 0.95,
            "avg_latency_ms": 50,
            "total_executions": 100,
            "is_enabled": True
        }

        mock_mcp_service.search_tools = AsyncMock(return_value=[mock_tool])

        response = await client.get(
            "/api/mcp/tools/search",
            params={"q": "read"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_tool(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/tools/{tool_id}."""
        tool_id = uuid4()
        mock_tool = MagicMock()
        mock_tool.to_dict.return_value = {
            "id": str(tool_id),
            "server_id": str(uuid4()),
            "server_name": "server1",
            "tool_name": "read_file",
            "description": "Read files",
            "category": "file",
            "tags": [],
            "success_rate": 0.95,
            "avg_latency_ms": 50,
            "total_executions": 100,
            "is_enabled": True
        }

        mock_mcp_service.get_tool = AsyncMock(return_value=mock_tool)

        response = await client.get(f"/api/mcp/tools/{tool_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(tool_id)

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/tools/{tool_id} not found."""
        mock_mcp_service.get_tool = AsyncMock(return_value=None)

        response = await client.get(f"/api/mcp/tools/{uuid4()}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_enable_tool(self, client: AsyncClient, mock_mcp_service):
        """Test PATCH /api/mcp/tools/{tool_id}/enable."""
        tool_id = uuid4()
        mock_tool = MagicMock()
        mock_tool.is_enabled = True
        mock_tool.to_dict.return_value = {
            "id": str(tool_id),
            "server_id": str(uuid4()),
            "server_name": "server1",
            "tool_name": "read_file",
            "description": "Read files",
            "category": "file",
            "tags": [],
            "success_rate": 0.95,
            "avg_latency_ms": 50,
            "total_executions": 100,
            "is_enabled": True
        }

        mock_mcp_service.get_tool = AsyncMock(return_value=mock_tool)

        response = await client.patch(
            f"/api/mcp/tools/{tool_id}/enable",
            params={"enabled": True}
        )

        assert response.status_code == 200


# ==============================================================================
# EXECUTION ENDPOINT TESTS
# ==============================================================================

class TestExecutionEndpoints:
    """Tests for tool execution endpoints."""

    @pytest.mark.asyncio
    async def test_execute_tool(self, client: AsyncClient, mock_mcp_service):
        """Test POST /api/mcp/execute."""
        mock_mcp_service.execute_tool = AsyncMock(return_value={
            "result": "file contents",
            "status": "success",
            "cached": False,
            "tokens_saved": 100,
            "latency_ms": 50
        })

        response = await client.post(
            "/api/mcp/execute",
            json={
                "tool_name": "read_file",
                "params": {"path": "/test.txt"},
                "use_cache": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["tokens_saved"] == 100

    @pytest.mark.asyncio
    async def test_execute_tool_with_task_id(self, client: AsyncClient, mock_mcp_service):
        """Test executing tool with task ID."""
        task_id = uuid4()
        mock_mcp_service.execute_tool = AsyncMock(return_value={
            "result": "ok",
            "status": "success",
            "cached": False,
            "tokens_saved": 50,
            "latency_ms": 30
        })

        response = await client.post(
            "/api/mcp/execute",
            json={
                "tool_name": "write_file",
                "params": {"path": "/test.txt", "content": "hello"},
                "task_id": str(task_id)
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_execute_tool_invalid_task_id(self, client: AsyncClient, mock_mcp_service):
        """Test executing tool with invalid task ID."""
        response = await client.post(
            "/api/mcp/execute",
            json={
                "tool_name": "test",
                "params": {},
                "task_id": "invalid-uuid"
            }
        )

        assert response.status_code == 400
        assert "Invalid task_id" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_execute_tool_cache_hit(self, client: AsyncClient, mock_mcp_service):
        """Test executing tool with cache hit."""
        mock_mcp_service.execute_tool = AsyncMock(return_value={
            "result": "cached result",
            "status": "success",
            "cached": True,
            "tokens_saved": 500,
            "latency_ms": 5
        })

        response = await client.post(
            "/api/mcp/execute",
            json={
                "tool_name": "read_file",
                "params": {"path": "/cached.txt"},
                "use_cache": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] == True
        assert data["tokens_saved"] == 500

    @pytest.mark.asyncio
    async def test_select_best_server(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/execute/select-server."""
        mock_server = MagicMock()
        mock_server.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "best-server",
            "server_type": "stdio",
            "command": "node",
            "args": [],
            "security_level": "standard",
            "is_active": True,
            "health_status": "healthy",
            "priority": 50,
            "tool_count": 10,
            "created_at": None
        }

        mock_mcp_service.select_best_server = AsyncMock(return_value=mock_server)

        response = await client.get(
            "/api/mcp/execute/select-server",
            params={"tool_name": "read_file"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == True
        assert data["server"]["name"] == "best-server"

    @pytest.mark.asyncio
    async def test_select_best_server_not_found(self, client: AsyncClient, mock_mcp_service):
        """Test selecting server when none available."""
        mock_mcp_service.select_best_server = AsyncMock(return_value=None)

        response = await client.get(
            "/api/mcp/execute/select-server",
            params={"tool_name": "nonexistent"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == False


# ==============================================================================
# ANALYTICS ENDPOINT TESTS
# ==============================================================================

class TestAnalyticsEndpoints:
    """Tests for token savings analytics endpoints."""

    @pytest.mark.asyncio
    async def test_get_savings_summary(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/analytics/savings."""
        mock_mcp_service.calculate_savings_summary = AsyncMock(return_value={
            "period_days": 7,
            "total_executions": 1000,
            "total_input_tokens": 50000,
            "total_output_tokens": 30000,
            "total_tokens_saved": 20000,
            "total_tokens_without_optimization": 100000,
            "savings_percentage": 20.0,
            "cache_hits": 300,
            "cache_hit_rate": 30.0,
            "avg_latency_ms": 50,
            "estimated_cost_saved_usd": 0.50
        })

        response = await client.get(
            "/api/mcp/analytics/savings",
            params={"days": 7}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7
        assert data["total_executions"] == 1000
        assert data["savings_percentage"] == 20.0

    @pytest.mark.asyncio
    async def test_get_daily_savings(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/analytics/daily."""
        mock_mcp_service.get_daily_savings = AsyncMock(return_value=[
            {
                "date": "2024-01-01",
                "total_executions": 100,
                "total_tokens_saved": 2000
            },
            {
                "date": "2024-01-02",
                "total_executions": 150,
                "total_tokens_saved": 3000
            }
        ])

        response = await client.get("/api/mcp/analytics/daily")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_daily_savings_filtered(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/analytics/daily with filters."""
        mock_mcp_service.get_daily_savings = AsyncMock(return_value=[])

        response = await client.get(
            "/api/mcp/analytics/daily",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "agent_id": "felix"
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_tool_performance(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/analytics/tools."""
        mock_mcp_service.get_tool_performance = AsyncMock(return_value=[
            {
                "tool_name": "read_file",
                "total_executions": 500,
                "success_rate": 0.98,
                "avg_latency_ms": 45
            }
        ])

        response = await client.get(
            "/api/mcp/analytics/tools",
            params={"limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_category_stats(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/analytics/categories."""
        mock_tool = MagicMock()
        mock_tool.category = "file"
        mock_tool.total_executions = 100
        mock_tool.success_rate = 0.95

        mock_mcp_service.list_tools = AsyncMock(return_value=[mock_tool])

        response = await client.get("/api/mcp/analytics/categories")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ==============================================================================
# HEALTH & STATUS ENDPOINT TESTS
# ==============================================================================

class TestHealthEndpoints:
    """Tests for health and status endpoints."""

    @pytest.mark.asyncio
    async def test_mcp_health(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/health."""
        mock_server = MagicMock()
        mock_server.health_status = "healthy"

        mock_mcp_service.list_servers = AsyncMock(return_value=[mock_server])
        mock_mcp_service.list_tools = AsyncMock(return_value=[])
        mock_mcp_service._cache = {}

        response = await client.get("/api/mcp/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "total_servers" in data
        assert "healthy_servers" in data

    @pytest.mark.asyncio
    async def test_mcp_status(self, client: AsyncClient, mock_mcp_service):
        """Test GET /api/mcp/status."""
        mock_server = MagicMock()
        mock_server.is_active = True
        mock_server.health_status = "healthy"
        mock_server.server_type = "stdio"

        mock_tool = MagicMock()
        mock_tool.is_enabled = True
        mock_tool.category = "file"

        mock_mcp_service.list_servers = AsyncMock(return_value=[mock_server])
        mock_mcp_service.list_tools = AsyncMock(return_value=[mock_tool])
        mock_mcp_service.calculate_savings_summary = AsyncMock(return_value={
            "period_days": 7,
            "total_executions": 100,
            "total_input_tokens": 5000,
            "total_output_tokens": 3000,
            "total_tokens_saved": 2000,
            "total_tokens_without_optimization": 10000,
            "savings_percentage": 20.0,
            "cache_hits": 30,
            "cache_hit_rate": 30.0,
            "avg_latency_ms": 50,
            "estimated_cost_saved_usd": 0.10
        })

        response = await client.get("/api/mcp/status")

        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "tools" in data
        assert "savings_7d" in data
        assert "version" in data
        assert "features" in data

    @pytest.mark.asyncio
    async def test_status_includes_features(self, client: AsyncClient, mock_mcp_service):
        """Test that status includes expected features."""
        mock_mcp_service.list_servers = AsyncMock(return_value=[])
        mock_mcp_service.list_tools = AsyncMock(return_value=[])
        mock_mcp_service.calculate_savings_summary = AsyncMock(return_value={
            "period_days": 7,
            "total_executions": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens_saved": 0,
            "total_tokens_without_optimization": 0,
            "savings_percentage": 0,
            "cache_hits": 0,
            "cache_hit_rate": 0,
            "avg_latency_ms": 0,
            "estimated_cost_saved_usd": 0
        })

        response = await client.get("/api/mcp/status")

        assert response.status_code == 200
        data = response.json()
        features = data.get("features", [])
        assert "server_federation" in features
        assert "tool_registry" in features
        assert "caching" in features
        assert "failover" in features
        assert "analytics" in features
