"""
Week 71: MCP Proxy API

REST API for MCP server management, tool execution,
and token savings analytics.

Endpoints:
- Server management (CRUD, health)
- Tool registry (CRUD, search)
- Tool execution (with caching)
- Token savings analytics
"""

from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.mcp_proxy_service import MCPProxyService

router = APIRouter(prefix="/api/mcp", tags=["MCP Proxy (Week 71)"])


# ==============================================================================
# SCHEMAS
# ==============================================================================

class ServerCreate(BaseModel):
    """Create MCP server request."""
    name: str = Field(..., description="Unique server name")
    server_type: str = Field(..., description="Server type: stdio, http, docker")
    command: Optional[str] = Field(None, description="Command to start server (stdio)")
    args: Optional[List[str]] = Field(default_factory=list, description="Command arguments")
    env_vars: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")
    docker_image: Optional[str] = Field(None, description="Docker image (docker type)")
    docker_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Docker config")
    security_level: str = Field("standard", description="Security: standard, isolated, quarantine")
    priority: int = Field(100, description="Priority (lower = higher)")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional config")


class ServerResponse(BaseModel):
    """Server response."""
    id: str
    name: str
    server_type: str
    command: Optional[str]
    args: List[str]
    security_level: str
    is_active: bool
    health_status: str
    priority: int
    tool_count: int
    created_at: Optional[str]


class ToolCreate(BaseModel):
    """Create tool request."""
    server_id: str = Field(..., description="Server UUID")
    tool_name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema")
    category: Optional[str] = Field(None, description="Category: file, code, browser, etc.")
    tags: Optional[List[str]] = Field(default_factory=list, description="Search tags")


class ToolResponse(BaseModel):
    """Tool response."""
    id: str
    server_id: str
    server_name: Optional[str]
    tool_name: str
    description: Optional[str]
    category: Optional[str]
    tags: List[str]
    success_rate: Optional[float]
    avg_latency_ms: Optional[int]
    total_executions: int
    is_enabled: bool


