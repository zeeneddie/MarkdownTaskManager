"""
Re-Run Upgrade API - Week 85

API endpoints for tier upgrades and extraction re-runs.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.rerun_upgrade_service import (
    RerunUpgradeService,
    get_rerun_upgrade_service,
    ExtractionTier,
    UpgradeReason,
)

router = APIRouter(prefix="/rerun-upgrade", tags=["Re-Run Upgrade"])


# ==================== Request Models ====================

class GenerateQuoteRequest(BaseModel):
    """Request to generate upgrade quote."""
    session_id: str = Field(..., description="Original extraction session ID")
    target_tier: str = Field(..., description="Target tier (BASIC, STANDARD, PROFESSIONAL, PREMIUM)")
    original_result: Optional[Dict[str, Any]] = Field(None, description="Original extraction result")


class RerunRequest(BaseModel):
    """Request to re-run extraction."""
    original_session_id: str = Field(..., description="Original extraction session ID")
    target_tier: str = Field(..., description="Target tier")
    reason: str = Field("tier_upgrade", description="Reason for re-run")
    quote_id: Optional[str] = Field(None, description="Quote ID if upgrading")
    focus_areas: Optional[List[str]] = Field(None, description="Areas to focus on")
    repository_path: str = Field(..., description="Path to repository")
    original_result: Dict[str, Any] = Field(..., description="Original extraction result")


class CalculateDeltaRequest(BaseModel):
    """Request to calculate delta between runs."""
    original_result: Dict[str, Any] = Field(..., description="Original extraction result")
    rerun_result: Dict[str, Any] = Field(..., description="Re-run extraction result")
    original_tier: str = Field("FREE", description="Original tier")
    rerun_tier: str = Field("STANDARD", description="Re-run tier")


class MergeResultsRequest(BaseModel):
    """Request to merge two extraction results."""
    original_result: Dict[str, Any] = Field(..., description="Original extraction result")
    rerun_result: Dict[str, Any] = Field(..., description="Re-run extraction result")
    strategy: str = Field("prefer_rerun", description="Merge strategy")


class GetRecommendationsRequest(BaseModel):
    """Request for upgrade recommendations."""
    session_id: str = Field(..., description="Current extraction session ID")
    result: Dict[str, Any] = Field(..., description="Current extraction result")


# ==================== Response Models ====================

class QuoteResponse(BaseModel):
    """Upgrade quote response."""
    quote_id: str
    current_tier: str
    target_tier: str
    price_difference: float
    expected_confidence_gain: float
    expected_story_improvement: int
    estimated_duration_minutes: int
    valid_until: datetime
    project_id: int
    session_id: str


class StoryDeltaResponse(BaseModel):
    """Story delta in response."""
    story_id: str
    change_type: str
    confidence_change: float
    field_changes: Dict[str, List[Any]]


class DeltaResponse(BaseModel):
    """Extraction delta response."""
    delta_id: str
    original_session_id: str
    rerun_session_id: str
    original_tier: str
    rerun_tier: str
    calculated_at: datetime
    added_stories_count: int
    removed_stories_count: int
    modified_stories_count: int
    unchanged_stories: int
    total_original_stories: int
    total_rerun_stories: int
    confidence_improvement: float
    coverage_improvement: float
    quality_improvement: float
    recommendations: List[str]


class RerunResultResponse(BaseModel):
    """Re-run result response."""
    rerun_id: str
    request_id: str
    new_session_id: str
    completed_at: datetime
    duration_ms: int
    cost_incurred: float
    success: bool
    errors: List[str]
    delta: DeltaResponse


class RecommendationsResponse(BaseModel):
    """Upgrade recommendations response."""
    should_upgrade: bool
    recommended_tier: Optional[str]
    reasons: List[str]
    expected_improvements: List[str]
    estimated_cost: float


class MergeResultResponse(BaseModel):
    """Merged result response."""
    total_stories: int
    merge_strategy: str
    merged_at: str
    original_session_id: str
    rerun_session_id: str
    overall_confidence: float
    stories: List[Dict[str, Any]]


# ==================== Helper Functions ====================

def _get_service() -> RerunUpgradeService:
    """Get service instance."""
    return get_rerun_upgrade_service()


def _delta_to_response(delta) -> DeltaResponse:
    """Convert delta to response model."""
    return DeltaResponse(
        delta_id=delta.delta_id,
        original_session_id=delta.original_session_id,
        rerun_session_id=delta.rerun_session_id,
        original_tier=delta.original_tier.value,
        rerun_tier=delta.rerun_tier.value,
        calculated_at=delta.calculated_at,
        added_stories_count=len(delta.added_stories),
        removed_stories_count=len(delta.removed_stories),
        modified_stories_count=len(delta.modified_stories),
        unchanged_stories=delta.unchanged_stories,
        total_original_stories=delta.total_original_stories,
        total_rerun_stories=delta.total_rerun_stories,
        confidence_improvement=delta.confidence_improvement,
        coverage_improvement=delta.coverage_improvement,
        quality_improvement=delta.quality_improvement,
        recommendations=delta.recommendations,
    )


# ==================== Endpoints ====================

@router.post("/projects/{project_id}/quote", response_model=QuoteResponse)
async def generate_upgrade_quote(
    project_id: int,
    request: GenerateQuoteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a quote for tier upgrade.

    Returns pricing and expected improvements for upgrading to a higher tier.
    """
    service = _get_service()

    try:
        quote = await service.generate_upgrade_quote(
            project_id=project_id,
            session_id=request.session_id,
            target_tier=request.target_tier,
            original_result=request.original_result,
        )

        return QuoteResponse(
            quote_id=quote.quote_id,
            current_tier=quote.current_tier.value,
            target_tier=quote.target_tier.value,
            price_difference=quote.price_difference,
            expected_confidence_gain=quote.expected_confidence_gain,
            expected_story_improvement=quote.expected_story_improvement,
            estimated_duration_minutes=quote.estimated_duration_minutes,
            valid_until=quote.valid_until,
            project_id=quote.project_id,
            session_id=quote.session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quote: {e}")


@router.post("/projects/{project_id}/rerun", response_model=RerunResultResponse)
async def execute_rerun(
    project_id: int,
    request: RerunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute extraction re-run with upgraded tier.

    Returns the new extraction result with delta analysis.
    """
    service = _get_service()

    try:
        # Create re-run request
        rerun_request = await service.request_rerun(
            project_id=project_id,
            original_session_id=request.original_session_id,
            target_tier=request.target_tier,
            reason=request.reason,
            requested_by="api",
            quote_id=request.quote_id,
            focus_areas=request.focus_areas,
        )

        # Execute re-run
        result = await service.execute_rerun(
            request=rerun_request,
            original_result=request.original_result,
            repository_path=request.repository_path,
        )

        return RerunResultResponse(
            rerun_id=result.rerun_id,
            request_id=result.request.request_id,
            new_session_id=result.new_session_id,
            completed_at=result.completed_at,
            duration_ms=result.duration_ms,
            cost_incurred=result.cost_incurred,
            success=result.success,
            errors=result.errors,
            delta=_delta_to_response(result.delta),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-run failed: {e}")


@router.post("/calculate-delta", response_model=DeltaResponse)
async def calculate_delta(
    request: CalculateDeltaRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate delta between two extraction runs.

    Useful for comparing results without executing a new extraction.
    """
    service = _get_service()

    try:
        delta = await service.calculate_delta(
            original_result=request.original_result,
            rerun_result=request.rerun_result,
            original_tier=ExtractionTier(request.original_tier.upper()),
            rerun_tier=ExtractionTier(request.rerun_tier.upper()),
        )

        return _delta_to_response(delta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delta calculation failed: {e}")


@router.post("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    request: GetRecommendationsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get upgrade recommendations based on current extraction results.

    Analyzes quality and confidence to suggest if upgrade would help.
    """
    service = _get_service()

    try:
        recommendations = await service.get_upgrade_recommendations(
            session_id=request.session_id,
            result=request.result,
        )

        return RecommendationsResponse(
            should_upgrade=recommendations["should_upgrade"],
            recommended_tier=recommendations.get("recommended_tier"),
            reasons=recommendations["reasons"],
            expected_improvements=recommendations["expected_improvements"],
            estimated_cost=recommendations["estimated_cost"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {e}")


@router.post("/merge-results", response_model=MergeResultResponse)
async def merge_results(
    request: MergeResultsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Merge two extraction results using specified strategy.

    Strategies:
    - prefer_rerun: Keep rerun results, fill gaps from original
    - prefer_original: Keep original, add new from rerun
    - highest_confidence: Keep story with highest confidence
    - union: Keep all stories from both
    """
    service = _get_service()

    if request.strategy not in ["prefer_rerun", "prefer_original", "highest_confidence", "union"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy: {request.strategy}. "
            f"Must be one of: prefer_rerun, prefer_original, highest_confidence, union"
        )

    try:
        merged = await service.merge_results(
            original=request.original_result,
            rerun=request.rerun_result,
            strategy=request.strategy,
        )

        return MergeResultResponse(
            total_stories=merged["total_stories"],
            merge_strategy=merged["merge_strategy"],
            merged_at=merged["merged_at"],
            original_session_id=merged.get("original_session_id", ""),
            rerun_session_id=merged.get("rerun_session_id", ""),
            overall_confidence=merged.get("overall_confidence", 0.0),
            stories=merged.get("stories", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {e}")


@router.get("/tiers", response_model=Dict[str, Any])
async def get_tier_info():
    """
    Get information about available extraction tiers.

    Returns pricing, expected confidence, and LLM configuration for each tier.
    """
    return {
        "tiers": [
            {
                "name": "FREE",
                "price": 0.0,
                "expected_confidence": 0.60,
                "llm_count": 3,
                "llms": ["Ollama qwen2.5-coder", "Ollama deepseek-r1", "Ollama codellama"],
                "features": ["Basic extraction", "Local processing", "No cost"],
                "human_review": False,
            },
            {
                "name": "BASIC",
                "price": 5.0,
                "expected_confidence": 0.70,
                "llm_count": 5,
                "llms": ["+ Groq llama3.1", "+ Qwen-Turbo"],
                "features": ["Improved accuracy", "Fast inference", "Cloud backup"],
                "human_review": False,
            },
            {
                "name": "STANDARD",
                "price": 25.0,
                "expected_confidence": 0.80,
                "llm_count": 7,
                "llms": ["+ Gemini Flash", "+ Gemini Pro"],
                "features": ["High accuracy", "Cross-validation", "Quality assurance"],
                "human_review": False,
                "recommended": True,
            },
            {
                "name": "PROFESSIONAL",
                "price": 75.0,
                "expected_confidence": 0.90,
                "llm_count": 9,
                "llms": ["+ GPT-5.2", "+ Moonshot Kimi"],
                "features": ["Very high accuracy", "Deep analysis", "Expert models"],
                "human_review": "optional",
            },
            {
                "name": "PREMIUM",
                "price": 150.0,
                "expected_confidence": 0.95,
                "llm_count": 10,
                "llms": ["+ Claude Opus 4.5"],
                "features": ["Maximum accuracy", "Full synthesis", "All features"],
                "human_review": "included",
            },
        ],
        "comparison_note": "Prices based on 50K lines of code. Actual cost scales with codebase size.",
    }


@router.get("/reasons", response_model=List[Dict[str, str]])
async def get_rerun_reasons():
    """Get valid reasons for re-running extraction."""
    return [
        {
            "value": "tier_upgrade",
            "label": "Tier Upgrade",
            "description": "Upgrading to a higher tier for better accuracy",
        },
        {
            "value": "low_confidence",
            "label": "Low Confidence",
            "description": "Original extraction had low confidence scores",
        },
        {
            "value": "human_request",
            "label": "Human Review Request",
            "description": "Human reviewer requested re-extraction",
        },
        {
            "value": "codebase_changed",
            "label": "Codebase Changed",
            "description": "Code has changed since last extraction",
        },
        {
            "value": "new_llm_available",
            "label": "New LLM Available",
            "description": "Better LLM became available",
        },
        {
            "value": "quality_issue",
            "label": "Quality Issue",
            "description": "Quality issues found in original extraction",
        },
    ]
