"""
Brown Paper Database Models

Week 57 Day 2: Database persistence for Brown Paper sessions and analysis.

Brown Paper sessions follow the same lifecycle as Green Paper:
- Session -> Analysis -> Constitution -> Specification -> Epics

The key difference is the source:
- Green Paper: User answers questions -> AI generates constitution
- Brown Paper: AI analyzes code -> Human refines constitution
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class BrownPaperSessionStatus:
    """Brown Paper session status constants."""
    SCANNING = "scanning"           # Analyzing code structure
    ANALYZING = "analyzing"         # Extracting domains
    GENERATING = "generating"       # Creating constitution/epics
    REVIEW = "review"               # Awaiting human review
    APPROVED = "approved"           # Ready for implementation
    REJECTED = "rejected"           # Needs rework


class BrownPaperSession(Base):
    """
    Brown Paper session tracking for reverse engineering workflow.
    Links an Application to the analysis and generated artifacts.
    """
    __tablename__ = "brown_paper_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to Application Registry
    application_id = Column(Integer, nullable=False, index=True)
    application_name = Column(String(200), nullable=False)
    root_path = Column(String(500), nullable=False)

    # Session status
    status = Column(String(20), nullable=False, default=BrownPaperSessionStatus.SCANNING, index=True)

    # Analysis summary (quick reference without loading full analysis)
    modules_count = Column(Integer, default=0)
    domains_count = Column(Integer, default=0)
    classes_count = Column(Integer, default=0)
    functions_count = Column(Integer, default=0)
    patterns_detected = Column(JSONB, nullable=True)  # List of architecture patterns

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Generation metadata
    generation_metadata = Column(JSONB, nullable=True)  # analysis_time_ms, etc.

    # Relationships
    analysis = relationship("BrownPaperAnalysis", back_populates="session", uselist=False, cascade="all, delete-orphan")
    constitution = relationship("BrownPaperConstitution", back_populates="session", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BrownPaperSession(id={self.id}, app={self.application_name}, status='{self.status}')>"


class BrownPaperAnalysis(Base):
    """
    Detailed code analysis results from Brown Paper workflow.
    Stored separately to allow lazy loading of large analysis data.
    """
    __tablename__ = "brown_paper_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Code analysis (stored as JSON for flexibility)
    modules = Column(JSONB, nullable=False, default=[])  # List of CodeModule dicts
    primary_patterns = Column(JSONB, nullable=False, default=[])  # Detected architecture patterns

    # Documentation analysis
    doc_insights = Column(JSONB, nullable=False, default=[])  # List of DocumentationInsight dicts
    readme_summary = Column(Text, nullable=True)

    # Domain extraction
    domains = Column(JSONB, nullable=False, default=[])  # List of BusinessDomain dicts

    # Statistics
    analysis_time_ms = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    session = relationship("BrownPaperSession", back_populates="analysis")

    def __repr__(self):
        return f"<BrownPaperAnalysis(id={self.id}, modules={len(self.modules or [])}, domains={len(self.domains or [])})>"


class BrownPaperConstitution(Base):
    """
    Generated constitution from Brown Paper analysis.
    Same structure as Green Paper Constitution for unified output.
    """
    __tablename__ = "brown_paper_constitutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Link to project (if created)
    project_id = Column(String(50), ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True)

    # Status tracking
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft, review, approved, rejected

    # Constitution content (same structure as Green Paper)
    content_json = Column(JSONB, nullable=False)  # {mission_vision, core_principles, key_requirements, ...}
    content_markdown = Column(Text, nullable=True)  # Rendered markdown version

    # Generation info
    generated_by = Column(String(50), default="BrownPaper")
    generation_attempt = Column(Integer, default=1)

    # Human review tracking
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    review_feedback = Column(Text, nullable=True)

    # Human refinements (edits to auto-generated content)
    human_refinements = Column(JSONB, nullable=True)  # Track what human changed

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Metadata
    generation_metadata = Column(JSONB, nullable=True)

    # Relationships
    session = relationship("BrownPaperSession", back_populates="constitution")
    epics = relationship("BrownPaperEpic", back_populates="constitution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BrownPaperConstitution(id={self.id}, status='{self.status}')>"


class BrownPaperEpic(Base):
    """
    Epic generated from Brown Paper domain analysis.
    Same output format as Green Paper epics for unified task hierarchy.
    """
    __tablename__ = "brown_paper_epics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    constitution_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_constitutions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Epic identifier (for display)
    epic_number = Column(String(20), nullable=False)  # e.g., "EPIC-001"

    # Epic content
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=1)  # 1-5
    complexity = Column(String(20), default="medium")  # low, medium, high, very_high

    # Source domain info
    source_domain = Column(String(100), nullable=True)
    source_modules = Column(JSONB, nullable=True)  # Module paths that map to this epic
    source_entities = Column(JSONB, nullable=True)  # Entity/class names

    # Features (stored as JSON, can be expanded to separate table if needed)
    features = Column(JSONB, nullable=False, default=[])

    # Link to actual Epic in task hierarchy (after approval)
    linked_epic_id = Column(UUID(as_uuid=True), ForeignKey("task_epics.id", ondelete="SET NULL"), nullable=True)

    # Status
    status = Column(String(20), default="draft")  # draft, approved, linked

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    constitution = relationship("BrownPaperConstitution", back_populates="epics")

    def __repr__(self):
        return f"<BrownPaperEpic(id={self.id}, name='{self.name}', priority={self.priority})>"


class BrownPaperCodeModule(Base):
    """
    Individual code module discovered during analysis.
    Provides detailed view of each module for UI display.
    """
    __tablename__ = "brown_paper_code_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Module identification
    name = Column(String(200), nullable=False)
    path = Column(String(500), nullable=False)
    module_type = Column(String(50), nullable=False)  # service, repository, model, etc.

    # Module content
    description = Column(Text, nullable=True)
    classes = Column(JSONB, default=[])  # List of class names
    functions = Column(JSONB, default=[])  # List of function names
    dependencies = Column(JSONB, default=[])  # Import dependencies

    # Analysis
    estimated_complexity = Column(String(20), default="medium")
    business_domain = Column(String(100), nullable=True)  # Assigned domain

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<BrownPaperCodeModule(name='{self.name}', type='{self.module_type}')>"


class BrownPaperDomain(Base):
    """
    Business domain extracted from code analysis.
    Maps code modules to business concepts.
    """
    __tablename__ = "brown_paper_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Domain identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Domain content
    modules = Column(JSONB, default=[])  # Module paths
    entities = Column(JSONB, default=[])  # Entity/class names
    use_cases = Column(JSONB, default=[])  # Identified use cases

    # Analysis
    complexity = Column(String(20), default="medium")
    priority = Column(Integer, default=1)

    # Human refinement
    human_description = Column(Text, nullable=True)  # Human-provided description
    human_priority = Column(Integer, nullable=True)  # Human-adjusted priority

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<BrownPaperDomain(name='{self.name}', priority={self.priority})>"
