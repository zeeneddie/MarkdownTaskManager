"""
Application Registry API

Week 57 Day 1: API endpoints for hierarchical application management.

Supports:
- Multi-project monorepos
- Shared library detection
- Cross-project dependency tracking
- Application-level agent coordination
- Backlog to Kanban sync (Week 58+)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.services.application_registry_service import (
    get_application_registry_service,
    get_application_registry_service_async,
    Application,
    ApplicationComponent,
    ComponentType,
)
from app.services.backlog_service import get_backlog_service
from app.models.task_hierarchy import Epic, Feature, Story, Task, EpicStatus, FeatureStatus, StoryStatus, TaskStatus
from app.models.item import Item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["applications"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ScanApplicationRequest(BaseModel):
    """Request to scan an application directory."""
    name: str = Field(..., description="Application name")
    root_path: str = Field(..., description="Path to application root directory")
    description: str = Field("", description="Application description")
    max_depth: int = Field(3, description="Max directory depth to scan")
    auto_create_agents: bool = Field(True, description="Auto-create agents for components")


class ScanResultResponse(BaseModel):
    """Response from scanning an application."""
    success: bool
    application_id: Optional[int] = None
    application_name: Optional[str] = None
    components_found: int
    libraries_found: int
    total_stacks: List[str]
    scan_time_ms: int
    errors: List[str] = []


class ComponentResponse(BaseModel):
    """Response with component details."""
    id: int
    name: str
    path: str
    component_type: str
    stacks: List[str]
    frameworks: Dict[str, List[str]]
    dependencies: List[int]
    dependents: List[int]
    agents: List[Dict[str, Any]]


class ApplicationResponse(BaseModel):
    """Response with full application details."""
    id: int
    name: str
    root_path: str
    description: str
    created_at: str
    application_type: str
    primary_stacks: List[str]
    components: List[ComponentResponse]


class ApplicationSummaryResponse(BaseModel):
    """Response with application summary."""
    id: int
    name: str
    root_path: str
    description: str
    created_at: str
    application_type: str
    primary_stacks: List[str]
    total_components: int
    components_by_type: Dict[str, int]
    total_agents: int
    agents_by_role: Dict[str, int]


class DependencyGraphResponse(BaseModel):
    """Response with dependency graph."""
    application: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    libraries: List[Dict[str, Any]]


class ComponentContextResponse(BaseModel):
    """Response with full component context."""
    component: Dict[str, Any]
    application: Dict[str, Any]
    dependencies: List[Dict[str, Any]]
    dependents: List[Dict[str, Any]]
    siblings: List[Dict[str, Any]]
    agents: List[Dict[str, Any]]


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/scan", response_model=ScanResultResponse)
async def scan_application(request: ScanApplicationRequest):
    """
    Scan a directory to discover and register all components.

    This is the main entry point for registering a multi-project application.
    It will:
    1. Scan the directory tree for components (projects, libraries, services)
    2. Detect technology stacks for each component
    3. Identify dependencies between components
    4. Create appropriate agents for each component

    **Example Request:**
    ```json
    {
      "name": "my-platform",
      "root_path": "/path/to/monorepo",
      "description": "E-commerce platform with frontend, backend, and shared libs",
      "max_depth": 3,
      "auto_create_agents": true
    }
    ```

    **Example Response:**
    ```json
    {
      "success": true,
      "application_id": 1,
      "components_found": 4,
      "libraries_found": 1,
      "total_stacks": ["python", "typescript"],
      "scan_time_ms": 150
    }
    ```
    """
    try:
        service = get_application_registry_service()

        result = service.scan_application(
            name=request.name,
            root_path=request.root_path,
            description=request.description,
            max_depth=request.max_depth,
            auto_create_agents=request.auto_create_agents,
        )

        # Persist to database for durability across server restarts
        if result.success and result.application:
            await service.save_application_to_database(result.application.id)

        return ScanResultResponse(
            success=result.success,
            application_id=result.application.id if result.application else None,
            application_name=result.application.name if result.application else None,
            components_found=result.components_found,
            libraries_found=result.libraries_found,
            total_stacks=result.total_stacks,
            scan_time_ms=result.scan_time_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.error(f"Application scan failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.get("/", response_model=List[ApplicationSummaryResponse])
async def list_applications():
    """
    List all registered applications with summary information.

    Applications are loaded from the database on first request.
    """
    try:
        service = await get_application_registry_service_async()
        applications = service.list_applications()

        return [
            ApplicationSummaryResponse(**service.get_application_summary(app.id))
            for app in applications
        ]

    except Exception as e:
        logger.error(f"Failed to list applications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list applications: {str(e)}",
        )


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(app_id: int):
    """
    Get detailed information about an application including all components.
    """
    try:
        service = get_application_registry_service()
        app = service.get_application(app_id)

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {app_id}",
            )

        return ApplicationResponse(
            id=app.id,
            name=app.name,
            root_path=app.root_path,
            description=app.description,
            created_at=app.created_at.isoformat(),
            application_type=app.application_type,
            primary_stacks=app.primary_stacks,
            components=[
                ComponentResponse(
                    id=comp.id,
                    name=comp.name,
                    path=comp.path,
                    component_type=comp.component_type.value,
                    stacks=comp.stacks,
                    frameworks=comp.frameworks,
                    dependencies=comp.dependencies,
                    dependents=comp.dependents,
                    agents=comp.agents,
                )
                for comp in app.components.values()
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application: {str(e)}",
        )


@router.get("/{app_id}/summary", response_model=ApplicationSummaryResponse)
async def get_application_summary(app_id: int):
    """
    Get a summary of the application structure.
    """
    try:
        service = get_application_registry_service()
        summary = service.get_application_summary(app_id)

        if "error" in summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=summary["error"],
            )

        return ApplicationSummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary: {str(e)}",
        )


@router.get("/{app_id}/dependencies", response_model=DependencyGraphResponse)
async def get_dependency_graph(app_id: int):
    """
    Get the dependency graph for an application.

    Returns nodes (components) and edges (dependencies) suitable
    for visualization.

    **Example Response:**
    ```json
    {
      "application": "my-platform",
      "nodes": [
        {"id": 1, "name": "backend", "type": "project", "stacks": ["python"]},
        {"id": 2, "name": "frontend", "type": "project", "stacks": ["typescript"]},
        {"id": 3, "name": "shared-types", "type": "library", "stacks": ["typescript"]}
      ],
      "edges": [
        {"from": 1, "to": 3, "type": "depends_on"},
        {"from": 2, "to": 3, "type": "depends_on"}
      ],
      "libraries": [
        {"id": 3, "name": "shared-types", "type": "library", "stacks": ["typescript"]}
      ]
    }
    ```
    """
    try:
        service = get_application_registry_service()
        graph = service.get_dependency_graph(app_id)

        if "error" in graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=graph["error"],
            )

        return DependencyGraphResponse(**graph)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dependencies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dependencies: {str(e)}",
        )


@router.get("/{app_id}/agents")
async def get_application_agents(app_id: int) -> List[Dict[str, Any]]:
    """
    Get all agents across all components in an application.

    Each agent includes its component information for context.
    """
    try:
        service = get_application_registry_service()
        agents = service.get_application_agents(app_id)

        if not agents:
            app = service.get_application(app_id)
            if not app:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Application not found: {app_id}",
                )

        return agents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agents: {str(e)}",
        )


@router.get("/{app_id}/components/{component_id}", response_model=ComponentResponse)
async def get_component(app_id: int, component_id: int):
    """
    Get detailed information about a specific component.
    """
    try:
        service = get_application_registry_service()
        component = service.get_component(app_id, component_id)

        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component not found: {component_id}",
            )

        return ComponentResponse(
            id=component.id,
            name=component.name,
            path=component.path,
            component_type=component.component_type.value,
            stacks=component.stacks,
            frameworks=component.frameworks,
            dependencies=component.dependencies,
            dependents=component.dependents,
            agents=component.agents,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get component: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get component: {str(e)}",
        )


@router.get("/{app_id}/components/{component_id}/context", response_model=ComponentContextResponse)
async def get_component_context(app_id: int, component_id: int):
    """
    Get full context for a component including dependencies and siblings.

    This endpoint provides the complete context that agents need
    to understand cross-project relationships.

    **Includes:**
    - Component details (stacks, frameworks, agents)
    - Application context (total stacks, type)
    - Dependencies (libraries and other components this depends on)
    - Dependents (components that depend on this)
    - Siblings (other components in the same application)
    """
    try:
        service = get_application_registry_service()
        context = service.get_component_context(app_id, component_id)

        if "error" in context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=context["error"],
            )

        return ComponentContextResponse(**context)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}",
        )


@router.get("/{app_id}/components/{component_id}/libraries")
async def get_component_libraries(app_id: int, component_id: int) -> List[Dict[str, Any]]:
    """
    Get all library components that a component depends on.

    Useful for understanding shared code dependencies.
    """
    try:
        service = get_application_registry_service()
        libraries = service.get_libraries_for_component(app_id, component_id)

        return [
            {
                "id": lib.id,
                "name": lib.name,
                "path": lib.path,
                "stacks": lib.stacks,
                "frameworks": lib.frameworks,
            }
            for lib in libraries
        ]

    except Exception as e:
        logger.error(f"Failed to get libraries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get libraries: {str(e)}",
        )


# ============================================================================
# BACKLOG ENDPOINTS
# ============================================================================

class BacklogSummaryResponse(BaseModel):
    """Response with backlog summary."""
    name: str
    status: str
    total_story_points: int
    total_function_points: int
    completed_story_points: int
    progress_percent: float
    statistics: Dict[str, Any]


class EpicResponse(BaseModel):
    """Response with epic details."""
    id: str
    title: str
    status: str
    priority: str
    story_points: int
    function_points: int
    features_count: int
    stories_count: int
    tasks_count: int
    path: str


class BacklogDetailResponse(BaseModel):
    """Response with full backlog details."""
    name: str
    status: str
    total_story_points: int
    total_function_points: int
    completed_story_points: int
    progress_percent: float
    epics: List[EpicResponse]
    statistics: Dict[str, Any]


# Nested response models for full hierarchy
class TaskNestedResponse(BaseModel):
    """Task with full details."""
    id: str
    title: str
    status: str
    priority: str
    story_points: int
    function_points: int
    category: str
    path: str


class StoryNestedResponse(BaseModel):
    """Story with nested tasks."""
    id: str
    title: str
    status: str
    priority: str
    story_points: int
    function_points: int
    path: str
    tasks: List[TaskNestedResponse] = []


class FeatureNestedResponse(BaseModel):
    """Feature with nested stories."""
    id: str
    title: str
    status: str
    path: str
    stories: List[StoryNestedResponse] = []


class EpicNestedResponse(BaseModel):
    """Epic with nested features."""
    id: str
    title: str
    status: str
    priority: str
    story_points: int
    function_points: int
    path: str
    features: List[FeatureNestedResponse] = []


class BacklogNestedResponse(BaseModel):
    """Response with full nested backlog hierarchy."""
    name: str
    status: str
    total_story_points: int
    total_function_points: int
    completed_story_points: int
    progress_percent: float
    epics: List[EpicNestedResponse]
    statistics: Dict[str, Any]


@router.get("/{app_id}/backlog", response_model=BacklogDetailResponse)
async def get_application_backlog(app_id: int):
    """
    Get the project backlog (epics/features/stories/tasks) for an application.

    Reads the markdown-based backlog from:
        {app_root}/doc/project/

    **Example Response:**
    ```json
    {
      "name": "HCI-CRS",
      "status": "ACTIVE",
      "total_story_points": 39,
      "total_function_points": 50,
      "completed_story_points": 0,
      "progress_percent": 0.0,
      "epics": [
        {
          "id": "EPIC-001-jeugdtraject-defaults",
          "title": "Default Inrichting Jeugdtraject",
          "status": "PLANNED",
          "story_points": 18,
          "features_count": 1,
          "stories_count": 2
        }
      ],
      "statistics": {
        "total_epics": 2,
        "total_features": 2,
        "total_stories": 6,
        "total_tasks": 8
      }
    }
    ```
    """
    try:
        # Get application to find root path (use async to load from database)
        app_service = await get_application_registry_service_async()
        app = app_service.get_application(app_id)

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {app_id}",
            )

        # Get backlog
        backlog_service = get_backlog_service()
        backlog = backlog_service.get_backlog(app.root_path)

        if not backlog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No backlog found for application {app_id}. Expected at: {app.root_path}/doc/project/",
            )

        # Convert epics to response format
        epics_response = []
        for epic in backlog.epics:
            stories_count = sum(len(f.stories) for f in epic.features)
            tasks_count = sum(len(s.tasks) for f in epic.features for s in f.stories)

            epics_response.append(EpicResponse(
                id=epic.id,
                title=epic.title,
                status=epic.status,
                priority=epic.priority,
                story_points=epic.story_points,
                function_points=epic.function_points,
                features_count=len(epic.features),
                stories_count=stories_count,
                tasks_count=tasks_count,
                path=epic.path,
            ))

        return BacklogDetailResponse(
            name=backlog.name,
            status=backlog.status,
            total_story_points=backlog.total_story_points,
            total_function_points=backlog.total_function_points,
            completed_story_points=backlog.completed_story_points,
            progress_percent=backlog.progress_percent,
            epics=epics_response,
            statistics=backlog.statistics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backlog: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backlog: {str(e)}",
        )


@router.get("/{app_id}/backlog/summary", response_model=BacklogSummaryResponse)
async def get_application_backlog_summary(app_id: int):
    """
    Get a summary of the project backlog for quick overview.

    Lighter endpoint for dashboard cards.
    """
    try:
        # Use async to load from database
        app_service = await get_application_registry_service_async()
        app = app_service.get_application(app_id)

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {app_id}",
            )

        backlog_service = get_backlog_service()
        backlog = backlog_service.get_backlog(app.root_path)

        if not backlog:
            # Return empty backlog summary
            return BacklogSummaryResponse(
                name=app.name,
                status="NO_BACKLOG",
                total_story_points=0,
                total_function_points=0,
                completed_story_points=0,
                progress_percent=0.0,
                statistics={},
            )

        return BacklogSummaryResponse(
            name=backlog.name,
            status=backlog.status,
            total_story_points=backlog.total_story_points,
            total_function_points=backlog.total_function_points,
            completed_story_points=backlog.completed_story_points,
            progress_percent=backlog.progress_percent,
            statistics=backlog.statistics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backlog summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backlog summary: {str(e)}",
        )


@router.get("/{app_id}/backlog/nested", response_model=BacklogNestedResponse)
async def get_application_backlog_nested(app_id: int):
    """
    Get the full nested backlog hierarchy for drill-down navigation.

    Returns complete epic → feature → story → task hierarchy for UI drill-down.

    **Example Response:**
    ```json
    {
      "name": "HCI-CRS",
      "status": "ACTIVE",
      "total_story_points": 39,
      "epics": [
        {
          "id": "EPIC-001",
          "title": "Default Inrichting Jeugdtraject",
          "features": [
            {
              "id": "FEATURE-001",
              "title": "Declarabele Streefminuten",
              "stories": [
                {
                  "id": "STORY-001",
                  "title": "Configuratie Declarabele Tijd",
                  "tasks": [
                    {"id": "TASK-001", "title": "Database Model"},
                    {"id": "TASK-002", "title": "API Endpoint"}
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
    ```
    """
    try:
        # Get application to find root path (use async to load from database)
        app_service = await get_application_registry_service_async()
        app = app_service.get_application(app_id)

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {app_id}",
            )

        # Get backlog
        backlog_service = get_backlog_service()
        backlog = backlog_service.get_backlog(app.root_path)

        if not backlog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No backlog found for application {app_id}. Expected at: {app.root_path}/doc/project/",
            )

        # Convert to nested response format
        epics_nested = []
        for epic in backlog.epics:
            features_nested = []
            for feature in epic.features:
                stories_nested = []
                for story in feature.stories:
                    tasks_nested = [
                        TaskNestedResponse(
                            id=task.id,
                            title=task.title,
                            status=task.status,
                            priority=task.priority,
                            story_points=task.story_points,
                            function_points=task.function_points,
                            category=task.category,
                            path=task.path,
                        )
                        for task in story.tasks
                    ]
                    stories_nested.append(StoryNestedResponse(
                        id=story.id,
                        title=story.title,
                        status=story.status,
                        priority=story.priority,
                        story_points=story.story_points,
                        function_points=story.function_points,
                        path=story.path,
                        tasks=tasks_nested,
                    ))
                features_nested.append(FeatureNestedResponse(
                    id=feature.id,
                    title=feature.title,
                    status=feature.status,
                    path=feature.path,
                    stories=stories_nested,
                ))
            epics_nested.append(EpicNestedResponse(
                id=epic.id,
                title=epic.title,
                status=epic.status,
                priority=epic.priority,
                story_points=epic.story_points,
                function_points=epic.function_points,
                path=epic.path,
                features=features_nested,
            ))

        return BacklogNestedResponse(
            name=backlog.name,
            status=backlog.status,
            total_story_points=backlog.total_story_points,
            total_function_points=backlog.total_function_points,
            completed_story_points=backlog.completed_story_points,
            progress_percent=backlog.progress_percent,
            epics=epics_nested,
            statistics=backlog.statistics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get nested backlog: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get nested backlog: {str(e)}",
        )


# ============================================================================
# BACKLOG TO KANBAN SYNC
# ============================================================================

class SyncResult(BaseModel):
    """Result of sync operation."""
    success: bool
    message: str
    epics_synced: int = 0
    features_synced: int = 0
    stories_synced: int = 0
    tasks_synced: int = 0
    errors: List[str] = Field(default_factory=list)


def map_status_to_story_status(status_str: str) -> str:
    """Map backlog status to StoryStatus."""
    status_map = {
        "NEW": StoryStatus.DRAFT,
        "ACTIVE": StoryStatus.DRAFT,
        "PLANNED": StoryStatus.READY,
        "IN_PROGRESS": StoryStatus.IN_PROGRESS,
        "COMPLETED": StoryStatus.DONE,
        "DONE": StoryStatus.DONE,
        "ANALYSE": StoryStatus.DRAFT,
        "ONTWIKKELING": StoryStatus.IN_PROGRESS,
        "TEST": StoryStatus.IN_REVIEW,
        "IMPLEMENTATIE": StoryStatus.IN_PROGRESS,
    }
    return status_map.get(status_str.upper(), StoryStatus.DRAFT)


def map_status_to_epic_status(status_str: str) -> str:
    """Map backlog status to EpicStatus."""
    status_map = {
        "NEW": EpicStatus.DRAFT,
        "ACTIVE": EpicStatus.IN_PROGRESS,
        "PLANNED": EpicStatus.PLANNED,
        "IN_PROGRESS": EpicStatus.IN_PROGRESS,
        "COMPLETED": EpicStatus.COMPLETED,
        "DONE": EpicStatus.COMPLETED,
    }
    return status_map.get(status_str.upper(), EpicStatus.DRAFT)


def to_fibonacci(n: int) -> int:
    """Round to nearest Fibonacci number (1, 2, 3, 5, 8, 13, 21)."""
    if n is None or n <= 0:
        return None
    fibonacci = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    # Find closest fibonacci
    closest = min(fibonacci, key=lambda x: abs(x - n))
    return closest


@router.post("/{app_id}/sync-to-kanban", response_model=SyncResult)
async def sync_backlog_to_kanban(
    app_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Sync application backlog from markdown files to Kanban database.

    This enables the 9-lane Kanban board to display stories and tasks
    from markdown-based project documentation.

    The sync:
    1. Reads epics/features/stories/tasks from markdown (doc/project/epics/)
    2. Creates or updates corresponding database records
    3. Links items to the project for Kanban filtering

    **Flow:**
    ```
    Markdown (doc/project/epics/EPIC-001/...)
         ↓ BacklogService reads
    ProjectBacklog dataclass
         ↓ This endpoint syncs
    Database (Epic, Feature, Story, Task tables)
         ↓ Kanban API reads
    9-Lane Kanban Board
    ```
    """
    try:
        # Get application
        app_service = await get_application_registry_service_async()
        app = app_service.get_application(app_id)

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {app_id}",
            )

        # Get backlog from markdown
        backlog_service = get_backlog_service()
        backlog = backlog_service.get_backlog(app.root_path)

        if not backlog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No backlog found for application {app_id}. Expected at: {app.root_path}/doc/project/",
            )

        result = SyncResult(success=True, message="")
        project_id = f"app-{app_id}"  # Use app ID as project reference

        # Ensure project exists in items table (for FK reference)
        from app.models.item import ItemType as ItemTypeEnum
        existing_project = await db.execute(
            select(Item).where(Item.id == project_id)
        )
        if not existing_project.scalar_one_or_none():
            # Create project item (using EPIC type as it's the highest level)
            project_item = Item(
                id=project_id,
                type=ItemTypeEnum.EPIC,
                title=app.name,
                description=f"Project: {app.name}",
                status="active",
            )
            db.add(project_item)
            await db.flush()

        # Create dummy constitution and specification for FK constraints
        # (Epic requires specification_id, Specification requires constitution_id)
        from app.models.green_paper import Specification, Constitution, GreenPaperSession

        # First create session
        session_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"session-{app_id}")
        existing_session = await db.execute(
            select(GreenPaperSession).where(GreenPaperSession.id == session_id)
        )
        if not existing_session.scalar_one_or_none():
            session = GreenPaperSession(
                id=session_id,
                project_id=project_id,
                session_type="green-paper",
                status="completed",
            )
            db.add(session)
            await db.flush()

        # Then create constitution
        const_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"const-{app_id}")
        existing_const = await db.execute(
            select(Constitution).where(Constitution.id == const_id)
        )
        if not existing_const.scalar_one_or_none():
            const = Constitution(
                id=const_id,
                session_id=session_id,
                project_id=project_id,
                status="approved",
                content_json={"auto_generated": True, "app_name": app.name},
                content_markdown=f"# {app.name} Constitution\n\nAuto-generated for backlog sync.",
            )
            db.add(const)
            await db.flush()

        # Finally create specification
        spec_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"spec-{app_id}")
        existing_spec = await db.execute(
            select(Specification).where(Specification.id == spec_id)
        )
        if not existing_spec.scalar_one_or_none():
            spec = Specification(
                id=spec_id,
                constitution_id=const_id,
                project_id=project_id,
                status="approved",
                content_json={"auto_generated": True, "app_name": app.name},
                content_markdown=f"# {app.name} Specification\n\nAuto-generated for backlog sync.",
            )
            db.add(spec)
            await db.flush()

        # Sync epics
        for seq_num, epic_info in enumerate(backlog.epics, 1):
            try:
                epic_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{app_id}-{epic_info.id}")

                # Check if epic exists
                existing_epic = await db.execute(
                    select(Epic).where(Epic.id == epic_id)
                )
                epic = existing_epic.scalar_one_or_none()

                if epic:
                    # Update existing
                    epic.title = epic_info.title
                    epic.status = map_status_to_epic_status(epic_info.status)
                    epic.priority = epic_info.priority.lower()
                    epic.estimated_story_points = epic_info.story_points
                    epic.updated_at = datetime.utcnow()
                else:
                    # Create new
                    epic = Epic(
                        id=epic_id,
                        specification_id=spec_id,
                        project_id=project_id,
                        title=epic_info.title,
                        description=f"Epic from {epic_info.path}",
                        status=map_status_to_epic_status(epic_info.status),
                        priority=epic_info.priority.lower(),
                        estimated_story_points=epic_info.story_points,
                        sequence_number=seq_num,
                    )
                    db.add(epic)

                result.epics_synced += 1
                await db.flush()

                # Sync features
                for feat_seq, feature_info in enumerate(epic_info.features, 1):
                    try:
                        feature_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{app_id}-{feature_info.id}")

                        existing_feature = await db.execute(
                            select(Feature).where(Feature.id == feature_id)
                        )
                        feature = existing_feature.scalar_one_or_none()

                        if feature:
                            feature.title = feature_info.title
                            feature.status = map_status_to_epic_status(feature_info.status)
                            feature.updated_at = datetime.utcnow()
                        else:
                            feature = Feature(
                                id=feature_id,
                                epic_id=epic_id,
                                project_id=project_id,
                                title=feature_info.title,
                                description=f"Feature from {feature_info.path}",
                                status=map_status_to_epic_status(feature_info.status),
                                sequence_number=feat_seq,
                            )
                            db.add(feature)

                        result.features_synced += 1
                        await db.flush()

                        # Sync stories
                        for story_seq, story_info in enumerate(feature_info.stories, 1):
                            try:
                                story_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{app_id}-{story_info.id}")

                                existing_story = await db.execute(
                                    select(Story).where(Story.id == story_id)
                                )
                                story = existing_story.scalar_one_or_none()

                                # Convert to Fibonacci story points
                                fib_sp = to_fibonacci(story_info.story_points)

                                if story:
                                    story.title = story_info.title
                                    story.status = map_status_to_story_status(story_info.status)
                                    story.priority = story_info.priority.lower()
                                    story.story_points = fib_sp
                                    story.updated_at = datetime.utcnow()
                                else:
                                    story = Story(
                                        id=story_id,
                                        feature_id=feature_id,
                                        project_id=project_id,
                                        title=story_info.title,
                                        description=f"Story from {story_info.path}",
                                        status=map_status_to_story_status(story_info.status),
                                        priority=story_info.priority.lower(),
                                        story_points=fib_sp,
                                        sequence_number=story_seq,
                                        acceptance_criteria=[{"description": "Synced from markdown backlog"}],
                                    )
                                    db.add(story)

                                result.stories_synced += 1
                                await db.flush()

                                # Sync tasks
                                for task_seq, task_info in enumerate(story_info.tasks, 1):
                                    try:
                                        task_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{app_id}-{task_info.id}")

                                        existing_task = await db.execute(
                                            select(Task).where(Task.id == task_id)
                                        )
                                        task = existing_task.scalar_one_or_none()

                                        if task:
                                            task.title = task_info.title
                                            task.status = TaskStatus.TODO if task_info.status.upper() == "NEW" else TaskStatus.IN_PROGRESS
                                            task.priority = task_info.priority.lower()
                                            task.updated_at = datetime.utcnow()
                                        else:
                                            task = Task(
                                                id=task_id,
                                                story_id=story_id,
                                                project_id=project_id,
                                                title=task_info.title,
                                                description=f"Task from {task_info.path}",
                                                status=TaskStatus.TODO,
                                                priority=task_info.priority.lower(),
                                                sequence_number=task_seq,
                                            )
                                            db.add(task)

                                        result.tasks_synced += 1

                                    except Exception as e:
                                        result.errors.append(f"Task {task_info.id}: {str(e)}")

                            except Exception as e:
                                result.errors.append(f"Story {story_info.id}: {str(e)}")

                    except Exception as e:
                        result.errors.append(f"Feature {feature_info.id}: {str(e)}")

            except Exception as e:
                result.errors.append(f"Epic {epic_info.id}: {str(e)}")

        await db.commit()

        result.message = (
            f"Synced {result.epics_synced} epics, {result.features_synced} features, "
            f"{result.stories_synced} stories, {result.tasks_synced} tasks"
        )

        if result.errors:
            result.success = False
            result.message += f" with {len(result.errors)} errors"

        logger.info(f"Sync complete for app {app_id}: {result.message}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync backlog to kanban: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync backlog to kanban: {str(e)}",
        )


