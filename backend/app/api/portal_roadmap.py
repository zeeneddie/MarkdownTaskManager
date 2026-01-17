"""
Week 90: Portal Roadmap API Endpoints

Provides endpoints for:
- Analysis queue (submit backlog items for agent analysis)
- Release management (CRUD, timeline, status)
- Roadmap items (only analyzed items can be added)
- Public roadmaps (shareable URLs, customization)
"""

from datetime import datetime, date, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.portal_roadmap import (
    PortalAnalysisQueue,
    PortalRelease,
    PortalRoadmapItem,
    PortalPublicRoadmap,
    ANALYSIS_STATUSES,
    RELEASE_STATUSES,
    ROADMAP_ITEM_STATUSES
)
from app.models.graph_workflow import PortalFeatureRequest
from app.models.item import Item

router = APIRouter(prefix="/api/portal/roadmap", tags=["portal-roadmap"])


# =============================================================================
# Pydantic Schemas
# =============================================================================

# Analysis Queue Schemas
class AnalysisQueueCreate(BaseModel):
    """Submit a backlog item for analysis."""
    item_id: str = Field(..., min_length=1, max_length=50)
    project_id: Optional[int] = None
    priority: int = Field(0, ge=0, le=100)
    requested_by: Optional[str] = Field(None, max_length=100)


class AnalysisQueueUpdate(BaseModel):
    """Update analysis queue entry (used by agents)."""
    status: Optional[str] = Field(None, pattern=r'^(pending|analyzing|completed|failed)$')
    analyzed_by: Optional[str] = Field(None, max_length=100)
    analysis_result: Optional[dict] = None


# Release Schemas
class ReleaseCreate(BaseModel):
    """Create a new release."""
    project_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    target_date: Optional[date] = None
    start_date: Optional[date] = None
    status: str = Field("planned", pattern=r'^(planned|in_progress|released|cancelled)$')
    display_order: int = 0


class ReleaseUpdate(BaseModel):
    """Update an existing release."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    target_date: Optional[date] = None
    actual_date: Optional[date] = None
    start_date: Optional[date] = None
    status: Optional[str] = Field(None, pattern=r'^(planned|in_progress|released|cancelled)$')
    display_order: Optional[int] = None


class RoadmapItemCreate(BaseModel):
    """Add an analyzed item to the roadmap.

    Either item_id (backlog item) OR feature_request_id must be provided.
    For backlog items, the item must have completed analysis first.
    """
    item_id: Optional[str] = Field(None, max_length=50)  # Backlog item (must be analyzed)
    feature_request_id: Optional[UUID] = None  # Portal feature request
    release_id: Optional[UUID] = None
    display_order: int = 0
    lane: Optional[str] = Field(None, max_length=50)
    roadmap_status: Optional[str] = None
    estimated_days: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None  # List of item_ids


class RoadmapItemUpdate(BaseModel):
    """Update a roadmap item."""
    release_id: Optional[UUID] = None
    display_order: Optional[int] = None
    lane: Optional[str] = Field(None, max_length=50)
    roadmap_status: Optional[str] = None
    estimated_days: Optional[int] = Field(None, ge=0)
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None


class RoadmapItemReorder(BaseModel):
    """Reorder items within a release."""
    item_ids: List[UUID]  # Ordered list of item IDs


class PublicRoadmapCreate(BaseModel):
    """Create a public roadmap configuration."""
    project_id: Optional[int] = None
    slug: str = Field(..., min_length=3, max_length=100, pattern=r'^[a-z0-9-]+$')
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    show_completed: bool = True
    show_cancelled: bool = False
    show_dates: bool = True
    show_progress: bool = True
    show_votes: bool = True
    theme: str = Field("light", pattern=r'^(light|dark|auto)$')
    logo_url: Optional[str] = Field(None, max_length=500)
    header_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class PublicRoadmapUpdate(BaseModel):
    """Update a public roadmap configuration."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    show_completed: Optional[bool] = None
    show_cancelled: Optional[bool] = None
    show_dates: Optional[bool] = None
    show_progress: Optional[bool] = None
    show_votes: Optional[bool] = None
    included_releases: Optional[List[str]] = None
    excluded_statuses: Optional[List[str]] = None
    theme: Optional[str] = Field(None, pattern=r'^(light|dark|auto)$')
    custom_css: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    header_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


