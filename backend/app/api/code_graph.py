"""
Code Graph API - Week 75

REST API endpoints for the Graph Persistence Service.
Provides code entity management, impact analysis, and graph operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.graph_persistence_service import GraphPersistenceService


router = APIRouter(prefix="/api/code-graph", tags=["Code Graph"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class SyncProjectRequest(BaseModel):
    """Request to sync a project's code graph."""
    project_id: int = Field(..., description="Project ID to sync")
    repo_path: str = Field(..., description="Path to repository")
    languages: List[str] = Field(default=["python"], description="Languages to analyze")


class SyncProjectResponse(BaseModel):
    """Response from project sync."""
    success: bool
    project_id: int
    repo_path: str
    entities_added: int
    entities_updated: int
    relations_added: int
    files_processed: int


class EntityResponse(BaseModel):
    """Code entity response."""
    id: str
    project_id: int
    entity_type: str
    name: str
    qualified_name: Optional[str]
    file_path: str
    start_line: Optional[int]
    end_line: Optional[int]
    docstring: Optional[str]
    signature: Optional[str]
    entity_data: Dict[str, Any]
    metrics: Dict[str, Any]
    hash: Optional[str]
    last_synced: Optional[str]
    created_at: Optional[str]


class ImpactAnalysisResponse(BaseModel):
    """Impact analysis response."""
    entity_id: str
    affected_entities: List[Dict[str, Any]]
    affected_files: List[str]
    impact_score: float
    depth: int
    from_cache: bool


class DependencyResponse(BaseModel):
    """Dependency/dependent response."""
    entity_id: str
    dependencies: Optional[List[Dict[str, Any]]] = None
    dependents: Optional[List[Dict[str, Any]]] = None
    count: int


class CircularDependencyResponse(BaseModel):
    """Circular dependency detection response."""
    project_id: int
    cycles_found: int
    cycles: List[Dict[str, Any]]


class ModuleCouplingResponse(BaseModel):
    """Module coupling metrics response."""
    project_id: int
    total_modules: int
    total_connections: int
    total_coupling_strength: int
    average_coupling: float
    couplings: List[Dict[str, Any]]


class SnapshotRequest(BaseModel):
    """Request to create a graph snapshot."""
    project_id: int
    snapshot_name: Optional[str] = None
    git_commit: Optional[str] = None


class SnapshotResponse(BaseModel):
    """Graph snapshot response."""
    id: str
    project_id: int
    snapshot_name: Optional[str]
    git_commit: Optional[str]
    entity_count: int
    relation_count: int
    file_count: int
    summary_stats: Dict[str, Any]
    created_at: Optional[str]


class SnapshotComparisonResponse(BaseModel):
    """Snapshot comparison response."""
    snapshot_1: Dict[str, Any]
    snapshot_2: Dict[str, Any]
    entity_changes: Dict[str, Any]
    relation_changes: Dict[str, Any]
    total_entity_change: int
    total_relation_change: int
    total_file_change: int


class ProjectStatisticsResponse(BaseModel):
    """Project statistics response."""
    project_id: int
    total_entities: int
    total_relations: int
    total_files: int
    entity_counts: Dict[str, int]
    relation_counts: Dict[str, int]
    top_referenced_entities: List[Dict[str, Any]]


class GraphExportResponse(BaseModel):
    """Graph export response."""
    nodes: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[Dict[str, Any]]] = None
    dot: Optional[str] = None


class SearchRequest(BaseModel):
    """Entity search request."""
    query: str = Field(..., min_length=1, description="Search query")
    entity_type: Optional[str] = None
    limit: int = Field(default=50, le=200)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/sync", response_model=SyncProjectResponse, status_code=status.HTTP_200_OK)
