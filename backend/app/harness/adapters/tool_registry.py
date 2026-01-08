"""
MarQed Native Tool Registry

Permission-based tool access with:
- Agent-specific tool permissions
- Rate limiting per agent/tool
- Sandbox execution for unsafe operations
- OpenAI-compatible function schema generation
- Integration with ConstraintManager for action checks
"""

import uuid
import asyncio
import time
import logging
import importlib
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import functools

from app.harness.core.protocols import (
    ToolRegistryProtocol,
    ToolDefinition,
    ToolCallRequest,
    ToolCallResult,
    ToolCategory,
    BaseAdapter,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DEFAULT TOOL DEFINITIONS
# =============================================================================

DEFAULT_TOOLS: List[ToolDefinition] = [
    # File Operations
    ToolDefinition(
        name="file_read",
        category=ToolCategory.FILE_READ,
        description="Read contents of a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "encoding": {"type": "string", "default": "utf-8"},
            },
            "required": ["path"],
        },
        handler="app.harness.tools.file_ops.read_file",
        timeout_seconds=30,
    ),
    ToolDefinition(
        name="file_write",
        category=ToolCategory.FILE_WRITE,
        description="Write contents to a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
                "encoding": {"type": "string", "default": "utf-8"},
            },
            "required": ["path", "content"],
        },
        handler="app.harness.tools.file_ops.write_file",
        requires_approval=False,
        timeout_seconds=30,
    ),
    ToolDefinition(
        name="file_delete",
        category=ToolCategory.FILE_DELETE,
        description="Delete a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
            },
            "required": ["path"],
        },
        handler="app.harness.tools.file_ops.delete_file",
        requires_approval=True,
        timeout_seconds=10,
    ),
    # Code Operations
    ToolDefinition(
        name="code_generate",
        category=ToolCategory.CODE_GENERATE,
        description="Generate code based on specifications",
        parameters={
            "type": "object",
            "properties": {
                "language": {"type": "string", "description": "Programming language"},
                "specification": {"type": "string", "description": "What to generate"},
                "context": {"type": "object", "description": "Additional context"},
            },
            "required": ["language", "specification"],
        },
        handler="app.harness.tools.code_ops.generate_code",
        timeout_seconds=60,
    ),
    ToolDefinition(
        name="code_execute",
        category=ToolCategory.CODE_EXECUTE,
        description="Execute code in a sandboxed environment",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code to execute"},
                "language": {"type": "string", "enum": ["python", "javascript", "bash"]},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["code", "language"],
        },
        handler="app.harness.tools.code_ops.execute_code",
        sandbox_required=True,
        requires_approval=True,
        timeout_seconds=60,
    ),
    ToolDefinition(
        name="code_analyze",
        category=ToolCategory.CODE_GENERATE,
        description="Analyze code for issues, patterns, or metrics",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code to analyze"},
                "analysis_type": {"type": "string", "enum": ["security", "quality", "complexity"]},
            },
            "required": ["code", "analysis_type"],
        },
        handler="app.harness.tools.code_ops.analyze_code",
        timeout_seconds=30,
    ),
    # API Operations
    ToolDefinition(
        name="api_internal",
        category=ToolCategory.API_INTERNAL,
        description="Call internal MarQed API endpoints",
        parameters={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "API endpoint path"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                "data": {"type": "object", "description": "Request body"},
            },
            "required": ["endpoint", "method"],
        },
        handler="app.harness.tools.api_ops.call_internal_api",
        rate_limit=60,  # 60 calls per minute
        timeout_seconds=30,
    ),
    ToolDefinition(
        name="api_external",
        category=ToolCategory.API_EXTERNAL,
        description="Call external APIs",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL"},
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "headers": {"type": "object"},
                "data": {"type": "object"},
            },
            "required": ["url", "method"],
        },
        handler="app.harness.tools.api_ops.call_external_api",
        requires_approval=True,
        rate_limit=10,  # 10 calls per minute
        timeout_seconds=60,
    ),
    # Database Operations
    ToolDefinition(
        name="database_read",
        category=ToolCategory.DATABASE_READ,
        description="Execute read-only database queries",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query (SELECT only)"},
                "params": {"type": "array", "description": "Query parameters"},
            },
            "required": ["query"],
        },
        handler="app.harness.tools.db_ops.execute_read_query",
        rate_limit=30,
        timeout_seconds=30,
    ),
    ToolDefinition(
        name="database_write",
        category=ToolCategory.DATABASE_WRITE,
        description="Execute write database operations",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query"},
                "params": {"type": "array", "description": "Query parameters"},
            },
            "required": ["query"],
        },
        handler="app.harness.tools.db_ops.execute_write_query",
        requires_approval=True,
        rate_limit=10,
        timeout_seconds=30,
    ),
    # Security Operations
    ToolDefinition(
        name="security_scan",
        category=ToolCategory.SECURITY,
        description="Perform security analysis on code or configurations",
        parameters={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Code or config to scan"},
                "scan_type": {"type": "string", "enum": ["code", "dependencies", "secrets"]},
            },
            "required": ["target", "scan_type"],
        },
        handler="app.harness.tools.security_ops.security_scan",
        timeout_seconds=60,
    ),
    # System Operations
    ToolDefinition(
        name="system_info",
        category=ToolCategory.SYSTEM,
        description="Get system information",
        parameters={
            "type": "object",
            "properties": {
                "info_type": {"type": "string", "enum": ["memory", "cpu", "disk", "network"]},
            },
            "required": ["info_type"],
        },
        handler="app.harness.tools.system_ops.get_system_info",
        timeout_seconds=10,
    ),
]


