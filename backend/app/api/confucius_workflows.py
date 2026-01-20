"""
API Routes for Confucius Workflow Orchestration.

Provides endpoints for executing and monitoring orchestrated workflows
through the Confucius agent system.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import asyncio
import json

from app.confucius.workflows import (
    BrownPaperOrchestrator,
    MigrationOrchestrator,
    GreenPaperOrchestrator,
    QualityOrchestrator,
    WorkflowResult,
    WorkflowStatus,
)
from app.confucius.quality import (
    QualityProgressStream,
    StreamEventType,
    get_global_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/confucius/workflows", tags=["confucius-workflows"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class BrownPaperRequest(BaseModel):
    """Request for Brown Paper workflow."""

    session_id: str = Field(..., description="Session identifier")
    application_id: str = Field(..., description="Application to analyze")
    scan_path: str = Field(..., description="Path to scan")
    tech_stack: List[str] = Field(
        default=["python"], description="Technology stack"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class MigrationRequest(BaseModel):
    """Request for Migration workflow."""

    session_id: str = Field(..., description="Session identifier")
    answers: Dict[str, str] = Field(
        ..., description="Answers to 8 strategic questions"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class GreenPaperRequest(BaseModel):
    """Request for Green Paper workflow."""

    session_id: str = Field(..., description="Session identifier")
    project_name: str = Field(..., description="Project name")
    answers: Dict[str, str] = Field(
        ..., description="Answers to 6 vision questions"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class QualityRequest(BaseModel):
    """Request for Quality workflow."""

    session_id: str = Field(..., description="Session identifier")
    project_path: str = Field(..., description="Path to project")
    tech_stack: List[str] = Field(
        default=["python"], description="Technology stack"
    )
    scanners: List[str] = Field(
        default=["complexity", "security"],
        description="Scanners to run",
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class WorkflowResponse(BaseModel):
    """Response for workflow execution."""

    workflow_id: str
    workflow_type: str
    status: str
    message: str
    started: bool = True


class WorkflowResultResponse(BaseModel):
    """Response with workflow results."""

    workflow_id: str
    workflow_type: str
    status: str
    success: bool
    stages_completed: int
    stages_total: int
    overall_quality_score: float
    duration_seconds: Optional[float]
    final_output: Dict[str, Any]
    error: Optional[str] = None


# =============================================================================
# ORCHESTRATOR INSTANCES
# =============================================================================

_brown_paper_orchestrator: Optional[BrownPaperOrchestrator] = None
_migration_orchestrator: Optional[MigrationOrchestrator] = None
_green_paper_orchestrator: Optional[GreenPaperOrchestrator] = None
_quality_orchestrator: Optional[QualityOrchestrator] = None
_running_results: Dict[str, WorkflowResult] = {}


def get_brown_paper_orchestrator() -> BrownPaperOrchestrator:
    global _brown_paper_orchestrator
    if _brown_paper_orchestrator is None:
        _brown_paper_orchestrator = BrownPaperOrchestrator(
            stream=get_global_stream()
        )
    return _brown_paper_orchestrator


def get_migration_orchestrator() -> MigrationOrchestrator:
    global _migration_orchestrator
    if _migration_orchestrator is None:
        _migration_orchestrator = MigrationOrchestrator(
            stream=get_global_stream()
        )
    return _migration_orchestrator


def get_green_paper_orchestrator() -> GreenPaperOrchestrator:
    global _green_paper_orchestrator
    if _green_paper_orchestrator is None:
        _green_paper_orchestrator = GreenPaperOrchestrator(
            stream=get_global_stream()
        )
    return _green_paper_orchestrator


def get_quality_orchestrator() -> QualityOrchestrator:
    global _quality_orchestrator
    if _quality_orchestrator is None:
        _quality_orchestrator = QualityOrchestrator(
            stream=get_global_stream()
        )
    return _quality_orchestrator


# =============================================================================
# WORKFLOW ENDPOINTS
# =============================================================================


@router.post("/brown-paper/start", response_model=WorkflowResponse)
async def start_brown_paper_workflow(
    request: BrownPaperRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a Brown Paper analysis workflow.

    Analyzes legacy codebase through 6 phases:
    1. Code Understanding
    2. Domain Extraction
    3. Story Extraction
    4. Deep Extraction (optional)
    5. Estimation
    6. Output Consolidation
    """
    orchestrator = get_brown_paper_orchestrator()

    async def run_workflow():
        result = await orchestrator.run(
            session_id=request.session_id,
            input_data={
                "application_id": request.application_id,
                "scan_path": request.scan_path,
                "tech_stack": request.tech_stack,
            },
            metadata=request.metadata,
        )
        _running_results[result.workflow_id] = result

    background_tasks.add_task(run_workflow)

    return WorkflowResponse(
        workflow_id=f"bp-{request.session_id[:8]}",
        workflow_type="brown_paper",
        status="started",
        message="Brown Paper workflow started in background",
    )


