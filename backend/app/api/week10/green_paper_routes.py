"""
Green-Paper Workflow API Routes

FastAPI endpoints for BMAD green-paper workflow (Week 10):
- Session & Answer Management (4 endpoints)
- Constitution Management (5 endpoints)
- Specification Management (4 endpoints)
- Search & Discovery (1 endpoint)
"""

from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.project_profile import (
    ProjectProfile,
    ProjectSize,
    FocusArea,
    StrictnessLevel,
    get_preset_profile
)


# Type alias for flexible project ID (accepts UUID string or integer)
ProjectId = Union[str, int]


def normalize_project_id(project_id: ProjectId) -> str:
    """
    Normalize project_id to string format.
    - Integer IDs are converted to string
    - UUID strings are validated and kept as-is
    - Other string IDs (like "EPIC-001") are allowed
    """
    if isinstance(project_id, int):
        return str(project_id)

    project_id_str = str(project_id)

    # Only validate as UUID if it matches UUID pattern (8-4-4-4-12 hex chars)
    # This allows custom string IDs like "EPIC-001" or "EPIC-TEST-abc123"
    import re
    uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    if re.match(uuid_pattern, project_id_str):
        try:
            UUID(project_id_str)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {project_id_str}")

    return project_id_str

from app.database import get_db
from app.services.week10.green_paper_service import (
    GreenPaperService,
    GreenPaperValidationError,
    IncompleteSessionError,
    InvalidStatusError
)
from app.services.agent_service import AgentService
from app.services.chroma_service import ChromaService


router = APIRouter(prefix="/api/week10", tags=["Green-Paper Workflow"])


# ========== Request/Response Models ==========

class ProjectProfileConfig(BaseModel):
    """Configuration for project profile at session start."""
    size: str = Field(default="small", description="Project size: hobby, small, medium, large, enterprise")
    preset: Optional[str] = Field(default=None, description="Use preset: club_app, startup_mvp, saas_product, fintech, healthcare")
    focus_areas: Optional[Dict[str, str]] = Field(default=None, description="Focus area overrides: {area: strictness}")
    team_size: int = Field(default=2, ge=1, le=500)
    expected_users: int = Field(default=100, ge=1)
    budget_type: str = Field(default="volunteer", description="volunteer, startup, corporate, enterprise")
    timeline_weeks: int = Field(default=16, ge=0, le=520)


class StartSessionRequest(BaseModel):
    """Request to start green-paper session."""
    project_id: ProjectId = Field(..., description="Project ID (integer or UUID string)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    project_profile: Optional[ProjectProfileConfig] = Field(
        default=None,
        description="Project profile for agent configuration. Sets strictness levels for all agents throughout project lifecycle."
    )

    @field_validator('project_id', mode='before')
    @classmethod
    def validate_project_id(cls, v):
        return normalize_project_id(v)


class StartSessionResponse(BaseModel):
    """Response from starting session."""
    session_id: UUID
    project_id: str  # Changed to str to support both int and UUID
    status: str
    questions: List[Dict[str, Any]]
    created_at: str
    message: str


class SubmitAnswerRequest(BaseModel):
    """Request to submit answer."""
    question_number: int = Field(..., ge=1, le=6)
    answer: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator('answer')
    @classmethod
    def answer_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Answer cannot be empty")
        return v


class GenerateConstitutionRequest(BaseModel):
    """Request to generate constitution."""
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReviewConstitutionRequest(BaseModel):
    """Request to review constitution."""
    action: str = Field(..., pattern="^(approve|reject)$")
    feedback: str = Field(..., min_length=10)
    reviewed_by: str
    requested_changes: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_rejection_changes(self):
        if self.action == 'reject' and not self.requested_changes:
            raise ValueError("Rejection requires at least one requested change")
        return self


class RegenerateConstitutionRequest(BaseModel):
    """Request to regenerate constitution."""
    requested_changes: List[Dict[str, Any]]
    feedback: str = Field(..., min_length=10)


