"""
A/B Testing Models for Agent Evolution

Tracks experiments, variants, and results for continuous evolution.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Experiment(Base):
    """
    An A/B test experiment for an agent feature.

    Lifecycle: DRAFT -> ACTIVE -> COMPLETED/CANCELLED
    Can be PAUSED temporarily.
    """
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False, index=True)
    feature_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Status with CHECK constraint
    status = Column(String(20), nullable=False, default="DRAFT")

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Winner tracking
    winner_variant_id = Column(UUID(as_uuid=True), ForeignKey('experiment_variants.id'), nullable=True)

    # Extra metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    extra_metadata = Column(JSONB, nullable=True, default={})

    # Relationships
    variants = relationship("ExperimentVariant", back_populates="experiment", foreign_keys="ExperimentVariant.experiment_id")
    winner_variant = relationship("ExperimentVariant", foreign_keys=[winner_variant_id], post_update=True)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')",
            name='check_experiment_status'
        ),
        Index('idx_experiment_agent_status', 'agent_id', 'status'),
    )

    def __repr__(self):
        return f"<Experiment {self.id} agent={self.agent_id} feature={self.feature_name} status={self.status}>"


class ExperimentVariant(Base):
    """
    A variant in an A/B test experiment.

    Contains configuration and traffic allocation percentage.
    """
    __tablename__ = "experiment_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False, index=True)

    variant_name = Column(String(100), nullable=False)  # e.g., "control", "variant_a"
    description = Column(Text, nullable=True)

    # Traffic allocation (must sum to 100 across variants)
    traffic_percentage = Column(Float, nullable=False)

    # Configuration JSON (agent-specific config)
    config_json = Column(JSONB, nullable=False, default={})

    # Is this the control/baseline variant?
    is_control = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    experiment = relationship("Experiment", back_populates="variants", foreign_keys=[experiment_id])
    results = relationship("ExperimentResult", back_populates="variant", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('traffic_percentage >= 0 AND traffic_percentage <= 100', name='check_traffic_percentage'),
        Index('idx_variant_experiment', 'experiment_id'),
    )

    def __repr__(self):
        return f"<ExperimentVariant {self.id} name={self.variant_name} traffic={self.traffic_percentage}%>"


class ExperimentResult(Base):
    """
    A single result/outcome from an experiment variant.

    Tracks task execution success and metrics.
    """
    __tablename__ = "experiment_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variant_id = Column(UUID(as_uuid=True), ForeignKey('experiment_variants.id', ondelete='CASCADE'), nullable=False, index=True)

    # Task tracking
    task_id = Column(String(100), nullable=False, index=True)
    work_type = Column(String(50), nullable=True)

    # Outcome
    success = Column(Boolean, nullable=False)

    # Metrics (JSON with flexible schema)
    metrics_json = Column(JSONB, nullable=False, default={})
    # Example metrics:
    # {
    #   "success_rate": 0.95,
    #   "estimation_accuracy": 0.85,
    #   "code_quality_score": 8.5,
    #   "execution_time_ms": 1500,
    #   "retry_count": 1
    # }

    # Error tracking (if success=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    variant = relationship("ExperimentVariant", back_populates="results")

    # Indexes
    __table_args__ = (
        Index('idx_result_variant_created', 'variant_id', 'created_at'),
        Index('idx_result_task', 'task_id'),
    )

    def __repr__(self):
        return f"<ExperimentResult {self.id} variant={self.variant_id} success={self.success}>"
