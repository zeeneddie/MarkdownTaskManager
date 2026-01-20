from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
import uuid
from app.database import Base


# Status constants (using String instead of Enum for simpler migration)
class SessionStatus:
    """Green-paper session status constants"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ConstitutionStatus:
    """Constitution approval status constants"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class SpecificationStatus:
    """Specification approval status constants"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class GreenPaperSession(Base):
    """
    Green-paper session tracking for MarQed workflow.
    One session contains 6 strategic questions.
    """
    __tablename__ = "green_paper_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(50), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)

    session_type = Column(String(50), nullable=False, default="green-paper")
    status = Column(String(20), nullable=False, default=SessionStatus.IN_PROGRESS, index=True)

    current_question = Column(Integer, default=1)
    total_questions = Column(Integer, default=6)
    progress_percentage = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    generation_metadata = Column(JSONB, nullable=True)  # initiated_by, context, etc.

    # Relationships
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")
    constitutions = relationship("Constitution", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GreenPaperSession(id={self.id}, project_id={self.project_id}, status='{self.status}')>"


class Answer(Base):
    """
    Individual answer to a MarQed question.
    Questions 1-4 are required, 5-6 are optional.
    """
    __tablename__ = "green_paper_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("green_paper_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    question_number = Column(Integer, nullable=False)  # 1-6
    question_text = Column(Text, nullable=False)  # Store question text for historical reference
    answer = Column(Text, nullable=False)

    is_required = Column(Integer, default=1)  # 1=required, 0=optional
    max_length = Column(Integer, nullable=True)  # Character limit

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    generation_metadata = Column(JSONB, nullable=True)  # time_spent_seconds, revision_count

    # Relationships
    session = relationship("GreenPaperSession", back_populates="answers")

    def __repr__(self):
        return f"<Answer(id={self.id}, session_id={self.session_id}, question={self.question_number})>"


class Constitution(Base):
    """
    Generated project constitution from MarQed answers.
    Created by Peter (Product Owner agent) using deepseek-r1:latest.
    Target: 1000-1500 words, 7 sections.
    """
    __tablename__ = "green_paper_constitutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("green_paper_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(50), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(20), nullable=False, default=ConstitutionStatus.DRAFT, index=True)

    # Content in both formats
    content_json = Column(JSONB, nullable=False)  # Structured: {principles, requirements, constraints, risks, scope}
    content_markdown = Column(Text, nullable=False)  # Markdown document

    word_count = Column(Integer, nullable=True)
    generated_by = Column(String(50), default="Peter")  # Agent name

    # Review tracking
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)  # User ID
    review_feedback = Column(Text, nullable=True)  # Rejection reason or comments

    generation_attempt = Column(Integer, default=1)  # Retry counter (max 3)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    generation_metadata = Column(JSONB, nullable=True)  # generation_time, model_version, etc.

    # Relationships
    session = relationship("GreenPaperSession", back_populates="constitutions")
    specifications = relationship("Specification", back_populates="constitution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Constitution(id={self.id}, project_id={self.project_id}, status='{self.status}', words={self.word_count})>"


class Specification(Base):
    """
    Generated High-Level Design specification from approved constitution.
    Created by Felix (Feature Architect agent) using qwen2.5-coder:7b.
    Contains architecture, components, interfaces, data models.
    """
    __tablename__ = "green_paper_specifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    constitution_id = Column(UUID(as_uuid=True), ForeignKey("green_paper_constitutions.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(50), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(20), nullable=False, default=SpecificationStatus.DRAFT, index=True)

    # Content in both formats
    content_json = Column(JSONB, nullable=False)  # Structured: {architecture, components, interfaces, data_model, quality_requirements}
    content_markdown = Column(Text, nullable=False)  # Markdown document

    generated_by = Column(String(50), default="Felix")  # Agent name

    # Review tracking
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    review_feedback = Column(Text, nullable=True)

    generation_attempt = Column(Integer, default=1)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    generation_metadata = Column(JSONB, nullable=True)

    # Relationships
    constitution = relationship("Constitution", back_populates="specifications")
    epics = relationship("Epic", back_populates="specification", cascade="all, delete-orphan")  # Week 11: Task hierarchy

    def __repr__(self):
        return f"<Specification(id={self.id}, project_id={self.project_id}, status='{self.status}')>"
