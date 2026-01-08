# Stability Analysis API
# Fase 21: ASP Application Stability Analyzer
#
# Endpoints:
# - POST /api/stability/analyze - Run stability analysis
# - GET /api/stability/report/{project_id} - Get stability report
# - GET /api/stability/categories - List analysis categories
# - GET /api/stability/findings/{scan_id} - Get findings
# - GET /api/stability/trends/{project_id} - Get trend data

from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stability import (
    StabilityScan,
    StabilityFinding,
    StabilityMetric,
    StabilityCategorySummary,
)
from app.services.stability import (
    ResourceLeakDetectorService,
    StabilityCategory,
    SeverityLevel,
)
from app.services.stability.detectors import (
    ClassicASPLeakDetector,
    ClassicASPCOMDetector,
    ClassicASPFileDetector,
    # Week 144: New analyzers
    ExternalServiceAnalyzer,
    MemoryAnalyzer,
    SessionAnalyzer,
    IncludeResolver,
)

router = APIRouter(
    prefix="/api/stability",
    tags=["stability"]
)


# === Schemas ===

class AnalyzeRequest(BaseModel):
    """Request to analyze a project for stability issues."""
    project_id: int = Field(..., description="Project ID to analyze")
    base_path: str = Field(..., description="Path to project files")
    recursive: bool = Field(True, description="Scan subdirectories")
    exclude_patterns: Optional[List[str]] = Field(None, description="Glob patterns to exclude")


class AnalyzeResponse(BaseModel):
    """Response from stability analysis."""
    scan_id: int
    project_id: int
    total_files_scanned: int
    total_files_with_issues: int
    overall_score: int
    overall_risk: str
    critical_count: int
    high_count: int
    analysis_time_seconds: float
    message: str

    class Config:
        from_attributes = True


class FindingResponse(BaseModel):
    """A single stability finding."""
    id: int
    category: str
    file_path: str
    line_number: int
    resource_type: str
    variable_name: Optional[str]
    leak_pattern: str
    severity: str
    description: str
    suggested_fix: Optional[str]
    confidence: float
    status: str

    class Config:
        from_attributes = True


class CategorySummaryResponse(BaseModel):
    """Summary for a stability category."""
    category: str
    issues_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    severity_score: int

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    """Full scan report response."""
    id: int
    project_id: int
    scan_timestamp: datetime
    total_files_scanned: int
    total_files_with_issues: int
    overall_score: int
    overall_risk: str
    categories: List[CategorySummaryResponse]
    findings: List[FindingResponse]

    class Config:
        from_attributes = True


class TrendDataPoint(BaseModel):
    """A single trend data point."""
    date: date
    overall_score: int
    total_findings: int
    critical_count: int
    high_count: int


class TrendResponse(BaseModel):
    """Trend data for a project."""
    project_id: int
    data_points: List[TrendDataPoint]


class CategoryInfo(BaseModel):
    """Information about a stability category."""
    name: str
    description: str
    severity_weight: int


# === Helper Functions ===

def get_detector_service(db: Session) -> ResourceLeakDetectorService:
    """Create and configure detector service."""
    service = ResourceLeakDetectorService(db=db)
    service.register_detector(ClassicASPLeakDetector())
    service.register_detector(ClassicASPCOMDetector())
    service.register_detector(ClassicASPFileDetector())
    return service


# === Endpoints ===

