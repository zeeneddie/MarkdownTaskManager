"""
Week 88: Graph Workflow Integration Models

SQLAlchemy models for graph-based workflow integration and portal feature requests.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class PortalFeatureRequest(Base):
    """Customer portal feature request with agent classification."""
    __tablename__ = 'portal_feature_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(100), nullable=True)
    user_email = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)

    # Request details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default='medium')
    category = Column(String(100), nullable=True)
    attachments = Column(JSONB, nullable=True)

    # Classification (by Peter agent)
    work_type = Column(String(50), nullable=True)
    classification_confidence = Column(Float, nullable=True)
    classification_reasoning = Column(Text, nullable=True)
    classified_at = Column(DateTime, nullable=True)
    classified_by = Column(String(50), nullable=True)

    # Epic/Feature mapping
    mapped_project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    mapped_epic_id = Column(String(100), nullable=True)
    mapped_feature_id = Column(String(100), nullable=True)
    mapping_confidence = Column(Float, nullable=True)
    mapping_suggestions = Column(JSONB, nullable=True)

    # Status tracking
    status = Column(String(50), default='submitted')
    kanban_item_id = Column(Integer, nullable=True)
    sprint_id = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", backref="feature_requests")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "external_id": self.external_id,
            "user_email": self.user_email,
            "user_name": self.user_name,
            "organization": self.organization,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "attachments": self.attachments,
            "work_type": self.work_type,
            "classification_confidence": self.classification_confidence,
            "classification_reasoning": self.classification_reasoning,
            "classified_at": self.classified_at.isoformat() if self.classified_at else None,
            "classified_by": self.classified_by,
            "mapped_project_id": self.mapped_project_id,
            "mapped_epic_id": self.mapped_epic_id,
            "mapped_feature_id": self.mapped_feature_id,
            "mapping_confidence": self.mapping_confidence,
            "mapping_suggestions": self.mapping_suggestions,
            "status": self.status,
            "kanban_item_id": self.kanban_item_id,
            "sprint_id": self.sprint_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class GraphAnalysisCache(Base):
    """Cache for graph analysis results."""
    __tablename__ = 'graph_analysis_cache'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    entity_id = Column(String(200), nullable=True)
    entity_type = Column(String(50), nullable=True)
    result = Column(JSONB, nullable=False)
    metrics = Column(JSONB, nullable=True)
    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    cache_hit_count = Column(Integer, default=0)

    # Relationships
    project = relationship("Project", backref="graph_analysis_cache")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "analysis_type": self.analysis_type,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "result": self.result,
            "metrics": self.metrics,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cache_hit_count": self.cache_hit_count,
        }


class WorkflowGraphIntegration(Base):
    """Tracks graph integration usage within workflows."""
    __tablename__ = 'workflow_graph_integrations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_type = Column(String(50), nullable=False)
    workflow_session_id = Column(String(100), nullable=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    integration_type = Column(String(50), nullable=False)
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    status = Column(String(30), default='pending')
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", backref="graph_integrations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_type": self.workflow_type,
            "workflow_session_id": self.workflow_session_id,
            "project_id": self.project_id,
            "integration_type": self.integration_type,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Analysis types
ANALYSIS_TYPES = [
    "impact_analysis",
    "dependency_check",
    "coupling_metrics",
    "test_coverage_map",
    "enhancement_scope",
]

# Integration types per workflow
WORKFLOW_GRAPH_INTEGRATIONS = {
    "NEW_FEATURE": ["impact_analysis", "dependency_check"],
    "BUG": ["dependency_check", "test_coverage_map"],
    "MAINTENANCE": ["impact_analysis", "coupling_metrics"],
    "MIGRATION": ["dependency_check", "coupling_metrics"],
    "QUALITY_AUDIT": ["coupling_metrics"],
    "QUALITY_IMPROVEMENT": ["coupling_metrics", "impact_analysis"],
    "TESTING": ["test_coverage_map"],
    "ENHANCEMENT": ["enhancement_scope", "impact_analysis"],
}

# Feature request statuses
FEATURE_REQUEST_STATUSES = [
    "submitted",
    "analyzing",
    "classified",
    "mapped",
    "planned",
    "in_progress",
    "testing",
    "done",
    "rejected",
]

# Work types for classification
WORK_TYPES = [
    "GREEN_PAPER",
    "BROWN_PAPER",
    "NEW_FEATURE",
    "BUG",
    "MAINTENANCE",
    "MIGRATION",
    "QUALITY_AUDIT",
    "QUALITY_IMPROVEMENT",
    "TESTING",
    "ENHANCEMENT",
    "PROJECT_DEFINITION",
]
