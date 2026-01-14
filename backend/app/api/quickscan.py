"""
API Routes for Legacy Quickscan.

Fase 24 - A1: 15-minute automated legacy assessment.
"""

from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from app.services.quickscan import (
    LegacyQuickscanService,
    create_quickscan_service,
    QuickscanConfig,
    QuickscanReport,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quickscan", tags=["quickscan"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class QuickscanRequest(BaseModel):
    """Request for legacy quickscan."""
    project_path: str = Field(..., description="Path to project to scan")
    project_name: Optional[str] = Field(None, description="Project name (defaults to folder name)")
    max_scan_time_seconds: int = Field(900, description="Maximum scan time (default 15 min)")
    include_security_scan: bool = Field(True, description="Include security analysis")
    include_complexity_scan: bool = Field(True, description="Include complexity analysis")
    exclude_patterns: Optional[List[str]] = Field(None, description="Patterns to exclude")


class QuickscanSummaryResponse(BaseModel):
    """Summary response for quickscan."""
    id: str
    project_name: str
    recommendation: str
    recommendation_score: float
    suggested_approach: str
    duration_seconds: float
    key_findings: List[str]


class QuickscanFullResponse(BaseModel):
    """Full quickscan report response."""
    id: str
    project_name: str
    project_path: str
    started_at: str
    completed_at: str
    duration_seconds: float

    # Recommendation
    recommendation: str
    recommendation_score: float
    recommendation_reasons: List[str]
    suggested_approach: str
    approach_rationale: str

    # Technology
    technology_stack: Optional[dict]

    # Complexity
    complexity_score: Optional[dict]

    # Risk
    risk_assessment: Optional[dict]

    # Effort
    effort_estimate: Optional[dict]

    # Findings
    key_findings: List[str]
    opportunities: List[str]
    challenges: List[str]
    recommended_next_steps: List[str]


# =============================================================================
# SERVICE INSTANCE
# =============================================================================


_service: Optional[LegacyQuickscanService] = None


def get_service() -> LegacyQuickscanService:
    """Get or create quickscan service."""
    global _service
    if _service is None:
        _service = create_quickscan_service()
    return _service


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/scan", response_model=QuickscanFullResponse)
async def run_quickscan(request: QuickscanRequest):
    """
    Run 15-minute legacy quickscan.

    Returns Go/No-Go recommendation with:
    - Technology stack detection
    - Complexity analysis
    - Security risk assessment
    - Effort estimation
    - Modernization approach recommendation

    Target: < 15 minutes for 100K LOC
    """
    service = get_service()

    project_path = Path(request.project_path)
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.project_path}")

    config = QuickscanConfig(
        project_path=project_path,
        project_name=request.project_name or project_path.name,
        max_scan_time_seconds=request.max_scan_time_seconds,
        include_security_scan=request.include_security_scan,
        include_complexity_scan=request.include_complexity_scan,
        exclude_patterns=request.exclude_patterns or [
            "node_modules", "vendor", ".git", "__pycache__", "bin", "obj"
        ],
    )

    try:
        report = await service.scan(config)

        return QuickscanFullResponse(
            id=report.id,
            project_name=report.project_name,
            project_path=report.project_path,
            started_at=report.started_at.isoformat() if report.started_at else "",
            completed_at=report.completed_at.isoformat() if report.completed_at else "",
            duration_seconds=report.duration_seconds,
            recommendation=report.recommendation.value,
            recommendation_score=report.recommendation_score,
            recommendation_reasons=report.recommendation_reasons,
            suggested_approach=report.suggested_approach.value,
            approach_rationale=report.approach_rationale,
            technology_stack=report.technology_stack.to_dict() if report.technology_stack else None,
            complexity_score=report.complexity_score.to_dict() if report.complexity_score else None,
            risk_assessment=report.risk_assessment.to_dict() if report.risk_assessment else None,
            effort_estimate=report.effort_estimate.to_dict() if report.effort_estimate else None,
            key_findings=report.key_findings,
            opportunities=report.opportunities,
            challenges=report.challenges,
            recommended_next_steps=report.recommended_next_steps,
        )

    except Exception as e:
        logger.error(f"Quickscan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/scan/summary", response_model=QuickscanSummaryResponse)
async def run_quickscan_summary(request: QuickscanRequest):
    """
    Run quickscan and return summary only.

    Faster response with just the recommendation and key findings.
    """
    full_response = await run_quickscan(request)

    return QuickscanSummaryResponse(
        id=full_response.id,
        project_name=full_response.project_name,
        recommendation=full_response.recommendation,
        recommendation_score=full_response.recommendation_score,
        suggested_approach=full_response.suggested_approach,
        duration_seconds=full_response.duration_seconds,
        key_findings=full_response.key_findings[:5],
    )


@router.get("/health")
async def health_check():
    """Health check for quickscan service."""
    return {
        "status": "healthy",
        "service": "legacy-quickscan",
        "fase": "24-A1",
        "version": "1.0.0",
        "target_scan_time": "15 minutes",
        "analyzers": [
            "TechnologyDetector",
            "ComplexityAnalyzer",
            "SecurityAnalyzer",
            "EffortEstimator",
        ],
    }


@router.get("/approaches")
async def list_approaches():
    """List available modernization approaches."""
    return {
        "approaches": [
            {
                "value": "rehost",
                "name": "Rehost (Lift & Shift)",
                "description": "Move to cloud without code changes",
            },
            {
                "value": "replatform",
                "name": "Replatform (Lift & Reshape)",
                "description": "Migrate to new platform with minimal changes",
            },
            {
                "value": "refactor",
                "name": "Refactor (Re-architect)",
                "description": "Restructure code while preserving business logic",
            },
            {
                "value": "rebuild",
                "name": "Rebuild (Rewrite)",
                "description": "Rewrite from scratch with new architecture",
            },
            {
                "value": "replace",
                "name": "Replace (Buy COTS)",
                "description": "Replace with commercial off-the-shelf solution",
            },
        ]
    }


@router.get("/recommendations")
async def list_recommendations():
    """List possible recommendations."""
    return {
        "recommendations": [
            {
                "value": "go",
                "name": "GO",
                "description": "Project is a good candidate for modernization",
                "score_range": "60-100",
            },
            {
                "value": "conditional",
                "name": "CONDITIONAL",
                "description": "Modernization possible with careful planning",
                "score_range": "35-59",
            },
            {
                "value": "no_go",
                "name": "NO GO",
                "description": "Modernization not recommended - consider alternatives",
                "score_range": "0-34",
            },
        ]
    }
