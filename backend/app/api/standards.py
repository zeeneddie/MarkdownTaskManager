"""
Standards API - Endpoints for managing coding standards

Week 59: Agent OS Integration
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

from app.services.standards_loader_service import (
    get_standards_loader,
    StandardCategory,
    TechStack,
)


router = APIRouter(prefix="/api/standards", tags=["standards"])


# Response schemas
class StandardItem(BaseModel):
    key: str
    category: str
    name: str
    size: int


class CategoryItem(BaseModel):
    category: str
    count: int


class SearchResult(BaseModel):
    key: str
    category: str
    name: str
    snippet: str


class StandardsStats(BaseModel):
    total_standards: int
    total_size_bytes: int
    total_size_kb: float
    categories: List[CategoryItem]
    standards_path: str
    path_exists: bool


class WorkflowMapping(BaseModel):
    workflow: str
    categories: List[str]


# Endpoints

@router.get("/", response_model=List[StandardItem])
async def list_standards():
    """
    List all available coding standards.

    Returns a list of all standards with their category, name, and size.
    """
    loader = get_standards_loader()
    return loader.list_standards()


@router.get("/categories", response_model=List[CategoryItem])
async def list_categories():
    """
    List all standard categories with counts.

    Categories: global, backend, frontend, testing, security
    """
    loader = get_standards_loader()
    return loader.list_categories()


@router.get("/stats", response_model=StandardsStats)
async def get_stats():
    """
    Get statistics about loaded standards.

    Returns total count, size, and category breakdown.
    """
    loader = get_standards_loader()
    return loader.get_stats()


@router.get("/mapping", response_model=List[WorkflowMapping])
async def get_workflow_mapping():
    """
    Get the workflow to standards category mapping.

    Shows which standards are loaded for each workflow type.
    """
    loader = get_standards_loader()
    mapping = loader.get_workflow_mapping()
    return [
        {"workflow": workflow, "categories": categories}
        for workflow, categories in mapping.items()
    ]


@router.get("/tech-stacks")
async def list_tech_stacks() -> Dict[str, Any]:
    """
    List all supported tech stacks for filtering standards.

    Returns:
        Dict with available tech stacks and their descriptions
    """
    return {
        "tech_stacks": [
            {"id": stack.value, "name": stack.name}
            for stack in TechStack
        ],
        "description": "Use these tech stack IDs when filtering standards for a project. "
                       "Multiple stacks can be combined (e.g., 'python,javascript' for full-stack projects)."
    }


@router.get("/search")
async def search_standards(
    q: str = Query(..., min_length=2, description="Search query")
) -> List[SearchResult]:
    """
    Search standards by content.

    Searches all standards for the given query (case-insensitive).
    Returns matching standards with context snippets.
    """
    loader = get_standards_loader()
    results = loader.search(q)
    if not results:
        return []
    return results


@router.get("/workflow/{workflow_type}")
async def get_standards_for_workflow(
    workflow_type: str,
    tech_stacks: Optional[str] = Query(
        None,
        description="Comma-separated list of tech stacks to filter by (e.g., 'python,javascript')"
    )
) -> Dict[str, Any]:
    """
    Get concatenated standards for a specific workflow type, filtered by tech stack.

    This is what gets injected into agent prompts.

    Args:
        workflow_type: Workflow type (e.g., NEW_FEATURE, BUG, MAINTENANCE, MIGRATION)
        tech_stacks: Optional comma-separated list of tech stacks.
                     Valid stacks: python, javascript, dotnet, java, go, rust

    Returns:
        Dict with workflow type, tech stacks used, and concatenated standards content

    Example:
        GET /api/standards/workflow/MIGRATION?tech_stacks=dotnet
        -> Returns only .NET migration standards

        GET /api/standards/workflow/NEW_FEATURE?tech_stacks=python,javascript
        -> Returns Python and JavaScript standards for new features
    """
    loader = get_standards_loader()

    # Parse tech_stacks from comma-separated string
    stack_list = None
    if tech_stacks:
        stack_list = [s.strip() for s in tech_stacks.split(",") if s.strip()]

    content = loader.get_standards_for_workflow(workflow_type, stack_list)
    return {
        "workflow_type": workflow_type.upper(),
        "tech_stacks": stack_list,
        "content": content,
        "content_length": len(content)
    }


@router.get("/{category}/{name}")
async def get_standard(category: str, name: str) -> Dict[str, str]:
    """
    Get a specific standard by category and name.

    Args:
        category: Standard category (global, backend, frontend, testing, security)
        name: Standard name without .md extension (e.g., git-conventions)

    Returns:
        Dict with standard metadata and content
    """
    # Validate category
    valid_categories = [c.value for c in StandardCategory]
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {valid_categories}"
        )

    loader = get_standards_loader()
    content = loader.get_standard(category, name)

    if content is None:
        raise HTTPException(
            status_code=404,
            detail=f"Standard not found: {category}/{name}"
        )

    return {
        "category": category,
        "name": name,
        "key": f"{category}/{name}",
        "content": content,
        "content_length": len(content)
    }


@router.post("/reload")
async def reload_standards() -> Dict[str, Any]:
    """
    Reload all standards from disk.

    Use this after adding or modifying standards files.

    Returns:
        Dict with reload status and count
    """
    loader = get_standards_loader()
    count = loader.reload()
    return {
        "status": "success",
        "message": f"Reloaded {count} standards",
        "count": count
    }
