"""
CCTrace API Endpoints - Observability and Tracing

Week 61: Enhanced Observability Integration

Endpoints for:
- Thinking block capture and retrieval
- Tool execution logging
- Session export
- Cache metrics
- Pattern analysis
"""

from datetime import datetime, timezone
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.cctrace_service import CCTraceService, get_cot_forcing_prompt
from app.services.token_cache_service import TokenCacheService
from app.services.cost_management_service import CostManagementService, AlertLevel
from app.services.session_exporters import get_exporter, SessionData
from app.services.session_exporters.base import (
    ThinkingBlockExport,
    ToolExecutionExport,
    MessageExport,
)
from app.models.cctrace import ThinkingBlock, ToolExecution, SessionExport

router = APIRouter(prefix="/cctrace", tags=["CCTrace"])


# ============ Request/Response Models ============

class CaptureThinkingRequest(BaseModel):
    """Request to capture thinking blocks from LLM response."""
    action_id: int
    provider: str
    response_data: dict
    session_id: Optional[str] = None


class LogToolRequest(BaseModel):
    """Request to log a tool execution."""
    action_id: int
    tool_name: str
    tool_input: dict
    tool_output: Optional[str] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    session_id: Optional[str] = None


class ThinkingBlockResponse(BaseModel):
    """Response containing thinking block data."""
    id: int
    action_id: int
    session_id: Optional[str]
    block_type: str
    content: str
    token_count: int
    sequence_number: int
    signature: Optional[str]
    content_hash: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolExecutionResponse(BaseModel):
    """Response containing tool execution data."""
    id: int
    action_id: int
    session_id: Optional[str]
    tool_name: str
    tool_input: dict
    tool_output: Optional[str]
    duration_ms: Optional[int]
    success: bool
    error_message: Optional[str]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionSummaryResponse(BaseModel):
    """Response containing session summary."""
    session_id: str
    thinking_blocks: dict
    tool_executions: dict


class CacheMetricsResponse(BaseModel):
    """Response containing cache metrics."""
    period_hours: int
    action_count: int
    tokens: dict
    cache: dict
    savings: dict


class CotPromptResponse(BaseModel):
    """Response containing CoT prompt."""
    prompt: str
    structured: bool


# ============ Thinking Block Endpoints ============

@router.post("/thinking/capture", response_model=List[ThinkingBlockResponse])
async def capture_thinking_blocks(
    request: CaptureThinkingRequest,
    db: Session = Depends(get_db)
):
    """
    Capture thinking blocks from LLM response.

    Extracts and stores thinking blocks based on provider:
    - Claude: Native thinking blocks
    - Codex: Tag-based extraction
    - Ollama: CoT parsed content
    """
    service = CCTraceService(db)

    blocks = service.capture_thinking_blocks(
        action_id=request.action_id,
        provider=request.provider,
        response_data=request.response_data,
        session_id=request.session_id,
    )

    db.commit()
    return [ThinkingBlockResponse.model_validate(b) for b in blocks]


