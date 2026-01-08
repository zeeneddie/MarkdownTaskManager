"""
BMAD Session Database Models

Week 144 - Fase 28: BMAD Persistentie

Persistent storage for BMAD 8-question workflow sessions.
Enables resume functionality and session history.

Difference from BrownPaperSession:
- BrownPaperSession: Code-analysis workflow (bottom-up, analyze code)
- BMADSession: Question workflow (top-down, 8 strategic questions)
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.database import Base


class BMADSessionStatus:
    """BMAD session status constants."""
    QUESTIONS = "questions"       # Answering 8 questions
    ANALYZING = "analyzing"       # Miguel analyzing migration complexity
    GENERATING = "generating"     # Peter generating specification
    TASKS = "tasks"               # Felix generating task hierarchy
    REVIEW = "review"             # Quinn reviewing, user approval pending
    APPROVED = "approved"         # Ready for implementation
    REJECTED = "rejected"         # Needs rework
    CANCELLED = "cancelled"       # Session abandoned


class BMADWorkflowType:
    """BMAD workflow type constants."""
    BROWN_PAPER = "brown_paper"   # Migration projects (8 questions)
    GREEN_PAPER = "green_paper"   # New projects (6 questions)


class BMADSession(Base):
    """
    BMAD 8-question workflow session.

    Supports both Brown Paper (migration) and Green Paper (new project) workflows.
    All answers and analysis results are persisted for resume functionality.
    """
    __tablename__ = "bmad_sessions"

    id = Column(String(36), primary_key=True)  # UUID as string
    project_name = Column(String(255), nullable=False, index=True)
    project_path = Column(String(1024), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True)

    # Workflow tracking
    status = Column(String(50), nullable=False, default=BMADSessionStatus.QUESTIONS, index=True)
    current_question = Column(Integer, nullable=False, default=1)
    workflow_type = Column(String(50), nullable=False, default=BMADWorkflowType.BROWN_PAPER, index=True)

    # JSONB columns for complex data
    answers = Column(JSONB, nullable=False, default=dict)  # {1: {...}, 2: {...}, ...}
    migration_analysis = Column(JSONB, nullable=True)  # Miguel's analysis result
    specification = Column(JSONB, nullable=True)  # Peter's migration specification
    tasks = Column(JSONB, nullable=True)  # Felix's task hierarchy
    enhanced_analysis = Column(JSONB, nullable=True)  # 6-phase analysis results

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Tracking
    created_by = Column(String(255), nullable=True)
    last_modified_by = Column(String(255), nullable=True)

    # Relationships
    answer_history = relationship("BMADAnswer", back_populates="session", cascade="all, delete-orphan")
    events = relationship("BMADSessionEvent", back_populates="session", cascade="all, delete-orphan")
    customer = relationship("Customer", back_populates="bmad_sessions")

    @property
    def total_questions(self) -> int:
        """Return total questions based on workflow type."""
        return 8 if self.workflow_type == BMADWorkflowType.BROWN_PAPER else 6

    @property
    def progress_percent(self) -> float:
        """Calculate completion percentage based on answered questions."""
        if not self.answers:
            return 0.0
        return (len(self.answers) / self.total_questions) * 100

    @property
    def is_complete(self) -> bool:
        """Check if all questions have been answered."""
        return len(self.answers or {}) >= self.total_questions

    @property
    def can_resume(self) -> bool:
        """Check if session can be resumed."""
        return self.status in [BMADSessionStatus.QUESTIONS, BMADSessionStatus.REVIEW]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "customer_id": self.customer_id,
            "status": self.status,
            "current_question": self.current_question,
            "workflow_type": self.workflow_type,
            "answers": self.answers,
            "migration_analysis": self.migration_analysis,
            "specification": self.specification,
            "tasks": self.tasks,
            "enhanced_analysis": self.enhanced_analysis,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percent": self.progress_percent,
            "is_complete": self.is_complete,
            "can_resume": self.can_resume,
            "total_questions": self.total_questions,
        }

    def __repr__(self):
        return f"<BMADSession(id={self.id}, project={self.project_name}, status='{self.status}', q={self.current_question}/{self.total_questions})>"


class BMADAnswer(Base):
    """
    Individual BMAD answer with version history.

    Supports answer revisions - when a user updates an answer,
    the old version is kept with is_current=False.
    """
    __tablename__ = "bmad_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey('bmad_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    question_number = Column(Integer, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    answered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True, index=True)

    # Relationship
    session = relationship("BMADSession", back_populates="answer_history")

    # Partial unique constraint (handled in migration)
    __table_args__ = (
        # Note: Partial unique constraint is defined in migration, not here
        # UniqueConstraint('session_id', 'question_number', sqlite_on_conflict='REPLACE'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "answer": self.answer,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
            "version": self.version,
            "is_current": self.is_current,
        }

    def __repr__(self):
        return f"<BMADAnswer(session={self.session_id}, q={self.question_number}, v={self.version})>"


class BMADSessionEvent(Base):
    """
    Audit trail for BMAD session events.

    Tracks all significant events in a session's lifecycle.
    """
    __tablename__ = "bmad_session_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey('bmad_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # started, answer_submitted, etc.
    event_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)

    # Relationship
    session = relationship("BMADSession", back_populates="events")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }

    def __repr__(self):
        return f"<BMADSessionEvent(session={self.session_id}, type='{self.event_type}')>"


class BMADEventType:
    """Event type constants for audit trail."""
    SESSION_STARTED = "session_started"
    ANSWER_SUBMITTED = "answer_submitted"
    ANSWER_UPDATED = "answer_updated"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    SPECIFICATION_GENERATED = "specification_generated"
    TASKS_GENERATED = "tasks_generated"
    ENHANCED_ANALYSIS_COMPLETED = "enhanced_analysis_completed"
    REVIEW_SUBMITTED = "review_submitted"
    SESSION_APPROVED = "session_approved"
    SESSION_REJECTED = "session_rejected"
    SESSION_RESUMED = "session_resumed"
    SESSION_CANCELLED = "session_cancelled"
