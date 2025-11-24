"""
Task Generation API Endpoints
Week 23-24: Self-Questioning Agents

API for generating and managing agent training tasks.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.services.task_generation_service import TaskGenerationService
from app.schemas.task_generation import (
    GenerateTasksRequest, GenerateTasksResponse,
    TrainingTaskResponse, TrainingTaskListResponse, TrainingTaskQuery,
    TrainingTaskResultCreate, TrainingTaskResultResponse,
    SkillGapResponse, GetSkillGapsResponse,
    GenerationStrategyInput, GenerationStrategyResponse,
    TaskGenerationSummary,
    GeneratedTaskType, TaskStatus, TaskDifficulty, SkillGapSeverity
)

router = APIRouter(prefix="/api/task-generation", tags=["task-generation"])


def get_service(db: AsyncSession = Depends(get_db)) -> TaskGenerationService:
    """Dependency injection for task generation service."""
    return TaskGenerationService(db)


# =============================================================================
# Task Generation
# =============================================================================

@router.post("/generate", response_model=dict)
async def generate_tasks(
    request: GenerateTasksRequest,
    service: TaskGenerationService = Depends(get_service)
):
    """
    Generate training tasks for an agent.

    Analyzes recent attributions to identify skill gaps and generates
    appropriate training tasks based on the agent's strategy.
    """
    try:
        result = await service.generate_tasks(request)
        return {
            "tasks": [_task_to_response(t) for t in result["tasks"]],
            "skillGapsTargeted": [_gap_to_response(g) for g in result["skill_gaps_targeted"]],
            "estimatedTrainingTimeMs": result["estimated_training_time_ms"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Task Management
# =============================================================================

@router.get("/tasks", response_model=TrainingTaskListResponse)
async def list_tasks(
    agent_id: Optional[str] = Query(None, alias="agentId"),
    task_type: Optional[GeneratedTaskType] = Query(None, alias="taskType"),
    status: Optional[TaskStatus] = None,
    difficulty: Optional[TaskDifficulty] = None,
    min_priority: int = Query(0, alias="minPriority", ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    service: TaskGenerationService = Depends(get_service)
):
    """
    List training tasks with optional filtering.

    Supports filtering by agent, task type, status, difficulty, and priority.
    """
    query = TrainingTaskQuery(
        agent_id=agent_id,
        task_type=task_type,
        status=status,
        difficulty=difficulty,
        min_priority=min_priority,
        page=page,
        page_size=page_size
    )
    result = await service.list_tasks(query)
    return TrainingTaskListResponse(
        items=[_task_to_response(t) for t in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"]
    )


@router.get("/tasks/{task_id}", response_model=TrainingTaskResponse)
async def get_task(
    task_id: UUID,
    service: TaskGenerationService = Depends(get_service)
):
    """Get a specific training task by ID."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)