@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_201_CREATED)
async def analyze_project(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> AnalyzeResponse:
    """
    Run stability analysis on a project.

    Analyzes all supported files for resource leaks and other stability issues.
    """
    service = get_detector_service(db)

    # Run analysis
    report = await service.analyze_project(
        project_id=request.project_id,
        project_name=f"Project {request.project_id}",
        base_path=request.base_path,
        recursive=request.recursive,
        exclude_patterns=request.exclude_patterns,
    )

    # Create database record
    scan = StabilityScan(
        project_id=request.project_id,
        total_files_scanned=report.total_files_scanned,
        total_files_with_issues=report.total_files_with_issues,
        categories_analyzed=[c.value for c in report.categories.keys()],
        languages_analyzed=report.languages_analyzed,
        overall_risk=report.overall_risk.value,
        overall_score=report.overall_score,
        analysis_time_seconds=report.analysis_time_seconds,
        base_path=request.base_path,
    )
    db.add(scan)
    db.flush()

    # Add findings
    for finding in report.all_findings:
        db_finding = StabilityFinding(
            scan_id=scan.id,
            category=finding.category.value,
            file_path=finding.file_path,
            line_number=finding.line_number,
            resource_type=finding.resource_type.value,
            variable_name=finding.variable_name,
            leak_pattern=finding.leak_pattern.value,
            severity=finding.severity.value,
            description=finding.description,
            suggested_fix=finding.suggested_fix,
            code_context=finding.code_context,
            confidence=finding.confidence,
        )
        db.add(db_finding)

    # Add category summaries
    for category, cat_finding in report.categories.items():
        summary = StabilityCategorySummary(
            scan_id=scan.id,
            category=category.value,
            issues_found=cat_finding.issues_found,
            critical_count=cat_finding.critical_count,
            high_count=cat_finding.high_count,
            medium_count=cat_finding.medium_count,
            low_count=cat_finding.low_count,
            severity_score=cat_finding.severity_score,
        )
        db.add(summary)

    db.commit()

    return AnalyzeResponse(
        scan_id=scan.id,
        project_id=request.project_id,
        total_files_scanned=report.total_files_scanned,
        total_files_with_issues=report.total_files_with_issues,
        overall_score=report.overall_score,
        overall_risk=report.overall_risk.value,
        critical_count=report.critical_count,
        high_count=report.high_count,
        analysis_time_seconds=report.analysis_time_seconds,
        message=f"Analysis complete. Found {report.total_findings} issues.",
    )


@router.get("/report/{project_id}", response_model=ScanResponse)
async def get_report(
    project_id: int,
    db: Session = Depends(get_db)
) -> ScanResponse:
    """Get the latest stability report for a project."""
    scan = db.query(StabilityScan).filter(
        StabilityScan.project_id == project_id
    ).order_by(StabilityScan.scan_timestamp.desc()).first()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stability scan found for project {project_id}"
        )

    return ScanResponse(
        id=scan.id,
        project_id=scan.project_id,
        scan_timestamp=scan.scan_timestamp,
        total_files_scanned=scan.total_files_scanned,
        total_files_with_issues=scan.total_files_with_issues,
        overall_score=scan.overall_score,
        overall_risk=scan.overall_risk,
        categories=[
            CategorySummaryResponse(
                category=cs.category,
                issues_found=cs.issues_found,
                critical_count=cs.critical_count,
                high_count=cs.high_count,
                medium_count=cs.medium_count,
                low_count=cs.low_count,
                severity_score=cs.severity_score,
            )
            for cs in scan.category_summaries
        ],
        findings=[
            FindingResponse(
                id=f.id,
                category=f.category,
                file_path=f.file_path,
                line_number=f.line_number,
                resource_type=f.resource_type,
                variable_name=f.variable_name,
                leak_pattern=f.leak_pattern,
                severity=f.severity,
                description=f.description,
                suggested_fix=f.suggested_fix,
                confidence=f.confidence,
                status=f.status,
            )
            for f in scan.findings
        ],
    )


