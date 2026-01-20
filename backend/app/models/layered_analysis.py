"""
Layered Analysis Service Models

Week 77: Complete analysis with 100% coverage, SWOT generation,
VBScript support, and Stored Procedure analysis.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class LayeredAnalysisSession(Base):
    """Main orchestration table for layered analysis sessions."""

    __tablename__ = 'layered_analysis_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey('project_assessments.id', ondelete='SET NULL'), nullable=True)

    # Session metadata
    name = Column(String(255), nullable=False)
    source_path = Column(Text)
    analysis_depth = Column(String(20), default='standard')  # quick, standard, deep

    # Coverage metrics
    total_files = Column(Integer, default=0)
    analyzed_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    analyzed_lines = Column(Integer, default=0)
    coverage_percentage = Column(Numeric(5, 2), default=0)

    # Detected technologies
    detected_stack = Column(JSONB, default=dict)
    has_vbscript = Column(Boolean, default=False)
    has_stored_procedures = Column(Boolean, default=False)

    # Status
    status = Column(String(30), default='pending')
    current_phase = Column(String(50))
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    vbscript_analysis = relationship("VBScriptAnalysis", back_populates="session", uselist=False, cascade="all, delete-orphan")
    stored_procedure_analysis = relationship("StoredProcedureAnalysis", back_populates="session", uselist=False, cascade="all, delete-orphan")
    swot_analysis = relationship("SWOTAnalysis", back_populates="session", uselist=False, cascade="all, delete-orphan")
    improvement_items = relationship("ImprovementItem", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("AnalysisReport", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "application_id": self.application_id,
            "name": self.name,
            "source_path": self.source_path,
            "analysis_depth": self.analysis_depth,
            "total_files": self.total_files,
            "analyzed_files": self.analyzed_files,
            "total_lines": self.total_lines,
            "analyzed_lines": self.analyzed_lines,
            "coverage_percentage": float(self.coverage_percentage) if self.coverage_percentage else 0,
            "detected_stack": self.detected_stack,
            "has_vbscript": self.has_vbscript,
            "has_stored_procedures": self.has_stored_procedures,
            "status": self.status,
            "current_phase": self.current_phase,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VBScriptAnalysis(Base):
    """Classic ASP/VBScript specific analysis results."""

    __tablename__ = 'vbscript_analysis'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False)

    # File inventory
    asp_files = Column(Integer, default=0)
    vbs_files = Column(Integer, default=0)
    inc_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)

    # Extraction counts
    functions_count = Column(Integer, default=0)
    subs_count = Column(Integer, default=0)
    includes_count = Column(Integer, default=0)
    com_objects_count = Column(Integer, default=0)
    sql_patterns_count = Column(Integer, default=0)

    # Detailed extractions
    functions = Column(JSONB, default=list)
    subs = Column(JSONB, default=list)
    includes = Column(JSONB, default=list)
    com_objects = Column(JSONB, default=list)
    sql_patterns = Column(JSONB, default=list)

    # Dependency graphs
    include_graph = Column(JSONB, default=dict)
    com_dependency_graph = Column(JSONB, default=dict)
    data_flow_graph = Column(JSONB, default=dict)

    # Security findings
    sql_injection_risks = Column(JSONB, default=list)
    xss_risks = Column(JSONB, default=list)
    session_issues = Column(JSONB, default=list)
    error_handling_issues = Column(JSONB, default=list)

    # Metrics
    complexity_score = Column(Integer)
    maintainability_score = Column(Integer)
    security_score = Column(Integer)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("LayeredAnalysisSession", back_populates="vbscript_analysis")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "file_inventory": {
                "asp_files": self.asp_files,
                "vbs_files": self.vbs_files,
                "inc_files": self.inc_files,
                "total_lines": self.total_lines,
            },
            "extraction_counts": {
                "functions": self.functions_count,
                "subs": self.subs_count,
                "includes": self.includes_count,
                "com_objects": self.com_objects_count,
                "sql_patterns": self.sql_patterns_count,
            },
            "functions": self.functions,
            "subs": self.subs,
            "includes": self.includes,
            "com_objects": self.com_objects,
            "sql_patterns": self.sql_patterns,
            "include_graph": self.include_graph,
            "security_findings": {
                "sql_injection_risks": self.sql_injection_risks,
                "xss_risks": self.xss_risks,
                "session_issues": self.session_issues,
                "error_handling_issues": self.error_handling_issues,
            },
            "scores": {
                "complexity": self.complexity_score,
                "maintainability": self.maintainability_score,
                "security": self.security_score,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StoredProcedureAnalysis(Base):
    """Database stored procedure/function analysis results."""

    __tablename__ = 'stored_procedure_analysis'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False)

    # Database info
    database_type = Column(String(50))  # sql_server, oracle, postgresql, mysql
    database_name = Column(String(255))
    schema_name = Column(String(255))

    # Inventory counts
    stored_procedures_count = Column(Integer, default=0)
    functions_count = Column(Integer, default=0)
    triggers_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)

    # Detailed inventory
    stored_procedures = Column(JSONB, default=list)
    functions = Column(JSONB, default=list)
    triggers = Column(JSONB, default=list)
    views = Column(JSONB, default=list)

    # Dependency analysis
    sp_dependencies = Column(JSONB, default=dict)
    table_usage = Column(JSONB, default=dict)
    cross_database_calls = Column(JSONB, default=list)

    # Business logic extraction
    business_rules = Column(JSONB, default=list)
    data_transformations = Column(JSONB, default=list)
    validation_logic = Column(JSONB, default=list)

    # Complexity metrics
    complexity_distribution = Column(JSONB, default=dict)
    most_complex_sps = Column(JSONB, default=list)
    most_called_sps = Column(JSONB, default=list)

    # Migration indicators
    vendor_specific_features = Column(JSONB, default=list)
    deprecated_syntax = Column(JSONB, default=list)
    performance_concerns = Column(JSONB, default=list)

    # Scores
    overall_complexity_score = Column(Integer)
    migration_difficulty_score = Column(Integer)
    business_logic_coverage = Column(Integer)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("LayeredAnalysisSession", back_populates="stored_procedure_analysis")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "database_info": {
                "type": self.database_type,
                "name": self.database_name,
                "schema": self.schema_name,
            },
            "inventory": {
                "stored_procedures": self.stored_procedures_count,
                "functions": self.functions_count,
                "triggers": self.triggers_count,
                "views": self.views_count,
                "total_lines": self.total_lines,
            },
            "stored_procedures": self.stored_procedures,
            "functions": self.functions,
            "triggers": self.triggers,
            "views": self.views,
            "dependencies": {
                "sp_dependencies": self.sp_dependencies,
                "table_usage": self.table_usage,
                "cross_database_calls": self.cross_database_calls,
            },
            "business_logic": {
                "business_rules": self.business_rules,
                "data_transformations": self.data_transformations,
                "validation_logic": self.validation_logic,
            },
            "complexity": {
                "distribution": self.complexity_distribution,
                "most_complex": self.most_complex_sps,
                "most_called": self.most_called_sps,
            },
            "migration_indicators": {
                "vendor_specific": self.vendor_specific_features,
                "deprecated": self.deprecated_syntax,
                "performance_concerns": self.performance_concerns,
            },
            "scores": {
                "complexity": self.overall_complexity_score,
                "migration_difficulty": self.migration_difficulty_score,
                "business_logic_coverage": self.business_logic_coverage,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SWOTAnalysis(Base):
    """SWOT (Strength/Weakness/Opportunity/Threat) analysis results."""

    __tablename__ = 'swot_analysis'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False)

    # SWOT Matrix
    strengths = Column(JSONB, default=list)
    weaknesses = Column(JSONB, default=list)
    opportunities = Column(JSONB, default=list)
    threats = Column(JSONB, default=list)

    # Categorized findings
    architecture_findings = Column(JSONB, default=dict)
    code_quality_findings = Column(JSONB, default=dict)
    security_findings = Column(JSONB, default=dict)
    performance_findings = Column(JSONB, default=dict)
    maintainability_findings = Column(JSONB, default=dict)
    database_findings = Column(JSONB, default=dict)

    # Prioritization
    prioritized_weaknesses = Column(JSONB, default=list)
    quick_wins = Column(JSONB, default=list)
    strategic_items = Column(JSONB, default=list)

    # Summary scores
    overall_health_score = Column(Integer)
    technical_debt_score = Column(Integer)
    modernization_readiness = Column(Integer)

    # Recommendations
    top_recommendations = Column(JSONB, default=list)
    risk_assessment = Column(JSONB, default=dict)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("LayeredAnalysisSession", back_populates="swot_analysis")
    improvement_items = relationship("ImprovementItem", back_populates="swot")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "matrix": {
                "strengths": self.strengths,
                "weaknesses": self.weaknesses,
                "opportunities": self.opportunities,
                "threats": self.threats,
            },
            "categorized_findings": {
                "architecture": self.architecture_findings,
                "code_quality": self.code_quality_findings,
                "security": self.security_findings,
                "performance": self.performance_findings,
                "maintainability": self.maintainability_findings,
                "database": self.database_findings,
            },
            "prioritization": {
                "prioritized_weaknesses": self.prioritized_weaknesses,
                "quick_wins": self.quick_wins,
                "strategic_items": self.strategic_items,
            },
            "scores": {
                "overall_health": self.overall_health_score,
                "technical_debt": self.technical_debt_score,
                "modernization_readiness": self.modernization_readiness,
            },
            "recommendations": {
                "top": self.top_recommendations,
                "risk_assessment": self.risk_assessment,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ImprovementItem(Base):
    """Prioritized improvement backlog items."""

    __tablename__ = 'improvement_items'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False)
    swot_id = Column(UUID(as_uuid=True), ForeignKey('swot_analysis.id', ondelete='CASCADE'), nullable=True)

    # Item details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # architecture, security, performance, maintainability, database
    item_type = Column(String(30))  # quick_win, strategic, technical_debt, security_fix

    # Source
    source_weakness = Column(String(255))
    affected_files = Column(JSONB, default=list)
    affected_sps = Column(JSONB, default=list)

    # Prioritization
    priority = Column(Integer)  # 1-5 (1 = highest)
    business_impact = Column(String(20))  # critical, high, medium, low
    effort_days = Column(Numeric(5, 1))
    risk_if_not_done = Column(String(20))

    # Dependencies
    depends_on = Column(JSONB, default=list)
    blocks = Column(JSONB, default=list)

    # Implementation hints
    implementation_notes = Column(Text)
    code_examples = Column(JSONB, default=list)
    references = Column(JSONB, default=list)

    # Tracking
    status = Column(String(20), default='identified')
    assigned_to = Column(String(100))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    session = relationship("LayeredAnalysisSession", back_populates="improvement_items")
    swot = relationship("SWOTAnalysis", back_populates="improvement_items")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "item_type": self.item_type,
            "source_weakness": self.source_weakness,
            "affected_files": self.affected_files,
            "affected_sps": self.affected_sps,
            "priority": self.priority,
            "business_impact": self.business_impact,
            "effort_days": float(self.effort_days) if self.effort_days else None,
            "risk_if_not_done": self.risk_if_not_done,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "implementation_notes": self.implementation_notes,
            "code_examples": self.code_examples,
            "references": self.references,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnalysisReport(Base):
    """Generated reports at different stakeholder levels."""

    __tablename__ = 'analysis_reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False)

    # Report type
    report_level = Column(String(20), nullable=False)  # executive, management, technical
    report_format = Column(String(20), default='markdown')

    # Content
    title = Column(String(255))
    content = Column(Text)
    sections = Column(JSONB, default=list)

    # Metrics included
    key_metrics = Column(JSONB, default=dict)
    charts_data = Column(JSONB, default=dict)

    # Generation info
    generated_by = Column(String(50))
    generation_time_ms = Column(Integer)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("LayeredAnalysisSession", back_populates="reports")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "report_level": self.report_level,
            "report_format": self.report_format,
            "title": self.title,
            "content": self.content,
            "sections": self.sections,
            "key_metrics": self.key_metrics,
            "charts_data": self.charts_data,
            "generated_by": self.generated_by,
            "generation_time_ms": self.generation_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
