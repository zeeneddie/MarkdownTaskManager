"""
Gradual Rollout Models

Week 53 Day 4: Gradual Rollout System
SQLAlchemy models for managing gradual rollout of experiment winners.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.models.ab_testing import Base


class Rollout(Base):
    """Main rollout configuration and tracking."""
    __tablename__ = 'rollouts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey('experiment_variants.id', ondelete='CASCADE'), nullable=False)
    agent_id = Column(String(50), nullable=False)
    feature_name = Column(String(200), nullable=False)
    current_stage = Column(Integer, nullable=False, default=0)
    current_percentage = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default='PENDING')
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)
    rollback_reason = Column(Text, nullable=True)
    extra_metadata = Column(JSONB, nullable=True)

    # Relationships
    stages = relationship("RolloutStage", back_populates="rollout", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('current_stage >= 0 AND current_stage <= 4', name='valid_stage'),
        CheckConstraint('current_percentage >= 0.0 AND current_percentage <= 100.0', name='valid_percentage'),
        CheckConstraint(
            "status IN ('PENDING', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ROLLED_BACK')",
            name='valid_status'
        ),
    )


class RolloutStage(Base):
    """Individual stage in rollout process."""
    __tablename__ = 'rollout_stages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rollout_id = Column(UUID(as_uuid=True), ForeignKey('rollouts.id', ondelete='CASCADE'), nullable=False)
    stage_number = Column(Integer, nullable=False)
    traffic_percentage = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default='PENDING')
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    success_rate = Column(Float, nullable=True)
    baseline_success_rate = Column(Float, nullable=True)
    performance_drop = Column(Float, nullable=True)
    total_requests = Column(Integer, nullable=False, default=0)
    successful_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    health_check_passed = Column(Boolean, nullable=False, default=False)
    rollback_triggered = Column(Boolean, nullable=False, default=False)
    rollback_reason = Column(Text, nullable=True)
    extra_metadata = Column(JSONB, nullable=True)

    # Relationships
    rollout = relationship("Rollout", back_populates="stages")
    metrics = relationship("RolloutMetric", back_populates="stage", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('stage_number >= 0 AND stage_number <= 4', name='valid_stage_number'),
        CheckConstraint('traffic_percentage >= 0.0 AND traffic_percentage <= 100.0', name='valid_traffic'),
        CheckConstraint(
            "status IN ('PENDING', 'ACTIVE', 'COMPLETED', 'FAILED', 'ROLLED_BACK')",
            name='valid_stage_status'
        ),
        CheckConstraint(
            'success_rate IS NULL OR (success_rate >= 0.0 AND success_rate <= 100.0)',
            name='valid_success_rate'
        ),
        UniqueConstraint('rollout_id', 'stage_number', name='unique_rollout_stage'),
    )


class RolloutMetric(Base):
    """Detailed metrics collected during rollout."""
    __tablename__ = 'rollout_metrics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id = Column(UUID(as_uuid=True), ForeignKey('rollout_stages.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)
    threshold_value = Column(Float, nullable=True)
    threshold_breached = Column(Boolean, nullable=False, default=False)
    extra_metadata = Column(JSONB, nullable=True)

    # Relationships
    stage = relationship("RolloutStage", back_populates="metrics")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "metric_name IN ('success_rate', 'response_time', 'error_rate', 'throughput', 'cpu_usage', 'memory_usage', 'custom')",
            name='valid_metric_name'
        ),
    )