# ============================================================================
# GENERATE INITIAL BACKLOG (When no markdown exists)
# ============================================================================

# Template defaults for epic generation based on detected stack
TEMPLATE_EPICS = {
    "web-app": [
        ("Project Setup & Infrastructure", "Set up development environment, CI/CD, and infrastructure"),
        ("User Authentication", "Implement authentication, authorization, and session management"),
        ("Core Features", "Build the main application features"),
        ("Testing & QA", "Create test suites, documentation, and quality assurance"),
    ],
    "api-service": [
        ("API Foundation", "Set up API structure, routing, and base configuration"),
        ("Authentication & Authorization", "Implement API security, auth endpoints, and access control"),
        ("Core Endpoints", "Build the main API endpoints and business logic"),
        ("Documentation & Testing", "API documentation, tests, and performance benchmarks"),
    ],
    "migration": [
        ("Legacy Code Analysis", "Analyze and document existing codebase"),
        ("Migration Strategy", "Define migration approach and milestones"),
        ("Core Migration", "Execute primary code migration"),
        ("Data Migration", "Migrate data and database schemas"),
        ("Validation & Testing", "Validate functionality and performance"),
    ],
    "custom": [
        ("Project Setup", "Initialize project structure and tooling"),
        ("Core Implementation", "Implement main functionality"),
    ],
}