class GenerateSpecificationRequest(BaseModel):
    """Request to generate specification."""
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReviewSpecificationRequest(BaseModel):
    """Request to review specification."""
    action: str = Field(..., pattern="^(approve|reject)$")
    feedback: str = Field(..., min_length=10)
    reviewed_by: str
    requested_changes: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_rejection_changes(self):
        if self.action == 'reject' and not self.requested_changes:
            raise ValueError("Rejection requires at least one requested change")
        return self


class RegenerateSpecificationRequest(BaseModel):
    """Request to regenerate specification."""
    requested_changes: List[Dict[str, Any]]
    feedback: str = Field(..., min_length=10)


# ========== Dependency Injection ==========

async def get_green_paper_service(
    db: AsyncSession = Depends(get_db)
) -> GreenPaperService:
    """Dependency for GreenPaperService."""
    agent_service = AgentService()
    chroma_service = ChromaService()
    return GreenPaperService(db, agent_service, chroma_service)


# ========== Session & Answer Endpoints (4) ==========

@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
    summary="Start BMAD green-paper session",
    response_description="Session created with 6 questions"
)
async def start_green_paper_session(
    request: StartSessionRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Initialize a new BMAD green-paper session for a project.

    **Requirements**:
    - Project must exist
    - No active session already exists

    **Returns**: Session data with 6 BMAD questions

    **Example Request**:
    ```json
    {
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "metadata": {
        "initiated_by": "user_123"
      }
    }
    ```

    **Example Response**:
    ```json
    {
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "in_progress",
      "questions": [
        {
          "number": 1,
          "question": "What problem are you trying to solve?",
          "required": true,
          "min_length": 50,
          "max_length": 500
        }
      ],
      "created_at": "2025-11-19T10:00:00Z",
      "message": "BMAD session started successfully"
    }
    ```
    """
    try:
        # Build project profile from request
        profile_data = None
        if request.project_profile:
            profile = _build_profile_from_config(request.project_profile)
            profile_data = profile.to_dict()

        # Merge profile into metadata for storage
        metadata = request.metadata or {}
        if profile_data:
            metadata["project_profile"] = profile_data

        session = await service.start_session(
            project_id=request.project_id,
            metadata=metadata
        )

        # Add profile info to response
        if profile_data:
            session["project_profile"] = profile_data

        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    summary="Get green-paper session status",
    response_description="Session data with current progress"
)
async def get_session_status(
    session_id: UUID,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Retrieve current status of a green-paper session.

    **Returns**: Session data including all submitted answers and progress

    **Example Response**:
    ```json
    {
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "in_progress",
      "created_at": "2025-11-19T10:00:00Z",
      "completed_at": null,
      "answers": [
        {
          "question_number": 1,
          "answer": "We need to solve the problem of...",
          "created_at": "2025-11-19T10:05:00Z"
        }
      ],
      "progress": {
        "answered": 1,
        "remaining": 5,
        "percentage": 16.67,
        "required_remaining": 3,
        "is_complete": false
      },
      "questions": [...]
    }
    ```
    """
    try:
        session = await service.get_session(session_id=session_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.post(
    "/sessions/{session_id}/answers",
    summary="Submit answer to BMAD question",
    response_description="Answer accepted with progress update"
)
async def submit_answer(
    session_id: UUID,
    request: SubmitAnswerRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Submit or update an answer to a BMAD question.

    **Validation**:
    - Answer must not exceed max_length for question
    - Required questions (1-4) must be at least 50 characters
    - Optional questions (5-6) can be skipped

    **Returns**: Progress information and next question

    **Example Request**:
    ```json
    {
      "question_number": 1,
      "answer": "We are building a task management system to help software teams break down requirements into actionable tasks using AI assistance.",
      "metadata": {
        "submitted_by": "user_123"
      }
    }
    ```

    **Example Response**:
    ```json
    {
      "answer_id": "770e8400-e29b-41d4-a716-446655440000",
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "question_number": 1,
      "created_at": "2025-11-19T10:05:00Z",
      "updated_at": "2025-11-19T10:05:00Z",
      "progress": {
        "answered": 1,
        "remaining": 5,
        "percentage": 16.67,
        "required_remaining": 3,
        "is_complete": false
      },
      "next_question": 2,
      "message": "Answer submitted successfully"
    }
    ```
    """
    try:
        result = await service.submit_answer(
            session_id=session_id,
            question_number=request.question_number,
            answer=request.answer,
            metadata=request.metadata
        )
        return result
    except GreenPaperValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/statistics",
    summary="Get session statistics",
    response_description="Session and project statistics"
)
async def get_session_statistics(
    session_id: UUID,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Get statistics for a session including answer counts and constitution status.

    **Returns**: Statistics for the session and related entities

    **Example Response**:
    ```json
    {
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "answers": {
        "total": 4,
        "required": 4,
        "optional": 0
      },
      "constitutions": {
        "total": 1,
        "draft": 0,
        "approved": 1,
        "rejected": 0
      },
      "specifications": {
        "total": 1,
        "draft": 1,
        "approved": 0,
        "rejected": 0
      },
      "session_status": "completed",
      "created_at": "2025-11-19T10:00:00Z",
      "completed_at": "2025-11-19T10:30:00Z"
    }
    ```
    """
    try:
        stats = await service.get_session_statistics(session_id=session_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


# ========== Constitution Endpoints (5) ==========

@router.post(
    "/sessions/{session_id}/constitution",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate project constitution",
    response_description="Constitution generation task created"
)
async def generate_constitution(
    session_id: UUID,
    request: GenerateConstitutionRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Trigger Peter (Product Owner) to generate project constitution.

    **Requirements**:
    - All required questions (1-4) must be answered
    - Session must be completed

    **Process**:
    - Peter receives BMAD answers
    - Analyzes and generates comprehensive constitution
    - Returns async task for monitoring

    **Returns**: Task ID and workflow information

    **Example Request**:
    ```json
    {
      "options": {
        "generate_immediately": true,
        "include_optional_questions": true
      }
    }
    ```

    **Example Response**:
    ```json
    {
      "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "status": "draft",
      "workflow_id": "workflow_880e8400",
      "agent": "Peter",
      "model": "deepseek-r1:latest",
      "estimated_completion_time": "2-5 minutes",
      "message": "Constitution generation started"
    }
    ```
    """
    try:
        # Get project_id from session
        session = await service.get_session(session_id=session_id)
        project_id = session["project_id"]  # Keep as string, can be int or UUID

        result = await service.generate_constitution(
            project_id=project_id,
            session_id=session_id,
            options=request.options
        )
        return result
    except IncompleteSessionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate constitution: {str(e)}"
        )


@router.get(
    "/constitutions/{constitution_id}",
    summary="Get project constitution",
    response_description="Constitution data (JSON or Markdown)"
)
async def get_constitution(
    constitution_id: UUID,
    format: str = Query("json", pattern="^(json|markdown)$"),
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Retrieve project constitution by ID.

    **Query Parameters**:
    - `format`: Response format - 'json' or 'markdown' (default: json)

    **Returns**: Constitution data in requested format

    **Example Response (JSON)**:
    ```json
    {
      "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "status": "approved",
      "content": {
        "problem_statement": "...",
        "stakeholders": [...],
        "core_functionalities": [...],
        "success_criteria": [...],
        "technical_constraints": [...],
        "timeline": {...},
        "risks_and_assumptions": {...}
      },
      "word_count": 1250,
      "generated_by": "Peter",
      "generation_attempt": 1,
      "created_at": "2025-11-19T10:35:00Z",
      "reviewed_at": "2025-11-19T11:00:00Z",
      "reviewed_by": "user_123"
    }
    ```
    """
    try:
        # Get project_id from constitution
        from app.models.green_paper import Constitution
        result = await service.db.execute(
            select(Constitution).where(Constitution.id == constitution_id)
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found")

        project_id = constitution.project_id  # Keep as string - may be int ID or UUID

        constitution_data = await service.get_constitution(
            project_id=project_id,
            constitution_id=constitution_id,
            format=format
        )

        if format == "markdown":
            return Response(
                content=constitution_data["content"],
                media_type="text/markdown"
            )
        return constitution_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve constitution: {str(e)}"
        )


@router.post(
    "/constitutions/{constitution_id}/review",
    summary="Review constitution (approve/reject)",
    response_description="Review result with next step"
)
async def review_constitution(
    constitution_id: UUID,
    request: ReviewConstitutionRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    User reviews and approves or rejects the constitution.

    **Actions**:
    - `approve`: Constitution is approved, proceed to specification
    - `reject`: Constitution needs revision, Peter will regenerate

    **Approval**:
    - Returns next_step: generate_specification
    - Constitution status → approved

    **Rejection**:
    - Requires feedback and requested_changes
    - Returns next_step: regenerate_constitution
    - Constitution status → rejected

    **Example Request (Approve)**:
    ```json
    {
      "action": "approve",
      "feedback": "Excellent constitution, captures all requirements clearly",
      "reviewed_by": "user_123",
      "requested_changes": []
    }
    ```

    **Example Request (Reject)**:
    ```json
    {
      "action": "reject",
      "feedback": "Timeline is too aggressive",
      "reviewed_by": "user_123",
      "requested_changes": [
        {
          "section": "timeline",
          "field": "total_duration_weeks",
          "current_value": "40",
          "suggested_value": "52",
          "reason": "Need more time for testing phase"
        }
      ]
    }
    ```

    **Example Response (Approve)**:
    ```json
    {
      "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "status": "approved",
      "reviewed_at": "2025-11-19T11:00:00Z",
      "reviewed_by": "user_123",
      "next_step": "generate_specification",
      "next_actions": [
        "Call POST /api/week10/constitutions/{constitution_id}/specification to generate HLD",
        "Felix agent will create detailed technical specification"
      ],
      "message": "Constitution approved successfully"
    }
    ```
    """
    try:
        # Get project_id from constitution
        from app.models.green_paper import Constitution
        result = await service.db.execute(
            select(Constitution).where(Constitution.id == constitution_id)
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found")

        project_id = constitution.project_id  # Keep as string - may be int ID or UUID

        result = await service.review_constitution(
            project_id=project_id,
            constitution_id=constitution_id,
            action=request.action,
            feedback=request.feedback,
            reviewed_by=request.reviewed_by,
            requested_changes=request.requested_changes
        )
        return result
    except GreenPaperValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review constitution: {str(e)}"
        )


@router.post(
    "/constitutions/{constitution_id}/regenerate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate constitution with feedback",
    response_description="New constitution generation started"
)
async def regenerate_constitution(
    constitution_id: UUID,
    request: RegenerateConstitutionRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Regenerate constitution incorporating user feedback.

    **Requirements**:
    - Constitution must be rejected
    - Maximum 3 regeneration attempts allowed

    **Process**:
    - Peter receives original answers + user feedback + requested changes
    - Regenerates constitution with improvements
    - Returns new constitution record

    **Example Request**:
    ```json
    {
      "requested_changes": [
        {
          "section": "timeline",
          "field": "total_duration_weeks",
          "current_value": "40",
          "suggested_value": "52",
          "reason": "Need more time for testing phase"
        }
      ],
      "feedback": "Please adjust timeline to be more realistic"
    }
    ```

    **Example Response**:
    ```json
    {
      "constitution_id": "990e8400-e29b-41d4-a716-446655440000",
      "previous_constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "generation_attempt": 2,
      "max_attempts": 3,
      "attempts_remaining": 1,
      "status": "draft",
      "workflow_id": "workflow_990e8400",
      "message": "Constitution regeneration started (attempt #2)"
    }
    ```
    """
    try:
        # Get project_id from constitution
        from app.models.green_paper import Constitution
        result = await service.db.execute(
            select(Constitution).where(Constitution.id == constitution_id)
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found")

        project_id = constitution.project_id  # Keep as string - may be int ID or UUID

        result = await service.regenerate_constitution(
            project_id=project_id,
            constitution_id=constitution_id,
            requested_changes=request.requested_changes,
            feedback=request.feedback
        )
        return result
    except GreenPaperValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate constitution: {str(e)}"
        )


@router.post(
    "/constitutions/{constitution_id}/embeddings",
    summary="Store constitution embeddings",
    response_description="Embeddings stored successfully"
)
async def store_constitution_embeddings(
    constitution_id: UUID,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Store constitution in ChromaDB for semantic search.

    **Process**:
    - Extracts text from 5 key constitution sections
    - Generates embeddings using sentence-transformers (all-MiniLM-L6-v2)
    - Stores in project_constitutions collection

    **Returns**: Storage confirmation with metadata

    **Example Response**:
    ```json
    {
      "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "status": "stored",
      "collection": "project_constitutions",
      "embedding_model": "all-MiniLM-L6-v2",
      "embedding_dimensions": 384,
      "text_length": 1247,
      "sections_extracted": [
        "problem_statement",
        "stakeholders",
        "core_functionalities",
        "success_criteria",
        "technical_constraints"
      ],
      "message": "Constitution embeddings stored successfully"
    }
    ```
    """
    try:
        # Get constitution content
        from app.models.green_paper import Constitution
        result = await service.db.execute(
            select(Constitution).where(Constitution.id == constitution_id)
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found")

        # Store embeddings
        await service.store_constitution_embeddings(
            constitution_id=constitution_id,
            constitution_content=constitution.content_json
        )

        return {
            "constitution_id": str(constitution_id),
            "status": "stored",
            "collection": "project_constitutions",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimensions": 384,
            "text_length": len(str(constitution.content_json)),
            "sections_extracted": [
                "problem_statement",
                "stakeholders",
                "core_functionalities",
                "success_criteria",
                "technical_constraints"
            ],
            "message": "Constitution embeddings stored successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store embeddings: {str(e)}"
        )


# ========== Specification Endpoints (4) ==========

@router.post(
    "/constitutions/{constitution_id}/specification",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate HLD specification",
    response_description="Specification generation task created"
)
async def generate_specification(
    constitution_id: UUID,
    request: GenerateSpecificationRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Trigger Felix (Feature Architect) to generate HLD specification.

    **Requirements**:
    - Constitution must be approved
    - No pending specification generation

    **Process**:
    - Felix receives approved constitution
    - Generates High-Level Design specification (10 sections, 2000-3000 words)
    - Returns async task for monitoring

    **Returns**: Task ID and workflow information

    **Example Request**:
    ```json
    {
      "options": {
        "generate_immediately": true,
        "include_architecture_diagrams": true
      }
    }
    ```

    **Example Response**:
    ```json
    {
      "specification_id": "aa0e8400-e29b-41d4-a716-446655440000",
      "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "status": "draft",
      "workflow_id": "workflow_aa0e8400",
      "agent": "Felix",
      "model": "qwen2.5-coder:7b",
      "estimated_completion_time": "3-7 minutes",
      "message": "Specification generation started"
    }
    ```
    """
    try:
        # Get project_id from constitution
        from app.models.green_paper import Constitution
        result = await service.db.execute(
            select(Constitution).where(Constitution.id == constitution_id)
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found")

        # Keep project_id as string - it may be an integer ID or UUID
        project_id = constitution.project_id

        result = await service.generate_specification(
            project_id=project_id,
            constitution_id=constitution_id,
            options=request.options
        )
        return result
    except InvalidStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate specification: {str(e)}"
        )


@router.get(
    "/specifications/{specification_id}",
    summary="Get specification",
    response_description="Specification data (JSON or Markdown)"
)
async def get_specification(
    specification_id: UUID,
    format: str = Query("json", pattern="^(json|markdown)$"),
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Retrieve specification by ID.

    **Query Parameters**:
    - `format`: Response format - 'json' or 'markdown' (default: json)

    **Returns**: Specification data in requested format

    **Example Response (JSON)**:
    ```json
    {
      "specification_id": "aa0e8400-e29b-41d4-a716-446655440000",
      "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "approved",
      "content": {
        "architecture_overview": {...},
        "components": [...],
        "data_model": {...},
        "api_design": {...},
        "integration_points": [...],
        "quality_attributes": {...},
        "technology_stack": {...},
        "deployment_infrastructure": {...},
        "development_phases": [...],
        "risk_mitigation": [...]
      },
      "generated_by": "Felix",
      "generation_attempt": 1,
      "created_at": "2025-11-19T11:10:00Z",
      "reviewed_at": "2025-11-19T11:30:00Z",
      "reviewed_by": "user_123"
    }
    ```
    """
    try:
        # Get project_id from specification
        from app.models.green_paper import Specification
        result = await service.db.execute(
            select(Specification).where(Specification.id == specification_id)
        )
        specification = result.scalar_one_or_none()

        if not specification:
            raise ValueError(f"Specification {specification_id} not found")

        project_id = specification.project_id  # Keep as string - may be int ID or UUID

        specification_data = await service.get_specification(
            project_id=project_id,
            specification_id=specification_id,
            format=format
        )

        if format == "markdown":
            return Response(
                content=specification_data["content"],
                media_type="text/markdown"
            )
        return specification_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve specification: {str(e)}"
        )


@router.post(
    "/specifications/{specification_id}/review",
    summary="Review specification (approve/reject)",
    response_description="Review result with next step"
)
async def review_specification(
    specification_id: UUID,
    request: ReviewSpecificationRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    User reviews and approves or rejects the specification.

    **Actions**:
    - `approve`: Specification is approved, proceed to task generation
    - `reject`: Specification needs revision, Felix will regenerate

    **Approval**:
    - Returns next_step: generate_tasks
    - Specification status → approved

    **Rejection**:
    - Requires feedback and requested_changes
    - Returns next_step: regenerate_specification
    - Specification status → rejected

    **Example Request (Approve)**:
    ```json
    {
      "action": "approve",
      "feedback": "Great architecture, all components well-defined",
      "reviewed_by": "user_123",
      "requested_changes": []
    }
    ```

    **Example Response (Approve)**:
    ```json
    {
      "specification_id": "aa0e8400-e29b-41d4-a716-446655440000",
      "status": "approved",
      "reviewed_at": "2025-11-19T11:30:00Z",
      "reviewed_by": "user_123",
      "next_step": "generate_tasks",
      "next_actions": [
        "Use specification to generate epics, features, and stories",
        "Begin sprint planning with approved HLD"
      ],
      "message": "Specification approved successfully"
    }
    ```
    """
    try:
        # Get project_id from specification
        from app.models.green_paper import Specification
        result = await service.db.execute(
            select(Specification).where(Specification.id == specification_id)
        )
        specification = result.scalar_one_or_none()

        if not specification:
            raise ValueError(f"Specification {specification_id} not found")

        project_id = specification.project_id  # Keep as string - may be int ID or UUID

        result = await service.review_specification(
            project_id=project_id,
            specification_id=specification_id,
            action=request.action,
            feedback=request.feedback,
            reviewed_by=request.reviewed_by,
            requested_changes=request.requested_changes
        )
        return result
    except GreenPaperValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review specification: {str(e)}"
        )


@router.post(
    "/specifications/{specification_id}/regenerate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate specification with feedback",
    response_description="New specification generation started"
)
async def regenerate_specification(
    specification_id: UUID,
    request: RegenerateSpecificationRequest,
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Regenerate specification incorporating user feedback.

    **Requirements**:
    - Specification must be rejected
    - Maximum 3 regeneration attempts allowed

    **Process**:
    - Felix receives constitution + user feedback + requested changes
    - Regenerates specification with improvements
    - Returns new specification record

    **Example Request**:
    ```json
    {
      "requested_changes": [
        {
          "section": "technology_stack",
          "field": "database",
          "current_value": "MongoDB",
          "suggested_value": "PostgreSQL",
          "reason": "Need ACID compliance for financial data"
        }
      ],
      "feedback": "Please use PostgreSQL for better data integrity"
    }
    ```

    **Example Response**:
    ```json
    {
      "specification_id": "bb0e8400-e29b-41d4-a716-446655440000",
      "previous_specification_id": "aa0e8400-e29b-41d4-a716-446655440000",
      "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "generation_attempt": 2,
      "max_attempts": 3,
      "attempts_remaining": 1,
      "status": "draft",
      "workflow_id": "workflow_bb0e8400",
      "message": "Specification regeneration started (attempt #2)"
    }
    ```
    """
    try:
        # Get project_id from specification
        from app.models.green_paper import Specification
        result = await service.db.execute(
            select(Specification).where(Specification.id == specification_id)
        )
        specification = result.scalar_one_or_none()

        if not specification:
            raise ValueError(f"Specification {specification_id} not found")

        project_id = specification.project_id  # Keep as string - may be int ID or UUID

        result = await service.regenerate_specification(
            project_id=project_id,
            specification_id=specification_id,
            requested_changes=request.requested_changes,
            feedback=request.feedback
        )
        return result
    except GreenPaperValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate specification: {str(e)}"
        )


# ========== Search & Discovery Endpoints (1) ==========

@router.get(
    "/projects/similar",
    summary="Search similar projects",
    response_description="Projects with similar constitutions"
)
async def search_similar_projects(
    query: str = Query(..., min_length=10, description="Search query describing the project"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of results"),
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """
    Search for projects with similar constitutions using semantic search.

    **Query Parameters**:
    - `query`: Text description of project to search for (min 10 chars)
    - `limit`: Maximum results to return (1-20, default: 5)

    **Process**:
    - Generates embeddings for query text
    - Searches ChromaDB project_constitutions collection
    - Returns projects ranked by similarity score

    **Use Cases**:
    1. Find similar projects: "task management system with AI automation"
    2. Discover patterns: "projects using local AI execution"
    3. Learn from history: "projects with similar stakeholders"
    4. Avoid duplication: "has this problem been solved before?"

    **Example Request**:
    ```
    GET /api/week10/projects/similar?query=task+management+with+AI&limit=5
    ```

    **Example Response**:
    ```json
    {
      "query": "task management with AI",
      "similar_projects": [
        {
          "constitution_id": "880e8400-e29b-41d4-a716-446655440000",
          "project_id": "550e8400-e29b-41d4-a716-446655440000",
          "session_id": "660e8400-e29b-41d4-a716-446655440000",
          "similarity_score": 0.92,
          "status": "approved",
          "generated_by": "Peter",
          "created_at": "2025-11-19T10:35:00Z",
          "word_count": 1250,
          "num_stakeholders": 4,
          "num_functionalities": 5,
          "preview": "Problem: Software teams waste 40% of sprint planning time..."
        },
        {
          "constitution_id": "cc0e8400-e29b-41d4-a716-446655440000",
          "project_id": "dd0e8400-e29b-41d4-a716-446655440000",
          "session_id": "ee0e8400-e29b-41d4-a716-446655440000",
          "similarity_score": 0.87,
          "status": "approved",
          "generated_by": "Peter",
          "created_at": "2025-11-18T14:20:00Z",
          "word_count": 1180,
          "num_stakeholders": 3,
          "num_functionalities": 6,
          "preview": "Problem: Project managers need AI assistance for task estimation..."
        }
      ],
      "count": 2,
      "message": "Found 2 similar projects"
    }
    ```
    """
    try:
        similar_projects = await service.search_similar_projects(
            query=query,
            limit=limit
        )

        return {
            "query": query,
            "similar_projects": similar_projects,
            "count": len(similar_projects),
            "message": f"Found {len(similar_projects)} similar project{'s' if len(similar_projects) != 1 else ''}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search similar projects: {str(e)}"
        )


# ========== Health Check ==========

@router.get(
    "/health",
    tags=["Health"],
    summary="Green-paper workflow health check"
)
async def health_check():
    """Check if green-paper workflow endpoints are operational."""
    return {
        "status": "healthy",
        "service": "green-paper-workflow",
        "version": "1.0",
        "endpoints": {
            "sessions": 4,
            "constitutions": 5,
            "specifications": 4,
            "search": 1,
            "total": 14
        }
    }


# ========== Helper Functions ==========

def _build_profile_from_config(config: ProjectProfileConfig) -> ProjectProfile:
    """
    Build ProjectProfile from API config.

    Priority:
    1. If preset specified, use that
    2. Otherwise build custom profile from size/focus_areas
    """
    # Use preset if specified
    if config.preset:
        return get_preset_profile(config.preset)

    # Build custom profile
    focus_areas = {}
    if config.focus_areas:
        for area_str, level_str in config.focus_areas.items():
            try:
                focus_areas[FocusArea(area_str)] = StrictnessLevel(level_str)
            except ValueError:
                pass  # Skip invalid values

    return ProjectProfile(
        size=ProjectSize(config.size),
        focus_areas=focus_areas if focus_areas else None,
        team_size=config.team_size,
        expected_users=config.expected_users,
        budget_type=config.budget_type,
        timeline_weeks=config.timeline_weeks
    )
