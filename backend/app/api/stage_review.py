"""
API Routes for Stage-Based Council Review.

Fase 23.6: Stage-based LLM council reviews with performance tracking.

Phase 24.1: Core review endpoints
Phase 24.4: Performance metrics endpoints
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
import logging

from app.services.stage_review import (
    StageReviewService,
    create_stage_review_service,
    StageType,
    ReviewDecision,
    IssueSeverity,
    IssueCategory,
    get_stage_config,
    get_all_stage_types,
    STAGE_COUNCIL_CONFIGS,
    # Performance tracking (Phase 24.4)
    PerformanceTrackingService,
    create_performance_tracking_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stage-review", tags=["stage-review"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class ReviewArtifactRequest(BaseModel):
    """Request for artifact review."""
    stage_type: str = Field(..., description="Development stage: architecture, design, analysis, programming, testing, infrastructure")
    artifact: str = Field(..., description="The artifact content to review")
    artifact_type: str = Field(default="code", description="Type of artifact: code, document, config, schema, test")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the review")
    force_review: bool = Field(default=False, description="Skip cache and force new review")


class IssueResponse(BaseModel):
    """Response model for a review issue."""
    severity: str
    category: str
    title: str
    description: str
    suggested_fix: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    code_snippet: Optional[str]
    confirmed_by_models: List[str]
    consensus_score: float


class ReviewResponse(BaseModel):
    """Response with review results."""
    session_id: str
    stage_type: str
    decision: str
    approved: bool
    issues: List[IssueResponse]
    consensus_level: float
    rounds_completed: int
    improved_artifact: Optional[str]
    metrics: Optional[Dict[str, Any]]


class StageConfigResponse(BaseModel):
    """Response with stage configuration."""
    stage_type: str
    primary_models: List[str]
    secondary_models: List[str]
    specialist_model: Optional[str]
    criteria: Dict[str, float]
    critical_threshold: int
    major_threshold: int
    consensus_minimum: float
    max_rounds: int


# =============================================================================
# SERVICE INSTANCE
# =============================================================================


_service: Optional[StageReviewService] = None


def get_service() -> StageReviewService:
    """Get or create stage review service."""
    global _service
    if _service is None:
        _service = create_stage_review_service()
    return _service


# =============================================================================
# REVIEW ENDPOINTS
# =============================================================================


@router.post("/review", response_model=ReviewResponse)
async def review_artifact(request: ReviewArtifactRequest):
    """
    Submit artifact for stage-based council review.

    Executes multi-model review with consensus calculation.
    Automatic second round if issues exceed threshold.
    """
    service = get_service()

    try:
        result = await service.review_artifact(
            stage_type=request.stage_type,
            artifact=request.artifact,
            artifact_type=request.artifact_type,
            context=request.context,
            force_review=request.force_review,
        )

        return ReviewResponse(
            session_id=result.session_id,
            stage_type=result.stage_type.value,
            decision=result.decision.value,
            approved=result.approved,
            issues=[
                IssueResponse(
                    severity=i.severity.value,
                    category=i.category.value,
                    title=i.title,
                    description=i.description,
                    suggested_fix=i.suggested_fix,
                    line_start=i.line_start,
                    line_end=i.line_end,
                    code_snippet=i.code_snippet,
                    confirmed_by_models=i.confirmed_by_models,
                    consensus_score=i.consensus_score,
                )
                for i in result.issues
            ],
            consensus_level=result.consensus_level,
            rounds_completed=result.rounds_completed,
            improved_artifact=result.improved_artifact,
            metrics=result.metrics,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Review failed: {e}")
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================


@router.get("/config/{stage_type}", response_model=StageConfigResponse)
async def get_stage_configuration(stage_type: str):
    """
    Get configuration for a specific development stage.

    Returns models, criteria, and thresholds for the stage.
    """
    try:
        config = get_stage_config(stage_type)

        return StageConfigResponse(
            stage_type=stage_type,
            primary_models=config.primary_models,
            secondary_models=config.secondary_models,
            specialist_model=config.specialist_model,
            criteria=config.criteria,
            critical_threshold=config.critical_threshold,
            major_threshold=config.major_threshold,
            consensus_minimum=config.consensus_minimum,
            max_rounds=config.max_rounds,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stages")
async def list_stages():
    """List all available development stages."""
    stages = []
    for stage_type in get_all_stage_types():
        config = STAGE_COUNCIL_CONFIGS[stage_type]
        stages.append({
            "stage_type": stage_type,
            "primary_models_count": len(config.primary_models),
            "critical_threshold": config.critical_threshold,
            "major_threshold": config.major_threshold,
            "consensus_minimum": config.consensus_minimum,
        })

    return {"stages": stages}


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================


@router.get("/issue-severities")
async def list_issue_severities():
    """List all issue severity levels."""
    return {
        "severities": [
            {"value": s.value, "description": _get_severity_description(s)}
            for s in IssueSeverity
        ]
    }


@router.get("/issue-categories")
async def list_issue_categories():
    """List all issue categories."""
    return {
        "categories": [
            {"value": c.value, "description": _get_category_description(c)}
            for c in IssueCategory
        ]
    }


@router.get("/decisions")
async def list_decision_types():
    """List all review decision types."""
    return {
        "decisions": [
            {"value": d.value, "description": _get_decision_description(d)}
            for d in ReviewDecision
        ]
    }


@router.get("/health")
async def health_check():
    """Health check for stage review service."""
    return {
        "status": "healthy",
        "service": "stage-review",
        "version": "1.0.0",
        "stages_configured": len(STAGE_COUNCIL_CONFIGS),
    }


@router.post("/cache/clear")
async def clear_cache():
    """Clear the review cache."""
    service = get_service()
    service.clear_cache()
    return {"status": "cache_cleared"}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _get_severity_description(severity: IssueSeverity) -> str:
    """Get description for severity level."""
    descriptions = {
        IssueSeverity.CRITICAL: "Must fix, blocks approval (security, crashes, data loss)",
        IssueSeverity.MAJOR: "Should fix, counts toward threshold (bugs, performance)",
        IssueSeverity.MINOR: "Nice to fix, doesn't block approval (style, improvements)",
        IssueSeverity.SUGGESTION: "Optional improvement ideas",
    }
    return descriptions.get(severity, "")


def _get_category_description(category: IssueCategory) -> str:
    """Get description for issue category."""
    descriptions = {
        IssueCategory.SECURITY: "Security vulnerabilities (injection, XSS, etc.)",
        IssueCategory.PERFORMANCE: "Performance problems (slow queries, inefficient algorithms)",
        IssueCategory.CORRECTNESS: "Correctness issues (bugs, logic errors)",
        IssueCategory.MAINTAINABILITY: "Maintainability concerns (complexity, coupling)",
        IssueCategory.STYLE: "Style issues (formatting, naming conventions)",
        IssueCategory.DOCUMENTATION: "Documentation problems (missing, outdated)",
        IssueCategory.TESTING: "Testing issues (coverage, assertions)",
        IssueCategory.ARCHITECTURE: "Architecture concerns (design patterns, structure)",
    }
    return descriptions.get(category, "")


def _get_decision_description(decision: ReviewDecision) -> str:
    """Get description for review decision."""
    descriptions = {
        ReviewDecision.APPROVED: "Artifact approved, meets quality standards",
        ReviewDecision.REJECTED: "Artifact rejected, critical issues found",
        ReviewDecision.NEEDS_REVISION: "Artifact needs revision, major issues found",
    }
    return descriptions.get(decision, "")


# =============================================================================
# PERFORMANCE TRACKING (Phase 24.4)
# =============================================================================


_performance_service: Optional[PerformanceTrackingService] = None


def get_performance_service() -> PerformanceTrackingService:
    """Get or create performance tracking service."""
    global _performance_service
    if _performance_service is None:
        _performance_service = create_performance_tracking_service()
    return _performance_service


class ModelPerformanceResponse(BaseModel):
    """Response model for model performance."""
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    total_reviews: int
    successful_reviews: int
    timeout_rate: float
    error_rate: float
    avg_response_time_ms: float
    p95_response_time_ms: int
    avg_issues_found: float
    consensus_alignment: float


class StagePerformanceResponse(BaseModel):
    """Response model for stage performance."""
    stage_type: str
    total_reviews: int
    approval_rate: float
    avg_consensus: float
    avg_duration_ms: float
    avg_issues_per_review: float
    second_round_rate: float
    improvement_success_rate: float
    top_issue_categories: List[str]


class OverallPerformanceResponse(BaseModel):
    """Response model for overall performance."""
    total_reviews: int
    approval_rate: float
    avg_consensus: float
    avg_duration_ms: float
    second_round_rate: float
    most_common_issues: List[Dict[str, Any]]
    best_performing_model: Optional[str]
    worst_performing_stage: Optional[str]
    period_start: Optional[str]
    period_end: Optional[str]


@router.get("/performance/models", response_model=List[ModelPerformanceResponse])
async def get_model_performance(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
):
    """
    Get performance metrics for LLM models.

    Returns response times, success rates, and issue detection metrics.
    """
    service = get_performance_service()
    reports = service.get_model_performance(model_name=model_name)

    return [
        ModelPerformanceResponse(
            model_name=r.model_name,
            total_reviews=r.total_reviews,
            successful_reviews=r.successful_reviews,
            timeout_rate=r.timeout_rate,
            error_rate=r.error_rate,
            avg_response_time_ms=r.avg_response_time_ms,
            p95_response_time_ms=r.p95_response_time_ms,
            avg_issues_found=r.avg_issues_found,
            consensus_alignment=r.consensus_alignment,
        )
        for r in reports
    ]


@router.get("/performance/stages", response_model=List[StagePerformanceResponse])
async def get_stage_performance(
    stage_type: Optional[str] = Query(None, description="Filter by stage type"),
):
    """
    Get performance metrics for development stages.

    Returns approval rates, consensus levels, and issue statistics.
    """
    service = get_performance_service()

    try:
        stage = StageType(stage_type) if stage_type else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage type: {stage_type}")

    reports = service.get_stage_performance(stage_type=stage)

    return [
        StagePerformanceResponse(
            stage_type=r.stage_type.value,
            total_reviews=r.total_reviews,
            approval_rate=r.approval_rate,
            avg_consensus=r.avg_consensus,
            avg_duration_ms=r.avg_duration_ms,
            avg_issues_per_review=r.avg_issues_per_review,
            second_round_rate=r.second_round_rate,
            improvement_success_rate=r.improvement_success_rate,
            top_issue_categories=r.top_issue_categories,
        )
        for r in reports
    ]


@router.get("/performance/overall", response_model=OverallPerformanceResponse)
async def get_overall_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get overall performance summary.

    Returns aggregated metrics across all models and stages.
    """
    service = get_performance_service()
    report = service.get_overall_performance(days=days)

    return OverallPerformanceResponse(
        total_reviews=report.total_reviews,
        approval_rate=report.approval_rate,
        avg_consensus=report.avg_consensus,
        avg_duration_ms=report.avg_duration_ms,
        second_round_rate=report.second_round_rate,
        most_common_issues=report.most_common_issues,
        best_performing_model=report.best_performing_model,
        worst_performing_stage=report.worst_performing_stage,
        period_start=report.period_start.isoformat() if report.period_start else None,
        period_end=report.period_end.isoformat() if report.period_end else None,
    )


@router.post("/performance/reset")
async def reset_performance_metrics():
    """Reset all in-memory performance metrics."""
    service = get_performance_service()
    service.clear_metrics()
    return {"status": "metrics_reset"}
