from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.epic import Epic, EpicCreate, EpicUpdate
from app.crud import item as crud
from app.models.item import ItemType
from app.utils.markdown import generate_epic_markdown

router = APIRouter(prefix="/epics", tags=["epics"])


@router.get("/", response_model=List[Epic])
async def list_epics(db: AsyncSession = Depends(get_db)):
    """Get all epics"""
    epics = await crud.get_epics(db)
    return epics


@router.get("/{epic_id}", response_model=Epic)
async def get_epic(epic_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific epic by ID"""
    epic = await crud.get_item_by_id(db, epic_id)
    if not epic or epic.type != ItemType.EPIC:
        raise HTTPException(status_code=404, detail="Epic not found")
    return epic


@router.post("/", response_model=Epic, status_code=201)
async def create_epic(epic: EpicCreate, db: AsyncSession = Depends(get_db)):
    """Create a new epic"""
    # Generate next epic ID
    epic_id = await crud.get_next_id(db, ItemType.EPIC)

    # Generate markdown
    epic_dict = {"id": epic_id, **epic.model_dump()}
    markdown = generate_epic_markdown(epic_dict)

    # Create item
    item_data = {
        "id": epic_id,
        "type": ItemType.EPIC,
        "markdown_full": markdown,
        **epic.model_dump()
    }
    new_epic = await crud.create_item(db, item_data)
    return new_epic


@router.put("/{epic_id}", response_model=Epic)
async def update_epic(
    epic_id: str,
    epic: EpicUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing epic"""
    existing = await crud.get_item_by_id(db, epic_id)
    if not existing or existing.type != ItemType.EPIC:
        raise HTTPException(status_code=404, detail="Epic not found")

    update_data = epic.model_dump(exclude_unset=True)

    # Regenerate markdown
    epic_dict = {
        "id": epic_id,
        "title": existing.title,
        **update_data
    }
    markdown = generate_epic_markdown(epic_dict)
    update_data["markdown_full"] = markdown

    updated_epic = await crud.update_item(db, epic_id, update_data)
    return updated_epic


@router.delete("/{epic_id}", status_code=204)
async def delete_epic(epic_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an epic and all its descendants"""
    existing = await crud.get_item_by_id(db, epic_id)
    if not existing or existing.type != ItemType.EPIC:
        raise HTTPException(status_code=404, detail="Epic not found")

    success = await crud.delete_item(db, epic_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete epic")


@router.get("/{epic_id}/hierarchy")
async def get_epic_hierarchy(epic_id: str, db: AsyncSession = Depends(get_db)):
    """Get epic with all its descendants"""
    epic = await crud.get_item_by_id(db, epic_id)
    if not epic or epic.type != ItemType.EPIC:
        raise HTTPException(status_code=404, detail="Epic not found")

    hierarchy = await crud.get_item_hierarchy(db, epic_id)
    return hierarchy
