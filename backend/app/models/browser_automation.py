"""
Browser Automation Models - Week 78

SQLAlchemy models for:
- Playwriter: Browser automation sessions and executions
- BigAGI: Multi-model validation and consensus
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from enum import Enum
import uuid

from app.database import Base


class BrowserType(str, Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class SessionStatus(str, Enum):
    """Playwriter session status."""
    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"
    ERROR = "error"


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationStatus(str, Enum):
    """BigAGI validation status."""
    PENDING = "pending"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsensusMethod(str, Enum):
    """Consensus calculation methods."""
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    UNANIMOUS = "unanimous"


class ConsensusRecommendation(str, Enum):
    """Consensus recommendations."""
    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"


# Playwriter Models

class PlaywriterSession(Base):
    """Browser automation session."""
    __tablename__ = "playwriter_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    browser_type = Column(String(50), default=BrowserType.CHROMIUM.value)
    headless = Column(Boolean, default=True)
    viewport_width = Column(Integer, default=1280)
    viewport_height = Column(Integer, default=720)
    status = Column(String(50), default=SessionStatus.CREATED.value)
    error_message = Column(Text, nullable=True)
    context_options = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    executions = relationship("PlaywriterExecution", back_populates="session", cascade="all, delete-orphan")
    tabs = relationship("PlaywriterTab", back_populates="session", cascade="all, delete-orphan")


class PlaywriterExecution(Base):
    """Code execution record."""
    __tablename__ = "playwriter_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("playwriter_sessions.id", ondelete="CASCADE"), nullable=False)
    tab_id = Column(Integer, nullable=True)
    code = Column(Text, nullable=False)
    result = Column(JSONB, nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    error = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    status = Column(String(50), default=ExecutionStatus.PENDING.value)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("PlaywriterSession", back_populates="executions")


class PlaywriterTab(Base):
    """Tab permission management."""
    __tablename__ = "playwriter_tabs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("playwriter_sessions.id", ondelete="CASCADE"), nullable=False)
    tab_index = Column(Integer, nullable=False)
    url = Column(String(2000), nullable=True)
    title = Column(String(500), nullable=True)
    permitted = Column(Boolean, default=False)
    permitted_at = Column(DateTime, nullable=True)
    permitted_by = Column(String(100), nullable=True)
    last_accessed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("PlaywriterSession", back_populates="tabs")


# BigAGI Models

class BigAGIValidation(Base):
    """Multi-model validation session."""
    __tablename__ = "bigagi_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task = Column(Text, nullable=False)
    primary_response = Column(Text, nullable=False)
    primary_model = Column(String(100), nullable=False)
    validation_models = Column(JSONB, nullable=False)
    status = Column(String(50), default=ValidationStatus.PENDING.value)
    consensus_score = Column(Float, nullable=True)
    consensus_reached = Column(Boolean, nullable=True)
    final_answer = Column(Text, nullable=True)
    session_metadata = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    responses = relationship("BigAGIResponse", back_populates="validation", cascade="all, delete-orphan")
    consensus = relationship("BigAGIConsensus", back_populates="validation", cascade="all, delete-orphan", uselist=False)


class BigAGIResponse(Base):
    """Individual model response."""
    __tablename__ = "bigagi_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    validation_id = Column(UUID(as_uuid=True), ForeignKey("bigagi_validations.id", ondelete="CASCADE"), nullable=False)
    model = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    response = Column(Text, nullable=False)
    thinking = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    agreement_score = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    validation = relationship("BigAGIValidation", back_populates="responses")


class BigAGIConsensus(Base):
    """Consensus calculation result."""
    __tablename__ = "bigagi_consensus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    validation_id = Column(UUID(as_uuid=True), ForeignKey("bigagi_validations.id", ondelete="CASCADE"), nullable=False)
    method = Column(String(50), nullable=False)
    agreement_matrix = Column(JSONB, nullable=True)
    key_agreements = Column(JSONB, default=[])
    key_disagreements = Column(JSONB, default=[])
    synthesis = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    recommendation = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    validation = relationship("BigAGIValidation", back_populates="consensus")
