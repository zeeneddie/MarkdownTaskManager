from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.schemas.sprint import Sprint, SprintCreate, SprintUpdate, SprintWithStories
from app.crud import sprint as crud

router = APIRouter(prefix="/sprints", tags=["sprints"])

@router.get("/", response_model=List[Sprint])
async def list_sprints(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """Get all sprints, optionally filtered by status"""
    sprints = await crud.get_all_sprints(db, status)
    return sprints

@router.get("/active", response_model=Sprint)
async def get_active_sprint(db: AsyncSession = Depends(get_db)):
    """Get the currently active sprint"""
    sprint = await crud.get_active_sprint(db)
    if not sprint:
        raise HTTPException(status_code=404, detail="No active sprint found")
    return sprint

@router.get("/backlog/items")
async def get_backlog_items(db: AsyncSession = Depends(get_db)):
    """Get all items not assigned to any sprint (backlog)"""
    from app.crud import item as item_crud
    items = await item_crud.get_unassigned_items(db)
    return items

@router.get("/{sprint_id}", response_model=Sprint)
async def get_sprint(sprint_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific sprint by ID"""
    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint

@router.get("/{sprint_id}/with-stories", response_model=SprintWithStories)
async def get_sprint_with_stories(sprint_id: int, db: AsyncSession = Depends(get_db)):
    """Get a sprint with all its stories"""
    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    stories = await crud.get_sprint_stories(db, sprint.name)

    # Convert SQLAlchemy models to dicts for Pydantic serialization
    stories_data = []
    for story in stories:
        story_dict = {
            "id": story.id,
            "title": story.title,
            "type": story.type.value if hasattr(story.type, 'value') else str(story.type),
            "status": story.status,
            "priority": story.priority,
            "sp": story.sp,
            "sprint_id": story.sprint_id,
            "description": story.description,
            "created_at": story.created_at,
            "updated_at": story.updated_at,
        }
        stories_data.append(story_dict)

    return {
        **sprint.__dict__,
        "stories": stories_data
    }

@router.post("/", response_model=Sprint, status_code=201)
async def create_sprint(sprint: SprintCreate, db: AsyncSession = Depends(get_db)):
    """Create a new sprint"""
    # Check if sprint name already exists
    existing = await crud.get_sprint_by_name(db, sprint.name)
    if existing:
        raise HTTPException(status_code=400, detail="Sprint with this name already exists")

    # Validate dates
    if sprint.start_date >= sprint.end_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    new_sprint = await crud.create_sprint(db, sprint.model_dump())
    return new_sprint

@router.put("/{sprint_id}", response_model=Sprint)
async def update_sprint(
    sprint_id: int,
    sprint: SprintUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing sprint"""
    existing = await crud.get_sprint_by_id(db, sprint_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # If name is being changed, check uniqueness
    if sprint.name and sprint.name != existing.name:
        name_exists = await crud.get_sprint_by_name(db, sprint.name)
        if name_exists:
            raise HTTPException(status_code=400, detail="Sprint with this name already exists")

    # Validate dates if both are provided
    start = sprint.start_date if sprint.start_date else existing.start_date
    end = sprint.end_date if sprint.end_date else existing.end_date
    if start >= end:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    update_data = sprint.model_dump(exclude_unset=True)
    updated_sprint = await crud.update_sprint(db, sprint_id, update_data)
    return updated_sprint

@router.delete("/{sprint_id}", status_code=204)
async def delete_sprint(sprint_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a sprint (stories will be unassigned)"""
    existing = await crud.get_sprint_by_id(db, sprint_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sprint not found")

    success = await crud.delete_sprint(db, sprint_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete sprint")

@router.get("/{sprint_id}/velocity")
async def get_sprint_velocity(sprint_id: int, db: AsyncSession = Depends(get_db)):
    """Get sprint velocity and metrics"""
    velocity = await crud.get_sprint_velocity(db, sprint_id)
    if not velocity:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return velocity

@router.post("/{sprint_id}/start")
async def start_sprint(sprint_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a sprint as active"""
    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if sprint.status != "PLANNED":
        raise HTTPException(status_code=400, detail="Only planned sprints can be started")

    updated = await crud.update_sprint(db, sprint_id, {"status": "ACTIVE"})
    return updated

@router.post("/{sprint_id}/complete")
async def complete_sprint(sprint_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a sprint as completed"""
    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if sprint.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Only active sprints can be completed")

    updated = await crud.update_sprint(db, sprint_id, {"status": "COMPLETED"})
    return updated

# Sprint Planning Endpoints

@router.get("/{sprint_id}/items")
async def get_sprint_items(sprint_id: int, db: AsyncSession = Depends(get_db)):
    """Get all items assigned to a sprint"""
    from app.crud import item as item_crud

    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    items = await item_crud.get_items_by_sprint(db, sprint_id)
    return items

@router.post("/{sprint_id}/assign")
async def assign_item_to_sprint(
    sprint_id: int,
    item_id: str,
    order: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Assign an item to a sprint"""
    from app.crud import item as item_crud

    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    item = await item_crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check capacity
    item_sp = item.sp or 0
    if sprint.total_sp + item_sp > sprint.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Sprint capacity exceeded. Available: {sprint.capacity - sprint.total_sp} SP, Required: {item_sp} SP"
        )

    # Assign item
    updated_item = await item_crud.assign_to_sprint(db, item_id, sprint_id, order)

    # Update sprint total_sp
    await crud.update_sprint(db, sprint_id, {"total_sp": sprint.total_sp + item_sp})

    return updated_item

@router.post("/{sprint_id}/unassign")
async def unassign_item_from_sprint(
    sprint_id: int,
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove an item from a sprint"""
    from app.crud import item as item_crud

    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    item = await item_crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item_sp = item.sp or 0

    # Unassign item
    updated_item = await item_crud.unassign_from_sprint(db, item_id)

    # Update sprint total_sp
    new_total = max(0, sprint.total_sp - item_sp)
    await crud.update_sprint(db, sprint_id, {"total_sp": new_total})

    return updated_item


# =============================================================================
# ENHANCED BACKLOG ENDPOINTS (KaibanJS-Style Sprint Planning)
# =============================================================================

@router.get("/backlog/needs-estimation")
async def get_items_needing_estimation(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get items that need estimation (story_points IS NULL).

    These items are in BACKLOG or ANALYSIS lane and need agent estimation.
    """
    from app.crud import item as item_crud
    from sqlalchemy import select, or_
    from app.models.item import Item, ItemType
    from app.models.task_hierarchy import Story, StoryStatus

    # Get stories without story_points
    query = select(Story).where(
        Story.story_points.is_(None),
        Story.sprint_id.is_(None),
        Story.status.in_([StoryStatus.DRAFT, "todo", "analysis"])
    )

    if project_id:
        query = query.where(Story.project_id == project_id)

    query = query.order_by(Story.priority.desc().nullsfirst(), Story.created_at)

    result = await db.execute(query)
    stories = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "title": s.title,
            "description": s.description,
            "type": "story",
            "priority": s.priority,
            "status": s.status.value if hasattr(s.status, 'value') else s.status,
            "story_points": None,
            "feature_id": str(s.feature_id) if s.feature_id else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "needs_estimation": True
        }
        for s in stories
    ]


@router.get("/backlog/ready-for-sprint")
async def get_items_ready_for_sprint(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get items that are estimated and ready for sprint assignment.

    These items have story_points > 0 but no sprint_id assigned.
    They are in PLANNED lane, ready for sprint selection.
    """
    from app.models.task_hierarchy import Story, StoryStatus
    from sqlalchemy import select

    # Get all stories with story_points that are not in a sprint
    # (regardless of status - they're estimated and available)
    query = select(Story).where(
        Story.story_points.isnot(None),
        Story.story_points > 0,
        Story.sprint_id.is_(None)
    )

    if project_id:
        query = query.where(Story.project_id == project_id)

    query = query.order_by(Story.priority.desc().nullsfirst(), Story.story_points.desc())

    result = await db.execute(query)
    stories = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "title": s.title,
            "description": s.description,
            "type": "story",
            "priority": s.priority,
            "status": s.status.value if hasattr(s.status, 'value') else s.status,
            "story_points": s.story_points,
            "estimated_hours": s.estimated_hours,
            "feature_id": str(s.feature_id) if s.feature_id else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "ready_for_sprint": True
        }
        for s in stories
    ]


@router.get("/backlog/summary")
async def get_backlog_summary(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics for backlog planning.
    """
    from app.models.task_hierarchy import Story
    from sqlalchemy import select, func

    # Count needs estimation
    needs_est_query = select(func.count(Story.id)).where(
        Story.story_points.is_(None),
        Story.sprint_id.is_(None)
    )
    if project_id:
        needs_est_query = needs_est_query.where(Story.project_id == project_id)

    result = await db.execute(needs_est_query)
    needs_estimation_count = result.scalar() or 0

    # Count ready for sprint
    ready_query = select(func.count(Story.id), func.sum(Story.story_points)).where(
        Story.story_points.isnot(None),
        Story.story_points > 0,
        Story.sprint_id.is_(None)
    )
    if project_id:
        ready_query = ready_query.where(Story.project_id == project_id)

    result = await db.execute(ready_query)
    row = result.first()
    ready_count = row[0] or 0
    ready_total_sp = row[1] or 0

    # Get sprint capacity
    sprint_query = select(func.sum(crud.Sprint.capacity), func.sum(crud.Sprint.total_sp)).where(
        crud.Sprint.status.in_(["PLANNED", "ACTIVE"])
    )
    result = await db.execute(sprint_query)
    row = result.first()
    total_capacity = row[0] or 0
    used_capacity = row[1] or 0

    return {
        "needs_estimation": {
            "count": needs_estimation_count,
            "label": "Items need estimation"
        },
        "ready_for_sprint": {
            "count": ready_count,
            "total_story_points": ready_total_sp,
            "label": "Items ready for sprint"
        },
        "sprint_capacity": {
            "total": total_capacity,
            "used": used_capacity,
            "available": total_capacity - used_capacity,
            "utilization_percent": round((used_capacity / total_capacity * 100), 1) if total_capacity > 0 else 0
        }
    }


@router.post("/backlog/{item_id}/request-estimation")
async def request_item_estimation(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Request estimation for an item by triggering the Eliza agent.

    This moves the item to ANALYSIS lane and triggers the estimation workflow.
    """
    from app.models.task_hierarchy import Story, StoryStatus
    from app.services.kanban_agent_service import KanbanAgentService
    from sqlalchemy import select

    # Get story
    result = await db.execute(select(Story).where(Story.id == item_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if story.story_points is not None:
        raise HTTPException(status_code=400, detail="Story is already estimated")

    # Update status to analysis
    story.status = StoryStatus.TODO  # Will be moved to analysis by kanban
    await db.commit()

    # Trigger Eliza agent for estimation via Kanban
    try:
        kanban_service = KanbanAgentService(db)
        trigger_result = await kanban_service.trigger_agent_for_item(
            item_id=item_id,
            item_type="story",
            lane="analysis",
            agent_name="Eliza"
        )

        return {
            "success": True,
            "message": f"Estimation requested for story {item_id}",
            "agent_triggered": "Eliza",
            "lane": "analysis",
            "trigger_result": trigger_result
        }
    except Exception as e:
        # Even if agent trigger fails, the status update succeeded
        return {
            "success": True,
            "message": f"Story moved to analysis. Agent trigger: {str(e)}",
            "agent_triggered": None,
            "lane": "analysis"
        }


@router.post("/backlog/bulk-request-estimation")
async def bulk_request_estimation(
    item_ids: List[str],
    db: AsyncSession = Depends(get_db)
):
    """
    Request estimation for multiple items at once.
    """
    results = []
    for item_id in item_ids:
        try:
            result = await request_item_estimation(item_id, db)
            results.append({"id": item_id, "success": True, **result})
        except HTTPException as e:
            results.append({"id": item_id, "success": False, "error": e.detail})
        except Exception as e:
            results.append({"id": item_id, "success": False, "error": str(e)})

    return {
        "total": len(item_ids),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }


@router.post("/{sprint_id}/assign-story")
async def assign_story_to_sprint(
    sprint_id: int,
    story_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a story to a sprint.

    This endpoint is for assigning Story entities (from task_stories table)
    to sprints, as opposed to the /assign endpoint which is for Item entities.
    """
    from app.models.task_hierarchy import Story
    from sqlalchemy import select

    # Get sprint
    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Get story
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check capacity
    story_sp = story.story_points or 0
    if sprint.total_sp + story_sp > sprint.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Sprint capacity exceeded. Available: {sprint.capacity - sprint.total_sp} SP, Required: {story_sp} SP"
        )

    # Assign story to sprint
    story.sprint_id = str(sprint_id)

    # Update sprint total_sp directly (avoid calculate_sprint_points bug)
    sprint.total_sp = sprint.total_sp + story_sp
    await db.commit()

    return {
        "id": str(story.id),
        "title": story.title,
        "story_points": story.story_points,
        "sprint_id": story.sprint_id,
        "assigned": True
    }


@router.post("/{sprint_id}/unassign-story")
async def unassign_story_from_sprint(
    sprint_id: int,
    story_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a story from a sprint."""
    from app.models.task_hierarchy import Story
    from sqlalchemy import select

    sprint = await crud.get_sprint_by_id(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    story_sp = story.story_points or 0

    # Unassign story
    story.sprint_id = None

    # Update sprint total_sp directly
    sprint.total_sp = max(0, sprint.total_sp - story_sp)
    await db.commit()

    return {
        "id": str(story.id),
        "title": story.title,
        "unassigned": True
    }
