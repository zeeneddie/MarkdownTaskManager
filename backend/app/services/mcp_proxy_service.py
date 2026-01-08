"""
Week 71: MCP Proxy Service

Token optimization via intelligent MCP tool management:
- Server federation and health monitoring
- Tool registry with semantic search
- Caching and token savings tracking
- Security isolation levels
- Automatic failover

Target: 99% token reduction via intelligent tool selection.
"""

import asyncio
import hashlib
import json
import subprocess
import time
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_proxy import MCPServer, MCPToolRegistry, MCPToolExecution, MCPTokenSavings


class MCPProxyService:
    """
    MCP Proxy Service for token optimization.

    Features:
    - Server management (stdio, http, docker)
    - Tool discovery and registry
    - Intelligent caching with hash keys
    - Token usage tracking and savings calculation
    - Health monitoring and failover
    - Security isolation levels
    """

    # Estimated tokens per typical MCP operation (without optimization)
    BASELINE_TOKENS = {
        "file_read": 500,
        "file_write": 200,
        "search": 1000,
        "browser": 2000,
        "code_analysis": 1500,
        "default": 300
    }

    # Tool categories for semantic grouping
    TOOL_CATEGORIES = {
        "file": ["read", "write", "list", "search", "glob", "grep"],
        "code": ["analyze", "parse", "refactor", "lint", "format"],
        "browser": ["navigate", "click", "screenshot", "scrape"],
        "search": ["web", "semantic", "vector", "fts"],
        "system": ["bash", "exec", "env", "process"]
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: Dict[str, Dict[str, Any]] = {}  # In-memory cache
        self._cache_ttl = 300  # 5 minutes TTL

    # ========================================================================
    # SERVER MANAGEMENT
    # ========================================================================

    async def register_server(
        self,
        name: str,
        server_type: str,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        docker_image: Optional[str] = None,
        docker_config: Optional[Dict[str, Any]] = None,
        security_level: str = "standard",
        priority: int = 100,
        config: Optional[Dict[str, Any]] = None
    ) -> MCPServer:
        """Register a new MCP server."""
        server = MCPServer(
            name=name,
            server_type=server_type,
            command=command,
            args=args or [],
            env_vars=env_vars or {},
            docker_image=docker_image,
            docker_config=docker_config or {},
            security_level=security_level,
            priority=priority,
            config=config or {},
            is_active=True,
            health_status="unknown"
        )
        self.db.add(server)
        await self.db.commit()
        await self.db.refresh(server)
        return server

    async def get_server(self, server_id: UUID) -> Optional[MCPServer]:
        """Get server by ID."""
        result = await self.db.execute(
            select(MCPServer).where(MCPServer.id == server_id)
        )
        return result.scalar_one_or_none()

    async def get_server_by_name(self, name: str) -> Optional[MCPServer]:
        """Get server by name."""
        result = await self.db.execute(
            select(MCPServer).where(MCPServer.name == name)
        )
        return result.scalar_one_or_none()

    async def list_servers(
        self,
        active_only: bool = True,
        server_type: Optional[str] = None
    ) -> List[MCPServer]:
        """List all registered MCP servers."""
        query = select(MCPServer).order_by(MCPServer.priority)

        if active_only:
            query = query.where(MCPServer.is_active == True)
        if server_type:
            query = query.where(MCPServer.server_type == server_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_server_health(
        self,
        server_id: UUID,
        status: str
    ) -> Optional[MCPServer]:
        """Update server health status."""
        server = await self.get_server(server_id)
        if server:
            server.health_status = status
            server.last_health_check = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(server)
        return server

    async def check_server_health(self, server_id: UUID) -> Dict[str, Any]:
        """Check if a server is healthy and responsive."""
        server = await self.get_server(server_id)
        if not server:
            return {"status": "not_found", "healthy": False}

        try:
            if server.server_type == "stdio":
                # For stdio servers, try to ping the process
                healthy = await self._check_stdio_health(server)
            elif server.server_type == "http":
                # For HTTP servers, try health endpoint
                healthy = await self._check_http_health(server)
            elif server.server_type == "docker":
                # For Docker servers, check container status
                healthy = await self._check_docker_health(server)
            else:
                healthy = False

            status = "healthy" if healthy else "unhealthy"
            await self.update_server_health(server_id, status)

            return {
                "status": status,
                "healthy": healthy,
                "server_name": server.name,
                "server_type": server.server_type,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            await self.update_server_health(server_id, "unhealthy")
            return {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }

    async def _check_stdio_health(self, server: MCPServer) -> bool:
        """Check stdio server health by verifying process exists."""
        if not server.command:
            return False
        # Simple check - verify command exists
        try:
            result = subprocess.run(
                ["which", server.command.split()[0]],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _check_http_health(self, server: MCPServer) -> bool:
        """Check HTTP server health via health endpoint."""
        # Placeholder - would use aiohttp in real implementation
        return True

    async def _check_docker_health(self, server: MCPServer) -> bool:
        """Check Docker container health."""
        if not server.docker_image:
            return False
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"ancestor={server.docker_image}", "-q"],
                capture_output=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    # ========================================================================
    # TOOL REGISTRY
    # ========================================================================

    async def register_tool(
        self,
        server_id: UUID,
        tool_name: str,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> MCPToolRegistry:
        """Register a tool from an MCP server."""
        # Auto-detect category if not provided
        if not category:
            category = self._detect_tool_category(tool_name)

        tool = MCPToolRegistry(
            server_id=server_id,
            tool_name=tool_name,
            description=description,
            input_schema=input_schema,
            category=category,
            tags=tags or [],
            is_enabled=True
        )
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        return tool

    def _detect_tool_category(self, tool_name: str) -> str:
        """Auto-detect tool category from name."""
        tool_lower = tool_name.lower()
        for category, keywords in self.TOOL_CATEGORIES.items():
            if any(kw in tool_lower for kw in keywords):
                return category
        return "other"

    async def get_tool(self, tool_id: UUID) -> Optional[MCPToolRegistry]:
        """Get tool by ID."""
        result = await self.db.execute(
            select(MCPToolRegistry).where(MCPToolRegistry.id == tool_id)
        )
        return result.scalar_one_or_none()

    async def find_tool(
        self,
        tool_name: str,
        server_name: Optional[str] = None
    ) -> Optional[MCPToolRegistry]:
        """Find a tool by name, optionally filtered by server."""
        query = select(MCPToolRegistry).where(MCPToolRegistry.tool_name == tool_name)

        if server_name:
            query = query.join(MCPServer).where(MCPServer.name == server_name)

        query = query.order_by(MCPToolRegistry.success_rate.desc())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_tools(
        self,
        server_id: Optional[UUID] = None,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[MCPToolRegistry]:
        """List all registered tools."""
        query = select(MCPToolRegistry)

        if server_id:
            query = query.where(MCPToolRegistry.server_id == server_id)
        if category:
            query = query.where(MCPToolRegistry.category == category)
        if enabled_only:
            query = query.where(MCPToolRegistry.is_enabled == True)

        query = query.order_by(MCPToolRegistry.success_rate.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_tools(
        self,
        query: str,
        limit: int = 10
    ) -> List[MCPToolRegistry]:
        """Search tools by name or description (semantic search placeholder)."""
        # Simple text search - in production would use vector similarity
        search_query = select(MCPToolRegistry).where(
            MCPToolRegistry.is_enabled == True
        ).where(
            MCPToolRegistry.tool_name.ilike(f"%{query}%") |
            MCPToolRegistry.description.ilike(f"%{query}%")
        ).order_by(MCPToolRegistry.success_rate.desc()).limit(limit)

        result = await self.db.execute(search_query)
        return list(result.scalars().all())

    # ========================================================================
    # TOOL EXECUTION WITH CACHING
    # ========================================================================

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        agent_id: Optional[str] = None,
        task_id: Optional[UUID] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool with intelligent caching.

        Returns dict with:
        - result: The tool output
        - cached: Whether result was from cache
        - tokens_saved: Estimated tokens saved
        - latency_ms: Execution time
        """
        start_time = time.time()

        # Find the tool
        tool = await self.find_tool(tool_name)
        if not tool:
            return {
                "error": f"Tool '{tool_name}' not found",
                "status": "failed",
                "cached": False,
                "tokens_saved": 0
            }

        # Generate cache key
        cache_key = self._generate_cache_key(tool_name, params)

        # Check cache
        if use_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                await self._record_execution(
                    tool=tool,
                    params=params,
                    result=cached_result,
                    agent_id=agent_id,
                    task_id=task_id,
                    was_cached=True,
                    cache_key=cache_key,
                    latency_ms=int((time.time() - start_time) * 1000)
                )
                return {
                    "result": cached_result,
                    "status": "success",
                    "cached": True,
                    "tokens_saved": self._estimate_baseline_tokens(tool.category),
                    "latency_ms": int((time.time() - start_time) * 1000)
                }

        # Execute tool (placeholder - would call actual MCP server)
        try:
            result = await self._execute_mcp_tool(tool, params)
            latency_ms = int((time.time() - start_time) * 1000)

            # Cache result
            if use_cache:
                self._set_cache(cache_key, result)

            # Record execution
            await self._record_execution(
                tool=tool,
                params=params,
                result=result,
                agent_id=agent_id,
                task_id=task_id,
                was_cached=False,
                cache_key=cache_key,
                latency_ms=latency_ms,
                status="success"
            )

            return {
                "result": result,
                "status": "success",
                "cached": False,
                "tokens_saved": 0,
                "latency_ms": latency_ms
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            await self._record_execution(
                tool=tool,
                params=params,
                result=None,
                agent_id=agent_id,
                task_id=task_id,
                was_cached=False,
                cache_key=cache_key,
                latency_ms=latency_ms,
                status="failed",
                error=str(e)
            )
            return {
                "error": str(e),
                "status": "failed",
                "cached": False,
                "tokens_saved": 0,
                "latency_ms": latency_ms
            }

    async def _execute_mcp_tool(
        self,
        tool: MCPToolRegistry,
        params: Dict[str, Any]
    ) -> Any:
        """Execute tool via MCP protocol (placeholder)."""
        # In production, this would:
        # 1. Find the server
        # 2. Send MCP request
        # 3. Wait for response
        # For now, return mock response
        return {
            "tool": tool.tool_name,
            "params": params,
            "mock_result": "Tool execution result",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _generate_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate deterministic cache key from tool and params."""
        content = json.dumps({"tool": tool_name, "params": params}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:64]

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self._cache_ttl:
                return entry["value"]
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """Set cache value with timestamp."""
        self._cache[key] = {
            "value": value,
            "timestamp": time.time()
        }

    def _estimate_baseline_tokens(self, category: Optional[str]) -> int:
        """Estimate baseline tokens for a tool category."""
        return self.BASELINE_TOKENS.get(category, self.BASELINE_TOKENS["default"])

    async def _record_execution(
        self,
        tool: MCPToolRegistry,
        params: Dict[str, Any],
        result: Any,
        agent_id: Optional[str],
        task_id: Optional[UUID],
        was_cached: bool,
        cache_key: str,
        latency_ms: int,
        status: str = "success",
        error: Optional[str] = None
    ):
        """Record tool execution for analytics."""
        baseline_tokens = self._estimate_baseline_tokens(tool.category)
        input_tokens = len(json.dumps(params)) // 4  # Rough estimate
        output_tokens = len(json.dumps(result)) // 4 if result else 0
        tokens_saved = baseline_tokens if was_cached else 0

        execution = MCPToolExecution(
            tool_id=tool.id,
            server_id=tool.server_id,
            agent_id=agent_id,
            task_id=task_id,
            input_params=params,
            output_result=result,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens_saved=tokens_saved,
            latency_ms=latency_ms,
            status=status,
            error_message=error,
            was_cached=was_cached,
            cache_key=cache_key
        )
        self.db.add(execution)

        # Update tool statistics
        tool.total_executions = (tool.total_executions or 0) + 1
        if status == "success":
            # Update success rate (moving average)
            old_rate = tool.success_rate or 1.0
            tool.success_rate = (old_rate * (tool.total_executions - 1) + 1.0) / tool.total_executions
            # Update average latency
            old_latency = tool.avg_latency_ms or latency_ms
            tool.avg_latency_ms = int((old_latency * (tool.total_executions - 1) + latency_ms) / tool.total_executions)
        else:
            old_rate = tool.success_rate or 1.0
            tool.success_rate = (old_rate * (tool.total_executions - 1)) / tool.total_executions

        await self.db.commit()

    # ========================================================================
    # TOKEN SAVINGS ANALYTICS
    # ========================================================================

    async def get_daily_savings(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        server_id: Optional[UUID] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get daily token savings statistics."""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        query = select(MCPTokenSavings).where(
            and_(
                MCPTokenSavings.date >= start_date,
                MCPTokenSavings.date <= end_date
            )
        )

        if server_id:
            query = query.where(MCPTokenSavings.server_id == server_id)
        if agent_id:
            query = query.where(MCPTokenSavings.agent_id == agent_id)

        query = query.order_by(MCPTokenSavings.date.desc())
        result = await self.db.execute(query)

        return [s.to_dict() for s in result.scalars().all()]

    async def calculate_savings_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Calculate overall token savings summary."""
        start_date = date.today() - timedelta(days=days)

        # Aggregate from executions
        result = await self.db.execute(
            select(
                func.count(MCPToolExecution.id).label("total_executions"),
                func.sum(MCPToolExecution.input_tokens).label("total_input"),
                func.sum(MCPToolExecution.output_tokens).label("total_output"),
                func.sum(MCPToolExecution.tokens_saved).label("total_saved"),
                func.sum(
                    func.cast(MCPToolExecution.was_cached, Integer)
                ).label("cache_hits"),
                func.avg(MCPToolExecution.latency_ms).label("avg_latency")
            ).where(
                MCPToolExecution.created_at >= datetime.combine(start_date, datetime.min.time())
            )
        )
        row = result.one()

        total_input = row.total_input or 0
        total_output = row.total_output or 0
        total_saved = row.total_saved or 0
        total_without_savings = total_input + total_output + total_saved

        return {
            "period_days": days,
            "total_executions": row.total_executions or 0,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens_saved": total_saved,
            "total_tokens_without_optimization": total_without_savings,
            "savings_percentage": round(
                (total_saved / total_without_savings) * 100, 2
            ) if total_without_savings > 0 else 0,
            "cache_hits": row.cache_hits or 0,
            "cache_hit_rate": round(
                (row.cache_hits or 0) / (row.total_executions or 1) * 100, 2
            ),
            "avg_latency_ms": int(row.avg_latency or 0),
            "estimated_cost_saved_usd": round(total_saved * 0.00001, 4)  # Rough estimate
        }

    async def get_tool_performance(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get performance metrics for top tools."""
        result = await self.db.execute(
            select(MCPToolRegistry)
            .where(MCPToolRegistry.total_executions > 0)
            .order_by(MCPToolRegistry.total_executions.desc())
            .limit(limit)
        )

        tools = result.scalars().all()
        return [
            {
                "tool_name": t.tool_name,
                "server_name": t.server.name if t.server else None,
                "category": t.category,
                "total_executions": t.total_executions,
                "success_rate": round(t.success_rate * 100, 2) if t.success_rate else 0,
                "avg_latency_ms": t.avg_latency_ms
            }
            for t in tools
        ]

    # ========================================================================
    # FAILOVER AND SERVER SELECTION
    # ========================================================================

    async def select_best_server(
        self,
        tool_name: str
    ) -> Optional[MCPServer]:
        """
        Select the best server for a tool based on:
        1. Health status
        2. Success rate
        3. Priority
        4. Latency
        """
        # Find all servers that have this tool
        result = await self.db.execute(
            select(MCPToolRegistry)
            .where(MCPToolRegistry.tool_name == tool_name)
            .where(MCPToolRegistry.is_enabled == True)
            .join(MCPServer)
            .where(MCPServer.is_active == True)
            .where(MCPServer.health_status == "healthy")
            .order_by(
                MCPServer.priority.asc(),
                MCPToolRegistry.success_rate.desc()
            )
        )

        tool = result.scalar_one_or_none()
        return tool.server if tool else None

    async def get_failover_servers(
        self,
        primary_server_id: UUID
    ) -> List[MCPServer]:
        """Get ordered list of failover servers."""
        primary = await self.get_server(primary_server_id)
        if not primary:
            return []

        # Get all active healthy servers except primary
        result = await self.db.execute(
            select(MCPServer)
            .where(MCPServer.id != primary_server_id)
            .where(MCPServer.is_active == True)
            .where(MCPServer.health_status.in_(["healthy", "unknown"]))
            .order_by(MCPServer.priority.asc())
        )

        return list(result.scalars().all())
