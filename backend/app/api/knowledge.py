"""
Knowledge API Endpoints - Unified Code Understanding

Week 62: Code Understanding Integration

Endpoints for:
- Unified knowledge queries
- Code search (semantic)
- Agent context generation
- Index management
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.unified_knowledge_service import (
    UnifiedKnowledgeService,
    KnowledgeSource,
    QueryType
)
from app.services.code_rag_service import get_code_rag_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


# ============ Request/Response Models ============

class QueryRequest(BaseModel):
    """Request for unified knowledge query."""
    query: str = Field(..., description="Search query")
    sources: Optional[List[str]] = Field(None, description="Sources to query")
    query_type: Optional[str] = Field(None, description="Query type for optimization")
    n_results: int = Field(10, description="Max results per source")
    language: Optional[str] = Field(None, description="Filter by language")


class IndexRequest(BaseModel):
    """Request to index a project."""
    repository_path: str = Field(..., description="Path to repository")


class CodeSearchRequest(BaseModel):
    """Request for code search."""
    query: str = Field(..., description="Search query or code snippet")
    language: Optional[str] = Field(None, description="Filter by language")
    chunk_type: Optional[str] = Field(None, description="Filter by chunk type")
    n_results: int = Field(10, description="Number of results")


class KnowledgeResult(BaseModel):
    """Single knowledge result."""
    source: str
    type: str
    id: str
    title: str
    content: str
    metadata: dict
    score: float


class QueryResponse(BaseModel):
    """Response from knowledge query."""
    query: str
    project_id: int
    query_type: Optional[str]
    sources_queried: List[str]
    results: List[KnowledgeResult]
    metadata: dict


# ============ Query Endpoints ============

@router.post("/{project_id}/query", response_model=QueryResponse)
async def query_knowledge(
    project_id: int,
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query unified knowledge sources.

    Searches across CodeWiki, CodeRAG, and other sources.
    """
    service = UnifiedKnowledgeService(db)

    # Parse sources
    sources = None
    if request.sources:
        try:
            sources = [KnowledgeSource(s) for s in request.sources]
        except ValueError:
            pass

    # Parse query type
    query_type = None
    if request.query_type:
        try:
            query_type = QueryType(request.query_type)
        except ValueError:
            pass

    result = service.query(
        query=request.query,
        project_id=project_id,
        sources=sources,
        query_type=query_type,
        n_results=request.n_results,
        language=request.language
    )

    return QueryResponse(**result)


@router.get("/{project_id}/search")
async def search_code(
    project_id: int,
    q: str = Query(..., description="Search query"),
    language: Optional[str] = Query(None, description="Language filter"),
    type: Optional[str] = Query(None, description="Chunk type filter"),
    limit: int = Query(10, description="Max results"),
    db: Session = Depends(get_db)
):
    """
    Search code semantically.

    Uses embeddings for semantic similarity search.
    """
    service = get_code_rag_service()

    if not service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Code search not available (ChromaDB not configured)"
        )

    results = service.search(
        query=q,
        n_results=limit,
        project_id=project_id,
        language=language,
        chunk_type=type
    )

    return {
        "query": q,
        "project_id": project_id,
        "total": len(results),
        "results": results,
    }