def detect_template_from_stacks(stacks: List[str], frameworks: Dict[str, List[str]]) -> str:
    """Map detected tech stack to template type."""
    stacks_lower = [s.lower() for s in stacks]
    all_frameworks = []
    for fw_list in frameworks.values():
        all_frameworks.extend([f.lower() for f in fw_list])

    # Check for migration signals (legacy tech stacks)
    legacy_markers = [
        "oracle", "progress", "vbscript", "cobol", "legacy",
        "asp_classic", "aspnet_webforms", "wcf", "vb6", "vb.net",
        "delphi", "powerbuilder", "foxpro", "clipper", "4gl"
    ]
    if any(s in stacks_lower for s in legacy_markers):
        return "migration"

    # Check for web frontend signals (modern frameworks)
    modern_frontend = ["nextjs", "react", "vue", "angular", "svelte", "vue3", "nuxt"]
    if any(f in all_frameworks for f in modern_frontend):
        return "web-app"
    if "typescript" in stacks_lower and "html" in stacks_lower:
        return "web-app"

    # Check for API backend signals
    api_frameworks = ["fastapi", "flask", "django", "express", "gin", "echo", "fiber", "actix"]
    if any(f in all_frameworks for f in api_frameworks):
        return "api-service"
    if "python" in stacks_lower or "go" in stacks_lower or "rust" in stacks_lower:
        return "api-service"

    return "custom"


