from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.models.item import Item, ItemType
from typing import List, Optional
from datetime import datetime

# Generic CRUD operations

async def get_item_by_id(db: AsyncSession, item_id: str) -> Optional[Item]:
    """Get any item by ID"""
    result = await db.execute(
        select(Item).where(Item.id == item_id)
    )
    return result.scalar_one_or_none()

async def get_items_by_type(db: AsyncSession, item_type: ItemType, parent_id: Optional[str] = None) -> List[Item]:
    """Get all items of a specific type, optionally filtered by parent"""
    query = select(Item).where(Item.type == item_type)
    if parent_id is not None:
        query = query.where(Item.parent_id == parent_id)
    query = query.order_by(Item.id)
    result = await db.execute(query)
    return result.scalars().all()

async def get_children(db: AsyncSession, parent_id: str) -> List[Item]:
    """Get all direct children of an item"""
    result = await db.execute(
        select(Item).where(Item.parent_id == parent_id).order_by(Item.id)
    )
    return result.scalars().all()

async def get_item_hierarchy(db: AsyncSession, item_id: str) -> dict:
    """Get item with all its descendants in a hierarchical structure"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return None

    children = await get_children(db, item_id)
    item_dict = {
        "item": item,
        "children": []
    }

    for child in children:
        child_hierarchy = await get_item_hierarchy(db, child.id)
        item_dict["children"].append(child_hierarchy)

    return item_dict

async def create_item(db: AsyncSession, item_data: dict) -> Item:
    """Create a new item"""
    item = Item(**item_data)
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Trigger aggregation if item has story points
    if item.parent_id and item.type == ItemType.STORY and item.sp:
        await aggregate_story_points(db, item.parent_id)

    return item

async def update_item(db: AsyncSession, item_id: str, update_data: dict) -> Optional[Item]:
    """Update an existing item"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return None

    old_sp = item.sp
    old_status = item.status
    old_parent_id = item.parent_id

    for key, value in update_data.items():
        setattr(item, key, value)

    item.updated_at = datetime.utcnow()

    # Handle status changes
    if "status" in update_data and update_data["status"] != old_status:
        if update_data["status"] == "IN_PROGRESS" and not item.started_at:
            item.started_at = datetime.utcnow()
        elif update_data["status"] == "COMPLETED" and not item.completed_at:
            item.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(item)

    # Trigger aggregation if story points changed or parent changed
    if item.type == ItemType.STORY:
        if old_sp != item.sp or old_status != item.status:
            if item.parent_id:
                await aggregate_story_points(db, item.parent_id)
        if old_parent_id and old_parent_id != item.parent_id:
            # Re-aggregate old parent too
            await aggregate_story_points(db, old_parent_id)

    return item

