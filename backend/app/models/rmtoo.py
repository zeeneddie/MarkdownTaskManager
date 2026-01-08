# backend/app/models/rmtoo.py
"""
SQLAlchemy models for rmtoo Requirements Management - Week 117.

Tables:
- rmtoo_requirements: Individual requirements in rmtoo format
- rmtoo_topics: Topic hierarchy for organizing requirements
- rmtoo_sync_sessions: Track sync operations
- rmtoo_exports: Track export operations
- rmtoo_traceability_links: Links between MarQed and rmtoo
"""

from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID
import uuid

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, Date,
    ForeignKey, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class RequirementType(str, Enum):
    """rmtoo requirement types."""
    REQUIREMENT = "requirement"
    DECISION = "decision"
    CONSTRAINT = "constraint"


class RequirementStatus(str, Enum):
    """rmtoo requirement status."""
    NOT_DONE = "not done"
    DONE = "done"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequirementCategory(str, Enum):
    """MarQed requirement categories mapped to rmtoo."""
    BR = "BR"   # Business Rule
    FR = "FR"   # Functional Requirement
    NFR = "NFR"  # Non-Functional Requirement
    TR = "TR"   # Technical Requirement
    CMP = "CMP"  # Compliance Requirement


class SourceType(str, Enum):
    """How the requirement was created."""
    EXTRACTED = "extracted"  # Extracted from code
    MANUAL = "manual"       # Manually created
    IMPORTED = "imported"   # Imported from external source


class SyncDirection(str, Enum):
    """Sync operation direction."""
    DB_TO_FILES = "db_to_files"
    FILES_TO_DB = "files_to_db"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Sync session status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportType(str, Enum):
    """Export format types."""
    PDF = "pdf"
    HTML = "html"
    LATEX = "latex"
    GRAPH = "graph"
    XML = "xml"
    MARKDOWN = "markdown"


class LinkType(str, Enum):
    """Traceability link types."""
    IMPLEMENTS = "implements"     # Requirement implements epic/feature/story
    DERIVES_FROM = "derives_from"  # Requirement derives from code
    TESTS = "tests"              # Requirement is tested by
    CONFLICTS_WITH = "conflicts_with"


class RmtooRequirement(Base):
    """Individual requirement in rmtoo format."""
    __tablename__ = 'rmtoo_requirements'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # rmtoo core fields
    name = Column(String(100), nullable=False)  # REQ-BR-001, REQ-FR-002
    req_type = Column(String(50), nullable=False, default='requirement')
    description = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)

    # Metadata
    invented_on = Column(Date, nullable=True)
    invented_by = Column(String(100), nullable=True)
    owner = Column(String(100), nullable=True, default='development')

    # Status and priority
    status = Column(String(30), nullable=False, default='not done')
    priority = Column(String(50), nullable=True)
    effort_estimation = Column(Integer, nullable=True)

    # Organization
    topic = Column(String(100), nullable=True)
    topic_id = Column(PGUUID(as_uuid=True), ForeignKey('rmtoo_topics.id', ondelete='SET NULL'), nullable=True)

    # Dependencies
    solved_by = Column(JSONB, default=[])
    depends_on = Column(JSONB, default=[])

    # Category
    category = Column(String(30), nullable=False)

    # Source tracking
    source_type = Column(String(30), nullable=True)
    source_file = Column(String(500), nullable=True)
    source_line = Column(Integer, nullable=True)
    extraction_session_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Confidence and validation
    confidence = Column(Float, nullable=True)
    validated = Column(Boolean, default=False)
    validated_by = Column(String(100), nullable=True)
    validated_at = Column(DateTime, nullable=True)

    # rmtoo file content (cached)
    rmtoo_content = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    topic_rel = relationship("RmtooTopic", back_populates="requirements", foreign_keys=[topic_id])
    traceability_links = relationship("RmtooTraceabilityLink", back_populates="requirement", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_rmtoo_req_project_name'),
    )

    def to_rmtoo_format(self) -> str:
        """Generate rmtoo .req file content."""
        lines = [
            f"Name: {self.name}",
            f"Type: {self.req_type}",
        ]

        if self.invented_on:
            lines.append(f"Invented on: {self.invented_on.isoformat()}")
        if self.invented_by:
            lines.append(f"Invented by: {self.invented_by}")

        # Description with multi-line support
        desc_lines = self.description.split('\n')
        lines.append(f"Description: {desc_lines[0]}")
        for line in desc_lines[1:]:
            lines.append(f" {line}")

        if self.rationale:
            rat_lines = self.rationale.split('\n')
            lines.append(f"Rationale: {rat_lines[0]}")
            for line in rat_lines[1:]:
                lines.append(f" {line}")

        if self.owner:
            lines.append(f"Owner: {self.owner}")

        lines.append(f"Status: {self.status}")

        if self.priority:
            lines.append(f"Priority: {self.priority}")
        if self.effort_estimation:
            lines.append(f"Effort estimation: {self.effort_estimation}")
        if self.topic:
            lines.append(f"Topic: {self.topic}")

        if self.solved_by:
            lines.append(f"Solved by: {' '.join(self.solved_by)}")
        if self.depends_on:
            lines.append(f"Depends on: {' '.join(self.depends_on)}")

        # MarQed extension: category
        lines.append(f"# MarQed Category: {self.category}")

        return '\n'.join(lines)


