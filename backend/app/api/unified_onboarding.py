"""
Unified Onboarding API

4th Brown Paper workflow: orchestrates the 3 existing workflows and adds
a Reconciliation step that compares bottom-up vs top-down vs enhanced results.

Endpoints:
- POST /api/brown-paper/unified/start          - Start workflow from MarQed session
- POST /api/brown-paper/unified/{id}/execute-step/{step}  - Execute single step
- POST /api/brown-paper/unified/{id}/execute-all           - Execute all 8 steps
- GET  /api/brown-paper/unified/{id}/status                - Progress per step
- GET  /api/brown-paper/unified/{id}/reconciliation        - Full reconciliation report
- GET  /api/brown-paper/unified/{id}/results               - Complete results
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.unified_onboarding_service import UnifiedOnboardingService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/brown-paper/unified",
    tags=["Unified Onboarding"],
)


# ============================================================================
# REQUEST / RESPONSE MODELS
# ============================================================================

class UnifiedStartRequest(BaseModel):
    """Request to start a unified onboarding workflow."""
    marqed_session_id: str = Field(..., description="ID of an existing MarQed session with 8 answers")
    project_path: Optional[str] = Field(None, description="Path to the project source code for code scanning")


class UnifiedStartResponse(BaseModel):
    """Response after starting a unified onboarding workflow."""
    unified_session_id: str
    status: str
    total_steps: int = 8
    project_name: str


class StepResultResponse(BaseModel):
    """Response after executing a single step."""
    step: int
    name: str
    status: str
    duration_ms: Optional[int] = None
    result_summary: dict = {}


class StepDetail(BaseModel):
    """Detail for a single step in the status overview."""
    step: int
    name: str
    status: str
    duration_ms: Optional[int] = None


class UnifiedStatusResponse(BaseModel):
    """Detailed progress per step."""
    unified_session_id: str
    project_name: str
    status: str
    current_step: int
    total_steps: int = 8
    steps: list = []
    total_duration_ms: Optional[int] = None
    error_message: Optional[str] = None


class ReconciliationResponse(BaseModel):
    """Full reconciliation report."""
    blind_spots: list = []
    phantom_features: list = []
    confidence_heatmap: list = []
    fp_deltas: list = []
    domain_disputes: list = []
    unified_epics_count: int = 0
    unified_features_count: int = 0
    unified_stories_count: int = 0
    matching_summary: dict = {}


class UnifiedResultResponse(BaseModel):
    """Complete results including all 8 steps."""
    unified_session_id: str
    status: str
    steps_completed: int = 0
    total_duration_ms: Optional[int] = None
    reconciliation_summary: dict = {}
    step_results: dict = {}


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/start", response_model=UnifiedStartResponse)
async def start_unified_workflow(
    request: UnifiedStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start unified onboarding workflow from an existing MarQed session.

    The MarQed session should have 8 answered questions. The project_path is
    optional but enables code scanning (step 1) and bottom-up epic generation (step 5).
    """
    try:
        service = UnifiedOnboardingService(db)
        session = await service.start(
            marqed_session_id=request.marqed_session_id,
            project_path=request.project_path,
        )
        return UnifiedStartResponse(
            unified_session_id=str(session.id),
            status=session.status,
            total_steps=8,
            project_name=session.project_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start unified workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{unified_id}/execute-step/{step}", response_model=StepResultResponse)
async def execute_step(
    unified_id: UUID,
    step: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a single step (1-8) of the unified workflow.

    Steps can be executed independently, but some steps depend on results
    from earlier steps (e.g., step 5 needs step 1 results).
    """
    try:
        service = UnifiedOnboardingService(db)
        result = await service.execute_step(unified_id, step)
        return StepResultResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Step {step} failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{unified_id}/execute-all", response_model=UnifiedResultResponse)
async def execute_all_steps(
    unified_id: UUID,
    tier: str = "ENTERPRISE",
    db: AsyncSession = Depends(get_db),
):
    """
    Execute all 8 steps sequentially.

    This is the recommended way to run the complete unified workflow.
    Each step's result is saved to the database, so the workflow can be
    monitored via the status endpoint.
    """
    try:
        service = UnifiedOnboardingService(db)
        result = await service.execute_all(unified_id, tier=tier)
        return UnifiedResultResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Execute all failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{unified_id}/status", response_model=UnifiedStatusResponse)
async def get_unified_status(
    unified_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed progress per step.

    Shows status (pending/running/completed) and duration for each of the 8 steps.
    """
    try:
        service = UnifiedOnboardingService(db)
        status = await service.get_status(unified_id)
        return UnifiedStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{unified_id}/reconciliation", response_model=ReconciliationResponse)
async def get_reconciliation(
    unified_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the full reconciliation report (step 8 results).

    Includes blind spots, phantom features, confidence heatmap,
    FP deltas, domain disputes, and unified epic counts.
    """
    service = UnifiedOnboardingService(db)
    session = await service.get_session(unified_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {unified_id}")

    step_8 = session.step_8_result
    if not step_8:
        raise HTTPException(status_code=400, detail="Reconciliation not yet completed (step 8)")

    return ReconciliationResponse(
        blind_spots=step_8.get("blind_spots", []),
        phantom_features=step_8.get("phantom_features", []),
        confidence_heatmap=step_8.get("confidence_heatmap", []),
        fp_deltas=step_8.get("fp_deltas", []),
        domain_disputes=step_8.get("domain_disputes", []),
        unified_epics_count=step_8.get("unified_epics_count", 0),
        unified_features_count=step_8.get("unified_features_count", 0),
        unified_stories_count=step_8.get("unified_stories_count", 0),
        matching_summary=step_8.get("matching_summary", {}),
    )


@router.get("/{unified_id}/results", response_model=UnifiedResultResponse)
async def get_unified_results(
    unified_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete results including all 8 step results.
    """
    service = UnifiedOnboardingService(db)
    session = await service.get_session(unified_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {unified_id}")

    # Count completed steps
    steps_completed = 0
    step_results = {}
    for i in range(1, 9):
        result = getattr(session, f"step_{i}_result", None)
        if result:
            steps_completed = i
            step_results[f"step_{i}"] = {
                "status": result.get("status", "unknown"),
                "summary": {
                    k: v for k, v in result.items()
                    if k not in ("modules", "domains", "epics", "specification", "features", "stories")
                },
            }

    # Reconciliation summary
    recon_summary = {}
    if session.step_8_result:
        recon_summary = {
            k: session.step_8_result.get(k)
            for k in [
                "blind_spots", "phantom_features", "confidence_heatmap",
                "fp_deltas", "domain_disputes", "unified_epics_count",
                "unified_features_count", "unified_stories_count",
            ]
            if k in (session.step_8_result or {})
        }

    return UnifiedResultResponse(
        unified_session_id=str(session.id),
        status=session.status,
        steps_completed=steps_completed,
        total_duration_ms=session.total_duration_ms,
        reconciliation_summary=recon_summary,
        step_results=step_results,
    )