class GenerateBacklogResult(BaseModel):
    """Response from generating initial backlog."""
    success: bool
    message: str
    template_used: str
    epics_generated: int = 0
    features_generated: int = 0
    errors: List[str] = []


@router.post("/{app_id}/generate-initial-backlog", response_model=GenerateBacklogResult)
async def generate_initial_backlog(
    app_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate initial backlog (epics/features) when no markdown backlog exists.

    This provides starter epics based on detected tech stack, enabling
    projects without existing documentation to begin with structured planning.

    **Flow:**
    ```
    Detected Tech Stack (from scan)
         ↓ Template selection
    TEMPLATE_EPICS (web-app, api-service, migration, custom)
         ↓ This endpoint creates
    Database (Epic, Feature records)
         ↓ Kanban API reads
    9-Lane Kanban Board
    ```

    Use this endpoint as fallback when sync-to-kanban returns 0 epics.
    """
    try:
        # Get application
        app_service = await get_application_registry_service_async()
        app = app_service.get_application(app_id)

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {app_id}",
            )

        # Detect template from stacks (using primary_stacks from Application)
        stacks = app.primary_stacks or []
        # Collect frameworks from all components
        frameworks: Dict[str, List[str]] = {}
        for comp in app.components.values():
            for stack, fw_list in comp.frameworks.items():
                if stack not in frameworks:
                    frameworks[stack] = []
                frameworks[stack].extend(fw_list)
        template = detect_template_from_stacks(stacks, frameworks)

        result = GenerateBacklogResult(
            success=True,
            message="",
            template_used=template,
        )

        project_id = f"app-{app_id}"

        # Ensure project exists in items table (for FK reference)
        from app.models.item import ItemType as ItemTypeEnum
        existing_project = await db.execute(
            select(Item).where(Item.id == project_id)
        )
        if not existing_project.scalar_one_or_none():
            project_item = Item(
                id=project_id,
                type=ItemTypeEnum.EPIC,
                title=app.name,
                description=f"Project: {app.name}",
                status="active",
            )
            db.add(project_item)
            await db.flush()

        # Create session/constitution/specification FK chain
        from app.models.green_paper import Specification, Constitution, GreenPaperSession

        session_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"session-{app_id}")
        existing_session = await db.execute(
            select(GreenPaperSession).where(GreenPaperSession.id == session_id)
        )
        if not existing_session.scalar_one_or_none():
            session = GreenPaperSession(
                id=session_id,
                project_id=project_id,
                session_type="auto-generated",
                status="completed",
            )
            db.add(session)
            await db.flush()

        const_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"const-{app_id}")
        existing_const = await db.execute(
            select(Constitution).where(Constitution.id == const_id)
        )
        if not existing_const.scalar_one_or_none():
            const = Constitution(
                id=const_id,
                session_id=session_id,
                project_id=project_id,
                status="approved",
                content_json={"auto_generated": True, "template": template, "stacks": stacks},
                content_markdown=f"# {app.name} Constitution\n\nAuto-generated from template: {template}",
            )
            db.add(const)
            await db.flush()

        spec_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"spec-{app_id}")
        existing_spec = await db.execute(
            select(Specification).where(Specification.id == spec_id)
        )
        if not existing_spec.scalar_one_or_none():
            spec = Specification(
                id=spec_id,
                constitution_id=const_id,
                project_id=project_id,
                status="approved",
                content_json={"auto_generated": True, "template": template, "stacks": stacks},
                content_markdown=f"# {app.name} Specification\n\nAuto-generated from template: {template}",
            )
            db.add(spec)
            await db.flush()

        # Get template epics
        epic_templates = TEMPLATE_EPICS.get(template, TEMPLATE_EPICS["custom"])

        # Create epics
        for seq_num, (epic_title, epic_desc) in enumerate(epic_templates, 1):
            try:
                epic_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{app_id}-gen-epic-{seq_num}")

                existing_epic = await db.execute(
                    select(Epic).where(Epic.id == epic_id)
                )
                epic = existing_epic.scalar_one_or_none()

                if not epic:
                    epic = Epic(
                        id=epic_id,
                        specification_id=spec_id,
                        project_id=project_id,
                        title=epic_title,
                        description=epic_desc,
                        status=EpicStatus.DRAFT,
                        priority="medium",
                        estimated_story_points=13,  # Default estimate
                        sequence_number=seq_num,
                    )
                    db.add(epic)
                    await db.flush()

                result.epics_generated += 1

                # Create a default feature per epic
                feature_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{app_id}-gen-feature-{seq_num}")
                existing_feature = await db.execute(
                    select(Feature).where(Feature.id == feature_id)
                )
                if not existing_feature.scalar_one_or_none():
                    feature = Feature(
                        id=feature_id,
                        epic_id=epic_id,
                        project_id=project_id,
                        title=f"{epic_title} - Initial Work",
                        description=f"Initial feature for {epic_title}",
                        status=FeatureStatus.DRAFT,
                        sequence_number=1,
                    )
                    db.add(feature)
                    result.features_generated += 1

            except Exception as e:
                result.errors.append(f"Epic {seq_num}: {str(e)}")

        await db.commit()

        result.message = (
            f"Generated {result.epics_generated} epics and {result.features_generated} features "
            f"using template '{template}' for {app.name}"
        )

        if result.errors:
            result.success = False
            result.message += f" with {len(result.errors)} errors"

        logger.info(f"Generate backlog complete for app {app_id}: {result.message}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate initial backlog: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate initial backlog: {str(e)}",
        )
