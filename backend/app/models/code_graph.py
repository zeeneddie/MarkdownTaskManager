"""
Code Graph Models - Week 75 Graph Persistence

SQLAlchemy models for persistent code graph storage.
Extends KnowledgeGraphService with database persistence.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class CodeGraphEntity(Base):
    """
    Persistent code entity (class, function, module, etc.)

    Stores parsed code entities with their metadata and metrics.
    Used for impact analysis and dependency tracking.
    """
    __tablename__ = 'code_graph_entities'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), nullable=False)  # class, function, method, module, import
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(500))  # Full path: module.Class.method
    file_path = Column(String(500), nullable=False)
    start_line = Column(Integer)
    end_line = Column(Integer)
    docstring = Column(Text)
    signature = Column(Text)  # Function/method signature
    entity_data = Column(JSONB, default=dict)  # Additional metadata
    metrics = Column(JSONB, default=dict)  # Complexity, lines, etc.
    hash = Column(String(64))  # Content hash for change detection
    last_synced = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    outgoing_relations = relationship(
        "CodeGraphRelation",
        foreign_keys="CodeGraphRelation.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan"
    )
    incoming_relations = relationship(
        "CodeGraphRelation",
        foreign_keys="CodeGraphRelation.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan"
    )
    impact_cache = relationship("CodeGraphImpactCache", back_populates="entity", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "entity_type": self.entity_type,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "docstring": self.docstring,
            "signature": self.signature,
            "entity_data": self.entity_data or {},
            "metrics": self.metrics or {},
            "hash": self.hash,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CodeGraphRelation(Base):
    """
    Relationship between two code entities.

    Types: imports, extends, calls, uses, contains, depends_on
    """
    __tablename__ = 'code_graph_relations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey('code_graph_entities.id', ondelete='CASCADE'), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey('code_graph_entities.id', ondelete='CASCADE'), nullable=False)
    relation_type = Column(String(50), nullable=False)  # imports, extends, calls, uses, contains
    relation_data = Column(JSONB, default=dict)  # Additional metadata
    weight = Column(Float, default=1.0)  # Relation strength/importance
    created_at = Column(DateTime, default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('source_entity_id', 'target_entity_id', 'relation_type', name='uq_entity_relation'),
    )

    # Relationships
    source_entity = relationship("CodeGraphEntity", foreign_keys=[source_entity_id], back_populates="outgoing_relations")
    target_entity = relationship("CodeGraphEntity", foreign_keys=[target_entity_id], back_populates="incoming_relations")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "source_entity_id": str(self.source_entity_id),
            "target_entity_id": str(self.target_entity_id),
            "relation_type": self.relation_type,
            "relation_data": self.relation_data or {},
            "weight": self.weight,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CodeGraphSnapshot(Base):
    """
    Graph snapshot for version comparison.

    Captures graph state at a point in time, optionally linked to git commit.
    """
    __tablename__ = 'code_graph_snapshots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    snapshot_name = Column(String(100))  # Optional name
    git_commit = Column(String(40))  # Associated git commit
    entity_count = Column(Integer, default=0)
    relation_count = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    summary_stats = Column(JSONB, default=dict)  # Entity type counts, metrics
    created_at = Column(DateTime, default=func.now())


    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "snapshot_name": self.snapshot_name,
            "git_commit": self.git_commit,
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "file_count": self.file_count,
            "summary_stats": self.summary_stats or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CodeGraphImpactCache(Base):
    """
    Cached impact analysis results.

    Stores precomputed impact analysis for faster queries.
    """
    __tablename__ = 'code_graph_impact_cache'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('code_graph_entities.id', ondelete='CASCADE'), nullable=False)
    impact_type = Column(String(50), nullable=False)  # direct, transitive, circular
    affected_entities = Column(JSONB, default=list)  # List of affected entity IDs
    affected_files = Column(JSONB, default=list)  # List of affected file paths
    impact_score = Column(Float)  # Calculated impact score
    depth = Column(Integer)  # Depth in dependency chain
    cache_valid_until = Column(DateTime)  # Cache expiration
    created_at = Column(DateTime, default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('entity_id', 'impact_type', name='uq_entity_impact'),
    )

    # Relationships
    entity = relationship("CodeGraphEntity", back_populates="impact_cache")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "entity_id": str(self.entity_id),
            "impact_type": self.impact_type,
            "affected_entities": self.affected_entities or [],
            "affected_files": self.affected_files or [],
            "impact_score": self.impact_score,
            "depth": self.depth,
            "cache_valid_until": self.cache_valid_until.isoformat() if self.cache_valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CodeGraphModuleCoupling(Base):
    """
    Module-level coupling metrics.

    Tracks coupling between modules for architectural analysis.
    """
    __tablename__ = 'code_graph_module_coupling'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    source_module = Column(String(255), nullable=False)  # Module path
    target_module = Column(String(255), nullable=False)  # Module path
    coupling_count = Column(Integer, default=0)  # Number of connections
    coupling_type = Column(String(50))  # import, call, inherit
    coupling_data = Column(JSONB, default=dict)  # Detailed coupling info
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('project_id', 'source_module', 'target_module', name='uq_module_coupling'),
    )


    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "source_module": self.source_module,
            "target_module": self.target_module,
            "coupling_count": self.coupling_count,
            "coupling_type": self.coupling_type,
            "coupling_data": self.coupling_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
