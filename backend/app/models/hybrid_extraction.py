# backend/app/models/hybrid_extraction.py
"""
SQLAlchemy models for Hybrid Business Rule Extraction - Week 111-114 Phase 5.

Tables:
- hybrid_extraction_sessions: Track extraction sessions
- hybrid_extracted_rules: Store extracted business rules
- hybrid_workflow_correlations: Detected CRUD workflows
- hybrid_entity_mappings: Detected entities from rules
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID
import uuid

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class ExtractionStatus(str, Enum):
    """Extraction session status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionTier(str, Enum):
    """Customer extraction tier."""
    FREE = "FREE"
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    PREMIUM = "PREMIUM"


class RuleType(str, Enum):
    """Business rule types."""
    VALIDATION = "VALIDATION"
    AUTHORIZATION = "AUTHORIZATION"
    SCHEDULING = "SCHEDULING"
    WORKFLOW = "WORKFLOW"
    BRANCHING = "BRANCHING"
    THRESHOLD = "THRESHOLD"
    DATA_ACCESS = "DATA_ACCESS"
    STATE_MANAGEMENT = "STATE_MANAGEMENT"
    ERROR_HANDLING = "ERROR_HANDLING"
    NAVIGATION = "NAVIGATION"
    CALCULATION = "CALCULATION"
    CONSTRAINT = "CONSTRAINT"
    DERIVATION = "DERIVATION"


class ExtractionMethod(str, Enum):
    """How the rule was extracted."""
    AST = "AST"
    REGEX = "REGEX"
    LLM = "LLM"
    HYBRID = "HYBRID"


class WorkflowType(str, Enum):
    """Detected workflow types."""
    CRUD = "CRUD"
    STATE_MACHINE = "STATE_MACHINE"
    APPROVAL = "APPROVAL"
    SCHEDULING = "SCHEDULING"
    NOTIFICATION = "NOTIFICATION"
    INTEGRATION = "INTEGRATION"


class EntityType(str, Enum):
    """Entity types detected."""
    TABLE = "TABLE"
    CLASS = "CLASS"
    MODULE = "MODULE"
    SERVICE = "SERVICE"


