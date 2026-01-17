"""
Week 90: Portal Roadmap Models

SQLAlchemy models for:
- PortalAnalysisQueue: Backlog items pending agent analysis
- PortalRelease: Release/milestone planning
- PortalRoadmapItem: Feature-to-release mapping with ordering
- PortalPublicRoadmap: Shareable public roadmap configuration
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, Date,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# Analysis queue status enum values
ANALYSIS_STATUSES = ["pending", "analyzing", "completed", "failed"]

# Release status enum values
RELEASE_STATUSES = ["planned", "in_progress", "released", "cancelled"]

# Roadmap item status enum values
ROADMAP_ITEM_STATUSES = ["backlog", "planned", "in_progress", "completed", "cancelled"]


class PortalAnalysisQueue(Base):
    """
    Queue for backlog items pending agent analysis.

    Items must be analyzed by agents (Peter, Felix, etc.) before
    they can be added to the roadmap.
    """
    __tablename__ = "portal_analysis_queue"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id = Column(
        String(50),
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )

    # Queue metadata
    priority = Column(Integer, default=0)  # Higher = more urgent
    requested_by = Column(String(100), nullable=True)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Analysis status
    status = Column(String(30), default="pending")
    # pending, analyzing, completed, failed

    # Analysis results
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    analyzed_by = Column(String(100), nullable=True)  # Agent name (Peter, Felix, etc.)
    analysis_result = Column(JSONB, nullable=True)  # Agent output

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    backlog_item = relationship("Item", foreign_keys=[item_id])

    __table_args__ = (
        UniqueConstraint('item_id', name='uq_analysis_queue_item'),
    )

    def to_dict(self, include_item: bool = False) -> Dict[str, Any]:
        """Convert analysis queue entry to dictionary."""
        result = {
            "id": str(self.id),
            "item_id": self.item_id,
            "project_id": self.project_id,
            "priority": self.priority,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "status": self.status,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "analyzed_by": self.analyzed_by,
            "analysis_result": self.analysis_result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_ready_for_roadmap": self.status == "completed",
        }

        if include_item and self.backlog_item:
            result["item"] = {
                "id": self.backlog_item.id,
                "type": self.backlog_item.type.value if self.backlog_item.type else None,
                "title": self.backlog_item.title,
                "status": self.backlog_item.status,
                "priority": self.backlog_item.priority,
            }

        return result

    @property
    def is_completed(self) -> bool:
        """Check if analysis is completed."""
        return self.status == "completed"

    @property
    def is_ready_for_roadmap(self) -> bool:
        """Check if item can be added to roadmap."""
        return self.status == "completed"


class PortalRelease(Base):
    """
    A release or milestone for grouping features.

    Represents a version release (e.g., v1.0, v2.0) or
    time-based milestone (e.g., Q1 2025) for roadmap planning.
    """
    __tablename__ = "portal_releases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )

    # Release info
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color

    # Timeline
    target_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)

    # Status
    status = Column(String(30), default="planned")

    # Ordering
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    released_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    roadmap_items = relationship(
        "PortalRoadmapItem",
        back_populates="release",
        lazy="dynamic"
    )

    def to_dict(self, include_items: bool = False) -> Dict[str, Any]:
        """Convert release to dictionary."""
        result = {
            "id": str(self.id),
            "project_id": self.project_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "color": self.color,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "status": self.status,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
        }

        if include_items:
            result["items"] = [
                item.to_dict() for item in self.roadmap_items.order_by(
                    PortalRoadmapItem.display_order
                ).all()
            ]
            result["item_count"] = self.roadmap_items.count()

        return result

    @property
    def is_overdue(self) -> bool:
        """Check if release is overdue."""
        if self.status == "released" or not self.target_date:
            return False
        return date.today() > self.target_date

    @property
    def days_until_target(self) -> Optional[int]:
        """Get days until target date."""
        if not self.target_date:
            return None
        return (self.target_date - date.today()).days


class PortalRoadmapItem(Base):
    """
    Maps a backlog item or feature request to a release with positioning.

    Provides drag-drop ordering, progress tracking, and
    dependency management for roadmap visualization.

    Supports both:
    - Backlog items (epic, feature, story, task) via item_id
    - Portal feature requests via feature_request_id
    """
    __tablename__ = "portal_roadmap_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    # Primary link: backlog items (epic, feature, story, task)
    item_id = Column(
        String(50),
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=True
    )
    # Optional link: portal feature requests
    feature_request_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_feature_requests.id", ondelete="CASCADE"),
        nullable=True
    )
    # Link to analysis queue entry (proves item was analyzed)
    analysis_queue_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_analysis_queue.id", ondelete="SET NULL"),
        nullable=True
    )
    release_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_releases.id", ondelete="SET NULL"),
        nullable=True
    )

    # Positioning
    display_order = Column(Integer, default=0)
    lane = Column(String(50), nullable=True)

    # Status override
    roadmap_status = Column(String(30), nullable=True)

    # Effort estimation
    estimated_days = Column(Integer, nullable=True)
    progress_percent = Column(Integer, default=0)

    # Dependencies
    depends_on = Column(JSONB, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    release = relationship("PortalRelease", back_populates="roadmap_items")
    backlog_item = relationship("Item", foreign_keys=[item_id])
    analysis_entry = relationship("PortalAnalysisQueue", foreign_keys=[analysis_queue_id])

    __table_args__ = (
        UniqueConstraint('item_id', name='uq_roadmap_item_backlog'),
        UniqueConstraint('feature_request_id', name='uq_roadmap_item_feature'),
    )

    def to_dict(self, include_item_details: bool = False) -> Dict[str, Any]:
        """Convert roadmap item to dictionary."""
        result = {
            "id": str(self.id),
            "item_id": self.item_id,
            "feature_request_id": str(self.feature_request_id) if self.feature_request_id else None,
            "analysis_queue_id": str(self.analysis_queue_id) if self.analysis_queue_id else None,
            "release_id": str(self.release_id) if self.release_id else None,
            "display_order": self.display_order,
            "lane": self.lane,
            "roadmap_status": self.roadmap_status,
            "estimated_days": self.estimated_days,
            "progress_percent": self.progress_percent,
            "depends_on": self.depends_on,
            "notes": self.notes,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_item_details and self.backlog_item:
            result["item"] = {
                "id": self.backlog_item.id,
                "type": self.backlog_item.type.value if self.backlog_item.type else None,
                "title": self.backlog_item.title,
                "status": self.backlog_item.status,
                "priority": self.backlog_item.priority,
                "sp": self.backlog_item.sp,
            }

        return result


class PortalPublicRoadmap(Base):
    """
    Configuration for a public, shareable roadmap view.

    Allows creating embeddable or linkable roadmap pages
    with customizable visibility and styling options.
    """
    __tablename__ = "portal_public_roadmaps"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )

    # Sharing
    slug = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Visibility settings
    is_active = Column(Boolean, default=True)
    show_completed = Column(Boolean, default=True)
    show_cancelled = Column(Boolean, default=False)
    show_dates = Column(Boolean, default=True)
    show_progress = Column(Boolean, default=True)
    show_votes = Column(Boolean, default=True)

    # Filtering
    included_releases = Column(JSONB, nullable=True)
    excluded_statuses = Column(JSONB, nullable=True)

    # Customization
    theme = Column(String(20), default="light")
    custom_css = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    header_color = Column(String(7), nullable=True)

    # Analytics
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert public roadmap config to dictionary."""
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "is_active": self.is_active,
            "show_completed": self.show_completed,
            "show_cancelled": self.show_cancelled,
            "show_dates": self.show_dates,
            "show_progress": self.show_progress,
            "show_votes": self.show_votes,
            "included_releases": self.included_releases,
            "excluded_statuses": self.excluded_statuses,
            "theme": self.theme,
            "logo_url": self.logo_url,
            "header_color": self.header_color,
            "view_count": self.view_count,
            "last_viewed_at": self.last_viewed_at.isoformat() if self.last_viewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "public_url": f"/roadmap/{self.slug}",
        }

    def increment_views(self) -> None:
        """Increment view count and update last viewed timestamp."""
        self.view_count = (self.view_count or 0) + 1
        self.last_viewed_at = datetime.now(timezone.utc)
