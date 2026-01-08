"""
LLM Council REST API

Week 52: Multi-Model Decision Making API
Provides 8 endpoints for the 3-stage consensus process
"""

from typing import Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.llm_council_service import LLMCouncilService
from app.models.llm_council import CouncilSession, CouncilResponse, CouncilReview, CouncilDecision


router = APIRouter(prefix="/api/council", tags=["LLM Council"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create new council session."""
    question: str = Field(..., min_length=10, max_length=5000, description="Question for the council")
    context: Dict = Field(default_factory=dict, description="Additional context")
    decision_type: str = Field(..., pattern="^(architecture|planning|quality|generation)$")
    agent_id: str = Field(..., min_length=1, max_length=50)


class ResponseSummary(BaseModel):
    """Summary of a council response."""
    id: str
    model_name: str
    confidence: float
    created_at: str

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class DecisionSummary(BaseModel):
    """Summary of final council decision."""
    id: str
    chairman_model: str
    final_decision: str
    confidence: float
    consensus_level: float
    dissenting_opinions: Optional[List[str]]
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    """Full session response with relationships."""
    id: str
    question: str
    context: Dict
    decision_type: str
    agent_id: str
    status: str
    created_at: str
    completed_at: Optional[str]
    response_count: int
    has_decision: bool

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(BaseModel):
    """Detailed session with all responses and decision."""
    session: SessionResponse
    responses: List[ResponseSummary]
    decision: Optional[DecisionSummary]
    consensus_level: Optional[float]


class QuickDecisionRequest(BaseModel):
    """All-in-one: create session + run 3 stages."""
    question: str = Field(..., min_length=10, max_length=5000)
    context: Dict = Field(default_factory=dict)
    decision_type: str = Field(..., pattern="^(architecture|planning|quality|generation)$")
    agent_id: str = Field(..., min_length=1, max_length=50)
    chairman_model: str = Field(default="deepseek-r1:latest")


class QuickDecisionResponse(BaseModel):
    """Response from quick decision."""
    session_id: str
    decision: DecisionSummary
    consensus_level: float
    response_count: int
    review_count: int
    message: str


class SessionListResponse(BaseModel):
    """List of sessions with pagination."""
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int


class StageResponse(BaseModel):
    """Response for stage execution."""
    session_id: str
    stage: str
    status: str
    count: int  # responses or reviews
    message: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_session(session: CouncilSession) -> SessionResponse:
    """Format CouncilSession to SessionResponse."""
    return SessionResponse(
        id=str(session.id),
        question=session.question,
        context=session.context,
        decision_type=session.decision_type,
        agent_id=session.agent_id,
        status=session.status,
        created_at=session.created_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        response_count=len(session.responses) if session.responses else 0,
        has_decision=session.decision is not None
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new council session.

    Creates a session in 'pending' status ready for Stage 1 (query_all_models).
    """
    service = LLMCouncilService(db)

    try:
        session = await service.create_session(
            question=request.question,
            context=request.context,
            decision_type=request.decision_type,
            agent_id=request.agent_id
        )

        return _format_session(session)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    agent_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    decision_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List council sessions with optional filters.

    Supports pagination and filtering by agent, status, and decision type.
    """
    service = LLMCouncilService(db)

    try:
        offset = (page - 1) * page_size

        sessions = await service.list_sessions(
            agent_id=agent_id,
            status=status_filter,
            decision_type=decision_type,
            limit=page_size,
            offset=offset
        )

        return SessionListResponse(
            sessions=[_format_session(s) for s in sessions],
            total=len(sessions),  # Note: This is count of returned items, not total in DB
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get session details with all responses and decision.

    Returns full session data including responses, reviews, and final decision.
    """
    service = LLMCouncilService(db)

    try:
        session = await service.get_session(session_id, include_relationships=True)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        # Format responses
        responses = [
            ResponseSummary(
                id=str(r.id),
                model_name=r.model_name,
                confidence=r.confidence,
                created_at=r.created_at.isoformat()
            )
            for r in (session.responses or [])
        ]

        # Format decision
        decision = None
        if session.decision:
            decision = DecisionSummary(
                id=str(session.decision.id),
                chairman_model=session.decision.chairman_model,
                final_decision=session.decision.final_decision,
                confidence=session.decision.confidence,
                consensus_level=session.decision.consensus_level,
                dissenting_opinions=session.decision.dissenting_opinions,
                created_at=session.decision.created_at.isoformat()
            )

        return SessionDetailResponse(
            session=_format_session(session),
            responses=responses,
            decision=decision,
            consensus_level=session.decision.consensus_level if session.decision else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.post("/sessions/{session_id}/query", response_model=StageResponse)
async def query_models(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute Stage 1: Query all models in parallel.

    Queries 6 Ollama models concurrently and saves responses.
    Updates session status to 'reviewing'.
    """
    service = LLMCouncilService(db)

    try:
        responses = await service.query_all_models(session_id)

        return StageResponse(
            session_id=str(session_id),
            stage="query_models",
            status="success",
            count=len(responses),
            message=f"Stage 1 complete: {len(responses)} models responded"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query models: {str(e)}"
        )


@router.post("/sessions/{session_id}/review", response_model=StageResponse)
async def peer_review(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute Stage 2: Peer review (blind/anonymous).

    Each model reviews all other models' responses.
    Generates N × (N-1) reviews where N = number of responses.
    """
    service = LLMCouncilService(db)

    try:
        reviews = await service.peer_review(session_id)

        return StageResponse(
            session_id=str(session_id),
            stage="peer_review",
            status="success",
            count=len(reviews),
            message=f"Stage 2 complete: {len(reviews)} reviews completed"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute peer review: {str(e)}"
        )


@router.post("/sessions/{session_id}/synthesize", response_model=DecisionSummary)
async def synthesize_decision(
    session_id: UUID,
    chairman_model: str = "deepseek-r1:latest",
    db: AsyncSession = Depends(get_db)
):
    """
    Execute Stage 3: Chairman synthesizes final decision.

    Chairman model considers:
    - All model responses
    - Peer review scores
    - Model weights
    - Consensus level

    Returns final decision with confidence and consensus metrics.
    """
    service = LLMCouncilService(db)

    try:
        decision = await service.synthesize(session_id, chairman_model)

        return DecisionSummary(
            id=str(decision.id),
            chairman_model=decision.chairman_model,
            final_decision=decision.final_decision,
            confidence=decision.confidence,
            consensus_level=decision.consensus_level,
            dissenting_opinions=decision.dissenting_opinions,
            created_at=decision.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synthesize decision: {str(e)}"
        )


@router.get("/sessions/{session_id}/decision", response_model=DecisionSummary)
async def get_decision(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get final decision for a session.

    Returns 404 if session has no decision yet.
    """
    service = LLMCouncilService(db)

    try:
        session = await service.get_session(session_id, include_relationships=True)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        if not session.decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} has no decision yet"
            )

        return DecisionSummary(
            id=str(session.decision.id),
            chairman_model=session.decision.chairman_model,
            final_decision=session.decision.final_decision,
            confidence=session.decision.confidence,
            consensus_level=session.decision.consensus_level,
            dissenting_opinions=session.decision.dissenting_opinions,
            created_at=session.decision.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get decision: {str(e)}"
        )


@router.post("/quick", response_model=QuickDecisionResponse)
async def quick_decision(
    request: QuickDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    All-in-one: Create session + execute all 3 stages.

    Convenience endpoint that:
    1. Creates session
    2. Queries all models (Stage 1)
    3. Peer review (Stage 2)
    4. Synthesis (Stage 3)

    Returns final decision immediately.
    Useful for synchronous decision making.
    """
    service = LLMCouncilService(db)

    try:
        # Stage 0: Create session
        session = await service.create_session(
            question=request.question,
            context=request.context,
            decision_type=request.decision_type,
            agent_id=request.agent_id
        )

        # Stage 1: Query models
        responses = await service.query_all_models(session.id)

        if not responses:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No models responded successfully"
            )

        # Stage 2: Peer review
        reviews = await service.peer_review(session.id)

        # Stage 3: Synthesis
        decision = await service.synthesize(session.id, request.chairman_model)

        return QuickDecisionResponse(
            session_id=str(session.id),
            decision=DecisionSummary(
                id=str(decision.id),
                chairman_model=decision.chairman_model,
                final_decision=decision.final_decision,
                confidence=decision.confidence,
                consensus_level=decision.consensus_level,
                dissenting_opinions=decision.dissenting_opinions,
                created_at=decision.created_at.isoformat()
            ),
            consensus_level=decision.consensus_level,
            response_count=len(responses),
            review_count=len(reviews),
            message=f"Council decision complete with {decision.consensus_level:.1f}% consensus"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute quick decision: {str(e)}"
        )
