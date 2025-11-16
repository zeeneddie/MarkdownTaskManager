from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.sprint import Sprint
from app.models.item import Item, ItemType
from typing import List, Optional
from datetime import datetime

async def get_sprint_by_id(db: AsyncSession, sprint_id: int) -> Optional[Sprint]:
    """Get sprint by ID"""
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    return result.scalar_one_or_none()

async def get_sprint_by_name(db: AsyncSession, name: str) -> Optional[Sprint]:
    """Get sprint by name"""
    result = await db.execute(
        select(Sprint).where(Sprint.name == name)
    )
    return result.scalar_one_or_none()

async def get_all_sprints(db: AsyncSession, status: Optional[str] = None) -> List[Sprint]:
    """Get all sprints, optionally filtered by status"""
    query = select(Sprint)
    if status:
        query = query.where(Sprint.status == status)
    query = query.order_by(Sprint.start_date.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_active_sprint(db: AsyncSession) -> Optional[Sprint]:
    """Get the currently active sprint"""
    result = await db.execute(
        select(Sprint).where(Sprint.status == "ACTIVE").order_by(Sprint.start_date.desc())
    )
    return result.scalar_one_or_none()

async def create_sprint(db: AsyncSession, sprint_data: dict) -> Sprint:
    """Create a new sprint"""
    sprint = Sprint(**sprint_data)
    db.add(sprint)
    await db.commit()
    await db.refresh(sprint)
    return sprint

async def update_sprint(db: AsyncSession, sprint_id: int, update_data: dict) -> Optional[Sprint]:
    """Update an existing sprint"""
    sprint = await get_sprint_by_id(db, sprint_id)
    if not sprint:
        return None

    for key, value in update_data.items():
        setattr(sprint, key, value)

    sprint.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(sprint)

    # Recalculate story points
    await calculate_sprint_points(db, sprint.name)

    return sprint

async def delete_sprint(db: AsyncSession, sprint_id: int) -> bool:
    """Delete a sprint (unassign stories first)"""
    sprint = await get_sprint_by_id(db, sprint_id)
    if not sprint:
        return False

    # Unassign all stories from this sprint
    result = await db.execute(
        select(Item).where(
            and_(Item.type == ItemType.STORY, Item.sprint == sprint.name)
        )
    )
    stories = result.scalars().all()

    for story in stories:
        story.sprint = None
        story.updated_at = datetime.utcnow()

    await db.delete(sprint)
    await db.commit()
    return True

async def calculate_sprint_points(db: AsyncSession, sprint_name: str):
    """Calculate total and completed story points for a sprint"""
    # Get sprint
    sprint = await get_sprint_by_name(db, sprint_name)
    if not sprint:
        return

    # Get all stories in this sprint
    result = await db.execute(
        select(Item).where(
            and_(Item.type == ItemType.STORY, Item.sprint == sprint_name)
        )
    )
    stories = result.scalars().all()

    total_sp = sum(story.sp or 0 for story in stories)
    completed_sp = sum(
        story.sp or 0
        for story in stories
        if story.status == "COMPLETED"
    )

    sprint.total_sp = total_sp
    sprint.completed_sp = completed_sp
    sprint.updated_at = datetime.utcnow()

    await db.commit()

async def get_sprint_stories(db: AsyncSession, sprint_name: str) -> List[Item]:
    """Get all stories in a sprint"""
    result = await db.execute(
        select(Item).where(
            and_(Item.type == ItemType.STORY, Item.sprint == sprint_name)
        ).order_by(Item.id)
    )
    return result.scalars().all()

async def assign_story_to_sprint(db: AsyncSession, story_id: str, sprint_name: str) -> Optional[Item]:
    """Assign a story to a sprint"""
    # Verify sprint exists
    sprint = await get_sprint_by_name(db, sprint_name)
    if not sprint:
        return None

    # Get story
    result = await db.execute(
        select(Item).where(and_(Item.id == story_id, Item.type == ItemType.STORY))
    )
    story = result.scalar_one_or_none()
    if not story:
        return None

    old_sprint = story.sprint
    story.sprint = sprint_name
    story.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(story)

    # Recalculate points for both sprints
    await calculate_sprint_points(db, sprint_name)
    if old_sprint:
        await calculate_sprint_points(db, old_sprint)

    return story

async def unassign_story_from_sprint(db: AsyncSession, story_id: str) -> Optional[Item]:
    """Remove a story from its sprint"""
    result = await db.execute(
        select(Item).where(and_(Item.id == story_id, Item.type == ItemType.STORY))
    )
    story = result.scalar_one_or_none()
    if not story or not story.sprint:
        return None

    old_sprint = story.sprint
    story.sprint = None
    story.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(story)

    # Recalculate points for old sprint
    await calculate_sprint_points(db, old_sprint)

    return story

async def get_sprint_velocity(db: AsyncSession, sprint_id: int) -> dict:
    """Calculate sprint velocity and metrics"""
    sprint = await get_sprint_by_id(db, sprint_id)
    if not sprint:
        return None

    stories = await get_sprint_stories(db, sprint.name)

    total_stories = len(stories)
    completed_stories = len([s for s in stories if s.status == "COMPLETED"])
    in_progress_stories = len([s for s in stories if s.status == "IN_PROGRESS"])

    # Calculate days elapsed and remaining
    now = datetime.utcnow()
    total_days = (sprint.end_date - sprint.start_date).days
    days_elapsed = max(0, (now - sprint.start_date).days)
    days_remaining = max(0, (sprint.end_date - now).days)

    # Calculate velocity (completed SP per day)
    velocity = sprint.completed_sp / days_elapsed if days_elapsed > 0 else 0

    # Predict completion
    remaining_sp = sprint.total_sp - sprint.completed_sp
    predicted_days = remaining_sp / velocity if velocity > 0 else float('inf')

    return {
        "sprint_id": sprint.id,
        "sprint_name": sprint.name,
        "status": sprint.status,
        "total_sp": sprint.total_sp,
        "completed_sp": sprint.completed_sp,
        "remaining_sp": remaining_sp,
        "total_stories": total_stories,
        "completed_stories": completed_stories,
        "in_progress_stories": in_progress_stories,
        "total_days": total_days,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "velocity": round(velocity, 2),
        "predicted_days_to_completion": round(predicted_days, 1) if predicted_days != float('inf') else None,
        "on_track": predicted_days <= days_remaining if predicted_days != float('inf') else None
    }
