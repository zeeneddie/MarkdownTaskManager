"""
Projects API endpoints for new project creation and management
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import logging

from app.schemas.workflow import ProjectDefinitionRequest, ProjectDefinitionResult
from app.services.project_service import get_project_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/define", response_model=ProjectDefinitionResult, status_code=status.HTTP_201_CREATED)
async def define_new_project(
    request: ProjectDefinitionRequest
) -> ProjectDefinitionResult:
    """
    Define and create a new project

    This endpoint executes the complete PROJECT_DEFINITION workflow:

    **Workflow Steps:**
    1. Peter (Product Owner) - Business case & scope definition
    2. Felix (Feature Architect) - Architecture vision & tech stack
    3. Peter (Product Owner) - Epic breakdown from business goals
    4. Eliza (Estimation Engine) - Effort estimation per epic
    5. Paul (Project Lead) - Project plan, sprints, milestones
    6. Diana (Documentation Writer) - Complete project documentation

    **Results:**
    - Complete project charter
    - Architecture document
    - Epic breakdown with story points
    - Sprint plan with milestones
    - Project folder with all documentation

    **Example Request:**
    ```json
    {
      "project_name": "E-commerce Platform",
      "description": "Online shop with payment processing and inventory management",
      "business_goals": [
        "Increase online sales by 50%",
        "Reduce cart abandonment"
      ],
      "target_audience": "Small to medium businesses",
      "constraints": [
        "Budget: €50,000",
        "Timeline: 6 months",
        "Team: 5 developers"
      ]
    }
    ```

    **Example Response:**
    ```json
    {
      "project_name": "E-commerce Platform",
      "business_case": {
        "value": "Enables online sales channel",
        "roi": "150% over 12 months",
        "risks": ["Market competition", "Technical complexity"]
      },
      "architecture": {
        "tech_stack": ["FastAPI", "Vue.js", "PostgreSQL"],
        "patterns": ["RESTful API", "Repository pattern"]
      },
      "epics": [
        {
          "id": "EPIC-1",
          "title": "User Management System",
          "estimated_effort": 21
        }
      ],
      "folder_structure": {
        "created": true,
        "path": "projects/e-commerce-platform",
        "files": ["project.md", "README.md", "epics/"]
      }
    }
    ```
    """
    try:
        logger.info(f"New project definition request: {request.project_name}")

        project_service = get_project_service()
        result = await project_service.create_project(request)

        logger.info(f"Project defined successfully: {request.project_name}")

        return result

    except ValueError as e:
        # Project already exists or validation error
        logger.warning(f"Project definition failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Project definition error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to define project: {str(e)}"
        )


@router.get("/list")
async def list_projects() -> List[str]:
    """
    List all existing projects

    Returns a list of project folder names.

    **Example Response:**
    ```json
    [
      "e-commerce-platform",
      "mobile-app",
      "data-pipeline"
    ]
    ```
    """
    try:
        project_service = get_project_service()

        # List all directories in projects folder
        if not project_service.projects_base.exists():
            return []

        projects = [
            d.name for d in project_service.projects_base.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

        return sorted(projects)

    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.get("/{project_name}/info")
async def get_project_info(project_name: str) -> dict:
    """
    Get information about a specific project

    Returns project metadata and file structure.

    **Example Response:**
    ```json
    {
      "name": "e-commerce-platform",
      "path": "projects/e-commerce-platform",
      "files": [
        "project.md",
        "README.md",
        "epics/EPIC-1.md",
        "docs/PROJECT_PLAN.md"
      ],
      "created": "2025-11-13T10:00:00"
    }
    ```
    """
    try:
        project_service = get_project_service()
        project_path = project_service.projects_base / project_name

        if not project_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_name}"
            )

        # Collect all files recursively
        files = []
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(project_path)
                files.append(str(relative_path))

        return {
            "name": project_name,
            "path": str(project_path),
            "files": sorted(files),
            "created": project_path.stat().st_ctime
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project info: {str(e)}"
        )


# ========================================
# ASYNC PROJECT DEFINITION (Celery)
# ========================================

@router.post("/define/async", status_code=status.HTTP_202_ACCEPTED)
async def define_project_async(request: ProjectDefinitionRequest) -> dict:
    """
    Define a new project asynchronously using Celery

    This endpoint starts PROJECT_DEFINITION workflow in the background and immediately
    returns a task ID. Use GET /api/workflows/tasks/{task_id} to check status.

    **Use this for:**
    - Complex project definitions
    - Large project setups
    - Projects that need extensive planning

    **Example Request:**
    ```json
    {
      "project_name": "e-commerce-platform",
      "description": "Modern e-commerce platform with AI recommendations",
      "business_goals": [
        "Increase conversion rate by 20%",
        "Reduce cart abandonment by 30%"
      ],
      "target_audience": "Tech-savvy millennials and Gen Z shoppers"
    }
    ```

    **Returns:**
    ```json
    {
      "task_id": "xyz-789-abc-123",
      "status": "PENDING",
      "project_name": "e-commerce-platform",
      "message": "Project definition started",
      "check_status_url": "/api/workflows/tasks/xyz-789-abc-123"
    }
    ```
    """
    try:
        from app.tasks.workflow_tasks import execute_project_definition_async

        # Start async task
        task = execute_project_definition_async.delay(
            project_name=request.project_name,
            description=request.description,
            business_goals=request.business_goals,
            target_audience=request.target_audience,
            constraints=request.constraints,
            folder_path=request.folder_path,
            timeout=1800  # 30 minutes
        )

        return {
            "task_id": task.id,
            "status": "PENDING",
            "project_name": request.project_name,
            "message": "Project definition started in background",
            "check_status_url": f"/api/workflows/tasks/{task.id}"
        }

    except Exception as e:
        logger.error(f"Error starting async project definition: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start async project definition: {str(e)}"
        )