@router.get("/categories", response_model=List[CategoryInfo])
async def list_categories() -> List[CategoryInfo]:
    """List all stability analysis categories."""
    categories = [
        CategoryInfo(
            name=StabilityCategory.ADO_LEAKS.value,
            description="ADO Connection and Recordset leaks",
            severity_weight=100,
        ),
        CategoryInfo(
            name=StabilityCategory.COM_OBJECTS.value,
            description="COM object leaks (XMLHTTP, ABCpdf, XMLDOM)",
            severity_weight=80,
        ),
        CategoryInfo(
            name=StabilityCategory.EXTERNAL_SERVICES.value,
            description="External service timeout and retry issues",
            severity_weight=70,
        ),
        CategoryInfo(
            name=StabilityCategory.MEMORY_INTENSIVE.value,
            description="Memory-intensive operations (PDF, arrays)",
            severity_weight=60,
        ),
        CategoryInfo(
            name=StabilityCategory.FILE_HANDLES.value,
            description="File handle leaks (FSO, TextStream)",
            severity_weight=50,
        ),
        CategoryInfo(
            name=StabilityCategory.SESSION_STATE.value,
            description="Session state size and timeout issues",
            severity_weight=40,
        ),
        CategoryInfo(
            name=StabilityCategory.EXCEPTION_HANDLING.value,
            description="Exception handling patterns",
            severity_weight=30,
        ),
        CategoryInfo(
            name=StabilityCategory.SQL_PERFORMANCE.value,
            description="SQL performance issues (N+1, deadlocks)",
            severity_weight=50,
        ),
    ]
    return categories


