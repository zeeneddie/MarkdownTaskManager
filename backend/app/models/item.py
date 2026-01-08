from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ItemType(str, enum.Enum):
    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"


class Item(Base):
    __tablename__ = "items"

    id = Column(String(50), primary_key=True)
    type = Column(Enum(ItemType), nullable=False, index=True)
    parent_id = Column(String(50), ForeignKey("items.id", ondelete="CASCADE"), nullable=True, index=True)

    title = Column(Text, nullable=False)
    status = Column(String(30), index=True)
    priority = Column(String(20))
    lane = Column(String(30), index=True)  # Kanban lane (BACKLOG, ANALYSIS, etc.)
    owner = Column(String(100))
    assigned_to = Column(String(100))
    tags = Column(Text)  # Comma-separated tags

    sp = Column(Integer)  # Story points (alias: story_points)
    source_extraction_id = Column(String(50), index=True)  # Link to extraction session
    sp_total = Column(Integer, default=0)
    sp_completed = Column(Integer, default=0)
    hours = Column(Integer)
    sprint_id = Column(Integer, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True, index=True)
    sprint_order = Column(Integer)  # Order within sprint

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    started_at = Column(DateTime)
    target_date = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    description = Column(Text)
    markdown_full = Column(Text)
    item_metadata = Column(JSONB)

    # Relationships
    parent = relationship("Item", remote_side=[id], backref="children")
    sprint_rel = relationship("Sprint", backref="items", foreign_keys=[sprint_id])

    def __repr__(self):
        return f"<Item(id={self.id}, type='{self.type}', title='{self.title}')>"