@router.get("/thinking/session/{session_id}", response_model=List[ThinkingBlockResponse])
async def get_session_thinking_blocks(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get all thinking blocks for a session."""
    service = CCTraceService(db)
    blocks = service.get_session_thinking_blocks(session_id)
    return [ThinkingBlockResponse.model_validate(b) for b in blocks]


@router.get("/thinking/block/{block_id}", response_model=ThinkingBlockResponse)
async def get_thinking_block(
    block_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific thinking block by ID."""
    block = db.query(ThinkingBlock).filter(ThinkingBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Thinking block not found")
    return ThinkingBlockResponse.model_validate(block)


# ============ Tool Execution Endpoints ============

@router.post("/tools/log", response_model=ToolExecutionResponse)
async def log_tool_execution(
    request: LogToolRequest,
    db: Session = Depends(get_db)
):
    """Log a tool execution event."""
    service = CCTraceService(db)

    tool = service.log_tool_execution(
        action_id=request.action_id,
        tool_name=request.tool_name,
        tool_input=request.tool_input,
        tool_output=request.tool_output,
        duration_ms=request.duration_ms,
        success=request.success,
        error_message=request.error_message,
        session_id=request.session_id,
    )

    db.commit()
    return ToolExecutionResponse.model_validate(tool)


@router.get("/tools/session/{session_id}", response_model=List[ToolExecutionResponse])
async def get_session_tool_executions(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get all tool executions for a session."""
    service = CCTraceService(db)
    tools = service.get_session_tool_executions(session_id)
    return [ToolExecutionResponse.model_validate(t) for t in tools]


# ============ Session Endpoints ============

@router.get("/session/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get summary statistics for a session."""
    service = CCTraceService(db)
    summary = service.get_session_summary(session_id)
    return SessionSummaryResponse(**summary)


@router.get("/session/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = Query("json", description="Export format: md, json, xml, jsonl"),
    include_thinking: bool = Query(True, description="Include thinking blocks"),
    include_tools: bool = Query(True, description="Include tool executions"),
    include_messages: bool = Query(True, description="Include messages"),
    db: Session = Depends(get_db)
):
    """
    Export session in specified format.

    Supported formats:
    - json: Structured JSON
    - md: Human-readable Markdown
    - xml: XML for external tools
    - jsonl: Line-delimited JSON for streaming/ML
    """
    try:
        exporter = get_exporter(format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = CCTraceService(db)

    # Get session data
    thinking_blocks = service.get_session_thinking_blocks(session_id) if include_thinking else []
    tool_executions = service.get_session_tool_executions(session_id) if include_tools else []

    # Build session data
    session_data = SessionData(
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
        provider="multi",
        model="mixed",
        thinking_blocks=[
            ThinkingBlockExport(
                block_type=b.block_type,
                content=b.content,
                token_count=b.token_count or 0,
                sequence_number=b.sequence_number or 0,
                signature=b.signature,
                content_hash=b.content_hash,
                extra_data=b.extra_data or {},
            )
            for b in thinking_blocks
        ],
        tool_executions=[
            ToolExecutionExport(
                tool_name=t.tool_name,
                tool_input=t.tool_input or {},
                tool_output=t.tool_output,
                duration_ms=t.duration_ms,
                success=t.success,
                error_message=t.error_message,
                executed_at=t.executed_at,
            )
            for t in tool_executions
        ],
    )

    # Export
    content = exporter.export(
        session_data,
        include_thinking=include_thinking,
        include_tools=include_tools,
        include_messages=include_messages,
    )

    # Record export
    db_export = service.create_session_export(
        session_id=session_id,
        format=format,
        include_thinking=include_thinking,
        include_tools=include_tools,
        include_messages=include_messages,
    )
    service.complete_export(db_export.id, content)
    db.commit()

    return Response(
        content=content,
        media_type=exporter.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={exporter.get_filename(session_id)}"
        }
    )


# ============ Cache Metrics Endpoints ============

@router.get("/cache/metrics", response_model=CacheMetricsResponse)
async def get_cache_metrics(
    session_id: Optional[str] = Query(None, description="Filter by session"),
    agent_name: Optional[str] = Query(None, description="Filter by agent"),
    hours: int = Query(24, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    """Get aggregated cache metrics."""
    service = TokenCacheService(db)
    metrics = service.get_cache_metrics(
        session_id=session_id,
        agent_name=agent_name,
        hours=hours,
    )
    return CacheMetricsResponse(**metrics)


@router.get("/cache/by-agent")
async def get_cache_metrics_by_agent(
    hours: int = Query(24, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    """Get cache metrics grouped by agent."""
    service = TokenCacheService(db)
    return service.get_cache_metrics_by_agent(hours=hours)


@router.get("/cache/trend")
async def get_cache_trend(
    hours: int = Query(24, description="Number of hours"),
    db: Session = Depends(get_db)
):
    """Get hourly cache usage trend."""
    service = TokenCacheService(db)
    return service.get_hourly_cache_trend(hours=hours)


@router.post("/cache/calculate-savings")
async def calculate_cost_savings(
    model: str = Query(..., description="Model name"),
    input_tokens: int = Query(..., description="Input tokens"),
    output_tokens: int = Query(..., description="Output tokens"),
    cache_created: int = Query(0, description="Cache tokens created"),
    cache_read: int = Query(0, description="Cache tokens read"),
    db: Session = Depends(get_db)
):
    """Calculate cost savings from caching."""
    service = TokenCacheService(db)
    return service.calculate_cost_savings(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_created=cache_created,
        cache_read=cache_read,
    )


# ============ Utility Endpoints ============

@router.get("/cot-prompt", response_model=CotPromptResponse)
async def get_cot_prompt(
    structured: bool = Query(False, description="Use structured 5-step format")
):
    """
    Get Chain-of-Thought forcing prompt for Ollama.

    Use this prompt in system messages to encourage
    models to use <thinking> tags.
    """
    return CotPromptResponse(
        prompt=get_cot_forcing_prompt(structured),
        structured=structured,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "cctrace",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============ Cost Management Endpoints ============

class CreateBudgetRequest(BaseModel):
    """Request to create a budget."""
    name: str
    daily_limit: Optional[float] = None
    weekly_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95
    project_id: Optional[str] = None
    agent_name: Optional[str] = None
    allowed_providers: Optional[List[str]] = None
    fallback_chain: Optional[List[str]] = None


class BudgetResponse(BaseModel):
    """Budget configuration response."""
    id: int
    name: str
    daily_limit: Optional[float]
    weekly_limit: Optional[float]
    monthly_limit: Optional[float]
    warning_threshold: float
    critical_threshold: float
    project_id: Optional[str]
    agent_name: Optional[str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


@router.post("/budget", response_model=BudgetResponse)
async def create_budget(
    request: CreateBudgetRequest,
    db: Session = Depends(get_db)
):
    """Create a new budget configuration."""
    service = CostManagementService(db)
    budget = service.create_budget(
        name=request.name,
        daily_limit=request.daily_limit,
        weekly_limit=request.weekly_limit,
        monthly_limit=request.monthly_limit,
        warning_threshold=request.warning_threshold,
        critical_threshold=request.critical_threshold,
        project_id=request.project_id,
        agent_name=request.agent_name,
        allowed_providers=request.allowed_providers,
        fallback_chain=request.fallback_chain,
    )
    return BudgetResponse.model_validate(budget)


@router.get("/budget", response_model=List[BudgetResponse])
async def get_budgets(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    agent_name: Optional[str] = Query(None, description="Filter by agent"),
    active_only: bool = Query(True, description="Only active budgets"),
    db: Session = Depends(get_db)
):
    """Get budget configurations."""
    service = CostManagementService(db)
    budgets = service.get_budgets(
        project_id=project_id,
        agent_name=agent_name,
        active_only=active_only,
    )
    return [BudgetResponse.model_validate(b) for b in budgets]


@router.get("/budget/{budget_id}/spend")
async def get_budget_spend(
    budget_id: int,
    period: str = Query("daily", description="Period: daily, weekly, monthly"),
    db: Session = Depends(get_db)
):
    """Get current spend for a budget period."""
    service = CostManagementService(db)
    return service.get_current_spend(budget_id, period)


@router.get("/budget/{budget_id}/check")
async def check_budget(
    budget_id: int,
    estimated_cost: float = Query(..., description="Estimated request cost"),
    db: Session = Depends(get_db)
):
    """Check if budget allows a request."""
    service = CostManagementService(db)
    allowed, reason, fallback = service.check_budget_available(budget_id, estimated_cost)
    return {
        "allowed": allowed,
        "reason": reason,
        "recommended_fallback": fallback,
    }


@router.get("/cost/breakdown")
async def get_cost_breakdown(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    days: int = Query(30, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """Get cost breakdown by model and agent."""
    service = CostManagementService(db)
    return service.get_cost_breakdown(project_id=project_id, days=days)


@router.get("/cost/recommendations")
async def get_cost_recommendations(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    days: int = Query(7, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """Get cost optimization recommendations."""
    service = CostManagementService(db)
    return service.get_optimization_recommendations(project_id=project_id, days=days)


@router.post("/cost/calculate")
async def calculate_cost(
    model: str = Query(..., description="Model name"),
    input_tokens: int = Query(..., description="Input tokens"),
    output_tokens: int = Query(..., description="Output tokens"),
    cache_created: int = Query(0, description="Cache tokens created"),
    cache_read: int = Query(0, description="Cache tokens read"),
    db: Session = Depends(get_db)
):
    """Calculate cost for a request."""
    service = CostManagementService(db)
    cost = service.calculate_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_created=cache_created,
        cache_read=cache_read,
    )
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_created": cache_created,
        "cache_read": cache_read,
        "cost_usd": round(cost, 6),
    }
