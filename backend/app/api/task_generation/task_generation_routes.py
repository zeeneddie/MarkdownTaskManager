"""
Task Generation API Routes

REST API for hierarchical task generation from specifications:
- Generate epics from specifications
- Generate features from epics
- Generate stories from features
- Generate tasks from stories
- Query and update work items at all levels

Felix agent performs intelligent breakdown with estimation.

API prefix: /api/task-generation
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.task_generation.task_generation_service import TaskGenerationService
from app.services.agent_service import AgentService
from app.models.task_hierarchy import (
    Epic, Feature, Story, Task,
    EpicStatus, FeatureStatus, StoryStatus, TaskStatus,
    Priority
)
from sqlalchemy import select


router = APIRouter(prefix="/api/task-generation", tags=["Task Generation"])


# ========== Request/Response Models ==========

class GenerateEpicsRequest(BaseModel):
    """Request to generate epics from specification."""
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generation options (e.g., max_epics, focus_areas)")


class GenerateFeaturesRequest(BaseModel):
    """Request to generate features from epic."""
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GenerateStoriesRequest(BaseModel):
    """Request to generate stories from feature."""
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GenerateTasksRequest(BaseModel):
    """Request to generate tasks from story."""
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GenerateHierarchyRequest(BaseModel):
    """Request to generate complete hierarchy from specification."""
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EpicResponse(BaseModel):
    """Epic response model."""
    id: str
    specification_id: str
    project_id: str
    title: str
    description: str
    status: str
    priority: str
    business_value: Optional[str]
    user_personas: Optional[List[str]]
    acceptance_criteria: Optional[List[str]]
    estimated_story_points: Optional[int]
    estimated_weeks: Optional[int]
    sequence_number: int
    progress_percentage: int
    generated_by: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FeatureResponse(BaseModel):
    """Feature response model."""
    id: str
    epic_id: str
    project_id: str
    title: str
    description: str
    status: str
    priority: str
    technical_approach: Optional[str]
    complexity: Optional[str]
    estimated_story_points: Optional[int]
    estimated_days: Optional[int]
    sequence_number: int
    generated_by: str

    model_config = ConfigDict(from_attributes=True)


class StoryResponse(BaseModel):
    """Story response model."""
    id: str
    feature_id: str
    project_id: str
    title: str
    description: str
    user_type: Optional[str]
    status: str
    priority: str
    acceptance_criteria: List[Dict[str, Any]]
    story_points: Optional[int]
    estimated_hours: Optional[float]
    sprint_id: Optional[str]
    assigned_to: Optional[str]
    sequence_number: int
    is_blocked: bool

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    """Task response model."""
    id: str
    story_id: str
    project_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    task_type: Optional[str]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    sequence_number: int
    assigned_to: Optional[str]
    is_blocked: bool
    branch_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ========== Dependency Injection ==========

async def get_task_generation_service(
    db: AsyncSession = Depends(get_db)
) -> TaskGenerationService:
    """Dependency for TaskGenerationService."""
    agent_service = AgentService()
    return TaskGenerationService(db, agent_service)


# ========== Epic Generation Endpoints ==========

@router.post(
    "/specifications/{specification_id}/epics",
    status_code=status.HTTP_201_CREATED,
    summary="Generate epics from specification",
    response_description="Epics generated successfully"
)
async def generate_epics(
    specification_id: UUID,
    request: GenerateEpicsRequest,
    service: TaskGenerationService = Depends(get_task_generation_service)
):
    """
    Generate epics from an approved HLD specification.

    Felix agent analyzes the specification and breaks it down into
    3-7 high-level epics (major business capabilities).

    **Requirements**:
    - Specification must exist
    - Specification must be approved
    - Epics must not already exist for this specification

    **Returns**:
    - List of generated epics
    - Statistics
    - Next step recommendation
    """
    try:
        result = await service.generate_epics_from_specification(
            specification_id=specification_id,
            options=request.options
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate epics: {str(e)}"
        )


@router.get(
    "/epics/{epic_id}",
    response_model=EpicResponse,
    summary="Get epic details",
    response_description="Epic details retrieved"
)
async def get_epic(
    epic_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve detailed information about an epic.

    **Returns**:
    - Epic details including all fields
    - Status and progress information
    - Metadata
    """
    result = await db.execute(
        select(Epic).where(Epic.id == epic_id)
    )
    epic = result.scalar_one_or_none()

    if not epic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Epic {epic_id} not found"
        )

    return EpicResponse(
        id=str(epic.id),
        specification_id=str(epic.specification_id),
        project_id=epic.project_id,
        title=epic.title,
        description=epic.description,
        status=epic.status,
        priority=epic.priority,
        business_value=epic.business_value,
        user_personas=epic.user_personas,
        acceptance_criteria=epic.acceptance_criteria,
        estimated_story_points=epic.estimated_story_points,
        estimated_weeks=epic.estimated_weeks,
        sequence_number=epic.sequence_number,
        progress_percentage=epic.progress_percentage,
        generated_by=epic.generated_by,
        created_at=epic.created_at.isoformat()
    )


