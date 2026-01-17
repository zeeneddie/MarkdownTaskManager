from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    goal = Column(Text)
    status = Column(String(20), default="PLANNED", index=True)  # PLANNED, ACTIVE, COMPLETED

    total_sp = Column(Integer, default=0)
    completed_sp = Column(Integer, default=0)
    capacity = Column(Integer, default=50)  # Max story points per sprint

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Sprint(id={self.id}, name='{self.name}', status='{self.status}')>"
