"""
Specification Review API Routes

Endpoints for the Quinn/Felix two-agent review system.
Now with ProjectProfile support for dynamic agent configuration!
"""

from uuid import UUID
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.spec_review_service import (
    SpecReviewService,
    ReviewResult,
    ProcessedResult,
    SuggestionStatus
)
from app.models.project_profile import (
    ProjectProfile,
    ProjectSize,
    FocusArea,
    StrictnessLevel,
    get_preset_profile
)

router = APIRouter(prefix="/api/spec-review", tags=["Specification Review"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ReviewSuggestionResponse(BaseModel):
    id: str
    type: str
    priority: str
    section: str
    description: str
    reasoning: str
    status: str
    felix_response: Optional[str] = None


class ReviewResultResponse(BaseModel):
    specification_id: str
    suggestions: list[ReviewSuggestionResponse]
    overall_quality_score: float
    requires_human_review: bool
    escalation_reason: Optional[str]
    reviewed_at: str
    review_duration_seconds: float


class ProcessedResultResponse(BaseModel):
    specification_id: str
    accepted_count: int
    rejected_count: int
    updated_content: Optional[str]
    needs_human_decision: list[ReviewSuggestionResponse]
    processed_at: str


class FullReviewResponse(BaseModel):
    status: str
    reason: str
    review: Optional[ReviewResultResponse]
    processed: Optional[ProcessedResultResponse]
    final_action: str


class HumanDecisionRequest(BaseModel):
    suggestion_id: str
    decision: str  # "accept" or "reject"
    reasoning: Optional[str] = None


class ProjectProfileRequest(BaseModel):
    """Request body for specifying project profile."""
    size: str = "small"  # hobby, small, medium, large, enterprise
    focus_areas: Optional[Dict[str, str]] = None  # e.g., {"security": "strict", "usability": "strict"}
    preset: Optional[str] = None  # Use preset instead: club_app, startup_mvp, saas_product, fintech, healthcare
    team_size: int = 2
    expected_users: int = 100
    budget_type: str = "volunteer"


class ProfileInfoResponse(BaseModel):
    """Response showing available profiles and focus areas."""
    available_sizes: List[str]
    available_focus_areas: List[str]
    available_strictness_levels: List[str]
    available_presets: List[str]


# ============================================================================
# ROUTES
# ============================================================================

@router.post(
    "/specifications/{specification_id}/review",
    response_model=ReviewResultResponse,
    summary="Quinn reviews specification",
    description="Quinn (QA agent) reviews the specification and generates suggestions"
)
async def quinn_review_spec(
    specification_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Stage 1: Quinn reviews the specification.

    Returns quality score and list of suggestions.
    """
    service = SpecReviewService(db)

    try:
        result = await service.quinn_review(specification_id)

        return ReviewResultResponse(
            specification_id=str(result.specification_id),
            suggestions=[
                ReviewSuggestionResponse(
                    id=s.id,
                    type=s.type.value,
                    priority=s.priority.value,
                    section=s.section,
                    description=s.description,
                    reasoning=s.reasoning,
                    status=s.status.value,
                    felix_response=s.felix_response
                )
                for s in result.suggestions
            ],
            overall_quality_score=result.overall_quality_score,
            requires_human_review=result.requires_human_review,
            escalation_reason=result.escalation_reason,
            reviewed_at=result.reviewed_at.isoformat(),
            review_duration_seconds=result.review_duration_seconds
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")


@router.post(
    "/specifications/{specification_id}/full-review",
    response_model=FullReviewResponse,
    summary="Complete review cycle",
    description="Run full Quinn review + Felix processing cycle with project profile"
)
async def full_review_cycle(
    specification_id: UUID,
    profile_request: Optional[ProjectProfileRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete review cycle:
    1. Quinn reviews specification
    2. Felix processes suggestions (accept/reject)
    3. Returns final status with any needed human decisions

    Optionally provide a project profile to adjust agent strictness.
    Use preset="club_app" for small volunteer projects like klaverjas.
    """
    # Build project profile from request
    project_profile = _build_profile_from_request(profile_request)

    service = SpecReviewService(db, project_profile=project_profile)

    try:
        result = await service.full_review_cycle(specification_id)

        # Convert review result if present
        review_response = None
        if result.get("review"):
            r = result["review"]
            review_response = ReviewResultResponse(
                specification_id=str(r.specification_id),
                suggestions=[
                    ReviewSuggestionResponse(
                        id=s.id,
                        type=s.type.value,
                        priority=s.priority.value,
                        section=s.section,
                        description=s.description,
                        reasoning=s.reasoning,
                        status=s.status.value,
                        felix_response=s.felix_response
                    )
                    for s in r.suggestions
                ],
                overall_quality_score=r.overall_quality_score,
                requires_human_review=r.requires_human_review,
                escalation_reason=r.escalation_reason,
                reviewed_at=r.reviewed_at.isoformat(),
                review_duration_seconds=r.review_duration_seconds
            )

        # Convert processed result if present
        processed_response = None
        if result.get("processed"):
            p = result["processed"]
            processed_response = ProcessedResultResponse(
                specification_id=str(p.specification_id),
                accepted_count=p.accepted_count,
                rejected_count=p.rejected_count,
                updated_content=p.updated_content,
                needs_human_decision=[
                    ReviewSuggestionResponse(
                        id=s.id,
                        type=s.type.value,
                        priority=s.priority.value,
                        section=s.section,
                        description=s.description,
                        reasoning=s.reasoning,
                        status=s.status.value,
                        felix_response=s.felix_response
                    )
                    for s in p.needs_human_decision
                ],
                processed_at=p.processed_at.isoformat()
            )

        return FullReviewResponse(
            status=result["status"],
            reason=result["reason"],
            review=review_response,
            processed=processed_response,
            final_action=result["final_action"]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review cycle failed: {e}")


@router.get(
    "/health",
    summary="Check review service health",
    description="Verify Quinn and Felix models are available"
)
async def check_health(
    db: AsyncSession = Depends(get_db)
):
    """Check if required Ollama models are available."""
    import aiohttp

    models = {
        "quinn": "deepseek-r1:latest",
        "felix": "qwen2.5-coder:7b"
    }

    health = {}

    async with aiohttp.ClientSession() as session:
        for agent, model in models.items():
            try:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json={"model": model, "prompt": "test", "stream": False},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    health[agent] = {
                        "model": model,
                        "available": response.status == 200
                    }
            except Exception as e:
                health[agent] = {
                    "model": model,
                    "available": False,
                    "error": str(e)
                }

    all_healthy = all(h.get("available", False) for h in health.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "agents": health
    }


@router.get(
    "/profiles",
    response_model=ProfileInfoResponse,
    summary="List available profiles",
    description="Get all available project sizes, focus areas, and presets"
)
async def list_profiles():
    """List all available profile options."""
    return ProfileInfoResponse(
        available_sizes=[s.value for s in ProjectSize],
        available_focus_areas=[f.value for f in FocusArea],
        available_strictness_levels=[s.value for s in StrictnessLevel],
        available_presets=["hobby", "club_app", "startup_mvp", "saas_product", "fintech", "healthcare"]
    )


@router.get(
    "/profiles/{preset_name}",
    summary="Get preset profile details",
    description="Get details of a specific preset profile"
)
async def get_profile_details(preset_name: str):
    """Get details of a preset profile."""
    try:
        profile = get_preset_profile(preset_name)
        config = profile.get_agent_config("quinn")

        return {
            "preset": preset_name,
            "size": profile.size.value,
            "team_size": profile.team_size,
            "expected_users": profile.expected_users,
            "budget_type": profile.budget_type,
            "timeline_weeks": profile.timeline_weeks,
            "thresholds": {
                "min_quality_score": config.min_quality_score,
                "critical_issue_threshold": config.critical_issue_threshold,
            },
            "focus_areas": {
                area.value: level.value
                for area, level in profile.focus_areas.items()
            },
            "context_instructions": config.context_instructions
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_name}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _build_profile_from_request(request: Optional[ProjectProfileRequest]) -> ProjectProfile:
    """Build ProjectProfile from API request."""
    if request is None:
        # Default to club_app preset (good for klaverjas-type projects)
        return get_preset_profile("club_app")

    # If preset specified, use that as base
    if request.preset:
        return get_preset_profile(request.preset)

    # Build custom profile
    focus_areas = {}
    if request.focus_areas:
        for area_str, level_str in request.focus_areas.items():
            try:
                focus_areas[FocusArea(area_str)] = StrictnessLevel(level_str)
            except ValueError:
                pass  # Ignore invalid values

    return ProjectProfile(
        size=ProjectSize(request.size),
        focus_areas=focus_areas if focus_areas else None,
        team_size=request.team_size,
        expected_users=request.expected_users,
        budget_type=request.budget_type,
    )
