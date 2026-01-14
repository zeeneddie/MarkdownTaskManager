"""
API Routes for Context Engineering.

Provides endpoints for reference management, context optimization,
and token-efficient agent execution.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from app.confucius.context import (
    ReferenceSelector,
    ReferenceRegistry,
    ContextOptimizer,
    Reference,
    ReferenceCategory,
    ReferenceMatch,
    OptimizedContext,
    create_reference_selector,
    create_reference_registry,
    create_context_optimizer,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/context-engineering", tags=["context-engineering"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class AnalyzeTaskRequest(BaseModel):
    """Request for task analysis."""

    task: str = Field(..., description="Task description to analyze")
    context: Dict[str, Any] = Field(default_factory=dict, description="Task context")
    agent_name: Optional[str] = Field(None, description="Agent name for filtering")
    max_references: int = Field(default=3, ge=1, le=10, description="Max references")


class AnalyzeTaskResponse(BaseModel):
    """Response with reference matches."""

    task: str
    matches: List[Dict[str, Any]]
    total_token_estimate: int
    token_savings_percent: float


class OptimizeContextRequest(BaseModel):
    """Request for context optimization."""

    task: str = Field(..., description="Task description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Task context")
    agent_name: Optional[str] = Field(None, description="Agent name")
    required_references: List[str] = Field(default_factory=list, description="Required reference IDs")


class OptimizeContextResponse(BaseModel):
    """Response with optimized context."""

    task: str
    agent_name: Optional[str]
    references_selected: int
    reference_ids: List[str]
    token_estimate: int
    token_savings: int
    optimization_ratio: float


class ReferenceResponse(BaseModel):
    """Reference information response."""

    id: str
    name: str
    category: str
    description: str
    keywords: List[str]
    token_estimate: int
    domains: List[str]
    agents: List[str]
    is_loaded: bool = False


class RegistryStatsResponse(BaseModel):
    """Registry statistics response."""

    total_registered: int
    total_loaded: int
    total_words: int
    estimated_tokens: int
    by_category: Dict[str, int]


# =============================================================================
# SERVICE INSTANCES
# =============================================================================


_selector: Optional[ReferenceSelector] = None
_registry: Optional[ReferenceRegistry] = None
_optimizer: Optional[ContextOptimizer] = None


def get_selector() -> ReferenceSelector:
    """Get or create reference selector."""
    global _selector
    if _selector is None:
        _selector = create_reference_selector()
    return _selector


def get_registry() -> ReferenceRegistry:
    """Get or create reference registry."""
    global _registry
    if _registry is None:
        _registry = create_reference_registry(auto_load=False)
    return _registry


def get_optimizer() -> ContextOptimizer:
    """Get or create context optimizer."""
    global _optimizer
    if _optimizer is None:
        _optimizer = create_context_optimizer()
    return _optimizer


# =============================================================================
# ANALYSIS ENDPOINTS
# =============================================================================


@router.post("/analyze", response_model=AnalyzeTaskResponse)
async def analyze_task(request: AnalyzeTaskRequest):
    """
    Analyze a task to determine relevant references.

    Returns matched references with relevance scores and token estimates.
    """
    selector = get_selector()

    if request.agent_name:
        matches = selector.select_for_agent(
            agent_name=request.agent_name,
            task=request.task,
            context=request.context,
        )
    else:
        matches = selector.select(
            task=request.task,
            context=request.context,
            max_references=request.max_references,
        )

    total_tokens = selector.get_token_estimate(matches)
    # Estimate savings vs full context (25000 tokens)
    savings_percent = ((25000 - total_tokens) / 25000) * 100

    return AnalyzeTaskResponse(
        task=request.task[:100],
        matches=[m.to_dict() for m in matches],
        total_token_estimate=total_tokens,
        token_savings_percent=round(savings_percent, 1),
    )


@router.post("/optimize", response_model=OptimizeContextResponse)
async def optimize_context(request: OptimizeContextRequest):
    """
    Optimize context for a task.

    Selects relevant references and builds token-efficient context.
    """
    optimizer = get_optimizer()

    result = optimizer.optimize(
        task=request.task,
        context=request.context,
        agent_name=request.agent_name,
        required_references=request.required_references,
    )

    return OptimizeContextResponse(
        task=request.task[:100],
        agent_name=result.agent_name,
        references_selected=len(result.selected_references),
        reference_ids=[m.reference.id for m in result.selected_references],
        token_estimate=result.token_estimate,
        token_savings=result.token_savings,
        optimization_ratio=round(result.optimization_ratio, 2),
    )


# =============================================================================
# REFERENCE ENDPOINTS
# =============================================================================


@router.get("/references", response_model=List[ReferenceResponse])
async def list_references(
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    List all available references.

    Optionally filter by category.
    """
    selector = get_selector()
    registry = get_registry()

    refs = selector.list_references()

    if category:
        try:
            cat = ReferenceCategory(category.lower())
            refs = [r for r in refs if r.category == cat]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Valid: {[c.value for c in ReferenceCategory]}",
            )

    return [
        ReferenceResponse(
            id=r.id,
            name=r.name,
            category=r.category.value,
            description=r.description,
            keywords=r.keywords[:10],
            token_estimate=r.token_estimate,
            domains=r.domains,
            agents=r.agents,
            is_loaded=registry.is_loaded(r.id),
        )
        for r in refs
    ]


