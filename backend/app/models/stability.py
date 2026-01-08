# Stability Analysis Models
# SQLAlchemy models for Fase 21: ASP Stability Analyzer
#
# Tables:
# - StabilityScan: Project-level scan records
# - StabilityFinding: Individual leak findings
# - StabilityMetric: Trend tracking over time
# - StabilityCategorySummary: Category aggregates per scan

from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Date,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class StabilityScan(Base):
    """
    Project-level stability scan record.

    Tracks overall scan results and metadata.
    """
    __tablename__ = "stability_scans"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scan_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_files_scanned = Column(Integer, default=0)
    total_files_with_issues = Column(Integer, default=0)
    categories_analyzed = Column(ARRAY(String), nullable=True)
    languages_analyzed = Column(ARRAY(String), nullable=True)
    overall_risk = Column(String(20), default="LOW")
    overall_score = Column(Integer, default=100)
    analysis_time_seconds = Column(Float, default=0.0)
    base_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    findings = relationship("StabilityFinding", back_populates="scan", cascade="all, delete-orphan")
    category_summaries = relationship("StabilityCategorySummary", back_populates="scan", cascade="all, delete-orphan")

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "CRITICAL")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "HIGH")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "scan_timestamp": self.scan_timestamp.isoformat() if self.scan_timestamp else None,
            "total_files_scanned": self.total_files_scanned,
            "total_files_with_issues": self.total_files_with_issues,
            "categories_analyzed": self.categories_analyzed,
            "languages_analyzed": self.languages_analyzed,
            "overall_risk": self.overall_risk,
            "overall_score": self.overall_score,
            "analysis_time_seconds": self.analysis_time_seconds,
            "total_findings": len(self.findings) if self.findings else 0,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
        }


class StabilityFinding(Base):
    """
    Individual stability finding (resource leak, etc.).

    Contains detailed information about each detected issue.
    """
    __tablename__ = "stability_findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("stability_scans.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    file_path = Column(Text, nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    resource_type = Column(String(50), nullable=False)
    variable_name = Column(String(255), nullable=True)
    leak_pattern = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    code_context = Column(ARRAY(Text), nullable=True)
    confidence = Column(Float, default=1.0)

    # Tracking fields
    status = Column(String(20), default="open", index=True)
    fixed_at = Column(DateTime, nullable=True)
    fixed_by = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    fix_commit_hash = Column(String(40), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    scan = relationship("StabilityScan", back_populates="findings")

    @property
    def is_critical(self) -> bool:
        return self.severity == "CRITICAL"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "category": self.category,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "resource_type": self.resource_type,
            "variable_name": self.variable_name,
            "leak_pattern": self.leak_pattern,
            "severity": self.severity,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "code_context": self.code_context,
            "confidence": self.confidence,
            "status": self.status,
            "fixed_at": self.fixed_at.isoformat() if self.fixed_at else None,
            "fix_commit_hash": self.fix_commit_hash,
            "notes": self.notes,
        }


class StabilityMetric(Base):
    """
    Daily stability metrics for trend tracking.

    Aggregated metrics per project per day.
    """
    __tablename__ = "stability_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_date = Column(Date, nullable=False, index=True)

    # Category counts
    ado_leak_count = Column(Integer, default=0)
    com_leak_count = Column(Integer, default=0)
    external_service_issues = Column(Integer, default=0)
    memory_issues = Column(Integer, default=0)
    file_leak_count = Column(Integer, default=0)
    session_issues = Column(Integer, default=0)
    exception_issues = Column(Integer, default=0)
    sql_issues = Column(Integer, default=0)

    # Aggregates
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    overall_score = Column(Integer, default=100)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('project_id', 'metric_date', name='uq_stability_metrics_project_date'),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "metric_date": self.metric_date.isoformat() if self.metric_date else None,
            "ado_leak_count": self.ado_leak_count,
            "com_leak_count": self.com_leak_count,
            "external_service_issues": self.external_service_issues,
            "memory_issues": self.memory_issues,
            "file_leak_count": self.file_leak_count,
            "session_issues": self.session_issues,
            "exception_issues": self.exception_issues,
            "sql_issues": self.sql_issues,
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "overall_score": self.overall_score,
        }


class StabilityCategorySummary(Base):
    """
    Category-level summary per scan.

    Aggregated statistics for each stability category.
    """
    __tablename__ = "stability_category_summaries"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("stability_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    issues_found = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    severity_score = Column(Integer, default=0)
    files_affected = Column(Integer, default=0)

    # Relationships
    scan = relationship("StabilityScan", back_populates="category_summaries")

    __table_args__ = (
        UniqueConstraint('scan_id', 'category', name='uq_stability_category_scan'),
    )

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "issues_found": self.issues_found,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "severity_score": self.severity_score,
            "files_affected": self.files_affected,
        }