async def sync_project_graph(
    request: SyncProjectRequest,
    db: AsyncSession = Depends(get_db)
) -> SyncProjectResponse:
    """
    Sync a project's code graph to the database.

    Analyzes the source code at the given path and persists
    all entities and relationships to PostgreSQL.
    """
    service = GraphPersistenceService(db)
    result = await service.sync_project_graph(
        project_id=request.project_id,
        repo_path=request.repo_path,
        languages=request.languages
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return SyncProjectResponse(**result)


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EntityResponse:
    """Get a single entity by ID."""
    service = GraphPersistenceService(db)
    entity = await service.get_entity_by_id(entity_id)

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )

    return EntityResponse(**entity)


@router.get("/projects/{project_id}/entities", response_model=List[EntityResponse])
async def search_entities(
    project_id: int,
    query: str = Query(..., min_length=1),
    entity_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db)
) -> List[EntityResponse]:
    """Search for entities by name in a project."""
    service = GraphPersistenceService(db)
    entities = await service.search_entities(
        project_id=project_id,
        query=query,
        entity_type=entity_type,
        limit=limit
    )

    return [EntityResponse(**e) for e in entities]


@router.get("/projects/{project_id}/files/{file_path:path}/entities", response_model=List[EntityResponse])
async def get_entities_by_file(
    project_id: int,
    file_path: str,
    db: AsyncSession = Depends(get_db)
) -> List[EntityResponse]:
    """Get all entities in a specific file."""
    service = GraphPersistenceService(db)
    entities = await service.get_entities_by_file(
        project_id=project_id,
        file_path=file_path
    )

    return [EntityResponse(**e) for e in entities]


# =============================================================================
# IMPACT ANALYSIS
# =============================================================================

@router.get("/impact/{entity_id}", response_model=ImpactAnalysisResponse)
async def get_impact_analysis(
    entity_id: UUID,
    project_id: int = Query(...),
    max_depth: int = Query(default=5, le=10),
    db: AsyncSession = Depends(get_db)
) -> ImpactAnalysisResponse:
    """
    Perform impact analysis for an entity.

    Returns all entities that would be affected by changes to this entity,
    using recursive traversal of the dependency graph.
    """
    service = GraphPersistenceService(db)
    result = await service.get_impact_analysis(
        project_id=project_id,
        entity_id=entity_id,
        max_depth=max_depth
    )

    return ImpactAnalysisResponse(**result)


@router.get("/dependencies/{entity_id}", response_model=DependencyResponse)
async def get_dependencies(
    entity_id: UUID,
    project_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
) -> DependencyResponse:
    """Get direct dependencies of an entity."""
    service = GraphPersistenceService(db)
    result = await service.get_direct_dependencies(
        project_id=project_id,
        entity_id=entity_id
    )

    return DependencyResponse(**result)


@router.get("/dependents/{entity_id}", response_model=DependencyResponse)
async def get_dependents(
    entity_id: UUID,
    project_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
) -> DependencyResponse:
    """Get entities that depend on this entity."""
    service = GraphPersistenceService(db)
    result = await service.get_dependents(
        project_id=project_id,
        entity_id=entity_id
    )

    return DependencyResponse(**result)


# =============================================================================
# CIRCULAR DEPENDENCIES
# =============================================================================

@router.get("/projects/{project_id}/circular-dependencies", response_model=CircularDependencyResponse)
async def detect_circular_dependencies(
    project_id: int,
    db: AsyncSession = Depends(get_db)
) -> CircularDependencyResponse:
    """
    Detect circular dependencies in a project.

    Returns all cycles found in the dependency graph.
    """
    service = GraphPersistenceService(db)
    result = await service.detect_circular_dependencies(project_id)

    return CircularDependencyResponse(**result)


# =============================================================================
# MODULE COUPLING
# =============================================================================

