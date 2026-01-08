"""
Harness Framework API Endpoints

Week 91: Agent Harness Framework
REST API for constraint checking, context management, and harness status.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.database import get_db
from app.harness import registry, ModuleType
from app.harness.core.protocols import ConstraintSeverity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/harness", tags=["harness"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class ActionCheckRequest(BaseModel):
    """Request to check if an action is allowed."""
    agent_id: str = Field(..., description="Agent attempting the action")
    action_type: str = Field(..., description="Type of action (e.g., file_write)")
    action_params: Dict[str, Any] = Field(default={}, description="Action parameters")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ActionCheckResponse(BaseModel):
    """Response from action check."""
    allowed: bool
    severity: str
    reason: Optional[str]
    requires_approval: bool
    audit_id: Optional[str]
    matched_rules: List[str]


class OutputValidationRequest(BaseModel):
    """Request to validate agent output."""
    agent_id: str
    output: str
    output_type: str = Field(..., description="Type: code, sql, text, markdown")


class ConstraintAddRequest(BaseModel):
    """Request to add a runtime constraint."""
    agent_id: str
    action_type: str
    denied: bool = True
    reason: Optional[str] = None


class SetSystemContextRequest(BaseModel):
    """Request to set agent system context."""
    agent_id: str
    role: str
    capabilities: List[str] = []
    rules: List[str] = []
    ethics: List[str] = []
    llm_model: Optional[str] = None


class SetTaskContextRequest(BaseModel):
    """Request to set task context for a session."""
    session_id: str
    context: Dict[str, Any]
    ttl_seconds: Optional[int] = None


class AddMemoryRequest(BaseModel):
    """Request to add memory to a session."""
    session_id: str
    observation: str
    tags: Optional[List[str]] = None
    priority: int = 5


class ResolveContextRequest(BaseModel):
    """Request to resolve context for an agent."""
    agent_id: str
    session_id: str
    token_budget: int = 4000


class ResolvedContextResponse(BaseModel):
    """Resolved context response."""
    system: str
    task: str
    memory: str
    total_tokens: int
    layers_used: List[str]
    truncated: bool
    context_hash: str


class HarnessStatusResponse(BaseModel):
    """Overall harness status."""
    constraints_mounted: bool
    context_mounted: bool
    tools_mounted: bool
    versioning_mounted: bool
    health: Dict[str, Optional[bool]]
    adapters_registered: int


# =============================================================================
# STATUS ENDPOINTS
# =============================================================================

@router.get("/status", response_model=HarnessStatusResponse)
async def get_harness_status():
    """Get overall status of the harness framework."""
    status = registry.get_status()
    health = registry.health_check()

    return HarnessStatusResponse(
        constraints_mounted=registry.is_mounted(ModuleType.CONSTRAINTS),
        context_mounted=registry.is_mounted(ModuleType.CONTEXT),
        tools_mounted=registry.is_mounted(ModuleType.TOOLS),
        versioning_mounted=registry.is_mounted(ModuleType.VERSIONING),
        health=health,
        adapters_registered=status["registered_adapters"],
    )


@router.get("/adapters")
async def list_adapters(
    module_type: Optional[str] = Query(None, description="Filter by module type")
):
    """List all registered adapters."""
    mt = ModuleType(module_type) if module_type else None
    adapters = registry.list_adapters(mt)
    return {"adapters": adapters}


@router.post("/mount/{module_type}/{adapter_name}")
async def mount_adapter(
    module_type: str,
    adapter_name: str,
    config: Optional[Dict[str, Any]] = None
):
    """Mount an adapter as the active module."""
    try:
        mt = ModuleType(module_type)
        instance = registry.mount(mt, adapter_name, config)
        return {
            "success": True,
            "module_type": module_type,
            "adapter": adapter_name,
            "class": type(instance).__name__,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/unmount/{module_type}")
async def unmount_module(module_type: str):
    """Unmount a module."""
    try:
        mt = ModuleType(module_type)
        success = registry.unmount(mt)
        return {"success": success, "module_type": module_type}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# CONSTRAINT ENDPOINTS
# =============================================================================

@router.post("/constraints/check", response_model=ActionCheckResponse)
async def check_action(request: ActionCheckRequest):
    """
    Check if an action is allowed for an agent.

    Returns constraint result with severity and audit ID.
    """
    try:
        constraints = registry.get(ModuleType.CONSTRAINTS)
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="Constraint manager not mounted. Call POST /api/harness/mount/constraints/marqed first."
        )

    result = await constraints.check_action(
        agent_id=request.agent_id,
        action_type=request.action_type,
        action_params=request.action_params,
        context=request.context,
    )

    return ActionCheckResponse(
        allowed=result.allowed,
        severity=result.severity.value if hasattr(result.severity, 'value') else str(result.severity),
        reason=result.reason,
        requires_approval=result.requires_approval,
        audit_id=result.audit_id,
        matched_rules=result.matched_rules,
    )


@router.post("/constraints/validate-output", response_model=ActionCheckResponse)
async def validate_output(request: OutputValidationRequest):
    """Validate agent output against constraints."""
    try:
        constraints = registry.get(ModuleType.CONSTRAINTS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Constraint manager not mounted")

    result = await constraints.validate_output(
        agent_id=request.agent_id,
        output=request.output,
        output_type=request.output_type,
    )

    return ActionCheckResponse(
        allowed=result.allowed,
        severity=result.severity.value if hasattr(result.severity, 'value') else str(result.severity),
        reason=result.reason,
        requires_approval=result.requires_approval,
        audit_id=result.audit_id,
        matched_rules=result.matched_rules,
    )


@router.get("/constraints/{agent_id}")
async def get_agent_constraints(agent_id: str):
    """Get all constraints for an agent."""
    try:
        constraints = registry.get(ModuleType.CONSTRAINTS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Constraint manager not mounted")

    agent_constraints = await constraints.get_constraints(agent_id)
    return {"agent_id": agent_id, "constraints": agent_constraints}


@router.post("/constraints/add")
async def add_runtime_constraint(request: ConstraintAddRequest):
    """Add a runtime constraint for an agent."""
    try:
        constraints = registry.get(ModuleType.CONSTRAINTS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Constraint manager not mounted")

    success = await constraints.add_constraint(
        agent_id=request.agent_id,
        constraint={
            "action_type": request.action_type,
            "denied": request.denied,
            "reason": request.reason,
        }
    )

    return {"success": success, "agent_id": request.agent_id}


@router.delete("/constraints/{agent_id}/{constraint_id}")
async def remove_runtime_constraint(agent_id: str, constraint_id: str):
    """Remove a runtime constraint."""
    try:
        constraints = registry.get(ModuleType.CONSTRAINTS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Constraint manager not mounted")

    success = await constraints.remove_constraint(agent_id, constraint_id)
    return {"success": success, "agent_id": agent_id, "constraint_id": constraint_id}


@router.get("/constraints/audit-log")
async def get_audit_log(
    agent_id: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get constraint audit log."""
    try:
        constraints = registry.get(ModuleType.CONSTRAINTS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Constraint manager not mounted")

    log = constraints.get_audit_log(agent_id=agent_id, limit=limit)
    return {"entries": log, "count": len(log)}


@router.get("/constraints/stats")
async def get_constraint_stats():
    """Get constraint manager statistics."""
    try:
        constraints = registry.get(ModuleType.CONSTRAINTS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Constraint manager not mounted")

    return constraints.get_stats()


# =============================================================================
# CONTEXT ENDPOINTS
# =============================================================================

@router.post("/context/system")
async def set_system_context(request: SetSystemContextRequest):
    """Set system context for an agent."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    await context_mgr.set_system_context(
        agent_id=request.agent_id,
        context={
            "role": request.role,
            "capabilities": request.capabilities,
            "rules": request.rules,
            "ethics": request.ethics,
            "llm": request.llm_model,
        }
    )

    return {"success": True, "agent_id": request.agent_id}


@router.get("/context/system/{agent_id}")
async def get_system_context(agent_id: str):
    """Get system context for an agent."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    layer = await context_mgr.get_system_context(agent_id)
    if not layer:
        raise HTTPException(status_code=404, detail=f"No system context for agent {agent_id}")

    return {
        "agent_id": agent_id,
        "content": layer.content,
        "token_count": layer.token_count,
        "priority": layer.priority,
    }


@router.post("/context/task")
async def set_task_context(request: SetTaskContextRequest):
    """Set task context for a session."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    await context_mgr.set_task_context(
        session_id=request.session_id,
        context=request.context,
        ttl_seconds=request.ttl_seconds,
    )

    return {"success": True, "session_id": request.session_id}


@router.post("/context/memory")
async def add_memory(request: AddMemoryRequest):
    """Add memory observation to a session."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    memory_id = await context_mgr.add_memory(
        session_id=request.session_id,
        observation=request.observation,
        tags=request.tags,
        priority=request.priority,
    )

    return {"success": True, "session_id": request.session_id, "memory_id": memory_id}


@router.post("/context/resolve", response_model=ResolvedContextResponse)
async def resolve_context(request: ResolveContextRequest):
    """Resolve all context layers for an agent."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    resolved = await context_mgr.resolve_context(
        agent_id=request.agent_id,
        session_id=request.session_id,
        token_budget=request.token_budget,
    )

    return ResolvedContextResponse(
        system=resolved.system,
        task=resolved.task,
        memory=resolved.memory,
        total_tokens=resolved.total_tokens,
        layers_used=resolved.layers_used,
        truncated=resolved.truncated,
        context_hash=resolved.context_hash,
    )


@router.post("/context/compress/{session_id}")
async def compress_memory(
    session_id: str,
    compression_ratio: float = Query(0.1, ge=0.01, le=1.0)
):
    """Compress memories for a session."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    tokens_saved = await context_mgr.compress_memory(
        session_id=session_id,
        compression_ratio=compression_ratio,
    )

    return {"session_id": session_id, "tokens_saved": tokens_saved}


