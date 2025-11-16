from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.schemas.story import Story, StoryCreate, StoryUpdate
from app.crud import item as crud
from app.crud import sprint as sprint_crud
from app.models.item import ItemType
from app.utils.markdown import generate_story_markdown

router = APIRouter(prefix="/stories", tags=["stories"])

@router.get("/", response_model=List[Story])
async def list_stories(
    feature_id: Optional[str] = Query(None, description="Filter by feature ID"),
    sprint: Optional[str] = Query(None, description="Filter by sprint name"),
    db: AsyncSession = Depends(get_db)
):
    """Get all stories, optionally filtered by feature or sprint"""
    stories = await crud.get_stories(db, feature_id, sprint)
    return stories

@router.get("/{story_id}", response_model=Story)
async def get_story(story_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific story by ID"""
    story = await crud.get_item_by_id(db, story_id)
    if not story or story.type != ItemType.STORY:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@router.post("/", response_model=Story, status_code=201)
async def create_story(story: StoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a new story"""
    # Verify parent feature exists
    parent = await crud.get_item_by_id(db, story.parent_id)
    if not parent or parent.type != ItemType.FEATURE:
        raise HTTPException(status_code=404, detail="Parent feature not found")

    # Verify sprint exists if specified
    if story.sprint:
        sprint_obj = await sprint_crud.get_sprint_by_name(db, story.sprint)
        if not sprint_obj:
            raise HTTPException(status_code=404, detail=f"Sprint '{story.sprint}' not found")

    # Generate next story ID
    story_id = await crud.get_next_id(db, ItemType.STORY)

    # Generate markdown
    story_dict = {"id": story_id, **story.model_dump()}
    markdown = generate_story_markdown(story_dict)

    # Create item
    item_data = {
        "id": story_id,
        "type": ItemType.STORY,
        "markdown_full": markdown,
        **story.model_dump()
    }
    new_story = await crud.create_item(db, item_data)

    # Update sprint points if assigned to sprint
    if story.sprint:
        await sprint_crud.calculate_sprint_points(db, story.sprint)

    return new_story

@router.put("/{story_id}", response_model=Story)
async def update_story(
    story_id: str,
    story: StoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing story"""
    existing = await crud.get_item_by_id(db, story_id)
    if not existing or existing.type != ItemType.STORY:
        raise HTTPException(status_code=404, detail="Story not found")

    # If parent_id is being changed, verify new parent exists
    if story.parent_id and story.parent_id != existing.parent_id:
        parent = await crud.get_item_by_id(db, story.parent_id)
        if not parent or parent.type != ItemType.FEATURE:
            raise HTTPException(status_code=404, detail="Parent feature not found")

    # If sprint is being changed, verify it exists
    if story.sprint and story.sprint != existing.sprint:
        sprint_obj = await sprint_crud.get_sprint_by_name(db, story.sprint)
        if not sprint_obj:
            raise HTTPException(status_code=404, detail=f"Sprint '{story.sprint}' not found")

    old_sprint = existing.sprint
    update_data = story.model_dump(exclude_unset=True)

    # Regenerate markdown
    story_dict = {
        "id": story_id,
        "title": existing.title,
        "parent_id": existing.parent_id,
        **update_data
    }
    markdown = generate_story_markdown(story_dict)
    update_data["markdown_full"] = markdown

    updated_story = await crud.update_item(db, story_id, update_data)

    # Update sprint points for both old and new sprints
    if old_sprint:
        await sprint_crud.calculate_sprint_points(db, old_sprint)
    if updated_story.sprint and updated_story.sprint != old_sprint:
        await sprint_crud.calculate_sprint_points(db, updated_story.sprint)

    return updated_story

@router.delete("/{story_id}", status_code=204)
async def delete_story(story_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a story and all its tasks"""
    existing = await crud.get_item_by_id(db, story_id)
    if not existing or existing.type != ItemType.STORY:
        raise HTTPException(status_code=404, detail="Story not found")

    sprint = existing.sprint
    success = await crud.delete_item(db, story_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete story")

    # Update sprint points if story was in a sprint
    if sprint:
        await sprint_crud.calculate_sprint_points(db, sprint)

@router.get("/{story_id}/hierarchy")
async def get_story_hierarchy(story_id: str, db: AsyncSession = Depends(get_db)):
    """Get story with all its tasks"""
    story = await crud.get_item_by_id(db, story_id)
    if not story or story.type != ItemType.STORY:
        raise HTTPException(status_code=404, detail="Story not found")

    hierarchy = await crud.get_item_hierarchy(db, story_id)
    return hierarchy

@router.post("/{story_id}/move")
async def move_story(
    story_id: str,
    new_feature_id: str = Query(..., description="New parent feature ID"),
    db: AsyncSession = Depends(get_db)
):
    """Move a story to a different feature"""
    moved = await crud.move_item(db, story_id, new_feature_id)
    if not moved:
        raise HTTPException(status_code=400, detail="Failed to move story")
    return moved

@router.post("/{story_id}/assign-sprint")
async def assign_to_sprint(
    story_id: str,
    sprint_name: str = Query(..., description="Sprint name"),
    db: AsyncSession = Depends(get_db)
):
    """Assign a story to a sprint"""
    story = await sprint_crud.assign_story_to_sprint(db, story_id, sprint_name)
    if not story:
        raise HTTPException(status_code=404, detail="Story or sprint not found")
    return story

@router.post("/{story_id}/unassign-sprint")
async def unassign_from_sprint(story_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a story from its sprint"""
    story = await sprint_crud.unassign_story_from_sprint(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found or not assigned to a sprint")
    return story
