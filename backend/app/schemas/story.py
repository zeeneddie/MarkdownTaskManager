from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class StoryBase(BaseModel):
    title: str
    parent_id: str  # Feature ID
    status: Optional[str] = "BACKLOG"
    priority: Optional[str] = None
    owner: Optional[str] = None
    assigned_to: Optional[str] = None
    sp: Optional[int] = None
    sprint: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class StoryCreate(StoryBase):
    pass

class StoryUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    owner: Optional[str] = None
    assigned_to: Optional[str] = None
    sp: Optional[int] = None
    sprint: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class Story(StoryBase):
    id: str
    type: str = "story"
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    markdown_full: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
