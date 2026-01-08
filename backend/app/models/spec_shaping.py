"""
Spec Shaping Models - Database models for spec iteration loop

Week 59: Agent OS Integration
Implements the "Shape → Verify → Loop" pattern from Agent OS.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.green_paper import Base


class SpecShapingSession(Base):
    """
    Tracks an overall spec shaping session.

    A session represents the full journey from initial description
    to verified specification, potentially through multiple iterations.
    """
    __tablename__ = "spec_shaping_sessions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)  # Optional link to project
    workflow_type = Column(String(50), nullable=False)  # NEW_FEATURE, BUG, etc.
    initial_description = Column(Text, nullable=False)
    current_spec = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    # Status: draft, shaping, verifying, approved, rejected, max_iterations
    iteration_count = Column(Integer, nullable=False, default=0)
    max_iterations = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    iterations = relationship("SpecIteration", back_populates="session", cascade="all, delete-orphan")


class SpecIteration(Base):
    """
    Tracks a single shape/verify cycle within a session.

    Each iteration takes an input spec, shapes it, and produces an output spec.
    """
    __tablename__ = "spec_iterations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("spec_shaping_sessions.id", ondelete="CASCADE"), nullable=False)
    iteration_number = Column(Integer, nullable=False)
    input_spec = Column(Text, nullable=False)
    output_spec = Column(Text, nullable=True)
    shaping_prompt = Column(Text, nullable=True)  # The prompt used for shaping
    agent_used = Column(String(50), nullable=True)  # Felix, Quinn, etc.
    llm_model = Column(String(100), nullable=True)  # qwen2.5-coder:7b, etc.
    tokens_used = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("SpecShapingSession", back_populates="iterations")
    verifications = relationship("SpecVerification", back_populates="iteration", cascade="all, delete-orphan")


class SpecVerification(Base):
    """
    Tracks a single quality check result for an iteration.

    Multiple verifications per iteration (one per quality check).
    """
    __tablename__ = "spec_verifications"

    id = Column(Integer, primary_key=True, index=True)
    iteration_id = Column(Integer, ForeignKey("spec_iterations.id", ondelete="CASCADE"), nullable=False)
    check_name = Column(String(100), nullable=False)  # e.g., "completeness", "clarity"
    check_category = Column(String(50), nullable=False)  # e.g., "structure", "content", "feasibility"
    passed = Column(Boolean, nullable=False)
    score = Column(Float, nullable=True)  # 0.0 - 1.0
    message = Column(Text, nullable=True)  # Explanation
    suggestions = Column(Text, nullable=True)  # Improvement suggestions
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    iteration = relationship("SpecIteration", back_populates="verifications")
