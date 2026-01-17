"""
Project Model

Matches the existing database schema for projects table.
Used for BMAD workflow project definitions.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Customer relationship (Week 143 - Fase 28)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)

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

    # Deep Extraction (Week 81-87)
    extraction_tier = Column(String(20), nullable=True, default='FREE')  # FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM

    # Progress tracking
    total_story_points = Column(Integer)
    completed_story_points = Column(Integer)
    estimated_days = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
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

    # Customer relationship (Week 143 - Fase 28)
    customer = relationship("Customer", back_populates="projects")

    # CCPM Relationships (Week 79)
    worktrees = relationship("GitWorktree", back_populates="project", cascade="all, delete-orphan")
    github_issues = relationship("GitHubIssueSync", back_populates="project", cascade="all, delete-orphan")
    prd_decompositions = relationship("PRDDecomposition", back_populates="project", cascade="all, delete-orphan")
    task_recommendations = relationship("TaskRecommendation", back_populates="project", cascade="all, delete-orphan")

    # Code Analysis (Week 83)
    code_analyses = relationship("CodeAnalysisAggregation", back_populates="project", cascade="all, delete-orphan")

    # Hierarchical Story Extraction (Week 84)
    hierarchical_extractions = relationship("HierarchicalExtractionSession", back_populates="project", cascade="all, delete-orphan")

    # Static Analysis (Week 97-98 - Fase 15)
    static_analyses = relationship("StaticAnalysisResult", back_populates="project", cascade="all, delete-orphan")

    # Hybrid Business Rule Extraction (Week 111-114)
    hybrid_extraction_sessions = relationship("HybridExtractionSession", back_populates="project", cascade="all, delete-orphan")

    # Week 131 Research - Fix for SQLAlchemy relationship mismatch
    background_jobs = relationship("BackgroundJobModel", back_populates="project", cascade="all, delete-orphan")
    load_estimations = relationship("LoadEstimationModel", back_populates="project", cascade="all, delete-orphan")
    documentation_rules = relationship("DocumentationRuleModel", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', type='{self.project_type}', status='{self.project_status}')>"
