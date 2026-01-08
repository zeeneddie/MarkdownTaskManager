"""
MigrationAnalyzer Models

Week 65: MigrationAnalyzer Multi-Agent System
SQLAlchemy models for legacy code and database migration analysis.

Models:
- MigrationAnalysis: Main analysis sessions
- MigrationModule: Detected code modules
- MigrationDBSchema: Database schema analysis
- LegacyPattern: Pattern detections
- DBCompatibilityIssue: Database conversion issues
- MigrationRecommendation: Generated recommendations
- FPBreakdown: Function Point details
- RiskAssessment: Risk register

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MigrationAnalysis(Base):
    """Main analysis record for migration projects"""
    __tablename__ = 'migration_analyses'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    repo_path = Column(String(500), nullable=False)
    repo_name = Column(String(200))

    # Detected stacks
    source_stack = Column(String(50))  # Primary: aspnet_webforms, java, php
    secondary_stacks = Column(JSONB, default=[])  # ["jquery", "angularjs"]

    # Target
    target_stack = Column(String(50))  # dotnet8, python, nodejs
    target_db = Column(String(50))  # postgresql, mysql

    # Code Metrics
    total_files = Column(Integer, default=0)
    total_loc = Column(Integer, default=0)
    total_modules = Column(Integer, default=0)
    estimated_fp = Column(Integer)
    complexity_score = Column(Float)
    risk_score = Column(Float)

    # Database Metrics
    db_type = Column(String(50))  # oracle, sqlserver, mysql
    db_version = Column(String(20))
    db_table_count = Column(Integer)
    db_sp_count = Column(Integer)
    db_migration_difficulty = Column(String(1))  # A-E
    db_estimated_days = Column(Float)

    # JSON summary fields
    file_inventory = Column(JSONB, default={})
    module_inventory = Column(JSONB, default={})
    dependency_graph = Column(JSONB, default={})
    pattern_summary = Column(JSONB, default={})
    risk_summary = Column(JSONB, default={})

    # Status
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    current_phase = Column(String(50))  # detection, stack_analysis, db_analysis, cross_cutting, output
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    modules = relationship("MigrationModule", back_populates="analysis", cascade="all, delete-orphan")
    db_schemas = relationship("MigrationDBSchema", back_populates="analysis", cascade="all, delete-orphan")
    patterns = relationship("LegacyPattern", back_populates="analysis", cascade="all, delete-orphan")
    recommendations = relationship("MigrationRecommendation", back_populates="analysis", cascade="all, delete-orphan")
    fp_breakdowns = relationship("FPBreakdown", back_populates="analysis", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="analysis", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "project_id": self.project_id,
            "repo_path": self.repo_path,
            "repo_name": self.repo_name,
            "source_stack": self.source_stack,
            "secondary_stacks": self.secondary_stacks,
            "target_stack": self.target_stack,
            "target_db": self.target_db,
            "total_files": self.total_files,
            "total_loc": self.total_loc,
            "total_modules": self.total_modules,
            "estimated_fp": self.estimated_fp,
            "complexity_score": self.complexity_score,
            "risk_score": self.risk_score,
            "db_type": self.db_type,
            "db_version": self.db_version,
            "db_table_count": self.db_table_count,
            "db_sp_count": self.db_sp_count,
            "db_migration_difficulty": self.db_migration_difficulty,
            "db_estimated_days": self.db_estimated_days,
            "file_inventory": self.file_inventory,
            "module_inventory": self.module_inventory,
            "dependency_graph": self.dependency_graph,
            "pattern_summary": self.pattern_summary,
            "risk_summary": self.risk_summary,
            "status": self.status,
            "current_phase": self.current_phase,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MigrationModule(Base):
    """Individual modules within analysis"""
    __tablename__ = 'migration_modules'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False)

    name = Column(String(200), nullable=False)
    module_type = Column(String(50))  # page, service, model, controller, component
    stack_type = Column(String(50))  # aspnet_webforms, angularjs, vue
    file_path = Column(String(500))
    file_count = Column(Integer, default=1)
    loc = Column(Integer, default=0)

    # Complexity (from Lizard)
    cyclomatic_complexity = Column(Float)
    cognitive_complexity = Column(Float)
    max_complexity = Column(Float)
    avg_complexity = Column(Float)
    function_count = Column(Integer)

    # Migration assessment
    estimated_fp = Column(Integer)
    migration_difficulty = Column(String(20))  # easy, medium, hard, complex
    migration_target = Column(String(100))  # "Blazor component", "Vue 3"
    migration_notes = Column(Text)
    dependencies = Column(JSONB, default=[])

    # Patterns
    legacy_patterns = Column(JSONB, default=[])
    pattern_count = Column(Integer, default=0)
    pattern_multiplier = Column(Float, default=1.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("MigrationAnalysis", back_populates="modules")
    patterns = relationship("LegacyPattern", back_populates="module", cascade="all, delete-orphan")
    fp_breakdowns = relationship("FPBreakdown", back_populates="module", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "analysis_id": str(self.analysis_id) if self.analysis_id else None,
            "name": self.name,
            "module_type": self.module_type,
            "stack_type": self.stack_type,
            "file_path": self.file_path,
            "file_count": self.file_count,
            "loc": self.loc,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "max_complexity": self.max_complexity,
            "avg_complexity": self.avg_complexity,
            "function_count": self.function_count,
            "estimated_fp": self.estimated_fp,
            "migration_difficulty": self.migration_difficulty,
            "migration_target": self.migration_target,
            "migration_notes": self.migration_notes,
            "dependencies": self.dependencies,
            "legacy_patterns": self.legacy_patterns,
            "pattern_count": self.pattern_count,
            "pattern_multiplier": self.pattern_multiplier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MigrationDBSchema(Base):
    """Database schema analysis"""
    __tablename__ = 'migration_db_schemas'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False)

    # Source database
    source_type = Column(String(50), nullable=False)  # oracle, sqlserver, mysql
    source_version = Column(String(20))
    connection_string_hash = Column(String(64))  # For tracking without exposing credentials

    # Schema inventory
    table_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    stored_procedure_count = Column(Integer, default=0)
    function_count = Column(Integer, default=0)
    trigger_count = Column(Integer, default=0)
    index_count = Column(Integer, default=0)
    sequence_count = Column(Integer, default=0)
    constraint_count = Column(Integer, default=0)

    # Schema details
    tables = Column(JSONB, default=[])  # [{name, columns, pk, fks, indexes}]
    views = Column(JSONB, default=[])
    stored_procedures = Column(JSONB, default=[])  # [{name, params, complexity}]
    functions = Column(JSONB, default=[])
    triggers = Column(JSONB, default=[])

    # Stored procedure complexity
    sp_avg_complexity = Column(Float)
    sp_max_complexity = Column(Float)
    sp_high_complexity_count = Column(Integer)
    sp_total_loc = Column(Integer)

    # Migration assessment (Ora2Pg scale)
    migration_difficulty = Column(String(1))  # A-E
    estimated_man_days = Column(Float)
    auto_convertible_percent = Column(Float)

    # Tool outputs
    ora2pg_report = Column(JSONB, default={})
    sqlines_report = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("MigrationAnalysis", back_populates="db_schemas")
    compatibility_issues = relationship("DBCompatibilityIssue", back_populates="schema", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "analysis_id": str(self.analysis_id) if self.analysis_id else None,
            "source_type": self.source_type,
            "source_version": self.source_version,
            "table_count": self.table_count,
            "view_count": self.view_count,
            "stored_procedure_count": self.stored_procedure_count,
            "function_count": self.function_count,
            "trigger_count": self.trigger_count,
            "index_count": self.index_count,
            "sequence_count": self.sequence_count,
            "constraint_count": self.constraint_count,
            "sp_avg_complexity": self.sp_avg_complexity,
            "sp_max_complexity": self.sp_max_complexity,
            "sp_high_complexity_count": self.sp_high_complexity_count,
            "sp_total_loc": self.sp_total_loc,
            "migration_difficulty": self.migration_difficulty,
            "estimated_man_days": self.estimated_man_days,
            "auto_convertible_percent": self.auto_convertible_percent,
            "ora2pg_report": self.ora2pg_report,
            "sqlines_report": self.sqlines_report,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LegacyPattern(Base):
    """Pattern detections in legacy code"""
    __tablename__ = 'legacy_patterns'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False)
    module_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_modules.id', ondelete='CASCADE'), nullable=True)

    pattern_name = Column(String(100), nullable=False)  # viewstate, scope_usage, mysql_functions
    pattern_category = Column(String(50))  # aspnet_webforms, angularjs, php_legacy
    file_path = Column(String(500))
    line_number = Column(Integer)
    code_snippet = Column(Text)  # Matched code

    # Assessment
    risk_level = Column(String(20))  # low, medium, high, critical
    fp_multiplier = Column(Float, default=1.0)
    migration_note = Column(Text)
    migration_target = Column(String(200))  # What to replace with

    # Security flag
    is_security_issue = Column(Boolean, default=False)
    owasp_category = Column(String(10))  # A01-A10

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("MigrationAnalysis", back_populates="patterns")
    module = relationship("MigrationModule", back_populates="patterns")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "analysis_id": str(self.analysis_id) if self.analysis_id else None,
            "module_id": str(self.module_id) if self.module_id else None,
            "pattern_name": self.pattern_name,
            "pattern_category": self.pattern_category,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "risk_level": self.risk_level,
            "fp_multiplier": self.fp_multiplier,
            "migration_note": self.migration_note,
            "migration_target": self.migration_target,
            "is_security_issue": self.is_security_issue,
            "owasp_category": self.owasp_category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DBCompatibilityIssue(Base):
    """Database conversion issues"""
    __tablename__ = 'db_compatibility_issues'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    schema_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_db_schemas.id', ondelete='CASCADE'), nullable=False)

    issue_type = Column(String(50), nullable=False)  # datatype, feature, procedural, syntax
    source_feature = Column(String(200), nullable=False)  # NVARCHAR, IDENTITY, T-SQL
    target_equivalent = Column(String(200))  # VARCHAR, SERIAL, PL/pgSQL

    object_type = Column(String(50))  # table, view, sp, function, trigger
    object_name = Column(String(200))
    location = Column(String(500))  # File or schema location

    # Assessment
    auto_convertible = Column(Boolean, default=True)
    conversion_effort = Column(String(20))  # low, medium, high
    conversion_note = Column(Text)

    # Occurrences
    occurrence_count = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    schema = relationship("MigrationDBSchema", back_populates="compatibility_issues")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "schema_id": str(self.schema_id) if self.schema_id else None,
            "issue_type": self.issue_type,
            "source_feature": self.source_feature,
            "target_equivalent": self.target_equivalent,
            "object_type": self.object_type,
            "object_name": self.object_name,
            "location": self.location,
            "auto_convertible": self.auto_convertible,
            "conversion_effort": self.conversion_effort,
            "conversion_note": self.conversion_note,
            "occurrence_count": self.occurrence_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MigrationRecommendation(Base):
    """Generated recommendations by agents"""
    __tablename__ = 'migration_recommendations'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False)

    category = Column(String(50), nullable=False)  # architecture, database, security, performance, testing
    priority = Column(String(20))  # critical, high, medium, low
    title = Column(String(300), nullable=False)
    description = Column(Text)

    # Source
    source_agent = Column(String(50))  # miguel, quinn, eliza, felix, diana
    related_modules = Column(JSONB, default=[])  # Module IDs
    related_patterns = Column(JSONB, default=[])  # Pattern IDs

    # Action items
    action_items = Column(JSONB, default=[])  # [{step, effort, dependency}]
    estimated_effort = Column(String(20))  # hours, days, weeks
    estimated_fp_impact = Column(Integer)

    # Status
    status = Column(String(20), default='pending')  # pending, accepted, rejected, implemented

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("MigrationAnalysis", back_populates="recommendations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "analysis_id": str(self.analysis_id) if self.analysis_id else None,
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "source_agent": self.source_agent,
            "related_modules": self.related_modules,
            "related_patterns": self.related_patterns,
            "action_items": self.action_items,
            "estimated_effort": self.estimated_effort,
            "estimated_fp_impact": self.estimated_fp_impact,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FPBreakdown(Base):
    """Function Point breakdown details"""
    __tablename__ = 'fp_breakdowns'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False)
    module_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_modules.id', ondelete='CASCADE'), nullable=True)

    # IFPUG components
    fp_type = Column(String(20), nullable=False)  # EI, EO, EQ, ILF, EIF
    fp_name = Column(String(200))
    complexity_rating = Column(String(10))  # low, average, high
    unadjusted_fp = Column(Integer)

    # Adjustments
    pattern_multiplier = Column(Float, default=1.0)
    legacy_multiplier = Column(Float, default=1.0)  # 1.2-2.0x for legacy
    db_migration_multiplier = Column(Float, default=1.0)
    adjusted_fp = Column(Float)

    # Source
    source_file = Column(String(500))
    detected_by = Column(String(50))  # eliza, lizard, manual

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("MigrationAnalysis", back_populates="fp_breakdowns")
    module = relationship("MigrationModule", back_populates="fp_breakdowns")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "analysis_id": str(self.analysis_id) if self.analysis_id else None,
            "module_id": str(self.module_id) if self.module_id else None,
            "fp_type": self.fp_type,
            "fp_name": self.fp_name,
            "complexity_rating": self.complexity_rating,
            "unadjusted_fp": self.unadjusted_fp,
            "pattern_multiplier": self.pattern_multiplier,
            "legacy_multiplier": self.legacy_multiplier,
            "db_migration_multiplier": self.db_migration_multiplier,
            "adjusted_fp": self.adjusted_fp,
            "source_file": self.source_file,
            "detected_by": self.detected_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RiskAssessment(Base):
    """Risk register with FMEA-style assessment"""
    __tablename__ = 'risk_assessments'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False)

    risk_id = Column(String(20))  # R001, R002, etc.
    title = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # technical, security, performance, business, resource

    # Assessment (FMEA style)
    probability = Column(Integer)  # 1-5
    impact = Column(Integer)  # 1-5
    detectability = Column(Integer)  # 1-5
    risk_score = Column(Integer)  # probability * impact * detectability

    # Status
    status = Column(String(20), default='identified')  # identified, mitigating, mitigated, accepted

    # Mitigation
    mitigation_strategy = Column(Text)
    mitigation_owner = Column(String(100))
    mitigation_deadline = Column(DateTime(timezone=True))

    # Related items
    related_modules = Column(JSONB, default=[])
    related_patterns = Column(JSONB, default=[])

    # Source
    identified_by = Column(String(50))  # quinn, felix, eliza, manual

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    analysis = relationship("MigrationAnalysis", back_populates="risk_assessments")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "analysis_id": str(self.analysis_id) if self.analysis_id else None,
            "risk_id": self.risk_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "probability": self.probability,
            "impact": self.impact,
            "detectability": self.detectability,
            "risk_score": self.risk_score,
            "status": self.status,
            "mitigation_strategy": self.mitigation_strategy,
            "mitigation_owner": self.mitigation_owner,
            "mitigation_deadline": self.mitigation_deadline.isoformat() if self.mitigation_deadline else None,
            "related_modules": self.related_modules,
            "related_patterns": self.related_patterns,
            "identified_by": self.identified_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
