"""
Software Intake API - Fase 1: Automated Code Analysis

Provides endpoints for automated software intake analysis without requiring
user questions. This is the code-driven intake that:
- Scans source code
- Detects technologies and frameworks
- Analyzes security issues (CWE)
- Estimates migration effort
- Generates comprehensive IntakeReport

Week 158 - Separated from Brown Paper workflow for clarity.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
import asyncio
import json

from app.schemas.intake import (
    IntakeReport,
    IntakeStatus,
    IntakeOptions,
    Complexity,
)
from app.services.software_intake_service import (
    SoftwareIntakeService,
    AnalysisProgress,
)

router = APIRouter(prefix="/api/software-intake", tags=["Software Intake - Code Analysis"])

# Service singleton
_intake_service = SoftwareIntakeService()

# In-memory storage for progress (in production, use Redis)
_analysis_progress: Dict[str, AnalysisProgress] = {}
_analysis_reports: Dict[str, IntakeReport] = {}


# ============================================================
# PYDANTIC SCHEMAS (API-specific)
# ============================================================

class IntakeAnalyzeRequest(BaseModel):
    """Request to start a new software intake analysis."""
    project_path: str = Field(..., description="Path to the source code directory")
    project_name: Optional[str] = Field(None, description="Optional project name")
    target_stack: Optional[str] = Field(
        None,
        description="Target technology stack: dotnet8, python_fastapi, nodejs_nestjs, java_spring"
    )
    include_phases: Optional[List[str]] = Field(
        None,
        description="Specific phases to run. If None, runs all phases."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_path": "/home/projects/legacy-app",
                "project_name": "Legacy CRM System",
                "target_stack": "dotnet8"
            }
        }
    )


class IntakeAnalyzeResponse(BaseModel):
    """Response when starting an intake analysis."""
    intake_id: UUID
    status: str
    message: str
    progress_url: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intake_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "analyzing",
                "message": "Intake analysis started",
                "progress_url": "/api/software-intake/123e4567-e89b-12d3-a456-426614174000/progress"
            }
        }
    )


class IntakeProgressResponse(BaseModel):
    """Response with current analysis progress."""
    intake_id: UUID
    status: str
    current_phase: Optional[str] = None
    progress_percent: int = 0
    phases_completed: List[str] = Field(default_factory=list)
    phases_pending: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intake_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "analyzing",
                "current_phase": "security",
                "progress_percent": 45,
                "phases_completed": ["stack_detection", "code_metrics"],
                "phases_pending": ["estimation", "architecture", "dependencies", "business_rules", "aggregation"]
            }
        }
    )


class IntakeSummaryResponse(BaseModel):
    """Summary of an intake analysis for listing."""
    intake_id: UUID
    project_path: str
    project_name: Optional[str] = None
    status: str
    health_score: int = 0
    total_files: int = 0
    total_loc: int = 0
    primary_language: Optional[str] = None
    migration_complexity: str = "unknown"
    analyzed_at: Optional[datetime] = None


class IntakeListResponse(BaseModel):
    """Response for listing all intakes."""
    intakes: List[IntakeSummaryResponse]
    total: int


# ============================================================
# BACKGROUND TASK
# ============================================================

async def run_intake_analysis(
    intake_id: str,
    project_path: str,
    options: IntakeOptions,
):
    """Background task to run the intake analysis."""
    async def progress_callback(progress: AnalysisProgress):
        _analysis_progress[intake_id] = progress

    try:
        report = await _intake_service.analyze(
            project_path=project_path,
            options=options,
            progress_callback=progress_callback,
        )
        _analysis_reports[intake_id] = report
    except Exception as e:
        # Store error in progress
        if intake_id in _analysis_progress:
            progress = _analysis_progress[intake_id]
            progress.status = IntakeStatus.FAILED
            progress.error_message = str(e)


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post(
    "/analyze",
    response_model=IntakeAnalyzeResponse,
    summary="Start Software Intake Analysis",
    description="""
    Starts an automated software intake analysis on the specified project path.

    The analysis runs asynchronously in the background. Use the returned
    progress_url to poll for status, or use the SSE endpoint for real-time updates.

    **Phases executed:**
    1. Stack Detection - Detect languages, frameworks, databases
    2. Code Metrics - LOC, complexity, duplication
    3. Security Scan - CWE issues, OWASP coverage
    4. Estimation - Function points, effort hours
    5. Architecture - Layer detection, component mapping
    6. Dependencies - Internal/external dependency graph
    7. Business Rules - Extract embedded business logic
    8. Aggregation - Compile findings and recommendations
    """
)
async def start_intake_analysis(
    request: IntakeAnalyzeRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new software intake analysis."""
    # Generate intake ID
    intake_id = uuid4()

    # Build options
    options = IntakeOptions(
        target_stack=request.target_stack,
        include_phases=request.include_phases,
    )

    # Initialize progress
    _analysis_progress[str(intake_id)] = AnalysisProgress(
        intake_id=intake_id,
        status=IntakeStatus.PENDING,
    )

    # Start background analysis
    background_tasks.add_task(
        run_intake_analysis,
        str(intake_id),
        request.project_path,
        options,
    )

    return IntakeAnalyzeResponse(
        intake_id=intake_id,
        status="analyzing",
        message="Intake analysis started",
        progress_url=f"/api/software-intake/{intake_id}/progress",
    )


