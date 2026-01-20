"""
SQLAlchemy models for Confucius orchestrator.

Tables:
- confucius_sessions: Cross-task memory (permanent)
- confucius_entries: Per-task memory (30 days)
- confucius_runnables: Tool execution outputs (7 days)
- confucius_notes: Cross-session learning notes
"""

from datetime import datetime
from app.utils.datetime_utils import utc_now
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class ConfuciusSession(Base):
    """
    Session-level memory (cross-task, permanent retention).

    Stores insights, patterns, and decisions learned across tasks.
    """
    __tablename__ = "confucius_sessions"
    __table_args__ = {"extend_existing": True}

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    insights = Column(JSONB, default=list)
    patterns = Column(JSONB, default=list)
    decisions = Column(JSONB, default=list)
    preferences = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    entries = relationship(
        "ConfuciusEntry",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "ConfuciusNote",
        back_populates="session",
    )

    def __repr__(self):
        return f"<ConfuciusSession(session_id={self.session_id}, project_id={self.project_id})>"


class ConfuciusEntry(Base):
    """
    Entry-level memory (per-task, 30 days retention).

    Stores task context, results, and quality metrics.
    """
    __tablename__ = "confucius_entries"
    __table_args__ = (
        Index("ix_confucius_entries_quality_score", "quality_score"),
        {"extend_existing": True},
    )

    entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("confucius_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task = Column(Text, nullable=False)
    context_summary = Column(Text, default="")
    results_summary = Column(Text, default="")
    quality_score = Column(Float, default=0.0)
    iterations_used = Column(Integer, default=1)
    extensions_called = Column(JSONB, default=list)
    entry_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=utc_now, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("ConfuciusSession", back_populates="entries")
    runnables = relationship(
        "ConfuciusRunnable",
        back_populates="entry",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ConfuciusEntry(entry_id={self.entry_id}, task={self.task[:30]}...)>"


class ConfuciusRunnable(Base):
    """
    Runnable-level memory (per-extension call, 7 days retention).

    Stores individual extension execution results.
    """
    __tablename__ = "confucius_runnables"
    __table_args__ = {"extend_existing": True}

    runnable_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("confucius_entries.entry_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    extension_name = Column(String(100), nullable=False, index=True)
    input_summary = Column(Text, default="")
    output_summary = Column(Text, default="")
    output_data = Column(JSONB, default=dict)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    # Relationships
    entry = relationship("ConfuciusEntry", back_populates="runnables")

    def __repr__(self):
        return f"<ConfuciusRunnable(runnable_id={self.runnable_id}, extension={self.extension_name})>"


class ConfuciusNote(Base):
    """
    Cross-session learning notes.

    Records problems, solutions, and insights for future reference.
    """
    __tablename__ = "confucius_notes"
    __table_args__ = (
        Index(
            "ix_confucius_notes_context_tags",
            "context_tags",
            postgresql_using="gin",
        ),
        {"extend_existing": True},
    )

    note_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("confucius_sessions.session_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    note_type = Column(String(50), nullable=False, index=True)  # success, failure, insight, pattern, decision
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=True)
    insights = Column(JSONB, default=list)
    context_tags = Column(JSONB, default=list)
    quality_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now, index=True)

    # Relationships
    session = relationship("ConfuciusSession", back_populates="notes")

    def __repr__(self):
        return f"<ConfuciusNote(note_id={self.note_id}, type={self.note_type})>"