@router.post("/migration/start", response_model=WorkflowResponse)
async def start_migration_workflow(
    request: MigrationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a Migration planning workflow.

    Executes MarQed 8-question migration planning:
    1. Validate Answers
    2. Technical Analysis (Miguel)
    3. Generate Specification (Peter, Betty)
    4. Generate Tasks (Felix, Paul)
    5. Estimate Effort (Eliza)
    6. Quality Review (Quinn)
    """
    orchestrator = get_migration_orchestrator()

    # Validate required answers
    questions = orchestrator.get_questions()
    missing = [q["id"] for q in questions if q["id"] not in request.answers]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing answers for questions: {missing}",
        )

    async def run_workflow():
        result = await orchestrator.run(
            session_id=request.session_id,
            input_data={"answers": request.answers},
            metadata=request.metadata,
        )
        _running_results[result.workflow_id] = result

    background_tasks.add_task(run_workflow)

    return WorkflowResponse(
        workflow_id=f"mig-{request.session_id[:8]}",
        workflow_type="migration",
        status="started",
        message="Migration workflow started in background",
    )


@router.post("/green-paper/start", response_model=WorkflowResponse)
async def start_green_paper_workflow(
    request: GreenPaperRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a Green Paper greenfield project workflow.

    Creates comprehensive project specification:
    1. Validate Vision
    2. Requirements Constitution (Peter, Betty)
    3. UX Design (Vicky)
    4. Architecture Design (Felix)
    5. Implementation Planning (Paul, Eliza)
    6. Quality Review (Quinn)
    """
    orchestrator = get_green_paper_orchestrator()

    # Validate required answers
    questions = orchestrator.get_questions()
    missing = [q["id"] for q in questions if q["id"] not in request.answers]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing answers for questions: {missing}",
        )

    async def run_workflow():
        result = await orchestrator.run(
            session_id=request.session_id,
            input_data={
                "project_name": request.project_name,
                "answers": request.answers,
            },
            metadata=request.metadata,
        )
        _running_results[result.workflow_id] = result

    background_tasks.add_task(run_workflow)

    return WorkflowResponse(
        workflow_id=f"gp-{request.session_id[:8]}",
        workflow_type="green_paper",
        status="started",
        message="Green Paper workflow started in background",
    )


