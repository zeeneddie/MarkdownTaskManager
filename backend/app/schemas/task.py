from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TaskBase(BaseModel):
    title: str
    parent_id: str  # Story ID
    status: Optional[str] = "TODO"
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    hours: Optional[int] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    hours: Optional[int] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class Task(TaskBase):
    id: str
    type: str = "task"
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    markdown_full: Optional[str] = None

    class Config:
        from_attributes = True