@router.post("/tasks/{task_id}/result", response_model=dict)
async def record_task_result(
    task_id: UUID,
    data: TrainingTaskResultCreate,
    service: TaskGenerationService = Depends(get_service)
):
    """
    Record the result of executing a training task.

    Updates task status and potentially marks skill gaps as addressed.
    """
    try:
        # Ensure task_id matches
        if data.task_id != task_id:
            raise HTTPException(status_code=400, detail="Task ID mismatch")

        result = await service.record_result(data)
        return {
            "status": "recorded",
            "resultId": str(result.id),
            "taskId": str(result.task_id),
            "success": result.success
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Skill Gaps
# =============================================================================

@router.get("/skill-gaps", response_model=GetSkillGapsResponse)
async def get_skill_gaps(
    agent_id: str = Query(..., alias="agentId"),
    min_severity: Optional[SkillGapSeverity] = Query(None, alias="minSeverity"),
    include_addressed: bool = Query(False, alias="includeAddressed"),
    service: TaskGenerationService = Depends(get_service)
):
    """
    Get skill gaps for an agent.

    Can filter by severity and whether to include already addressed gaps.
    """
    result = await service.get_skill_gaps(agent_id, min_severity, include_addressed)
    return GetSkillGapsResponse(
        skill_gaps=[_gap_to_response(g) for g in result["skill_gaps"]],
        total_gaps=result["total_gaps"],
        critical_gaps=result["critical_gaps"],
        addressed_gaps=result["addressed_gaps"]
    )


# =============================================================================
# Strategy Management
# =============================================================================

@router.get("/strategy/{agent_id}", response_model=GenerationStrategyResponse)
async def get_strategy(
    agent_id: str,
    service: TaskGenerationService = Depends(get_service)
):
    """Get the generation strategy for an agent."""
    strategy = await service._get_or_create_strategy(agent_id)
    return _strategy_to_response(strategy)


@router.put("/strategy/{agent_id}", response_model=GenerationStrategyResponse)
async def update_strategy(
    agent_id: str,
    data: GenerationStrategyInput,
    service: TaskGenerationService = Depends(get_service)
):
    """Update the generation strategy for an agent."""
    try:
        strategy = await service.update_strategy(agent_id, data)
        return _strategy_to_response(strategy)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Summary & Health
# =============================================================================

@router.get("/summary", response_model=TaskGenerationSummary)
async def get_summary(
    service: TaskGenerationService = Depends(get_service)
):
    """Get task generation summary statistics."""
    return await service.get_summary()


@router.get("/health", response_model=dict)
async def health_check(
    service: TaskGenerationService = Depends(get_service)
):
    """Check task generation service health."""
    try:
        summary = await service.get_summary()
        return {
            "status": "healthy",
            "totalTasks": summary.total_tasks,
            "pendingTasks": summary.pending_tasks,
            "agentsActive": summary.agents_active
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# =============================================================================
# Response Transformers
# =============================================================================

def _task_to_response(task) -> TrainingTaskResponse:
    """Convert task model to response schema."""
    return TrainingTaskResponse(
        id=task.id,
        agent_id=task.agent_id,
        agent_name=task.agent_name,
        task_type=task.task_type,
        difficulty=task.difficulty,
        source=task.source,
        status=task.status,
        scenario_description=task.scenario_description,
        scenario_context=task.scenario_context or {},
        scenario_constraints=task.scenario_constraints or [],
        scenario_success_criteria=task.scenario_success_criteria or [],
        learning_objective=task.learning_objective or "",
        expected_success_rate=task.expected_success_rate or 0.7,
        target_skills=task.target_skills or [],
        parent_attribution_id=task.parent_attribution_id,
        skill_gap_id=task.skill_gap_id,
        priority=task.priority,
        estimated_duration_ms=task.estimated_duration_ms,
        execution_attempts=task.execution_attempts,
        max_attempts=task.max_attempts,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )


def _gap_to_response(gap) -> SkillGapResponse:
    """Convert skill gap model to response schema."""
    return SkillGapResponse(
        id=gap.id,
        agent_id=gap.agent_id,
        agent_name=gap.agent_name,
        description=gap.description,
        area=gap.area,
        severity=gap.severity,
        evidence=gap.evidence or [],
        addressed=gap.addressed,
        identified_at=gap.identified_at,
        addressed_at=gap.addressed_at
    )


def _strategy_to_response(strategy) -> GenerationStrategyResponse:
    """Convert strategy model to response schema."""
    return GenerationStrategyResponse(
        id=strategy.id,
        agent_id=strategy.agent_id,
        focus_areas=strategy.focus_areas or [],
        difficulty_preference=strategy.difficulty_preference,
        max_tasks_per_session=strategy.max_tasks_per_session,
        cooldown_period_ms=strategy.cooldown_period_ms,
        type_weights=strategy.type_weights or {},
        created_at=strategy.created_at,
        updated_at=strategy.updated_at
    )