@router.delete("/context/task/{session_id}")
async def clear_task_context(session_id: str):
    """Clear task context for a session."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    await context_mgr.clear_task_context(session_id)
    return {"success": True, "session_id": session_id}


@router.delete("/context/session/{session_id}")
async def clear_session(session_id: str):
    """Clear all context for a session."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    await context_mgr.clear_session(session_id)
    return {"success": True, "session_id": session_id}


@router.get("/context/agents")
async def list_agents_with_context():
    """List all agents with system contexts."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    agents = context_mgr.list_agents()
    return {"agents": agents, "count": len(agents)}


@router.get("/context/stats")
async def get_context_stats():
    """Get context manager statistics."""
    try:
        context_mgr = registry.get(ModuleType.CONTEXT)
    except ValueError:
        raise HTTPException(status_code=503, detail="Context manager not mounted")

    return context_mgr.get_stats()


# =============================================================================
# TOOL REGISTRY ENDPOINTS
# =============================================================================

class ToolExecuteRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    agent_id: str
    session_id: str
    parameters: Dict[str, Any] = {}


class ToolExecuteResponse(BaseModel):
    """Response from tool execution."""
    success: bool
    result: Optional[Any]
    error: Optional[str]
    execution_time_ms: int
    audit_id: Optional[str]
    sandbox_used: bool


class SetToolPermissionsRequest(BaseModel):
    """Request to set agent tool permissions."""
    agent_id: str
    allowed: List[str]
    denied: List[str]
    requires_approval: Optional[List[str]] = None


class SetRateLimitRequest(BaseModel):
    """Request to set rate limit."""
    agent_id: str
    tool_name: str
    limit: int
    window_seconds: int = 60


@router.get("/tools")
async def list_tools():
    """List all registered tools."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    return {"tools": tool_registry.list_tools()}


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get a specific tool definition."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return {
        "name": tool.name,
        "category": tool.category.value,
        "description": tool.description,
        "parameters": tool.parameters,
        "requires_approval": tool.requires_approval,
        "sandbox_required": tool.sandbox_required,
        "rate_limit": tool.rate_limit,
        "timeout_seconds": tool.timeout_seconds,
        "enabled": tool.enabled,
    }


