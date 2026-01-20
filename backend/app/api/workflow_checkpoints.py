"""
API Routes for Workflow Checkpoints - Restartable Workflows.

Week 158 - Fase 24.6: Restartable Workflows

Provides endpoints for:
- Checking workflow status and progress
- Resuming failed workflows
- Restarting workflows from scratch
- Listing checkpoints (admin/monitoring)
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from app.services.checkpoint_service import get_checkpoint_service, CheckpointService
from app.models.workflow_checkpoint import (
    CheckpointStatus,
    CheckpointResponse,
    CheckpointStatusResponse,
    ResumeRequest,
    ResumeResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflow-checkpoints"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class WorkflowStatusResponse(BaseModel):
    """Response for workflow status endpoint."""
    workflow_id: str
    workflow_type: str
    status: str
    current_stage: Optional[str]
    stages_completed: int
    can_resume: bool
    resume_stage: Optional[str]
    has_error: bool
    last_error: Optional[str]
    retry_count: int
    started_at: Optional[str]
    last_checkpoint_at: Optional[str]


class CheckpointListResponse(BaseModel):
    """Response for listing checkpoints."""
    checkpoints: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class RestartResponse(BaseModel):
    """Response for restart operation."""
    success: bool
    message: str
    checkpoints_cleared: int


class SessionStatusResponse(BaseModel):
    """Response for all workflows in a session."""
    session_id: str
    workflows: List[WorkflowStatusResponse]
    total: int


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/{workflow_id}/status",
    response_model=WorkflowStatusResponse,
    summary="Get workflow status",
    description="Get the current status, progress, and resume information for a workflow.",
)
async def get_workflow_status(workflow_id: str):
    """
    Get workflow status and checkpoint information.

    Returns:
        - Current status (running, paused, completed, failed, cancelled)
        - Progress (current stage, completed stages count)
        - Resume information (can_resume, resume_stage)
        - Error information if applicable
    """
    service = get_checkpoint_service()
    status = await service.get_checkpoint_status(workflow_id)

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"No checkpoint found for workflow {workflow_id}"
        )

    return WorkflowStatusResponse(
        workflow_id=status.workflow_id,
        workflow_type=status.workflow_type,
        status=status.status,
        current_stage=status.current_stage,
        stages_completed=status.stages_completed,
        can_resume=status.can_resume,
        resume_stage=status.resume_stage,
        has_error=status.has_error,
        last_error=status.last_error,
        retry_count=status.retry_count,
        started_at=status.started_at,
        last_checkpoint_at=status.last_checkpoint_at,
    )


@router.post(
    "/{workflow_id}/resume",
    response_model=ResumeResponse,
    summary="Resume workflow from checkpoint",
    description="Resume a failed or paused workflow from its last checkpoint.",
)
async def resume_workflow(
    workflow_id: str,
    request: ResumeRequest = ResumeRequest(),
):
    """
    Resume a workflow from its last checkpoint.

    Options:
        - skip_failed_stage: Skip the stage that failed and continue with the next
        - override_input: Provide new input data to override stored input

    Note: This endpoint prepares the checkpoint for resume. The actual execution
    should be triggered via the appropriate workflow endpoint with resume=true.
    """
    service = get_checkpoint_service()

    # Load checkpoint to verify it exists and can be resumed
    checkpoints = await service.list_checkpoints(
        workflow_type=None,
        status=None,
        limit=1,
    )

    # Find the specific workflow
    checkpoint = None
    all_checkpoints = await service.list_checkpoints(limit=1000)
    for cp in all_checkpoints:
        if cp.workflow_id == workflow_id:
            checkpoint = cp
            break

    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"No checkpoint found for workflow {workflow_id}"
        )

    if not checkpoint.can_resume:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow {workflow_id} cannot be resumed (status: {checkpoint.status})"
        )

    # Prepare for resume
    restored = await service.prepare_for_resume(
        session_id=checkpoint.session_id,
        workflow_type=checkpoint.workflow_type,
        workflow_id=workflow_id,
        skip_failed_stage=request.skip_failed_stage,
    )

    if not restored:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare workflow {workflow_id} for resume"
        )

    return ResumeResponse(
        success=True,
        message=f"Workflow {workflow_id} prepared for resume from stage {checkpoint.resume_stage}",
        checkpoint_id=checkpoint.id,
        resume_from_stage=checkpoint.resume_stage,
        workflow_id=workflow_id,
    )


@router.post(
    "/{workflow_id}/restart",
    response_model=RestartResponse,
    summary="Restart workflow from scratch",
    description="Clear all checkpoints for a workflow and allow fresh start.",
)
async def restart_workflow(workflow_id: str):
    """
    Clear all checkpoints for a workflow, allowing a fresh start.

    This is useful when:
        - You want to re-run a workflow from the beginning
        - The checkpoint data has become corrupted
        - Requirements have changed significantly
    """
    service = get_checkpoint_service()

    # Find the checkpoint to get session_id and workflow_type
    all_checkpoints = await service.list_checkpoints(limit=1000)
    checkpoint = None
    for cp in all_checkpoints:
        if cp.workflow_id == workflow_id:
            checkpoint = cp
            break

    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"No checkpoint found for workflow {workflow_id}"
        )

    # Clear checkpoints
    deleted = await service.clear_checkpoints(
        session_id=checkpoint.session_id,
        workflow_type=checkpoint.workflow_type,
    )

    return RestartResponse(
        success=True,
        message=f"Cleared {deleted} checkpoint(s) for workflow {workflow_id}",
        checkpoints_cleared=deleted,
    )


@router.get(
    "/session/{session_id}/status",
    response_model=SessionStatusResponse,
    summary="Get all workflows for a session",
    description="Get status of all workflows associated with a session.",
)
async def get_session_workflows(session_id: str):
    """
    Get status of all workflows for a session.

    Useful for dashboards showing overall session progress.
    """
    service = get_checkpoint_service()
    checkpoints = await service.list_checkpoints(session_id=session_id)

    workflows = []
    for cp in checkpoints:
        workflows.append(WorkflowStatusResponse(
            workflow_id=cp.workflow_id,
            workflow_type=cp.workflow_type,
            status=cp.status,
            current_stage=cp.current_stage,
            stages_completed=cp.stages_completed_count,
            can_resume=cp.can_resume,
            resume_stage=cp.resume_stage,
            has_error=cp.has_error,
            last_error=cp.last_error,
            retry_count=cp.retry_count,
            started_at=cp.started_at.isoformat() if cp.started_at else None,
            last_checkpoint_at=cp.last_checkpoint_at.isoformat() if cp.last_checkpoint_at else None,
        ))

    return SessionStatusResponse(
        session_id=session_id,
        workflows=workflows,
        total=len(workflows),
    )


@router.get(
    "/checkpoints",
    response_model=CheckpointListResponse,
    summary="List all checkpoints (admin)",
    description="List all workflow checkpoints with optional filters. For admin/monitoring use.",
)
async def list_checkpoints(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
):
    """
    List all checkpoints with optional filters.

    Filters:
        - session_id: Only show checkpoints for this session
        - workflow_type: Only show checkpoints for this workflow type
        - status: Only show checkpoints with this status

    Pagination:
        - limit: Maximum number of results (1-200)
        - offset: Skip this many results
    """
    service = get_checkpoint_service()
    checkpoints = await service.list_checkpoints(
        session_id=session_id,
        workflow_type=workflow_type,
        status=status,
        limit=limit,
        offset=offset,
    )

    return CheckpointListResponse(
        checkpoints=[cp.to_dict() for cp in checkpoints],
        total=len(checkpoints),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/checkpoints/failed",
    response_model=CheckpointListResponse,
    summary="List failed checkpoints (monitoring)",
    description="List all failed workflow checkpoints for monitoring and alerting.",
)
async def list_failed_checkpoints(
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
):
    """
    List all failed checkpoints.

    Useful for:
        - Monitoring dashboards
        - Alerting systems
        - Identifying workflows that need attention
    """
    service = get_checkpoint_service()
    checkpoints = await service.list_failed_checkpoints(limit=limit)

    return CheckpointListResponse(
        checkpoints=[cp.to_dict() for cp in checkpoints],
        total=len(checkpoints),
        limit=limit,
        offset=0,
    )


@router.delete(
    "/checkpoints/{checkpoint_id}",
    summary="Delete a specific checkpoint",
    description="Delete a specific checkpoint by ID. Use with caution.",
)
async def delete_checkpoint(checkpoint_id: str):
    """
    Delete a specific checkpoint.

    Warning: This cannot be undone. The workflow will not be resumable after deletion.
    """
    # This would require adding a delete_by_id method to the service
    # For now, return not implemented
    raise HTTPException(
        status_code=501,
        detail="Delete by checkpoint ID not yet implemented. Use /restart endpoint instead."
    )
