"""
Attribution Database Models
Week 21-22 Implementation
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class TaskOutcome(Base):
    """Stores raw task outcome data for attribution analysis."""

    __tablename__ = "task_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(100), nullable=False, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    outcome_type = Column(String(20), nullable=False)
    steps_data = Column(Text)
    quality_gate_results = Column(Text)
    validation_history = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class Attribution(Base):
    """Stores attribution analysis results."""

    __tablename__ = "attributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(100), nullable=False, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    outcome = Column(String(20), nullable=False)
    key_steps = Column(Text)
    causal_factors = Column(Text)
    quality_gate_results = Column(Text)
    validation_history = Column(Text)
    confidence = Column(Float, nullable=False)
    confidence_level = Column(String(20))
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    analyzed_at = Column(DateTime, default=lambda: datetime.utcnow())


class AttributionFeedback(Base):
    """Stores feedback generated from attribution analysis."""

    __tablename__ = "attribution_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribution_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False)
    lessons = Column(Text)
    recommended_adjustments = Column(Text)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class QualityGateStats(Base):
    """Aggregated quality gate effectiveness statistics."""

    __tablename__ = "quality_gate_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_type = Column(String(50), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_checks = Column(Integer, default=0)
    issues_caught = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    effectiveness = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
