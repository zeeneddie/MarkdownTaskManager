from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SprintBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    goal: Optional[str] = None
    status: Optional[str] = "PLANNED"  # PLANNED, ACTIVE, COMPLETED
    capacity: Optional[int] = 50  # Max story points per sprint

class SprintCreate(SprintBase):
    pass

class SprintUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    capacity: Optional[int] = None

class Sprint(SprintBase):
    id: int
    created_at: datetime
    updated_at: datetime
    total_sp: Optional[int] = 0
    completed_sp: Optional[int] = 0

    class Config:
        from_attributes = True

class SprintWithStories(Sprint):
    stories: list = []

    class Config:
        from_attributes = True
