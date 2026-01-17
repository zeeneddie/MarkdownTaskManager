"""
CodeWiki API Endpoints - Repository Documentation Analysis

Week 62: Code Understanding Integration

Endpoints for:
- Repository analysis via CodeWiki
- Module tree retrieval
- Diagram access (Mermaid)
- Agent context retrieval
"""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.codewiki_service import CodeWikiService
from app.models.codewiki import (
    CodeWikiAnalysis, CodeWikiAnalysisStatus,
    CodeWikiModule, CodeWikiDiagram, DiagramType
)

router = APIRouter(prefix="/codewiki", tags=["CodeWiki"])


# ============ Request/Response Models ============

class AnalyzeRequest(BaseModel):
    """Request to start repository analysis."""
    repository_path: str = Field(..., description="Path to repository")
    branch: str = Field(default="main", description="Git branch to analyze")


class AnalysisResponse(BaseModel):
    """Analysis status response."""
    id: int
    project_id: int
    repository_path: str
    branch: str
    languages_detected: List[str]
    status: str
    status_message: Optional[str]
    progress_percent: int
    total_files: int
    total_modules: int
    total_functions: int
    total_classes: int
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    created_at: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, analysis: CodeWikiAnalysis) -> "AnalysisResponse":
        return cls(
            id=analysis.id,
            project_id=analysis.project_id,
            repository_path=analysis.repository_path,
            branch=analysis.branch or "main",
            languages_detected=analysis.languages_detected or [],
            status=analysis.status.value if analysis.status else "unknown",
            status_message=analysis.status_message,
            progress_percent=analysis.progress_percent or 0,
            total_files=analysis.total_files or 0,
            total_modules=analysis.total_modules or 0,
            total_functions=analysis.total_functions or 0,
            total_classes=analysis.total_classes or 0,
            started_at=analysis.started_at.isoformat() if analysis.started_at else None,
            completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
            duration_seconds=analysis.duration_seconds,
            created_at=analysis.created_at.isoformat() if analysis.created_at else "",
        )