# =============================================================================
# DEFAULT AGENT PERMISSIONS
# =============================================================================

DEFAULT_AGENT_PERMISSIONS: Dict[str, Dict[str, Any]] = {
    "felix": {  # Feature Architect
        "allowed": [
            "file_read", "file_write", "code_generate", "code_analyze",
            "api_internal", "database_read"
        ],
        "denied": ["file_delete", "code_execute", "database_write"],
        "requires_approval": ["api_external"],
        "rate_limits": {"api_internal": 30},
    },
    "marcus": {  # Maintenance Specialist
        "allowed": [
            "file_read", "file_write", "code_generate", "code_analyze",
            "api_internal", "database_read"
        ],
        "denied": ["code_execute", "api_external"],
        "requires_approval": ["file_delete", "database_write"],
        "rate_limits": {},
    },
    "quinn": {  # Quality Inspector
        "allowed": [
            "file_read", "code_analyze", "security_scan",
            "api_internal", "database_read"
        ],
        "denied": ["file_write", "file_delete", "code_execute", "database_write"],
        "requires_approval": [],
        "rate_limits": {},
    },
    "betty": {  # Bug Hunter
        "allowed": [
            "file_read", "file_write", "code_generate", "code_execute",
            "code_analyze", "api_internal", "database_read", "system_info"
        ],
        "denied": ["file_delete", "database_write", "api_external"],
        "requires_approval": [],
        "rate_limits": {"code_execute": 5},  # 5 per minute
    },
    "eliza": {  # Estimation Engine
        "allowed": [
            "file_read", "code_analyze", "api_internal", "database_read"
        ],
        "denied": ["file_write", "file_delete", "code_execute", "database_write"],
        "requires_approval": [],
        "rate_limits": {},
    },
    "diana": {  # Documentation Writer
        "allowed": [
            "file_read", "file_write", "code_generate", "api_internal"
        ],
        "denied": ["file_delete", "code_execute", "database_read", "database_write"],
        "requires_approval": [],
        "rate_limits": {},
    },
    "tessa": {  # Test Engineer
        "allowed": [
            "file_read", "file_write", "code_generate", "code_execute",
            "code_analyze", "api_internal", "database_read"
        ],
        "denied": ["file_delete", "database_write", "api_external"],
        "requires_approval": [],
        "rate_limits": {"code_execute": 10},
    },
    "miguel": {  # Migration Architect
        "allowed": [
            "file_read", "file_write", "code_generate", "code_analyze",
            "api_internal", "database_read", "database_write"
        ],
        "denied": ["code_execute", "api_external"],
        "requires_approval": ["file_delete"],
        "rate_limits": {"database_write": 10},
    },
    "peter": {  # Product Owner
        "allowed": [
            "file_read", "api_internal", "database_read"
        ],
        "denied": ["file_write", "file_delete", "code_execute", "database_write"],
        "requires_approval": [],
        "rate_limits": {},
    },
    "paul": {  # Project Lead
        "allowed": [
            "file_read", "file_write", "api_internal", "database_read", "system_info"
        ],
        "denied": ["code_execute", "database_write", "api_external"],
        "requires_approval": ["file_delete"],
        "rate_limits": {},
    },
}


# =============================================================================
# RATE LIMITER
# =============================================================================

