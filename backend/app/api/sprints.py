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

    return {
        **sprint.__dict__,
        "stories": stories
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
