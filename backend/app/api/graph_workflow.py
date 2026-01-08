"""
Graph Workflow API - Week 88

API endpoints for Graph-Workflow integration:
- Impact analysis for NEW_FEATURE, MAINTENANCE
- Dependency check for BUG
- Coupling metrics for QUALITY_AUDIT, QUALITY_IMPROVEMENT
- Test coverage map for TESTING
- Enhancement scope for ENHANCEMENT
- Sync and document integration
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.graph_workflow_service import GraphWorkflowService, get_graph_workflow_service

router = APIRouter(prefix="/graph-workflow", tags=["Graph Workflow"])


# =========================================================================
# Request/Response Models
# =========================================================================

class ImpactAnalysisRequest(BaseModel):
    """Request for impact analysis."""
    project_id: int = Field(..., description="Project ID")
    changes: List[str] = Field(..., description="List of file paths or entity names to analyze")
    workflow_type: str = Field(default="NEW_FEATURE", description="NEW_FEATURE or MAINTENANCE")
    max_depth: int = Field(default=5, description="Maximum depth for transitive impact")


class DependencyCheckRequest(BaseModel):
    """Request for dependency check."""
    project_id: int = Field(..., description="Project ID")
    entity_name: str = Field(..., description="Name of buggy entity")
    file_path: Optional[str] = Field(None, description="Optional file path to narrow search")


class CouplingMetricsRequest(BaseModel):
    """Request for coupling metrics."""
    project_id: int = Field(..., description="Project ID")
    coupling_threshold: int = Field(default=10, description="Threshold for high coupling")


class TestCoverageRequest(BaseModel):
    """Request for test coverage map."""
    project_id: int = Field(..., description="Project ID")
    test_file_patterns: Optional[List[str]] = Field(
        None,
        description="Patterns to identify test files"
    )


class EnhancementScopeRequest(BaseModel):
    """Request for enhancement scope."""
    project_id: int = Field(..., description="Project ID")
    feature_name: str = Field(..., description="Name/description of enhancement")
    target_entities: Optional[List[str]] = Field(
        None,
        description="Specific entities to enhance"
    )


class SyncAndDocumentRequest(BaseModel):
    """Request for sync and document."""
    project_id: int = Field(..., description="Project ID")
    repo_path: str = Field(..., description="Repository path")
    languages: Optional[List[str]] = Field(None, description="Languages to analyze")


class WorkflowContextRequest(BaseModel):
    """Request for workflow context."""
    project_id: int = Field(..., description="Project ID")
    workflow_type: str = Field(..., description="Type of workflow")
    agent_name: Optional[str] = Field(None, description="Optional agent name")


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/impact-analysis")
async def impact_analysis(
    request: ImpactAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze impact of proposed changes.

    Used by NEW_FEATURE and MAINTENANCE workflows to understand
    the blast radius of changes before implementation.

    Returns:
        ImpactReport with affected entities, files, and risk score
    """
    service = get_graph_workflow_service(db)
    result = await service.graph_impact_analysis(
        project_id=request.project_id,
        changes=request.changes,
        workflow_type=request.workflow_type,
        max_depth=request.max_depth
    )

    if "error" in result and "Graph not synced" not in result.get("warning", ""):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/dependency-check")
