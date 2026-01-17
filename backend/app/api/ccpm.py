"""
CCPM API - Week 79

REST API endpoints for Claude Code Project Management:
- Git Worktrees: Parallel agent workspaces
- GitHub Issues: Bidirectional synchronization
- PRD Decomposition: Automated work breakdown
- Task Recommendations: Intelligent prioritization
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.git_worktree_service import GitWorktreeService
from app.services.github_issues_service import GitHubIssuesService
from app.services.ccpm_orchestrator import CCPMOrchestrator
from app.services.ccpm_workflow_integration_service import (
    CCPMWorkflowIntegrationService,
    SUPPORTED_WORKFLOW_TYPES,
    WORKFLOW_WORKTREE_CONFIGS
)


router = APIRouter(prefix="/api/ccpm", tags=["CCPM"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

# Git Worktrees
class CreateWorktreeRequest(BaseModel):
    """Request to create a new worktree."""
    agent_id: str = Field(..., min_length=1, max_length=100)
    base_branch: str = Field(default="main")
    project_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class CommitRequest(BaseModel):
    """Request to commit changes."""
    message: str = Field(..., min_length=1, max_length=500)
    files: Optional[List[str]] = None


class MergeWorktreeRequest(BaseModel):
    """Request to merge a worktree."""
    target_branch: str = Field(default="main")
    delete_after: bool = True


class WorktreeResponse(BaseModel):
    """Worktree response."""
    id: str
    agent_id: str
    worktree_path: str
    base_branch: str
    work_branch: str
    status: str
    commit_count: int
    files_changed: int
    last_commit_sha: Optional[str]
    created_at: datetime


# Workflow Worktrees (Week 89)
class StartWorkflowSessionRequest(BaseModel):
    """Request to start a workflow worktree session."""
    workflow_type: str = Field(..., description="Type of workflow (GREEN_PAPER, BROWN_PAPER, MIGRATION, NEW_FEATURE, BUG)")
    project_id: int = Field(..., description="Project ID")
    context: Optional[Dict[str, Any]] = None


class CompletePhaseRequest(BaseModel):
    """Request to complete a workflow phase."""
    message: str = Field(..., min_length=1, max_length=500)
    files: Optional[List[str]] = None


class MergeWorkflowRequest(BaseModel):
    """Request to merge all workflow worktrees."""
    target_branch: Optional[str] = None


class WorkflowSessionResponse(BaseModel):
    """Workflow session response."""
    workflow_type: str
    project_id: int
    worktrees: List[Dict[str, Any]]
    status: str
    created_at: datetime


class WorkflowWorktreeResponse(BaseModel):
    """Workflow worktree response."""
    id: str
    agent_id: str
    phase: Optional[str]
    worktree_path: str
    work_branch: str
    status: str
    commit_count: int
    files_changed: int
    last_commit_sha: Optional[str]


# GitHub Issues
class SyncIssuesRequest(BaseModel):
    """Request to sync GitHub issues."""
    repo: str = Field(..., pattern=r"^[\w-]+/[\w.-]+$", description="owner/repo format")
    project_id: Optional[int] = None
    direction: str = Field(
        default="bidirectional",
        pattern="^(github_to_local|local_to_github|bidirectional)$"
    )
    labels_filter: Optional[List[str]] = None


class CreateIssueRequest(BaseModel):
    """Request to create a GitHub issue from task."""
    task_id: str
    task_type: str
    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1, max_length=10000)
    repo: str = Field(..., pattern=r"^[\w-]+/[\w.-]+$")
    project_id: Optional[int] = None
    labels: Optional[List[str]] = None


class ResolveConflictRequest(BaseModel):
    """Request to resolve a sync conflict."""
    repo: str
    issue_number: int
    resolution: str = Field(..., pattern="^(use_github|use_local)$")


class SyncResultResponse(BaseModel):
    """Sync operation result."""
    success: bool
    created: int
    updated: int
    conflicts: int
    errors: List[str]
    message: str


class GitHubIssueResponse(BaseModel):
    """GitHub issue response."""
    id: str
    github_repo: str
    github_issue_number: int
    title: str
    state: str
    labels: List[str]
    sync_status: str
    github_url: Optional[str]
    last_synced_at: Optional[datetime]


# PRD Decomposition
class DecomposePRDRequest(BaseModel):
    """Request to decompose a PRD."""
    title: str = Field(..., min_length=1, max_length=500)
    prd_content: str = Field(..., min_length=10, max_length=100000)
    project_id: Optional[int] = None
    agent: str = Field(default="peter")
    llm_model: Optional[str] = None


class DecompositionResponse(BaseModel):
    """PRD decomposition response."""
    id: str
    title: str
    status: str
    epics_count: int
    features_count: int
    stories_count: int
    tasks_count: int
    total_story_points: Optional[int]
    total_function_points: Optional[float]
    processing_time_ms: Optional[int]
    created_at: datetime


class DecompositionDetailResponse(DecompositionResponse):
    """Detailed decomposition with hierarchy."""
    epics: List[Dict[str, Any]]
    features: List[Dict[str, Any]]
    stories: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]


# Task Recommendations
class TaskRecommendationResponse(BaseModel):
    """Task recommendation response."""
    id: str
    task_title: str
    task_type: str
    priority_score: float
    reasoning: str
    recommended_agent: str
    estimated_hours: float
    impact_score: float
    urgency_score: float
    complexity_score: float
    dependencies_met: bool
    status: str


class AcceptRecommendationRequest(BaseModel):
    """Request to accept a recommendation."""
    accepted_by: str = Field(default="user")


# =============================================================================
# GIT WORKTREES ENDPOINTS
# =============================================================================

@router.post("/worktrees", response_model=WorktreeResponse, status_code=status.HTTP_201_CREATED)
async def create_worktree(
    request: CreateWorktreeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new git worktree for an agent."""
    service = GitWorktreeService(db)

    try:
        worktree_info = await service.create_worktree(
            agent_id=request.agent_id,
            base_branch=request.base_branch,
            project_id=request.project_id,
            metadata=request.metadata
        )

        worktree = await service.get_worktree(worktree_info.id)

        return WorktreeResponse(
            id=str(worktree.id),
            agent_id=worktree.agent_id,
            worktree_path=worktree.worktree_path,
            base_branch=worktree.base_branch,
            work_branch=worktree.work_branch,
            status=worktree.status,
            commit_count=worktree.commit_count or 0,
            files_changed=worktree.files_changed or 0,
            last_commit_sha=worktree.last_commit_sha,
            created_at=worktree.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/worktrees", response_model=List[WorktreeResponse])
async def list_worktrees(
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List active worktrees."""
    service = GitWorktreeService(db)
    worktrees = await service.list_active_worktrees(project_id=project_id)

    return [
        WorktreeResponse(
            id=str(w.id),
            agent_id=w.agent_id,
            worktree_path=w.worktree_path,
            base_branch=w.base_branch,
            work_branch=w.work_branch,
            status=w.status,
            commit_count=w.commit_count or 0,
            files_changed=w.files_changed or 0,
            last_commit_sha=w.last_commit_sha,
            created_at=w.created_at
        )
        for w in worktrees
    ]


@router.get("/worktrees/{worktree_id}/status")
async def get_worktree_status(
    worktree_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed worktree status."""
    service = GitWorktreeService(db)

    try:
        return await service.get_worktree_status(worktree_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/worktrees/{worktree_id}/commit")
async def commit_changes(
    worktree_id: UUID,
    request: CommitRequest,
    db: AsyncSession = Depends(get_db)
):
    """Commit changes in a worktree."""
    service = GitWorktreeService(db)

    try:
        return await service.commit_changes(
            worktree_id=worktree_id,
            message=request.message,
            files=request.files
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/worktrees/{worktree_id}/merge")
async def merge_worktree(
    worktree_id: UUID,
    request: MergeWorktreeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Merge worktree back to target branch."""
    service = GitWorktreeService(db)

    try:
        result = await service.merge_worktree(
            worktree_id=worktree_id,
            target_branch=request.target_branch,
            delete_after=request.delete_after
        )

        return {
            "success": result.success,
            "status": result.status,
            "merge_commit_sha": result.merge_commit_sha,
            "conflicts": result.conflicts,
            "message": result.message
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/worktrees/{worktree_id}/sync")
async def sync_worktree(
    worktree_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Sync worktree with base branch."""
    service = GitWorktreeService(db)

    try:
        return await service.sync_with_base(worktree_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/worktrees/{worktree_id}")
async def delete_worktree(
    worktree_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a worktree."""
    service = GitWorktreeService(db)
    success = await service.cleanup_worktree(worktree_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worktree {worktree_id} not found"
        )

    return {"deleted": True}


# =============================================================================
# WORKFLOW WORKTREES ENDPOINTS (Week 89)
# =============================================================================

@router.get("/workflow-worktrees/types")
async def get_supported_workflow_types():
    """Get supported workflow types for worktree integration."""
    return {
        "supported_types": SUPPORTED_WORKFLOW_TYPES,
        "configs": {
            wt: {
                "phases": config["phases"],
                "agents": config["agents"],
                "base_branch": config["base_branch"],
                "merge_strategy": config["merge_strategy"]
            }
            for wt, config in WORKFLOW_WORKTREE_CONFIGS.items()
        }
    }


@router.post("/workflow-worktrees/start", response_model=WorkflowSessionResponse)
async def start_workflow_session(
    request: StartWorkflowSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start a new worktree session for a workflow."""
    if request.workflow_type not in SUPPORTED_WORKFLOW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported workflow type: {request.workflow_type}. Supported: {SUPPORTED_WORKFLOW_TYPES}"
        )

    service = CCPMWorkflowIntegrationService(db)

    try:
        session = await service.start_workflow_session(
            workflow_type=request.workflow_type,
            project_id=request.project_id,
            context=request.context
        )

        return WorkflowSessionResponse(
            workflow_type=session.workflow_type,
            project_id=session.project_id,
            worktrees=[
                {
                    "id": str(wt.id),
                    "agent_id": wt.agent_id,
                    "worktree_path": wt.worktree_path,
                    "work_branch": wt.work_branch,
                    "status": wt.status
                }
                for wt in session.worktrees
            ],
            status=session.status,
            created_at=session.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/workflow-worktrees/{workflow_type}/{project_id}", response_model=List[WorkflowWorktreeResponse])
async def list_workflow_worktrees(
    workflow_type: str,
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all worktrees for a workflow session."""
    if workflow_type not in SUPPORTED_WORKFLOW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported workflow type: {workflow_type}"
        )

    service = CCPMWorkflowIntegrationService(db)
    worktrees = await service.list_workflow_worktrees(workflow_type, project_id)

    return [
        WorkflowWorktreeResponse(
            id=wt["id"],
            agent_id=wt["agent_id"],
            phase=wt.get("phase"),
            worktree_path=wt["worktree_path"],
            work_branch=wt["work_branch"],
            status=wt["status"],
            commit_count=wt.get("commit_count", 0),
            files_changed=wt.get("files_changed", 0),
            last_commit_sha=wt.get("last_commit_sha")
        )
        for wt in worktrees
    ]


@router.post("/workflow-worktrees/{worktree_id}/complete-phase")
async def complete_workflow_phase(
    worktree_id: UUID,
    request: CompletePhaseRequest,
    db: AsyncSession = Depends(get_db)
):
    """Complete a workflow phase by committing changes."""
    service = CCPMWorkflowIntegrationService(db)

    try:
        result = await service.complete_phase(
            worktree_id=worktree_id,
            message=request.message,
            files=request.files
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/workflow-worktrees/{workflow_type}/{project_id}/merge")
async def merge_workflow_session(
    workflow_type: str,
    project_id: int,
    request: MergeWorkflowRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """Merge all workflow worktrees back to target branch."""
    if workflow_type not in SUPPORTED_WORKFLOW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported workflow type: {workflow_type}"
        )

    service = CCPMWorkflowIntegrationService(db)

    try:
        target_branch = request.target_branch if request else None
        result = await service.merge_workflow_session(
            workflow_type=workflow_type,
            project_id=project_id,
            target_branch=target_branch
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/workflow-worktrees/{workflow_type}/{project_id}/sync")
async def sync_workflow_worktrees(
    workflow_type: str,
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Sync all workflow worktrees with their base branches."""
    if workflow_type not in SUPPORTED_WORKFLOW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported workflow type: {workflow_type}"
        )

    service = CCPMWorkflowIntegrationService(db)
    return await service.sync_workflow_worktrees(workflow_type, project_id)


@router.delete("/workflow-worktrees/{workflow_type}/{project_id}")
async def cleanup_workflow_session(
    workflow_type: str,
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cleanup all worktrees for a workflow session."""
    if workflow_type not in SUPPORTED_WORKFLOW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported workflow type: {workflow_type}"
        )

    service = CCPMWorkflowIntegrationService(db)
    return await service.cleanup_workflow_session(workflow_type, project_id)


@router.get("/workflow-worktrees/stats")
async def get_workflow_worktree_stats(
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get workflow worktree statistics."""
    service = CCPMWorkflowIntegrationService(db)
    return await service.get_workflow_statistics(project_id)


# =============================================================================
# GITHUB ISSUES ENDPOINTS
# =============================================================================

@router.post("/issues/sync", response_model=SyncResultResponse)
async def sync_github_issues(
    request: SyncIssuesRequest,
    db: AsyncSession = Depends(get_db)
):
    """Synchronize GitHub issues with local tasks."""
    service = GitHubIssuesService(db)

    result = await service.sync_issues(
        repo=request.repo,
        project_id=request.project_id,
        direction=request.direction,
        labels_filter=request.labels_filter
    )

    return SyncResultResponse(
        success=result.success,
        created=result.created,
        updated=result.updated,
        conflicts=result.conflicts,
        errors=result.errors,
        message=result.message
    )


@router.post("/issues/create")
async def create_github_issue(
    request: CreateIssueRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a GitHub issue from a local task."""
    service = GitHubIssuesService(db)

    try:
        issue = await service.create_issue_from_task(
            task_id=UUID(request.task_id),
            task_type=request.task_type,
            title=request.title,
            body=request.body,
            repo=request.repo,
            project_id=request.project_id,
            labels=request.labels
        )

        return {
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "url": issue.url
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/issues", response_model=List[GitHubIssueResponse])
async def list_synced_issues(
    repo: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List synced GitHub issues."""
    service = GitHubIssuesService(db)
    issues = await service.get_synced_issues(
        repo=repo,
        project_id=project_id,
        status=status,
        limit=limit
    )

    return [
        GitHubIssueResponse(
            id=str(i.id),
            github_repo=i.github_repo,
            github_issue_number=i.github_issue_number,
            title=i.title,
            state=i.state,
            labels=i.labels or [],
            sync_status=i.sync_status,
            github_url=i.github_url,
            last_synced_at=i.last_synced_at
        )
        for i in issues
    ]


@router.get("/issues/conflicts")
async def get_sync_conflicts(
    repo: str = Query(..., description="Repository in owner/repo format"),
    db: AsyncSession = Depends(get_db)
):
    """Detect sync conflicts between local and GitHub."""
    service = GitHubIssuesService(db)
    return await service.detect_conflicts(repo)


@router.post("/issues/resolve-conflict")
async def resolve_sync_conflict(
    request: ResolveConflictRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a sync conflict."""
    service = GitHubIssuesService(db)

    try:
        sync_record = await service.resolve_conflict(
            repo=request.repo,
            issue_number=request.issue_number,
            resolution=request.resolution
        )

        return {
            "resolved": True,
            "issue_number": sync_record.github_issue_number,
            "resolution": request.resolution,
            "sync_status": sync_record.sync_status
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# PRD DECOMPOSITION ENDPOINTS
# =============================================================================

@router.post("/prd/decompose", response_model=DecompositionDetailResponse)
async def decompose_prd(
    request: DecomposePRDRequest,
    db: AsyncSession = Depends(get_db)
):
    """Decompose a PRD into epics, features, stories, and tasks."""
    orchestrator = CCPMOrchestrator(db)

    try:
        result = await orchestrator.decompose_prd(
            title=request.title,
            prd_content=request.prd_content,
            project_id=request.project_id,
            agent=request.agent,
            llm_model=request.llm_model
        )

        return DecompositionDetailResponse(
            id=str(result.id),
            title=result.title,
            status="completed",
            epics_count=len(result.epics),
            features_count=len(result.features),
            stories_count=len(result.stories),
            tasks_count=len(result.tasks),
            total_story_points=result.total_story_points,
            total_function_points=result.total_function_points,
            processing_time_ms=result.processing_time_ms,
            created_at=datetime.now(timezone.utc),
            epics=result.epics,
            features=result.features,
            stories=result.stories,
            tasks=result.tasks
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/prd/decompositions", response_model=List[DecompositionResponse])
async def list_decompositions(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List PRD decompositions."""
    orchestrator = CCPMOrchestrator(db)
    decompositions = await orchestrator.list_decompositions(
        project_id=project_id,
        status=status,
        limit=limit
    )

    return [
        DecompositionResponse(
            id=str(d.id),
            title=d.title,
            status=d.status,
            epics_count=d.epics_count or 0,
            features_count=d.features_count or 0,
            stories_count=d.stories_count or 0,
            tasks_count=d.tasks_count or 0,
            total_story_points=d.total_story_points,
            total_function_points=d.total_function_points,
            processing_time_ms=d.processing_time_ms,
            created_at=d.created_at
        )
        for d in decompositions
    ]


@router.get("/prd/decompositions/{decomposition_id}", response_model=DecompositionDetailResponse)
async def get_decomposition(
    decomposition_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific decomposition."""
    orchestrator = CCPMOrchestrator(db)
    decomposition = await orchestrator.get_decomposition(decomposition_id)

    if not decomposition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decomposition {decomposition_id} not found"
        )

    hierarchy = decomposition.decomposition_result or {}

    return DecompositionDetailResponse(
        id=str(decomposition.id),
        title=decomposition.title,
        status=decomposition.status,
        epics_count=decomposition.epics_count or 0,
        features_count=decomposition.features_count or 0,
        stories_count=decomposition.stories_count or 0,
        tasks_count=decomposition.tasks_count or 0,
        total_story_points=decomposition.total_story_points,
        total_function_points=decomposition.total_function_points,
        processing_time_ms=decomposition.processing_time_ms,
        created_at=decomposition.created_at,
        epics=hierarchy.get("epics", []),
        features=hierarchy.get("features", []),
        stories=hierarchy.get("stories", []),
        tasks=hierarchy.get("tasks", [])
    )


@router.post("/prd/{decomposition_id}/create-recommendations")
async def create_recommendations_from_decomposition(
    decomposition_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Create task recommendations from a decomposition."""
    orchestrator = CCPMOrchestrator(db)

    try:
        recommendations = await orchestrator.create_recommendations_from_decomposition(
            decomposition_id
        )

        return {
            "created": len(recommendations),
            "recommendations": [str(r.id) for r in recommendations]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# TASK RECOMMENDATIONS ENDPOINTS
# =============================================================================

@router.get("/recommendations/next")
async def get_next_task(
    project_id: int = Query(...),
    agent_id: Optional[str] = Query(None),
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get the next recommended task."""
    orchestrator = CCPMOrchestrator(db)

    recommendation = await orchestrator.get_next_task(
        project_id=project_id,
        agent_id=agent_id,
        refresh=refresh
    )

    if not recommendation:
        return {"message": "No pending tasks available"}

    return TaskRecommendationResponse(
        id=str(recommendation.id),
        task_title=recommendation.task_title,
        task_type=recommendation.task_type,
        priority_score=recommendation.priority_score,
        reasoning=recommendation.reasoning,
        recommended_agent=recommendation.recommended_agent,
        estimated_hours=recommendation.estimated_hours,
        impact_score=recommendation.impact_score,
        urgency_score=recommendation.urgency_score,
        complexity_score=recommendation.complexity_score,
        dependencies_met=recommendation.dependencies_met,
        status="pending"
    )


@router.get("/recommendations", response_model=List[TaskRecommendationResponse])
async def list_recommendations(
    project_id: int = Query(...),
    agent_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """List ranked task recommendations."""
    orchestrator = CCPMOrchestrator(db)

    recommendations = await orchestrator.get_task_recommendations(
        project_id=project_id,
        agent_id=agent_id,
        limit=limit
    )

    return [
        TaskRecommendationResponse(
            id=str(r.id),
            task_title=r.task_title,
            task_type=r.task_type,
            priority_score=r.priority_score,
            reasoning=r.reasoning,
            recommended_agent=r.recommended_agent,
            estimated_hours=r.estimated_hours,
            impact_score=r.impact_score,
            urgency_score=r.urgency_score,
            complexity_score=r.complexity_score,
            dependencies_met=r.dependencies_met,
            status="pending"
        )
        for r in recommendations
    ]


@router.post("/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: UUID,
    request: AcceptRecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Accept a task recommendation."""
    orchestrator = CCPMOrchestrator(db)

    try:
        recommendation = await orchestrator.accept_recommendation(
            recommendation_id=recommendation_id,
            accepted_by=request.accepted_by
        )

        return {
            "accepted": True,
            "task_title": recommendation.task_title,
            "recommended_agent": recommendation.recommended_agent
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/recommendations/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Reject a task recommendation."""
    orchestrator = CCPMOrchestrator(db)

    try:
        await orchestrator.reject_recommendation(recommendation_id)
        return {"rejected": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# STATISTICS
# =============================================================================

@router.get("/stats")
async def get_ccpm_stats(
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get CCPM statistics."""
    worktree_service = GitWorktreeService(db)
    issues_service = GitHubIssuesService(db)
    orchestrator = CCPMOrchestrator(db)

    worktree_stats = await worktree_service.get_statistics()
    issues_stats = await issues_service.get_statistics()
    orchestrator_stats = await orchestrator.get_statistics(project_id)

    return {
        "worktrees": worktree_stats,
        "github_issues": issues_stats,
        "decompositions": orchestrator_stats["decompositions"],
        "recommendations": orchestrator_stats["recommendations"],
        "totals": {
            "story_points": orchestrator_stats["total_story_points"],
            "function_points": orchestrator_stats["total_function_points"]
        }
    }