class RmtooTopic(Base):
    """Topic hierarchy for organizing requirements."""
    __tablename__ = 'rmtoo_topics'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Topic info
    name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # Hierarchy
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey('rmtoo_topics.id', ondelete='SET NULL'), nullable=True)
    level = Column(Integer, default=0)
    order_index = Column(Integer, default=0)

    # Content
    content = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    parent = relationship("RmtooTopic", remote_side=[id], back_populates="children")
    children = relationship("RmtooTopic", back_populates="parent")
    requirements = relationship("RmtooRequirement", back_populates="topic_rel")

    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_rmtoo_topic_project_name'),
    )


class RmtooSyncSession(Base):
    """Track sync operations between MarQed and rmtoo files."""
    __tablename__ = 'rmtoo_sync_sessions'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Sync info
    direction = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='pending')

    # Statistics
    requirements_created = Column(Integer, default=0)
    requirements_updated = Column(Integer, default=0)
    requirements_deleted = Column(Integer, default=0)
    topics_synced = Column(Integer, default=0)
    conflicts_detected = Column(Integer, default=0)
    conflicts_resolved = Column(Integer, default=0)

    # File system
    output_path = Column(String(500), nullable=True)
    files_written = Column(JSONB, default=[])

    # Git integration
    git_commit_hash = Column(String(40), nullable=True)
    git_auto_commit = Column(Boolean, default=False)

    # Error handling
    errors = Column(JSONB, default=[])
    warnings = Column(JSONB, default=[])

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class RmtooExport(Base):
    """Track export operations."""
    __tablename__ = 'rmtoo_exports'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Export info
    export_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default='pending')

    # Output
    output_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Options
    include_topics = Column(JSONB, default=[])
    include_categories = Column(JSONB, default=[])
    graph_type = Column(String(30), nullable=True)

    # Generation
    requirements_included = Column(Integer, default=0)
    pages_generated = Column(Integer, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class RmtooTraceabilityLink(Base):
    """Links between MarQed entities and rmtoo requirements."""
    __tablename__ = 'rmtoo_traceability_links'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Requirement side
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('rmtoo_requirements.id', ondelete='CASCADE'), nullable=False)
    requirement_name = Column(String(100), nullable=False)

    # MarQed entity side
    entity_type = Column(String(30), nullable=False)  # epic, feature, story, task, business_rule
    entity_id = Column(String(100), nullable=False)
    entity_name = Column(String(200), nullable=True)

    # Link type
    link_type = Column(String(30), nullable=False)

    # Confidence and validation
    confidence = Column(Float, nullable=True)
    validated = Column(Boolean, default=False)
    validated_by = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    requirement = relationship("RmtooRequirement", back_populates="traceability_links")