@router.get("/tools/agent/{agent_id}")
async def get_tools_for_agent(agent_id: str):
    """Get all tools available to an agent."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    tools = tool_registry.get_tools_for_agent(agent_id)
    return {
        "agent_id": agent_id,
        "tools": [
            {
                "name": t.name,
                "category": t.category.value,
                "description": t.description,
            }
            for t in tools
        ],
        "count": len(tools),
    }


@router.get("/tools/schema/{agent_id}")
async def get_tool_schema(agent_id: str):
    """Get OpenAI-compatible function schema for agent."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    return tool_registry.get_tool_schema(agent_id)


@router.post("/tools/can-use")
async def can_use_tool(
    agent_id: str = Query(...),
    tool_name: str = Query(...),
):
    """Check if an agent can use a specific tool."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    can_use = await tool_registry.can_use_tool(agent_id, tool_name)
    remaining = tool_registry.get_rate_limit_remaining(agent_id, tool_name)

    return {
        "agent_id": agent_id,
        "tool_name": tool_name,
        "can_use": can_use,
        "rate_limit_remaining": remaining,
    }


@router.post("/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest):
    """Execute a tool for an agent."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    from app.harness.core.protocols import ToolCallRequest

    call_request = ToolCallRequest(
        tool_name=request.tool_name,
        agent_id=request.agent_id,
        session_id=request.session_id,
        parameters=request.parameters,
    )

    result = await tool_registry.execute_tool(call_request)

    return ToolExecuteResponse(
        success=result.success,
        result=result.result,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
        audit_id=result.audit_id,
        sandbox_used=result.sandbox_used,
    )