class HybridExtractionSession(Base):
    """Hybrid extraction session record."""
    __tablename__ = 'hybrid_extraction_sessions'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    source_path = Column(String(1000), nullable=False)
    extraction_tier = Column(String(20), nullable=False, default='STANDARD')
    status = Column(String(20), nullable=False, default='pending')
    workflow_type = Column(String(30), nullable=True)

    # Metrics
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    total_rules = Column(Integer, default=0)
    high_confidence_rules = Column(Integer, default=0)
    average_confidence = Column(Float, default=0.0)

    # LLM Statistics
    static_rules_extracted = Column(Integer, default=0)
    llm_rules_extracted = Column(Integer, default=0)
    rules_classified = Column(Integer, default=0)
    rules_confirmed = Column(Integer, default=0)
    rules_rejected = Column(Integer, default=0)
    multi_llm_validated = Column(Integer, default=0)
    consensus_reached = Column(Integer, default=0)
    premium_synthesis_performed = Column(Boolean, default=False)

    # Cost tracking
    total_tokens = Column(Integer, default=0)
    total_cost_cents = Column(Float, default=0.0)

    # Timing (milliseconds)
    static_extraction_ms = Column(Integer, default=0)
    llm_classification_ms = Column(Integer, default=0)
    llm_extraction_ms = Column(Integer, default=0)
    multi_llm_validation_ms = Column(Integer, default=0)
    premium_synthesis_ms = Column(Integer, default=0)
    total_ms = Column(Integer, default=0)

    # Detected technologies
    detected_languages = Column(JSONB, default=[])
    detected_frameworks = Column(JSONB, default=[])
    database_patterns = Column(JSONB, default=[])

    # Premium synthesis result
    synthesis_result = Column(JSONB, nullable=True)

    # Errors and warnings
    errors = Column(JSONB, default=[])
    warnings = Column(JSONB, default=[])

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship('Project', back_populates='hybrid_extraction_sessions')
    rules = relationship('HybridExtractedRule', back_populates='session', cascade='all, delete-orphan')
    workflows = relationship('HybridWorkflowCorrelation', back_populates='session', cascade='all, delete-orphan')
    entities = relationship('HybridEntityMapping', back_populates='session', cascade='all, delete-orphan')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'project_id': self.project_id,
            'source_path': self.source_path,
            'extraction_tier': self.extraction_tier,
            'status': self.status,
            'workflow_type': self.workflow_type,
            'metrics': {
                'total_files': self.total_files,
                'total_lines': self.total_lines,
                'total_rules': self.total_rules,
                'high_confidence_rules': self.high_confidence_rules,
                'average_confidence': self.average_confidence,
            },
            'llm_stats': {
                'static_rules_extracted': self.static_rules_extracted,
                'llm_rules_extracted': self.llm_rules_extracted,
                'rules_classified': self.rules_classified,
                'rules_confirmed': self.rules_confirmed,
                'rules_rejected': self.rules_rejected,
                'multi_llm_validated': self.multi_llm_validated,
                'consensus_reached': self.consensus_reached,
                'premium_synthesis_performed': self.premium_synthesis_performed,
            },
            'cost': {
                'total_tokens': self.total_tokens,
                'total_cost_cents': self.total_cost_cents,
            },
            'timing': {
                'static_extraction_ms': self.static_extraction_ms,
                'llm_classification_ms': self.llm_classification_ms,
                'llm_extraction_ms': self.llm_extraction_ms,
                'multi_llm_validation_ms': self.multi_llm_validation_ms,
                'premium_synthesis_ms': self.premium_synthesis_ms,
                'total_ms': self.total_ms,
            },
            'technology': {
                'detected_languages': self.detected_languages or [],
                'detected_frameworks': self.detected_frameworks or [],
                'database_patterns': self.database_patterns or [],
            },
            'synthesis_result': self.synthesis_result,
            'errors': self.errors or [],
            'warnings': self.warnings or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class HybridExtractedRule(Base):
    """Extracted business rule from any of the 12 extractors."""
    __tablename__ = 'hybrid_extracted_rules'

    id = Column(String(50), primary_key=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey('hybrid_extraction_sessions.id', ondelete='CASCADE'), nullable=False)

    # Rule classification
    rule_type = Column(String(30), nullable=False)
    extraction_method = Column(String(20), nullable=False)
    language = Column(String(30), nullable=False)

    # Rule content
    condition = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    natural_language = Column(Text, nullable=True)
    code_snippet = Column(Text, nullable=True)

    # Source location
    source_file = Column(String(500), nullable=False)
    source_line_start = Column(Integer, nullable=True)
    source_line_end = Column(Integer, nullable=True)

    # Variables and entities
    variables_involved = Column(JSONB, default=[])
    entities_referenced = Column(JSONB, default=[])

    # Confidence
    confidence = Column(Float, nullable=False)
    llm_validated = Column(Boolean, default=False)
    llm_confidence = Column(Float, nullable=True)
    validation_provider = Column(String(30), nullable=True)

    # Compliance
    compliance_tags = Column(JSONB, default=[])

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship('HybridExtractionSession', back_populates='rules')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'session_id': str(self.session_id),
            'rule_type': self.rule_type,
            'extraction_method': self.extraction_method,
            'language': self.language,
            'condition': self.condition,
            'action': self.action,
            'description': self.description,
            'natural_language': self.natural_language,
            'code_snippet': self.code_snippet,
            'source_file': self.source_file,
            'source_lines': [self.source_line_start, self.source_line_end] if self.source_line_start else None,
            'variables_involved': self.variables_involved or [],
            'entities_referenced': self.entities_referenced or [],
            'confidence': self.confidence,
            'llm_validated': self.llm_validated,
            'llm_confidence': self.llm_confidence,
            'validation_provider': self.validation_provider,
            'compliance_tags': self.compliance_tags or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class HybridWorkflowCorrelation(Base):
    """Detected workflow pattern (CRUD, state machine, etc.)."""
    __tablename__ = 'hybrid_workflow_correlations'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey('hybrid_extraction_sessions.id', ondelete='CASCADE'), nullable=False)

    # Workflow identification
    workflow_name = Column(String(200), nullable=False)
    workflow_type = Column(String(30), nullable=False)
    primary_entity = Column(String(100), nullable=True)

    # Operations
    operations = Column(JSONB, default=[])
    total_rules = Column(Integer, default=0)

    # Source
    source_files = Column(JSONB, default=[])
    auth_pattern = Column(String(100), nullable=True)

    # Confidence
    confidence = Column(Float, nullable=False, default=0.7)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship('HybridExtractionSession', back_populates='workflows')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'workflow_name': self.workflow_name,
            'workflow_type': self.workflow_type,
            'primary_entity': self.primary_entity,
            'operations': self.operations or [],
            'total_rules': self.total_rules,
            'source_files': self.source_files or [],
            'auth_pattern': self.auth_pattern,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class HybridEntityMapping(Base):
    """Detected entity from business rules."""
    __tablename__ = 'hybrid_entity_mappings'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey('hybrid_extraction_sessions.id', ondelete='CASCADE'), nullable=False)

    # Entity identification
    entity_name = Column(String(200), nullable=False)
    entity_type = Column(String(30), nullable=False)

    # CRUD coverage
    rule_count = Column(Integer, default=0)
    has_create = Column(Boolean, default=False)
    has_read = Column(Boolean, default=False)
    has_update = Column(Boolean, default=False)
    has_delete = Column(Boolean, default=False)
    crud_coverage = Column(String(10), nullable=True)

    # Source
    files_referenced = Column(JSONB, default=[])

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship('HybridExtractionSession', back_populates='entities')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'entity_name': self.entity_name,
            'entity_type': self.entity_type,
            'rule_count': self.rule_count,
            'has_create': self.has_create,
            'has_read': self.has_read,
            'has_update': self.has_update,
            'has_delete': self.has_delete,
            'crud_coverage': self.crud_coverage,
            'files_referenced': self.files_referenced or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
