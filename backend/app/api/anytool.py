"""
Week 72: AnyTool Universal Tool Calling API

REST endpoints for intelligent tool orchestration with:
- Multi-stage filtering (server → name → semantic → LLM ranking)
- Automatic failover on tool failures
- Quality-aware selection with reliability tracking
- Learning from feedback

Endpoints:
- POST /api/anytool/discover - Discover tools matching query
- POST /api/anytool/execute - Execute tool with failover
- GET /api/anytool/reliability - Get reliability statistics
- GET /api/anytool/suggestions - Get tool suggestions
- POST /api/anytool/feedback - Submit tool feedback
- GET /api/anytool/status - Get system status
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.anytool_service import AnyToolService


router = APIRouter(prefix="/api/anytool", tags=["AnyTool Universal Tool Calling"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ToolDiscoverRequest(BaseModel):
    """Request to discover matching tools."""
    query: str = Field(..., description="Natural language description of desired tool")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (file, task type)")
    max_results: int = Field(10, ge=1, le=50, description="Maximum tools to return")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "query": "read a file from the filesystem",
                "context": {"task_type": "code_analysis"},
                "max_results": 5
            }
        })


class ToolExecuteRequest(BaseModel):
    """Request to execute a tool."""
    query: str = Field(..., description="Natural language tool description")
    params: Dict[str, Any] = Field(..., description="Tool parameters")
    agent_id: Optional[str] = Field(None, description="Requesting agent ID")
    task_id: Optional[UUID] = Field(None, description="Associated task ID")
    fallback_enabled: bool = Field(True, description="Enable automatic failover")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "query": "read file contents",
                "params": {"file_path": "/src/main.py"},
                "agent_id": "felix",
                "fallback_enabled": True
            }
        })


class ToolFeedbackRequest(BaseModel):
    """Request to submit tool feedback."""
    tool_id: UUID = Field(..., description="Tool ID")
    feedback: str = Field(..., description="Feedback text")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "tool_id": "123e4567-e89b-12d3-a456-426614174000",
                "feedback": "Tool worked well but was slow",
                "rating": 4
            }
        })


class ToolDiscoverResponse(BaseModel):
    """Response with discovered tools."""
    query: str
    total_found: int
    tools: List[Dict[str, Any]]


class ToolExecuteResponse(BaseModel):
    """Response from tool execution."""
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    tool_used: Optional[str] = None
    selection_score: Optional[float] = None
    failover_attempts: Optional[int] = None
    latency_ms: int


class ReliabilityStatsResponse(BaseModel):
    """Response with reliability statistics."""
    period_hours: int
    tools: Dict[str, Dict[str, Any]]
    total_executions: int


class ToolSuggestion(BaseModel):
    """A single tool suggestion."""
    tool_name: str
    usage_count: int
    success_rate: float


class ToolSuggestionsResponse(BaseModel):
    """Response with tool suggestions."""
    task_type: str
    agent_id: Optional[str]
    suggestions: List[ToolSuggestion]


class FeedbackResponse(BaseModel):
    """Response from feedback submission."""
    status: str
    tool_name: Optional[str] = None
    new_success_rate: Optional[float] = None
    message: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """Response with system status."""
    status: str
    servers: Dict[str, int]
    tools: Dict[str, int]
    reliability_24h: Dict[str, Any]
    features: List[str]
    version: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/discover", response_model=ToolDiscoverResponse)
async def discover_tools(
    request: ToolDiscoverRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Discover relevant tools using multi-stage filtering.

    Stages:
    1. Filter by available servers
    2. Name-based filtering
    3. Semantic similarity
    4. Rank by quality and context

    Returns tools with semantic, quality, and final scores.
    """
    service = AnyToolService(db)

    tools = await service.discover_tools(
        query=request.query,
        context=request.context,
        max_results=request.max_results
    )

    return ToolDiscoverResponse(
        query=request.query,
        total_found=len(tools),
        tools=tools
    )


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a tool with automatic failover.

    1. Discovers best matching tools
    2. Tries primary tool
    3. On failure, tries fallback tools (if enabled)
    4. Records execution metrics

    Returns execution result with metadata.
    """
    service = AnyToolService(db)

    result = await service.execute_tool(
        query=request.query,
        params=request.params,
        agent_id=request.agent_id,
        task_id=request.task_id,
        fallback_enabled=request.fallback_enabled
    )

    return ToolExecuteResponse(**result)


@router.get("/reliability", response_model=ReliabilityStatsResponse)
async def get_reliability_stats(
    tool_id: Optional[UUID] = Query(None, description="Filter by tool ID"),
    hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reliability statistics for tools.

    Returns success rates, failure counts, and failover statistics
    for the specified time period.
    """
    service = AnyToolService(db)

    stats = await service.get_reliability_stats(
        tool_id=tool_id,
        hours=hours
    )

    return ReliabilityStatsResponse(**stats)


@router.get("/suggestions", response_model=ToolSuggestionsResponse)
async def get_tool_suggestions(
    task_type: str = Query(..., description="Type of task"),
    agent_id: Optional[str] = Query(None, description="Agent ID for personalized suggestions"),
    limit: int = Query(5, ge=1, le=20, description="Maximum suggestions"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tool suggestions based on task type and agent history.

    Returns most successful tools for similar tasks,
    optionally personalized for the requesting agent.
    """
    service = AnyToolService(db)

    suggestions = await service.get_tool_suggestions(
        task_type=task_type,
        agent_id=agent_id,
        limit=limit
    )

    return ToolSuggestionsResponse(
        task_type=task_type,
        agent_id=agent_id,
        suggestions=[ToolSuggestion(**s) for s in suggestions]
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: ToolFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback about tool performance.

    Feedback is used to adjust tool success rates
    and improve future tool selection.
    """
    service = AnyToolService(db)

    result = await service.learn_from_feedback(
        tool_id=request.tool_id,
        feedback=request.feedback,
        rating=request.rating
    )

    return FeedbackResponse(**result)


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get AnyTool system status.

    Returns server health, tool counts, and reliability metrics.
    """
    service = AnyToolService(db)

    status = await service.get_system_status()

    return SystemStatusResponse(**status)


@router.get("/health")
async def health_check():
    """Health check endpoint for AnyTool service."""
    return {
        "status": "healthy",
        "service": "anytool",
        "version": "1.0.0",
        "features": [
            "multi_stage_filtering",
            "semantic_search",
            "automatic_failover",
            "quality_tracking",
            "learning_from_feedback"
        ]
    }
