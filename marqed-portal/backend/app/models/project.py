"""
Project models for tenant projects and repositories.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Text,
    Integer,
    Float,
)
from sqlalchemy.orm import relationship
from enum import Enum

from ..core.database import Base
from .base import TimestampMixin, TenantMixin, generate_uuid

if TYPE_CHECKING:
    from .tenant import Tenant


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectType(str, Enum):
    """Type of project."""

    GREENFIELD = "greenfield"  # New development
    BROWNFIELD = "brownfield"  # Legacy modernization
    MIGRATION = "migration"  # System migration
    MAINTENANCE = "maintenance"  # Ongoing maintenance


class Project(Base, TimestampMixin, TenantMixin):
    """
    Project within a tenant.

    Represents a software project being managed through MarQed.
    """

    __tablename__ = "projects"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Basic info
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)  # Short code like "HCI", "FRM"
    description = Column(Text, nullable=True)

    # Status
    status = Column(
        SQLEnum(ProjectStatus),
        default=ProjectStatus.DRAFT,
        nullable=False,
    )
    project_type = Column(
        SQLEnum(ProjectType),
        default=ProjectType.BROWNFIELD,
        nullable=False,
    )

    # FP Budget
    total_fp_estimated = Column(Float, default=0.0, nullable=False)
    total_fp_consumed = Column(Float, default=0.0, nullable=False)
    current_sprint_fp = Column(Float, default=0.0, nullable=False)

    # Progress
    completion_percentage = Column(Float, default=0.0, nullable=False)
    stories_total = Column(Integer, default=0, nullable=False)
    stories_completed = Column(Integer, default=0, nullable=False)

    # Integration with main backend
    main_backend_session_id = Column(String(36), nullable=True)
    brown_paper_session_id = Column(String(36), nullable=True)
    analysis_contract_id = Column(String(36), nullable=True)

    # Dates
    started_at = Column(DateTime(timezone=True), nullable=True)
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    tech_stack = Column(JSON, default=list, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)

    # Relationships
    tenant: "Tenant" = relationship("Tenant", back_populates="projects")
    repositories: List["ProjectRepository"] = relationship(
        "ProjectRepository",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project {self.name} ({self.code})>"

    @property
    def fp_remaining(self) -> float:
        """Calculate remaining FP budget."""
        return max(0, self.total_fp_estimated - self.total_fp_consumed)

    @property
    def is_over_budget(self) -> bool:
        """Check if project is over FP budget."""
        return self.total_fp_consumed > self.total_fp_estimated

    def update_progress(self) -> None:
        """Recalculate progress percentage."""
        if self.stories_total > 0:
            self.completion_percentage = (
                self.stories_completed / self.stories_total * 100
            )
        else:
            self.completion_percentage = 0.0


class ProjectRepository(Base, TimestampMixin, TenantMixin):
    """
    Repository linked to a project.

    Tracks source code repositories for analysis.
    """

    __tablename__ = "project_repositories"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Foreign key to project
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository info
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=True)
    clone_path = Column(String(500), nullable=True)

    # Type
    repository_type = Column(String(50), default="git", nullable=False)
    default_branch = Column(String(100), default="main", nullable=False)

    # Analysis state
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    last_commit_hash = Column(String(40), nullable=True)
    total_files = Column(Integer, default=0, nullable=False)
    total_loc = Column(Integer, default=0, nullable=False)

    # Metadata
    languages = Column(JSON, default=dict, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)

    # Relationships
    project: "Project" = relationship("Project", back_populates="repositories")

    def __repr__(self) -> str:
        return f"<ProjectRepository {self.name}>"
