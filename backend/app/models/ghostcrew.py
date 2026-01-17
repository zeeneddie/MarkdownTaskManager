"""
GhostCrew Security Models - Week 80-82

Database models for security scanning, vulnerability tracking,
pattern learning, and compliance checking.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class GhostCrewScan(Base):
    """Security scan sessions."""
    __tablename__ = "ghostcrew_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    workflow_type = Column(String(50), nullable=True)  # QUALITY_AUDIT, BROWN_PAPER, MIGRATION, etc.
    workflow_session_id = Column(String(100), nullable=True)  # Link to workflow session
    scan_mode = Column(String(50), nullable=False)  # assist, autonomous, crew
    scan_type = Column(String(50), nullable=False)  # full, quick, targeted, compliance
    target_path = Column(String(500), nullable=True)
    target_type = Column(String(50), nullable=True)  # repository, directory, file, url
    status = Column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Findings summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)

    # Security score
    security_score = Column(Float, nullable=True)  # 0-100
    risk_level = Column(String(20), nullable=True)  # critical, high, medium, low

    # Configuration & results
    scan_config = Column(JSONB, default=dict)
    agents_used = Column(JSONB, default=list)
    tools_used = Column(JSONB, default=list)
    scan_summary = Column(Text, nullable=True)
    recommendations = Column(JSONB, default=list)
    scan_metadata = Column(JSONB, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    # Relationships
    findings = relationship("SecurityFinding", back_populates="scan", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="scan", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "workflow_type": self.workflow_type,
            "workflow_session_id": self.workflow_session_id,
            "scan_mode": self.scan_mode,
            "scan_type": self.scan_type,
            "target_path": self.target_path,
            "target_type": self.target_type,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "security_score": self.security_score,
            "risk_level": self.risk_level,
            "agents_used": self.agents_used,
            "tools_used": self.tools_used,
            "scan_summary": self.scan_summary,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SecurityFinding(Base):
    """Individual vulnerability findings."""
    __tablename__ = "security_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("ghostcrew_scans.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    # Classification
    finding_type = Column(String(100), nullable=False)  # sql_injection, xss, hardcoded_secret, etc.
    category = Column(String(50), nullable=False)  # injection, auth, crypto, config, etc.
    severity = Column(String(20), nullable=False)  # critical, high, medium, low, info
    confidence = Column(String(20), nullable=False)  # high, medium, low

    # OWASP/CWE mapping
    owasp_category = Column(String(50), nullable=True)  # A01:2021, A02:2021, etc.
    cwe_id = Column(String(20), nullable=True)  # CWE-89, CWE-79, etc.
    cvss_score = Column(Float, nullable=True)  # 0-10

    # Location
    file_path = Column(String(500), nullable=True)
    line_number = Column(Integer, nullable=True)
    column_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    function_name = Column(String(200), nullable=True)
    class_name = Column(String(200), nullable=True)

    # Description
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    references = Column(JSONB, default=list)

    # Status tracking
    status = Column(String(50), default="open")  # open, confirmed, false_positive, fixed, accepted_risk
    verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    fixed_at = Column(DateTime, nullable=True)
    fixed_in_commit = Column(String(40), nullable=True)

    # Agent info
    detected_by_agent = Column(String(100), nullable=True)
    detection_method = Column(String(100), nullable=True)
    finding_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("GhostCrewScan", back_populates="findings")
    learnings = relationship("VulnerabilityLearning", back_populates="finding", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "scan_id": str(self.scan_id),
            "project_id": self.project_id,
            "finding_type": self.finding_type,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "owasp_category": self.owasp_category,
            "cwe_id": self.cwe_id,
            "cvss_score": self.cvss_score,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "remediation": self.remediation,
            "status": self.status,
            "verified": self.verified,
            "detected_by_agent": self.detected_by_agent,
            "detection_method": self.detection_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ShadowPattern(Base):
    """Learned vulnerability patterns (ShadowGraph)."""
    __tablename__ = "shadow_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pattern_name = Column(String(200), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # vulnerability, false_positive, secure_pattern
    category = Column(String(50), nullable=False)
    language = Column(String(50), nullable=True)  # python, javascript, java, etc.
    framework = Column(String(100), nullable=True)  # django, fastapi, react, etc.

    # Pattern definition
    pattern_regex = Column(Text, nullable=True)
    ast_pattern = Column(JSONB, nullable=True)
    semantic_pattern = Column(Text, nullable=True)
    code_examples = Column(JSONB, default=list)

    # Classification
    severity = Column(String(20), nullable=True)
    owasp_mapping = Column(String(50), nullable=True)
    cwe_mapping = Column(String(20), nullable=True)

    # Learning metrics
    times_detected = Column(Integer, default=0)
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    accuracy_score = Column(Float, nullable=True)
    last_detection = Column(DateTime, nullable=True)

    # Source
    source = Column(String(50), default="learned")  # learned, manual, imported
    learned_from_scans = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    pattern_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    learnings = relationship("VulnerabilityLearning", back_populates="pattern")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "pattern_name": self.pattern_name,
            "pattern_type": self.pattern_type,
            "category": self.category,
            "language": self.language,
            "framework": self.framework,
            "severity": self.severity,
            "owasp_mapping": self.owasp_mapping,
            "cwe_mapping": self.cwe_mapping,
            "times_detected": self.times_detected,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "accuracy_score": self.accuracy_score,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VulnerabilityLearning(Base):
    """False positive tracking and continuous learning."""
    __tablename__ = "vulnerability_learnings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("security_findings.id", ondelete="CASCADE"), nullable=True)
    pattern_id = Column(UUID(as_uuid=True), ForeignKey("shadow_patterns.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    # Learning type
    learning_type = Column(String(50), nullable=False)  # false_positive, confirmed_vuln, new_pattern, pattern_refinement
    original_classification = Column(String(50), nullable=True)
    corrected_classification = Column(String(50), nullable=True)

    # Context
    code_context = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    language = Column(String(50), nullable=True)
    framework = Column(String(100), nullable=True)

    # Feedback
    feedback_source = Column(String(50), nullable=False)  # human, agent, automated
    feedback_reason = Column(Text, nullable=True)
    feedback_by = Column(String(100), nullable=True)

    # Impact
    applied_to_pattern = Column(Boolean, default=False)
    pattern_updated_at = Column(DateTime, nullable=True)
    prevents_future_fp = Column(Boolean, default=False)
    learning_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    finding = relationship("SecurityFinding", back_populates="learnings")
    pattern = relationship("ShadowPattern", back_populates="learnings")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "finding_id": str(self.finding_id) if self.finding_id else None,
            "pattern_id": str(self.pattern_id) if self.pattern_id else None,
            "project_id": self.project_id,
            "learning_type": self.learning_type,
            "original_classification": self.original_classification,
            "corrected_classification": self.corrected_classification,
            "feedback_source": self.feedback_source,
            "feedback_reason": self.feedback_reason,
            "applied_to_pattern": self.applied_to_pattern,
            "prevents_future_fp": self.prevents_future_fp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ComplianceCheck(Base):
    """Compliance audit results (GDPR, SOC2, etc.)."""
    __tablename__ = "compliance_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("ghostcrew_scans.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    # Compliance framework
    framework = Column(String(50), nullable=False)  # GDPR, SOC2, HIPAA, PCI_DSS, ISO27001
    framework_version = Column(String(20), nullable=True)
    check_type = Column(String(100), nullable=False)

    # Results
    status = Column(String(50), default="pending")  # pending, passed, failed, partial, not_applicable
    overall_score = Column(Float, nullable=True)
    controls_total = Column(Integer, default=0)
    controls_passed = Column(Integer, default=0)
    controls_failed = Column(Integer, default=0)
    controls_partial = Column(Integer, default=0)
    controls_na = Column(Integer, default=0)

    # Details
    control_results = Column(JSONB, default=list)
    gaps_identified = Column(JSONB, default=list)
    recommendations = Column(JSONB, default=list)
    evidence_collected = Column(JSONB, default=list)

    # Audit info
    audited_by_agent = Column(String(100), nullable=True)
    audit_notes = Column(Text, nullable=True)
    next_audit_date = Column(DateTime, nullable=True)
    compliance_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    scan = relationship("GhostCrewScan", back_populates="compliance_checks")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "scan_id": str(self.scan_id) if self.scan_id else None,
            "project_id": self.project_id,
            "framework": self.framework,
            "framework_version": self.framework_version,
            "check_type": self.check_type,
            "status": self.status,
            "overall_score": self.overall_score,
            "controls_total": self.controls_total,
            "controls_passed": self.controls_passed,
            "controls_failed": self.controls_failed,
            "gaps_identified": self.gaps_identified,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class SecurityKnowledge(Base):
    """OWASP/CWE knowledge base entries."""
    __tablename__ = "security_knowledge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    knowledge_type = Column(String(50), nullable=False)  # owasp, cwe, best_practice, pattern
    identifier = Column(String(50), nullable=False, unique=True)  # A01:2021, CWE-89, etc.
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)

    # Risk info
    severity_default = Column(String(20), nullable=True)
    likelihood = Column(String(20), nullable=True)
    impact_description = Column(Text, nullable=True)

    # Remediation
    remediation_guidance = Column(Text, nullable=True)
    code_examples_vulnerable = Column(JSONB, default=list)
    code_examples_secure = Column(JSONB, default=list)
    prevention_techniques = Column(JSONB, default=list)

    # References
    external_references = Column(JSONB, default=list)
    related_cwes = Column(JSONB, default=list)
    related_owasp = Column(JSONB, default=list)

    # Metadata
    languages_affected = Column(JSONB, default=list)
    frameworks_affected = Column(JSONB, default=list)
    detection_methods = Column(JSONB, default=list)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "knowledge_type": self.knowledge_type,
            "identifier": self.identifier,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "severity_default": self.severity_default,
            "likelihood": self.likelihood,
            "remediation_guidance": self.remediation_guidance,
            "code_examples_vulnerable": self.code_examples_vulnerable,
            "code_examples_secure": self.code_examples_secure,
            "languages_affected": self.languages_affected,
            "is_active": self.is_active,
        }