async def dependency_check(
    request: DependencyCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Check dependencies for bug investigation.

    Used by BUG workflow to understand what a buggy component
    depends on and what depends on it.

    Returns:
        DependencyReport with upstream/downstream dependencies
    """
    service = get_graph_workflow_service(db)
    result = await service.graph_dependency_check(
        project_id=request.project_id,
        entity_name=request.entity_name,
        file_path=request.file_path
    )

    if "error" in result and "not found" not in result.get("error", ""):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/coupling-metrics")
async def coupling_metrics(
    request: CouplingMetricsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze module coupling for quality assessment.

    Used by QUALITY_AUDIT and QUALITY_IMPROVEMENT workflows
    to identify tightly coupled modules.

    Returns:
        CouplingMetrics with module coupling analysis
    """
    service = get_graph_workflow_service(db)
    result = await service.graph_coupling_metrics(
        project_id=request.project_id,
        coupling_threshold=request.coupling_threshold
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/test-coverage-map")
async def test_coverage_map(
    request: TestCoverageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Map test files to code entities for coverage analysis.

    Used by TESTING workflow to identify untested code
    and suggest test priorities.

    Returns:
        CoverageMap with test-to-code mapping and priorities
    """
    service = get_graph_workflow_service(db)
    result = await service.graph_test_coverage_map(
        project_id=request.project_id,
        test_file_patterns=request.test_file_patterns
    )

    if "error" in result and "Graph not synced" not in result.get("warning", ""):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/enhancement-scope")
async def enhancement_scope(
    request: EnhancementScopeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze scope of a feature enhancement.

    Used by ENHANCEMENT workflow to understand scope
    and impact of enhancing existing functionality.

    Returns:
        ScopeReport with affected scope and risk assessment
    """
    service = get_graph_workflow_service(db)
    result = await service.graph_enhancement_scope(
        project_id=request.project_id,
        feature_name=request.feature_name,
        target_entities=request.target_entities
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/sync-and-document")
async def sync_and_document(
    request: SyncAndDocumentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sync project graph and generate CodeWiki documentation.

    Combines graph sync with auto-documentation for a complete
    project understanding update.

    Returns:
        Combined sync and documentation result
    """
    service = get_graph_workflow_service(db)
    result = await service.sync_and_document(
        project_id=request.project_id,
        repo_path=request.repo_path,
        languages=request.languages
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/workflow-context")
async def get_workflow_context(
    request: WorkflowContextRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get graph and CodeWiki context for a workflow.

    Provides combined context from graph analysis and CodeWiki
    for enhanced workflow processing.

    Returns:
        Combined context for workflow
    """
    service = get_graph_workflow_service(db)
    result = await service.get_workflow_context(
        project_id=request.project_id,
        workflow_type=request.workflow_type,
        agent_name=request.agent_name
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


# =========================================================================
# GET Endpoints for specific workflow types
# =========================================================================

@router.get("/new-feature/{project_id}/impact")
async def new_feature_impact(
    project_id: int,
    changes: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick impact analysis for NEW_FEATURE workflow.

    Args:
        project_id: Project ID
        changes: Comma-separated list of entity names

    Returns:
        Impact analysis result
    """
    service = get_graph_workflow_service(db)
    change_list = [c.strip() for c in changes.split(",")]

    return await service.graph_impact_analysis(
        project_id=project_id,
        changes=change_list,
        workflow_type="NEW_FEATURE"
    )


@router.get("/maintenance/{project_id}/impact")
async def maintenance_impact(
    project_id: int,
    changes: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick impact analysis for MAINTENANCE workflow.

    Args:
        project_id: Project ID
        changes: Comma-separated list of entity names

    Returns:
        Impact analysis result
    """
    service = get_graph_workflow_service(db)
    change_list = [c.strip() for c in changes.split(",")]

    return await service.graph_impact_analysis(
        project_id=project_id,
        changes=change_list,
        workflow_type="MAINTENANCE"
    )


@router.get("/bug/{project_id}/dependencies/{entity_name}")
async def bug_dependencies(
    project_id: int,
    entity_name: str,
    file_path: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick dependency check for BUG workflow.

    Args:
        project_id: Project ID
        entity_name: Name of buggy entity

    Returns:
        Dependency check result
    """
    service = get_graph_workflow_service(db)

    return await service.graph_dependency_check(
        project_id=project_id,
        entity_name=entity_name,
        file_path=file_path
    )


@router.get("/quality/{project_id}/coupling")
async def quality_coupling(
    project_id: int,
    threshold: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick coupling metrics for QUALITY_AUDIT workflow.

    Args:
        project_id: Project ID
        threshold: Coupling threshold

    Returns:
        Coupling metrics result
    """
    service = get_graph_workflow_service(db)

    return await service.graph_coupling_metrics(
        project_id=project_id,
        coupling_threshold=threshold
    )


@router.get("/testing/{project_id}/coverage")
async def testing_coverage(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick test coverage map for TESTING workflow.

    Args:
        project_id: Project ID

    Returns:
        Test coverage map result
    """
    service = get_graph_workflow_service(db)

    return await service.graph_test_coverage_map(project_id=project_id)


@router.get("/enhancement/{project_id}/scope")
async def enhancement_scope_get(
    project_id: int,
    feature_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick enhancement scope for ENHANCEMENT workflow.

    Args:
        project_id: Project ID
        feature_name: Feature name/description

    Returns:
        Enhancement scope result
    """
    service = get_graph_workflow_service(db)

    return await service.graph_enhancement_scope(
        project_id=project_id,
        feature_name=feature_name
    )


# =========================================================================
# Statistics & Health
# =========================================================================

@router.get("/statistics/{project_id}")
async def get_statistics(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get graph statistics for a project.

    Returns:
        Project graph statistics
    """
    from app.services.graph_persistence_service import GraphPersistenceService

    service = GraphPersistenceService(db)
    return await service.get_project_statistics(project_id)


@router.get("/health")
async def health():
    """
    Health check for graph-workflow API.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "graph-workflow",
        "version": "week-88",
        "endpoints": {
            "impact_analysis": "/api/graph-workflow/impact-analysis",
            "dependency_check": "/api/graph-workflow/dependency-check",
            "coupling_metrics": "/api/graph-workflow/coupling-metrics",
            "test_coverage_map": "/api/graph-workflow/test-coverage-map",
            "enhancement_scope": "/api/graph-workflow/enhancement-scope",
            "sync_and_document": "/api/graph-workflow/sync-and-document",
            "workflow_context": "/api/graph-workflow/workflow-context",
        },
        "workflow_integrations": [
            "NEW_FEATURE -> impact-analysis",
            "MAINTENANCE -> impact-analysis",
            "BUG -> dependency-check",
            "QUALITY_AUDIT -> coupling-metrics",
            "QUALITY_IMPROVEMENT -> coupling-metrics",
            "TESTING -> test-coverage-map",
            "ENHANCEMENT -> enhancement-scope",
        ]
    }