@router.post("/{project_id}/find-similar")
async def find_similar_code(
    project_id: int,
    request: CodeSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Find code similar to a given snippet.

    Useful for finding duplicate or similar implementations.
    """
    service = UnifiedKnowledgeService(db)

    results = service.find_similar_implementations(
        code_snippet=request.query,
        project_id=project_id,
        language=request.language
    )

    return {
        "query_snippet": request.query[:100] + "..." if len(request.query) > 100 else request.query,
        "project_id": project_id,
        "total": len(results),
        "similar_code": results,
    }


@router.post("/{project_id}/find-functions")
async def find_function_implementations(
    project_id: int,
    description: str = Query(..., description="Function description"),
    language: Optional[str] = Query(None, description="Language filter"),
    db: Session = Depends(get_db)
):
    """
    Find function implementations by description.

    Search for functions that match a natural language description.
    """
    service = UnifiedKnowledgeService(db)

    results = service.search_functions(
        description=description,
        project_id=project_id,
        language=language
    )

    return {
        "description": description,
        "project_id": project_id,
        "total": len(results),
        "functions": results,
    }


# ============ Agent Context Endpoints ============

@router.get("/{project_id}/agent-context/{agent_name}")
async def get_agent_knowledge_context(
    project_id: int,
    agent_name: str,
    task: Optional[str] = Query(None, description="Task description for context"),
    db: Session = Depends(get_db)
):
    """
    Get optimized knowledge context for an agent.

    Combines knowledge from all sources optimized for the specific agent.
    """
    valid_agents = ["felix", "miguel", "quinn", "diana", "betty", "eliza", "marcus", "tessa", "peter", "paul"]

    if agent_name.lower() not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent. Valid agents: {', '.join(valid_agents)}"
        )

    service = UnifiedKnowledgeService(db)

    context = service.get_agent_context(
        agent_name=agent_name,
        project_id=project_id,
        task_description=task
    )

    return context


@router.get("/{project_id}/architecture")
async def get_architecture_knowledge(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get architecture-focused knowledge.

    Optimized for Felix (Feature Architect).
    """
    service = UnifiedKnowledgeService(db)
    return service.get_architecture_context(project_id)


@router.get("/{project_id}/dependencies")
async def get_dependency_knowledge(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get dependency-focused knowledge.

    Optimized for Miguel (Migration Architect).
    """
    service = UnifiedKnowledgeService(db)
    return service.get_dependency_context(project_id)


# ============ Index Management Endpoints ============

@router.post("/{project_id}/index")
async def index_project(
    project_id: int,
    request: IndexRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Index a project for knowledge search.

    Indexes code for semantic search using CodeRAG.
    """
    service = UnifiedKnowledgeService(db)

    # Run indexing in background
    async def do_index():
        try:
            service.index_project(project_id, request.repository_path)
        except Exception as e:
            # Log error
            pass

    background_tasks.add_task(do_index)

    return {
        "message": "Indexing started",
        "project_id": project_id,
        "repository_path": request.repository_path,
    }


@router.get("/{project_id}/index/status")
async def get_index_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get indexing status for a project."""
    service = UnifiedKnowledgeService(db)
    return service.get_index_statistics(project_id)


@router.delete("/{project_id}/index")
async def delete_project_index(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Delete index for a project."""
    service = get_code_rag_service()

    if not service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Index management not available"
        )

    success = service.delete_project_index(project_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete index"
        )

    return {
        "message": "Index deleted",
        "project_id": project_id,
    }


# ============ Statistics Endpoints ============

@router.get("/statistics")
async def get_knowledge_statistics(
    db: Session = Depends(get_db)
):
    """Get overall knowledge index statistics."""
    service = UnifiedKnowledgeService(db)
    return service.get_index_statistics()


@router.get("/sources")
async def list_knowledge_sources():
    """List available knowledge sources."""
    return {
        "sources": [
            {
                "id": "codewiki",
                "name": "CodeWiki",
                "description": "Repository documentation and module structure",
                "provides": ["modules", "diagrams", "documentation"],
            },
            {
                "id": "coderag",
                "name": "CodeRAG",
                "description": "Semantic code search using embeddings",
                "provides": ["code_search", "similar_code", "function_search"],
            },
        ],
        "query_types": [
            {"id": "architecture", "description": "Architecture and module structure"},
            {"id": "code_search", "description": "General code search"},
            {"id": "documentation", "description": "Documentation and comments"},
            {"id": "dependencies", "description": "Internal and external dependencies"},
            {"id": "similar_code", "description": "Find similar code patterns"},
            {"id": "implementation", "description": "Find function implementations"},
        ]
    }


@router.get("/health")
async def knowledge_health_check():
    """Health check for knowledge services."""
    coderag = get_code_rag_service()

    return {
        "status": "healthy",
        "services": {
            "coderag": {
                "available": coderag.is_available,
            },
            "codewiki": {
                "available": True,  # Always available (DB-based)
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
