"""
Code Analysis API - Week 83

Endpoints for the Code Analysis Aggregator service.

Features:
- Trigger code analysis for a repository
- Get analysis results and status
- Query knowledge graph entries
- Generate LLM context from analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.code_analysis import CodeAnalysisAggregation, PotpieKnowledgeGraphEntry
from app.models.project import Project
from app.services.code_analysis_aggregator_service import (
    CodeAnalysisAggregatorService,
    get_aggregator_service,
    AggregatedAnalysis,
)
from app.services.potpie_adapter import PotpieAdapter, get_potpie_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code-analysis", tags=["code-analysis"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeRepositoryRequest(BaseModel):
    """Request to analyze a repository."""
    repository_path: str = Field(..., description="Path to the repository")
    branch: str = Field("main", description="Git branch to analyze")
    include_codewiki: bool = Field(True, description="Include CodeWiki analysis (slower)")
    include_potpie: bool = Field(True, description="Include Potpie knowledge graph")


class AnalysisStatusResponse(BaseModel):
    """Response with analysis status."""
    id: str
    project_id: int
    repository_path: str
    status: str
    analysis_score: Optional[float]
    duration_ms: Optional[int]
    created_at: datetime
    technology_summary: Optional[Dict[str, Any]]


class TechnologyProfileResponse(BaseModel):
    """Technology profile response."""
    primary_stack: Optional[str]
    secondary_stacks: List[str]
    database_type: Optional[str]
    languages: Dict[str, int]
    frameworks: List[str]
    total_files: int
    total_loc: int


class DependencyProfileResponse(BaseModel):
    """Dependency profile response."""
    module_count: int
    edge_count: int
    circular_dependencies: int
    external_dependencies: int
    internal_dependencies: int
    coupling_score: Optional[float]
    hub_modules: List[str]


class ComplexityProfileResponse(BaseModel):
    """Complexity profile response."""
    avg_cyclomatic: Optional[float]
    max_cyclomatic: Optional[float]
    total_functions: int
    high_complexity_count: int
    complexity_rating: Optional[str]


class KnowledgeGraphNodeResponse(BaseModel):
    """Knowledge graph node response."""
    id: str
    node_type: str
    node_name: str
    node_path: Optional[str]
    language: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    complexity: Optional[float]
    imports_count: int
    imported_by_count: int
    calls_count: int
    called_by_count: int


class LLMContextResponse(BaseModel):
    """LLM context response."""
    context: str
    token_estimate: int
    analysis_id: str


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@router.post("/analyze/{project_id}", response_model=AnalysisStatusResponse)
async def analyze_repository(
    project_id: int,
    request: AnalyzeRepositoryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger code analysis for a repository.

    This starts an asynchronous analysis that includes:
    - Technology stack detection
    - Dependency graph analysis
    - Code complexity metrics
    - Optional: CodeWiki documentation analysis
    - Optional: Potpie knowledge graph generation

    Returns immediately with analysis ID for polling.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create aggregation record
    aggregation = CodeAnalysisAggregation(
        project_id=project_id,
        repository_path=request.repository_path,
        branch=request.branch,
        status="pending",
    )
    db.add(aggregation)
    db.commit()
    db.refresh(aggregation)

    # Schedule background analysis
    background_tasks.add_task(
        _run_analysis,
        str(aggregation.id),
        project_id,
        request.repository_path,
        request.branch,
        request.include_codewiki,
        request.include_potpie,
    )

    return AnalysisStatusResponse(
        id=str(aggregation.id),
        project_id=project_id,
        repository_path=request.repository_path,
        status="pending",
        analysis_score=None,
        duration_ms=None,
        created_at=aggregation.created_at,
        technology_summary=None,
    )


async def _run_analysis(
    aggregation_id: str,
    project_id: int,
    repository_path: str,
    branch: str,
    include_codewiki: bool,
    include_potpie: bool,
):
    """Background task to run the analysis."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        # Update status to running
        aggregation = db.query(CodeAnalysisAggregation).filter(
            CodeAnalysisAggregation.id == aggregation_id
        ).first()

        if not aggregation:
            logger.error(f"Aggregation not found: {aggregation_id}")
            return

        aggregation.status = "running"
        db.commit()

        # Run aggregator service
        service = get_aggregator_service(db)
        result = await service.analyze(
            project_id=project_id,
            repository_path=repository_path,
            branch=branch,
            include_codewiki=include_codewiki,
        )

        # Store results
        aggregation.status = "completed" if result.is_successful else "failed"
        aggregation.duration_ms = result.duration_ms
        aggregation.analysis_score = result.analysis_score

        # Technology profile
        aggregation.primary_stack = result.technology.primary_stack
        aggregation.secondary_stacks = result.technology.secondary_stacks
        aggregation.database_type = result.technology.database_type
        aggregation.languages = result.technology.languages
        aggregation.frameworks = result.technology.frameworks
        aggregation.total_files = result.technology.total_files
        aggregation.total_loc = result.technology.total_loc

        # Dependency profile
        aggregation.module_count = result.dependencies.module_count
        aggregation.edge_count = result.dependencies.edge_count
        aggregation.circular_dependencies = result.dependencies.circular_dependencies
        aggregation.entry_points = result.dependencies.entry_points
        aggregation.hub_modules = result.dependencies.hub_modules
        aggregation.external_dependencies = result.dependencies.external_dependencies
        aggregation.internal_dependencies = result.dependencies.internal_dependencies
        aggregation.instability_avg = result.dependencies.instability_avg
        aggregation.coupling_score = result.dependencies.coupling_score

        # Complexity profile
        aggregation.avg_cyclomatic = result.complexity.avg_cyclomatic
        aggregation.max_cyclomatic = result.complexity.max_cyclomatic
        aggregation.total_functions = result.complexity.total_functions
        aggregation.high_complexity_count = result.complexity.high_complexity_count
        aggregation.complexity_rating = result.complexity.complexity_rating

        # Documentation profile
        aggregation.documented_ratio = result.documentation.documented_ratio
        aggregation.diagram_count = result.documentation.diagram_count
        aggregation.readme_exists = result.documentation.readme_exists
        aggregation.architecture_detected = result.documentation.architecture_detected

        # Errors/warnings
        aggregation.errors = result.errors
        aggregation.warnings = result.warnings

        db.commit()

        # Run Potpie if requested
        if include_potpie:
            potpie_adapter = get_potpie_adapter(db)
            graph = await potpie_adapter.analyze_repository(repository_path)
            await potpie_adapter.store_graph(UUID(aggregation_id), graph)

        logger.info(f"Analysis complete: {aggregation_id}, score={result.analysis_score}")

    except Exception as e:
        logger.exception(f"Analysis failed: {aggregation_id}")
        aggregation.status = "failed"
        aggregation.errors = [str(e)]
        db.commit()
    finally:
        db.close()


