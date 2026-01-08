"""
BigAGI Beam API - Week 78

REST API endpoints for BigAGI multi-model validation service.
Provides validation sessions, consensus calculation, and LLM Council integration.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.bigagi_beam_service import BigAGIBeamService


router = APIRouter(prefix="/api/bigagi", tags=["BigAGI Beam"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ModelConfig(BaseModel):
    """Configuration for a validator model."""
    name: str = Field(..., description="Model name")
    provider: str = Field(default="ollama", description="Provider: ollama, claude, codex")
    weight: float = Field(default=1.0, ge=0.1, le=5.0, description="Weight in consensus calculation")


class CreateValidationRequest(BaseModel):
    """Request to create a validation session."""
    task: str = Field(..., min_length=1, max_length=10000, description="Task/question that was answered")
    primary_response: str = Field(..., min_length=1, max_length=50000, description="Response to validate")
    primary_model: str = Field(..., description="Model that produced the response")
    validation_models: Optional[List[ModelConfig]] = Field(
        default=None,
        description="Models to use for validation (default: Ollama models)"
    )
    session_metadata: Optional[Dict[str, Any]] = None


class RunValidationRequest(BaseModel):
    """Request to run validation."""
    consensus_method: str = Field(
        default="weighted",
        pattern="^(majority|weighted|unanimous)$",
        description="Method for consensus calculation"
    )


class QuickValidateRequest(BaseModel):
    """Request for quick (stateless) validation."""
    task: str = Field(..., min_length=1, max_length=10000)
    response: str = Field(..., min_length=1, max_length=50000)
    model_used: str = Field(default="unknown")

    model_config = ConfigDict(protected_namespaces=())


class CrossValidateRequest(BaseModel):
    """Request to cross-validate a council session."""
    council_session_id: UUID


class ValidationResponse(BaseModel):
    """Validation session response."""
    id: str
    task: str
    primary_response: str
    primary_model: str
    validation_models: List[Dict[str, Any]]
    status: str
    consensus_score: Optional[float]
    consensus_reached: Optional[bool]
    final_answer: Optional[str]
    session_metadata: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime]


class ValidationResultResponse(BaseModel):
    """Result of running a validation."""
    validation_id: str
    consensus_reached: bool
    consensus_score: float
    recommendation: str
    final_answer: Optional[str]
    key_agreements: List[str]
    key_disagreements: List[str]
    model_responses: Dict[str, Dict[str, Any]]

    model_config = ConfigDict(protected_namespaces=())


class ModelResponseResponse(BaseModel):
    """Individual model response."""
    id: str
    validation_id: str
    model: str
    provider: str
    response: str
    thinking: Optional[str]
    confidence: Optional[float]
    agreement_score: Optional[float]
    tokens_used: Optional[int]
    latency_ms: Optional[int]
    error: Optional[str]
    created_at: datetime


class ConsensusResponse(BaseModel):
    """Consensus calculation result."""
    id: str
    validation_id: str
    method: str
    agreement_matrix: Optional[Dict[str, Dict[str, float]]]
    key_agreements: List[str]
    key_disagreements: List[str]
    synthesis: Optional[str]
    confidence: Optional[float]
    recommendation: Optional[str]
    created_at: datetime


# =============================================================================
# VALIDATION SESSIONS
# =============================================================================

@router.post("/validations", response_model=ValidationResponse, status_code=status.HTTP_201_CREATED)
async def create_validation(
    request: CreateValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new multi-model validation session.

    The session will be in 'pending' status until run.
    """
    service = BigAGIBeamService(db)

    validation_models = None
    if request.validation_models:
        validation_models = [m.model_dump() for m in request.validation_models]

    validation = await service.create_validation(
        task=request.task,
        primary_response=request.primary_response,
        primary_model=request.primary_model,
        validation_models=validation_models,
        session_metadata=request.session_metadata
    )

    return ValidationResponse(
        id=str(validation.id),
        task=validation.task,
        primary_response=validation.primary_response[:500] + "..." if len(validation.primary_response) > 500 else validation.primary_response,
        primary_model=validation.primary_model,
        validation_models=validation.validation_models,
        status=validation.status,
        consensus_score=validation.consensus_score,
        consensus_reached=validation.consensus_reached,
        final_answer=validation.final_answer,
        session_metadata=validation.session_metadata or {},
        created_at=validation.created_at,
        completed_at=validation.completed_at
    )


@router.get("/validations", response_model=List[ValidationResponse])
async def list_validations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List validation sessions."""
    service = BigAGIBeamService(db)
    validations = await service.list_validations(status=status, limit=limit)

    return [
        ValidationResponse(
            id=str(v.id),
            task=v.task[:200] + "..." if len(v.task) > 200 else v.task,
            primary_response=v.primary_response[:500] + "..." if len(v.primary_response) > 500 else v.primary_response,
            primary_model=v.primary_model,
            validation_models=v.validation_models,
            status=v.status,
            consensus_score=v.consensus_score,
            consensus_reached=v.consensus_reached,
            final_answer=v.final_answer[:500] + "..." if v.final_answer and len(v.final_answer) > 500 else v.final_answer,
            session_metadata=v.session_metadata or {},
            created_at=v.created_at,
            completed_at=v.completed_at
        )
        for v in validations
    ]


@router.get("/validations/{validation_id}", response_model=ValidationResponse)
async def get_validation(
    validation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get validation session details."""
    service = BigAGIBeamService(db)
    validation = await service.get_validation(validation_id, include_responses=False)

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation {validation_id} not found"
        )

    return ValidationResponse(
        id=str(validation.id),
        task=validation.task,
        primary_response=validation.primary_response,
        primary_model=validation.primary_model,
        validation_models=validation.validation_models,
        status=validation.status,
        consensus_score=validation.consensus_score,
        consensus_reached=validation.consensus_reached,
        final_answer=validation.final_answer,
        session_metadata=validation.session_metadata or {},
        created_at=validation.created_at,
        completed_at=validation.completed_at
    )


