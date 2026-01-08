"""
Claude-Mem API - Week 76

REST API endpoints for Claude-Mem session memory service.
Provides observation capture, context generation, search, and compression.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.claude_mem_service import ClaudeMemService


router = APIRouter(prefix="/api/claude-mem", tags=["Claude-Mem"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    session_id: str = Field(..., description="Unique session identifier")
    title: Optional[str] = None
    project_id: Optional[int] = None
    token_budget: int = Field(default=4000, ge=500, le=32000)
    auto_tag: bool = True


class UpdateSessionRequest(BaseModel):
    """Request to update session settings."""
    title: Optional[str] = None
    token_budget: Optional[int] = Field(default=None, ge=500, le=32000)
    compression_ratio: Optional[float] = Field(default=None, ge=0.01, le=1.0)
    auto_tag: Optional[bool] = None
    endless_mode: Optional[bool] = None


class CaptureObservationRequest(BaseModel):
    """Request to capture an observation."""
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., min_length=1, max_length=10000)
    observation_type: str = Field(default="insight")
    priority: Optional[str] = Field(default=None, pattern="^(critical|high|normal|low)$")
    tags: Optional[List[str]] = None
    source_context: Optional[str] = None
    related_files: Optional[List[str]] = None
    auto_tag: bool = True


class TagObservationRequest(BaseModel):
    """Request to tag an observation."""
    tags: List[str] = Field(..., min_length=1)
    replace: bool = False


class ContextWindowRequest(BaseModel):
    """Request to get context window."""
    token_budget: Optional[int] = Field(default=None, ge=500, le=32000)
    strategy: str = Field(default="recent", pattern="^(recent|priority|mixed)$")
    include_summaries: bool = True


class SearchRequest(BaseModel):
    """Request to search memories."""
    query: str = Field(..., min_length=1)
    use_fts: bool = True
    limit: int = Field(default=20, ge=1, le=100)
    tags_filter: Optional[List[str]] = None
    priority_filter: Optional[str] = Field(default=None, pattern="^(critical|high|normal|low)$")


class CompressRequest(BaseModel):
    """Request to compress memories."""
    compression_ratio: Optional[float] = Field(default=None, ge=0.01, le=1.0)
    older_than_hours: int = Field(default=24, ge=1, le=720)


class InjectContextRequest(BaseModel):
    """Request to inject context into prompt."""
    prompt: str = Field(..., min_length=1)


class SessionResponse(BaseModel):
    """Session response."""
    id: str
    session_id: str
    project_id: Optional[int]
    title: Optional[str]
    endless_mode: bool
    token_budget: int
    compression_ratio: float
    auto_tag: bool
    session_data: Dict[str, Any]
    last_activity: Optional[str]
    created_at: Optional[str]


class ObservationResponse(BaseModel):
    """Observation response."""
    id: str
    session_id: str
    content: str
    tags: List[str]
    priority: str
    observation_type: Optional[str]
    source_context: Optional[str]
    related_files: List[str]
    embedding_status: str
    created_at: Optional[str]


class ContextWindowResponse(BaseModel):
    """Context window response."""
    session_id: str
    context_text: str
    token_count: int
    token_budget: int
    observations_included: int
    summaries_included: int
    strategy: str
    context_id: str


class SearchResponse(BaseModel):
    """Search response."""
    session_id: str
    query: str
    results_count: int
    results: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    """Session statistics response."""
    session_id: str
    session_data: Dict[str, Any]
    observation_count: int
    summary_count: int
    total_tokens_estimated: int
    tag_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    endless_mode: bool
    token_budget: int


class DashboardResponse(BaseModel):
    """Dashboard data response."""
    project_id: Optional[int]
    total_sessions: int
    endless_sessions: int
    total_observations: int
    sessions: List[Dict[str, Any]]


# =============================================================================
# SESSION ENDPOINTS
# =============================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """Create a new Claude-Mem session."""
    service = ClaudeMemService(db)
    result = await service.create_session(
        session_id=request.session_id,
        title=request.title,
        project_id=request.project_id,
        token_budget=request.token_budget,
        auto_tag=request.auto_tag
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return SessionResponse(**result)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """Get session by ID."""
    service = ClaudeMemService(db)
    result = await service.get_session(session_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    return SessionResponse(**result)


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """Update session settings."""
    service = ClaudeMemService(db)

    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    result = await service.update_session(session_id, updates)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return SessionResponse(**result)


@router.post("/sessions/{session_id}/endless/enable", response_model=SessionResponse)
async def enable_endless_mode(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """Enable endless mode for a session."""
    service = ClaudeMemService(db)
    result = await service.enable_endless_mode(session_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return SessionResponse(**result)


@router.post("/sessions/{session_id}/endless/disable", response_model=SessionResponse)
async def disable_endless_mode(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """Disable endless mode for a session."""
    service = ClaudeMemService(db)
    result = await service.disable_endless_mode(session_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return SessionResponse(**result)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Delete a session and all related data."""
    service = ClaudeMemService(db)
    result = await service.delete_session(session_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return result


# =============================================================================
# OBSERVATION ENDPOINTS
# =============================================================================

@router.post("/observe", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
async def capture_observation(
    request: CaptureObservationRequest,
    db: AsyncSession = Depends(get_db)
) -> ObservationResponse:
    """Capture an observation during a session."""
    service = ClaudeMemService(db)
    result = await service.capture_observation(
        session_id=request.session_id,
        content=request.content,
        observation_type=request.observation_type,
        priority=request.priority,
        tags=request.tags,
        source_context=request.source_context,
        related_files=request.related_files,
        auto_tag=request.auto_tag
    )

    return ObservationResponse(**result)


@router.patch("/observations/{observation_id}/tags", response_model=ObservationResponse)
async def tag_observation(
    observation_id: UUID,
    request: TagObservationRequest,
    db: AsyncSession = Depends(get_db)
) -> ObservationResponse:
    """Add or replace tags on an observation."""
    service = ClaudeMemService(db)
    result = await service.tag_observation(
        observation_id=observation_id,
        tags=request.tags,
        replace=request.replace
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return ObservationResponse(**result)


@router.get("/sessions/{session_id}/observations")
async def get_observations_by_tags(
    session_id: str,
    tags: List[str] = Query(default=[]),
    match_all: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get observations matching specified tags."""
    service = ClaudeMemService(db)

    if tags:
        return await service.get_observations_by_tags(
            session_id=session_id,
            tags=tags,
            match_all=match_all
        )
    else:
        # Return all observations if no tags specified
        result = await service.search_memories(
            session_id=session_id,
            query="",
            use_fts=False
        )
        return result.get("results", [])


# =============================================================================
# CONTEXT WINDOW ENDPOINTS
# =============================================================================

@router.post("/sessions/{session_id}/context", response_model=ContextWindowResponse)
async def get_context_window(
    session_id: str,
    request: ContextWindowRequest,
    db: AsyncSession = Depends(get_db)
) -> ContextWindowResponse:
    """Get context window for session within token budget."""
    service = ClaudeMemService(db)
    result = await service.get_context_window(
        session_id=session_id,
        token_budget=request.token_budget,
        strategy=request.strategy,
        include_summaries=request.include_summaries
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return ContextWindowResponse(**result)


# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================

@router.post("/sessions/{session_id}/search", response_model=SearchResponse)
async def search_memories(
    session_id: str,
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
) -> SearchResponse:
    """Search session memories."""
    service = ClaudeMemService(db)
    result = await service.search_memories(
        session_id=session_id,
        query=request.query,
        use_fts=request.use_fts,
        limit=request.limit,
        tags_filter=request.tags_filter,
        priority_filter=request.priority_filter
    )

    return SearchResponse(**result)


# =============================================================================
# COMPRESSION ENDPOINTS
# =============================================================================

@router.post("/sessions/{session_id}/compress")
async def compress_memories(
    session_id: str,
    request: CompressRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Compress older observations into summaries."""
    service = ClaudeMemService(db)
    result = await service.compress_memories(
        session_id=session_id,
        compression_ratio=request.compression_ratio,
        older_than_hours=request.older_than_hours
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return result


# =============================================================================
# ENDLESS MODE ENDPOINTS
# =============================================================================

@router.post("/sessions/{session_id}/inject")
async def inject_context(
    session_id: str,
    request: InjectContextRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Inject session context into a prompt for endless mode."""
    service = ClaudeMemService(db)
    result = await service.inject_context(
        session_id=session_id,
        prompt=request.prompt
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return result


# =============================================================================
# STATISTICS & DASHBOARD ENDPOINTS
# =============================================================================

@router.get("/sessions/{session_id}/statistics", response_model=StatisticsResponse)
async def get_session_statistics(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> StatisticsResponse:
    """Get comprehensive statistics for a session."""
    service = ClaudeMemService(db)
    result = await service.get_session_statistics(session_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return StatisticsResponse(**result)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(
    project_id: Optional[int] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
) -> DashboardResponse:
    """Get dashboard data for sessions."""
    service = ClaudeMemService(db)
    result = await service.get_dashboard_data(
        project_id=project_id,
        limit=limit
    )

    return DashboardResponse(**result)


# =============================================================================
# CLEANUP ENDPOINTS
# =============================================================================

@router.delete("/cleanup")
async def cleanup_old_sessions(
    days_inactive: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Clean up sessions inactive for specified days."""
    service = ClaudeMemService(db)
    return await service.cleanup_old_sessions(days_inactive=days_inactive)