@router.get("/references/{reference_id}", response_model=ReferenceResponse)
async def get_reference(reference_id: str):
    """Get details of a specific reference."""
    selector = get_selector()
    registry = get_registry()

    ref = selector.get_reference(reference_id)
    if not ref:
        raise HTTPException(status_code=404, detail=f"Reference not found: {reference_id}")

    return ReferenceResponse(
        id=ref.id,
        name=ref.name,
        category=ref.category.value,
        description=ref.description,
        keywords=ref.keywords,
        token_estimate=ref.token_estimate,
        domains=ref.domains,
        agents=ref.agents,
        is_loaded=registry.is_loaded(ref.id),
    )


@router.get("/references/{reference_id}/content")
async def get_reference_content(reference_id: str):
    """Get content of a reference document."""
    registry = get_registry()

    content = registry.get_content(reference_id)
    if not content:
        # Try to load it
        if registry.load_reference(reference_id):
            content = registry.get_content(reference_id)

    if not content:
        raise HTTPException(
            status_code=404,
            detail=f"Reference content not available: {reference_id}",
        )

    cached = registry.get_cached(reference_id)
    return {
        "reference_id": reference_id,
        "content": content,
        "word_count": cached.word_count if cached else 0,
        "line_count": cached.line_count if cached else 0,
    }


# =============================================================================
# REGISTRY ENDPOINTS
# =============================================================================


@router.get("/registry/stats", response_model=RegistryStatsResponse)
async def get_registry_stats():
    """Get registry statistics."""
    registry = get_registry()
    stats = registry.get_statistics()

    return RegistryStatsResponse(
        total_registered=stats["total_registered"],
        total_loaded=stats["total_loaded"],
        total_words=stats["total_words"],
        estimated_tokens=stats["estimated_tokens"],
        by_category=stats["by_category"],
    )


@router.post("/registry/load")
async def load_references(reference_ids: Optional[List[str]] = None):
    """
    Load reference documents from filesystem.

    If no IDs provided, loads all references.
    """
    registry = get_registry()

    if reference_ids:
        results = {}
        for ref_id in reference_ids:
            results[ref_id] = registry.load_reference(ref_id)
    else:
        results = registry.load_all()

    loaded_count = sum(1 for v in results.values() if v)
    return {
        "loaded": loaded_count,
        "failed": len(results) - loaded_count,
        "results": results,
    }


@router.post("/registry/reload")
async def reload_references():
    """Reload all references from filesystem."""
    registry = get_registry()
    results = registry.reload_all()

    loaded_count = sum(1 for v in results.values() if v)
    return {
        "reloaded": loaded_count,
        "failed": len(results) - loaded_count,
        "results": results,
    }


# =============================================================================
# QUALITY GATE INTEGRATION ENDPOINTS
# =============================================================================


@router.get("/quality-gates/summary")
async def get_quality_gate_summary():
    """
    Get summary of quality gate integration with context engineering.

    Shows how context optimization affects quality scores.
    """
    optimizer = get_optimizer()
    summary = optimizer.get_reference_summary()

    return {
        **summary,
        "quality_gate_integration": {
            "piv_loop_enabled": True,
            "max_iterations": 3,
            "threshold": 0.85,
            "context_optimization_enabled": True,
        },
    }


@router.get("/categories")
async def list_categories():
    """List all reference categories."""
    return {
        "categories": [
            {"value": c.value, "description": _get_category_description(c)}
            for c in ReferenceCategory
        ]
    }


def _get_category_description(category: ReferenceCategory) -> str:
    """Get description for category."""
    descriptions = {
        ReferenceCategory.LANGUAGE: "Language-specific patterns (ASP, Python, etc.)",
        ReferenceCategory.FRAMEWORK: "Framework conventions (FastAPI, SQLAlchemy)",
        ReferenceCategory.TESTING: "Testing patterns and fixtures",
        ReferenceCategory.SECURITY: "Security patterns and OWASP",
        ReferenceCategory.ARCHITECTURE: "Architecture decisions",
        ReferenceCategory.STABILITY: "Resource leak detection",
        ReferenceCategory.ESTIMATION: "FP methodology",
        ReferenceCategory.DOCUMENTATION: "Documentation standards",
        ReferenceCategory.GENERAL: "General best practices",
    }
    return descriptions.get(category, "")