@router.post("/tools/permissions")
async def set_tool_permissions(request: SetToolPermissionsRequest):
    """Set tool permissions for an agent."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    tool_registry.set_agent_permissions(
        agent_id=request.agent_id,
        allowed=request.allowed,
        denied=request.denied,
        requires_approval=request.requires_approval,
    )

    return {"success": True, "agent_id": request.agent_id}


@router.post("/tools/rate-limit")
async def set_rate_limit(request: SetRateLimitRequest):
    """Set rate limit for agent/tool."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    tool_registry.set_rate_limit(
        agent_id=request.agent_id,
        tool_name=request.tool_name,
        limit=request.limit,
        window_seconds=request.window_seconds,
    )

    return {
        "success": True,
        "agent_id": request.agent_id,
        "tool_name": request.tool_name,
        "limit": request.limit,
    }


@router.get("/tools/audit-log")
async def get_tool_audit_log(
    agent_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = Query(100, le=1000),
):
    """Get tool execution audit log."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    log = tool_registry.get_audit_log(
        agent_id=agent_id,
        tool_name=tool_name,
        limit=limit,
    )
    return {"entries": log, "count": len(log)}


@router.get("/tools/stats")
async def get_tool_stats():
    """Get tool registry statistics."""
    try:
        tool_registry = registry.get(ModuleType.TOOLS)
    except ValueError:
        raise HTTPException(status_code=503, detail="Tool registry not mounted")

    return tool_registry.get_stats()


# =============================================================================
# VERSION TRACKER ENDPOINTS (Week 93)
# =============================================================================

class SnapshotCreateRequest(BaseModel):
    """Request to create a context snapshot."""
    agent_id: str
    session_id: str
    context: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class SnapshotResponse(BaseModel):
    """Response with snapshot details."""
    version_id: str
    content_hash: str
    agent_id: str
    session_id: str
    timestamp: datetime
    token_count: int
    parent_version: Optional[str]
    has_metadata: bool


class DiffRequest(BaseModel):
    """Request to calculate diff between versions."""
    from_version: str
    to_version: str


class DiffResponse(BaseModel):
    """Response with diff details."""
    from_version: str
    to_version: str
    added: Dict[str, Any]
    removed: Dict[str, Any]
    modified: Dict[str, Any]
    token_delta: int


class LinkActionRequest(BaseModel):
    """Request to link snapshot to action."""
    version_id: str
    action_id: str


@router.post("/versions/snapshot", response_model=SnapshotResponse)
async def create_snapshot(request: SnapshotCreateRequest):
    """Create an immutable context snapshot."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    snapshot = await version_tracker.snapshot(
        agent_id=request.agent_id,
        session_id=request.session_id,
        context=request.context,
        metadata=request.metadata,
    )

    return SnapshotResponse(
        version_id=snapshot.version_id,
        content_hash=snapshot.content_hash,
        agent_id=snapshot.agent_id,
        session_id=snapshot.session_id,
        timestamp=snapshot.timestamp,
        token_count=snapshot.token_count,
        parent_version=snapshot.parent_version,
        has_metadata=bool(snapshot.metadata),
    )