@dataclass
class RateLimitEntry:
    """Track rate limit for an agent/tool combination."""
    calls: List[float] = field(default_factory=list)  # Timestamps
    limit: int = 60
    window_seconds: int = 60


class RateLimiter:
    """Sliding window rate limiter."""

    def __init__(self):
        self._entries: Dict[str, RateLimitEntry] = {}

    def _get_key(self, agent_id: str, tool_name: str) -> str:
        return f"{agent_id}:{tool_name}"

    def set_limit(self, agent_id: str, tool_name: str, limit: int, window_seconds: int = 60) -> None:
        """Set rate limit for an agent/tool combination."""
        key = self._get_key(agent_id, tool_name)
        self._entries[key] = RateLimitEntry(calls=[], limit=limit, window_seconds=window_seconds)

    def check(self, agent_id: str, tool_name: str) -> bool:
        """Check if a call is allowed under rate limits."""
        key = self._get_key(agent_id, tool_name)
        entry = self._entries.get(key)

        if not entry:
            return True  # No limit configured

        now = time.time()
        cutoff = now - entry.window_seconds

        # Clean old entries
        entry.calls = [t for t in entry.calls if t > cutoff]

        return len(entry.calls) < entry.limit

    def record(self, agent_id: str, tool_name: str) -> None:
        """Record a call for rate limiting."""
        key = self._get_key(agent_id, tool_name)
        entry = self._entries.get(key)

        if entry:
            entry.calls.append(time.time())

    def get_remaining(self, agent_id: str, tool_name: str) -> Optional[int]:
        """Get remaining calls in current window."""
        key = self._get_key(agent_id, tool_name)
        entry = self._entries.get(key)

        if not entry:
            return None

        now = time.time()
        cutoff = now - entry.window_seconds
        current_calls = len([t for t in entry.calls if t > cutoff])

        return max(0, entry.limit - current_calls)


# =============================================================================
# SANDBOX EXECUTOR
# =============================================================================

class SandboxExecutor:
    """
    Execute tools in a sandboxed environment.

    For now, implements basic timeout-based isolation.
    Future: Docker container isolation, resource limits.
    """

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def execute(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        timeout_seconds: int = 30
    ) -> Any:
        """Execute a function with timeout in a thread pool."""
        loop = asyncio.get_event_loop()

        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    functools.partial(func, *args, **kwargs)
                ),
                timeout=timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool execution timed out after {timeout_seconds}s")

    def shutdown(self):
        """Cleanup executor."""
        self._executor.shutdown(wait=False)


# =============================================================================
# MARQED TOOL REGISTRY
# =============================================================================