@router.get(
    "/{intake_id}/progress",
    response_model=IntakeProgressResponse,
    summary="Get Analysis Progress",
    description="Returns the current progress of an intake analysis."
)
async def get_intake_progress(intake_id: UUID):
    """Get the current progress of an intake analysis."""
    progress = _analysis_progress.get(str(intake_id))

    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"Intake analysis {intake_id} not found"
        )

    # Determine completed/pending phases
    phases_completed = []
    phases_pending = []
    for phase_name, phase_info in progress.phases.items():
        if phase_info.status == "completed":
            phases_completed.append(phase_name)
        elif phase_info.status == "pending":
            phases_pending.append(phase_name)

    return IntakeProgressResponse(
        intake_id=progress.intake_id,
        status=progress.status.value,
        current_phase=progress.current_phase,
        progress_percent=progress.progress_percent,
        phases_completed=phases_completed,
        phases_pending=phases_pending,
        error_message=progress.error_message,
    )


@router.get(
    "/{intake_id}/progress/stream",
    summary="Stream Analysis Progress (SSE)",
    description="Server-Sent Events stream for real-time progress updates."
)
async def stream_intake_progress(intake_id: UUID):
    """Stream analysis progress as Server-Sent Events."""
    async def event_generator():
        last_percent = -1
        while True:
            progress = _analysis_progress.get(str(intake_id))

            if not progress:
                yield f"data: {json.dumps({'error': 'Intake not found'})}\n\n"
                break

            # Only send if changed
            if progress.progress_percent != last_percent:
                last_percent = progress.progress_percent
                data = {
                    "intake_id": str(progress.intake_id),
                    "status": progress.status.value,
                    "current_phase": progress.current_phase,
                    "progress_percent": progress.progress_percent,
                }
                yield f"data: {json.dumps(data)}\n\n"

            # Check if done
            if progress.status in [IntakeStatus.COMPLETED, IntakeStatus.FAILED]:
                yield f"data: {json.dumps({'status': progress.status.value, 'done': True})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get(
    "/{intake_id}",
    response_model=IntakeReport,
    summary="Get Intake Report",
    description="""
    Retrieves the complete intake report for an analysis.

    The report contains:
    - **summary**: High-level metrics (LOC, files, health score)
    - **findings**: Categorized issues with severity and recommendations
    - **code_metrics**: Detailed code quality metrics
    - **security**: Security vulnerabilities and CWE coverage
    - **estimation**: Function points and effort estimation
    - **architecture**: Detected layers and component mappings
    - **dependencies**: Dependency graph and outdated packages
    - **business_rules**: Extracted business logic patterns
    - **recommendations**: Prioritized improvement actions
    """
)
async def get_intake_report(intake_id: UUID):
    """Get the complete intake report."""
    report = _analysis_reports.get(str(intake_id))

    if not report:
        # Check if analysis is still running
        progress = _analysis_progress.get(str(intake_id))
        if progress and progress.status == IntakeStatus.ANALYZING:
            raise HTTPException(
                status_code=202,
                detail="Analysis still in progress",
                headers={"Retry-After": "5"}
            )
        raise HTTPException(
            status_code=404,
            detail=f"Intake report {intake_id} not found"
        )

    return report