class ExecuteToolRequest(BaseModel):
    """Execute tool request."""
    tool_name: str = Field(..., description="Tool to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    task_id: Optional[str] = Field(None, description="Task UUID")
    use_cache: bool = Field(True, description="Use cache")


class ExecuteToolResponse(BaseModel):
    """Execute tool response."""
    result: Optional[Any]
    status: str
    cached: bool
    tokens_saved: int
    latency_ms: int
    error: Optional[str] = None


class SavingsSummary(BaseModel):
    """Token savings summary."""
    period_days: int
    total_executions: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens_saved: int
    total_tokens_without_optimization: int
    savings_percentage: float
    cache_hits: int
    cache_hit_rate: float
    avg_latency_ms: int
    estimated_cost_saved_usd: float


# ==============================================================================
# SERVER ENDPOINTS
# ==============================================================================

@router.post("/servers", response_model=ServerResponse)
async def create_server(
    request: ServerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new MCP server."""
    service = MCPProxyService(db)

    # Check if name already exists
    existing = await service.get_server_by_name(request.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Server '{request.name}' already exists")

    server = await service.register_server(
        name=request.name,
        server_type=request.server_type,
        command=request.command,
        args=request.args,
        env_vars=request.env_vars,
        docker_image=request.docker_image,
        docker_config=request.docker_config,
        security_level=request.security_level,
        priority=request.priority,
        config=request.config
    )
    return server.to_dict()


@router.get("/servers", response_model=List[ServerResponse])
async def list_servers(
    active_only: bool = Query(True, description="Only active servers"),
    server_type: Optional[str] = Query(None, description="Filter by type"),
    db: AsyncSession = Depends(get_db)
):
    """List all registered MCP servers."""
    service = MCPProxyService(db)
    servers = await service.list_servers(active_only=active_only, server_type=server_type)
    return [s.to_dict() for s in servers]


@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get server details."""
    service = MCPProxyService(db)
    server = await service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server.to_dict()


@router.post("/servers/{server_id}/health")
async def check_server_health(
    server_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Check server health status."""
    service = MCPProxyService(db)
    result = await service.check_server_health(server_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Server not found")
    return result


@router.patch("/servers/{server_id}/activate")
async def activate_server(
    server_id: UUID,
    active: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Activate or deactivate a server."""
    service = MCPProxyService(db)
    server = await service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.is_active = active
    await db.commit()
    await db.refresh(server)
    return server.to_dict()


@router.get("/servers/{server_id}/failover")
async def get_failover_servers(
    server_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get ordered list of failover servers."""
    service = MCPProxyService(db)
    servers = await service.get_failover_servers(server_id)
    return [s.to_dict() for s in servers]


# ==============================================================================
# TOOL ENDPOINTS
# ==============================================================================

@router.post("/tools", response_model=ToolResponse)
async def create_tool(
    request: ToolCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new tool."""
    service = MCPProxyService(db)

    try:
        server_uuid = UUID(request.server_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid server_id format")

    # Verify server exists
    server = await service.get_server(server_uuid)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    tool = await service.register_tool(
        server_id=server_uuid,
        tool_name=request.tool_name,
        description=request.description,
        input_schema=request.input_schema,
        category=request.category,
        tags=request.tags
    )
    return tool.to_dict()


@router.get("/tools", response_model=List[ToolResponse])
async def list_tools(
    server_id: Optional[UUID] = Query(None, description="Filter by server"),
    category: Optional[str] = Query(None, description="Filter by category"),
    enabled_only: bool = Query(True, description="Only enabled tools"),
    db: AsyncSession = Depends(get_db)
):
    """List all registered tools."""
    service = MCPProxyService(db)
    tools = await service.list_tools(
        server_id=server_id,
        category=category,
        enabled_only=enabled_only
    )
    return [t.to_dict() for t in tools]


@router.get("/tools/search")
async def search_tools(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Max results"),
    db: AsyncSession = Depends(get_db)
):
    """Search tools by name or description."""
    service = MCPProxyService(db)
    tools = await service.search_tools(query=q, limit=limit)
    return [t.to_dict() for t in tools]


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get tool details."""
    service = MCPProxyService(db)
    tool = await service.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool.to_dict()


@router.patch("/tools/{tool_id}/enable")
async def enable_tool(
    tool_id: UUID,
    enabled: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Enable or disable a tool."""
    service = MCPProxyService(db)
    tool = await service.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool.is_enabled = enabled
    await db.commit()
    await db.refresh(tool)
    return tool.to_dict()


# ==============================================================================
# EXECUTION ENDPOINTS
# ==============================================================================

@router.post("/execute", response_model=ExecuteToolResponse)
async def execute_tool(
    request: ExecuteToolRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a tool with optional caching."""
    service = MCPProxyService(db)

    task_uuid = None
    if request.task_id:
        try:
            task_uuid = UUID(request.task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task_id format")

    result = await service.execute_tool(
        tool_name=request.tool_name,
        params=request.params,
        agent_id=request.agent_id,
        task_id=task_uuid,
        use_cache=request.use_cache
    )

    return ExecuteToolResponse(
        result=result.get("result"),
        status=result.get("status", "unknown"),
        cached=result.get("cached", False),
        tokens_saved=result.get("tokens_saved", 0),
        latency_ms=result.get("latency_ms", 0),
        error=result.get("error")
    )


@router.get("/execute/select-server")
async def select_best_server_for_tool(
    tool_name: str = Query(..., description="Tool name"),
    db: AsyncSession = Depends(get_db)
):
    """Select the best server for a given tool."""
    service = MCPProxyService(db)
    server = await service.select_best_server(tool_name)
    if not server:
        return {"selected": False, "reason": "No healthy server found for tool"}
    return {
        "selected": True,
        "server": server.to_dict()
    }


# ==============================================================================
# ANALYTICS ENDPOINTS
# ==============================================================================

@router.get("/analytics/savings", response_model=SavingsSummary)
async def get_savings_summary(
    days: int = Query(7, description="Number of days"),
    db: AsyncSession = Depends(get_db)
):
    """Get token savings summary."""
    service = MCPProxyService(db)
    return await service.calculate_savings_summary(days=days)


@router.get("/analytics/daily")
async def get_daily_savings(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    server_id: Optional[UUID] = Query(None),
    agent_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get daily token savings breakdown."""
    service = MCPProxyService(db)
    return await service.get_daily_savings(
        start_date=start_date,
        end_date=end_date,
        server_id=server_id,
        agent_id=agent_id
    )


@router.get("/analytics/tools")
async def get_tool_performance(
    limit: int = Query(20, description="Number of tools"),
    db: AsyncSession = Depends(get_db)
):
    """Get performance metrics for top tools."""
    service = MCPProxyService(db)
    return await service.get_tool_performance(limit=limit)


@router.get("/analytics/categories")
async def get_category_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get statistics grouped by tool category."""
    service = MCPProxyService(db)
    tools = await service.list_tools(enabled_only=False)

    # Group by category
    categories = {}
    for tool in tools:
        cat = tool.category or "other"
        if cat not in categories:
            categories[cat] = {
                "category": cat,
                "tool_count": 0,
                "total_executions": 0,
                "avg_success_rate": 0
            }
        categories[cat]["tool_count"] += 1
        categories[cat]["total_executions"] += tool.total_executions or 0
        if tool.success_rate:
            # Running average
            count = categories[cat]["tool_count"]
            old_avg = categories[cat]["avg_success_rate"]
            categories[cat]["avg_success_rate"] = (
                (old_avg * (count - 1) + tool.success_rate * 100) / count
            )

    return list(categories.values())


# ==============================================================================
# HEALTH & STATUS ENDPOINTS
# ==============================================================================

@router.get("/health")
async def mcp_proxy_health(
    db: AsyncSession = Depends(get_db)
):
    """Get MCP Proxy service health."""
    service = MCPProxyService(db)
    servers = await service.list_servers(active_only=True)
    tools = await service.list_tools(enabled_only=True)

    healthy_servers = sum(1 for s in servers if s.health_status == "healthy")

    return {
        "status": "healthy" if healthy_servers > 0 else "degraded",
        "total_servers": len(servers),
        "healthy_servers": healthy_servers,
        "total_tools": len(tools),
        "cache_size": len(service._cache)
    }


@router.get("/status")
async def mcp_proxy_status(
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive MCP Proxy status."""
    service = MCPProxyService(db)
    servers = await service.list_servers(active_only=False)
    tools = await service.list_tools(enabled_only=False)
    savings = await service.calculate_savings_summary(days=7)

    return {
        "servers": {
            "total": len(servers),
            "active": sum(1 for s in servers if s.is_active),
            "healthy": sum(1 for s in servers if s.health_status == "healthy"),
            "by_type": {
                "stdio": sum(1 for s in servers if s.server_type == "stdio"),
                "http": sum(1 for s in servers if s.server_type == "http"),
                "docker": sum(1 for s in servers if s.server_type == "docker")
            }
        },
        "tools": {
            "total": len(tools),
            "enabled": sum(1 for t in tools if t.is_enabled),
            "categories": list(set(t.category for t in tools if t.category))
        },
        "savings_7d": savings,
        "version": "1.0.0",
        "features": [
            "server_federation",
            "tool_registry",
            "caching",
            "failover",
            "analytics"
        ]
    }
