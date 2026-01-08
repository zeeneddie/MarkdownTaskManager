"""
Claude-Mem Models - Week 76 Session Memory

SQLAlchemy models for persistent session memory management.
Supports observation capture, tagging, compression, and search.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ClaudeMemSession(Base):
    """
    Session metadata and configuration.

    Tracks session state, endless mode settings, and compression parameters.
    """
    __tablename__ = 'claude_mem_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, unique=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    title = Column(String(255))
    endless_mode = Column(Boolean, default=False)
    token_budget = Column(Integer, default=4000)  # Max tokens for context window
    compression_ratio = Column(Float, default=0.1)  # Target compression
    auto_tag = Column(Boolean, default=True)
    session_data = Column(JSONB, default=dict)  # Session metadata
    last_activity = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    observations = relationship("ClaudeMemObservation", back_populates="session", cascade="all, delete-orphan")
    summaries = relationship("ClaudeMemSummary", back_populates="session", cascade="all, delete-orphan")
    context_windows = relationship("ClaudeMemContextWindow", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "project_id": self.project_id,
            "title": self.title,
            "endless_mode": self.endless_mode,
            "token_budget": self.token_budget,
            "compression_ratio": self.compression_ratio,
            "auto_tag": self.auto_tag,
            "session_data": self.session_data or {},
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ClaudeMemObservation(Base):
    """
    Captured observation during a session.

    Stores insights, decisions, errors, and progress notes with tagging support.
    """
    __tablename__ = 'claude_mem_observations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), ForeignKey('claude_mem_sessions.session_id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSONB, default=list)  # ["decision", "bugfix", "architecture"]
    priority = Column(String(20), default='normal')  # critical, high, normal, low
    observation_type = Column(String(50))  # insight, decision, error, progress
    source_context = Column(Text)  # Where the observation came from
    related_files = Column(JSONB, default=list)  # Related file paths
    embedding_status = Column(String(20), default='pending')  # pending, computed, failed
    observation_data = Column(JSONB, default=dict)  # Additional metadata
    created_at = Column(DateTime, default=func.now())

    # Relationships
    session = relationship("ClaudeMemSession", back_populates="observations")
    search_indices = relationship("ClaudeMemSearchIndex", back_populates="observation", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "content": self.content,
            "tags": self.tags or [],
            "priority": self.priority,
            "observation_type": self.observation_type,
            "source_context": self.source_context,
            "related_files": self.related_files or [],
            "embedding_status": self.embedding_status,
            "observation_data": self.observation_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ClaudeMemSummary(Base):
    """
    Compressed summary of observations.

    Provides progressive disclosure by summarizing older observations.
    """
    __tablename__ = 'claude_mem_summaries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), ForeignKey('claude_mem_sessions.session_id', ondelete='CASCADE'), nullable=False)
    original_count = Column(Integer, default=0)  # Number of observations summarized
    summary = Column(Text, nullable=False)
    compression_ratio = Column(Float)  # Actual compression achieved
    token_count = Column(Integer)  # Tokens in summary
    tags_summary = Column(JSONB, default=dict)  # Tag frequency counts
    time_range_start = Column(DateTime)  # When first obs was captured
    time_range_end = Column(DateTime)  # When last obs was captured
    summary_data = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    session = relationship("ClaudeMemSession", back_populates="summaries")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "original_count": self.original_count,
            "summary": self.summary,
            "compression_ratio": self.compression_ratio,
            "token_count": self.token_count,
            "tags_summary": self.tags_summary or {},
            "time_range_start": self.time_range_start.isoformat() if self.time_range_start else None,
            "time_range_end": self.time_range_end.isoformat() if self.time_range_end else None,
            "summary_data": self.summary_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ClaudeMemSearchIndex(Base):
    """
    Search index entry for full-text search.

    Supports PostgreSQL FTS for efficient observation retrieval.
    """
    __tablename__ = 'claude_mem_search_index'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    observation_id = Column(UUID(as_uuid=True), ForeignKey('claude_mem_observations.id', ondelete='CASCADE'), nullable=False)
    search_text = Column(Text)  # Normalized text for FTS
    tsvector = Column(Text)  # PostgreSQL tsvector
    chunk_number = Column(Integer, default=0)  # For long observations
    created_at = Column(DateTime, default=func.now())

    # Relationships
    observation = relationship("ClaudeMemObservation", back_populates="search_indices")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "observation_id": str(self.observation_id),
            "search_text": self.search_text,
            "chunk_number": self.chunk_number,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ClaudeMemContextWindow(Base):
    """
    Generated context window for a session.

    Stores assembled context including observations and summaries.
    """
    __tablename__ = 'claude_mem_context_windows'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), ForeignKey('claude_mem_sessions.session_id', ondelete='CASCADE'), nullable=False)
    context_text = Column(Text, nullable=False)  # Generated context
    token_count = Column(Integer)
    included_observations = Column(JSONB, default=list)  # Observation IDs included
    included_summaries = Column(JSONB, default=list)  # Summary IDs included
    generation_strategy = Column(String(50))  # recent, priority, search
    context_data = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    session = relationship("ClaudeMemSession", back_populates="context_windows")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "context_text": self.context_text,
            "token_count": self.token_count,
            "included_observations": self.included_observations or [],
            "included_summaries": self.included_summaries or [],
            "generation_strategy": self.generation_strategy,
            "context_data": self.context_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
