"""
Knowledge Base API - Famous Bugs & Post-Mortems

Endpoints for loading, querying, and managing knowledge base collections.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from app.services.knowledge_base.famous_bugs_loader import FamousBugsLoader, FAMOUS_BUGS_DATA
from app.services.knowledge_base.post_mortems_loader import PostMortemsLoader, POST_MORTEMS_DATA

router = APIRouter(prefix="/api/knowledge-base", tags=["Knowledge Base"])


# === Request/Response Models ===

class KBLoadResponse(BaseModel):
    success: bool
    loaded: int
    errors: int
    error_details: List[Dict[str, Any]] = []
    categories: Dict[str, int] = {}
    total_available: int = 0


class KBStatusResponse(BaseModel):
    collection: str
    loaded_count: int
    available_count: int
    categories: Dict[str, int] = {}


class KBQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    company: Optional[str] = Field(default=None, description="Filter by company (post-mortems only)")
    root_cause: Optional[str] = Field(default=None, description="Filter by root cause category")
    impact: Optional[str] = Field(default=None, description="Filter by impact category")


class KBQueryResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    relevance_score: float


class KBQueryResponse(BaseModel):
    query: str
    results: List[KBQueryResult]
    total_results: int


class KBStatisticsResponse(BaseModel):
    famous_bugs: Dict[str, Any]
    post_mortems: Dict[str, Any]
    total_items: int


class KBPostMortemsStatusResponse(BaseModel):
    collection: str
    loaded_count: int
    available_count: int
    root_cause_categories: Dict[str, int] = {}
    companies: List[str] = []


# === Helper: get ChromaService (lazy) ===

def _get_chroma_service():
    """Get or create ChromaService instance."""
    try:
        from app.services.chroma_service import get_chroma_service
        return get_chroma_service()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"ChromaDB service unavailable: {str(e)}"
        )


# === Famous Bugs Endpoints ===

@router.post("/famous-bugs/load", response_model=KBLoadResponse)
async def load_famous_bugs():
    """Load all famous bugs into the knowledge base."""
    chroma = _get_chroma_service()
    loader = FamousBugsLoader(chroma)
    stats = loader.load_all()
    return KBLoadResponse(
        success=stats["errors"] == 0,
        loaded=stats["loaded"],
        errors=stats["errors"],
        error_details=stats["error_details"],
        categories=stats["categories"],
        total_available=stats["total_available"],
    )


@router.get("/famous-bugs/status", response_model=KBStatusResponse)
async def get_famous_bugs_status():
    """Get the current status of the famous bugs collection."""
    chroma = _get_chroma_service()
    loader = FamousBugsLoader(chroma)
    status = loader.get_load_status()
    return KBStatusResponse(**status)


@router.post("/famous-bugs/query", response_model=KBQueryResponse)
async def query_famous_bugs(request: KBQueryRequest):
    """Query the famous bugs knowledge base."""
    chroma = _get_chroma_service()
    try:
        results = chroma.query(
            collection_name="famous_bugs",
            query_text=request.query,
            n_results=request.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    formatted = _format_query_results(results)
    return KBQueryResponse(
        query=request.query,
        results=formatted,
        total_results=len(formatted),
    )


@router.delete("/famous-bugs/clear")
async def clear_famous_bugs():
    """Clear the famous bugs collection."""
    chroma = _get_chroma_service()
    loader = FamousBugsLoader(chroma)
    loader.clear_collection()
    return {"success": True, "message": "Famous bugs collection cleared"}


# === Post-Mortems Endpoints ===

@router.post("/post-mortems/load", response_model=KBLoadResponse)
async def load_post_mortems():
    """Load all post-mortems into the knowledge base."""
    chroma = _get_chroma_service()
    loader = PostMortemsLoader(chroma)
    stats = loader.load_all()
    return KBLoadResponse(
        success=stats["errors"] == 0,
        loaded=stats["loaded"],
        errors=stats["errors"],
        error_details=stats["error_details"],
        categories=stats.get("root_cause_categories", {}),
        total_available=stats["total_available"],
    )


@router.get("/post-mortems/status", response_model=KBPostMortemsStatusResponse)
async def get_post_mortems_status():
    """Get the current status of the post-mortems collection."""
    chroma = _get_chroma_service()
    loader = PostMortemsLoader(chroma)
    status = loader.get_load_status()
    return KBPostMortemsStatusResponse(**status)


@router.post("/post-mortems/query", response_model=KBQueryResponse)
async def query_post_mortems(request: KBQueryRequest):
    """Query the post-mortems knowledge base with optional filters."""
    chroma = _get_chroma_service()

    where_filter = {}
    if request.company:
        where_filter["company"] = request.company
    if request.root_cause:
        where_filter["root_cause_category"] = request.root_cause
    if request.impact:
        where_filter["impact_category"] = request.impact

    try:
        kwargs = {
            "collection_name": "post_mortems",
            "query_text": request.query,
            "n_results": request.top_k,
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = chroma.query(**kwargs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    formatted = _format_query_results(results)
    return KBQueryResponse(
        query=request.query,
        results=formatted,
        total_results=len(formatted),
    )


@router.delete("/post-mortems/clear")
async def clear_post_mortems():
    """Clear the post-mortems collection."""
    chroma = _get_chroma_service()
    loader = PostMortemsLoader(chroma)
    loader.clear_collection()
    return {"success": True, "message": "Post-mortems collection cleared"}


# === Combined Statistics ===

@router.get("/statistics", response_model=KBStatisticsResponse)
async def get_kb_statistics():
    """Get combined statistics for all knowledge base collections."""
    chroma = _get_chroma_service()

    fb_loader = FamousBugsLoader(chroma)
    pm_loader = PostMortemsLoader(chroma)

    fb_status = fb_loader.get_load_status()
    pm_status = pm_loader.get_load_status()

    return KBStatisticsResponse(
        famous_bugs=fb_status,
        post_mortems=pm_status,
        total_items=fb_status["loaded_count"] + pm_status["loaded_count"],
    )


# === Helper Functions ===

def _format_query_results(results: Any) -> List[KBQueryResult]:
    """Format ChromaDB results into response format."""
    if not results:
        return []

    formatted = []
    documents = results.get("documents", [[]])[0] if isinstance(results, dict) else []
    metadatas = results.get("metadatas", [[]])[0] if isinstance(results, dict) else []
    distances = results.get("distances", [[]])[0] if isinstance(results, dict) else []

    for i, doc in enumerate(documents):
        formatted.append(KBQueryResult(
            content=doc,
            metadata=metadatas[i] if i < len(metadatas) else {},
            relevance_score=round(1.0 - (distances[i] if i < len(distances) else 0), 4),
        ))

    return formatted
