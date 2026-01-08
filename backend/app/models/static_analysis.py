# backend/app/models/static_analysis.py
"""
SQLAlchemy models for Static Analysis - Fase 15.

Tables:
- static_analysis_results: Main analysis results
- business_rules: Extracted business rules
- nfr_detections: Non-functional requirement patterns
- compliance_violations: Compliance framework violations
- variable_classifications: Variable type classifications
- program_slices: Program slicing results
- static_llm_conflicts: Conflicts between static and LLM analysis
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class StaticAnalysisResult(Base):
    """Main static analysis result record."""
    __tablename__ = 'static_analysis_results'

    id = Column(String(36), primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default='completed')
    total_files_analyzed = Column(Integer, nullable=False, default=0)
    total_lines_of_code = Column(Integer, nullable=False, default=0)
    domain_coverage = Column(Float, nullable=False, default=0.0)
    nfr_coverage = Column(Float, nullable=False, default=0.0)
    compliance_score = Column(Float, nullable=False, default=0.0)
    config = Column(JSONB, nullable=True)
    summary = Column(JSONB, nullable=True)
    errors = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    project = relationship('Project', back_populates='static_analyses')
    business_rules = relationship('BusinessRule', back_populates='analysis', cascade='all, delete-orphan')
    nfr_detections = relationship('NFRDetection', back_populates='analysis', cascade='all, delete-orphan')
    compliance_violations = relationship('ComplianceViolation', back_populates='analysis', cascade='all, delete-orphan')
    variable_classifications = relationship('VariableClassification', back_populates='analysis', cascade='all, delete-orphan')
    program_slices = relationship('ProgramSlice', back_populates='analysis', cascade='all, delete-orphan')
    conflicts = relationship('StaticAnalysisConflict', back_populates='analysis', cascade='all, delete-orphan')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'project_id': self.project_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'total_files_analyzed': self.total_files_analyzed,
            'total_lines_of_code': self.total_lines_of_code,
            'domain_coverage': self.domain_coverage,
            'nfr_coverage': self.nfr_coverage,
            'compliance_score': self.compliance_score,
            'config': self.config,
            'summary': self.summary,
            'errors': self.errors,
        }


class BusinessRule(Base):
    """Extracted business rule."""
    __tablename__ = 'business_rules'

    id = Column(String(20), primary_key=True)
    analysis_id = Column(String(36), ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False)
    rule_type = Column(String(20), nullable=False)
    condition = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    source_file = Column(String(500), nullable=False)
    source_line_start = Column(Integer, nullable=False)
    source_line_end = Column(Integer, nullable=False)
    variables_involved = Column(JSONB, nullable=True)
    confidence = Column(Float, nullable=False)
    natural_language = Column(Text, nullable=False)
    compliance_tags = Column(JSONB, nullable=True)
    llm_validated = Column(Boolean, default=False)
    llm_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    analysis = relationship('StaticAnalysisResult', back_populates='business_rules')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'rule_type': self.rule_type,
            'condition': self.condition,
            'action': self.action,
            'source_file': self.source_file,
            'source_lines': [self.source_line_start, self.source_line_end],
            'variables_involved': self.variables_involved,
            'confidence': self.confidence,
            'natural_language': self.natural_language,
            'compliance_tags': self.compliance_tags,
            'llm_validated': self.llm_validated,
            'llm_confidence': self.llm_confidence,
        }


class NFRDetection(Base):
    """Non-functional requirement detection."""
    __tablename__ = 'nfr_detections'

    id = Column(String(20), primary_key=True)
    analysis_id = Column(String(36), ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(30), nullable=False)
    pattern_matched = Column(String(100), nullable=False)
    source_file = Column(String(500), nullable=False)
    source_line = Column(Integer, nullable=False)
    code_snippet = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    compliance_relevance = Column(JSONB, nullable=True)
    llm_validated = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    analysis = relationship('StaticAnalysisResult', back_populates='nfr_detections')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'category': self.category,
            'pattern_matched': self.pattern_matched,
            'source_file': self.source_file,
            'source_line': self.source_line,
            'code_snippet': self.code_snippet,
            'confidence': self.confidence,
            'description': self.description,
            'recommendation': self.recommendation,
            'compliance_relevance': self.compliance_relevance,
            'llm_validated': self.llm_validated,
        }


class ComplianceViolation(Base):
    """Compliance framework violation."""
    __tablename__ = 'compliance_violations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False)
    requirement_id = Column(String(50), nullable=False)
    framework = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)
    violation_type = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=True)
    line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    remediation = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    analysis = relationship('StaticAnalysisResult', back_populates='compliance_violations')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'requirement_id': self.requirement_id,
            'framework': self.framework,
            'title': self.title,
            'category': self.category,
            'violation_type': self.violation_type,
            'severity': self.severity,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'code_snippet': self.code_snippet,
            'remediation': self.remediation,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
        }


class VariableClassification(Base):
    """Variable type classification."""
    __tablename__ = 'variable_classifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(200), nullable=False)
    variable_type = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    context = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    analysis = relationship('StaticAnalysisResult', back_populates='variable_classifications')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'name': self.name,
            'variable_type': self.variable_type,
            'confidence': self.confidence,
            'context': self.context,
            'reasoning': self.reasoning,
        }


class ProgramSlice(Base):
    """Program slicing result."""
    __tablename__ = 'program_slices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=False)
    variable_name = Column(String(200), nullable=False)
    direction = Column(String(20), nullable=False)
    statements = Column(JSONB, nullable=True)
    variables = Column(JSONB, nullable=True)
    functions_involved = Column(JSONB, nullable=True)
    files_involved = Column(JSONB, nullable=True)
    slice_size = Column(Integer, nullable=False)
    complexity_score = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    analysis = relationship('StaticAnalysisResult', back_populates='program_slices')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'variable_name': self.variable_name,
            'direction': self.direction,
            'statements': self.statements,
            'variables': self.variables,
            'functions_involved': self.functions_involved,
            'files_involved': self.files_involved,
            'slice_size': self.slice_size,
            'complexity_score': self.complexity_score,
        }


class StaticAnalysisConflict(Base):
    """Conflict between static and LLM analysis for static analysis results."""
    __tablename__ = 'static_analysis_conflicts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False)
    finding_type = Column(String(30), nullable=False)
    finding_id = Column(String(50), nullable=False)
    static_confidence = Column(Float, nullable=False)
    llm_confidence = Column(Float, nullable=True)
    conflict_type = Column(String(30), nullable=False)
    static_result = Column(JSONB, nullable=True)
    llm_result = Column(JSONB, nullable=True)
    resolution = Column(String(30), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    analysis = relationship('StaticAnalysisResult', back_populates='conflicts')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'finding_type': self.finding_type,
            'finding_id': self.finding_id,
            'static_confidence': self.static_confidence,
            'llm_confidence': self.llm_confidence,
            'conflict_type': self.conflict_type,
            'static_result': self.static_result,
            'llm_result': self.llm_result,
            'resolution': self.resolution,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
        }
