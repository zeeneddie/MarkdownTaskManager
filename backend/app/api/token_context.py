"""
Token-Optimized Context API

Week 143: Endpoints for retrieving Vector DB context within token budgets.
Optimizes context for efficient LLM consumption.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum

from app.services.token_optimization_service import (
    get_token_optimization_service,
    TokenOptimizationService,
    TokenBudget,
    OptimizedContext
)

router = APIRouter(prefix="/api/token-context", tags=["Token-Optimized Context"])


# ============================================================================
# Request/Response Models
# ============================================================================

class BudgetLevel(str, Enum):
    """Token budget levels for API."""
    minimal = "minimal"
    compact = "compact"
    standard = "standard"
    extended = "extended"
    full = "full"


class ContextItem(BaseModel):
    """Single context item for optimization."""
    content: str
    content_type: Optional[str] = None
    relevance: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class OptimizeRequest(BaseModel):
    """Request to optimize context items."""
    items: List[ContextItem]
    budget: BudgetLevel = BudgetLevel.standard
    query: Optional[str] = None
    preserve_structure: bool = True


class OptimizeResponse(BaseModel):
    """Optimized context response."""
    content: str
    token_count: int
    items_included: int
    items_truncated: int
    avg_relevance: float
    budget_used_percent: float


class CategoryOptimizeRequest(BaseModel):
    """Request to optimize categorized context."""
    categories: Dict[str, List[ContextItem]]
    budget: BudgetLevel = BudgetLevel.standard
    query: Optional[str] = None


class CategoryOptimizeResponse(BaseModel):
    """Optimized categorized context response."""
    categories: Dict[str, Dict[str, Any]]
    metadata: Dict[str, Any]


class VectorContextRequest(BaseModel):
    """Request for Vector DB context with optimization."""
    project_id: int = 1000
    query: str
    context_types: List[str] = Field(
        default=["code_patterns", "best_practices"],
        description="Types of context to fetch"
    )
    budget: BudgetLevel = BudgetLevel.standard
    max_items_per_type: int = 10


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/budgets")
async def list_token_budgets():
    """
    List available token budget levels.

    Returns budget names with their token limits.
    """
    return {
        "budgets": {
            budget.name: {
                "tokens": budget.value,
                "chars_approx": budget.value * 4,
                "description": _get_budget_description(budget)
            }
            for budget in TokenBudget
        },
        "default": "standard"
    }


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_context(request: OptimizeRequest):
    """
    Optimize a list of context items within token budget.

    Applies:
    - Relevance-based prioritization
    - Smart truncation at sentence boundaries
    - Deduplication and compression
    """
    service = get_token_optimization_service()

    # Convert to internal format
    items = [
        {
            "content": item.content,
            "content_type": item.content_type,
            "relevance": item.relevance,
            **(item.metadata or {})
        }
        for item in request.items
    ]

    # Map budget level
    budget = _map_budget_level(request.budget)

    # Extract query terms
    query_terms = request.query.split() if request.query else None

    # Optimize
    result = service.optimize_context(
        items=items,
        budget=budget,
        query_terms=query_terms,
        preserve_structure=request.preserve_structure
    )

    return OptimizeResponse(
        content=result.content,
        token_count=result.token_count,
        items_included=result.items_included,
        items_truncated=result.items_truncated,
        avg_relevance=sum(result.relevance_scores) / len(result.relevance_scores) if result.relevance_scores else 0,
        budget_used_percent=result.budget_used_percent
    )


@router.post("/optimize/categories", response_model=CategoryOptimizeResponse)
async def optimize_categorized_context(request: CategoryOptimizeRequest):
    """
    Optimize categorized context with budget distribution.

    Distributes token budget across categories based on priority:
    - code_patterns: 30%
    - similar_issues: 25%
    - best_practices: 20%
    - documentation: 15%
    - examples: 10%
    """
    service = get_token_optimization_service()

    # Convert categories to internal format
    context_dict = {}
    for category, items in request.categories.items():
        context_dict[category] = [
            {
                "content": item.content,
                "content_type": item.content_type,
                "relevance": item.relevance,
                **(item.metadata or {})
            }
            for item in items
        ]

    # Map budget level
    budget = _map_budget_level(request.budget)

    # Optimize
    result = service.optimize_for_llm(
        context_dict=context_dict,
        budget=budget,
        query=request.query
    )

    return CategoryOptimizeResponse(
        categories=result["categories"],
        metadata=result["metadata"]
    )


@router.get("/estimate-tokens")
async def estimate_tokens(
    text: str = Query(..., description="Text to estimate tokens for")
):
    """
    Estimate token count for given text.

    Uses approximation of ~4 characters per token.
    """
    service = get_token_optimization_service()
    token_count = service.estimate_tokens(text)

    return {
        "text_length": len(text),
        "estimated_tokens": token_count,
        "chars_per_token": service.CHARS_PER_TOKEN,
        "note": "Approximation - actual tokens may vary by model"
    }


@router.post("/vector-db/optimized")
async def get_optimized_vector_context(request: VectorContextRequest):
    """
    Fetch and optimize Vector DB context in one call.

    Combines ChromaDB query with token optimization.
    Returns context ready for LLM consumption.
    """
    try:
        from app.services.chroma_service import ChromaService
        CHROMA_AVAILABLE = True
    except ImportError:
        CHROMA_AVAILABLE = False

    if not CHROMA_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ChromaDB service not available"
        )

    try:
        # Fetch from Vector DB
        chroma_service = ChromaService()
        raw_context = {}

        for context_type in request.context_types:
            # Query ChromaDB for this context type
            results = chroma_service.query(
                collection_name=f"project_{request.project_id}_{context_type}",
                query_text=request.query,
                n_results=request.max_items_per_type
            )

            if results and results.get("documents"):
                raw_context[context_type] = [
                    {
                        "content": doc,
                        "similarity": results.get("distances", [[]])[0][i] if results.get("distances") else None,
                        "metadata": results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                    }
                    for i, doc in enumerate(results["documents"][0])
                ]

        # Optimize the fetched context
        service = get_token_optimization_service()
        budget = _map_budget_level(request.budget)

        optimized = service.optimize_for_llm(
            context_dict=raw_context,
            budget=budget,
            query=request.query
        )

        return {
            "project_id": request.project_id,
            "query": request.query,
            "optimized_context": optimized,
            "context_types_fetched": list(raw_context.keys())
        }

    except Exception as e:
        # Return graceful fallback
        return {
            "project_id": request.project_id,
            "query": request.query,
            "optimized_context": {
                "categories": {},
                "metadata": {
                    "error": str(e),
                    "tokens_used": 0,
                    "budget_used_percent": 0
                }
            },
            "context_types_fetched": []
        }


@router.get("/health")
async def health_check():
    """Token context API health check."""
    return {
        "status": "healthy",
        "service": "token-optimization",
        "endpoints": 6,
        "features": [
            "budget_levels",
            "item_optimization",
            "category_optimization",
            "token_estimation",
            "vector_db_integration"
        ]
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _map_budget_level(level: BudgetLevel) -> TokenBudget:
    """Map API budget level to internal TokenBudget."""
    mapping = {
        BudgetLevel.minimal: TokenBudget.MINIMAL,
        BudgetLevel.compact: TokenBudget.COMPACT,
        BudgetLevel.standard: TokenBudget.STANDARD,
        BudgetLevel.extended: TokenBudget.EXTENDED,
        BudgetLevel.full: TokenBudget.FULL,
    }
    return mapping.get(level, TokenBudget.STANDARD)


def _get_budget_description(budget: TokenBudget) -> str:
    """Get human-readable description for budget level."""
    descriptions = {
        TokenBudget.MINIMAL: "Quick lookups, single fact retrieval",
        TokenBudget.COMPACT: "Standard context for simple queries",
        TokenBudget.STANDARD: "Default for most operations",
        TokenBudget.EXTENDED: "Complex analysis requiring more context",
        TokenBudget.FULL: "Comprehensive context for deep analysis",
    }
    return descriptions.get(budget, "Unknown budget level")
