"""
Project Registration API

Week 56 Day 5: API endpoints for unified project registration
with automatic stack detection and agent creation.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.services.project_registration_service import (
    get_project_registration_service,
    ProjectConfig,
    RegistrationResult,
    RegisteredProject,
)
from app.services.extraction_integration_service import (
    get_extraction_integration_service,
    get_onboarding_integration,
    OnboardingExtractionResult,
    KanbanImportResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/project-registration", tags=["project-registration"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RegisterExistingRequest(BaseModel):
    """Request to register an existing project."""
    name: str = Field(..., description="Project display name")
    path: str = Field(..., description="Path to existing project directory")
    description: str = Field("", description="Project description")
    auto_create_agents: bool = Field(True, description="Auto-create stack agents")
    max_files: int = Field(1000, description="Max files to scan for detection")


class CreateNewProjectRequest(BaseModel):
    """Request to create a new project."""
    name: str = Field(..., description="Project name")
    description: str = Field("", description="Project description")
    stacks: Optional[List[str]] = Field(None, description="Initial stacks")
    template: str = Field("default", description="Project template")
    auto_create_agents: bool = Field(True, description="Auto-create stack agents")


class AddStackRequest(BaseModel):
    """Request to add a stack to a project."""
    stack: str = Field(..., description="Stack to add (e.g., python, typescript)")
    create_agents: bool = Field(True, description="Create agents for the stack")


class RefreshStacksRequest(BaseModel):
    """Request to refresh project stacks."""
    update_agents: bool = Field(True, description="Update agents based on detection")


class RegistrationResponse(BaseModel):
    """Response for registration operations."""
    success: bool
    message: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    stacks_detected: List[str] = []
    agents_created: int = 0
    detection_time_ms: int = 0
    errors: List[str] = []


class ProjectResponse(BaseModel):
    """Response with project details."""
    id: int
    name: str
    path: str
    description: str
    created_at: str
    stacks: List[str]
    agents: List[Dict[str, Any]]
    project_type: str
    frameworks: Dict[str, List[str]]


class ProjectSummaryResponse(BaseModel):
    """Response with project summary."""
    id: int
    name: str
    path: str
    description: str
    created_at: str
    stacks: List[str]
    project_type: str
    total_agents: int
    agents_by_role: Dict[str, int]
    frameworks: Dict[str, List[str]]


# ============================================================================
# EXTRACTION REQUEST/RESPONSE MODELS (Week 84)
# ============================================================================

class ExtractStoriesRequest(BaseModel):
    """Request to extract stories from a project."""
    tier: str = Field("FREE", description="Extraction tier: FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM")
    auto_import_to_kanban: bool = Field(True, description="Import extracted stories to kanban")
    target_lane: str = Field("BACKLOG", description="Initial kanban lane for imported items")
    levels: Optional[List[str]] = Field(None, description="Extraction levels: FUNCTION, CLASS, MODULE, SYSTEM")


class KanbanImportResultResponse(BaseModel):
    """Response for kanban import results."""
    success: bool
    items_created: int
    epics_created: int
    features_created: int
    stories_created: int
    tasks_created: int
    errors: List[str] = []
    kanban_item_ids: List[int] = []


class ExtractionResponse(BaseModel):
    """Response for extraction operations."""
    success: bool
    extraction_session_id: str
    stories_extracted: int
    tier_used: str
    confidence: float
    duration_ms: int
    kanban_import: Optional[KanbanImportResultResponse] = None
    errors: List[str] = []


class RegisterWithExtractionRequest(BaseModel):
    """Request to register project with automatic story extraction."""
    name: str = Field(..., description="Project display name")
    path: str = Field(..., description="Path to existing project directory")
    description: str = Field("", description="Project description")
    auto_create_agents: bool = Field(True, description="Auto-create stack agents")
    max_files: int = Field(1000, description="Max files to scan for detection")
    # Extraction options
    auto_extract_stories: bool = Field(False, description="Run story extraction after registration")
    extraction_tier: str = Field("FREE", description="Extraction tier if auto_extract_stories is True")
    auto_import_to_kanban: bool = Field(True, description="Import extracted stories to kanban")


class RegistrationWithExtractionResponse(BaseModel):
    """Response for registration with extraction."""
    registration: RegistrationResponse
    extraction: Optional[ExtractionResponse] = None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/register", response_model=RegistrationResponse)
async def register_existing_project(request: RegisterExistingRequest):
    """
    Register an existing project directory.

    Automatically detects technology stacks and creates appropriate agents.

    **Example:**
    ```json
    {
      "name": "my-python-api",
      "path": "/home/user/projects/my-python-api",
      "description": "FastAPI backend service",
      "auto_create_agents": true
    }
    ```

    **Returns:**
    - Detected stacks (python, typescript, etc.)
    - Created agents (backend_dev, code_reviewer, etc.)
    - Detection statistics
    """
    try:
        service = get_project_registration_service()

        result = service.register_existing_project(
            name=request.name,
            path=request.path,
            description=request.description,
            auto_create_agents=request.auto_create_agents,
            max_files=request.max_files,
        )

        return RegistrationResponse(
            success=result.success,
            message=result.message,
            project_id=result.project.id if result.project else None,
            project_name=result.project.name if result.project else None,
            stacks_detected=result.stacks_detected,
            agents_created=result.agents_created,
            detection_time_ms=result.detection_time_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/create", response_model=RegistrationResponse)
async def create_new_project(request: CreateNewProjectRequest):
    """
    Create a new project with specified stacks.

    Creates project directory structure and appropriate agents.

    **Example:**
    ```json
    {
      "name": "new-fullstack-app",
      "description": "React + FastAPI application",
      "stacks": ["python", "typescript"],
      "auto_create_agents": true
    }
    ```
    """
    try:
        service = get_project_registration_service()

        result = service.create_new_project(
            name=request.name,
            description=request.description,
            stacks=request.stacks,
            template=request.template,
            auto_create_agents=request.auto_create_agents,
        )

        return RegistrationResponse(
            success=result.success,
            message=result.message,
            project_id=result.project.id if result.project else None,
            project_name=result.project.name if result.project else None,
            stacks_detected=result.stacks_detected,
            agents_created=result.agents_created,
            detection_time_ms=result.detection_time_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.error(f"Project creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project creation failed: {str(e)}",
        )


@router.get("/projects", response_model=List[ProjectSummaryResponse])
async def list_registered_projects():
    """
    List all registered projects.

    Returns summary information for each project including
    stacks, agent counts, and frameworks.
    """
    try:
        service = get_project_registration_service()
        projects = service.list_projects()

        return [
            ProjectSummaryResponse(
                id=p.id,
                name=p.name,
                path=p.path,
                description=p.description,
                created_at=p.created_at.isoformat(),
                stacks=p.stacks,
                project_type=p.metadata.get("project_type", "unknown"),
                total_agents=len(p.agents),
                agents_by_role=_count_agents_by_role(p.agents),
                frameworks=p.metadata.get("frameworks", {}),
            )
            for p in projects
        ]

    except Exception as e:
        logger.error(f"Failed to list projects: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}",
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """
    Get detailed information about a registered project.
    """
    try:
        service = get_project_registration_service()
        project = service.get_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}",
            )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            path=project.path,
            description=project.description,
            created_at=project.created_at.isoformat(),
            stacks=project.stacks,
            agents=project.agents,
            project_type=project.metadata.get("project_type", "unknown"),
            frameworks=project.metadata.get("frameworks", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}",
        )


@router.get("/projects/{project_id}/summary", response_model=ProjectSummaryResponse)
async def get_project_summary(project_id: int):
    """
    Get a summary of project status.
    """
    try:
        service = get_project_registration_service()
        summary = service.get_project_summary(project_id)

        if "error" in summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=summary["error"],
            )

        return ProjectSummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project summary: {str(e)}",
        )


@router.get("/projects/{project_id}/agents")
async def get_project_agents(project_id: int) -> List[Dict[str, Any]]:
    """
    Get all agents for a project.
    """
    try:
        service = get_project_registration_service()
        agents = service.get_project_agents(project_id)

        if not agents and not service.get_project(project_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}",
            )

        return agents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project agents: {str(e)}",
        )


@router.post("/projects/{project_id}/stacks")
async def add_stack_to_project(project_id: int, request: AddStackRequest):
    """
    Add a new stack to an existing project.

    Creates appropriate agents for the new stack.

    **Example:**
    ```json
    {
      "stack": "rust",
      "create_agents": true
    }
    ```
    """
    try:
        service = get_project_registration_service()

        result = service.add_stack_to_project(
            project_id=project_id,
            stack=request.stack,
            create_agents=request.create_agents,
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to add stack: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add stack: {str(e)}",
        )


@router.delete("/projects/{project_id}/stacks/{stack}")
async def remove_stack_from_project(
    project_id: int,
    stack: str,
    remove_agents: bool = True,
):
    """
    Remove a stack from a project.

    Optionally removes associated agents.
    """
    try:
        service = get_project_registration_service()

        result = service.remove_stack_from_project(
            project_id=project_id,
            stack=stack,
            remove_agents=remove_agents,
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to remove stack: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove stack: {str(e)}",
        )


@router.post("/projects/{project_id}/refresh", response_model=RegistrationResponse)
async def refresh_project_stacks(project_id: int, request: RefreshStacksRequest):
    """
    Re-detect stacks for a project and update agents.

    Useful when project code has changed significantly.
    Adds agents for newly detected stacks and removes
    agents for stacks no longer present.
    """
    try:
        service = get_project_registration_service()

        result = service.refresh_project_stacks(
            project_id=project_id,
            update_agents=request.update_agents,
        )

        return RegistrationResponse(
            success=result.success,
            message=result.message,
            project_id=result.project.id if result.project else None,
            project_name=result.project.name if result.project else None,
            stacks_detected=result.stacks_detected,
            agents_created=result.agents_created,
            detection_time_ms=result.detection_time_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.error(f"Failed to refresh stacks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh stacks: {str(e)}",
        )


class DeleteResponse(BaseModel):
    """Response for delete operations."""
    success: bool
    message: str
    deleted: Dict[str, Any] = {}
    database_items_deleted: Dict[str, int] = {}


@router.delete("/projects/{project_id}", response_model=DeleteResponse)
async def delete_project(
    project_id: int,
    delete_files: bool = False,
    delete_database: bool = True,
):
    """
    Delete a project and all related data.

    **Parameters:**
    - project_id: Project ID to delete
    - delete_files: Also delete .project-config.json file (default: false)
    - delete_database: Also delete all related database records (default: true)

    **Deletes:**
    - Project from registry
    - Technical debt items and snapshots
    - Applications and components
    - Stack agents
    - All other related data (bugs, assessments, etc.)

    **Example:**
    DELETE /project-registration/projects/1?delete_database=true
    """
    try:
        # 1. Delete from database if requested
        db_deleted = {}
        if delete_database:
            from app.database import get_db
            db = next(get_db())
            try:
                # Get counts before deletion
                from sqlalchemy import text

                # Delete in correct order (foreign key dependencies)
                tables_to_clean = [
                    "technical_debt_items",
                    "technical_debt_snapshots",
                    "layered_analysis_sessions",
                    "project_assessments",
                    "bugs",
                    "stack_agents",
                    "components",
                    "applications",
                ]

                for table in tables_to_clean:
                    try:
                        result = db.execute(
                            text(f"DELETE FROM {table} WHERE project_id = :pid OR application_id IN (SELECT id FROM applications WHERE project_id = :pid)"),
                            {"pid": project_id}
                        )
                        db_deleted[table] = result.rowcount
                    except Exception as e:
                        # Some tables might not have project_id, try application_id only
                        try:
                            result = db.execute(
                                text(f"DELETE FROM {table} WHERE application_id IN (SELECT id FROM applications WHERE project_id = :pid)"),
                                {"pid": project_id}
                            )
                            db_deleted[table] = result.rowcount
                        except:
                            pass

                # Delete applications for this project
                result = db.execute(
                    text("DELETE FROM applications WHERE project_id = :pid"),
                    {"pid": project_id}
                )
                db_deleted["applications"] = result.rowcount

                # Finally delete the project
                result = db.execute(
                    text("DELETE FROM projects WHERE id = :pid"),
                    {"pid": project_id}
                )
                db_deleted["projects"] = result.rowcount

                db.commit()
                logger.info(f"Deleted database records for project {project_id}: {db_deleted}")
            except Exception as e:
                db.rollback()
                logger.error(f"Database deletion failed: {e}")
                raise
            finally:
                db.close()

        # 2. Delete from in-memory registry
        service = get_project_registration_service()
        result = service.delete_project(project_id, delete_files=delete_files)

        return DeleteResponse(
            success=True,
            message=f"Project {project_id} deleted successfully",
            deleted=result.get("deleted", {}),
            database_items_deleted=db_deleted,
        )

    except Exception as e:
        logger.error(f"Failed to delete project: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}",
        )


# ============================================================================
# STORY EXTRACTION ENDPOINTS (Week 84)
# ============================================================================

@router.post("/projects/{project_id}/extract-stories", response_model=ExtractionResponse)
async def extract_project_stories(project_id: int, request: ExtractStoriesRequest):
    """
    Extract user stories from a registered project.

    Uses hierarchical extraction to analyze code at multiple levels
    (function, class, module, system) and generate user stories.

    **Extraction Tiers:**
    - FREE: Local LLMs only, ~60% confidence
    - BASIC: +Groq/Qwen, ~70% confidence
    - STANDARD: +Gemini, ~80% confidence (recommended)
    - PROFESSIONAL: +GPT-5.2, ~90% confidence
    - PREMIUM: +Opus, ~95% confidence

    **Example:**
    ```json
    {
      "tier": "STANDARD",
      "auto_import_to_kanban": true,
      "target_lane": "BACKLOG"
    }
    ```
    """
    try:
        # Get project path
        reg_service = get_project_registration_service()
        project = reg_service.get_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}",
            )

        # Run extraction via database session
        from app.database import get_async_db

        async with get_async_db() as db:
            integration = get_extraction_integration_service(db)

            result = await integration.extract_and_import(
                project_id=project_id,
                repository_path=project.path,
                tier=request.tier,
                auto_import_to_kanban=request.auto_import_to_kanban,
                target_lane=request.target_lane,
                levels=request.levels,
            )

        # Convert to response
        kanban_response = None
        if result.kanban_import_result:
            kanban_response = KanbanImportResultResponse(
                success=result.kanban_import_result.success,
                items_created=result.kanban_import_result.items_created,
                epics_created=result.kanban_import_result.epics_created,
                features_created=result.kanban_import_result.features_created,
                stories_created=result.kanban_import_result.stories_created,
                tasks_created=result.kanban_import_result.tasks_created,
                errors=result.kanban_import_result.errors,
                kanban_item_ids=result.kanban_import_result.kanban_item_ids,
            )

        return ExtractionResponse(
            success=result.success,
            extraction_session_id=result.extraction_session_id,
            stories_extracted=result.stories_extracted,
            tier_used=result.tier_used,
            confidence=result.confidence,
            duration_ms=result.duration_ms,
            kanban_import=kanban_response,
            errors=result.errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Story extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Story extraction failed: {str(e)}",
        )


@router.post("/register-with-extraction", response_model=RegistrationWithExtractionResponse)
async def register_project_with_extraction(request: RegisterWithExtractionRequest):
    """
    Register a project and optionally extract stories in one call.

    Combines project registration with automatic story extraction.
    Useful for complete onboarding workflow.

    **Example:**
    ```json
    {
      "name": "my-project",
      "path": "/path/to/project",
      "description": "My FastAPI backend",
      "auto_extract_stories": true,
      "extraction_tier": "STANDARD",
      "auto_import_to_kanban": true
    }
    ```
    """
    try:
        # First register the project
        service = get_project_registration_service()

        reg_result = service.register_existing_project(
            name=request.name,
            path=request.path,
            description=request.description,
            auto_create_agents=request.auto_create_agents,
            max_files=request.max_files,
        )

        registration_response = RegistrationResponse(
            success=reg_result.success,
            message=reg_result.message,
            project_id=reg_result.project.id if reg_result.project else None,
            project_name=reg_result.project.name if reg_result.project else None,
            stacks_detected=reg_result.stacks_detected,
            agents_created=reg_result.agents_created,
            detection_time_ms=reg_result.detection_time_ms,
            errors=reg_result.errors,
        )

        # Run extraction if requested and registration succeeded
        extraction_response = None
        if request.auto_extract_stories and reg_result.success and reg_result.project:
            from app.database import get_async_db

            async with get_async_db() as db:
                integration = get_extraction_integration_service(db)

                ext_result = await integration.extract_and_import(
                    project_id=reg_result.project.id,
                    repository_path=request.path,
                    tier=request.extraction_tier,
                    auto_import_to_kanban=request.auto_import_to_kanban,
                    target_lane="BACKLOG",
                )

            kanban_response = None
            if ext_result.kanban_import_result:
                kanban_response = KanbanImportResultResponse(
                    success=ext_result.kanban_import_result.success,
                    items_created=ext_result.kanban_import_result.items_created,
                    epics_created=ext_result.kanban_import_result.epics_created,
                    features_created=ext_result.kanban_import_result.features_created,
                    stories_created=ext_result.kanban_import_result.stories_created,
                    tasks_created=ext_result.kanban_import_result.tasks_created,
                    errors=ext_result.kanban_import_result.errors,
                    kanban_item_ids=ext_result.kanban_import_result.kanban_item_ids,
                )

            extraction_response = ExtractionResponse(
                success=ext_result.success,
                extraction_session_id=ext_result.extraction_session_id,
                stories_extracted=ext_result.stories_extracted,
                tier_used=ext_result.tier_used,
                confidence=ext_result.confidence,
                duration_ms=ext_result.duration_ms,
                kanban_import=kanban_response,
                errors=ext_result.errors,
            )

        return RegistrationWithExtractionResponse(
            registration=registration_response,
            extraction=extraction_response,
        )

    except Exception as e:
        logger.error(f"Registration with extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration with extraction failed: {str(e)}",
        )


@router.post("/projects/{project_id}/import-session/{session_id}", response_model=KanbanImportResultResponse)
async def import_extraction_session_to_kanban(
    project_id: int,
    session_id: str,
    target_lane: str = "BACKLOG",
    min_confidence: float = 0.5,
):
    """
    Import an existing extraction session to kanban.

    Use this to import stories from a previous extraction that
    wasn't automatically imported.

    **Parameters:**
    - session_id: Extraction session UUID
    - target_lane: Initial kanban lane (BACKLOG, TODO, etc.)
    - min_confidence: Minimum confidence threshold (0.0-1.0)
    """
    try:
        from app.database import get_async_db

        async with get_async_db() as db:
            integration = get_extraction_integration_service(db)

            result = await integration.import_session_to_kanban(
                session_id=session_id,
                target_lane=target_lane,
                min_confidence=min_confidence,
            )

        return KanbanImportResultResponse(
            success=result.success,
            items_created=result.items_created,
            epics_created=result.epics_created,
            features_created=result.features_created,
            stories_created=result.stories_created,
            tasks_created=result.tasks_created,
            errors=result.errors,
            kanban_item_ids=result.kanban_item_ids,
        )

    except Exception as e:
        logger.error(f"Session import failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session import failed: {str(e)}",
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _count_agents_by_role(agents: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count agents by role."""
    counts = {}
    for agent in agents:
        role = agent.get("role", "unknown")
        counts[role] = counts.get(role, 0) + 1
    return counts
