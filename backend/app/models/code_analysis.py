"""
Code Analysis Models - Week 83

SQLAlchemy models for code analysis aggregation and Potpie integration.

Tables:
- CodeAnalysisAggregation: Unified analysis results
- PotpieKnowledgeGraphEntry: Knowledge graph nodes from Potpie
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class CodeAnalysisAggregation(Base):
    """
    Aggregated code analysis result.

    Combines results from:
    - StackDetectionService (technology profile)
    - DependencyGraphService (dependency profile)
    - CodeWikiService (documentation profile)
    - Lizard (complexity profile)

    This forms the input for the Deep Extraction Pipeline.
    """
    __tablename__ = 'code_analysis_aggregations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), index=True)

    # Source info
    repository_path = Column(String(500), nullable=False)
    branch = Column(String(100), default='main')
    commit_hash = Column(String(40), nullable=True)

    # Analysis status
    status = Column(String(20), default='pending', index=True)  # pending, running, completed, failed
    duration_ms = Column(Integer, nullable=True)
    analysis_score = Column(Float, nullable=True)  # 0-100

    # Technology profile
    primary_stack = Column(String(50), nullable=True)
    secondary_stacks = Column(JSONB, default=[])
    database_type = Column(String(50), nullable=True)
    languages = Column(JSONB, default={})  # {lang: file_count}
    frameworks = Column(JSONB, default=[])
    total_files = Column(Integer, default=0)
    total_loc = Column(Integer, default=0)

    # Dependency profile
    module_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    circular_dependencies = Column(Integer, default=0)
    entry_points = Column(JSONB, default=[])
    hub_modules = Column(JSONB, default=[])
    external_dependencies = Column(Integer, default=0)
    internal_dependencies = Column(Integer, default=0)
    instability_avg = Column(Float, nullable=True)
    coupling_score = Column(Float, nullable=True)

    # Complexity profile
    avg_cyclomatic = Column(Float, nullable=True)
    max_cyclomatic = Column(Float, nullable=True)
    total_functions = Column(Integer, default=0)
    high_complexity_count = Column(Integer, default=0)
    complexity_rating = Column(String(20), nullable=True)  # low, medium, high, critical

    # Documentation profile
    documented_ratio = Column(Float, nullable=True)
    diagram_count = Column(Integer, default=0)
    readme_exists = Column(Boolean, default=False)
    architecture_detected = Column(Boolean, default=False)

    # Raw data references
    stack_scan_result = Column(JSONB, nullable=True)  # Full ScanResult
    codewiki_analysis_id = Column(Integer, nullable=True)

    # Errors/warnings
    errors = Column(JSONB, default=[])
    warnings = Column(JSONB, default=[])

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship('Project', back_populates='code_analyses')
    knowledge_graph_entries = relationship(
        'PotpieKnowledgeGraphEntry',
        back_populates='aggregation',
        cascade='all, delete-orphan'
    )

    @property
    def is_successful(self) -> bool:
        """Check if analysis completed without critical errors."""
        return self.status == 'completed' and len(self.errors or []) == 0

    def to_llm_context(self) -> str:
        """Generate LLM context string."""
        lines = [
            f"## Code Analysis Summary",
            f"Repository: {self.repository_path}",
            f"",
            f"### Technology Stack",
            f"- Primary: {self.primary_stack or 'Unknown'}",
        ]

        if self.secondary_stacks:
            lines.append(f"- Secondary: {', '.join(self.secondary_stacks[:5])}")
        if self.database_type:
            lines.append(f"- Database: {self.database_type}")

        lines.extend([
            f"- Files: {self.total_files:,}",
            f"- Lines of Code: {self.total_loc:,}",
            f"",
            f"### Dependencies",
            f"- Modules: {self.module_count}",
            f"- Circular deps: {self.circular_dependencies}",
            f"- Coupling: {'High' if (self.coupling_score or 0) > 0.7 else 'Medium' if (self.coupling_score or 0) > 0.4 else 'Low'}",
            f"",
            f"### Complexity",
            f"- Rating: {(self.complexity_rating or 'unknown').upper()}",
            f"- Avg cyclomatic: {self.avg_cyclomatic:.1f}" if self.avg_cyclomatic else "- Avg cyclomatic: N/A",
        ])

        return "\n".join(lines)


class PotpieKnowledgeGraphEntry(Base):
    """
    Knowledge graph entry from Potpie analysis.

    Represents nodes in the code knowledge graph with relationships
    for semantic code understanding.
    """
    __tablename__ = 'potpie_knowledge_graph_entries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('code_analysis_aggregations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Node identification
    node_type = Column(String(50), nullable=False, index=True)  # file, function, class, module
    node_name = Column(String(255), nullable=False)
    node_path = Column(String(500), nullable=True)

    # Node metadata
    language = Column(String(30), nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    complexity = Column(Float, nullable=True)

    # Relationships
    imports = Column(JSONB, default=[])
    imported_by = Column(JSONB, default=[])
    calls = Column(JSONB, default=[])
    called_by = Column(JSONB, default=[])

    # Documentation
    docstring = Column(Text, nullable=True)
    description = Column(Text, nullable=True)  # LLM-generated

    # Embedding for semantic search
    embedding_vector = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    aggregation = relationship('CodeAnalysisAggregation', back_populates='knowledge_graph_entries')

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'node_type': self.node_type,
            'node_name': self.node_name,
            'node_path': self.node_path,
            'language': self.language,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'complexity': self.complexity,
            'imports': self.imports or [],
            'imported_by': self.imported_by or [],
            'calls': self.calls or [],
            'called_by': self.called_by or [],
            'docstring': self.docstring,
            'description': self.description,
        }
