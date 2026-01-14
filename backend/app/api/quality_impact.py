"""
API Routes for Quality Impact Mapping.

Fase 29: Provides endpoints for quality-to-functionality impact analysis.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from app.services.quality_impact import (
    QualityImpactMappingService,
    QualityIssue,
    IssueType,
    ImpactSeverity,
    ImpactSummary,
    ProjectImpactReport,
    create_quality_impact_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quality-impact", tags=["quality-impact"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class QualityIssueInput(BaseModel):
    """Input model for a quality issue."""
    issue_id: str = Field(..., description="Unique issue identifier")
    issue_type: str = Field(..., description="Type: security, privacy, performance, memory_leak, resource_leak, duplication, error_handling")
    severity: str = Field(..., description="Severity: critical, high, medium, low, info")
    file_path: str = Field(..., description="Path to affected file")
    line_number: int = Field(default=0, description="Line number in file")
    function_name: Optional[str] = Field(None, description="Affected function name")
    description: str = Field(..., description="Issue description")
    recommendation: str = Field(default="", description="Remediation recommendation")
    cwe_id: Optional[str] = Field(None, description="CWE identifier if applicable")
    data_exposed: List[str] = Field(default_factory=list, description="List of exposed data types")
    source_scanner: str = Field(default="", description="Scanner that detected the issue")


class AnalyzeProjectRequest(BaseModel):
    """Request for project quality impact analysis."""
    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    issues: List[QualityIssueInput] = Field(..., description="List of quality issues")
    base_user_count: int = Field(default=1000, ge=1, description="Estimated daily users")
    domain_mappings: Optional[Dict[str, Any]] = Field(None, description="Brown Paper domain mappings")
    traceability: Optional[Dict[str, Any]] = Field(None, description="Story-to-code traceability")


class AnalyzeProjectResponse(BaseModel):
    """Response with project impact analysis."""
    project_id: str
    project_name: str
    overall_health_score: float
    total_mappings: int
    critical_count: int
    high_count: int
    epic_summaries: List[Dict[str, Any]]
    feature_summaries: List[Dict[str, Any]]
    critical_issues: List[Dict[str, Any]]


class EntityImpactRequest(BaseModel):
    """Request for entity (epic/feature) impact analysis."""
    entity_id: str = Field(..., description="Entity identifier")
    issues: List[QualityIssueInput] = Field(..., description="List of quality issues")


class EntityImpactResponse(BaseModel):
    """Response with entity impact summary."""
    entity_type: str
    entity_id: str
    entity_name: str
    health_score: float
    issues_by_severity: Dict[str, int]
    total_issues: int
    top_issues: List[Dict[str, Any]]
    regulatory_risks: List[str]


class ImpactSummaryResponse(BaseModel):
    """Response with aggregated impact summary."""
    project_id: str
    total_issues: int
    mapped_count: int
    unmapped_count: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    affected_epics: int
    affected_features: int
    average_health_score: float


# =============================================================================
# SERVICE INSTANCE
# =============================================================================


_service: Optional[QualityImpactMappingService] = None


def get_service() -> QualityImpactMappingService:
    """Get or create quality impact service."""
    global _service
    if _service is None:
        _service = create_quality_impact_service()
    return _service


def _convert_input_to_issue(input_issue: QualityIssueInput) -> QualityIssue:
    """Convert API input to internal QualityIssue."""
    try:
        issue_type = IssueType(input_issue.issue_type.lower())
    except ValueError:
        issue_type = IssueType.CODE_SMELL

    try:
        severity = ImpactSeverity(input_issue.severity.lower())
    except ValueError:
        severity = ImpactSeverity.MEDIUM

    return QualityIssue(
        issue_id=input_issue.issue_id,
        issue_type=issue_type,
        severity=severity,
        location={
            "file": input_issue.file_path,
            "line": input_issue.line_number,
            "function": input_issue.function_name,
        },
        description=input_issue.description,
        recommendation=input_issue.recommendation,
        cwe_id=input_issue.cwe_id,
        data_exposed=input_issue.data_exposed,
        source_scanner=input_issue.source_scanner,
    )


# =============================================================================
# ANALYSIS ENDPOINTS
# =============================================================================


@router.post("/analyze", response_model=AnalyzeProjectResponse)
async def analyze_project(request: AnalyzeProjectRequest):
    """
    Run quality-to-functionality impact mapping for a project.

    Analyzes all issues and maps them to Epic/Feature/Story level,
    calculates impact scores, and provides prioritized summaries.
    """
    service = get_service()

    # Convert input issues
    issues = [_convert_input_to_issue(i) for i in request.issues]

    # Update base user count
    service.base_user_count = request.base_user_count

    # Run analysis
    report = service.analyze_project(
        project_id=request.project_id,
        project_name=request.project_name,
        issues=issues,
        domain_mappings=request.domain_mappings,
        traceability=request.traceability,
    )

    return AnalyzeProjectResponse(
        project_id=report.project_id,
        project_name=report.project_name,
        overall_health_score=report.overall_health_score,
        total_mappings=report.total_mappings,
        critical_count=report.mappings_by_severity.get("critical", 0),
        high_count=report.mappings_by_severity.get("high", 0),
        epic_summaries=[s.to_dict() for s in report.epic_summaries],
        feature_summaries=[s.to_dict() for s in report.feature_summaries[:10]],
        critical_issues=[m.to_dict() for m in report.critical_issues],
    )


@router.get("/project/{project_id}", response_model=ImpactSummaryResponse)
async def get_project_summary(project_id: str):
    """
    Get aggregated impact summary for a project.

    Returns high-level statistics about quality impact.
    """
    # In production, this would fetch from database
    # For now, return placeholder indicating no data
    return ImpactSummaryResponse(
        project_id=project_id,
        total_issues=0,
        mapped_count=0,
        unmapped_count=0,
        by_type={},
        by_severity={},
        affected_epics=0,
        affected_features=0,
        average_health_score=100.0,
    )


@router.post("/epic/{epic_id}", response_model=EntityImpactResponse)
async def get_epic_impact(epic_id: str, request: EntityImpactRequest):
    """
    Get impact summary for a specific epic.

    Shows all quality issues affecting this epic and their business impact.
    """
    service = get_service()

    issues = [_convert_input_to_issue(i) for i in request.issues]
    summary = service.get_epic_impact(epic_id, issues)

    return EntityImpactResponse(
        entity_type=summary.entity_type,
        entity_id=summary.entity_id,
        entity_name=summary.entity_name,
        health_score=summary.health_score,
        issues_by_severity={
            "critical": summary.critical_count,
            "high": summary.high_count,
            "medium": summary.medium_count,
            "low": summary.low_count,
        },
        total_issues=summary.total_issues,
        top_issues=[m.to_dict() for m in summary.top_issues],
        regulatory_risks=[r.value for r in summary.regulatory_risks],
    )


@router.post("/feature/{feature_id}", response_model=EntityImpactResponse)
async def get_feature_impact(feature_id: str, request: EntityImpactRequest):
    """
    Get impact summary for a specific feature.

    Shows all quality issues affecting this feature and their business impact.
    """
    service = get_service()

    issues = [_convert_input_to_issue(i) for i in request.issues]
    summary = service.get_feature_impact(feature_id, issues)

    return EntityImpactResponse(
        entity_type=summary.entity_type,
        entity_id=summary.entity_id,
        entity_name=summary.entity_name,
        health_score=summary.health_score,
        issues_by_severity={
            "critical": summary.critical_count,
            "high": summary.high_count,
            "medium": summary.medium_count,
            "low": summary.low_count,
        },
        total_issues=summary.total_issues,
        top_issues=[m.to_dict() for m in summary.top_issues],
        regulatory_risks=[r.value for r in summary.regulatory_risks],
    )


@router.post("/critical/{project_id}")
async def get_critical_issues(project_id: str, request: AnalyzeProjectRequest):
    """
    Get all critical issues with their business impact.

    Returns critical issues ranked by impact score.
    """
    service = get_service()

    issues = [_convert_input_to_issue(i) for i in request.issues]
    critical = service.get_critical_issues(issues)

    return {
        "project_id": project_id,
        "critical_count": len(critical),
        "issues": [m.to_dict() for m in critical],
    }


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================


@router.get("/issue-types")
async def list_issue_types():
    """List all supported issue types."""
    return {
        "issue_types": [
            {"value": t.value, "description": _get_type_description(t)}
            for t in IssueType
        ]
    }


@router.get("/severity-levels")
async def list_severity_levels():
    """List all severity levels."""
    return {
        "severity_levels": [
            {"value": s.value, "score": _get_severity_score(s)}
            for s in ImpactSeverity
        ]
    }


@router.get("/health")
async def health_check():
    """Health check for quality impact service."""
    return {
        "status": "healthy",
        "service": "quality-impact-mapping",
        "version": "1.0.0",
    }


def _get_type_description(issue_type: IssueType) -> str:
    """Get description for issue type."""
    descriptions = {
        IssueType.SECURITY: "Security vulnerabilities (SQL injection, XSS, etc.)",
        IssueType.PRIVACY: "Privacy issues (data exposure, GDPR)",
        IssueType.PERFORMANCE: "Performance problems (slow queries, N+1)",
        IssueType.MEMORY_LEAK: "Memory leaks",
        IssueType.RESOURCE_LEAK: "Resource leaks (connections, file handles)",
        IssueType.DUPLICATION: "Code duplication",
        IssueType.ERROR_HANDLING: "Error handling issues",
        IssueType.CODE_SMELL: "Code smells and maintainability issues",
        IssueType.DEPRECATED: "Use of deprecated APIs",
    }
    return descriptions.get(issue_type, "")


def _get_severity_score(severity: ImpactSeverity) -> int:
    """Get score for severity level."""
    scores = {
        ImpactSeverity.CRITICAL: 100,
        ImpactSeverity.HIGH: 75,
        ImpactSeverity.MEDIUM: 50,
        ImpactSeverity.LOW: 25,
        ImpactSeverity.INFO: 10,
    }
    return scores.get(severity, 0)
