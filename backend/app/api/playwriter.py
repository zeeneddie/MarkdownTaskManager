"""
Playwriter API - Week 78

REST API endpoints for Playwriter browser automation service.
Provides session management, code execution, and tab permission handling.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.playwriter_service import PlaywriterService


router = APIRouter(prefix="/api/playwriter", tags=["Playwriter"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new browser session."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    browser_type: str = Field(default="chromium", pattern="^(chromium|firefox|webkit)$")
    headless: bool = True
    viewport_width: int = Field(default=1280, ge=320, le=3840)
    viewport_height: int = Field(default=720, ge=240, le=2160)
    context_options: Optional[Dict[str, Any]] = None


class ExecuteCodeRequest(BaseModel):
    """Request to execute Playwright code."""
    code: str = Field(..., min_length=1, max_length=50000, description="Playwright code to execute")
    tab_id: Optional[int] = Field(default=None, description="Tab to execute in (must be permitted)")


class ClickRequest(BaseModel):
    """Request to click an element."""
    selector: str = Field(..., min_length=1, description="CSS selector for element")


class TypeTextRequest(BaseModel):
    """Request to type text."""
    selector: str = Field(..., min_length=1, description="CSS selector for input")
    text: str = Field(..., min_length=1, description="Text to type")


class FillRequest(BaseModel):
    """Request to fill a form field."""
    selector: str = Field(..., min_length=1, description="CSS selector for input")
    value: str = Field(..., description="Value to fill")


class GotoRequest(BaseModel):
    """Request to navigate to URL."""
    url: str = Field(..., min_length=1, description="URL to navigate to")
    wait_until: str = Field(default="load", pattern="^(load|domcontentloaded|networkidle)$")


class FillFormRequest(BaseModel):
    """Request to fill multiple form fields."""
    fields: Dict[str, str] = Field(..., description="Selector->value mapping")


class GrantPermissionRequest(BaseModel):
    """Request to grant tab permission."""
    granted_by: str = Field(..., min_length=1, max_length=100)


class SessionResponse(BaseModel):
    """Session response."""
    id: str
    name: str
    description: Optional[str]
    browser_type: str
    headless: bool
    viewport_width: int
    viewport_height: int
    status: str
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    closed_at: Optional[datetime]


class ExecutionResponse(BaseModel):
    """Execution response."""
    id: str
    session_id: str
    tab_id: Optional[int]
    code: str
    result: Optional[Dict[str, Any]]
    screenshot_path: Optional[str]
    error: Optional[str]
    execution_time_ms: Optional[int]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]


class TabResponse(BaseModel):
    """Tab response."""
    id: str
    session_id: str
    tab_index: int
    url: Optional[str]
    title: Optional[str]
    permitted: bool
    permitted_at: Optional[datetime]
    permitted_by: Optional[str]
    created_at: datetime


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new browser automation session.

    The session will be in 'created' status until started.
    """
    service = PlaywriterService(db)
    session = await service.create_session(
        name=request.name,
        description=request.description,
        browser_type=request.browser_type,
        headless=request.headless,
        viewport_width=request.viewport_width,
        viewport_height=request.viewport_height,
        context_options=request.context_options
    )

    return SessionResponse(
        id=str(session.id),
        name=session.name,
        description=session.description,
        browser_type=session.browser_type,
        headless=session.headless,
        viewport_width=session.viewport_width,
        viewport_height=session.viewport_height,
        status=session.status,
        error_message=session.error_message,
        created_at=session.created_at,
        started_at=session.started_at,
        closed_at=session.closed_at
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List browser automation sessions."""
    service = PlaywriterService(db)
    sessions = await service.list_sessions(status=status, limit=limit)

    return [
        SessionResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            browser_type=s.browser_type,
            headless=s.headless,
            viewport_width=s.viewport_width,
            viewport_height=s.viewport_height,
            status=s.status,
            error_message=s.error_message,
            created_at=s.created_at,
            started_at=s.started_at,
            closed_at=s.closed_at
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get session details by ID."""
    service = PlaywriterService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    return SessionResponse(
        id=str(session.id),
        name=session.name,
        description=session.description,
        browser_type=session.browser_type,
        headless=session.headless,
        viewport_width=session.viewport_width,
        viewport_height=session.viewport_height,
        status=session.status,
        error_message=session.error_message,
        created_at=session.created_at,
        started_at=session.started_at,
        closed_at=session.closed_at
    )


@router.post("/sessions/{session_id}/start", response_model=SessionResponse)
async def start_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a browser session.

    Launches the browser and sets status to 'active'.
    """
    service = PlaywriterService(db)
    session = await service.start_session(session_id)

    return SessionResponse(
        id=str(session.id),
        name=session.name,
        description=session.description,
        browser_type=session.browser_type,
        headless=session.headless,
        viewport_width=session.viewport_width,
        viewport_height=session.viewport_height,
        status=session.status,
        error_message=session.error_message,
        created_at=session.created_at,
        started_at=session.started_at,
        closed_at=session.closed_at
    )


@router.post("/sessions/{session_id}/close", response_model=SessionResponse)
async def close_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Close a browser session.

    Closes the browser and sets status to 'closed'.
    """
    service = PlaywriterService(db)
    session = await service.close_session(session_id)

    return SessionResponse(
        id=str(session.id),
        name=session.name,
        description=session.description,
        browser_type=session.browser_type,
        headless=session.headless,
        viewport_width=session.viewport_width,
        viewport_height=session.viewport_height,
        status=session.status,
        error_message=session.error_message,
        created_at=session.created_at,
        started_at=session.started_at,
        closed_at=session.closed_at
    )


# =============================================================================
# CODE EXECUTION
# =============================================================================

@router.post("/sessions/{session_id}/execute", response_model=ExecutionResponse)
async def execute_code(
    session_id: UUID,
    request: ExecuteCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute Playwright code in the session.

    The code has access to the `page` object for browser automation.
    Tab must be permitted before execution if tab_id is specified.
    """
    service = PlaywriterService(db)

    try:
        execution = await service.execute(
            session_id=session_id,
            code=request.code,
            tab_id=request.tab_id
        )

        return ExecutionResponse(
            id=str(execution.id),
            session_id=str(execution.session_id),
            tab_id=execution.tab_id,
            code=execution.code,
            result=execution.result,
            screenshot_path=execution.screenshot_path,
            error=execution.error,
            execution_time_ms=execution.execution_time_ms,
            status=execution.status,
            created_at=execution.created_at,
            completed_at=execution.completed_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/sessions/{session_id}/executions", response_model=List[ExecutionResponse])
async def list_executions(
    session_id: UUID,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List code executions for a session."""
    service = PlaywriterService(db)
    executions = await service.list_executions(session_id, status=status, limit=limit)

    return [
        ExecutionResponse(
            id=str(e.id),
            session_id=str(e.session_id),
            tab_id=e.tab_id,
            code=e.code,
            result=e.result,
            screenshot_path=e.screenshot_path,
            error=e.error,
            execution_time_ms=e.execution_time_ms,
            status=e.status,
            created_at=e.created_at,
            completed_at=e.completed_at
        )
        for e in executions
    ]


# =============================================================================
# CONVENIENCE ACTIONS
# =============================================================================

@router.post("/sessions/{session_id}/click", response_model=ExecutionResponse)
async def click_element(
    session_id: UUID,
    request: ClickRequest,
    db: AsyncSession = Depends(get_db)
):
    """Click an element by CSS selector."""
    service = PlaywriterService(db)
    execution = await service.click(session_id, request.selector)

    return ExecutionResponse(
        id=str(execution.id),
        session_id=str(execution.session_id),
        tab_id=execution.tab_id,
        code=execution.code,
        result=execution.result,
        screenshot_path=execution.screenshot_path,
        error=execution.error,
        execution_time_ms=execution.execution_time_ms,
        status=execution.status,
        created_at=execution.created_at,
        completed_at=execution.completed_at
    )


@router.post("/sessions/{session_id}/type", response_model=ExecutionResponse)
async def type_text(
    session_id: UUID,
    request: TypeTextRequest,
    db: AsyncSession = Depends(get_db)
):
    """Type text into an element."""
    service = PlaywriterService(db)
    execution = await service.type_text(session_id, request.selector, request.text)

    return ExecutionResponse(
        id=str(execution.id),
        session_id=str(execution.session_id),
        tab_id=execution.tab_id,
        code=execution.code,
        result=execution.result,
        screenshot_path=execution.screenshot_path,
        error=execution.error,
        execution_time_ms=execution.execution_time_ms,
        status=execution.status,
        created_at=execution.created_at,
        completed_at=execution.completed_at
    )


@router.post("/sessions/{session_id}/fill", response_model=ExecutionResponse)
async def fill_field(
    session_id: UUID,
    request: FillRequest,
    db: AsyncSession = Depends(get_db)
):
    """Fill a form field."""
    service = PlaywriterService(db)
    execution = await service.fill(session_id, request.selector, request.value)

    return ExecutionResponse(
        id=str(execution.id),
        session_id=str(execution.session_id),
        tab_id=execution.tab_id,
        code=execution.code,
        result=execution.result,
        screenshot_path=execution.screenshot_path,
        error=execution.error,
        execution_time_ms=execution.execution_time_ms,
        status=execution.status,
        created_at=execution.created_at,
        completed_at=execution.completed_at
    )


@router.post("/sessions/{session_id}/goto", response_model=ExecutionResponse)
async def navigate(
    session_id: UUID,
    request: GotoRequest,
    db: AsyncSession = Depends(get_db)
):
    """Navigate to a URL."""
    service = PlaywriterService(db)
    execution = await service.goto(session_id, request.url, request.wait_until)

    return ExecutionResponse(
        id=str(execution.id),
        session_id=str(execution.session_id),
        tab_id=execution.tab_id,
        code=execution.code,
        result=execution.result,
        screenshot_path=execution.screenshot_path,
        error=execution.error,
        execution_time_ms=execution.execution_time_ms,
        status=execution.status,
        created_at=execution.created_at,
        completed_at=execution.completed_at
    )


@router.post("/sessions/{session_id}/screenshot")
async def take_screenshot(
    session_id: UUID,
    full_page: bool = Query(False, description="Capture full page"),
    db: AsyncSession = Depends(get_db)
):
    """Take a screenshot of the current page."""
    service = PlaywriterService(db)

    try:
        screenshot_data = await service.screenshot(session_id, full_page=full_page)

        return Response(
            content=screenshot_data,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=screenshot_{session_id}.png"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sessions/{session_id}/fill-form", response_model=ExecutionResponse)
async def fill_form(
    session_id: UUID,
    request: FillFormRequest,
    db: AsyncSession = Depends(get_db)
):
    """Fill multiple form fields at once."""
    service = PlaywriterService(db)
    execution = await service.fill_form(session_id, request.fields)

    return ExecutionResponse(
        id=str(execution.id),
        session_id=str(execution.session_id),
        tab_id=execution.tab_id,
        code=execution.code,
        result=execution.result,
        screenshot_path=execution.screenshot_path,
        error=execution.error,
        execution_time_ms=execution.execution_time_ms,
        status=execution.status,
        created_at=execution.created_at,
        completed_at=execution.completed_at
    )


# =============================================================================
# TAB MANAGEMENT
# =============================================================================

@router.get("/sessions/{session_id}/tabs", response_model=List[TabResponse])
async def list_tabs(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all tabs for a session."""
    service = PlaywriterService(db)
    tabs = await service.get_tabs(session_id)

    return [
        TabResponse(
            id=str(t.id),
            session_id=str(t.session_id),
            tab_index=t.tab_index,
            url=t.url,
            title=t.title,
            permitted=t.permitted,
            permitted_at=t.permitted_at,
            permitted_by=t.permitted_by,
            created_at=t.created_at
        )
        for t in tabs
    ]


@router.get("/sessions/{session_id}/tabs/permitted", response_model=List[TabResponse])
async def list_permitted_tabs(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List only permitted tabs."""
    service = PlaywriterService(db)
    tabs = await service.get_permitted_tabs(session_id)

    return [
        TabResponse(
            id=str(t.id),
            session_id=str(t.session_id),
            tab_index=t.tab_index,
            url=t.url,
            title=t.title,
            permitted=t.permitted,
            permitted_at=t.permitted_at,
            permitted_by=t.permitted_by,
            created_at=t.created_at
        )
        for t in tabs
    ]


@router.post("/sessions/{session_id}/tabs/{tab_index}/request-permission", response_model=TabResponse)
async def request_tab_permission(
    session_id: UUID,
    tab_index: int,
    db: AsyncSession = Depends(get_db)
):
    """Request permission for a tab (creates pending permission request)."""
    service = PlaywriterService(db)
    tab = await service.request_tab_permission(session_id, tab_index)

    return TabResponse(
        id=str(tab.id),
        session_id=str(tab.session_id),
        tab_index=tab.tab_index,
        url=tab.url,
        title=tab.title,
        permitted=tab.permitted,
        permitted_at=tab.permitted_at,
        permitted_by=tab.permitted_by,
        created_at=tab.created_at
    )


@router.post("/sessions/{session_id}/tabs/{tab_index}/grant-permission", response_model=TabResponse)
async def grant_tab_permission(
    session_id: UUID,
    tab_index: int,
    request: GrantPermissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Grant permission for a tab."""
    service = PlaywriterService(db)
    tab = await service.grant_tab_permission(session_id, tab_index, request.granted_by)

    return TabResponse(
        id=str(tab.id),
        session_id=str(tab.session_id),
        tab_index=tab.tab_index,
        url=tab.url,
        title=tab.title,
        permitted=tab.permitted,
        permitted_at=tab.permitted_at,
        permitted_by=tab.permitted_by,
        created_at=tab.created_at
    )


@router.delete("/sessions/{session_id}/tabs/{tab_index}/revoke-permission", response_model=TabResponse)
async def revoke_tab_permission(
    session_id: UUID,
    tab_index: int,
    db: AsyncSession = Depends(get_db)
):
    """Revoke permission for a tab."""
    service = PlaywriterService(db)
    tab = await service.revoke_tab_permission(session_id, tab_index)

    return TabResponse(
        id=str(tab.id),
        session_id=str(tab.session_id),
        tab_index=tab.tab_index,
        url=tab.url,
        title=tab.title,
        permitted=tab.permitted,
        permitted_at=tab.permitted_at,
        permitted_by=tab.permitted_by,
        created_at=tab.created_at
    )


# =============================================================================
# STATISTICS
# =============================================================================

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get Playwriter usage statistics."""
    from sqlalchemy import func, select
    from app.models.browser_automation import PlaywriterSession, PlaywriterExecution

    # Count sessions by status
    sessions_query = await db.execute(
        select(PlaywriterSession.status, func.count(PlaywriterSession.id))
        .group_by(PlaywriterSession.status)
    )
    sessions_by_status = {row[0]: row[1] for row in sessions_query}

    # Total executions
    exec_query = await db.execute(
        select(func.count(PlaywriterExecution.id))
    )
    total_executions = exec_query.scalar() or 0

    # Average execution time
    avg_query = await db.execute(
        select(func.avg(PlaywriterExecution.execution_time_ms))
        .where(PlaywriterExecution.execution_time_ms.isnot(None))
    )
    avg_execution_ms = avg_query.scalar() or 0

    # Failed executions
    failed_query = await db.execute(
        select(func.count(PlaywriterExecution.id))
        .where(PlaywriterExecution.error.isnot(None))
    )
    failed_count = failed_query.scalar() or 0

    return {
        "sessions": {
            "total": sum(sessions_by_status.values()),
            "by_status": sessions_by_status
        },
        "executions": {
            "total": total_executions,
            "failed": failed_count,
            "success_rate": round((total_executions - failed_count) / total_executions, 3) if total_executions > 0 else 0,
            "avg_execution_ms": round(avg_execution_ms, 2)
        }
    }
