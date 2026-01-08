"""
Knowledge Graph API Endpoints

Week 62 Day 3: Local Knowledge Graph (no external dependencies)

Provides:
- Build code entity graphs from repositories
- Query class hierarchies, dependencies
- Agent-optimized insights (Felix, Miguel, Quinn)
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.knowledge_graph_service import (
    KnowledgeGraphService,
    EntityType
)

router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])


# ============ Request/Response Models ============

class BuildGraphRequest(BaseModel):
    """Request to build knowledge graph."""
    repository_path: str = Field(..., description="Path to repository")
    languages: Optional[List[str]] = Field(["python"], description="Languages to analyze")


class GraphStatsResponse(BaseModel):
    """Knowledge graph statistics."""
    project_id: int
    entities: int
    relations: int
    files_analyzed: int
    entity_types: dict
    relation_types: dict


# ============ Graph Building Endpoints ============

@router.post("/{project_id}/build")
async def build_knowledge_graph(
    project_id: int,
    request: BuildGraphRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Build knowledge graph for a repository.

    Analyzes Python code to extract:
    - Classes, functions, methods
    - Import relationships
    - Inheritance hierarchies
    """
    global _graph_services
    service = KnowledgeGraphService(db)

    # Build synchronously for now (fast for most repos)
    result = service.build_graph(
        repo_path=request.repository_path,
        project_id=project_id,
        languages=request.languages
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Store service instance for this project
    _graph_services[project_id] = service

    return result


# Module-level graph storage
_graph_services: dict = {}


def _get_graph_service(project_id: int, db: Session = None) -> KnowledgeGraphService:
    """Get graph service for a project."""
    return _graph_services.get(project_id)


@router.get("/{project_id}/stats")
async def get_graph_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get knowledge graph statistics."""
    service = _get_graph_service(project_id, db)

    if not service or not service._entities:
        return {
            "project_id": project_id,
            "status": "not_built",
            "message": "Knowledge graph not built. Use POST /build first."
        }

    return {
        "project_id": project_id,
        "status": "ready",
        "entities": len(service._entities),
        "relations": len(service._relations),
        "files_analyzed": len(service._file_entities),
        "entity_types": service._count_entity_types(),
        "relation_types": service._count_relation_types()
    }


# ============ Entity Query Endpoints ============

@router.get("/{project_id}/classes")
async def list_classes(
    project_id: int,
    pattern: Optional[str] = Query(None, description="Filter by name pattern"),
    limit: int = Query(50, description="Max results"),
    db: Session = Depends(get_db)
):
    """List all classes in the knowledge graph."""
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    classes = service.find_classes(pattern)[:limit]

    return {
        "project_id": project_id,
        "total": len(classes),
        "classes": [
            {
                "name": c.name,
                "file": c.file_path,
                "line": c.start_line,
                "docstring": c.docstring[:200] if c.docstring else None,
                "bases": c.metadata.get("bases", [])
            }
            for c in classes
        ]
    }


@router.get("/{project_id}/functions")
async def list_functions(
    project_id: int,
    pattern: Optional[str] = Query(None, description="Filter by name pattern"),
    limit: int = Query(50, description="Max results"),
    db: Session = Depends(get_db)
):
    """List all functions in the knowledge graph."""
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    functions = service.find_functions(pattern)[:limit]

    return {
        "project_id": project_id,
        "total": len(functions),
        "functions": [
            {
                "name": f.name,
                "file": f.file_path,
                "line": f.start_line,
                "docstring": f.docstring[:200] if f.docstring else None,
                "args": f.metadata.get("args", []),
                "is_async": f.metadata.get("is_async", False)
            }
            for f in functions
        ]
    }


@router.get("/{project_id}/class/{class_name}")
async def get_class_details(
    project_id: int,
    class_name: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a class."""
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    result = service.get_class_hierarchy(class_name)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/{project_id}/dependencies/{file_path:path}")
async def get_file_dependencies(
    project_id: int,
    file_path: str,
    db: Session = Depends(get_db)
):
    """Get dependencies for a specific file."""
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    return service.get_module_dependencies(file_path)


# ============ Agent Context Endpoints ============

@router.get("/{project_id}/agent/felix")
async def get_felix_context(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get architecture summary for Felix (Feature Architect).

    Provides:
    - Module structure overview
    - Main classes and their relationships
    - Directory organization
    """
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    return {
        "agent": "felix",
        "role": "Feature Architect",
        "context": service.get_architecture_summary()
    }


@router.get("/{project_id}/agent/miguel")
async def get_miguel_context(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get dependency graph for Miguel (Migration Architect).

    Provides:
    - External dependencies list
    - Internal vs external import analysis
    - Most dependent modules
    """
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    return {
        "agent": "miguel",
        "role": "Migration Architect",
        "context": service.get_dependency_graph()
    }


@router.get("/{project_id}/agent/quinn")
async def get_quinn_context(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get quality insights for Quinn (Quality Inspector).

    Provides:
    - Documentation coverage
    - Large class warnings
    - Quality recommendations
    """
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    return {
        "agent": "quinn",
        "role": "Quality Inspector",
        "context": service.get_quality_insights()
    }


# ============ Export Endpoints ============

@router.get("/{project_id}/export")
async def export_graph(
    project_id: int,
    format: str = Query("json", description="Export format"),
    db: Session = Depends(get_db)
):
    """Export knowledge graph as JSON."""
    service = _get_graph_service(project_id, db)

    if not service:
        raise HTTPException(status_code=404, detail="Graph not built")

    if format != "json":
        raise HTTPException(status_code=400, detail="Only JSON format supported")

    import json
    return json.loads(service.export_graph())


# ============ Health Check ============

@router.get("/health")
async def knowledge_graph_health():
    """Health check for knowledge graph service."""
    return {
        "status": "healthy",
        "service": "knowledge_graph",
        "features": [
            "python_ast_analysis",
            "class_hierarchy",
            "dependency_analysis",
            "agent_contexts"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
