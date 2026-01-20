"""
Enhanced Projects API - MarQed Integration

Provides endpoints for:
- Creating new projects (greenfield/brownfield)
- Starting MarQed sessions (green-paper/brown-paper)
- Running quality scans
- Managing project lifecycle

All project workflows are now project-first:
1. Create project (select type)
2. Run MarQed session (green or brown-paper)
3. Project becomes active
4. Start workflows (BUG, FEATURE, MAINTENANCE, etc.)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

# Note: ChromaService will be imported when implemented
# from app.services.chroma_service import get_chroma_service
from app.services.quality_scan_service import get_quality_scan_service
from app.database import get_db
from app.models.project import Project
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects-enhanced"])


# ==================== REQUEST/RESPONSE MODELS ====================

class ProjectCreateRequest(BaseModel):
    """Request to create a new project"""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    project_type: str = Field(..., pattern="^(greenfield|brownfield)$", description="Project type: greenfield or brownfield")
    codebase_path: Optional[str] = Field(None, description="Path to existing codebase (brownfield only)")


class ProjectResponse(BaseModel):
    """Project data response"""
    id: int
    name: str
    description: Optional[str]
    project_type: str
    project_status: str
    marqed_session_id: Optional[str]
    quality_scan_id: Optional[str]
    tech_stack: Optional[List[str]]
    created_at: datetime
    next_steps: List[str]


class GreenPaperSessionRequest(BaseModel):
    """Request to start a green-paper session"""
    facilitator: str = Field(..., description="Name of session facilitator")
    participants: List[str] = Field(default_factory=list, description="List of participant names")


class BrownPaperSessionRequest(BaseModel):
    """Request to start a brown-paper session"""
    facilitator: str = Field(..., description="Name of session facilitator")
    participants: List[str] = Field(default_factory=list, description="List of participant names")
    scan_id: str = Field(..., description="ID of quality scan to use")


class QualityScanRequest(BaseModel):
    """Request to run a quality scan"""
    codebase_path: str = Field(..., description="Path to codebase to scan")
    scan_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional scan configuration")


class QualityScanResponse(BaseModel):
    """Quality scan results summary"""
    scan_id: str
    project_id: int
    overall_score: int
    security_score: int
    quality_score: int
    test_coverage: int
    tech_debt_days: int
    total_violations: int
    top_violations: List[Dict[str, Any]]
    status: str
    scanned_at: datetime


class MarQedSessionResponse(BaseModel):
    """MarQed session execution response"""
    session_id: str
    project_id: int
    session_type: str
    workflow_status: str
    spec_kit_started: bool
    next_step: str


# ==================== API ENDPOINTS ====================

@router.post("/new", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(request: ProjectCreateRequest) -> ProjectResponse:
    """
    Create a new project (greenfield or brownfield)

    **Workflow**:
    - Greenfield: Creates project, returns "start_green_paper" as next step
    - Brownfield: Creates project, returns "start_quality_scan" as next step

    **Example Request**:
    ```json
    {
      "name": "Patient Portal v2.0",
      "description": "Modern patient engagement platform",
      "project_type": "greenfield"
    }
    ```

    **Example Response**:
    ```json
    {
      "id": 123,
      "name": "Patient Portal v2.0",
      "project_type": "greenfield",
      "project_status": "draft",
      "next_steps": [
        "Start MarQed green-paper session: POST /api/projects/123/green-paper"
      ]
    }
    ```
    """
    try:
        logger.info(f"Creating new {request.project_type} project: {request.name}")

        # TODO: Implement actual project creation in PostgreSQL
        # For now, placeholder response

        project_id = 123  # Placeholder

        # Determine next steps based on project type
        next_steps = []
        if request.project_type == "greenfield":
            next_steps = [
                f"Start MarQed green-paper session: POST /api/projects/{project_id}/green-paper",
                "Complete green-paper questions to define vision and scope",
                "System will then run Spec-Kit workflow automatically"
            ]
        else:  # brownfield
            next_steps = [
                f"Run quality scan: POST /api/projects/{project_id}/quality-scan",
                "Wait 5-15 minutes for scan to complete",
                f"Start MarQed brown-paper session: POST /api/projects/{project_id}/brown-paper"
            ]

        return ProjectResponse(
            id=project_id,
            name=request.name,
            description=request.description,
            project_type=request.project_type,
            project_status="draft",
            marqed_session_id=None,
            quality_scan_id=None,
            tech_stack=None,
            created_at=datetime.now(),
            next_steps=next_steps
        )

    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.post("/{project_id}/green-paper", response_model=MarQedSessionResponse)
async def start_green_paper_session(
    project_id: int,
    request: GreenPaperSessionRequest
) -> MarQedSessionResponse:
    """
    Start MarQed green-paper session for greenfield project

    This triggers the GREEN_PAPER_PROJECT workflow:
    1. MarQed facilitator guides session (6 questions)
    2. Generate green-paper.md document
    3. Store in ChromaDB
    4. Trigger Spec-Kit workflow (constitution → spec → tasks)
    5. Set project status to 'active'

    **Example Request**:
    ```json
    {
      "facilitator": "John Doe",
      "participants": ["Jane Smith", "Bob Johnson"]
    }
    ```

    **Example Response**:
    ```json
    {
      "session_id": "green-paper-123-2025-11-18",
      "project_id": 123,
      "session_type": "green-paper",
      "workflow_status": "started",
      "spec_kit_started": true,
      "next_step": "Wait for Spec-Kit completion (5-10 minutes)"
    }
    ```
    """
    try:
        logger.info(f"Starting green-paper session for project {project_id}")

        # TODO: Implement actual green-paper workflow
        # 1. Validate project exists and is greenfield
        # 2. Start GREEN_PAPER_PROJECT workflow via agent service
        # 3. Return session ID

        session_id = f"green-paper-{project_id}-{datetime.now().strftime('%Y-%m-%d')}"

        return MarQedSessionResponse(
            session_id=session_id,
            project_id=project_id,
            session_type="green-paper",
            workflow_status="started",
            spec_kit_started=False,  # Will be true after questions answered
            next_step="Complete green-paper questions via UI"
        )

    except Exception as e:
        logger.error(f"Failed to start green-paper session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start green-paper session: {str(e)}"
        )


@router.post("/{project_id}/brown-paper", response_model=MarQedSessionResponse)
async def start_brown_paper_session(
    project_id: int,
    request: BrownPaperSessionRequest
) -> MarQedSessionResponse:
    """
    Start MarQed brown-paper session for brownfield project

    Prerequisites: Quality scan MUST be completed first

    This triggers the BROWN_PAPER_PROJECT workflow:
    1. Load quality scan results from ChromaDB
    2. Pre-populate brown-paper form with scan data
    3. MarQed facilitator guides session (7 questions)
    4. Generate brown-paper.md document (includes scan summary)
    5. Store in ChromaDB
    6. Trigger Spec-Kit workflow with migration context
    7. Set project status to 'active'

    **Example Request**:
    ```json
    {
      "facilitator": "Jane Doe",
      "participants": ["John Smith", "Alice Brown"],
      "scan_id": "scan-456-2025-11-18"
    }
    ```

    **Example Response**:
    ```json
    {
      "session_id": "brown-paper-456-2025-11-18",
      "project_id": 456,
      "session_type": "brown-paper",
      "workflow_status": "started",
      "spec_kit_started": false,
      "next_step": "Complete brown-paper questions (scan data pre-loaded)"
    }
    ```
    """
    try:
        logger.info(f"Starting brown-paper session for project {project_id}")

        # TODO: Implement actual brown-paper workflow
        # 1. Validate project exists and is brownfield
        # 2. Validate quality scan exists
        # 3. Load scan results from ChromaDB
        # 4. Start BROWN_PAPER_PROJECT workflow via agent service
        # 5. Return session ID

        session_id = f"brown-paper-{project_id}-{datetime.now().strftime('%Y-%m-%d')}"

        return MarQedSessionResponse(
            session_id=session_id,
            project_id=project_id,
            session_type="brown-paper",
            workflow_status="started",
            spec_kit_started=False,
            next_step="Complete brown-paper questions (scan data pre-loaded)"
        )

    except Exception as e:
        logger.error(f"Failed to start brown-paper session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start brown-paper session: {str(e)}"
        )


@router.post("/{project_id}/quality-scan", response_model=QualityScanResponse)
async def run_quality_scan(
    project_id: int,
    request: QualityScanRequest
) -> QualityScanResponse:
    """
    Run quality scan on brownfield codebase

    This executes the complete quality gate suite:
    1. Code Metrics (LOC, complexity, duplication)
    2. Architecture Analysis (/architect command)
    3. Security Scan (/security OWASP Top 10)
    4. Quality Gates (42 validation rules)
    5. Test Coverage Analysis
    6. Dependency Audit
    7. Technical Debt Estimation

    Processing time: 5-15 minutes depending on codebase size

    Results are stored in ChromaDB for brown-paper session use.

    **Example Request**:
    ```json
    {
      "codebase_path": "/path/to/legacy/code",
      "scan_options": {
        "include_dependencies": true,
        "deep_analysis": true
      }
    }
    ```

    **Example Response**:
    ```json
    {
      "scan_id": "scan-456-2025-11-18",
      "project_id": 456,
      "overall_score": 65,
      "security_score": 58,
      "quality_score": 72,
      "test_coverage": 45,
      "tech_debt_days": 180,
      "total_violations": 287,
      "top_violations": [
        {
          "type": "SQL Injection",
          "severity": "critical",
          "count": 12,
          "description": "User input not sanitized"
        }
      ],
      "status": "completed",
      "scanned_at": "2025-11-18T10:30:00Z"
    }
    ```
    """
    db = next(get_db())
    try:
        logger.info(f"Starting quality scan for project {project_id}")

        # 1. Get project from database
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # 2. Validate codebase path
        codebase_path = request.codebase_path
        if not codebase_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="codebase_path is required"
            )

        # 3. Run quality scan using scanner registry
        scan_service = get_quality_scan_service()
        results = await scan_service.run_scan(
            project_path=codebase_path,
            tech_stack=project.tech_stack,  # Use project's configured tech stack
            scan_options=request.scan_options
        )

        # 4. Generate scan ID
        scan_id = f"scan-{project_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # 5. Update project with scan reference
        project.quality_scan_id = scan_id
        db.commit()

        logger.info(f"Quality scan completed: {scan_id}, {results['total_violations']} violations found")

        return QualityScanResponse(
            scan_id=scan_id,
            project_id=project_id,
            overall_score=results["scores"]["overall"],
            security_score=results["scores"]["security"],
            quality_score=results["scores"]["quality"],
            test_coverage=0,  # TODO: Add test coverage scanner
            tech_debt_days=results["tech_debt_days"],
            total_violations=results["total_violations"],
            top_violations=results["top_violations"],
            status="completed",
            scanned_at=datetime.now()
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid scan request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to run quality scan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run quality scan: {str(e)}"
        )
    finally:
        db.close()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int) -> ProjectResponse:
    """
    Get project details

    Returns complete project information including:
    - Project metadata
    - MarQed session status
    - Quality scan status (if brownfield)
    - Current status and next steps
    """
    try:
        logger.info(f"Getting project {project_id}")

        # TODO: Implement actual project retrieval from PostgreSQL

        # Placeholder response
        return ProjectResponse(
            id=project_id,
            name="Example Project",
            description="Example description",
            project_type="greenfield",
            project_status="draft",
            marqed_session_id=None,
            quality_scan_id=None,
            tech_stack=None,
            created_at=datetime.now(),
            next_steps=["Start MarQed session"]
        )

    except Exception as e:
        logger.error(f"Failed to get project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )


@router.put("/{project_id}/activate")
async def activate_project(project_id: int):
    """
    Activate a project after MarQed session and Spec-Kit completion

    This is called automatically after Spec-Kit workflow completes.

    Changes project_status from 'draft' to 'active'.
    """
    try:
        logger.info(f"Activating project {project_id}")

        # TODO: Implement actual project activation
        # 1. Validate project exists
        # 2. Validate MarQed session completed
        # 3. Validate Spec-Kit workflow completed
        # 4. Update project_status to 'active'
        # 5. Set activated_at timestamp

        return {
            "project_id": project_id,
            "status": "active",
            "message": "Project activated successfully. You can now start workflows (BUG, FEATURE, MAINTENANCE, etc.)"
        }

    except Exception as e:
        logger.error(f"Failed to activate project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate project: {str(e)}"
        )