@router.get("/versions/{version_id}")
async def get_snapshot(version_id: str):
    """Get a specific snapshot by version ID."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    snapshot = await version_tracker.get_snapshot(version_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {version_id}")

    return {
        "version_id": snapshot.version_id,
        "content_hash": snapshot.content_hash,
        "agent_id": snapshot.agent_id,
        "session_id": snapshot.session_id,
        "timestamp": snapshot.timestamp.isoformat(),
        "layers": snapshot.layers,
        "token_count": snapshot.token_count,
        "parent_version": snapshot.parent_version,
        "metadata": snapshot.metadata,
    }


@router.get("/versions/hash/{content_hash}")
async def get_snapshot_by_hash(content_hash: str):
    """Get snapshot by content hash (deduplication lookup)."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    snapshot = await version_tracker.get_by_hash(content_hash)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot not found for hash: {content_hash}")

    return {
        "version_id": snapshot.version_id,
        "content_hash": snapshot.content_hash,
        "agent_id": snapshot.agent_id,
        "session_id": snapshot.session_id,
        "timestamp": snapshot.timestamp.isoformat(),
        "token_count": snapshot.token_count,
        "parent_version": snapshot.parent_version,
    }


@router.get("/versions/session/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: int = Query(100, le=1000)
):
    """Get snapshot history for a session, newest first."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    history = await version_tracker.get_history(session_id, limit)

    return {
        "session_id": session_id,
        "snapshots": [
            {
                "version_id": s.version_id,
                "content_hash": s.content_hash,
                "timestamp": s.timestamp.isoformat(),
                "token_count": s.token_count,
                "parent_version": s.parent_version,
            }
            for s in history
        ],
        "count": len(history),
    }


@router.get("/versions/agent/{agent_id}/history")
async def get_agent_history(
    agent_id: str,
    limit: int = Query(100, le=1000)
):
    """Get snapshot history for an agent across sessions."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    history = await version_tracker.get_agent_history(agent_id, limit)

    return {
        "agent_id": agent_id,
        "snapshots": [
            {
                "version_id": s.version_id,
                "session_id": s.session_id,
                "content_hash": s.content_hash,
                "timestamp": s.timestamp.isoformat(),
                "token_count": s.token_count,
            }
            for s in history
        ],
        "count": len(history),
    }


@router.post("/versions/diff", response_model=DiffResponse)
async def calculate_diff(request: DiffRequest):
    """Calculate difference between two versions."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    try:
        diff = await version_tracker.diff(request.from_version, request.to_version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return DiffResponse(
        from_version=diff.from_version,
        to_version=diff.to_version,
        added=diff.added,
        removed=diff.removed,
        modified=diff.modified,
        token_delta=diff.token_delta,
    )


@router.post("/versions/{version_id}/restore")
async def restore_version(version_id: str):
    """Restore context to a specific version."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    try:
        context = await version_tracker.restore(version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "version_id": version_id,
        "restored_context": context,
    }


@router.post("/versions/link-action")
async def link_action(request: LinkActionRequest):
    """Link context snapshot to an agent action."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    try:
        await version_tracker.link_to_action(request.version_id, request.action_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "success": True,
        "version_id": request.version_id,
        "action_id": request.action_id,
    }


@router.get("/versions/{version_id}/actions")
async def get_actions_for_snapshot(version_id: str):
    """Get all action IDs linked to a snapshot."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    actions = await version_tracker.get_actions_for_snapshot(version_id)

    return {
        "version_id": version_id,
        "actions": actions,
        "count": len(actions),
    }


