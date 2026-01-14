"""
Stage Review Database Models.

Fase 23.6 Phase 24.4: Database persistence for stage reviews and performance metrics.

Tables:
- stage_review_sessions: Review session tracking
- stage_model_reviews: Individual model reviews within a session
- stage_review_issues: Detected issues with consensus
- stage_review_metrics: Performance metrics per model/stage
"""

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean,
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class StageTypeDB(str, enum.Enum):
    """Development stage types for database storage."""
    ARCHITECTURE = "architecture"
    DESIGN = "design"
    ANALYSIS = "analysis"
    PROGRAMMING = "programming"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"


class ReviewDecisionDB(str, enum.Enum):
    """Review decisions for database storage."""
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class IssueSeverityDB(str, enum.Enum):
    """Issue severity levels for database storage."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    SUGGESTION = "suggestion"


class IssueCategoryDB(str, enum.Enum):
    """Issue categories for database storage."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"


class StageReviewSession(Base):
    """
    Stage review session tracking.

    Stores metadata about each review session including
    stage type, decision, consensus, and timing.
    """
    __tablename__ = "stage_review_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)

    # Context
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=True, index=True)
    stage_type = Column(SQLEnum(StageTypeDB), nullable=False, index=True)
    artifact_type = Column(String(50), nullable=True)
    artifact_hash = Column(String(64), nullable=True, index=True)

    # Results
    decision = Column(SQLEnum(ReviewDecisionDB), nullable=False)
    approved = Column(Boolean, nullable=False, default=False)
    consensus_level = Column(Float, nullable=False, default=0.0)
    rounds_completed = Column(Integer, nullable=False, default=1)

    # Issue counts (denormalized for quick queries)
    total_issues = Column(Integer, nullable=False, default=0)
    critical_issues = Column(Integer, nullable=False, default=0)
    major_issues = Column(Integer, nullable=False, default=0)
    minor_issues = Column(Integer, nullable=False, default=0)

    # Timing
    duration_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Improvement
    improvement_applied = Column(Boolean, nullable=False, default=False)
    improved_artifact = Column(Text, nullable=True)

    # Relationships
    model_reviews = relationship(
        "StageModelReview",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    issues = relationship(
        "StageReviewIssue",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_stage_review_sessions_project_stage", "project_id", "stage_type"),
        Index("ix_stage_review_sessions_created", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "project_id": self.project_id,
            "workflow_id": self.workflow_id,
            "stage_type": self.stage_type.value if self.stage_type else None,
            "artifact_type": self.artifact_type,
            "decision": self.decision.value if self.decision else None,
            "approved": self.approved,
            "consensus_level": self.consensus_level,
            "rounds_completed": self.rounds_completed,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "major_issues": self.major_issues,
            "minor_issues": self.minor_issues,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "improvement_applied": self.improvement_applied,
        }


class StageModelReview(Base):
    """
    Individual model review within a session.

    Tracks each model's response, timing, and issues found.
    """
    __tablename__ = "stage_model_reviews"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("stage_review_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Model info
    model_name = Column(String(100), nullable=False, index=True)
    model_provider = Column(String(50), nullable=True)
    model_role = Column(String(20), nullable=False, default="primary")

    # Results
    round_number = Column(Integer, nullable=False, default=1)
    issues_found = Column(Integer, nullable=False, default=0)
    response_time_ms = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="completed")
    error_message = Column(Text, nullable=True)

    # Raw response (optional, for debugging)
    review_text = Column(Text, nullable=True)

    # Relationships
    session = relationship("StageReviewSession", back_populates="model_reviews")

    # Indexes
    __table_args__ = (
        Index("ix_stage_model_reviews_model_session", "model_name", "session_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "model_name": self.model_name,
            "model_provider": self.model_provider,
            "model_role": self.model_role,
            "round_number": self.round_number,
            "issues_found": self.issues_found,
            "response_time_ms": self.response_time_ms,
            "status": self.status,
            "error_message": self.error_message,
        }


class StageReviewIssue(Base):
    """
    Detected issue from a stage review.

    Stores consolidated issues with consensus information.
    """
    __tablename__ = "stage_review_issues"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("stage_review_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Issue details
    severity = Column(SQLEnum(IssueSeverityDB), nullable=False, index=True)
    category = Column(SQLEnum(IssueCategoryDB), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)

    # Location
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)

    # Consensus
    consensus_score = Column(Float, nullable=False, default=0.0)
    confirmed_by_models = Column(JSON, nullable=True)  # List of model names

    # Status tracking
    is_addressed = Column(Boolean, nullable=False, default=False)
    addressed_in_round = Column(Integer, nullable=True)

    # Relationships
    session = relationship("StageReviewSession", back_populates="issues")

    # Indexes
    __table_args__ = (
        Index("ix_stage_review_issues_severity_category", "severity", "category"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "severity": self.severity.value if self.severity else None,
            "category": self.category.value if self.category else None,
            "title": self.title,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "consensus_score": self.consensus_score,
            "confirmed_by_models": self.confirmed_by_models,
            "is_addressed": self.is_addressed,
            "addressed_in_round": self.addressed_in_round,
        }


class StageReviewMetrics(Base):
    """
    Performance metrics for stage reviews.

    Aggregated metrics per model and stage type for
    tuning and optimization.
    """
    __tablename__ = "stage_review_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Grouping
    model_name = Column(String(100), nullable=False, index=True)
    stage_type = Column(SQLEnum(StageTypeDB), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Review counts
    total_reviews = Column(Integer, nullable=False, default=0)
    successful_reviews = Column(Integer, nullable=False, default=0)
    timeout_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)

    # Timing metrics
    avg_response_time_ms = Column(Float, nullable=False, default=0.0)
    min_response_time_ms = Column(Integer, nullable=False, default=0)
    max_response_time_ms = Column(Integer, nullable=False, default=0)
    p95_response_time_ms = Column(Integer, nullable=False, default=0)

    # Issue metrics
    avg_issues_found = Column(Float, nullable=False, default=0.0)
    total_critical_found = Column(Integer, nullable=False, default=0)
    total_major_found = Column(Integer, nullable=False, default=0)

    # Consensus metrics
    avg_consensus_alignment = Column(Float, nullable=False, default=0.0)
    consensus_leader_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Unique constraint on model + stage + period
    __table_args__ = (
        UniqueConstraint(
            "model_name", "stage_type", "period_start",
            name="uq_stage_review_metrics_model_stage_period"
        ),
        Index("ix_stage_review_metrics_period", "period_start", "period_end"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "model_name": self.model_name,
            "stage_type": self.stage_type.value if self.stage_type else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_reviews": self.total_reviews,
            "successful_reviews": self.successful_reviews,
            "timeout_count": self.timeout_count,
            "error_count": self.error_count,
            "avg_response_time_ms": self.avg_response_time_ms,
            "min_response_time_ms": self.min_response_time_ms,
            "max_response_time_ms": self.max_response_time_ms,
            "p95_response_time_ms": self.p95_response_time_ms,
            "avg_issues_found": self.avg_issues_found,
            "total_critical_found": self.total_critical_found,
            "total_major_found": self.total_major_found,
            "avg_consensus_alignment": self.avg_consensus_alignment,
            "consensus_leader_count": self.consensus_leader_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
