# backend/app/api/devops_analysis.py
"""
DevOps Analysis API endpoints - Week 97-98 (Fase 14).

Provides REST API for GitHub and Azure DevOps repository analysis.
"""

import os
from typing import Optional, List, Literal
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.devops_analysis import (
    RepositoryAnalysis,
    HotSpot,
    ContributorAnalysis,
    PRPattern,
    CIPipelineAnalysis,
    IssueCorrelation,
    RepositoryInsight,
    RepositoryPlatform,
    AnalysisDepth,
)
from app.services.github_analysis_service import (
    GitHubAnalysisService,
    GitHubConfig,
    AnalysisRequest as GitHubAnalysisRequest,
)
from app.services.azure_devops_service import (
    AzureDevOpsService,
    AzureDevOpsConfig,
    AzureAnalysisRequest,
)


router = APIRouter(prefix="/api/devops", tags=["DevOps Analysis"])


# =============================================================================
# Pydantic Schemas
# =============================================================================

class AnalysisCreate(BaseModel):
    """Request to create a new repository analysis."""
    repository_url: str = Field(..., description="Full repository URL")
    platform: str = Field("auto", description="Platform: github, azure_devops, or auto")
    analysis_depth: Literal["quick", "standard", "full"] = Field(
        "standard", description="Analysis depth: quick, standard, or full"
    )
    max_commits: int = Field(1000, ge=100, le=10000)
    max_prs: int = Field(500, ge=100, le=5000)
    project_id: Optional[int] = Field(None, description="Link to project")

    # Platform-specific auth (optional - can use env vars)
    github_token: Optional[str] = Field(None, description="GitHub PAT")
    azure_pat: Optional[str] = Field(None, description="Azure DevOps PAT")
    azure_organization: Optional[str] = Field(None)
    azure_project: Optional[str] = Field(None)


class AnalysisSummary(BaseModel):
    """Summary of a repository analysis."""
    id: int
    platform: str
    repository_url: str
    repository_name: str
    status: str
    total_commits: int
    total_prs: int
    total_contributors: int
    total_issues: int
    avg_pr_review_time_hours: Optional[float]
    build_success_rate: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class HotSpotResponse(BaseModel):
    """Hot spot file information."""
    id: int
    file_path: str
    file_extension: Optional[str]
    change_count: int
    lines_changed_total: int
    distinct_authors: int
    risk_score: float
    associated_bugs: int
    last_modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ContributorResponse(BaseModel):
    """Contributor analysis information."""
    id: int
    contributor_id: str
    contributor_name: Optional[str]
    contributor_email: Optional[str]
    total_commits: int
    total_prs: int
    total_reviews: int
    bus_factor_contribution: float
    is_sole_maintainer_files: int
    primary_directories: List[str]
    primary_file_types: List[str]
    first_commit_date: Optional[datetime]
    last_commit_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PRPatternResponse(BaseModel):
    """Pull request pattern information."""
    id: int
    pr_number: int
    pr_title: Optional[str]
    pr_state: Optional[str]
    additions: int
    deletions: int
    changed_files: int
    review_count: int
    time_to_first_review: Optional[float]
    time_to_merge: Optional[float]
    had_merge_conflicts: bool
    had_ci_failures: bool
    required_rework: bool
    created_at: Optional[datetime]
    merged_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class InsightResponse(BaseModel):
    """Repository insight information."""
    id: int
    insight_type: str
    category: str
    title: str
    description: str
    severity: float
    evidence: dict
    recommendations: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisDetail(AnalysisSummary):
    """Full analysis details with nested data."""
    hot_spots_count: int
    insights_count: int
    error_message: Optional[str]


class ExtractionContext(BaseModel):
    """Context for extraction pipeline enrichment."""
    repository: dict
    metrics: dict
    hot_spots: List[dict]
    knowledge_silos: List[dict]
    issue_summary: Optional[dict] = None


# =============================================================================
# Helper Functions
# =============================================================================