async def delete_item(db: AsyncSession, item_id: str) -> bool:
    """Delete an item and all its descendants (soft delete in production)"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return False

    parent_id = item.parent_id
    item_type = item.type

    await db.delete(item)
    await db.commit()

    # Trigger aggregation if story was deleted
    if parent_id and item_type == ItemType.STORY:
        await aggregate_story_points(db, parent_id)

    return True

# Aggregation functions

async def aggregate_story_points(db: AsyncSession, parent_id: str):
    """Recursively aggregate story points from children up the hierarchy"""
    parent = await get_item_by_id(db, parent_id)
    if not parent:
        return

    # Get all descendant stories (not just direct children)
    stories = await get_descendant_stories(db, parent_id)

    total_sp = sum(story.sp or 0 for story in stories)
    completed_sp = sum(
        story.sp or 0
        for story in stories
        if story.status == "COMPLETED"
    )

    parent.sp_total = total_sp
    parent.sp_completed = completed_sp
    parent.updated_at = datetime.utcnow()

    await db.commit()

    # Recursively aggregate to grandparent
    if parent.parent_id:
        await aggregate_story_points(db, parent.parent_id)

async def get_descendant_stories(db: AsyncSession, parent_id: str) -> List[Item]:
    """Get all story descendants of an item (recursive)"""
    children = await get_children(db, parent_id)
    stories = []

    for child in children:
        if child.type == ItemType.STORY:
            stories.append(child)
        else:
            # Recursively get stories from this child
            child_stories = await get_descendant_stories(db, child.id)
            stories.extend(child_stories)

    return stories

# Type-specific helpers

async def get_epics(db: AsyncSession) -> List[Item]:
    """Get all epics"""
    return await get_items_by_type(db, ItemType.EPIC)

async def get_features(db: AsyncSession, epic_id: Optional[str] = None) -> List[Item]:
    """Get all features, optionally filtered by epic"""
    return await get_items_by_type(db, ItemType.FEATURE, epic_id)

async def get_stories(db: AsyncSession, feature_id: Optional[str] = None, sprint: Optional[str] = None) -> List[Item]:
    """Get all stories, optionally filtered by feature or sprint"""
    query = select(Item).where(Item.type == ItemType.STORY)

    if feature_id is not None:
        query = query.where(Item.parent_id == feature_id)

    if sprint is not None:
        if sprint == "no-sprint":
            query = query.where(Item.sprint.is_(None))
        else:
            query = query.where(Item.sprint == sprint)

    query = query.order_by(Item.id)
    result = await db.execute(query)
    return result.scalars().all()

async def get_tasks(db: AsyncSession, story_id: Optional[str] = None) -> List[Item]:
    """Get all tasks, optionally filtered by story"""
    return await get_items_by_type(db, ItemType.TASK, story_id)

async def get_next_id(db: AsyncSession, item_type: ItemType) -> str:
    """Generate next ID for an item type"""
    result = await db.execute(
        select(func.count(Item.id)).where(Item.type == item_type)
    )
    count = result.scalar()

    type_prefix = {
        ItemType.EPIC: "EPIC",
        ItemType.FEATURE: "FEAT",
        ItemType.STORY: "STORY",
        ItemType.TASK: "TASK"
    }

    return f"{type_prefix[item_type]}-{(count + 1):03d}"

# Move operations

async def move_item(db: AsyncSession, item_id: str, new_parent_id: str) -> Optional[Item]:
    """Move an item to a new parent"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return None

    old_parent_id = item.parent_id

    # Verify new parent exists and is valid type
    new_parent = await get_item_by_id(db, new_parent_id)
    if not new_parent:
        return None

    # Verify valid parent-child relationship
    valid_moves = {
        ItemType.TASK: ItemType.STORY,
        ItemType.STORY: ItemType.FEATURE,
        ItemType.FEATURE: ItemType.EPIC
    }

    if item.type not in valid_moves or new_parent.type != valid_moves[item.type]:
        return None

    item.parent_id = new_parent_id
    item.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)

    # Re-aggregate both old and new parents
    if item.type == ItemType.STORY and item.sp:
        if old_parent_id:
            await aggregate_story_points(db, old_parent_id)
        await aggregate_story_points(db, new_parent_id)

    return item

# Sprint assignment functions

async def get_items_by_sprint(db: AsyncSession, sprint_id: int) -> List[Item]:
    """Get all items assigned to a specific sprint"""
    result = await db.execute(
        select(Item)
        .where(Item.sprint_id == sprint_id)
        .order_by(Item.sprint_order.nullsfirst(), Item.id)
    )
    return result.scalars().all()

async def get_unassigned_items(db: AsyncSession) -> List[Item]:
    """Get all items not assigned to any sprint (backlog)"""
    result = await db.execute(
        select(Item)
        .where(Item.sprint_id.is_(None))
        .where(Item.type.in_([ItemType.STORY, ItemType.TASK]))
        .order_by(Item.priority.desc().nullsfirst(), Item.id)
    )
    return result.scalars().all()

async def assign_to_sprint(db: AsyncSession, item_id: str, sprint_id: int, order: Optional[int] = None) -> Optional[Item]:
    """Assign an item to a sprint"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return None

    item.sprint_id = sprint_id
    item.sprint_order = order
    item.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(item)
    return item

async def unassign_from_sprint(db: AsyncSession, item_id: str) -> Optional[Item]:
    """Remove an item from its sprint"""
    item = await get_item_by_id(db, item_id)
    if not item:
        return None

    item.sprint_id = None
    item.sprint_order = None
    item.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(item)
    return item

# Alias for backward compatibility
get_item = get_item_by_id