# ========== Feature Generation Endpoints ==========

@router.post(
    "/epics/{epic_id}/features",
    status_code=status.HTTP_201_CREATED,
    summary="Generate features from epic",
    response_description="Features generated successfully"
)
async def generate_features(
    epic_id: UUID,
    request: GenerateFeaturesRequest,
    service: TaskGenerationService = Depends(get_task_generation_service)
):
    """
    Generate features from an epic.

    Felix agent breaks down the epic into 5-15 specific features
    (user-facing capabilities).

    **Requirements**:
    - Epic must exist
    - Features must not already exist for this epic

    **Returns**:
    - List of generated features
    - Statistics
    - Next step recommendation
    """
    try:
        result = await service.generate_features_from_epic(
            epic_id=epic_id,
            options=request.options
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate features: {str(e)}"
        )


@router.get(
    "/features/{feature_id}",
    response_model=FeatureResponse,
    summary="Get feature details",
    response_description="Feature details retrieved"
)
async def get_feature(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed information about a feature."""
    result = await db.execute(
        select(Feature).where(Feature.id == feature_id)
    )
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )

    return FeatureResponse(
        id=str(feature.id),
        epic_id=str(feature.epic_id),
        project_id=feature.project_id,
        title=feature.title,
        description=feature.description,
        status=feature.status,
        priority=feature.priority,
        technical_approach=feature.technical_approach,
        complexity=feature.complexity,
        estimated_story_points=feature.estimated_story_points,
        estimated_days=feature.estimated_days,
        sequence_number=feature.sequence_number,
        generated_by=feature.generated_by
    )


# ========== Story Generation Endpoints ==========

@router.post(
    "/features/{feature_id}/stories",
    status_code=status.HTTP_201_CREATED,
    summary="Generate stories from feature",
    response_description="Stories generated successfully"
)
async def generate_stories(
    feature_id: UUID,
    request: GenerateStoriesRequest,
    service: TaskGenerationService = Depends(get_task_generation_service)
):
    """
    Generate user stories from a feature.

    Felix agent creates 3-10 user stories with acceptance criteria
    following the format: "As a [user], I want [goal] so that [benefit]"

    **Requirements**:
    - Feature must exist
    - Stories must not already exist for this feature

    **Returns**:
    - List of generated stories
    - Statistics
    - Next step recommendation
    """
    try:
        result = await service.generate_stories_from_feature(
            feature_id=feature_id,
            options=request.options
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate stories: {str(e)}"
        )


@router.get(
    "/stories/{story_id}",
    response_model=StoryResponse,
    summary="Get story details",
    response_description="Story details retrieved"
)
async def get_story(
    story_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed information about a user story."""
    result = await db.execute(
        select(Story).where(Story.id == story_id)
    )
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found"
        )

    return StoryResponse(
        id=str(story.id),
        feature_id=str(story.feature_id),
        project_id=story.project_id,
        title=story.title,
        description=story.description,
        user_type=story.user_type,
        status=story.status,
        priority=story.priority,
        acceptance_criteria=story.acceptance_criteria,
        story_points=story.story_points,
        estimated_hours=story.estimated_hours,
        sprint_id=story.sprint_id,
        assigned_to=story.assigned_to,
        sequence_number=story.sequence_number,
        is_blocked=story.is_blocked or False
    )


# ========== Task Generation Endpoints ==========

@router.post(
    "/stories/{story_id}/tasks",
    status_code=status.HTTP_201_CREATED,
    summary="Generate tasks from story",
    response_description="Tasks generated successfully"
)
async def generate_tasks(
    story_id: UUID,
    request: GenerateTasksRequest,
    service: TaskGenerationService = Depends(get_task_generation_service)
):
    """
    Generate technical tasks from a user story.

    Felix agent breaks down the story into 1-5 technical tasks
    (backend, frontend, database, testing, devops).

    **Requirements**:
    - Story must exist
    - Tasks must not already exist for this story

    **Returns**:
    - List of generated tasks
    - Statistics
    - Completion indicator
    """
    try:
        result = await service.generate_tasks_from_story(
            story_id=story_id,
            options=request.options
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tasks: {str(e)}"
        )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
    response_description="Task details retrieved"
)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed information about a task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    return TaskResponse(
        id=str(task.id),
        story_id=str(task.story_id),
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        task_type=task.task_type,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        sequence_number=task.sequence_number,
        assigned_to=task.assigned_to,
        is_blocked=task.is_blocked or False,
        branch_name=task.branch_name
    )


# ========== Complete Hierarchy Generation ==========