# =============================================================================
# Analysis Queue Endpoints
# =============================================================================

@router.post("/analysis-queue")
async def submit_for_analysis(
    data: AnalysisQueueCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit a backlog item for agent analysis."""
    from sqlalchemy import select

    # Verify item exists
    result = await db.execute(
        select(Item).where(Item.id == data.item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Backlog item not found")

    # Check if already in queue
    existing = await db.execute(
        select(PortalAnalysisQueue).where(
            PortalAnalysisQueue.item_id == data.item_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Item already in analysis queue")

    queue_entry = PortalAnalysisQueue(
        item_id=data.item_id,
        project_id=data.project_id,
        priority=data.priority,
        requested_by=data.requested_by
    )
    db.add(queue_entry)
    await db.commit()
    await db.refresh(queue_entry)

    return queue_entry.to_dict(include_item=True)


@router.get("/analysis-queue")
async def list_analysis_queue(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    include_items: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List analysis queue entries."""
    from sqlalchemy import select

    query = select(PortalAnalysisQueue)

    if project_id is not None:
        query = query.where(PortalAnalysisQueue.project_id == project_id)
    if status:
        query = query.where(PortalAnalysisQueue.status == status)

    query = query.order_by(
        PortalAnalysisQueue.priority.desc(),
        PortalAnalysisQueue.created_at
    )

    result = await db.execute(query)
    entries = result.scalars().all()

    return [e.to_dict(include_item=include_items) for e in entries]


@router.get("/analysis-queue/pending")
async def get_pending_analysis(
    project_id: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get pending items for agents to analyze (highest priority first)."""
    from sqlalchemy import select

    query = select(PortalAnalysisQueue).where(
        PortalAnalysisQueue.status == "pending"
    )

    if project_id is not None:
        query = query.where(PortalAnalysisQueue.project_id == project_id)

    query = query.order_by(
        PortalAnalysisQueue.priority.desc(),
        PortalAnalysisQueue.created_at
    ).limit(limit)

    result = await db.execute(query)
    entries = result.scalars().all()

    return [e.to_dict(include_item=True) for e in entries]


@router.get("/analysis-queue/completed")
async def get_completed_analysis(
    project_id: Optional[int] = None,
    not_on_roadmap: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get completed analysis entries (ready for roadmap)."""
    from sqlalchemy import select

    query = select(PortalAnalysisQueue).where(
        PortalAnalysisQueue.status == "completed"
    )

    if project_id is not None:
        query = query.where(PortalAnalysisQueue.project_id == project_id)

    query = query.order_by(PortalAnalysisQueue.analyzed_at.desc())

    result = await db.execute(query)
    entries = result.scalars().all()

    if not_on_roadmap:
        # Filter out items already on roadmap
        roadmap_items = await db.execute(
            select(PortalRoadmapItem.item_id)
        )
        on_roadmap = {r.item_id for r in roadmap_items.fetchall()}
        entries = [e for e in entries if e.item_id not in on_roadmap]

    return [e.to_dict(include_item=True) for e in entries]


@router.get("/analysis-queue/stats")
async def get_analysis_queue_stats(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get analysis queue statistics."""
    from sqlalchemy import select

    query = select(PortalAnalysisQueue)
    if project_id:
        query = query.where(PortalAnalysisQueue.project_id == project_id)

    result = await db.execute(query)
    entries = result.scalars().all()

    stats = {status: 0 for status in ANALYSIS_STATUSES}
    for entry in entries:
        if entry.status in stats:
            stats[entry.status] += 1

    return {
        "total": len(entries),
        "by_status": stats,
        "ready_for_roadmap": stats["completed"],
        "pending_analysis": stats["pending"],
        "in_progress": stats["analyzing"]
    }


@router.get("/analysis-queue/{queue_id}")
async def get_analysis_entry(
    queue_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific analysis queue entry."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalAnalysisQueue).where(PortalAnalysisQueue.id == queue_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Analysis queue entry not found")

    return entry.to_dict(include_item=True)


@router.patch("/analysis-queue/{queue_id}")
async def update_analysis_entry(
    queue_id: UUID,
    data: AnalysisQueueUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update analysis queue entry (used by agents to report results)."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalAnalysisQueue).where(PortalAnalysisQueue.id == queue_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Analysis queue entry not found")

    update_data = data.model_dump(exclude_unset=True)

    # If marking as completed, set analyzed_at
    if update_data.get("status") == "completed" and entry.status != "completed":
        update_data["analyzed_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(entry, field, value)

    entry.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(entry)

    return entry.to_dict(include_item=True)


@router.post("/analysis-queue/{queue_id}/start")
async def start_analysis(
    queue_id: UUID,
    agent_name: str = "Peter",
    db: AsyncSession = Depends(get_db)
):
    """Mark analysis as started (agent is working on it)."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalAnalysisQueue).where(PortalAnalysisQueue.id == queue_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Analysis queue entry not found")

    if entry.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot start: current status is {entry.status}")

    entry.status = "analyzing"
    entry.analyzed_by = agent_name
    entry.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(entry)

    return entry.to_dict(include_item=True)


@router.post("/analysis-queue/{queue_id}/complete")
async def complete_analysis(
    queue_id: UUID,
    analysis_result: dict,
    agent_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Mark analysis as completed with results."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalAnalysisQueue).where(PortalAnalysisQueue.id == queue_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Analysis queue entry not found")

    entry.status = "completed"
    entry.analyzed_at = datetime.now(timezone.utc)
    entry.analysis_result = analysis_result
    if agent_name:
        entry.analyzed_by = agent_name
    entry.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(entry)

    return entry.to_dict(include_item=True)


@router.delete("/analysis-queue/{queue_id}")
async def remove_from_analysis_queue(
    queue_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Remove item from analysis queue."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalAnalysisQueue).where(PortalAnalysisQueue.id == queue_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Analysis queue entry not found")

    await db.delete(entry)
    await db.commit()

    return {"status": "removed", "queue_id": str(queue_id)}


@router.get("/backlog/available")
async def get_available_backlog_items(
    item_type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get backlog items that are available for analysis (not yet in queue).

    These items can be selected and submitted to the analysis queue.
    """
    from sqlalchemy import select
    from app.models.item import ItemType

    # Get items already in analysis queue
    queue_result = await db.execute(
        select(PortalAnalysisQueue.item_id)
    )
    in_queue = {r.item_id for r in queue_result.fetchall()}

    # Get all backlog items
    query = select(Item)

    if item_type:
        try:
            type_enum = ItemType(item_type.lower())
            query = query.where(Item.type == type_enum)
        except ValueError:
            pass

    query = query.order_by(Item.created_at.desc()).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    # Filter out items already in queue
    available_items = [
        {
            "id": item.id,
            "type": item.type.value if item.type else None,
            "title": item.title,
            "status": item.status,
            "priority": item.priority,
            "sp": item.sp,
            "in_analysis_queue": item.id in in_queue
        }
        for item in items
        if item.id not in in_queue
    ]

    return {
        "available": available_items,
        "total_available": len(available_items),
        "in_queue_count": len(in_queue)
    }


# =============================================================================
# Release Endpoints
# =============================================================================

@router.post("/releases")
async def create_release(
    data: ReleaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new release/milestone."""
    release = PortalRelease(
        project_id=data.project_id,
        name=data.name,
        version=data.version,
        description=data.description,
        color=data.color,
        target_date=data.target_date,
        start_date=data.start_date,
        status=data.status,
        display_order=data.display_order
    )
    db.add(release)
    await db.commit()
    await db.refresh(release)
    return release.to_dict()


@router.get("/releases")
async def list_releases(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    include_items: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all releases with optional filtering."""
    from sqlalchemy import select

    query = select(PortalRelease)

    if project_id is not None:
        query = query.where(PortalRelease.project_id == project_id)
    if status:
        query = query.where(PortalRelease.status == status)

    query = query.order_by(PortalRelease.display_order, PortalRelease.target_date)

    result = await db.execute(query)
    releases = result.scalars().all()

    return [r.to_dict(include_items=include_items) for r in releases]


@router.get("/releases/{release_id}")
async def get_release(
    release_id: UUID,
    include_items: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific release by ID."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRelease).where(PortalRelease.id == release_id)
    )
    release = result.scalar_one_or_none()

    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    return release.to_dict(include_items=include_items)


@router.patch("/releases/{release_id}")
async def update_release(
    release_id: UUID,
    data: ReleaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a release."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRelease).where(PortalRelease.id == release_id)
    )
    release = result.scalar_one_or_none()

    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle status change to "released"
    if update_data.get("status") == "released" and release.status != "released":
        update_data["released_at"] = datetime.now(timezone.utc)
        if not update_data.get("actual_date"):
            update_data["actual_date"] = date.today()

    for field, value in update_data.items():
        setattr(release, field, value)

    release.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(release)

    return release.to_dict()


@router.delete("/releases/{release_id}")
async def delete_release(
    release_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a release (items will have release_id set to NULL)."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRelease).where(PortalRelease.id == release_id)
    )
    release = result.scalar_one_or_none()

    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    await db.delete(release)
    await db.commit()

    return {"status": "deleted", "release_id": str(release_id)}


@router.post("/releases/reorder")
async def reorder_releases(
    release_ids: List[UUID],
    db: AsyncSession = Depends(get_db)
):
    """Reorder releases by providing ordered list of IDs."""
    from sqlalchemy import select

    for index, release_id in enumerate(release_ids):
        result = await db.execute(
            select(PortalRelease).where(PortalRelease.id == release_id)
        )
        release = result.scalar_one_or_none()
        if release:
            release.display_order = index

    await db.commit()

    return {"status": "reordered", "count": len(release_ids)}


@router.get("/releases/{release_id}/timeline")
async def get_release_timeline(
    release_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get timeline view data for a release."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRelease).where(PortalRelease.id == release_id)
    )
    release = result.scalar_one_or_none()

    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    # Get items with their estimated days
    items_result = await db.execute(
        select(PortalRoadmapItem)
        .where(PortalRoadmapItem.release_id == release_id)
        .order_by(PortalRoadmapItem.display_order)
    )
    items = items_result.scalars().all()

    total_days = sum(item.estimated_days or 0 for item in items)
    completed_days = sum(
        (item.estimated_days or 0) * (item.progress_percent or 0) / 100
        for item in items
    )

    return {
        "release": release.to_dict(),
        "total_estimated_days": total_days,
        "completed_days": round(completed_days, 1),
        "overall_progress": round(completed_days / total_days * 100, 1) if total_days > 0 else 0,
        "days_until_target": release.days_until_target,
        "is_overdue": release.is_overdue,
        "items": [item.to_dict() for item in items]
    }


# =============================================================================
# Roadmap Item Endpoints
# =============================================================================

@router.post("/items")
async def add_to_roadmap(
    data: RoadmapItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add an analyzed backlog item or feature request to the roadmap.

    IMPORTANT: Backlog items must have completed analysis before they
    can be added to the roadmap.
    """
    from sqlalchemy import select

    # Validate: either item_id OR feature_request_id must be provided
    if not data.item_id and not data.feature_request_id:
        raise HTTPException(
            status_code=400,
            detail="Either item_id or feature_request_id must be provided"
        )

    analysis_queue_id = None

    # If adding a backlog item, validate it has been analyzed
    if data.item_id:
        # Verify item exists
        result = await db.execute(
            select(Item).where(Item.id == data.item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Backlog item not found")

        # Check if analysis is completed
        analysis_result = await db.execute(
            select(PortalAnalysisQueue).where(
                PortalAnalysisQueue.item_id == data.item_id,
                PortalAnalysisQueue.status == "completed"
            )
        )
        analysis_entry = analysis_result.scalar_one_or_none()

        if not analysis_entry:
            raise HTTPException(
                status_code=400,
                detail="Item must be analyzed before adding to roadmap. "
                       "Submit to /analysis-queue first and wait for analysis to complete."
            )

        analysis_queue_id = analysis_entry.id

        # Check if already on roadmap
        existing = await db.execute(
            select(PortalRoadmapItem).where(
                PortalRoadmapItem.item_id == data.item_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Item already on roadmap")

    # If adding a feature request
    if data.feature_request_id:
        # Verify feature request exists
        result = await db.execute(
            select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == data.feature_request_id
            )
        )
        feature = result.scalar_one_or_none()
        if not feature:
            raise HTTPException(status_code=404, detail="Feature request not found")

        # Check if already on roadmap
        existing = await db.execute(
            select(PortalRoadmapItem).where(
                PortalRoadmapItem.feature_request_id == data.feature_request_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Feature request already on roadmap")

    roadmap_item = PortalRoadmapItem(
        item_id=data.item_id,
        feature_request_id=data.feature_request_id,
        analysis_queue_id=analysis_queue_id,
        release_id=data.release_id,
        display_order=data.display_order,
        lane=data.lane,
        roadmap_status=data.roadmap_status or "backlog",
        estimated_days=data.estimated_days,
        notes=data.notes,
        tags=data.tags,
        depends_on=data.depends_on
    )
    db.add(roadmap_item)
    await db.commit()
    await db.refresh(roadmap_item)

    return roadmap_item.to_dict()


@router.get("/items")
async def list_roadmap_items(
    release_id: Optional[UUID] = None,
    status: Optional[str] = None,
    lane: Optional[str] = None,
    include_unassigned: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List roadmap items with optional filtering."""
    from sqlalchemy import select

    query = select(PortalRoadmapItem)

    conditions = []
    if release_id:
        conditions.append(PortalRoadmapItem.release_id == release_id)
    elif not include_unassigned:
        conditions.append(PortalRoadmapItem.release_id.isnot(None))

    if status:
        conditions.append(PortalRoadmapItem.roadmap_status == status)
    if lane:
        conditions.append(PortalRoadmapItem.lane == lane)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(PortalRoadmapItem.display_order)

    result = await db.execute(query)
    items = result.scalars().all()

    return [item.to_dict() for item in items]


@router.get("/items/{item_id}")
async def get_roadmap_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific roadmap item."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRoadmapItem).where(PortalRoadmapItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    return item.to_dict()


@router.patch("/items/{item_id}")
async def update_roadmap_item(
    item_id: UUID,
    data: RoadmapItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a roadmap item."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRoadmapItem).where(PortalRoadmapItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)

    return item.to_dict()


@router.delete("/items/{item_id}")
async def remove_from_roadmap(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Remove a feature from the roadmap."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRoadmapItem).where(PortalRoadmapItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    await db.delete(item)
    await db.commit()

    return {"status": "removed", "item_id": str(item_id)}


@router.post("/items/{item_id}/move")
async def move_roadmap_item(
    item_id: UUID,
    release_id: Optional[UUID] = None,
    display_order: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Move a roadmap item to a different release or position."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRoadmapItem).where(PortalRoadmapItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    if release_id is not None:
        item.release_id = release_id
    if display_order is not None:
        item.display_order = display_order

    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)

    return item.to_dict()


@router.post("/releases/{release_id}/reorder-items")
async def reorder_release_items(
    release_id: UUID,
    data: RoadmapItemReorder,
    db: AsyncSession = Depends(get_db)
):
    """Reorder items within a release."""
    from sqlalchemy import select

    for index, item_id in enumerate(data.item_ids):
        result = await db.execute(
            select(PortalRoadmapItem).where(
                PortalRoadmapItem.id == item_id,
                PortalRoadmapItem.release_id == release_id
            )
        )
        item = result.scalar_one_or_none()
        if item:
            item.display_order = index

    await db.commit()

    return {"status": "reordered", "release_id": str(release_id), "count": len(data.item_ids)}


@router.get("/items/{item_id}/dependencies")
async def get_item_dependencies(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get dependency information for a roadmap item."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalRoadmapItem).where(PortalRoadmapItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    dependencies = []
    if item.depends_on:
        for dep_id in item.depends_on:
            dep_result = await db.execute(
                select(PortalRoadmapItem).where(
                    PortalRoadmapItem.feature_request_id == UUID(dep_id)
                )
            )
            dep_item = dep_result.scalar_one_or_none()
            if dep_item:
                dependencies.append({
                    "id": str(dep_item.id),
                    "feature_request_id": dep_id,
                    "status": dep_item.roadmap_status,
                    "progress_percent": dep_item.progress_percent,
                    "is_blocking": dep_item.roadmap_status not in ["completed", "cancelled"]
                })

    # Find items that depend on this one
    dependents_result = await db.execute(
        select(PortalRoadmapItem).where(
            PortalRoadmapItem.depends_on.contains([str(item.feature_request_id)])
        )
    )
    dependents = dependents_result.scalars().all()

    return {
        "item_id": str(item_id),
        "depends_on": dependencies,
        "blocks": [d.to_dict() for d in dependents],
        "is_blocked": any(d.get("is_blocking") for d in dependencies)
    }


# =============================================================================
# Public Roadmap Endpoints
# =============================================================================

@router.post("/public")
async def create_public_roadmap(
    data: PublicRoadmapCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new public roadmap configuration."""
    from sqlalchemy import select

    # Check slug uniqueness
    existing = await db.execute(
        select(PortalPublicRoadmap).where(PortalPublicRoadmap.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")

    roadmap = PortalPublicRoadmap(
        project_id=data.project_id,
        slug=data.slug,
        title=data.title,
        description=data.description,
        show_completed=data.show_completed,
        show_cancelled=data.show_cancelled,
        show_dates=data.show_dates,
        show_progress=data.show_progress,
        show_votes=data.show_votes,
        theme=data.theme,
        logo_url=data.logo_url,
        header_color=data.header_color
    )
    db.add(roadmap)
    await db.commit()
    await db.refresh(roadmap)

    return roadmap.to_dict()


@router.get("/public")
async def list_public_roadmaps(
    project_id: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List public roadmap configurations."""
    from sqlalchemy import select

    query = select(PortalPublicRoadmap)

    if project_id is not None:
        query = query.where(PortalPublicRoadmap.project_id == project_id)
    if active_only:
        query = query.where(PortalPublicRoadmap.is_active == True)

    query = query.order_by(PortalPublicRoadmap.created_at.desc())

    result = await db.execute(query)
    roadmaps = result.scalars().all()

    return [r.to_dict() for r in roadmaps]


@router.get("/public/by-slug/{slug}")
async def get_public_roadmap_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a public roadmap by its slug (for public viewing)."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalPublicRoadmap).where(
            PortalPublicRoadmap.slug == slug,
            PortalPublicRoadmap.is_active == True
        )
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    # Increment view count
    roadmap.increment_views()
    await db.commit()

    # Get releases and items based on configuration
    releases_query = select(PortalRelease)
    if roadmap.project_id:
        releases_query = releases_query.where(PortalRelease.project_id == roadmap.project_id)
    if roadmap.included_releases:
        releases_query = releases_query.where(
            PortalRelease.id.in_([UUID(r) for r in roadmap.included_releases])
        )
    if not roadmap.show_cancelled:
        releases_query = releases_query.where(PortalRelease.status != "cancelled")

    releases_query = releases_query.order_by(PortalRelease.display_order)
    releases_result = await db.execute(releases_query)
    releases = releases_result.scalars().all()

    # Get items for each release
    roadmap_data = []
    for release in releases:
        items_query = select(PortalRoadmapItem).where(
            PortalRoadmapItem.release_id == release.id
        )
        if roadmap.excluded_statuses:
            items_query = items_query.where(
                PortalRoadmapItem.roadmap_status.notin_(roadmap.excluded_statuses)
            )
        if not roadmap.show_completed:
            items_query = items_query.where(PortalRoadmapItem.roadmap_status != "completed")
        if not roadmap.show_cancelled:
            items_query = items_query.where(PortalRoadmapItem.roadmap_status != "cancelled")

        items_query = items_query.order_by(PortalRoadmapItem.display_order)
        items_result = await db.execute(items_query)
        items = items_result.scalars().all()

        roadmap_data.append({
            "release": release.to_dict(),
            "items": [item.to_dict() for item in items]
        })

    return {
        "config": roadmap.to_dict(),
        "releases": roadmap_data
    }


@router.get("/public/{roadmap_id}")
async def get_public_roadmap(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a public roadmap configuration by ID."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalPublicRoadmap).where(PortalPublicRoadmap.id == roadmap_id)
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Public roadmap not found")

    return roadmap.to_dict()


@router.patch("/public/{roadmap_id}")
async def update_public_roadmap(
    roadmap_id: UUID,
    data: PublicRoadmapUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a public roadmap configuration."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalPublicRoadmap).where(PortalPublicRoadmap.id == roadmap_id)
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Public roadmap not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(roadmap, field, value)

    roadmap.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(roadmap)

    return roadmap.to_dict()


@router.delete("/public/{roadmap_id}")
async def delete_public_roadmap(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a public roadmap configuration."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalPublicRoadmap).where(PortalPublicRoadmap.id == roadmap_id)
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Public roadmap not found")

    await db.delete(roadmap)
    await db.commit()

    return {"status": "deleted", "roadmap_id": str(roadmap_id)}


@router.get("/public/{roadmap_id}/stats")
async def get_public_roadmap_stats(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for a public roadmap."""
    from sqlalchemy import select

    result = await db.execute(
        select(PortalPublicRoadmap).where(PortalPublicRoadmap.id == roadmap_id)
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Public roadmap not found")

    return {
        "roadmap_id": str(roadmap_id),
        "slug": roadmap.slug,
        "view_count": roadmap.view_count,
        "last_viewed_at": roadmap.last_viewed_at.isoformat() if roadmap.last_viewed_at else None,
        "created_at": roadmap.created_at.isoformat() if roadmap.created_at else None,
        "is_active": roadmap.is_active
    }


# =============================================================================
# Aggregate Views
# =============================================================================

@router.get("/overview")
async def get_roadmap_overview(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a high-level overview of the roadmap."""
    from sqlalchemy import select

    # Count releases by status
    releases_query = select(PortalRelease)
    if project_id:
        releases_query = releases_query.where(PortalRelease.project_id == project_id)

    releases_result = await db.execute(releases_query)
    releases = releases_result.scalars().all()

    release_stats = {status: 0 for status in RELEASE_STATUSES}
    for release in releases:
        if release.status in release_stats:
            release_stats[release.status] += 1

    # Count items by status
    items_result = await db.execute(select(PortalRoadmapItem))
    items = items_result.scalars().all()

    item_stats = {status: 0 for status in ROADMAP_ITEM_STATUSES}
    unassigned = 0
    for item in items:
        if item.roadmap_status in item_stats:
            item_stats[item.roadmap_status] += 1
        if not item.release_id:
            unassigned += 1

    # Overdue releases
    overdue = [r for r in releases if r.is_overdue]

    return {
        "releases": {
            "total": len(releases),
            "by_status": release_stats,
            "overdue": len(overdue)
        },
        "items": {
            "total": len(items),
            "by_status": item_stats,
            "unassigned": unassigned
        },
        "upcoming_releases": [
            r.to_dict() for r in sorted(
                [r for r in releases if r.target_date and r.status in ["planned", "in_progress"]],
                key=lambda x: x.target_date
            )[:5]
        ]
    }


@router.get("/kanban")
async def get_roadmap_kanban(
    project_id: Optional[int] = None,
    release_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get roadmap data in kanban board format."""
    from sqlalchemy import select

    query = select(PortalRoadmapItem)

    if release_id:
        query = query.where(PortalRoadmapItem.release_id == release_id)

    query = query.order_by(PortalRoadmapItem.display_order)

    result = await db.execute(query)
    items = result.scalars().all()

    # Group by status (lanes)
    lanes = {status: [] for status in ROADMAP_ITEM_STATUSES}
    for item in items:
        status = item.roadmap_status or "backlog"
        if status in lanes:
            lanes[status].append(item.to_dict())

    return {
        "lanes": lanes,
        "lane_order": ROADMAP_ITEM_STATUSES,
        "total_items": len(items)
    }