@router.get("/findings/{scan_id}", response_model=List[FindingResponse])
async def get_findings(
    scan_id: int,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[FindingResponse]:
    """Get findings for a scan with optional filters."""
    query = db.query(StabilityFinding).filter(
        StabilityFinding.scan_id == scan_id
    )

    if category:
        query = query.filter(StabilityFinding.category == category)

    if severity:
        query = query.filter(StabilityFinding.severity == severity)

    if status_filter:
        query = query.filter(StabilityFinding.status == status_filter)

    # Order by severity (CRITICAL first)
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    findings = query.all()

    # Sort in Python since SQLAlchemy ordering by custom list is complex
    findings.sort(key=lambda f: severity_order.index(f.severity) if f.severity in severity_order else 5)

    # Apply pagination
    findings = findings[offset:offset + limit]

    return [
        FindingResponse(
            id=f.id,
            category=f.category,
            file_path=f.file_path,
            line_number=f.line_number,
            resource_type=f.resource_type,
            variable_name=f.variable_name,
            leak_pattern=f.leak_pattern,
            severity=f.severity,
            description=f.description,
            suggested_fix=f.suggested_fix,
            confidence=f.confidence,
            status=f.status,
        )
        for f in findings
    ]


@router.get("/trends/{project_id}", response_model=TrendResponse)
async def get_trends(
    project_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
) -> TrendResponse:
    """Get stability trend data for a project."""
    from datetime import timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    metrics = db.query(StabilityMetric).filter(
        StabilityMetric.project_id == project_id,
        StabilityMetric.metric_date >= start_date,
        StabilityMetric.metric_date <= end_date,
    ).order_by(StabilityMetric.metric_date).all()

    return TrendResponse(
        project_id=project_id,
        data_points=[
            TrendDataPoint(
                date=m.metric_date,
                overall_score=m.overall_score,
                total_findings=m.total_findings,
                critical_count=m.critical_count,
                high_count=m.high_count,
            )
            for m in metrics
        ],
    )


@router.patch("/findings/{finding_id}/status")
async def update_finding_status(
    finding_id: int,
    new_status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
) -> FindingResponse:
    """Update the status of a finding."""
    valid_statuses = ["open", "acknowledged", "fixed", "wontfix"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    finding = db.query(StabilityFinding).filter(
        StabilityFinding.id == finding_id
    ).first()

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding {finding_id} not found"
        )

    finding.status = new_status
    if notes:
        finding.notes = notes

    if new_status == "fixed":
        finding.fixed_at = datetime.utcnow()

    db.commit()

    return FindingResponse(
        id=finding.id,
        category=finding.category,
        file_path=finding.file_path,
        line_number=finding.line_number,
        resource_type=finding.resource_type,
        variable_name=finding.variable_name,
        leak_pattern=finding.leak_pattern,
        severity=finding.severity,
        description=finding.description,
        suggested_fix=finding.suggested_fix,
        confidence=finding.confidence,
        status=finding.status,
    )


@router.get("/summary/{project_id}")
async def get_summary(
    project_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Get a quick summary of stability for a project."""
    scan = db.query(StabilityScan).filter(
        StabilityScan.project_id == project_id
    ).order_by(StabilityScan.scan_timestamp.desc()).first()

    if not scan:
        return {
            "project_id": project_id,
            "has_scan": False,
            "message": "No stability scan available",
        }

    return {
        "project_id": project_id,
        "has_scan": True,
        "last_scan": scan.scan_timestamp.isoformat(),
        "overall_score": scan.overall_score,
        "overall_risk": scan.overall_risk,
        "total_findings": len(scan.findings),
        "critical_count": scan.critical_count,
        "high_count": scan.high_count,
        "files_scanned": scan.total_files_scanned,
        "files_with_issues": scan.total_files_with_issues,
    }


# === Week 144: Enhanced Analyzers ===

class AnalyzeCodeRequest(BaseModel):
    """Request to analyze code with enhanced analyzers."""
    code: str = Field(..., description="Code content to analyze")
    file_path: str = Field("analysis.asp", description="File path for context")
    analyzers: Optional[List[str]] = Field(
        None,
        description="Analyzers to run: external_service, memory, session, all"
    )


class EnhancedFindingResponse(BaseModel):
    """A finding from the enhanced analyzers."""
    analyzer: str
    category: str
    issue_type: str
    line_number: int
    variable_name: Optional[str]
    severity: str
    description: str
    suggested_fix: Optional[str]
    confidence: float


class EnhancedAnalyzeResponse(BaseModel):
    """Response from enhanced analysis."""
    file_path: str
    total_findings: int
    findings_by_analyzer: dict
    findings: List[EnhancedFindingResponse]


@router.post("/analyze/enhanced", response_model=EnhancedAnalyzeResponse)
async def analyze_enhanced(request: AnalyzeCodeRequest) -> EnhancedAnalyzeResponse:
    """
    Analyze code with Week 144 enhanced analyzers.

    Runs ExternalServiceAnalyzer, MemoryAnalyzer, and SessionAnalyzer
    for comprehensive ASP stability analysis.
    """
    findings = []
    findings_by_analyzer = {}

    # Determine which analyzers to run
    run_all = request.analyzers is None or "all" in request.analyzers

    # External Service Analyzer
    if run_all or "external_service" in (request.analyzers or []):
        analyzer = ExternalServiceAnalyzer()
        ext_findings = analyzer.analyze(request.code, request.file_path)
        findings_by_analyzer["external_service"] = len(ext_findings)
        for f in ext_findings:
            findings.append(EnhancedFindingResponse(
                analyzer="external_service",
                category=StabilityCategory.EXTERNAL_SERVICES.value,
                issue_type=f.issue_type.value,
                line_number=f.line_number,
                variable_name=f.variable_name,
                severity=f.severity.value,
                description=f.description,
                suggested_fix=f.suggested_fix,
                confidence=f.confidence,
            ))

    # Memory Analyzer
    if run_all or "memory" in (request.analyzers or []):
        analyzer = MemoryAnalyzer()
        mem_findings = analyzer.analyze(request.code, request.file_path)
        findings_by_analyzer["memory"] = len(mem_findings)
        for f in mem_findings:
            findings.append(EnhancedFindingResponse(
                analyzer="memory",
                category=StabilityCategory.MEMORY_INTENSIVE.value,
                issue_type=f.issue_type.value,
                line_number=f.line_number,
                variable_name=f.variable_name,
                severity=f.severity.value,
                description=f.description,
                suggested_fix=f.suggested_fix,
                confidence=f.confidence,
            ))

    # Session Analyzer
    if run_all or "session" in (request.analyzers or []):
        analyzer = SessionAnalyzer()
        sess_findings = analyzer.analyze(request.code, request.file_path)
        findings_by_analyzer["session"] = len(sess_findings)
        for f in sess_findings:
            findings.append(EnhancedFindingResponse(
                analyzer="session",
                category=StabilityCategory.SESSION_STATE.value,
                issue_type=f.issue_type.value,
                line_number=f.line_number,
                variable_name=f.variable_name,
                severity=f.severity.value,
                description=f.description,
                suggested_fix=f.suggested_fix,
                confidence=f.confidence,
            ))

    return EnhancedAnalyzeResponse(
        file_path=request.file_path,
        total_findings=len(findings),
        findings_by_analyzer=findings_by_analyzer,
        findings=findings,
    )


class ResolveIncludesRequest(BaseModel):
    """Request to resolve include files."""
    root_file: str = Field(..., description="Root file to start from")
    web_root: Optional[str] = Field(None, description="Web root directory")
    include_merged: bool = Field(False, description="Include merged content")


class IncludeDirectiveResponse(BaseModel):
    """An include directive found in a file."""
    line_number: int
    include_type: str
    path: str
    resolved_path: Optional[str]
    exists: bool


class IncludeGraphResponse(BaseModel):
    """Include dependency graph response."""
    root_file: str
    total_files: int
    circular_refs: List[List[str]]
    include_order: List[str]
    directives: List[IncludeDirectiveResponse]
    merged_content: Optional[str]


@router.post("/includes/resolve", response_model=IncludeGraphResponse)
async def resolve_includes(request: ResolveIncludesRequest) -> IncludeGraphResponse:
    """
    Resolve include files and build dependency graph.

    Week 144: Include file resolver for cross-file analysis.
    """
    import os

    if not os.path.exists(request.root_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {request.root_file}"
        )

    resolver = IncludeResolver(web_root=request.web_root)

    # Build include graph
    graph = resolver.build_include_graph(request.root_file)

    # Get include order
    include_order = graph.get_include_order(os.path.abspath(request.root_file))

    # Get merged content if requested
    merged_content = None
    if request.include_merged:
        merged = resolver.get_merged_content(request.root_file)
        merged_content = merged.content

    # Get directives from root file
    root_resolved = resolver.load_file(request.root_file)
    directives = [
        IncludeDirectiveResponse(
            line_number=d.line_number,
            include_type=d.include_type,
            path=d.path,
            resolved_path=d.resolved_path,
            exists=d.exists,
        )
        for d in root_resolved.includes
    ]

    return IncludeGraphResponse(
        root_file=request.root_file,
        total_files=len(graph.all_files),
        circular_refs=[list(ref) for ref in graph.circular_refs],
        include_order=include_order,
        directives=directives,
        merged_content=merged_content,
    )


@router.get("/analyzers")
async def list_analyzers() -> dict:
    """List available stability analyzers."""
    return {
        "week_143": {
            "classic_asp_leak_detector": {
                "category": StabilityCategory.ADO_LEAKS.value,
                "description": "ADO Connection and Recordset leaks",
                "extensions": [".asp", ".inc"],
            },
            "classic_asp_com_detector": {
                "category": StabilityCategory.COM_OBJECTS.value,
                "description": "COM object leaks (XMLHTTP, ABCpdf, XMLDOM)",
                "extensions": [".asp", ".inc"],
            },
            "classic_asp_file_detector": {
                "category": StabilityCategory.FILE_HANDLES.value,
                "description": "File handle leaks (FSO, TextStream)",
                "extensions": [".asp", ".inc"],
            },
        },
        "week_144": {
            "external_service_analyzer": {
                "category": StabilityCategory.EXTERNAL_SERVICES.value,
                "description": "External service timeout, retry, and error handling",
                "extensions": [".asp", ".inc"],
            },
            "memory_analyzer": {
                "category": StabilityCategory.MEMORY_INTENSIVE.value,
                "description": "Memory-intensive operations (PDF, arrays, strings)",
                "extensions": [".asp", ".inc"],
            },
            "session_analyzer": {
                "category": StabilityCategory.SESSION_STATE.value,
                "description": "Session state issues (COM objects, sensitive data)",
                "extensions": [".asp", ".inc", ".asa"],
            },
            "include_resolver": {
                "category": "utility",
                "description": "Resolves and merges include files for cross-file analysis",
                "extensions": [".asp", ".inc"],
            },
        },
        "week_145": {
            "exception_analyzer": {
                "category": StabilityCategory.EXCEPTION_HANDLING.value,
                "description": "Exception handling patterns (On Error Resume Next, Err checks)",
                "extensions": [".asp", ".inc", ".asa"],
            },
            "sql_analyzer": {
                "category": StabilityCategory.SQL_PERFORMANCE.value,
                "description": "SQL performance issues (N+1 queries, injection, transactions)",
                "extensions": [".asp", ".inc"],
            },
        },
    }


# === Week 145-146: Quality Gate Integration ===

from app.services.stability import (
    get_brown_paper_stability_integration,
    get_stability_quality_gate_service,
    StabilityThresholds,
    StabilityGateStatus,
    WORKFLOW_STABILITY_THRESHOLDS,
)
from app.services.stability.detectors import (
    ExceptionAnalyzer,
    SQLAnalyzer,
)


class QualityGateRequest(BaseModel):
    """Request to run stability analysis with quality gate evaluation."""
    project_path: str = Field(..., description="Root path of the project")
    project_name: str = Field(..., description="Name of the project")
    project_id: int = Field(default=0, description="Optional project ID")
    workflow_type: str = Field(default="MIGRATION", description="Workflow type for thresholds")
    exclude_patterns: Optional[List[str]] = Field(default=None, description="Patterns to exclude")


class QualityGateResponse(BaseModel):
    """Response from quality gate evaluation."""
    success: bool
    stability_score: int
    risk_level: str
    gate_status: str
    gate_passed: bool
    message: str
    total_files_scanned: int
    files_with_issues: int
    total_findings: int
    severity_breakdown: dict
    category_breakdown: dict
    blocking_issues: list
    warnings: list
    hotspot_files: list
    top_issues: list
    analysis_time_ms: int


class ThresholdsResponse(BaseModel):
    """Response with threshold configurations."""
    workflow_types: dict
    default: dict


@router.post("/gate/evaluate", response_model=QualityGateResponse)
async def evaluate_quality_gate(request: QualityGateRequest) -> QualityGateResponse:
    """
    Run stability analysis and evaluate against quality gate.

    Week 145-146: Integrated stability analysis with quality gate
    evaluation for migration workflows.
    """
    try:
        gate_service = get_stability_quality_gate_service()

        gate_result = await gate_service.evaluate_project(
            project_path=request.project_path,
            project_name=request.project_name,
            project_id=request.project_id,
            workflow_type=request.workflow_type,
            exclude_patterns=request.exclude_patterns,
        )

        stability_result = gate_result.stability_result

        return QualityGateResponse(
            success=True,
            stability_score=stability_result.stability_score if stability_result else 0,
            risk_level=stability_result.risk_level if stability_result else "unknown",
            gate_status=gate_result.status.value,
            gate_passed=gate_result.status == StabilityGateStatus.PASSED,
            message=gate_result.message,
            total_files_scanned=stability_result.total_files_scanned if stability_result else 0,
            files_with_issues=stability_result.files_with_issues if stability_result else 0,
            total_findings=stability_result.total_findings if stability_result else 0,
            severity_breakdown={
                "critical": stability_result.critical_count if stability_result else 0,
                "high": stability_result.high_count if stability_result else 0,
                "medium": stability_result.medium_count if stability_result else 0,
                "low": stability_result.low_count if stability_result else 0,
            },
            category_breakdown=stability_result.category_breakdown if stability_result else {},
            blocking_issues=gate_result.blocking_issues,
            warnings=gate_result.warnings,
            hotspot_files=stability_result.hotspot_files if stability_result else [],
            top_issues=stability_result.top_issues if stability_result else [],
            analysis_time_ms=gate_result.evaluation_time_ms,
        )

    except Exception as e:
        import logging
        logging.error(f"Quality gate evaluation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quality gate evaluation failed: {str(e)}"
        )


@router.get("/gate/thresholds", response_model=ThresholdsResponse)
async def get_gate_thresholds() -> ThresholdsResponse:
    """
    Get quality gate threshold configurations for all workflow types.
    """
    workflow_thresholds = {}

    for workflow_type, thresholds in WORKFLOW_STABILITY_THRESHOLDS.items():
        workflow_thresholds[workflow_type] = {
            "max_critical": thresholds.max_critical,
            "max_high": thresholds.max_high,
            "max_medium": thresholds.max_medium,
            "max_low": thresholds.max_low,
            "min_score": thresholds.min_score,
            "max_risk_level": thresholds.max_risk_level,
            "blocking_categories": thresholds.blocking_categories,
        }

    return ThresholdsResponse(
        workflow_types=workflow_thresholds,
        default=workflow_thresholds.get("DEFAULT", {})
    )


class ExceptionAnalyzeRequest(BaseModel):
    """Request to analyze code for exception handling issues."""
    code: str = Field(..., description="Code content to analyze")
    file_path: str = Field("analysis.asp", description="File path for context")


class ExceptionFindingResponse(BaseModel):
    """A finding from the exception analyzer."""
    line_number: int
    issue_type: str
    severity: str
    description: str
    suggested_fix: str
    region_size: int
    confidence: float


@router.post("/analyze/exception")
async def analyze_exception_handling(request: ExceptionAnalyzeRequest) -> dict:
    """
    Analyze code for exception handling issues.

    Week 145: ExceptionAnalyzer for detecting:
    - On Error Resume Next without Err check
    - Missing On Error Goto 0
    - Global error suppression
    - Missing Err.Clear
    """
    analyzer = ExceptionAnalyzer()
    findings = analyzer.analyze(request.code, request.file_path)

    return {
        "file_path": request.file_path,
        "total_findings": len(findings),
        "findings": [
            ExceptionFindingResponse(
                line_number=f.line_number,
                issue_type=f.issue_type.value,
                severity=f.severity.value,
                description=f.description,
                suggested_fix=f.suggested_fix,
                region_size=f.region_size,
                confidence=f.confidence,
            ).model_dump()
            for f in findings
        ],
    }


class SQLAnalyzeRequest(BaseModel):
    """Request to analyze code for SQL performance issues."""
    code: str = Field(..., description="Code content to analyze")
    file_path: str = Field("analysis.asp", description="File path for context")


class SQLFindingResponse(BaseModel):
    """A finding from the SQL analyzer."""
    line_number: int
    issue_type: str
    severity: str
    description: str
    suggested_fix: str
    query_snippet: str
    confidence: float


@router.post("/analyze/sql")
async def analyze_sql_performance(request: SQLAnalyzeRequest) -> dict:
    """
    Analyze code for SQL performance and security issues.

    Week 145: SQLAnalyzer for detecting:
    - N+1 query patterns
    - SQL injection vulnerabilities
    - SELECT * usage
    - Missing query timeouts
    - Transaction handling issues
    """
    analyzer = SQLAnalyzer()
    findings = analyzer.analyze(request.code, request.file_path)

    return {
        "file_path": request.file_path,
        "total_findings": len(findings),
        "findings": [
            SQLFindingResponse(
                line_number=f.line_number,
                issue_type=f.issue_type.value,
                severity=f.severity.value,
                description=f.description,
                suggested_fix=f.suggested_fix,
                query_snippet=f.query_snippet,
                confidence=f.confidence,
            ).model_dump()
            for f in findings
        ],
    }