@router.post(
    "/specifications/{specification_id}/hierarchy",
    status_code=status.HTTP_201_CREATED,
    summary="Generate complete task hierarchy",
    response_description="Complete hierarchy generated"
)
async def generate_complete_hierarchy(
    specification_id: UUID,
    request: GenerateHierarchyRequest,
    service: TaskGenerationService = Depends(get_task_generation_service)
):
    """
    Generate complete task hierarchy from specification in one operation.

    This endpoint generates:
    - Epics from specification
    - Features from each epic
    - Stories from each feature
    - Tasks from each story

    **Warning**: This operation may take 2-5 minutes depending on specification size.

    **Requirements**:
    - Specification must exist and be approved
    - No hierarchy must exist yet for this specification

    **Returns**:
    - Complete hierarchy statistics
    - Total work item count
    - Breakdown by level
    """
    try:
        result = await service.generate_complete_hierarchy(
            specification_id=specification_id,
            options=request.options
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hierarchy: {str(e)}"
        )


# ========== Hierarchy Summary & Validation ==========

@router.get(
    "/specifications/{specification_id}/hierarchy/summary",
    summary="Get hierarchy summary for specification",
    response_description="Hierarchy statistics and limits"
)
async def get_hierarchy_summary(
    specification_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive hierarchy summary for a specification.

    Returns counts, limits, remaining capacity, and statistics for
    the entire task hierarchy under this specification.

    **Includes**:
    - Current counts (epics, features, stories, tasks)
    - Maximum limits per level
    - Remaining capacity
    - Average items per parent
    - Total story points

    **Use Cases**:
    - Check if you can create more items
    - See overall project breakdown
    - Monitor hierarchy balance
    """
    from app.services.task_generation.validation_service import get_validation_service

    try:
        validation_service = get_validation_service(db)
        summary = await validation_service.get_hierarchy_summary(str(specification_id))
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hierarchy summary: {str(e)}"
        )


# ========== Health Check ==========

@router.get(
    "/health",
    summary="Task generation workflow health check",
    response_description="Health status"
)
async def health_check():
    """
    Health check for task generation workflow.

    Returns service status and available endpoints.
    """
    return {
        "status": "healthy",
        "service": "task_generation",
        "version": "1.0",
        "endpoints": {
            "total": 12,  # Week 143: +2 Vector DB endpoints
            "generation": 5,
            "retrieval": 4,
            "vector_db": 2,
            "health": 1
        },
        "hierarchy_levels": ["Epic", "Feature", "Story", "Task"],
        "felix_agent": "ready"
    }


# ========== Week 143: Vector DB Context Endpoints ==========

@router.get(
    "/vector-context/{context_type}",
    summary="Get Vector DB context for task generation",
    response_description="Context from Vector DB for specified generation type"
)
async def get_vector_context(
    context_type: str,
    project_id: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Vector DB context for task generation.

    **Context Types**:
    - `epic`: Patterns for breaking down specs into epics
    - `feature`: API design, database patterns for features
    - `story`: User story examples, acceptance criteria
    - `task`: Implementation details, technical tasks

    **Returns**:
    - Implementation patterns
    - Technical details
    - Similar work items
    - Estimation guidance
    """
    valid_types = ["epic", "feature", "story", "task"]
    if context_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid context_type. Must be one of: {valid_types}"
        )

    try:
        agent_service = AgentService(ollama_base_url="http://localhost:11434")
        service = TaskGenerationService(db, agent_service, project_id=project_id)

        context = service.get_vector_context_for_type(context_type)

        if not context:
            return {
                "status": "no_context",
                "message": "No relevant context found in Vector DB",
                "context_type": context_type,
                "context": None
            }

        return {
            "status": "success",
            "context_type": context_type,
            "project_id": project_id,
            "context": context,
            "total_items": sum(len(v) for v in context.values() if isinstance(v, list))
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vector context: {str(e)}"
        )


@router.post(
    "/generate/epics/{specification_id}/with-context",
    summary="Generate epics with Vector DB context",
    response_description="Generated epics with context enhancement"
)
async def generate_epics_with_context(
    specification_id: UUID,
    request: GenerateEpicsRequest,
    project_id: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate epics from specification with Vector DB context.

    Same as regular epic generation, but with:
    - Pre-fetched architecture patterns
    - Similar epic examples
    - Estimation guidance from knowledge base

    Returns generation result with context usage info.
    """
    try:
        agent_service = AgentService(ollama_base_url="http://localhost:11434")
        service = TaskGenerationService(db, agent_service, project_id=project_id)

        # Fetch context first for reporting
        context = service.get_vector_context_for_type("epic")

        # Generate epics (context will be used internally if available)
        result = await service.generate_epics_from_specification(
            specification_id=specification_id,
            options=request.options
        )

        # Add context info to result
        result["vector_context_used"] = context is not None
        result["context_items"] = sum(len(v) for v in context.values() if isinstance(v, list)) if context else 0

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Epic generation failed: {str(e)}"
        )
