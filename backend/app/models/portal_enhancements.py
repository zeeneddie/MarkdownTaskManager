# backend/app/models/portal_enhancements.py
"""
Portal Enhancement Models - Week 118

Client Portal 2.0 Phase 2: Transparency & Control
- Priority Boost System
- Duplicate Detection
- Impact Preview (Felix)
"""

from datetime import datetime, date, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class CustomerTier(str, Enum):
    """Customer subscription tier."""
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class BoostStatus(str, Enum):
    """Priority boost status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    COMPLETED = "completed"


class DuplicateStatus(str, Enum):
    """Duplicate detection status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    MERGED = "merged"


class ImpactLevel(str, Enum):
    """Impact severity level."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Risk assessment level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BoostAllowance(Base):
    """Monthly boost allowance per customer."""
    __tablename__ = "boost_allowances"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, index=True)

    # Allowance period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Quota
    total_boosts = Column(Integer, default=1)
    used_boosts = Column(Integer, default=0)
    remaining_boosts = Column(Integer, default=1)

    # Tier determines quota
    tier = Column(String(20), default=CustomerTier.STANDARD.value)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    boosts = relationship("PriorityBoost", back_populates="allowance")

    def can_boost(self) -> bool:
        """Check if customer can use a boost."""
        return self.remaining_boosts > 0

    def use_boost(self) -> bool:
        """Use one boost from allowance."""
        if self.can_boost():
            self.used_boosts += 1
            self.remaining_boosts -= 1
            return True
        return False

    @classmethod
    def get_tier_quota(cls, tier: str) -> int:
        """Get boost quota for tier."""
        quotas = {
            CustomerTier.STANDARD.value: 1,
            CustomerTier.PREMIUM.value: 3,
            CustomerTier.ENTERPRISE.value: 10,
        }
        return quotas.get(tier, 1)


class PriorityBoost(Base):
    """Individual priority boost usage."""
    __tablename__ = "priority_boosts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    allowance_id = Column(PGUUID(as_uuid=True), ForeignKey('boost_allowances.id', ondelete='CASCADE'), nullable=False)

    # What was boosted
    feature_request_id = Column(Integer, nullable=False, index=True)
    feature_title = Column(String(200), nullable=True)

    # Boost details
    customer_id = Column(String(100), nullable=False, index=True)
    reason = Column(Text, nullable=True)

    # Priority change
    original_priority = Column(String(20), nullable=True)
    boosted_priority = Column(String(20), nullable=True)
    priority_delta = Column(Integer, default=1)

    # Effect tracking
    status = Column(String(20), default=BoostStatus.ACTIVE.value)
    expires_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    allowance = relationship("BoostAllowance", back_populates="boosts")


class FeatureDuplicate(Base):
    """Detected duplicate/similar features."""
    __tablename__ = "feature_duplicates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)

    # Original feature
    source_feature_id = Column(Integer, nullable=False, index=True)
    source_title = Column(String(200), nullable=True)
    source_description = Column(Text, nullable=True)

    # Duplicate candidate
    duplicate_feature_id = Column(Integer, nullable=False, index=True)
    duplicate_title = Column(String(200), nullable=True)
    duplicate_description = Column(Text, nullable=True)

    # Similarity metrics
    similarity_score = Column(Float, nullable=False)
    detection_method = Column(String(30), default='chromadb')
    embedding_model = Column(String(50), nullable=True)

    # Matching details
    matching_keywords = Column(JSONB, default=list)
    matching_entities = Column(JSONB, default=list)

    # Resolution
    status = Column(String(20), default=DuplicateStatus.PENDING.value)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    merge_target_id = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def is_high_confidence(self, threshold: float = 0.85) -> bool:
        """Check if this is a high-confidence duplicate."""
        return self.similarity_score >= threshold


class FeatureImpactPreview(Base):
    """Felix impact analysis for feature requests."""
    __tablename__ = "feature_impact_previews"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_request_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)

    # Analysis metadata
    analyzer_agent = Column(String(30), default='felix')
    analysis_version = Column(String(20), default='1.0')

    # Impact categories
    architecture_impact = Column(String(20), nullable=True)
    security_impact = Column(String(20), nullable=True)
    performance_impact = Column(String(20), nullable=True)
    ux_impact = Column(String(20), nullable=True)
    data_impact = Column(String(20), nullable=True)

    # Overall assessment
    overall_impact = Column(String(20), default=ImpactLevel.MEDIUM.value)
    risk_level = Column(String(20), default=RiskLevel.LOW.value)
    complexity_score = Column(Integer, nullable=True)

    # Detailed analysis
    affected_components = Column(JSONB, default=list)
    affected_apis = Column(JSONB, default=list)
    dependencies = Column(JSONB, default=list)
    breaking_changes = Column(JSONB, default=list)

    # Recommendations
    implementation_approach = Column(Text, nullable=True)
    recommended_priority = Column(String(20), nullable=True)
    estimated_effort_hours = Column(Integer, nullable=True)
    suggested_sprint = Column(String(50), nullable=True)

    # Warnings and notes
    warnings = Column(JSONB, default=list)
    notes = Column(Text, nullable=True)

    # LLM details
    llm_provider = Column(String(30), nullable=True)
    llm_model = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Cache management
    is_stale = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def has_breaking_changes(self) -> bool:
        """Check if this feature has breaking changes."""
        return len(self.breaking_changes or []) > 0

    def is_high_risk(self) -> bool:
        """Check if this is high risk."""
        return self.risk_level == RiskLevel.HIGH.value or self.overall_impact in [
            ImpactLevel.HIGH.value,
            ImpactLevel.CRITICAL.value
        ]

    def get_impact_summary(self) -> dict:
        """Get a summary of all impact categories."""
        return {
            "architecture": self.architecture_impact,
            "security": self.security_impact,
            "performance": self.performance_impact,
            "ux": self.ux_impact,
            "data": self.data_impact,
            "overall": self.overall_impact,
            "risk": self.risk_level,
            "complexity": self.complexity_score,
        }