@router.get("/versions/{version_id}/chain")
async def get_snapshot_chain(version_id: str):
    """Get full parent chain for a snapshot (oldest to newest)."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    try:
        chain = await version_tracker.get_snapshot_chain(version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "version_id": version_id,
        "chain": [
            {
                "version_id": s.version_id,
                "content_hash": s.content_hash,
                "timestamp": s.timestamp.isoformat(),
                "token_count": s.token_count,
            }
            for s in chain
        ],
        "chain_length": len(chain),
    }


@router.get("/versions/session/{session_id}/latest")
async def get_latest_snapshot(session_id: str):
    """Get the most recent snapshot for a session."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    snapshot = await version_tracker.get_latest_snapshot(session_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"No snapshots for session: {session_id}")

    return {
        "version_id": snapshot.version_id,
        "content_hash": snapshot.content_hash,
        "agent_id": snapshot.agent_id,
        "session_id": snapshot.session_id,
        "timestamp": snapshot.timestamp.isoformat(),
        "token_count": snapshot.token_count,
        "parent_version": snapshot.parent_version,
    }


@router.delete("/versions/session/{session_id}")
async def clear_session_snapshots(session_id: str):
    """Clear all snapshots for a session."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    removed = version_tracker.clear_session(session_id)

    return {
        "success": True,
        "session_id": session_id,
        "snapshots_removed": removed,
    }


@router.post("/versions/cleanup")
async def cleanup_old_snapshots(retention_days: int = Query(90, ge=1, le=365)):
    """Remove snapshots older than retention period."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    removed = await version_tracker.cleanup_old_snapshots(retention_days)

    return {
        "success": True,
        "retention_days": retention_days,
        "snapshots_removed": removed,
    }


@router.get("/versions/stats")
async def get_version_stats():
    """Get version tracker statistics."""
    try:
        version_tracker = registry.get(ModuleType.VERSIONING)
    except ValueError:
        raise HTTPException(status_code=503, detail="Version tracker not mounted")

    return version_tracker.get_statistics()


# =============================================================================
# INITIALIZATION ENDPOINT
# =============================================================================

@router.post("/initialize")
async def initialize_harness():
    """
    Initialize harness with default MarQed adapters.

    This mounts:
    - MarQedConstraintManager for constraints
    - MarQedContextManager for context
    - MarQedToolRegistry for tools
    - MarQedVersionTracker for versioning
    """
    from app.harness.adapters import (
        MarQedConstraintManager,
        MarQedContextManager,
        MarQedToolRegistry,
        MarQedVersionTracker,
    )

    results = {}

    # Register and mount constraint manager
    try:
        registry.register_adapter(
            "marqed",
            MarQedConstraintManager,
            ModuleType.CONSTRAINTS,
            {"version": "1.0", "author": "MarQed"}
        )
        registry.mount(ModuleType.CONSTRAINTS, "marqed")
        results["constraints"] = "mounted"
    except Exception as e:
        results["constraints"] = f"error: {str(e)}"

    # Register and mount context manager
    try:
        registry.register_adapter(
            "marqed",
            MarQedContextManager,
            ModuleType.CONTEXT,
            {"version": "1.0", "author": "MarQed"}
        )
        registry.mount(ModuleType.CONTEXT, "marqed")
        results["context"] = "mounted"
    except Exception as e:
        results["context"] = f"error: {str(e)}"

    # Register and mount tool registry
    try:
        # Get constraint manager for integration
        constraint_mgr = None
        try:
            constraint_mgr = registry.get(ModuleType.CONSTRAINTS)
        except ValueError:
            pass

        registry.register_adapter(
            "marqed",
            MarQedToolRegistry,
            ModuleType.TOOLS,
            {"version": "1.0", "author": "MarQed"}
        )
        registry.mount(ModuleType.TOOLS, "marqed", {"constraint_manager": constraint_mgr})
        results["tools"] = "mounted"
    except Exception as e:
        results["tools"] = f"error: {str(e)}"

    # Register and mount version tracker
    try:
        registry.register_adapter(
            "marqed",
            MarQedVersionTracker,
            ModuleType.VERSIONING,
            {"version": "1.0", "author": "MarQed"}
        )
        registry.mount(ModuleType.VERSIONING, "marqed")
        results["versioning"] = "mounted"
    except Exception as e:
        results["versioning"] = f"error: {str(e)}"

    return {
        "success": True,
        "results": results,
        "status": registry.get_status(),
    }
