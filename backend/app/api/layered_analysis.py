"""
Layered Analysis API - Week 77

Endpoints for the 4-layer analysis pipeline:
- Layer 1: VBScript Analysis
- Layer 2: Stored Procedure Analysis
- Layer 3: SWOT Generation
- Layer 4: Improvement Planning
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.layered_analysis_service import LayeredAnalysisService
from app.services.layered_reporting_service import LayeredReportingService
from app.services.improvement_planner_service import PlanningConstraints, ImprovementCategory

router = APIRouter(prefix="/api/layered-analysis", tags=["Layered Analysis"])


# Request/Response Models
class CreateSessionRequest(BaseModel):
    project_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class RunAnalysisRequest(BaseModel):
    vbscript_code: Optional[str] = None
    sp_code: Optional[str] = None
    max_effort_days: Optional[float] = None
    max_items: Optional[int] = None
    focus_categories: Optional[List[str]] = None
    team_size: int = 1


class RunSingleLayerRequest(BaseModel):
    layer: int = Field(..., ge=1, le=4)
    code: Optional[str] = None


class UpdateImprovementRequest(BaseModel):
    status: str = Field(..., pattern="^(identified|planned|in_progress|completed|deferred)$")


class GenerateReportRequest(BaseModel):
    report_type: str = Field(..., pattern="^(executive_summary|technical_deep_dive|improvement_backlog|migration_roadmap|swot_presentation)$")
    format: Optional[str] = "html"
    team_size: Optional[int] = 3
    include_code_samples: Optional[bool] = True


# Session Endpoints
@router.post("/sessions", response_model=Dict[str, Any])
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    """Create a new layered analysis session."""
    service = LayeredAnalysisService(db)
    session = await service.create_session(
        project_id=request.project_id,
        name=request.name,
        description=request.description
    )
    return {
        "id": str(session.id),
        "project_id": str(session.project_id),
        "name": session.name,
        "status": session.status,
        "created_at": session.created_at.isoformat()
    }


@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_sessions(
    project_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List analysis sessions with optional filters."""
    service = LayeredAnalysisService(db)
    return await service.list_sessions(project_id, status, limit)


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get session details with all analysis results."""
    service = LayeredAnalysisService(db)
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.get("/sessions/{session_id}/summary", response_model=Dict[str, Any])
async def get_session_summary(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a summary of the analysis session."""
    service = LayeredAnalysisService(db)
    try:
        return await service.get_session_summary(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Analysis Endpoints
@router.post("/sessions/{session_id}/analyze", response_model=Dict[str, Any])
async def run_full_analysis(
    session_id: UUID,
    request: RunAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Run all 4 layers of analysis."""
    service = LayeredAnalysisService(db)

    # Build constraints
    constraints = None
    if any([request.max_effort_days, request.max_items, request.focus_categories]):
        focus_cats = []
        if request.focus_categories:
            for cat in request.focus_categories:
                try:
                    focus_cats.append(ImprovementCategory(cat))
                except ValueError:
                    pass

        constraints = PlanningConstraints(
            max_effort_days=request.max_effort_days,
            max_items=request.max_items,
            focus_categories=focus_cats,
            team_size=request.team_size
        )

    try:
        return await service.run_full_analysis(
            session_id=session_id,
            vbscript_code=request.vbscript_code,
            sp_code=request.sp_code,
            constraints=constraints
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/layer", response_model=Dict[str, Any])
async def run_single_layer(
    session_id: UUID,
    request: RunSingleLayerRequest,
    db: Session = Depends(get_db)
):
    """Run a single layer of analysis."""
    service = LayeredAnalysisService(db)
    try:
        return await service.run_single_layer(
            session_id=session_id,
            layer=request.layer,
            code=request.code
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Improvement Management
@router.patch("/improvements/{item_id}", response_model=Dict[str, Any])
async def update_improvement_status(
    item_id: UUID,
    request: UpdateImprovementRequest,
    db: Session = Depends(get_db)
):
    """Update the status of an improvement item."""
    service = LayeredAnalysisService(db)
    try:
        return await service.update_improvement_status(item_id, request.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Reporting Endpoints
@router.post("/sessions/{session_id}/reports", response_model=Dict[str, Any])
async def generate_report(
    session_id: UUID,
    request: GenerateReportRequest,
    db: Session = Depends(get_db)
):
    """Generate a report for the analysis session."""
    service = LayeredReportingService(db)

    try:
        if request.report_type == "executive_summary":
            return await service.generate_executive_summary(session_id, request.format or "html")
        elif request.report_type == "technical_deep_dive":
            return await service.generate_technical_report(
                session_id,
                include_code_samples=request.include_code_samples or True
            )
        elif request.report_type == "improvement_backlog":
            return await service.generate_improvement_backlog(session_id, request.format or "csv")
        elif request.report_type == "migration_roadmap":
            return await service.generate_migration_roadmap(session_id, request.team_size or 3)
        elif request.report_type == "swot_presentation":
            return await service.generate_swot_presentation(session_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}/reports", response_model=List[Dict[str, Any]])
async def list_reports(
    session_id: UUID,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List reports for a session."""
    service = LayeredReportingService(db)
    return await service.list_reports(session_id, report_type)


@router.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific report."""
    service = LayeredReportingService(db)
    result = await service.get_report(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


# Quick Analysis Endpoints (without creating session)
@router.post("/analyze/vbscript", response_model=Dict[str, Any])
async def analyze_vbscript_quick(
    code: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Quick VBScript analysis without creating a session."""
    from app.services.vbscript_analyzer_service import VBScriptAnalyzerService

    analyzer = VBScriptAnalyzerService()
    result = await analyzer.analyze(code)
    return result.to_dict()


@router.post("/analyze/stored-procedure", response_model=Dict[str, Any])
async def analyze_sp_quick(
    code: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Quick stored procedure analysis without creating a session."""
    from app.services.stored_procedure_analyzer_service import StoredProcedureAnalyzerService

    analyzer = StoredProcedureAnalyzerService()
    result = await analyzer.analyze(code)
    return result.to_dict()


# Dashboard Data
@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data(
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get dashboard data for layered analysis."""
    service = LayeredAnalysisService(db)

    sessions = await service.list_sessions(project_id, limit=100)

    # Calculate statistics
    total_sessions = len(sessions)
    completed = len([s for s in sessions if s["status"] == "completed"])
    in_progress = len([s for s in sessions if s["status"] == "running"])
    failed = len([s for s in sessions if s["status"] == "failed"])

    # Get recent sessions
    recent = sessions[:5]

    return {
        "statistics": {
            "total_sessions": total_sessions,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "success_rate": (completed / total_sessions * 100) if total_sessions > 0 else 0
        },
        "recent_sessions": recent,
        "layer_info": {
            "layer_1": {
                "name": "VBScript Analysis",
                "description": "Analyze ASP Classic/VBScript code for security, complexity, and modernization"
            },
            "layer_2": {
                "name": "Stored Procedure Analysis",
                "description": "Analyze SQL Server stored procedures for patterns and portability"
            },
            "layer_3": {
                "name": "SWOT Generation",
                "description": "Generate SWOT matrix from analysis findings"
            },
            "layer_4": {
                "name": "Improvement Planning",
                "description": "Create prioritized improvement backlog with roadmap"
            }
        }
    }
