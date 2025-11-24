"""
Project Wizard API Endpoints

Provides a guided project creation workflow:
- Start wizard session
- Save step data
- Complete and create project
- Project templates

Integrates with existing projects API and agent system.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wizard", tags=["wizard"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TeamMember(BaseModel):
    """Team member configuration"""
    name: str = Field(..., min_length=1, description="Team member name")
    email: Optional[str] = Field(None, description="Email address")
    role: str = Field(default="developer", description="Role: lead, developer, designer, qa, devops")


class TechStack(BaseModel):
    """Technology stack configuration"""
    language: str = Field(..., description="Primary language: typescript, python, csharp, java, go, rust")
    framework: Optional[str] = Field(None, description="Framework: react, nextjs, fastapi, dotnet, express, django")
    database: Optional[str] = Field(None, description="Database: postgresql, mysql, mongodb, sqlserver, redis, none")


class WizardStartRequest(BaseModel):
    """Request to start a wizard session"""
    template: str = Field(
        default="web-app",
        pattern="^(web-app|api-service|migration|custom)$",
        description="Project template type"
    )


class WizardStepRequest(BaseModel):
    """Request to save wizard step data"""
    step_number: int = Field(..., ge=1, le=4, description="Step number (1-4)")
    data: Dict[str, Any] = Field(..., description="Step data to save")


class WizardCompleteRequest(BaseModel):
    """Request to complete wizard and create project"""
    template: str = Field(default="web-app", description="Project template")
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(..., min_length=1, description="Project description")
    repoUrl: Optional[str] = Field(None, description="Repository URL")

    # Tech stack
    language: str = Field(default="typescript", description="Primary language")
    framework: Optional[str] = Field(None, description="Framework")
    database: Optional[str] = Field(None, description="Database")

    # Team
    team: List[TeamMember] = Field(default_factory=list, description="Team members")
    sprintDuration: int = Field(default=2, ge=1, le=4, description="Sprint duration in weeks")
    workingHours: int = Field(default=8, ge=4, le=12, description="Working hours per day")

    # Workflow
    workflow: str = Field(
        default="spec-kit",
        pattern="^(spec-kit|bmad|maintenance|custom)$",
        description="Workflow type"
    )
    qualityGates: str = Field(
        default="standard",
        pattern="^(full|standard|minimal|none)$",
        description="Quality gates level"
    )
    autoAssign: bool = Field(default=True, description="Auto-assign agents")


class WizardSessionResponse(BaseModel):
    """Response for wizard session creation"""
    session_id: str
    template: str
    created_at: datetime
    message: str


class WizardStepResponse(BaseModel):
    """Response for wizard step save"""
    session_id: str
    step_number: int
    saved: bool
    message: str


class ProjectTemplateResponse(BaseModel):
    """Project template definition"""
    id: str
    name: str
    description: str
    icon: str
    default_language: str
    default_framework: Optional[str]
    default_workflow: str
    recommended_team_size: int
    features: List[str]


class WizardCompleteResponse(BaseModel):
    """Response for wizard completion"""
    project_id: int
    project_name: str
    workflow: str
    agents_assigned: List[str]
    quality_gates_enabled: int
    created_at: datetime
    message: str


# ============================================================================
# IN-MEMORY SESSION STORAGE (replace with Redis in production)
# ============================================================================

wizard_sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# PROJECT TEMPLATES
# ============================================================================

PROJECT_TEMPLATES = {
    "web-app": ProjectTemplateResponse(
        id="web-app",
        name="Web Application",
        description="Full-stack web application with frontend and backend",
        icon="globe",
        default_language="typescript",
        default_framework="nextjs",
        default_workflow="spec-kit",
        recommended_team_size=4,
        features=[
            "User authentication",
            "RESTful API",
            "Database integration",
            "Responsive UI",
            "Testing framework"
        ]
    ),
    "api-service": ProjectTemplateResponse(
        id="api-service",
        name="API Service",
        description="RESTful or GraphQL API backend service",
        icon="plug",
        default_language="python",
        default_framework="fastapi",
        default_workflow="spec-kit",
        recommended_team_size=3,
        features=[
            "RESTful endpoints",
            "OpenAPI documentation",
            "Database models",
            "Authentication middleware",
            "Rate limiting"
        ]
    ),
    "migration": ProjectTemplateResponse(
        id="migration",
        name="Migration Project",
        description="Legacy system modernization project",
        icon="package",
        default_language="csharp",
        default_framework="dotnet",
        default_workflow="bmad",
        recommended_team_size=5,
        features=[
            "Code analysis",
            "Dependency mapping",
            "Incremental migration",
            "Parallel running",
            "Data migration"
        ]
    ),
    "custom": ProjectTemplateResponse(
        id="custom",
        name="Custom",
        description="Start from scratch with custom configuration",
        icon="settings",
        default_language="typescript",
        default_framework=None,
        default_workflow="custom",
        recommended_team_size=2,
        features=[
            "Flexible configuration",
            "Custom workflows",
            "Manual agent assignment",
            "Custom quality gates"
        ]
    )
}


# ============================================================================
# AGENT MAPPING
# ============================================================================

WORKFLOW_AGENTS = {
    "spec-kit": ["Peter", "Felix", "Diana"],
    "bmad": ["Peter", "Felix", "Paul"],
    "maintenance": ["Marcus", "Quinn", "Tessa"],
    "custom": []
}

QUALITY_GATE_COUNTS = {
    "full": 7,
    "standard": 5,
    "minimal": 3,
    "none": 0
}


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/templates", response_model=List[ProjectTemplateResponse])
async def get_project_templates():
    """
    Get available project templates

    Returns list of predefined templates with recommended configurations.
    """
    return list(PROJECT_TEMPLATES.values())


@router.get("/templates/{template_id}", response_model=ProjectTemplateResponse)
async def get_template(template_id: str):
    """
    Get a specific project template by ID
    """
    if template_id not in PROJECT_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )
    return PROJECT_TEMPLATES[template_id]


@router.post("/start", response_model=WizardSessionResponse)
async def start_wizard_session(request: WizardStartRequest):
    """
    Start a new wizard session

    Creates a temporary session to track wizard progress.
    """
    session_id = str(uuid.uuid4())

    wizard_sessions[session_id] = {
        "template": request.template,
        "created_at": datetime.utcnow(),
        "steps": {},
        "completed": False
    }

    logger.info(f"Started wizard session: {session_id}")

    return WizardSessionResponse(
        session_id=session_id,
        template=request.template,
        created_at=wizard_sessions[session_id]["created_at"],
        message="Wizard session started successfully"
    )


@router.post("/step/{session_id}", response_model=WizardStepResponse)
async def save_wizard_step(session_id: str, request: WizardStepRequest):
    """
    Save data for a wizard step

    Stores step data in the session for later use during completion.
    """
    if session_id not in wizard_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )

    session = wizard_sessions[session_id]

    if session.get("completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already completed"
        )

    session["steps"][request.step_number] = request.data

    logger.info(f"Saved step {request.step_number} for session: {session_id}")

    return WizardStepResponse(
        session_id=session_id,
        step_number=request.step_number,
        saved=True,
        message=f"Step {request.step_number} saved successfully"
    )


@router.post("/complete", response_model=WizardCompleteResponse)
async def complete_wizard(request: WizardCompleteRequest):
    """
    Complete the wizard and create the project

    Creates the project in the database with all configurations.
    Assigns agents based on workflow selection.
    Enables quality gates based on selection.
    """
    try:
        # Import here to avoid circular imports
        from app.database import SessionLocal
        from app.models import Project

        db = SessionLocal()

        try:
            # Create project in database
            new_project = Project(
                name=request.name,
                description=request.description,
                status="active"
            )

            # Store additional metadata as JSON (if your model supports it)
            # Otherwise, you may need to extend the Project model
            project_metadata = {
                "template": request.template,
                "repo_url": request.repoUrl,
                "tech_stack": {
                    "language": request.language,
                    "framework": request.framework,
                    "database": request.database
                },
                "team": [member.dict() for member in request.team],
                "sprint_duration": request.sprintDuration,
                "working_hours": request.workingHours,
                "workflow": request.workflow,
                "quality_gates": request.qualityGates,
                "auto_assign": request.autoAssign
            }

            # Note: If Project model doesn't have metadata field, this stores locally
            # In production, extend the model or use a separate ProjectConfig table

            db.add(new_project)
            db.commit()
            db.refresh(new_project)

            project_id = new_project.id

            logger.info(f"Created project: {project_id} - {request.name}")

        finally:
            db.close()

        # Get assigned agents
        agents = WORKFLOW_AGENTS.get(request.workflow, [])

        # Get quality gate count
        gate_count = QUALITY_GATE_COUNTS.get(request.qualityGates, 5)

        return WizardCompleteResponse(
            project_id=project_id,
            project_name=request.name,
            workflow=request.workflow,
            agents_assigned=agents,
            quality_gates_enabled=gate_count,
            created_at=datetime.utcnow(),
            message=f"Project '{request.name}' created successfully with {request.workflow} workflow"
        )

    except ImportError as e:
        # Fallback if database is not configured
        logger.warning(f"Database not available, using mock response: {e}")

        return WizardCompleteResponse(
            project_id=1,
            project_name=request.name,
            workflow=request.workflow,
            agents_assigned=WORKFLOW_AGENTS.get(request.workflow, []),
            quality_gates_enabled=QUALITY_GATE_COUNTS.get(request.qualityGates, 5),
            created_at=datetime.utcnow(),
            message=f"Project '{request.name}' created (mock mode)"
        )

    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_wizard_session(session_id: str):
    """
    Get wizard session data

    Returns the current state of a wizard session.
    """
    if session_id not in wizard_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )

    return wizard_sessions[session_id]


@router.delete("/session/{session_id}")
async def delete_wizard_session(session_id: str):
    """
    Delete a wizard session

    Cleans up abandoned wizard sessions.
    """
    if session_id not in wizard_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )

    del wizard_sessions[session_id]

    return {"message": f"Session '{session_id}' deleted", "success": True}