@router.get(
    "",
    response_model=IntakeListResponse,
    summary="List All Intakes",
    description="Returns a list of all intake analyses with summary information."
)
async def list_intakes(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all intake analyses."""
    summaries = []

    for stored_id, report in _analysis_reports.items():
        # Apply status filter
        if status and report.status.value != status:
            continue

        summaries.append(IntakeSummaryResponse(
            intake_id=UUID(stored_id),  # Use the storage key, not report.id
            project_path=report.project_path,
            project_name=report.project_name,
            status=report.status.value,
            health_score=report.summary.health_score,
            total_files=report.summary.total_files,
            total_loc=report.summary.total_loc,
            primary_language=report.summary.primary_language,
            migration_complexity=report.summary.migration_complexity.value if report.summary.migration_complexity else "unknown",
            analyzed_at=report.analyzed_at,
        ))

    # Also include in-progress analyses
    for intake_id, progress in _analysis_progress.items():
        if intake_id not in _analysis_reports:
            if status and progress.status.value != status:
                continue
            summaries.append(IntakeSummaryResponse(
                intake_id=progress.intake_id,
                project_path="",  # Not available yet
                status=progress.status.value,
            ))

    # Sort by analyzed_at descending (most recent first)
    summaries.sort(key=lambda x: x.analyzed_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # Apply pagination
    total = len(summaries)
    summaries = summaries[offset:offset + limit]

    return IntakeListResponse(
        intakes=summaries,
        total=total,
    )


@router.delete(
    "/{intake_id}",
    summary="Delete Intake Analysis",
    description="Deletes an intake analysis and its report."
)
async def delete_intake(intake_id: UUID):
    """Delete an intake analysis."""
    intake_id_str = str(intake_id)

    deleted = False
    if intake_id_str in _analysis_reports:
        del _analysis_reports[intake_id_str]
        deleted = True
    if intake_id_str in _analysis_progress:
        del _analysis_progress[intake_id_str]
        deleted = True

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Intake {intake_id} not found"
        )

    return {"message": f"Intake {intake_id} deleted"}


@router.get(
    "/{intake_id}/export",
    summary="Export Intake Report",
    description="Export the intake report in various formats."
)
async def export_intake_report(
    intake_id: UUID,
    format: str = Query("json", description="Export format: json, markdown, pdf"),
):
    """Export intake report in specified format."""
    report = _analysis_reports.get(str(intake_id))

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Intake report {intake_id} not found"
        )

    if format == "json":
        return report.model_dump()

    elif format == "markdown":
        # Generate markdown summary
        md = f"""# Software Intake Report: {report.project_name or 'Unknown Project'}

## Summary
- **Status:** {report.status.value}
- **Health Score:** {report.summary.health_score}/100
- **Total Files:** {report.summary.total_files:,}
- **Total LOC:** {report.summary.total_loc:,}
- **Primary Language:** {report.summary.primary_language or 'Unknown'}
- **Migration Complexity:** {report.summary.migration_complexity.value if report.summary.migration_complexity else 'Unknown'}

## Findings
- **Total:** {report.findings.summary.total}
- **Critical:** {report.findings.summary.critical}
- **High:** {report.findings.summary.high}
- **Medium:** {report.findings.summary.medium}
- **Low:** {report.findings.summary.low}

"""
        if report.security:
            md += f"""## Security
- **Risk Score:** {report.security.risk_score}
- **Top Findings:** {len(report.security.top_findings)}
- **Migration Blockers:** {len(report.security.migration_blockers)}
- **Remediation Hours:** {report.security.estimated_remediation_hours}

"""
        if report.estimation:
            md += f"""## Estimation
- **Function Points:** {report.estimation.function_points_adjusted}
- **Effort Hours:** {report.estimation.effort_hours:,.0f}
- **Confidence:** {report.estimation.confidence.value}

"""
        if report.architecture:
            md += f"""## Architecture
- **Recommended Pattern:** {report.architecture.recommended_pattern}
- **Migration Strategy:** {report.architecture.recommended_strategy}
- **Detected Layers:** {len(report.architecture.detected_layers)}
- **Component Mappings:** {len(report.architecture.component_mapping)}

"""
        return StreamingResponse(
            iter([md]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=intake-{intake_id}.md"
            }
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format: {format}. Use json or markdown."
        )


@router.post(
    "/{intake_id}/rerun",
    response_model=IntakeAnalyzeResponse,
    summary="Re-run Intake Analysis",
    description="Re-runs the intake analysis with the same or updated options."
)
async def rerun_intake_analysis(
    intake_id: UUID,
    background_tasks: BackgroundTasks,
    target_stack: Optional[str] = Query(None, description="Override target stack"),
):
    """Re-run an intake analysis."""
    old_report = _analysis_reports.get(str(intake_id))

    if not old_report:
        raise HTTPException(
            status_code=404,
            detail=f"Intake {intake_id} not found"
        )

    # Generate new intake ID
    new_intake_id = uuid4()

    # Build options
    options = IntakeOptions(
        target_stack=target_stack or (old_report.analysis_options.target_stack if old_report.analysis_options else None),
    )

    # Initialize progress
    _analysis_progress[str(new_intake_id)] = AnalysisProgress(
        intake_id=new_intake_id,
        status=IntakeStatus.PENDING,
    )

    # Start background analysis
    background_tasks.add_task(
        run_intake_analysis,
        str(new_intake_id),
        old_report.project_path,
        options,
    )

    return IntakeAnalyzeResponse(
        intake_id=new_intake_id,
        status="analyzing",
        message=f"Re-running intake analysis (original: {intake_id})",
        progress_url=f"/api/software-intake/{new_intake_id}/progress",
    )


# ============================================================
# BACKLOG GENERATION
# ============================================================

# Import backlog service
from app.services.intake_to_backlog_service import (
    IntakeToBacklogService,
    BacklogGenerationResult,
)

_backlog_service = IntakeToBacklogService()


class BacklogGenerationResponse(BaseModel):
    """Response for backlog generation."""
    intake_id: UUID
    generated_at: datetime
    statistics: Dict[str, Any]
    domains: List[Dict[str, Any]]
    epics: List[Dict[str, Any]]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intake_id": "123e4567-e89b-12d3-a456-426614174000",
                "generated_at": "2026-01-20T12:00:00Z",
                "statistics": {
                    "total_epics": 5,
                    "total_features": 15,
                    "total_stories": 45,
                    "total_estimated_fp": 250,
                    "total_estimated_hours": 1250
                },
                "domains": [],
                "epics": []
            }
        }
    )


@router.post(
    "/{intake_id}/generate-backlog",
    response_model=BacklogGenerationResponse,
    summary="Generate Backlog from Intake",
    description="""
    Generate a structured backlog (Domains → Epics → Features → Stories) from an intake report.

    **Process:**
    1. Extract business domains from architecture components and business rules
    2. Generate epics from domains (1 epic per domain)
    3. Generate special epics (Security, Infrastructure, Data Migration)
    4. Generate features per component type
    5. Generate stories from business rules and findings

    **Returns:**
    - Extracted domains with priority scores
    - Generated epics with features and stories
    - Estimation statistics (FP, hours)
    """
)
async def generate_backlog_from_intake(intake_id: UUID):
    """Generate a backlog from an intake report."""
    report = _analysis_reports.get(str(intake_id))

    if not report:
        # Check if analysis is still running
        progress = _analysis_progress.get(str(intake_id))
        if progress and progress.status == IntakeStatus.ANALYZING:
            raise HTTPException(
                status_code=202,
                detail="Analysis still in progress. Wait for completion before generating backlog.",
                headers={"Retry-After": "10"}
            )
        raise HTTPException(
            status_code=404,
            detail=f"Intake report {intake_id} not found"
        )

    # Generate backlog
    result = _backlog_service.generate_backlog(report)

    return BacklogGenerationResponse(
        intake_id=result.intake_id,
        generated_at=result.generated_at,
        statistics={
            "total_domains": len(result.domains),
            "total_epics": result.total_epics,
            "total_features": result.total_features,
            "total_stories": result.total_stories,
            "total_estimated_fp": result.total_estimated_fp,
            "total_estimated_hours": result.total_estimated_hours,
        },
        domains=[d.to_dict() for d in result.domains],
        epics=[e.to_dict() for e in result.epics],
    )
