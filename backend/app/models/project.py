"""
Project Model

Matches the existing database schema for projects table.
Used for BMAD workflow project definitions.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)

    # Project classification
    project_type = Column(String(20), nullable=False)  # greenfield, brownfield
    project_status = Column(String(20), nullable=False, default="draft", index=True)  # draft, active, archived

    # BMAD/Quality references
    bmad_session_id = Column(String(100), index=True)
    quality_scan_id = Column(String(100), index=True)
    chroma_collection_id = Column(String(100))

    # Business context
    business_goals = Column(JSONB)
    constraints = Column(JSONB)
    stakeholders = Column(JSONB)

    # Technical context
    tech_stack = Column(ARRAY(String))
    architecture_pattern = Column(String(100))

    # Progress tracking
    total_story_points = Column(Integer)
    completed_story_points = Column(Integer)
    estimated_days = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime)
    archived_at = Column(DateTime)

    # Check constraints match existing DB
    __table_args__ = (
        CheckConstraint(
            "project_status IN ('draft', 'active', 'archived')",
            name="check_project_status"
        ),
        CheckConstraint(
            "project_type IN ('greenfield', 'brownfield')",
            name="check_project_type"
        ),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', type='{self.project_type}', status='{self.project_status}')>"
