"""
Technical Debt Models

Database models for tracking technical debt:
- TechnicalDebtItem: Individual debt items
- TechnicalDebtSnapshot: Point-in-time debt state
- RemediationPlan: Prioritized fix plans
- DebtResolution: Resolution tracking

Author: Claude Code (Week 18 Day 1)
Date: 2025-11-22
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    ForeignKey, Enum as SQLEnum, JSON, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from app.database import Base


# ============================================================================
# Enums
# ============================================================================

class DebtType(str, Enum):
    """Types of technical debt"""
    CODE_SMELL = "code_smell"           # Bad patterns, complex code
    SECURITY = "security"                # Security vulnerabilities
    PERFORMANCE = "performance"          # Performance issues
    DEPENDENCY = "dependency"            # Outdated/vulnerable dependencies
    TEST_GAP = "test_gap"               # Missing test coverage
    DOCUMENTATION = "documentation"      # Missing/outdated docs
    ARCHITECTURE = "architecture"        # Architectural issues
    DUPLICATION = "duplication"          # Code duplication
    COMPATIBILITY = "compatibility"      # Browser/platform issues
    ACCESSIBILITY = "accessibility"      # A11y issues


class DebtSeverity(str, Enum):
    """Severity levels for debt items"""
    CRITICAL = "critical"   # Must fix immediately (blocking)
    HIGH = "high"           # Fix within current sprint
    MEDIUM = "medium"       # Fix within 2-3 sprints
    LOW = "low"             # Fix when convenient


class DebtStatus(str, Enum):
    """Status of a debt item"""
    OPEN = "open"                   # Newly detected
    ACKNOWLEDGED = "acknowledged"    # Team aware, not yet planned
    PLANNED = "planned"             # In remediation plan
    IN_PROGRESS = "in_progress"     # Being fixed
    RESOLVED = "resolved"           # Fixed
    WONT_FIX = "wont_fix"          # Accepted as-is
    FALSE_POSITIVE = "false_positive"  # Not actually debt


class DetectionSource(str, Enum):
    """How the debt was detected"""
    SCANNER_RUFF = "scanner_ruff"
    SCANNER_ESLINT = "scanner_eslint"
    SCANNER_BANDIT = "scanner_bandit"
    SCANNER_NPM_AUDIT = "scanner_npm_audit"
    SCANNER_SONAR = "scanner_sonar"
    SCANNER_COVERAGE = "scanner_coverage"
    AGENT_QUINN = "agent_quinn"
    AGENT_MARCUS = "agent_marcus"
    MANUAL = "manual"
    PR_REVIEW = "pr_review"


# ============================================================================
# Technical Debt Item
# ============================================================================

class TechnicalDebtItem(Base):
    """
    Individual technical debt item.

    Tracks a single piece of technical debt with:
    - Location (file, line, function)
    - Type and severity
    - Principal (effort to fix)
    - Interest (ongoing cost)
    - Detection and resolution info
    """
    __tablename__ = "technical_debt_items"

    id = Column(Integer, primary_key=True, index=True)

    # Identification
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Classification
    # Note: Use native_enum=False to avoid asyncpg enum serialization issues
    debt_type = Column(SQLEnum(DebtType, values_callable=lambda e: [m.value for m in e]), nullable=False, index=True)
    severity = Column(SQLEnum(DebtSeverity, values_callable=lambda e: [m.value for m in e]), nullable=False, index=True)
    status = Column(SQLEnum(DebtStatus, values_callable=lambda e: [m.value for m in e]), default=DebtStatus.OPEN, index=True)

    # Location
    file_path = Column(String(500), nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    function_name = Column(String(255), nullable=True)
    module_name = Column(String(255), nullable=True)

    # Cost metrics (in hours)
    principal = Column(Float, default=1.0)  # Effort to fix
    interest_rate = Column(Float, default=0.1)  # Cost per sprint if not fixed

    # Detection
    detected_by = Column(SQLEnum(DetectionSource, values_callable=lambda e: [m.value for m in e]), nullable=False)
    detection_rule = Column(String(255), nullable=True)  # e.g., "E501", "SQL injection"
    detection_message = Column(Text, nullable=True)
    first_detected = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    occurrence_count = Column(Integer, default=1)

    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)  # agent_id or user
    resolution_notes = Column(Text, nullable=True)
    resolution_commit = Column(String(64), nullable=True)  # Git commit hash

    # Metadata
    tags = Column(JSON, default=list)
    extra_metadata = Column("metadata", JSON, default=dict)  # Maps to 'metadata' column in DB

    # Relationships
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    snapshot_id = Column(Integer, ForeignKey("technical_debt_snapshots.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def calculate_interest(self, sprints_elapsed: int = 1) -> float:
        """Calculate accumulated interest over sprints"""
        return self.principal * self.interest_rate * sprints_elapsed

    def calculate_roi(self) -> float:
        """Calculate ROI for fixing this item (interest saved per hour invested)"""
        if self.principal <= 0:
            return 0.0
        # Assuming 6-month payback period (12 sprints)
        total_interest = self.calculate_interest(12)
        return total_interest / self.principal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "debt_type": self.debt_type.value if self.debt_type else None,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "function_name": self.function_name,
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "current_interest": self.calculate_interest(),
            "roi": self.calculate_roi(),
            "detected_by": self.detected_by.value if self.detected_by else None,
            "detection_rule": self.detection_rule,
            "first_detected": self.first_detected.isoformat() if self.first_detected else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "tags": self.tags or [],
            "metadata": self.metadata or {}
        }


# ============================================================================
# Technical Debt Snapshot
# ============================================================================

class TechnicalDebtSnapshot(Base):
    """
    Point-in-time snapshot of technical debt state.

    Captures the overall debt metrics at a specific moment,
    useful for tracking trends over time.
    """
    __tablename__ = "technical_debt_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # Timing
    timestamp = Column(DateTime, default=func.now(), index=True)
    scan_duration_seconds = Column(Float, nullable=True)

    # Aggregate metrics
    total_items = Column(Integer, default=0)
    total_principal = Column(Float, default=0.0)  # Total hours to fix all
    total_interest = Column(Float, default=0.0)   # Interest per sprint

    # Technical Debt Ratio
    productive_hours = Column(Float, default=160.0)  # Hours per sprint
    debt_ratio = Column(Float, default=0.0)  # principal / productive_hours

    # Breakdown by type
    items_by_type = Column(JSON, default=dict)  # {type: count}
    principal_by_type = Column(JSON, default=dict)  # {type: hours}

    # Breakdown by severity
    items_by_severity = Column(JSON, default=dict)  # {severity: count}
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)

    # Quality metrics (from scanners)
    code_coverage = Column(Float, nullable=True)  # 0-100
    code_duplication = Column(Float, nullable=True)  # 0-100
    security_issues = Column(Integer, default=0)
    outdated_dependencies = Column(Integer, default=0)
    avg_complexity = Column(Float, nullable=True)

    # Comparison to previous
    items_delta = Column(Integer, default=0)  # vs previous snapshot
    principal_delta = Column(Float, default=0.0)
    ratio_delta = Column(Float, default=0.0)

    # Context
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    trigger = Column(String(50), default="scheduled")  # scheduled, pr, manual
    commit_hash = Column(String(64), nullable=True)
    branch = Column(String(255), nullable=True)

    # Metadata
    scanner_versions = Column(JSON, default=dict)
    extra_metadata = Column("metadata", JSON, default=dict)  # Maps to 'metadata' column in DB

    # Relationships
    items = relationship("TechnicalDebtItem", backref="snapshot")

    def calculate_debt_ratio(self) -> float:
        """Calculate TDR as percentage"""
        if self.productive_hours <= 0:
            return 0.0
        return (self.total_principal / self.productive_hours) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "total_items": self.total_items,
            "total_principal": self.total_principal,
            "total_interest": self.total_interest,
            "debt_ratio": self.debt_ratio,
            "items_by_type": self.items_by_type or {},
            "items_by_severity": self.items_by_severity or {},
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "code_coverage": self.code_coverage,
            "code_duplication": self.code_duplication,
            "security_issues": self.security_issues,
            "outdated_dependencies": self.outdated_dependencies,
            "items_delta": self.items_delta,
            "principal_delta": self.principal_delta,
            "ratio_delta": self.ratio_delta,
            "trigger": self.trigger,
            "commit_hash": self.commit_hash
        }


# ============================================================================
# Remediation Plan
# ============================================================================

class RemediationPlan(Base):
    """
    Prioritized plan for addressing technical debt.

    Contains ordered list of debt items to fix,
    with estimated effort and expected impact.
    """
    __tablename__ = "remediation_plans"

    id = Column(Integer, primary_key=True, index=True)

    # Plan info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")  # draft, active, completed, archived

    # Timing
    created_at = Column(DateTime, default=func.now())
    start_date = Column(DateTime, nullable=True)
    target_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Scope
    target_debt_ratio = Column(Float, nullable=True)  # Goal TDR %
    max_effort_hours = Column(Float, nullable=True)   # Budget
    priority_types = Column(JSON, default=list)       # Focus areas

    # Items (ordered list of debt item IDs)
    item_ids = Column(JSON, default=list)

    # Estimates
    total_items = Column(Integer, default=0)
    total_effort_hours = Column(Float, default=0.0)
    estimated_interest_saved = Column(Float, default=0.0)  # Per sprint
    estimated_ratio_reduction = Column(Float, default=0.0)

    # Progress
    items_completed = Column(Integer, default=0)
    effort_spent_hours = Column(Float, default=0.0)
    actual_interest_saved = Column(Float, default=0.0)

    # Assignment
    assigned_agent = Column(String(50), default="marcus")  # Usually Marcus
    assigned_to = Column(String(100), nullable=True)  # Human assignee

    # Context
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    snapshot_id = Column(Integer, ForeignKey("technical_debt_snapshots.id"), nullable=True)

    # Metadata
    extra_metadata = Column("metadata", JSON, default=dict)  # Maps to 'metadata' column in DB

    def calculate_progress(self) -> float:
        """Calculate completion percentage"""
        if self.total_items <= 0:
            return 0.0
        return (self.items_completed / self.total_items) * 100

    def calculate_roi(self) -> float:
        """Calculate ROI of the plan"""
        if self.total_effort_hours <= 0:
            return 0.0
        # Assuming 12 sprint payback period
        return (self.estimated_interest_saved * 12) / self.total_effort_hours

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "target_debt_ratio": self.target_debt_ratio,
            "max_effort_hours": self.max_effort_hours,
            "total_items": self.total_items,
            "total_effort_hours": self.total_effort_hours,
            "estimated_interest_saved": self.estimated_interest_saved,
            "items_completed": self.items_completed,
            "progress": self.calculate_progress(),
            "roi": self.calculate_roi(),
            "assigned_agent": self.assigned_agent
        }


# ============================================================================
# Debt Resolution Record
# ============================================================================

class DebtResolution(Base):
    """
    Record of a debt item being resolved.

    Tracks how and when debt was addressed,
    useful for learning and metrics.
    """
    __tablename__ = "debt_resolutions"

    id = Column(Integer, primary_key=True, index=True)

    # What was resolved
    debt_item_id = Column(Integer, ForeignKey("technical_debt_items.id"), nullable=False)

    # Resolution details
    resolution_type = Column(String(50), nullable=False)  # fix, refactor, remove, accept
    resolution_notes = Column(Text, nullable=True)

    # Who resolved it
    resolved_by_agent = Column(String(50), nullable=True)  # Agent ID
    resolved_by_human = Column(String(100), nullable=True)

    # When
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, default=func.now())

    # Effort
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)

    # Code changes
    commit_hash = Column(String(64), nullable=True)
    pr_number = Column(Integer, nullable=True)
    files_changed = Column(JSON, default=list)
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)

    # Verification
    verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verification_notes = Column(Text, nullable=True)

    # Impact
    interest_eliminated = Column(Float, default=0.0)
    new_issues_introduced = Column(Integer, default=0)

    # Context
    plan_id = Column(Integer, ForeignKey("remediation_plans.id"), nullable=True)

    # Metadata
    extra_metadata = Column("metadata", JSON, default=dict)  # Maps to 'metadata' column in DB

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "debt_item_id": self.debt_item_id,
            "resolution_type": self.resolution_type,
            "resolution_notes": self.resolution_notes,
            "resolved_by_agent": self.resolved_by_agent,
            "resolved_by_human": self.resolved_by_human,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "commit_hash": self.commit_hash,
            "pr_number": self.pr_number,
            "verified": self.verified,
            "interest_eliminated": self.interest_eliminated
        }


# ============================================================================
# Quality Gate Result
# ============================================================================

class QualityGateResult(Base):
    """
    Result of a quality gate check.

    Tracks pass/fail status for each gate type,
    integrates with CI/CD pipeline.
    """
    __tablename__ = "quality_gate_results"

    id = Column(Integer, primary_key=True, index=True)

    # Context
    timestamp = Column(DateTime, default=func.now())
    trigger = Column(String(50), default="pr")  # pr, push, scheduled, manual
    commit_hash = Column(String(64), nullable=True)
    branch = Column(String(255), nullable=True)
    pr_number = Column(Integer, nullable=True)

    # Overall result
    passed = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)  # PR blocked?

    # Individual gates
    gate_results = Column(JSON, default=dict)
    # Example: {
    #   "tests": {"passed": true, "score": 100, "threshold": 100},
    #   "coverage": {"passed": true, "score": 84, "threshold": 80},
    #   "security": {"passed": false, "score": 1, "threshold": 0},
    #   "debt_ratio": {"passed": true, "score": 8.5, "threshold": 10}
    # }

    # Scores
    test_score = Column(Float, nullable=True)
    coverage_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    debt_ratio_score = Column(Float, nullable=True)

    # Failures
    failure_reasons = Column(JSON, default=list)
    blocking_issues = Column(JSON, default=list)

    # Resolution
    override_approved = Column(Boolean, default=False)
    override_by = Column(String(100), nullable=True)
    override_reason = Column(Text, nullable=True)

    # Context
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    snapshot_id = Column(Integer, ForeignKey("technical_debt_snapshots.id"), nullable=True)

    # Metadata
    duration_seconds = Column(Float, nullable=True)
    extra_metadata = Column("metadata", JSON, default=dict)  # Maps to 'metadata' column in DB

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "trigger": self.trigger,
            "commit_hash": self.commit_hash,
            "branch": self.branch,
            "pr_number": self.pr_number,
            "passed": self.passed,
            "blocked": self.blocked,
            "gate_results": self.gate_results or {},
            "test_score": self.test_score,
            "coverage_score": self.coverage_score,
            "security_score": self.security_score,
            "debt_ratio_score": self.debt_ratio_score,
            "failure_reasons": self.failure_reasons or [],
            "override_approved": self.override_approved
        }
