from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.schemas.task import Task, TaskCreate, TaskUpdate
from app.crud import item as crud
from app.models.item import ItemType
from app.utils.markdown import generate_task_markdown

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[Task])
async def list_tasks(
    story_id: Optional[str] = Query(None, description="Filter by story ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks, optionally filtered by story"""
    tasks = await crud.get_tasks(db, story_id)
    return tasks

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific task by ID"""
    task = await crud.get_item_by_id(db, task_id)
    if not task or task.type != ItemType.TASK:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/", response_model=Task, status_code=201)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Create a new task"""
    # Verify parent story exists
    parent = await crud.get_item_by_id(db, task.parent_id)
    if not parent or parent.type != ItemType.STORY:
        raise HTTPException(status_code=404, detail="Parent story not found")

    # Generate next task ID
    task_id = await crud.get_next_id(db, ItemType.TASK)

    # Generate markdown
    task_dict = {"id": task_id, **task.model_dump()}
    markdown = generate_task_markdown(task_dict)

    # Create item
    item_data = {
        "id": task_id,
        "type": ItemType.TASK,
        "markdown_full": markdown,
        **task.model_dump()
    }
    new_task = await crud.create_item(db, item_data)
    return new_task

@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing task"""
    existing = await crud.get_item_by_id(db, task_id)
    if not existing or existing.type != ItemType.TASK:
        raise HTTPException(status_code=404, detail="Task not found")

    # If parent_id is being changed, verify new parent exists
    if task.parent_id and task.parent_id != existing.parent_id:
        parent = await crud.get_item_by_id(db, task.parent_id)
        if not parent or parent.type != ItemType.STORY:
            raise HTTPException(status_code=404, detail="Parent story not found")

    update_data = task.model_dump(exclude_unset=True)

    # Regenerate markdown
    task_dict = {
        "id": task_id,
        "title": existing.title,
        "parent_id": existing.parent_id,
        **update_data
    }
    markdown = generate_task_markdown(task_dict)
    update_data["markdown_full"] = markdown

    updated_task = await crud.update_item(db, task_id, update_data)
    return updated_task

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a task"""
    existing = await crud.get_item_by_id(db, task_id)
    if not existing or existing.type != ItemType.TASK:
        raise HTTPException(status_code=404, detail="Task not found")

    success = await crud.delete_item(db, task_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.post("/{task_id}/move")
async def move_task(
    task_id: str,
    new_story_id: str = Query(..., description="New parent story ID"),
    db: AsyncSession = Depends(get_db)
):
    """Move a task to a different story"""
    moved = await crud.move_item(db, task_id, new_story_id)
    if not moved:
        raise HTTPException(status_code=400, detail="Failed to move task")
    return moved
