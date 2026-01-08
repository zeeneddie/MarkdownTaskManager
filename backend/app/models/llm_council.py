"""
LLM Council Models for Multi-Model Decision Making

Week 52: LLM Council Multi-Model Decision Making
Supports 3-stage consensus process: Response → Peer Review → Synthesis
"""

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, CheckConstraint, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class CouncilSession(Base):
    """
    Council session for multi-LLM decision making.

    A session represents one question/decision that needs council input.
    Goes through 3 stages: Response → Review → Synthesis
    """
    __tablename__ = "council_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    context = Column(JSONB, nullable=False, default={})
    decision_type = Column(String(50), nullable=False)  # architecture, planning, quality, generation
    agent_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, reviewing, complete
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    responses = relationship(
        "CouncilResponse",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reviews = relationship(
        "CouncilReview",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    decision = relationship(
        "CouncilDecision",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'reviewing', 'complete']),
            name='ck_council_session_status'
        ),
        CheckConstraint(
            decision_type.in_(['architecture', 'planning', 'quality', 'generation']),
            name='ck_council_session_decision_type'
        ),
        Index('idx_council_session_agent_status', 'agent_id', 'status'),
    )

    def __repr__(self):
        return f"<CouncilSession(id={self.id}, type={self.decision_type}, status={self.status})>"


class CouncilResponse(Base):
    """
    Individual model response in a council session.

    Each LLM model provides its own response to the question.
    Stage 1 of the 3-stage process.
    """
    __tablename__ = "council_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("council_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    model_name = Column(String(100), nullable=False)
    response_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    session = relationship("CouncilSession", back_populates="responses")
    reviews_received = relationship(
        "CouncilReview",
        back_populates="reviewed_response",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            confidence.between(0.0, 1.0),
            name='ck_council_response_confidence'
        ),
        Index('idx_council_response_session', 'session_id'),
    )

    def __repr__(self):
        return f"<CouncilResponse(id={self.id}, model={self.model_name}, confidence={self.confidence})>"


class CouncilReview(Base):
    """
    Peer review from one model to another's response.

    Anonymous/blind review where models evaluate each other's responses.
    Stage 2 of the 3-stage process.
    """
    __tablename__ = "council_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("council_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reviewer_model = Column(String(100), nullable=False)
    reviewed_response_id = Column(
        UUID(as_uuid=True),
        ForeignKey("council_responses.id", ondelete="CASCADE"),
        nullable=False
    )
    accuracy_score = Column(Float, nullable=False)      # 0-10
    completeness_score = Column(Float, nullable=False)  # 0-10
    clarity_score = Column(Float, nullable=False)       # 0-10
    feasibility_score = Column(Float, nullable=False)   # 0-10
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    session = relationship("CouncilSession", back_populates="reviews")
    reviewed_response = relationship("CouncilResponse", back_populates="reviews_received")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            accuracy_score.between(0.0, 10.0),
            name='ck_council_review_accuracy'
        ),
        CheckConstraint(
            completeness_score.between(0.0, 10.0),
            name='ck_council_review_completeness'
        ),
        CheckConstraint(
            clarity_score.between(0.0, 10.0),
            name='ck_council_review_clarity'
        ),
        CheckConstraint(
            feasibility_score.between(0.0, 10.0),
            name='ck_council_review_feasibility'
        ),
        Index('idx_council_review_session', 'session_id'),
        Index('idx_council_review_response', 'reviewed_response_id'),
    )

    def __repr__(self):
        return f"<CouncilReview(id={self.id}, reviewer={self.reviewer_model})>"

    @property
    def average_score(self) -> float:
        """Calculate average of all review scores."""
        return (
            self.accuracy_score +
            self.completeness_score +
            self.clarity_score +
            self.feasibility_score
        ) / 4.0


class CouncilDecision(Base):
    """
    Final synthesized decision from chairman model.

    The chairman (deepseek-r1) synthesizes all responses and reviews
    into a single consensus decision.
    Stage 3 of the 3-stage process.
    """
    __tablename__ = "council_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("council_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    chairman_model = Column(String(100), nullable=False)
    final_decision = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    consensus_level = Column(Float, nullable=False)  # 0-100% agreement
    dissenting_opinions = Column(ARRAY(Text), nullable=True)  # Minority views
    synthesis_reasoning = Column(Text, nullable=True)  # Why this decision?
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    session = relationship("CouncilSession", back_populates="decision")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            confidence.between(0.0, 1.0),
            name='ck_council_decision_confidence'
        ),
        CheckConstraint(
            consensus_level.between(0.0, 100.0),
            name='ck_council_decision_consensus'
        ),
        Index('idx_council_decision_session', 'session_id'),
    )

    def __repr__(self):
        return f"<CouncilDecision(id={self.id}, consensus={self.consensus_level}%)>"

    @property
    def has_strong_consensus(self) -> bool:
        """Check if consensus level is strong (>80%)."""
        return self.consensus_level >= 80.0

    @property
    def has_dissent(self) -> bool:
        """Check if there are dissenting opinions."""
        return bool(self.dissenting_opinions)
