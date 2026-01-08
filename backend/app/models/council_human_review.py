"""
Council Human Review Models

Week 55: Human-in-the-Loop Council
Models for human review workflow and document versioning.

Tables:
- CouncilHumanSession: Extended session with human review capability
- CouncilProviderResponse: Individual provider responses
- CouncilPeerReview: Peer reviews from round-robin evaluation
- CouncilConsensus: Consensus documents with versioning and human feedback
- DocumentVersion: MD files synced with database
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class SessionStatus(str, Enum):
    """Status values for council human sessions."""
    DRAFT = "draft"
    GENERATING = "generating"
    PEER_REVIEW = "peer_review"
    ORCHESTRATING = "orchestrating"
    HUMAN_REVIEW = "human_review"
    FINALIZING = "finalizing"
    APPROVED = "approved"
    REJECTED = "rejected"


class DocumentType(str, Enum):
    """Types of documents that can be generated via council."""
    ONBOARDING = "onboarding"
    ARCHITECTURE = "architecture"
    ADR = "adr"  # Architecture Decision Record
    SPECIFICATION = "specification"
    README = "readme"
    API_DOCS = "api_docs"
    OTHER = "other"


class CouncilHumanSession(Base):
    """
    Extended council session with human review workflow.

    Represents a complete council process from generation through human approval.
    """
    __tablename__ = "council_human_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    document_type = Column(String(50), nullable=False)
    document_name = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default=SessionStatus.DRAFT.value)
    providers_config = Column(JSONB, nullable=False, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow(), nullable=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejected_by = Column(String(100), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Relationships
    provider_responses = relationship("CouncilProviderResponse", back_populates="session", cascade="all, delete-orphan")
    peer_reviews = relationship("CouncilPeerReview", back_populates="session", cascade="all, delete-orphan")
    consensus_versions = relationship("CouncilConsensus", back_populates="session", cascade="all, delete-orphan")
    document_versions = relationship("DocumentVersion", back_populates="council_session")

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'generating', 'peer_review', 'orchestrating', 'human_review', 'finalizing', 'approved', 'rejected')",
            name="ck_council_human_session_status"
        ),
        CheckConstraint(
            "document_type IN ('onboarding', 'architecture', 'adr', 'specification', 'readme', 'api_docs', 'other')",
            name="ck_council_human_session_doc_type"
        ),
        Index("idx_council_human_session_project", "project_id"),
        Index("idx_council_human_session_status", "status"),
        Index("idx_council_human_session_doc_type", "document_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "document_type": self.document_type,
            "document_name": self.document_name,
            "status": self.status,
            "providers_config": self.providers_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason,
        }


class CouncilProviderResponse(Base):
    """
    Individual provider response for a council session.

    Stores the raw response from each provider (Ollama, Claude, Codex).
    """
    __tablename__ = "council_provider_responses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("council_human_sessions.id", ondelete="CASCADE"), nullable=False)
    provider_name = Column(String(100), nullable=False)  # e.g., "ollama/qwen2.5-coder:7b", "claude/sonnet"
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    extra_data = Column("metadata", JSONB, nullable=False, default=dict)  # DB column is 'metadata', Python attr is 'extra_data'
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)

    # Relationships
    session = relationship("CouncilHumanSession", back_populates="provider_responses")

    __table_args__ = (
        Index("idx_council_provider_response_session", "session_id"),
        Index("idx_council_provider_response_provider", "provider_name"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "provider_name": self.provider_name,
            "content": self.content,
            "tokens_used": self.tokens_used,
            "generation_time_ms": self.generation_time_ms,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CouncilPeerReview(Base):
    """
    Peer review from round-robin evaluation.

    Each provider reviews all other providers' responses.
    """
    __tablename__ = "council_peer_reviews"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("council_human_sessions.id", ondelete="CASCADE"), nullable=False)
    reviewer_provider = Column(String(100), nullable=False)
    reviewed_provider = Column(String(100), nullable=False)
    score = Column(Integer, nullable=False)  # 0-100
    strengths = Column(ARRAY(Text), nullable=True)
    weaknesses = Column(ARRAY(Text), nullable=True)
    suggestions = Column(ARRAY(Text), nullable=True)
    consensus_contribution = Column(Text, nullable=True)  # What to keep in consensus
    extra_data = Column("metadata", JSONB, nullable=False, default=dict)  # DB column is 'metadata', Python attr is 'extra_data'
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)

    # Relationships
    session = relationship("CouncilHumanSession", back_populates="peer_reviews")

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_council_peer_review_score"),
        Index("idx_council_peer_review_session", "session_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "reviewer_provider": self.reviewer_provider,
            "reviewed_provider": self.reviewed_provider,
            "score": self.score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "consensus_contribution": self.consensus_contribution,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CouncilConsensus(Base):
    """
    Consensus document with versioning and human feedback.

    Stores the orchestrator's synthesis and human corrections/additions.
    """
    __tablename__ = "council_consensus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("council_human_sessions.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    consensus_content = Column(Text, nullable=False)
    orchestrator_notes = Column(Text, nullable=True)  # Orchestrator's synthesis reasoning

    # Human feedback fields
    human_feedback = Column(JSONB, nullable=True)  # General human corrections
    human_marked_correct = Column(JSONB, nullable=True)  # Items marked correct per provider
    human_conflicts_resolved = Column(JSONB, nullable=True)  # How conflicts were resolved
    human_additions = Column(Text, nullable=True)  # What human added that all LLMs missed

    is_approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("CouncilHumanSession", back_populates="consensus_versions")

    __table_args__ = (
        UniqueConstraint("session_id", "version", name="uq_council_consensus_session_version"),
        Index("idx_council_consensus_session", "session_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": str(self.session_id),
            "version": self.version,
            "consensus_content": self.consensus_content,
            "orchestrator_notes": self.orchestrator_notes,
            "human_feedback": self.human_feedback,
            "human_marked_correct": self.human_marked_correct,
            "human_conflicts_resolved": self.human_conflicts_resolved,
            "human_additions": self.human_additions,
            "is_approved": self.is_approved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


class DocumentVersion(Base):
    """
    Versioned document synced with MD files.

    Provides bi-directional sync between database and filesystem.
    """
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    document_path = Column(String(500), nullable=False)  # e.g., "docs/ONBOARDING.md"
    document_type = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA256 for change detection
    council_session_id = Column(PGUUID(as_uuid=True), ForeignKey("council_human_sessions.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(String(100), nullable=True)  # "council", "human", "sync"
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    extra_metadata = Column(JSONB, nullable=False, default=dict)

    # Relationships
    council_session = relationship("CouncilHumanSession", back_populates="document_versions")

    __table_args__ = (
        UniqueConstraint("project_id", "document_path", "version", name="uq_document_version"),
        Index("idx_document_version_project", "project_id"),
        Index("idx_document_version_path", "document_path"),
        Index("idx_document_version_type", "document_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "document_path": self.document_path,
            "document_type": self.document_type,
            "version": self.version,
            "content": self.content,
            "content_hash": self.content_hash,
            "council_session_id": str(self.council_session_id) if self.council_session_id else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "extra_metadata": self.extra_metadata,
        }