@router.post("/quality/start", response_model=WorkflowResponse)
async def start_quality_workflow(
    request: QualityRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a Quality gate workflow.

    Executes quality analysis:
    1. Scan Execution (Miguel)
    2. Metrics Analysis (Miguel)
    3. Quality Review (Quinn)
    4. Remediation Planning (Marcus) - if needed
    5. Test Validation (Tessa) - if needed
    """
    orchestrator = get_quality_orchestrator()

    async def run_workflow():
        result = await orchestrator.run(
            session_id=request.session_id,
            input_data={
                "project_path": request.project_path,
                "tech_stack": request.tech_stack,
                "scanners": request.scanners,
            },
            metadata=request.metadata,
        )
        _running_results[result.workflow_id] = result

    background_tasks.add_task(run_workflow)

    return WorkflowResponse(
        workflow_id=f"qa-{request.session_id[:8]}",
        workflow_type="quality",
        status="started",
        message="Quality workflow started in background",
    )


# =============================================================================
# STATUS AND RESULTS ENDPOINTS
# =============================================================================


@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of a running workflow."""
    # Check all orchestrators
    for orchestrator in [
        get_brown_paper_orchestrator(),
        get_migration_orchestrator(),
        get_green_paper_orchestrator(),
        get_quality_orchestrator(),
    ]:
        status = orchestrator.get_workflow_status(workflow_id)
        if status:
            return status

    # Check completed results
    if workflow_id in _running_results:
        result = _running_results[workflow_id]
        return result.to_dict()

    raise HTTPException(status_code=404, detail="Workflow not found")


@router.get("/result/{workflow_id}", response_model=WorkflowResultResponse)
async def get_workflow_result(workflow_id: str):
    """Get result of a completed workflow."""
    if workflow_id not in _running_results:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found or still running",
        )

    result = _running_results[workflow_id]

    return WorkflowResultResponse(
        workflow_id=result.workflow_id,
        workflow_type=result.workflow_type,
        status=result.status.value,
        success=result.success,
        stages_completed=result.stages_completed,
        stages_total=result.stages_total,
        overall_quality_score=result.overall_quality_score,
        duration_seconds=result.duration_seconds,
        final_output=result.final_output,
        error=result.error,
    )


@router.get("/running")
async def list_running_workflows():
    """List all running workflows."""
    running = []

    for orchestrator in [
        get_brown_paper_orchestrator(),
        get_migration_orchestrator(),
        get_green_paper_orchestrator(),
        get_quality_orchestrator(),
    ]:
        running.extend(orchestrator.list_running_workflows())

    return {"running_workflows": running, "count": len(running)}


# =============================================================================
# SSE STREAMING ENDPOINT
# =============================================================================


@router.get("/stream/{workflow_id}")
async def stream_workflow_progress(workflow_id: str):
    """
    Stream workflow progress via Server-Sent Events.

    Connect to this endpoint to receive real-time updates:
    - task_started
    - iteration_started
    - iteration_completed
    - progress_update
    - task_completed / task_failed
    """
    stream = get_global_stream()

    async def event_generator():
        try:
            async for event in stream.subscribe(workflow_id):
                yield event.to_sse()
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# QUESTION ENDPOINTS
# =============================================================================


@router.get("/migration/questions")
async def get_migration_questions():
    """Get the 8 strategic migration questions."""
    orchestrator = get_migration_orchestrator()
    return {"questions": orchestrator.get_questions()}


@router.get("/green-paper/questions")
async def get_green_paper_questions():
    """Get the 6 Green Paper vision questions."""
    orchestrator = get_green_paper_orchestrator()
    return {"questions": orchestrator.get_questions()}


# =============================================================================
# WORKFLOW STAGES INFO
# =============================================================================


@router.get("/brown-paper/stages")
async def get_brown_paper_stages():
    """Get Brown Paper workflow stage definitions."""
    orchestrator = get_brown_paper_orchestrator()
    return {
        "workflow_type": "brown_paper",
        "stages": [s.to_dict() for s in orchestrator.get_stages()],
    }


@router.get("/migration/stages")
async def get_migration_stages():
    """Get Migration workflow stage definitions."""
    orchestrator = get_migration_orchestrator()
    return {
        "workflow_type": "migration",
        "stages": [s.to_dict() for s in orchestrator.get_stages()],
    }


@router.get("/green-paper/stages")
async def get_green_paper_stages():
    """Get Green Paper workflow stage definitions."""
    orchestrator = get_green_paper_orchestrator()
    return {
        "workflow_type": "green_paper",
        "stages": [s.to_dict() for s in orchestrator.get_stages()],
    }


@router.get("/quality/stages")
async def get_quality_stages():
    """Get Quality workflow stage definitions."""
    orchestrator = get_quality_orchestrator()
    return {
        "workflow_type": "quality",
        "stages": [s.to_dict() for s in orchestrator.get_stages()],
    }