@router.get("/projects/{project_id}/coupling", response_model=ModuleCouplingResponse)
async def get_module_coupling(
    project_id: int,
    sort_by: str = Query(default="coupling_count"),
    db: AsyncSession = Depends(get_db)
) -> ModuleCouplingResponse:
    """Get module coupling metrics for a project."""
    service = GraphPersistenceService(db)
    result = await service.get_module_coupling(
        project_id=project_id,
        sort_by=sort_by
    )

    return ModuleCouplingResponse(**result)


@router.get("/projects/{project_id}/coupling/high", response_model=List[Dict[str, Any]])
async def get_highly_coupled_modules(
    project_id: int,
    threshold: int = Query(default=10, ge=1),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get modules with coupling above threshold."""
    service = GraphPersistenceService(db)
    return await service.get_highly_coupled_modules(
        project_id=project_id,
        threshold=threshold
    )


# =============================================================================
# SNAPSHOTS
# =============================================================================

@router.post("/snapshots", response_model=SnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    request: SnapshotRequest,
    db: AsyncSession = Depends(get_db)
) -> SnapshotResponse:
    """Create a snapshot of the current graph state."""
    service = GraphPersistenceService(db)
    result = await service.create_snapshot(
        project_id=request.project_id,
        snapshot_name=request.snapshot_name,
        git_commit=request.git_commit
    )

    return SnapshotResponse(**result)


@router.get("/projects/{project_id}/snapshots", response_model=List[SnapshotResponse])
async def get_snapshots(
    project_id: int,
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db)
) -> List[SnapshotResponse]:
    """Get recent snapshots for a project."""
    service = GraphPersistenceService(db)
    snapshots = await service.get_snapshots(
        project_id=project_id,
        limit=limit
    )

    return [SnapshotResponse(**s) for s in snapshots]


@router.get("/snapshots/compare", response_model=SnapshotComparisonResponse)
async def compare_snapshots(
    snapshot_id_1: UUID = Query(...),
    snapshot_id_2: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
) -> SnapshotComparisonResponse:
    """Compare two snapshots."""
    service = GraphPersistenceService(db)
    result = await service.compare_snapshots(
        snapshot_id_1=snapshot_id_1,
        snapshot_id_2=snapshot_id_2
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return SnapshotComparisonResponse(**result)


# =============================================================================
# STATISTICS & EXPORT
# =============================================================================

@router.get("/projects/{project_id}/statistics", response_model=ProjectStatisticsResponse)
async def get_project_statistics(
    project_id: int,
    db: AsyncSession = Depends(get_db)
) -> ProjectStatisticsResponse:
    """Get comprehensive statistics for a project's code graph."""
    service = GraphPersistenceService(db)
    result = await service.get_project_statistics(project_id)

    return ProjectStatisticsResponse(**result)


@router.get("/projects/{project_id}/export", response_model=GraphExportResponse)
async def export_graph(
    project_id: int,
    format: str = Query(default="d3", pattern="^(d3|dot)$"),
    db: AsyncSession = Depends(get_db)
) -> GraphExportResponse:
    """
    Export graph for visualization.

    Formats:
    - d3: D3.js force-directed graph format
    - dot: GraphViz DOT format
    """
    service = GraphPersistenceService(db)
    result = await service.export_graph_for_visualization(
        project_id=project_id,
        format=format
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return GraphExportResponse(**result)


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

@router.delete("/projects/{project_id}/cache")
async def invalidate_project_cache(
    project_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Invalidate all cached impact analyses for a project."""
    service = GraphPersistenceService(db)
    count = await service.invalidate_cache(project_id=project_id)

    return {
        "success": True,
        "project_id": project_id,
        "cache_entries_invalidated": count
    }


@router.delete("/cache/{entity_id}")
async def invalidate_entity_cache(
    entity_id: UUID,
    project_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Invalidate cached impact analysis for a specific entity."""
    service = GraphPersistenceService(db)
    count = await service.invalidate_cache(
        project_id=project_id,
        entity_id=entity_id
    )

    return {
        "success": True,
        "entity_id": str(entity_id),
        "cache_entries_invalidated": count
    }