@router.get("/status/{aggregation_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    aggregation_id: str,
    db: Session = Depends(get_db)
):
    """Get the status of an analysis."""
    aggregation = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.id == aggregation_id
    ).first()

    if not aggregation:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisStatusResponse(
        id=str(aggregation.id),
        project_id=aggregation.project_id,
        repository_path=aggregation.repository_path,
        status=aggregation.status,
        analysis_score=aggregation.analysis_score,
        duration_ms=aggregation.duration_ms,
        created_at=aggregation.created_at,
        technology_summary={
            "primary_stack": aggregation.primary_stack,
            "total_files": aggregation.total_files,
            "total_loc": aggregation.total_loc,
        } if aggregation.primary_stack else None,
    )


@router.get("/project/{project_id}/latest")
async def get_latest_analysis(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get the most recent analysis for a project."""
    aggregation = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.project_id == project_id
    ).order_by(CodeAnalysisAggregation.created_at.desc()).first()

    if not aggregation:
        raise HTTPException(status_code=404, detail="No analysis found for project")

    return {
        "id": str(aggregation.id),
        "project_id": aggregation.project_id,
        "repository_path": aggregation.repository_path,
        "status": aggregation.status,
        "analysis_score": aggregation.analysis_score,
        "duration_ms": aggregation.duration_ms,
        "created_at": aggregation.created_at.isoformat() if aggregation.created_at else None,
        "technology": {
            "primary_stack": aggregation.primary_stack,
            "secondary_stacks": aggregation.secondary_stacks or [],
            "database_type": aggregation.database_type,
            "languages": aggregation.languages or {},
            "total_files": aggregation.total_files,
            "total_loc": aggregation.total_loc,
        },
        "dependencies": {
            "module_count": aggregation.module_count,
            "edge_count": aggregation.edge_count,
            "circular_dependencies": aggregation.circular_dependencies,
            "coupling_score": aggregation.coupling_score,
            "hub_modules": aggregation.hub_modules or [],
        },
        "complexity": {
            "avg_cyclomatic": aggregation.avg_cyclomatic,
            "max_cyclomatic": aggregation.max_cyclomatic,
            "total_functions": aggregation.total_functions,
            "complexity_rating": aggregation.complexity_rating,
        },
        "errors": aggregation.errors or [],
        "warnings": aggregation.warnings or [],
    }


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

@router.get("/{aggregation_id}/technology", response_model=TechnologyProfileResponse)
async def get_technology_profile(
    aggregation_id: str,
    db: Session = Depends(get_db)
):
    """Get technology profile for an analysis."""
    aggregation = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.id == aggregation_id
    ).first()

    if not aggregation:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return TechnologyProfileResponse(
        primary_stack=aggregation.primary_stack,
        secondary_stacks=aggregation.secondary_stacks or [],
        database_type=aggregation.database_type,
        languages=aggregation.languages or {},
        frameworks=aggregation.frameworks or [],
        total_files=aggregation.total_files,
        total_loc=aggregation.total_loc,
    )


@router.get("/{aggregation_id}/dependencies", response_model=DependencyProfileResponse)
async def get_dependency_profile(
    aggregation_id: str,
    db: Session = Depends(get_db)
):
    """Get dependency profile for an analysis."""
    aggregation = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.id == aggregation_id
    ).first()

    if not aggregation:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return DependencyProfileResponse(
        module_count=aggregation.module_count,
        edge_count=aggregation.edge_count,
        circular_dependencies=aggregation.circular_dependencies,
        external_dependencies=aggregation.external_dependencies,
        internal_dependencies=aggregation.internal_dependencies,
        coupling_score=aggregation.coupling_score,
        hub_modules=aggregation.hub_modules or [],
    )


@router.get("/{aggregation_id}/complexity", response_model=ComplexityProfileResponse)
async def get_complexity_profile(
    aggregation_id: str,
    db: Session = Depends(get_db)
):
    """Get complexity profile for an analysis."""
    aggregation = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.id == aggregation_id
    ).first()

    if not aggregation:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return ComplexityProfileResponse(
        avg_cyclomatic=aggregation.avg_cyclomatic,
        max_cyclomatic=aggregation.max_cyclomatic,
        total_functions=aggregation.total_functions,
        high_complexity_count=aggregation.high_complexity_count,
        complexity_rating=aggregation.complexity_rating,
    )


# ============================================================================
# KNOWLEDGE GRAPH ENDPOINTS
# ============================================================================

@router.get("/{aggregation_id}/knowledge-graph/nodes")
async def get_knowledge_graph_nodes(
    aggregation_id: str,
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get knowledge graph nodes for an analysis."""
    query = db.query(PotpieKnowledgeGraphEntry).filter(
        PotpieKnowledgeGraphEntry.aggregation_id == aggregation_id
    )

    if node_type:
        query = query.filter(PotpieKnowledgeGraphEntry.node_type == node_type)

    if language:
        query = query.filter(PotpieKnowledgeGraphEntry.language == language)

    total = query.count()
    nodes = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "nodes": [
            {
                "id": str(n.id),
                "node_type": n.node_type,
                "node_name": n.node_name,
                "node_path": n.node_path,
                "language": n.language,
                "line_start": n.line_start,
                "line_end": n.line_end,
                "complexity": n.complexity,
                "imports_count": len(n.imports or []),
                "imported_by_count": len(n.imported_by or []),
                "calls_count": len(n.calls or []),
                "called_by_count": len(n.called_by or []),
            }
            for n in nodes
        ]
    }


