"""
Debt Categorization API

Links technical debt items to backlog hierarchy (epic/feature/story)
for categorized issue tracking and weak spot identification.

Endpoints:
- GET /stats/by-epic - Statistics per epic
- GET /stats/by-feature - Statistics per feature
- GET /stats/by-story - Statistics per story
- GET /stats/weak-spots - Identify weak spots
- GET /issues/{backlog_type}/{backlog_id} - Issues for a backlog item
- POST /mappings - Create file-to-backlog mapping
- GET /mappings - List file mappings
- DELETE /mappings/{id} - Delete a mapping
- POST /categorize - Auto-categorize debt items
- PUT /items/{id}/categorize - Manually categorize an item
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.debt_categorization_service import get_debt_categorization_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debt-categorization", tags=["debt-categorization"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateFileMappingRequest(BaseModel):
    """Request to create a file-to-backlog mapping."""
    file_pattern: str = Field(..., description="Glob pattern for file matching (e.g., 'src/auth/**/*.php')")
    epic_id: Optional[str] = Field(None, description="Epic UUID to link to")
    feature_id: Optional[str] = Field(None, description="Feature UUID to link to")
    story_id: Optional[str] = Field(None, description="Story UUID to link to")
    priority: int = Field(0, description="Priority for matching (higher = more specific)")


class ManualCategorizeRequest(BaseModel):
    """Request to manually categorize a debt item."""
    epic_id: Optional[str] = Field(None, description="Epic UUID")
    feature_id: Optional[str] = Field(None, description="Feature UUID")
    story_id: Optional[str] = Field(None, description="Story UUID")


class BacklogStatsResponse(BaseModel):
    """Statistics for a backlog item."""
    backlog_type: str
    backlog_id: Optional[str]
    backlog_title: str
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_principal: float
    total_interest: float
    health_score: float


class WeakSpotsResponse(BaseModel):
    """Response containing weak spot analysis."""
    project_id: int
    weak_epics: List[Dict[str, Any]]
    weak_features: List[Dict[str, Any]]
    weak_stories: List[Dict[str, Any]]
    uncategorized: Dict[str, Any]
    summary: Dict[str, Any]


class CategorizationResultResponse(BaseModel):
    """Response for categorization operation."""
    total_processed: int
    categorized: int
    skipped: int
    project_id: int


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/by-epic", response_model=List[BacklogStatsResponse])
async def get_stats_by_epic(
    project_id: int = Query(..., description="Project ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get technical debt statistics aggregated by epic.

    Returns counts, principal, interest, and health score per epic.
    Use this to identify which epics have the most quality issues.
    """
    try:
        service = get_debt_categorization_service(db)
        stats = await service.get_stats_by_epic(project_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats by epic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-feature", response_model=List[BacklogStatsResponse])
async def get_stats_by_feature(
    project_id: int = Query(..., description="Project ID"),
    epic_id: Optional[str] = Query(None, description="Filter by epic UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get technical debt statistics aggregated by feature.

    Optionally filter by epic_id to see features within a specific epic.
    """
    try:
        service = get_debt_categorization_service(db)
        epic_uuid = UUID(epic_id) if epic_id else None
        stats = await service.get_stats_by_feature(project_id, epic_uuid)
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats by feature: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-story", response_model=List[BacklogStatsResponse])
async def get_stats_by_story(
    project_id: int = Query(..., description="Project ID"),
    feature_id: Optional[str] = Query(None, description="Filter by feature UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get technical debt statistics aggregated by user story.

    Optionally filter by feature_id to see stories within a specific feature.
    """
    try:
        service = get_debt_categorization_service(db)
        feature_uuid = UUID(feature_id) if feature_id else None
        stats = await service.get_stats_by_story(project_id, feature_uuid)
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats by story: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/weak-spots", response_model=WeakSpotsResponse)
async def get_weak_spots(
    project_id: int = Query(..., description="Project ID"),
    top_n: int = Query(10, description="Number of weak spots to return per category"),
    db: AsyncSession = Depends(get_db)
):
    """
    Identify weak spots in the codebase.

    Returns the backlog items with the lowest health scores,
    indicating areas that need the most attention.
    """
    try:
        service = get_debt_categorization_service(db)
        weak_spots = await service.get_weak_spots(project_id, top_n)
        return weak_spots
    except Exception as e:
        logger.error(f"Failed to get weak spots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/uncategorized")
async def get_uncategorized_stats(
    project_id: int = Query(..., description="Project ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for uncategorized debt items.

    These items don't have a file mapping and need manual categorization
    or new file mappings to be added.
    """
    try:
        service = get_debt_categorization_service(db)
        stats = await service.get_uncategorized_stats(project_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get uncategorized stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ISSUES ENDPOINTS
# ============================================================================

@router.get("/issues/{backlog_type}/{backlog_id}")
async def get_issues_for_backlog_item(
    backlog_type: str,
    backlog_id: str,
    project_id: int = Query(..., description="Project ID"),
    limit: int = Query(100, description="Max issues to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all debt items linked to a specific backlog item.

    backlog_type: 'epic', 'feature', or 'story'
    backlog_id: UUID of the backlog item

    Returns issues sorted by severity (critical first) and principal.
    """
    if backlog_type not in ["epic", "feature", "story"]:
        raise HTTPException(status_code=400, detail="backlog_type must be 'epic', 'feature', or 'story'")

    try:
        service = get_debt_categorization_service(db)
        issues = await service.get_issues_for_backlog_item(
            project_id=project_id,
            backlog_type=backlog_type,
            backlog_id=UUID(backlog_id),
            limit=limit,
            offset=offset,
        )
        return {"items": issues, "total": len(issues), "limit": limit, "offset": offset}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")
    except Exception as e:
        logger.error(f"Failed to get issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAPPING ENDPOINTS
# ============================================================================

@router.post("/mappings")
async def create_file_mapping(
    project_id: int,
    request: CreateFileMappingRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a file-to-backlog mapping.

    File patterns support glob syntax:
    - '*' matches any characters within a path segment
    - '**' matches any path segments
    - '?' matches a single character

    Examples:
    - 'src/auth/*' -> All files in src/auth/
    - 'src/api/**/*.php' -> All PHP files under src/api/
    - 'src/models/User.php' -> Exact file match
    """
    try:
        service = get_debt_categorization_service(db)
        result = await service.create_file_mapping(
            project_id=project_id,
            file_pattern=request.file_pattern,
            epic_id=UUID(request.epic_id) if request.epic_id else None,
            feature_id=UUID(request.feature_id) if request.feature_id else None,
            story_id=UUID(request.story_id) if request.story_id else None,
            priority=request.priority,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")
    except Exception as e:
        logger.error(f"Failed to create mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mappings")
async def list_file_mappings(
    project_id: int = Query(..., description="Project ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all file-to-backlog mappings for a project.
    """
    try:
        service = get_debt_categorization_service(db)
        mappings = await service.get_file_mappings(project_id)
        return {"mappings": mappings, "total": len(mappings)}
    except Exception as e:
        logger.error(f"Failed to list mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mappings/{mapping_id}")
async def delete_file_mapping(
    mapping_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a file-to-backlog mapping.
    """
    try:
        service = get_debt_categorization_service(db)
        deleted = await service.delete_file_mapping(mapping_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return {"deleted": True, "id": mapping_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CATEGORIZATION ENDPOINTS
# ============================================================================

@router.post("/categorize", response_model=CategorizationResultResponse)
async def auto_categorize_debt_items(
    project_id: int = Query(..., description="Project ID"),
    limit: int = Query(1000, description="Max items to process"),
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-categorize uncategorized debt items based on file mappings.

    Matches file paths against configured patterns and assigns
    the corresponding epic/feature/story.
    """
    try:
        service = get_debt_categorization_service(db)
        result = await service.auto_categorize_debt_items(project_id, limit)
        return result
    except Exception as e:
        logger.error(f"Failed to categorize items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/items/{item_id}/categorize")
async def manually_categorize_item(
    item_id: int,
    request: ManualCategorizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually assign a debt item to a backlog item.

    Use this when auto-categorization doesn't work or for specific assignments.
    """
    try:
        service = get_debt_categorization_service(db)
        result = await service.manually_categorize_debt_item(
            item_id=item_id,
            epic_id=UUID(request.epic_id) if request.epic_id else None,
            feature_id=UUID(request.feature_id) if request.feature_id else None,
            story_id=UUID(request.story_id) if request.story_id else None,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")
    except Exception as e:
        logger.error(f"Failed to categorize item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD DATA ENDPOINT
# ============================================================================

@router.get("/dashboard/{project_id}")
async def get_dashboard_data(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all data needed for the quality dashboard's categorized view.

    Returns:
    - Stats by epic (with health scores)
    - Stats by feature
    - Uncategorized stats
    - Weak spots summary
    - Available mappings
    """
    try:
        service = get_debt_categorization_service(db)

        epic_stats = await service.get_stats_by_epic(project_id)
        feature_stats = await service.get_stats_by_feature(project_id)
        uncategorized = await service.get_uncategorized_stats(project_id)
        weak_spots = await service.get_weak_spots(project_id, top_n=5)
        mappings = await service.get_file_mappings(project_id)

        # Calculate overall categorization rate
        total_categorized = sum(s["total_issues"] for s in epic_stats)
        total_uncategorized = uncategorized["total_issues"]
        total_issues = total_categorized + total_uncategorized
        categorization_rate = (total_categorized / total_issues * 100) if total_issues > 0 else 0

        return {
            "project_id": project_id,
            "stats_by_epic": epic_stats,
            "stats_by_feature": feature_stats,
            "uncategorized": uncategorized,
            "weak_spots": weak_spots,
            "mappings": mappings,
            "summary": {
                "total_issues": total_issues,
                "categorized_issues": total_categorized,
                "uncategorized_issues": total_uncategorized,
                "categorization_rate": round(categorization_rate, 1),
                "total_mappings": len(mappings),
            }
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