@router.post("/validations/{validation_id}/run", response_model=ValidationResultResponse)
async def run_validation(
    validation_id: UUID,
    request: RunValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run multi-model validation.

    Queries all validator models in parallel, calculates agreement scores,
    and determines consensus using the specified method.
    """
    service = BigAGIBeamService(db)

    try:
        result = await service.run_validation(
            validation_id=validation_id,
            consensus_method=request.consensus_method
        )

        return ValidationResultResponse(
            validation_id=str(result.validation_id),
            consensus_reached=result.consensus_reached,
            consensus_score=result.consensus_score,
            recommendation=result.recommendation,
            final_answer=result.final_answer,
            key_agreements=result.key_agreements,
            key_disagreements=result.key_disagreements,
            model_responses=result.model_responses
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/validations/{validation_id}/responses", response_model=List[ModelResponseResponse])
async def get_validation_responses(
    validation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all model responses for a validation."""
    service = BigAGIBeamService(db)
    validation = await service.get_validation(validation_id, include_responses=True)

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation {validation_id} not found"
        )

    return [
        ModelResponseResponse(
            id=str(r.id),
            validation_id=str(r.validation_id),
            model=r.model,
            provider=r.provider,
            response=r.response,
            thinking=r.thinking,
            confidence=r.confidence,
            agreement_score=r.agreement_score,
            tokens_used=r.tokens_used,
            latency_ms=r.latency_ms,
            error=r.error,
            created_at=r.created_at
        )
        for r in validation.responses
    ]


@router.get("/validations/{validation_id}/consensus", response_model=ConsensusResponse)
async def get_validation_consensus(
    validation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get consensus result for a validation."""
    service = BigAGIBeamService(db)
    validation = await service.get_validation(validation_id, include_responses=True)

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation {validation_id} not found"
        )

    if not validation.consensus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No consensus calculated for validation {validation_id}"
        )

    consensus = validation.consensus
    return ConsensusResponse(
        id=str(consensus.id),
        validation_id=str(consensus.validation_id),
        method=consensus.method,
        agreement_matrix=consensus.agreement_matrix,
        key_agreements=consensus.key_agreements or [],
        key_disagreements=consensus.key_disagreements or [],
        synthesis=consensus.synthesis,
        confidence=consensus.confidence,
        recommendation=consensus.recommendation,
        created_at=consensus.created_at
    )


# =============================================================================
# QUICK VALIDATION
# =============================================================================

@router.post("/validate")
async def quick_validate(
    request: QuickValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick validation without full session tracking.

    Useful for inline validation during response generation.
    Returns a simple pass/fail result with confidence.
    """
    service = BigAGIBeamService(db)

    try:
        result = await service.quick_validate(
            task=request.task,
            response=request.response,
            model_used=request.model_used
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick validation failed: {str(e)}"
        )


# =============================================================================
# LLM COUNCIL INTEGRATION
# =============================================================================

@router.post("/cross-validate-council")
async def cross_validate_council(
    request: CrossValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cross-validate an LLM Council session decision.

    Takes the council's final decision and validates it with additional
    models that were not part of the original council.
    """
    service = BigAGIBeamService(db)

    try:
        result = await service.cross_validate_council(request.council_session_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cross-validation failed: {str(e)}"
        )


# =============================================================================
# STATISTICS
# =============================================================================

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get BigAGI Beam validation statistics."""
    service = BigAGIBeamService(db)
    return await service.get_validation_stats()


@router.get("/consensus-methods")
async def get_consensus_methods():
    """Get available consensus calculation methods."""
    return {
        "methods": [
            {
                "name": "majority",
                "description": "Simple majority voting (50%+ agreement wins)",
                "threshold": 0.5
            },
            {
                "name": "weighted",
                "description": "Weight-adjusted voting based on model confidence and role",
                "threshold": "varies by model weights"
            },
            {
                "name": "unanimous",
                "description": "All validators must agree (>70% each)",
                "threshold": 0.7
            }
        ],
        "recommendations": {
            "accept": "Consensus score >= 85% - safe to accept",
            "review": "Consensus score 70-85% - manual review recommended",
            "reject": "Consensus score < 70% - consider regenerating"
        }
    }


@router.get("/default-validators")
async def get_default_validators():
    """Get the default validator model configuration."""
    return {
        "validators": BigAGIBeamService.DEFAULT_VALIDATORS,
        "note": "Override by providing validation_models in create request"
    }