class MarQedToolRegistry(BaseAdapter, ToolRegistryProtocol):
    """
    MarQed native implementation of ToolRegistryProtocol.

    Features:
    - Permission-based tool access per agent
    - Rate limiting with sliding window
    - Sandbox execution for unsafe tools
    - OpenAI-compatible function schema generation
    - Audit logging of all tool calls

    Usage:
        registry = MarQedToolRegistry()

        # Check if agent can use tool
        can_use = await registry.can_use_tool("felix", "file_write")

        # Execute tool
        result = await registry.execute_tool(ToolCallRequest(
            tool_name="file_read",
            agent_id="felix",
            session_id="session-123",
            parameters={"path": "/tmp/test.txt"}
        ))

        # Get OpenAI-compatible schema for agent
        schema = registry.get_tool_schema("felix")
    """

    def __init__(
        self,
        use_default_tools: bool = True,
        use_default_permissions: bool = True,
        constraint_manager=None,  # Optional: for action validation
        **kwargs
    ):
        """
        Initialize tool registry.

        Args:
            use_default_tools: Load default tool definitions
            use_default_permissions: Load default agent permissions
            constraint_manager: Optional ConstraintManager for action validation
        """
        super().__init__(**kwargs)

        self._tools: Dict[str, ToolDefinition] = {}
        self._permissions: Dict[str, Dict[str, Any]] = {}
        self._rate_limiter = RateLimiter()
        self._sandbox = SandboxExecutor()
        self._constraint_manager = constraint_manager
        self._audit_log: List[Dict[str, Any]] = []

        if use_default_tools:
            self._load_default_tools()

        if use_default_permissions:
            self._load_default_permissions()

        self._initialized = True
        logger.info(f"MarQedToolRegistry initialized with {len(self._tools)} tools")

    def _load_default_tools(self) -> None:
        """Load default tool definitions."""
        for tool in DEFAULT_TOOLS:
            self._tools[tool.name] = tool

    def _load_default_permissions(self) -> None:
        """Load default agent permissions."""
        for agent_id, perms in DEFAULT_AGENT_PERMISSIONS.items():
            self._permissions[agent_id] = perms

            # Set up rate limits
            for tool_name, limit in perms.get("rate_limits", {}).items():
                self._rate_limiter.set_limit(agent_id, tool_name, limit)

            # Set default rate limits from tool definitions
            for tool_name in perms.get("allowed", []):
                tool = self._tools.get(tool_name)
                if tool and tool.rate_limit and tool_name not in perms.get("rate_limits", {}):
                    self._rate_limiter.set_limit(agent_id, tool_name, tool.rate_limit)

    def register_tool(self, tool: ToolDefinition) -> bool:
        """Register a new tool in the registry."""
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")

        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        return True

    def unregister_tool(self, tool_name: str) -> bool:
        """Remove a tool from the registry."""
        if tool_name not in self._tools:
            return False

        del self._tools[tool_name]
        logger.info(f"Unregistered tool: {tool_name}")
        return True

    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self._tools.get(tool_name)

    def get_tools_for_agent(self, agent_id: str) -> List[ToolDefinition]:
        """Get all tools available to an agent."""
        perms = self._permissions.get(agent_id, {})
        allowed = set(perms.get("allowed", []))
        denied = set(perms.get("denied", []))

        # If no permissions defined, allow all tools
        if not allowed and not denied:
            return list(self._tools.values())

        # Return allowed tools that aren't denied
        result = []
        for tool_name, tool in self._tools.items():
            if tool_name in allowed and tool_name not in denied:
                if tool.enabled:
                    result.append(tool)

        return result

    async def can_use_tool(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if an agent can use a specific tool."""
        tool = self._tools.get(tool_name)
        if not tool:
            return False

        if not tool.enabled:
            return False

        perms = self._permissions.get(agent_id, {})
        allowed = set(perms.get("allowed", []))
        denied = set(perms.get("denied", []))

        # Check explicit deny
        if tool_name in denied:
            return False

        # Check explicit allow (if permissions configured)
        if allowed and tool_name not in allowed:
            return False

        # Check rate limit
        if not self._rate_limiter.check(agent_id, tool_name):
            return False

        # Check constraint manager if available
        if self._constraint_manager:
            result = await self._constraint_manager.check_action(
                agent_id=agent_id,
                action_type=tool.category.value,
                action_params=parameters or {},
            )
            if not result.allowed:
                return False

        return True

    def _requires_approval(self, agent_id: str, tool_name: str) -> bool:
        """Check if tool requires approval for agent."""
        tool = self._tools.get(tool_name)
        if tool and tool.requires_approval:
            return True

        perms = self._permissions.get(agent_id, {})
        approval_list = perms.get("requires_approval", [])
        return tool_name in approval_list

    async def execute_tool(self, request: ToolCallRequest) -> ToolCallResult:
        """Execute a tool with full permission pipeline."""
        start_time = time.time()
        request_id = request.request_id or str(uuid.uuid4())[:8]

        tool = self._tools.get(request.tool_name)
        if not tool:
            return ToolCallResult(
                success=False,
                result=None,
                error=f"Tool '{request.tool_name}' not found",
                audit_id=request_id,
            )

        # 1. Check permissions
        can_use = await self.can_use_tool(
            request.agent_id,
            request.tool_name,
            request.parameters
        )
        if not can_use:
            self._log_audit(request_id, request, "DENIED", "Permission denied")
            return ToolCallResult(
                success=False,
                result=None,
                error="Permission denied",
                audit_id=request_id,
            )

        # 2. Check approval requirement
        if self._requires_approval(request.agent_id, request.tool_name):
            self._log_audit(request_id, request, "APPROVAL_REQUIRED", "Requires approval")
            return ToolCallResult(
                success=False,
                result=None,
                error="Tool requires approval before execution",
                audit_id=request_id,
            )

        # 3. Record rate limit
        self._rate_limiter.record(request.agent_id, request.tool_name)

        # 4. Execute tool
        try:
            handler = self._resolve_handler(tool.handler)
            if handler is None:
                # Return mock result if handler not implemented
                result = await self._execute_mock_handler(tool, request.parameters)
            elif tool.sandbox_required:
                result = await self._sandbox.execute(
                    handler,
                    (),
                    request.parameters,
                    timeout_seconds=tool.timeout_seconds,
                )
            else:
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(
                        handler(**request.parameters),
                        timeout=tool.timeout_seconds
                    )
                else:
                    result = handler(**request.parameters)

            execution_time = int((time.time() - start_time) * 1000)

            self._log_audit(request_id, request, "SUCCESS", None)

            return ToolCallResult(
                success=True,
                result=result,
                execution_time_ms=execution_time,
                audit_id=request_id,
                sandbox_used=tool.sandbox_required,
            )

        except TimeoutError as e:
            self._log_audit(request_id, request, "TIMEOUT", str(e))
            return ToolCallResult(
                success=False,
                result=None,
                error=f"Tool execution timed out: {e}",
                audit_id=request_id,
            )
        except Exception as e:
            logger.exception(f"Tool execution error: {e}")
            self._log_audit(request_id, request, "ERROR", str(e))
            return ToolCallResult(
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
                audit_id=request_id,
            )

    def _resolve_handler(self, handler_path: str) -> Optional[Callable]:
        """Resolve handler module path to callable."""
        try:
            module_path, func_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        except (ImportError, AttributeError, ValueError):
            logger.debug(f"Handler not found: {handler_path}")
            return None

    async def _execute_mock_handler(
        self,
        tool: ToolDefinition,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mock handler for testing/development."""
        return {
            "mock": True,
            "tool": tool.name,
            "parameters": parameters,
            "message": f"Mock execution of {tool.name}",
        }

    def get_tool_schema(self, agent_id: str) -> Dict[str, Any]:
        """Generate OpenAI-compatible function schema for agent."""
        tools = self.get_tools_for_agent(agent_id)

        functions = []
        for tool in tools:
            functions.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            })

        return {"tools": functions}

    def set_agent_permissions(
        self,
        agent_id: str,
        allowed: List[str],
        denied: List[str],
        requires_approval: Optional[List[str]] = None
    ) -> None:
        """Configure tool permissions for an agent."""
        self._permissions[agent_id] = {
            "allowed": allowed,
            "denied": denied,
            "requires_approval": requires_approval or [],
            "rate_limits": {},
        }
        logger.info(f"Updated permissions for agent {agent_id}")

    def set_rate_limit(
        self,
        agent_id: str,
        tool_name: str,
        limit: int,
        window_seconds: int = 60
    ) -> None:
        """Set rate limit for specific agent/tool."""
        self._rate_limiter.set_limit(agent_id, tool_name, limit, window_seconds)

        # Also store in permissions
        if agent_id in self._permissions:
            if "rate_limits" not in self._permissions[agent_id]:
                self._permissions[agent_id]["rate_limits"] = {}
            self._permissions[agent_id]["rate_limits"][tool_name] = limit

    def get_rate_limit_remaining(self, agent_id: str, tool_name: str) -> Optional[int]:
        """Get remaining rate limit for agent/tool."""
        return self._rate_limiter.get_remaining(agent_id, tool_name)

    def _log_audit(
        self,
        audit_id: str,
        request: ToolCallRequest,
        status: str,
        error: Optional[str]
    ) -> None:
        """Log tool execution for audit."""
        self._audit_log.append({
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": request.agent_id,
            "session_id": request.session_id,
            "tool_name": request.tool_name,
            "parameters": request.parameters,
            "status": status,
            "error": error,
        })

        # Keep last 1000 entries
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit log, optionally filtered."""
        log = self._audit_log

        if agent_id:
            log = [e for e in log if e["agent_id"] == agent_id]

        if tool_name:
            log = [e for e in log if e["tool_name"] == tool_name]

        return log[-limit:]

    def health_check(self) -> bool:
        """Check if the tool registry is operational."""
        return self._initialized

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tool registry."""
        return {
            "total_tools": len(self._tools),
            "enabled_tools": len([t for t in self._tools.values() if t.enabled]),
            "agents_configured": len(self._permissions),
            "audit_log_size": len(self._audit_log),
            "initialized": self._initialized,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with summary."""
        return [
            {
                "name": tool.name,
                "category": tool.category.value,
                "description": tool.description,
                "requires_approval": tool.requires_approval,
                "sandbox_required": tool.sandbox_required,
                "rate_limit": tool.rate_limit,
                "enabled": tool.enabled,
            }
            for tool in self._tools.values()
        ]

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._sandbox.shutdown()
        super().cleanup()