def detect_platform(url: str) -> RepositoryPlatform:
    """Auto-detect repository platform from URL."""
    url_lower = url.lower()

    if "github.com" in url_lower:
        return RepositoryPlatform.GITHUB
    elif "dev.azure.com" in url_lower or "visualstudio.com" in url_lower:
        return RepositoryPlatform.AZURE_DEVOPS
    elif "gitlab" in url_lower:
        return RepositoryPlatform.GITLAB
    elif "bitbucket" in url_lower:
        return RepositoryPlatform.BITBUCKET
    else:
        # Default to GitHub
        return RepositoryPlatform.GITHUB


async def run_github_analysis(
    analysis_id: int,
    request: GitHubAnalysisRequest,
    github_token: str,
    db: Session
):
    """Background task for GitHub analysis."""
    config = GitHubConfig(token=github_token)
    service = GitHubAnalysisService(config, db)

    # Get analysis record
    analysis = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.id == analysis_id
    ).first()

    if not analysis:
        return

    try:
        # Run analysis (service already has the analysis record)
        await service.analyze_repository(request)
    except Exception as e:
        analysis.status = "failed"
        analysis.error_message = str(e)
        analysis.completed_at = datetime.utcnow()
        db.commit()
    finally:
        await service.close()


async def run_azure_analysis(
    analysis_id: int,
    request: AzureAnalysisRequest,
    pat: str,
    organization: str,
    project: str,
    db: Session
):
    """Background task for Azure DevOps analysis."""
    config = AzureDevOpsConfig(
        personal_access_token=pat,
        organization=organization,
        project=project
    )
    service = AzureDevOpsService(config, db)

    # Get analysis record
    analysis = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.id == analysis_id
    ).first()

    if not analysis:
        return

    try:
        await service.analyze_repository(request)
    except Exception as e:
        analysis.status = "failed"
        analysis.error_message = str(e)
        analysis.completed_at = datetime.utcnow()
        db.commit()
    finally:
        await service.close()


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/analyses", response_model=AnalysisSummary)
async def create_analysis(
    request: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a new repository analysis.

    The analysis runs in the background. Use GET /analyses/{id} to check status.
    """
    # Detect platform
    if request.platform == "auto":
        platform = detect_platform(request.repository_url)
    else:
        platform = RepositoryPlatform(request.platform)

    # Parse depth
    depth = AnalysisDepth(request.analysis_depth)

    # Extract repo name from URL
    repo_name = request.repository_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    # Create analysis record
    analysis = RepositoryAnalysis(
        project_id=request.project_id,
        platform=platform,
        repository_url=request.repository_url,
        repository_name=repo_name,
        analysis_depth=depth,
        max_commits=request.max_commits,
        max_prs=request.max_prs,
        status="pending"
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Start background analysis based on platform
    if platform == RepositoryPlatform.GITHUB:
        github_token = request.github_token or os.getenv("GITHUB_TOKEN", "")

        if not github_token:
            analysis.status = "failed"
            analysis.error_message = "GitHub token required"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="GitHub token required. Set GITHUB_TOKEN env var or provide github_token."
            )

        gh_request = GitHubAnalysisRequest(
            repository_url=request.repository_url,
            analysis_depth=depth,
            max_commits=request.max_commits,
            max_pull_requests=request.max_prs,
            project_id=request.project_id
        )

        background_tasks.add_task(
            run_github_analysis,
            analysis.id,
            gh_request,
            github_token,
            db
        )

    elif platform == RepositoryPlatform.AZURE_DEVOPS:
        azure_pat = request.azure_pat or os.getenv("AZURE_DEVOPS_PAT", "")
        organization = request.azure_organization or os.getenv("AZURE_DEVOPS_ORG", "")
        project = request.azure_project or os.getenv("AZURE_DEVOPS_PROJECT", "")

        if not azure_pat:
            analysis.status = "failed"
            analysis.error_message = "Azure DevOps PAT required"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Azure DevOps PAT required"
            )

        azure_request = AzureAnalysisRequest(
            repository_url=request.repository_url,
            analysis_depth=depth,
            max_commits=request.max_commits,
            max_pull_requests=request.max_prs,
            project_id=request.project_id
        )

        background_tasks.add_task(
            run_azure_analysis,
            analysis.id,
            azure_request,
            azure_pat,
            organization,
            project,
            db
        )

    else:
        analysis.status = "failed"
        analysis.error_message = f"Platform {platform} not yet supported"
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Platform {platform} not yet supported. Use github or azure_devops."
        )

    analysis.status = "running"
    db.commit()
    db.refresh(analysis)

    return analysis


@router.get("/analyses", response_model=List[AnalysisSummary])
async def list_analyses(
    project_id: Optional[int] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List repository analyses with optional filters."""
    query = db.query(RepositoryAnalysis)

    if project_id:
        query = query.filter(RepositoryAnalysis.project_id == project_id)
    if platform:
        query = query.filter(RepositoryAnalysis.platform == platform)
    if status:
        query = query.filter(RepositoryAnalysis.status == status)

    analyses = query.order_by(
        RepositoryAnalysis.created_at.desc()
    ).offset(offset).limit(limit).all()

    return analyses


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Get analysis details by ID."""
    analysis = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.id == analysis_id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Count related records
    hot_spots_count = db.query(HotSpot).filter(
        HotSpot.analysis_id == analysis_id
    ).count()

    insights_count = db.query(RepositoryInsight).filter(
        RepositoryInsight.analysis_id == analysis_id
    ).count()

    return AnalysisDetail(
        id=analysis.id,
        platform=analysis.platform.value if hasattr(analysis.platform, 'value') else str(analysis.platform),
        repository_url=analysis.repository_url,
        repository_name=analysis.repository_name,
        status=analysis.status,
        total_commits=analysis.total_commits,
        total_prs=analysis.total_prs,
        total_contributors=analysis.total_contributors,
        total_issues=analysis.total_issues,
        avg_pr_review_time_hours=analysis.avg_pr_review_time_hours,
        build_success_rate=analysis.build_success_rate,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        hot_spots_count=hot_spots_count,
        insights_count=insights_count,
        error_message=analysis.error_message
    )


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Delete an analysis and all related data."""
    analysis = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.id == analysis_id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    db.delete(analysis)
    db.commit()

    return {"status": "deleted", "id": analysis_id}


# =============================================================================
# Hot Spots Endpoints
# =============================================================================

@router.get("/analyses/{analysis_id}/hot-spots", response_model=List[HotSpotResponse])
async def get_hot_spots(
    analysis_id: int,
    min_risk: float = 0.0,
    sort_by: str = "risk_score",
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get hot spots for an analysis."""
    query = db.query(HotSpot).filter(HotSpot.analysis_id == analysis_id)

    if min_risk > 0:
        query = query.filter(HotSpot.risk_score >= min_risk)

    if sort_by == "risk_score":
        query = query.order_by(HotSpot.risk_score.desc())
    elif sort_by == "change_count":
        query = query.order_by(HotSpot.change_count.desc())
    elif sort_by == "bugs":
        query = query.order_by(HotSpot.associated_bugs.desc())

    return query.limit(limit).all()


# =============================================================================
# Contributors Endpoints
# =============================================================================

@router.get("/analyses/{analysis_id}/contributors", response_model=List[ContributorResponse])
async def get_contributors(
    analysis_id: int,
    sort_by: str = "commits",
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get contributor analysis for a repository."""
    query = db.query(ContributorAnalysis).filter(
        ContributorAnalysis.analysis_id == analysis_id
    )

    if sort_by == "commits":
        query = query.order_by(ContributorAnalysis.total_commits.desc())
    elif sort_by == "bus_factor":
        query = query.order_by(ContributorAnalysis.bus_factor_contribution.desc())
    elif sort_by == "sole_maintainer":
        query = query.order_by(ContributorAnalysis.is_sole_maintainer_files.desc())

    return query.limit(limit).all()


# =============================================================================
# PR Patterns Endpoints
# =============================================================================

@router.get("/analyses/{analysis_id}/pr-patterns", response_model=List[PRPatternResponse])
async def get_pr_patterns(
    analysis_id: int,
    state: Optional[str] = None,
    has_conflicts: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get pull request patterns for an analysis."""
    query = db.query(PRPattern).filter(PRPattern.analysis_id == analysis_id)

    if state:
        query = query.filter(PRPattern.pr_state == state)
    if has_conflicts is not None:
        query = query.filter(PRPattern.had_merge_conflicts == has_conflicts)

    return query.order_by(PRPattern.created_at.desc()).limit(limit).all()


# =============================================================================
# Insights Endpoints
# =============================================================================

@router.get("/analyses/{analysis_id}/insights", response_model=List[InsightResponse])
async def get_insights(
    analysis_id: int,
    category: Optional[str] = None,
    min_severity: float = 0.0,
    db: Session = Depends(get_db)
):
    """Get repository insights."""
    query = db.query(RepositoryInsight).filter(
        RepositoryInsight.analysis_id == analysis_id
    )

    if category:
        query = query.filter(RepositoryInsight.category == category)
    if min_severity > 0:
        query = query.filter(RepositoryInsight.severity >= min_severity)

    return query.order_by(RepositoryInsight.severity.desc()).all()


# =============================================================================
# Extraction Context Endpoint
# =============================================================================

@router.get("/analyses/{analysis_id}/extraction-context", response_model=ExtractionContext)
async def get_extraction_context(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Get analysis results formatted for extraction pipeline enrichment.

    This endpoint provides a condensed view of the analysis suitable
    for enriching extraction sessions with repository intelligence.
    """
    analysis = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.id == analysis_id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {analysis.status}"
        )

    # Get top hot spots
    hot_spots = db.query(HotSpot).filter(
        HotSpot.analysis_id == analysis_id
    ).order_by(HotSpot.risk_score.desc()).limit(20).all()

    # Get top contributors by bus factor
    contributors = db.query(ContributorAnalysis).filter(
        ContributorAnalysis.analysis_id == analysis_id
    ).order_by(ContributorAnalysis.bus_factor_contribution.desc()).limit(10).all()

    # Count issues by type
    issues = db.query(IssueCorrelation).filter(
        IssueCorrelation.analysis_id == analysis_id
    ).all()

    issue_by_type = {}
    for issue in issues:
        wt = issue.suggested_work_type or "unknown"
        issue_by_type[wt] = issue_by_type.get(wt, 0) + 1

    return ExtractionContext(
        repository={
            "platform": analysis.platform.value if hasattr(analysis.platform, 'value') else str(analysis.platform),
            "url": analysis.repository_url,
            "name": analysis.repository_name,
            "default_branch": analysis.default_branch
        },
        metrics={
            "total_commits": analysis.total_commits,
            "total_prs": analysis.total_prs,
            "total_contributors": analysis.total_contributors,
            "total_issues": analysis.total_issues,
            "avg_pr_review_time_hours": analysis.avg_pr_review_time_hours,
            "build_success_rate": analysis.build_success_rate
        },
        hot_spots=[
            {
                "path": hs.file_path,
                "risk_score": hs.risk_score,
                "change_count": hs.change_count,
                "bug_associations": hs.associated_bugs
            }
            for hs in hot_spots
        ],
        knowledge_silos=[
            {
                "contributor": c.contributor_name or c.contributor_id,
                "bus_factor": c.bus_factor_contribution,
                "focus_areas": c.primary_directories or []
            }
            for c in contributors
        ],
        issue_summary={
            "total": analysis.total_issues,
            "by_type": issue_by_type
        }
    )


# =============================================================================
# Statistics Endpoint
# =============================================================================

@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall DevOps analysis statistics."""
    total_analyses = db.query(RepositoryAnalysis).count()
    completed = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.status == "completed"
    ).count()
    failed = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.status == "failed"
    ).count()
    running = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.status == "running"
    ).count()

    # Platform breakdown
    github_count = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.platform == RepositoryPlatform.GITHUB
    ).count()
    azure_count = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.platform == RepositoryPlatform.AZURE_DEVOPS
    ).count()

    # Total hot spots and insights
    total_hot_spots = db.query(HotSpot).count()
    total_insights = db.query(RepositoryInsight).count()

    return {
        "total_analyses": total_analyses,
        "by_status": {
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total_analyses - completed - failed - running
        },
        "by_platform": {
            "github": github_count,
            "azure_devops": azure_count
        },
        "total_hot_spots": total_hot_spots,
        "total_insights": total_insights
    }
