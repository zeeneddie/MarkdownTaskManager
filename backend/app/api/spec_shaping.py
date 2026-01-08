"""
Spec Shaping API - Endpoints for iterative spec refinement

Week 59: Agent OS Integration
Implements the "Shape → Verify → Loop" pattern.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.spec_shaping_service import SpecShapingService

router = APIRouter(prefix="/api/spec-shaping", tags=["spec-shaping"])


# Request/Response schemas
class StartSessionRequest(BaseModel):
    """Request to start a new spec shaping session."""
    description: str = Field(..., min_length=10, description="Initial description to shape")
    workflow_type: str = Field(..., description="Workflow type (NEW_FEATURE, BUG, etc.)")
    project_id: Optional[int] = Field(None, description="Optional project ID to link to")
    max_iterations: int = Field(5, ge=1, le=10, description="Maximum iterations allowed")


class SessionResponse(BaseModel):
    """Response for session operations."""
    session_id: int
    status: str
    message: Optional[str] = None


class IterationResponse(BaseModel):
    """Response for iteration operations."""
    session_id: int
    iteration_number: int
    status: str
    checks_passed: int
    checks_total: int
    all_passed: bool
    verifications: list
    current_spec_preview: str


# Endpoints
@router.post("/sessions", response_model=SessionResponse)
async def start_session(request: StartSessionRequest, db=Depends(get_db)):
    """
    Start a new spec shaping session.

    The session begins with an initial description and iteratively
    shapes it into a complete specification that passes all quality checks.

    Args:
        description: The initial description to shape
        workflow_type: Type of workflow (NEW_FEATURE, BUG, MAINTENANCE, etc.)
        project_id: Optional project ID to associate with
        max_iterations: Maximum number of shape/verify cycles (default: 5)

    Returns:
        Session ID and initial status
    """
    service = SpecShapingService(db)
    result = await service.start_session(
        description=request.description,
        workflow_type=request.workflow_type,
        project_id=request.project_id,
        max_iterations=request.max_iterations,
    )
    return result


@router.post("/sessions/{session_id}/iterate")
async def iterate_session(session_id: int, db=Depends(get_db)):
    """
    Perform one shape-verify iteration on a session.

    This endpoint:
    1. Takes the current spec
    2. Shapes it using Felix agent (or template fallback)
    3. Verifies against quality checks
    4. Returns results and updated status

    Call repeatedly until status is 'approved' or 'max_iterations'.

    Args:
        session_id: ID of the session to iterate

    Returns:
        Iteration results with verification details
    """
    service = SpecShapingService(db)
    try:
        result = await service.iterate(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: int, db=Depends(get_db)):
    """
    Get details of a spec shaping session.

    Returns session metadata, current spec, and iteration history.
    """
    service = SpecShapingService(db)
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return result


@router.get("/sessions")
async def list_sessions(
    status: Optional[str] = None,
    limit: int = 20,
    db=Depends(get_db)
):
    """
    List spec shaping sessions.

    Args:
        status: Optional filter by status (draft, approved, max_iterations)
        limit: Maximum number of sessions to return (default: 20)

    Returns:
        List of sessions with summary information
    """
    service = SpecShapingService(db)
    return await service.list_sessions(status=status, limit=limit)


@router.get("/checks")
async def list_quality_checks():
    """
    List all available quality checks for specs.

    Returns the checks that are run during verification,
    including their categories and requirements.
    """
    from app.services.spec_shaping_service import SPEC_QUALITY_CHECKS, CheckCategory

    return {
        "checks": [
            {
                "name": check["name"],
                "category": check["category"].value,
                "description": check["description"],
            }
            for check in SPEC_QUALITY_CHECKS
        ],
        "categories": [c.value for c in CheckCategory],
    }


@router.post("/sessions/{session_id}/approve")
async def approve_session(session_id: int, db=Depends(get_db)):
    """
    Manually approve a session (skip remaining checks).

    Use this when the spec is acceptable but some automated checks fail.
    """
    from app.models.spec_shaping import SpecShapingSession
    from sqlalchemy import select
    from datetime import datetime

    result = await db.execute(
        select(SpecShapingSession).where(SpecShapingSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    session.status = "approved"
    session.completed_at = datetime.now()
    await db.commit()

    return {
        "session_id": session_id,
        "status": "approved",
        "message": "Session manually approved",
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db=Depends(get_db)):
    """Delete a spec shaping session and all its iterations."""
    from app.models.spec_shaping import SpecShapingSession
    from sqlalchemy import select

    result = await db.execute(
        select(SpecShapingSession).where(SpecShapingSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    await db.delete(session)
    await db.commit()

    return {"message": f"Session {session_id} deleted"}
