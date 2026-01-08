from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.schemas.feature import Feature, FeatureCreate, FeatureUpdate
from app.crud import item as crud
from app.models.item import ItemType
from app.utils.markdown import generate_feature_markdown

router = APIRouter(prefix="/features", tags=["features"])

@router.get("/", response_model=List[Feature])
async def list_features(
    epic_id: Optional[str] = Query(None, description="Filter by epic ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all features, optionally filtered by epic"""
    features = await crud.get_features(db, epic_id)
    return features

@router.get("/{feature_id}", response_model=Feature)
async def get_feature(feature_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific feature by ID"""
    feature = await crud.get_item_by_id(db, feature_id)
    if not feature or feature.type != ItemType.FEATURE:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature

@router.post("/", response_model=Feature, status_code=201)
async def create_feature(feature: FeatureCreate, db: AsyncSession = Depends(get_db)):
    """Create a new feature"""
    # Verify parent epic exists
    parent = await crud.get_item_by_id(db, feature.parent_id)
    if not parent or parent.type != ItemType.EPIC:
        raise HTTPException(status_code=404, detail="Parent epic not found")

    # Generate next feature ID
    feature_id = await crud.get_next_id(db, ItemType.FEATURE)

    # Generate markdown
    feature_dict = {"id": feature_id, **feature.model_dump()}
    markdown = generate_feature_markdown(feature_dict)

    # Create item
    item_data = {
        "id": feature_id,
        "type": ItemType.FEATURE,
        "markdown_full": markdown,
        **feature.model_dump()
    }
    new_feature = await crud.create_item(db, item_data)
    return new_feature

@router.put("/{feature_id}", response_model=Feature)
async def update_feature(
    feature_id: str,
    feature: FeatureUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing feature"""
    existing = await crud.get_item_by_id(db, feature_id)
    if not existing or existing.type != ItemType.FEATURE:
        raise HTTPException(status_code=404, detail="Feature not found")

    # If parent_id is being changed, verify new parent exists
    if feature.parent_id and feature.parent_id != existing.parent_id:
        parent = await crud.get_item_by_id(db, feature.parent_id)
        if not parent or parent.type != ItemType.EPIC:
            raise HTTPException(status_code=404, detail="Parent epic not found")

    update_data = feature.model_dump(exclude_unset=True)

    # Regenerate markdown
    feature_dict = {
        "id": feature_id,
        "title": existing.title,
        "parent_id": existing.parent_id,
        **update_data
    }
    markdown = generate_feature_markdown(feature_dict)
    update_data["markdown_full"] = markdown

    updated_feature = await crud.update_item(db, feature_id, update_data)
    return updated_feature

@router.delete("/{feature_id}", status_code=204)
async def delete_feature(feature_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a feature and all its descendants"""
    existing = await crud.get_item_by_id(db, feature_id)
    if not existing or existing.type != ItemType.FEATURE:
        raise HTTPException(status_code=404, detail="Feature not found")

    success = await crud.delete_item(db, feature_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete feature")

@router.get("/{feature_id}/hierarchy")
async def get_feature_hierarchy(feature_id: str, db: AsyncSession = Depends(get_db)):
    """Get feature with all its descendants"""
    feature = await crud.get_item_by_id(db, feature_id)
    if not feature or feature.type != ItemType.FEATURE:
        raise HTTPException(status_code=404, detail="Feature not found")

    hierarchy = await crud.get_item_hierarchy(db, feature_id)
    return hierarchy

@router.post("/{feature_id}/move")
async def move_feature(
    feature_id: str,
    new_epic_id: str = Query(..., description="New parent epic ID"),
    db: AsyncSession = Depends(get_db)
):
    """Move a feature to a different epic"""
    moved = await crud.move_item(db, feature_id, new_epic_id)
    if not moved:
        raise HTTPException(status_code=400, detail="Failed to move feature")
    return moved
