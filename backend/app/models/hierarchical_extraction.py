"""
Hierarchical Story Extraction Models - Week 84

Database models for storing hierarchically extracted stories.

Tables:
- HierarchicalExtractionSession: Main extraction session
- ExtractedStoryItem: Individual extracted items (epics, features, stories, tasks)
- ExtractionHierarchyRelation: Parent-child relationships between items
"""

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Float, ForeignKey,
    Boolean, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from app.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class ExtractionLevel(str, Enum):
    """Hierarchical extraction levels."""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    SYSTEM = "system"


class StoryItemType(str, Enum):
    """Types of extracted items."""
    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"
    PRODUCT_AREA = "product_area"
    CROSS_CUTTING = "cross_cutting"


class StoryConfidenceLevel(str, Enum):
    """Confidence level categories."""
    HIGH = "high"       # >= 80%
    MEDIUM = "medium"   # 60-79%
    LOW = "low"         # < 60%


class ExtractionSessionStatus(str, Enum):
    """Session status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# MODELS
# =============================================================================

class HierarchicalExtractionSession(Base):
    """
    Tracks a hierarchical story extraction session.

    Stores metadata about the extraction run and links to
    the project and extracted items.
    """
    __tablename__ = "hierarchical_extraction_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # Configuration
    repository_path = Column(String(1024), nullable=False)
    tier = Column(String(50), default="FREE")
    primary_stack = Column(String(100), nullable=True)
    few_shot_template = Column(String(100), nullable=True)

    # Levels included
    include_function_level = Column(Boolean, default=True)
    include_class_level = Column(Boolean, default=True)
    include_module_level = Column(Boolean, default=True)
    include_system_level = Column(Boolean, default=True)

    # Status
    status = Column(
        SQLEnum(ExtractionSessionStatus),
        default=ExtractionSessionStatus.PENDING
    )

    # Metrics
    total_epics = Column(Integer, default=0)
    total_features = Column(Integer, default=0)
    total_stories = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    overall_confidence = Column(Float, default=0.0)

    # Cost and performance
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    duration_ms = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Errors
    errors = Column(JSONB, default=list)

    # Link to aggregation (Week 83)
    aggregation_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="hierarchical_extractions")
    items = relationship(
        "ExtractedStoryItem",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<HierarchicalExtractionSession {self.id} project={self.project_id}>"


class ExtractedStoryItem(Base):
    """
    Individual extracted item (epic, feature, story, task).

    Stores the content and metadata of an extracted item,
    with links to its parent and children.
    """
    __tablename__ = "extracted_story_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hierarchical_extraction_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Type and level
    item_type = Column(SQLEnum(StoryItemType), nullable=False)
    extraction_level = Column(SQLEnum(ExtractionLevel), nullable=False)

    # Content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(JSONB, default=list)  # List of strings

    # Source context
    source_file = Column(String(1024), nullable=True)
    source_symbol = Column(String(255), nullable=True)
    source_line_start = Column(Integer, nullable=True)
    source_line_end = Column(Integer, nullable=True)

    # Hierarchy
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extracted_story_items.id", ondelete="SET NULL"),
        nullable=True
    )

    # Confidence
    confidence = Column(Float, default=0.0)
    confidence_level = Column(
        SQLEnum(StoryConfidenceLevel),
        default=StoryConfidenceLevel.LOW
    )

    # Complexity
    complexity = Column(String(50), default="medium")  # low, medium, high, critical

    # Estimation
    story_points = Column(Integer, nullable=True)
    function_points = Column(Float, nullable=True)

    # Tags
    tags = Column(JSONB, default=list)

    # Extraction metadata
    extracted_by = Column(String(100), nullable=True)  # LLM provider
    extracted_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    # Raw LLM output for debugging
    raw_response = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.utcnow())

    # Relationships
    session = relationship("HierarchicalExtractionSession", back_populates="items")
    parent = relationship("ExtractedStoryItem", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<ExtractedStoryItem {self.item_type.value}: {self.title[:30]}>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "item_type": self.item_type.value,
            "extraction_level": self.extraction_level.value,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "source_file": self.source_file,
            "source_symbol": self.source_symbol,
            "source_lines": [self.source_line_start, self.source_line_end],
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "complexity": self.complexity,
            "story_points": self.story_points,
            "function_points": self.function_points,
            "tags": self.tags,
            "extracted_by": self.extracted_by,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
        }


class ExtractionHierarchyRelation(Base):
    """
    Explicit parent-child relationships between extracted items.

    Allows for many-to-many relationships (an item can belong to multiple parents)
    and tracks the relationship type.
    """
    __tablename__ = "extraction_hierarchy_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extracted_story_items.id", ondelete="CASCADE"),
        nullable=False
    )
    child_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extracted_story_items.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationship metadata
    relationship_type = Column(String(50), default="contains")  # contains, depends_on, relates_to
    confidence = Column(Float, default=1.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<ExtractionHierarchyRelation {self.parent_id} -> {self.child_id}>"


class ExtractionLevelMetrics(Base):
    """
    Metrics for each extraction level within a session.

    Stores aggregated statistics per level (function, class, module, system).
    """
    __tablename__ = "extraction_level_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hierarchical_extraction_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    level = Column(SQLEnum(ExtractionLevel), nullable=False)

    # Counts
    story_count = Column(Integer, default=0)
    feature_count = Column(Integer, default=0)
    epic_count = Column(Integer, default=0)
    task_count = Column(Integer, default=0)
    total_items = Column(Integer, default=0)

    # Quality
    avg_confidence = Column(Float, default=0.0)
    high_confidence_count = Column(Integer, default=0)
    medium_confidence_count = Column(Integer, default=0)
    low_confidence_count = Column(Integer, default=0)

    # Performance
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)

    # Errors
    error_count = Column(Integer, default=0)
    errors = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<ExtractionLevelMetrics {self.level.value} session={self.session_id}>"
