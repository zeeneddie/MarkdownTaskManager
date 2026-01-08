"""
Quality Gate Configuration Models

Database models for configurable quality gates:
- QualityGateConfig: Main config per project
- QualityCategoryConfig: Category settings (SIG, SOLID, etc.)
- QualityCheckConfig: Individual check settings
- QualityWorkflowRules: Per-workflow blocking rules
- QualityConfigHistory: Audit trail for changes

Author: Claude Code (Week 49 Day 1)
Date: 2025-11-24
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    ForeignKey, Enum as SQLEnum, JSON, Boolean, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from app.database import Base
import uuid


# ============================================================================
# Enums
# ============================================================================

class Severity(str, Enum):
    """Check severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ChangeType(str, Enum):
    """Types of configuration changes"""
    CATEGORY_UPDATE = "category_update"
    CHECK_UPDATE = "check_update"
    WORKFLOW_UPDATE = "workflow_update"
    RESET = "reset"
    CREATE = "create"


class EntityType(str, Enum):
    """Entity types for history tracking"""
    CATEGORY = "category"
    CHECK = "check"
    WORKFLOW = "workflow"
    CONFIG = "config"


# ============================================================================
# Models
# ============================================================================

class QualityGateConfig(Base):
    """
    Main quality gate configuration per project.

    Each project can have multiple named configs (e.g., 'default', 'strict', 'relaxed')
    but only one can be active at a time.
    """
    __tablename__ = "quality_gate_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, nullable=True)  # Optional: links to external project system
    name = Column(String(100), nullable=False, default="default")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)

    # Relationships
    categories = relationship("QualityCategoryConfig", back_populates="config", cascade="all, delete-orphan")
    checks = relationship("QualityCheckConfig", back_populates="config", cascade="all, delete-orphan")
    workflow_rules = relationship("QualityWorkflowRules", back_populates="config", cascade="all, delete-orphan")
    history = relationship("QualityConfigHistory", back_populates="config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<QualityGateConfig(id={self.id}, name='{self.name}', active={self.is_active})>"


class QualityCategoryConfig(Base):
    """
    Configuration for quality categories (SIG-TOP-10, SOLID, etc.).

    Each category can be enabled/disabled and has a target score.
    """
    __tablename__ = "quality_category_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("quality_gate_configs.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(String(50), nullable=False)  # 'sig-top-10', 'solid', etc.
    category_name = Column(String(100), nullable=True)  # Human-readable name
    enabled = Column(Boolean, default=True)
    target_score = Column(Integer, default=80)  # 0-100
    weight = Column(Float, default=1.0)  # Relative importance

    # Relationship
    config = relationship("QualityGateConfig", back_populates="categories")

    def __repr__(self):
        return f"<QualityCategoryConfig(category='{self.category_id}', enabled={self.enabled}, target={self.target_score})>"


class QualityCheckConfig(Base):
    """
    Configuration for individual quality checks.

    Each check belongs to a category and can have custom severity and thresholds.
    """
    __tablename__ = "quality_check_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("quality_gate_configs.id", ondelete="CASCADE"), nullable=False)
    check_id = Column(String(100), nullable=False)  # 'cyclomatic-complexity'
    check_name = Column(String(200), nullable=True)  # Human-readable name
    category_id = Column(String(50), nullable=False)  # Reference to category
    enabled = Column(Boolean, default=True)
    severity = Column(String(20), default="medium")  # Uses Severity enum values
    threshold_value = Column(Float, nullable=True)  # Configurable threshold
    threshold_type = Column(String(20), nullable=True)  # 'max', 'min', 'percentage'
    description = Column(Text, nullable=True)  # Check description
    fix_suggestion = Column(Text, nullable=True)  # How to fix

    # Relationship
    config = relationship("QualityGateConfig", back_populates="checks")

    def __repr__(self):
        return f"<QualityCheckConfig(check='{self.check_id}', severity={self.severity}, enabled={self.enabled})>"


class QualityWorkflowRules(Base):
    """
    Per-workflow quality rules.

    Different workflows (NEW_FEATURE, BUG, etc.) can have different
    blocking rules, coverage requirements, and validation settings.
    """
    __tablename__ = "quality_workflow_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("quality_gate_configs.id", ondelete="CASCADE"), nullable=False)
    workflow_type = Column(String(50), nullable=False)  # 'NEW_FEATURE', 'BUG', etc.
    blocking_severities = Column(ARRAY(String), default=["critical"])  # Which severities block
    required_coverage = Column(Integer, default=80)  # 0-100
    e2e_required = Column(Boolean, default=False)
    regression_required = Column(Boolean, default=False)
    documentation_required = Column(Boolean, default=False)
    max_iterations = Column(Integer, default=3)  # Max validation attempts
    stop_on_first_failure = Column(Boolean, default=True)

    # Relationship
    config = relationship("QualityGateConfig", back_populates="workflow_rules")

    def __repr__(self):
        return f"<QualityWorkflowRules(workflow='{self.workflow_type}', coverage={self.required_coverage})>"


class QualityConfigHistory(Base):
    """
    Audit trail for configuration changes.

    Tracks who changed what, when, and the before/after values.
    """
    __tablename__ = "quality_config_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("quality_gate_configs.id", ondelete="CASCADE"), nullable=False)
    changed_at = Column(DateTime, server_default=func.now())
    changed_by = Column(String(100), nullable=True)
    change_type = Column(String(50), nullable=False)  # Uses ChangeType enum values
    entity_type = Column(String(50), nullable=True)  # Uses EntityType enum values
    entity_id = Column(String(100), nullable=True)  # ID of changed entity
    old_value = Column(JSONB, nullable=True)  # Previous state
    new_value = Column(JSONB, nullable=True)  # New state
    comment = Column(Text, nullable=True)  # Optional change comment

    # Relationship
    config = relationship("QualityGateConfig", back_populates="history")

    def __repr__(self):
        return f"<QualityConfigHistory(change='{self.change_type}', at={self.changed_at})>"