class ModuleResponse(BaseModel):
    """Module data response."""
    id: int
    name: str
    path: Optional[str]
    level: int
    description: Optional[str]
    purpose: Optional[str]
    file_count: int
    function_count: int
    class_count: int
    line_count: int
    dependencies: List[str]
    external_dependencies: List[str]
    children: List["ModuleResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class DiagramResponse(BaseModel):
    """Diagram data response."""
    id: int
    name: str
    diagram_type: str
    description: Optional[str]
    mermaid_code: str
    has_svg: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class AgentContextResponse(BaseModel):
    """Agent context response."""
    agent_name: str
    context_type: str
    context_summary: str
    context_details: dict
    times_used: int
    last_used_at: Optional[str]


# ============ Analysis Endpoints ============

@router.post("/analyze/{project_id}", response_model=AnalysisResponse)
async def start_analysis(
    project_id: int,
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start CodeWiki repository analysis.

    Creates analysis record and runs analysis in background.
    """
    service = CodeWikiService(db)

    # Create analysis
    analysis = service.create_analysis(
        project_id=project_id,
        repository_path=request.repository_path,
        branch=request.branch,
    )

    # Run analysis in background
    async def run_analysis():
        try:
            await service.run_analysis(analysis.id)
        except Exception as e:
            # Error is logged and stored in analysis record
            pass

    background_tasks.add_task(run_analysis)

    return AnalysisResponse.from_model(analysis)


@router.get("/{project_id}/status", response_model=AnalysisResponse)
async def get_analysis_status(
    project_id: int,
    analysis_id: Optional[int] = Query(None, description="Specific analysis ID"),
    db: Session = Depends(get_db)
):
    """
    Get analysis status.

    If analysis_id is not provided, returns latest analysis for project.
    """
    service = CodeWikiService(db)

    if analysis_id:
        analysis = service.get_analysis(analysis_id)
    else:
        analysis = service.get_latest_analysis(project_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found")

    return AnalysisResponse.from_model(analysis)


@router.get("/{project_id}/analyses", response_model=List[AnalysisResponse])
async def list_analyses(
    project_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """List all analyses for a project."""
    service = CodeWikiService(db)

    status_enum = None
    if status:
        try:
            status_enum = CodeWikiAnalysisStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    analyses = service.get_project_analyses(project_id, status_enum)
    return [AnalysisResponse.from_model(a) for a in analyses]


@router.post("/{project_id}/refresh")
async def refresh_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Re-run analysis for project.

    Creates new analysis and runs in background.
    """
    service = CodeWikiService(db)

    # Get latest analysis to get repository path
    latest = service.get_latest_analysis(project_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No previous analysis found")

    # Create new analysis
    analysis = service.create_analysis(
        project_id=project_id,
        repository_path=latest.repository_path,
        branch=latest.branch or "main",
    )

    # Run in background
    async def run_analysis():
        try:
            await service.run_analysis(analysis.id)
        except Exception:
            pass

    background_tasks.add_task(run_analysis)

    return {
        "message": "Analysis refresh started",
        "analysis_id": analysis.id,
        "status": "pending",
    }


# ============ Module Endpoints ============

@router.get("/{project_id}/modules")
async def get_modules(
    project_id: int,
    level: Optional[int] = Query(None, description="Filter by hierarchy level"),
    format: str = Query("list", description="Output format: list or tree"),
    db: Session = Depends(get_db)
):
    """
    Get module hierarchy.

    Returns modules as flat list or tree structure.
    """
    service = CodeWikiService(db)

    # Get latest completed analysis
    analysis = service.get_latest_analysis(project_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found")

    if format == "tree":
        # Return raw module_tree.json
        tree = service.get_module_tree_json(analysis.id)
        if not tree:
            raise HTTPException(status_code=404, detail="Module tree not available")
        return tree

    # Return flat list
    modules = service.get_modules(analysis.id, level)
    return {
        "analysis_id": analysis.id,
        "total": len(modules),
        "modules": [m.to_dict() for m in modules],
    }


@router.get("/{project_id}/modules/{module_name}")
async def get_module_details(
    project_id: int,
    module_name: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific module."""
    service = CodeWikiService(db)

    analysis = service.get_latest_analysis(project_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found")

    modules = service.get_modules(analysis.id)
    module = next((m for m in modules if m.name == module_name), None)

    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")

    # Get children
    children = [m for m in modules if m.parent_module_id == module.id]

    return {
        **module.to_dict(),
        "documentation": module.documentation_md,
        "children": [c.to_dict() for c in children],
    }


# ============ Diagram Endpoints ============

@router.get("/{project_id}/diagram")
async def get_architecture_diagram(
    project_id: int,
    type: str = Query("architecture", description="Diagram type"),
    db: Session = Depends(get_db)
):
    """
    Get architecture diagram (Mermaid format).

    Returns first diagram of specified type.
    """
    service = CodeWikiService(db)

    analysis = service.get_latest_analysis(project_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found")

    # Parse diagram type
    try:
        diagram_type = DiagramType(type)
    except ValueError:
        diagram_type = DiagramType.ARCHITECTURE

    diagrams = service.get_diagrams(analysis.id, diagram_type)
    if not diagrams:
        # Generate basic diagram from modules
        modules = service.get_modules(analysis.id, level=0)
        mermaid = "graph TD\n"
        for i, m in enumerate(modules[:10]):
            mermaid += f"    M{i}[{m.name}]\n"

        return {
            "analysis_id": analysis.id,
            "diagram_type": type,
            "mermaid_code": mermaid,
            "generated": True,
        }

    diagram = diagrams[0]
    return {
        "analysis_id": analysis.id,
        "diagram_id": diagram.id,
        "name": diagram.name,
        "diagram_type": diagram.diagram_type.value if diagram.diagram_type else type,
        "mermaid_code": diagram.mermaid_code,
        "description": diagram.description,
    }


@router.get("/{project_id}/diagrams", response_model=List[DiagramResponse])
async def list_diagrams(
    project_id: int,
    type: Optional[str] = Query(None, description="Filter by diagram type"),
    db: Session = Depends(get_db)
):
    """List all diagrams for project."""
    service = CodeWikiService(db)

    analysis = service.get_latest_analysis(project_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found")

    diagram_type = None
    if type:
        try:
            diagram_type = DiagramType(type)
        except ValueError:
            pass

    diagrams = service.get_diagrams(analysis.id, diagram_type)

    return [
        DiagramResponse(
            id=d.id,
            name=d.name,
            diagram_type=d.diagram_type.value if d.diagram_type else "unknown",
            description=d.description,
            mermaid_code=d.mermaid_code,
            has_svg=bool(d.svg_content),
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in diagrams
    ]


# ============ Documentation Endpoints ============

@router.get("/{project_id}/docs")
async def get_documentation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get generated documentation.

    Returns overview and module documentation.
    """
    service = CodeWikiService(db)

    analysis = service.get_latest_analysis(project_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found")

    modules = service.get_modules(analysis.id)

    return {
        "analysis_id": analysis.id,
        "overview": analysis.overview_md,
        "modules": {
            m.name: m.documentation_md
            for m in modules
            if m.documentation_md
        },
        "metadata": analysis.metadata_json,
    }


# ============ Agent Context Endpoints ============

@router.get("/{project_id}/agent-context/{agent_name}")
async def get_agent_context(
    project_id: int,
    agent_name: str,
    context_type: Optional[str] = Query(None, description="Specific context type"),
    db: Session = Depends(get_db)
):
    """
    Get CodeWiki context optimized for specific agent.

    Available agents: felix, miguel, quinn, diana
    """
    service = CodeWikiService(db)

    analysis = service.get_latest_analysis(project_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found")

    valid_agents = ["felix", "miguel", "quinn", "diana"]
    if agent_name.lower() not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent. Valid agents: {', '.join(valid_agents)}"
        )

    context = service.get_agent_context(
        analysis.id,
        agent_name.lower(),
        context_type
    )

    if not context:
        raise HTTPException(
            status_code=404,
            detail=f"No context found for agent '{agent_name}'"
        )

    return AgentContextResponse(
        agent_name=context.agent_name,
        context_type=context.context_type,
        context_summary=context.context_summary or "",
        context_details=context.context_details or {},
        times_used=context.times_used or 0,
        last_used_at=context.last_used_at.isoformat() if context.last_used_at else None,
    )


# ============ Utility Endpoints ============

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "codewiki",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported programming languages."""
    return {
        "languages": [
            {"name": "Python", "extensions": [".py"]},
            {"name": "JavaScript", "extensions": [".js", ".jsx", ".mjs"]},
            {"name": "TypeScript", "extensions": [".ts", ".tsx"]},
            {"name": "Java", "extensions": [".java"]},
            {"name": "C", "extensions": [".c", ".h"]},
            {"name": "C++", "extensions": [".cpp", ".hpp", ".cc", ".cxx"]},
            {"name": "C#", "extensions": [".cs"]},
            {"name": "Go", "extensions": [".go"]},
            {"name": "Rust", "extensions": [".rs"]},
        ]
    }