@router.get("/{aggregation_id}/knowledge-graph/search")
async def search_knowledge_graph(
    aggregation_id: str,
    query: str = Query(..., min_length=2),
    node_type: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Search knowledge graph by name pattern."""
    q = db.query(PotpieKnowledgeGraphEntry).filter(
        PotpieKnowledgeGraphEntry.aggregation_id == aggregation_id,
        PotpieKnowledgeGraphEntry.node_name.ilike(f"%{query}%")
    )

    if node_type:
        q = q.filter(PotpieKnowledgeGraphEntry.node_type == node_type)

    nodes = q.limit(limit).all()

    return {
        "query": query,
        "results": [n.to_dict() for n in nodes]
    }


@router.get("/{aggregation_id}/knowledge-graph/call-graph/{function_name}")
async def get_call_graph(
    aggregation_id: str,
    function_name: str,
    depth: int = Query(2, le=5),
    db: Session = Depends(get_db)
):
    """Get call graph for a function."""
    adapter = get_potpie_adapter(db)
    graph = await adapter.get_call_graph(function_name, UUID(aggregation_id), depth)
    return graph


# ============================================================================
# LLM CONTEXT ENDPOINT
# ============================================================================

@router.get("/{aggregation_id}/llm-context", response_model=LLMContextResponse)
async def get_llm_context(
    aggregation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get optimized LLM context string for an analysis.

    This returns a token-efficient summary suitable for
    including in LLM prompts for code analysis tasks.
    """
    aggregation = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.id == aggregation_id
    ).first()

    if not aggregation:
        raise HTTPException(status_code=404, detail="Analysis not found")

    context = aggregation.to_llm_context()

    # Rough token estimate (4 chars per token)
    token_estimate = len(context) // 4

    return LLMContextResponse(
        context=context,
        token_estimate=token_estimate,
        analysis_id=str(aggregation.id),
    )


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/summary")
async def get_analysis_summary(
    db: Session = Depends(get_db)
):
    """Get overall analysis statistics."""
    total = db.query(CodeAnalysisAggregation).count()
    completed = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.status == "completed"
    ).count()
    failed = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.status == "failed"
    ).count()
    running = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.status == "running"
    ).count()

    # Average analysis score
    avg_score_result = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.analysis_score.isnot(None)
    ).all()

    avg_score = (
        sum(a.analysis_score for a in avg_score_result) / len(avg_score_result)
        if avg_score_result else 0
    )

    # Knowledge graph stats
    total_nodes = db.query(PotpieKnowledgeGraphEntry).count()

    return {
        "total_analyses": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "success_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "average_score": round(avg_score, 1),
        "total_knowledge_graph_nodes": total_nodes,
    }
