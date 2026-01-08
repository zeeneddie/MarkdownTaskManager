from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class EpicBase(BaseModel):
    title: str
    status: Optional[str] = "PLANNED"
    priority: Optional[str] = None
    owner: Optional[str] = None
    phase: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None


class EpicCreate(EpicBase):
    pass


class EpicUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    owner: Optional[str] = None
    phase: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None


class Epic(EpicBase):
    id: str
    type: str = "epic"
    sp_total: int = 0
    sp_completed: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    markdown_full: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
