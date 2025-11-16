from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FeatureBase(BaseModel):
    title: str
    parent_id: str  # Epic ID
    status: Optional[str] = "PLANNED"
    priority: Optional[str] = None
    owner: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class FeatureCreate(FeatureBase):
    pass

class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    owner: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class Feature(FeatureBase):
    id: str
    type: str = "feature"
    sp_total: int = 0
    sp_completed: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    markdown_full: Optional[str] = None

    class Config:
        from_attributes = True
