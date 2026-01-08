"""
Week 90: Portal Voting and Comments Models

SQLAlchemy models for:
- PortalFeatureVote: User votes on feature requests
- PortalFeatureComment: Threaded comments on feature requests
- PortalFeatureVoteAggregate: Cached vote aggregations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, backref

from app.database import Base


class PortalFeatureVote(Base):
    """
    User vote on a feature request.

    Supports upvotes and downvotes with optional weighting
    for premium users or stakeholders.
    """
    __tablename__ = "portal_feature_votes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_request_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_feature_requests.id", ondelete="CASCADE"),
        nullable=False
    )
    user_email = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=True)

    # Vote details
    vote_type = Column(String(10), nullable=False)  # 'up' or 'down'
    vote_weight = Column(Integer, default=1)  # Can be weighted for premium users

    # Tracking
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.utcnow())

    # Unique constraint defined in migration
    __table_args__ = (
        UniqueConstraint('feature_request_id', 'user_email', name='uq_feature_vote_user'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert vote to dictionary."""
        return {
            "id": str(self.id),
            "feature_request_id": str(self.feature_request_id),
            "user_email": self.user_email,
            "user_name": self.user_name,
            "vote_type": self.vote_type,
            "vote_weight": self.vote_weight,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PortalFeatureComment(Base):
    """
    Threaded comment on a feature request.

    Supports:
    - Nested replies (via parent_id)
    - @mentions
    - Markdown content
    - Edit/delete tracking
    """
    __tablename__ = "portal_feature_comments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_request_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_feature_requests.id", ondelete="CASCADE"),
        nullable=False
    )

    # Comment author
    user_email = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)  # customer, developer, admin

    # Comment content
    content = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)  # Rendered markdown

    # Threading
    parent_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_feature_comments.id", ondelete="CASCADE"),
        nullable=True
    )
    thread_depth = Column(Integer, default=0)

    # Mentions (@username)
    mentions = Column(JSONB, nullable=True)

    # Status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.utcnow())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships - self-referential for threaded comments
    replies = relationship(
        "PortalFeatureComment",
        backref=backref("parent", remote_side="PortalFeatureComment.id"),
        foreign_keys=[parent_id],
        lazy="select"
    )

    def __init__(self, **kwargs):
        """Initialize with Python-level defaults for non-persisted instantiation."""
        kwargs.setdefault('thread_depth', 0)
        kwargs.setdefault('is_edited', False)
        kwargs.setdefault('is_deleted', False)
        kwargs.setdefault('is_pinned', False)
        super().__init__(**kwargs)

    def to_dict(self, include_replies: bool = False) -> Dict[str, Any]:
        """Convert comment to dictionary."""
        result = {
            "id": str(self.id),
            "feature_request_id": str(self.feature_request_id),
            "user_email": self.user_email,
            "user_name": self.user_name,
            "user_role": self.user_role,
            "content": self.content if not self.is_deleted else "[deleted]",
            "content_html": self.content_html if not self.is_deleted else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "thread_depth": self.thread_depth,
            "mentions": self.mentions,
            "is_edited": self.is_edited,
            "is_deleted": self.is_deleted,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_replies:
            result["replies"] = [
                reply.to_dict(include_replies=True)
                for reply in self.replies if not reply.is_deleted
            ]

        return result


class PortalFeatureVoteAggregate(Base):
    """
    Cached vote aggregation for a feature request.

    Provides fast access to vote counts and rankings
    without needing to count votes on every request.
    """
    __tablename__ = "portal_feature_vote_aggregates"

    feature_request_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_feature_requests.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Aggregated counts
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    total_votes = Column(Integer, default=0)
    score = Column(Integer, default=0)  # upvotes - downvotes
    weighted_score = Column(Float, default=0.0)  # With time decay and user weight

    # Ranking
    rank_position = Column(Integer, nullable=True)  # Position in ranked list
    hot_score = Column(Float, default=0.0)  # Reddit-style hot ranking

    # Tracking
    last_vote_at = Column(DateTime(timezone=True), nullable=True)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregate to dictionary."""
        return {
            "feature_request_id": str(self.feature_request_id),
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "total_votes": self.total_votes,
            "score": self.score,
            "weighted_score": self.weighted_score,
            "rank_position": self.rank_position,
            "hot_score": self.hot_score,
            "last_vote_at": self.last_vote_at.isoformat() if self.last_vote_at else None,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
        }

    @classmethod
    def calculate_hot_score(cls, ups: int, downs: int, created_at: datetime) -> float:
        """
        Calculate Reddit-style hot score.

        Based on: https://medium.com/hacking-and-gonzo/how-reddit-ranking-algorithms-work-ef111e33d0d9
        """
        import math
        from datetime import timezone

        score = ups - downs
        order = math.log10(max(abs(score), 1))

        if score > 0:
            sign = 1
        elif score < 0:
            sign = -1
        else:
            sign = 0

        # Epoch: Jan 1, 2025
        epoch = datetime(2025, 1, 1, tzinfo=timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        seconds = (created_at - epoch).total_seconds()

        # For product roadmaps, net-negative items should have negative hot scores
        # This differs from Reddit where controversial items still rank positively
        return round(sign * (order + seconds / 45000), 7)
