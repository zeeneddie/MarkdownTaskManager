"""
CodeWiki Models - Repository Documentation Analysis

Week 62: Code Understanding Integration

Stores CodeWiki analysis results:
- Analysis sessions and status
- Module hierarchy (module_tree.json)
- Generated diagrams (Mermaid)
- Documentation content
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class CodeWikiAnalysisStatus(str, Enum):
    """Status of a CodeWiki analysis."""
    PENDING = "pending"
    SCANNING = "scanning"
    CLUSTERING = "clustering"
    DOCUMENTING = "documenting"
    GENERATING_DIAGRAMS = "generating_diagrams"
    COMPLETED = "completed"
    FAILED = "failed"


class CodeWikiAnalysis(Base):
    """
    CodeWiki repository analysis session.

    Tracks the analysis of a project repository
    including status, configuration, and results.
    """
    __tablename__ = "codewiki_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Analysis configuration
    repository_path = Column(String(500), nullable=False)
    branch = Column(String(100), default="main")
    languages_detected = Column(JSON, default=list)  # ["python", "typescript"]

    # Status tracking
    status = Column(
        SQLEnum(CodeWikiAnalysisStatus),
        default=CodeWikiAnalysisStatus.PENDING
    )
    status_message = Column(Text)
    progress_percent = Column(Integer, default=0)

    # Analysis results
    total_files = Column(Integer, default=0)
    total_modules = Column(Integer, default=0)
    total_functions = Column(Integer, default=0)
    total_classes = Column(Integer, default=0)

    # Raw outputs
    module_tree_json = Column(JSON)  # Full module_tree.json content
    metadata_json = Column(JSON)  # metadata.json from CodeWiki
    overview_md = Column(Text)  # overview.md content

    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.utcnow())

    # Relationships
    modules = relationship("CodeWikiModule", back_populates="analysis", cascade="all, delete-orphan")
    diagrams = relationship("CodeWikiDiagram", back_populates="analysis", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "repository_path": self.repository_path,
            "branch": self.branch,
            "languages_detected": self.languages_detected or [],
            "status": self.status.value if self.status else None,
            "status_message": self.status_message,
            "progress_percent": self.progress_percent,
            "total_files": self.total_files,
            "total_modules": self.total_modules,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CodeWikiModule(Base):
    """
    CodeWiki module from module_tree.json.

    Represents a logical module/component discovered
    during repository analysis.
    """
    __tablename__ = "codewiki_modules"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("codewiki_analyses.id"), nullable=False)

    # Module identification
    name = Column(String(200), nullable=False)
    path = Column(String(500))  # Relative path in repo
    parent_module_id = Column(Integer, ForeignKey("codewiki_modules.id"), nullable=True)
    level = Column(Integer, default=0)  # Depth in hierarchy

    # Module contents
    description = Column(Text)
    purpose = Column(Text)
    files = Column(JSON, default=list)  # List of file paths in this module

    # Statistics
    file_count = Column(Integer, default=0)
    function_count = Column(Integer, default=0)
    class_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)

    # Dependencies
    dependencies = Column(JSON, default=list)  # Internal dependencies
    external_dependencies = Column(JSON, default=list)  # External packages

    # Generated documentation
    documentation_md = Column(Text)  # module*.md content

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    # Relationships
    analysis = relationship("CodeWikiAnalysis", back_populates="modules")
    children = relationship("CodeWikiModule", backref="parent", remote_side=[id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "name": self.name,
            "path": self.path,
            "parent_module_id": self.parent_module_id,
            "level": self.level,
            "description": self.description,
            "purpose": self.purpose,
            "files": self.files or [],
            "file_count": self.file_count,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "line_count": self.line_count,
            "dependencies": self.dependencies or [],
            "external_dependencies": self.external_dependencies or [],
        }


class DiagramType(str, Enum):
    """Type of generated diagram."""
    ARCHITECTURE = "architecture"
    DATA_FLOW = "data_flow"
    DEPENDENCY = "dependency"
    SEQUENCE = "sequence"
    CLASS = "class"
    COMPONENT = "component"
    ERD = "erd"


class CodeWikiDiagram(Base):
    """
    CodeWiki generated diagram.

    Stores Mermaid diagrams generated during analysis
    for architecture visualization.
    """
    __tablename__ = "codewiki_diagrams"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("codewiki_analyses.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("codewiki_modules.id"), nullable=True)

    # Diagram metadata
    name = Column(String(200), nullable=False)
    diagram_type = Column(SQLEnum(DiagramType), nullable=False)
    description = Column(Text)

    # Mermaid content
    mermaid_code = Column(Text, nullable=False)

    # Rendered output (optional)
    svg_content = Column(Text)
    png_path = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    # Relationships
    analysis = relationship("CodeWikiAnalysis", back_populates="diagrams")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "module_id": self.module_id,
            "name": self.name,
            "diagram_type": self.diagram_type.value if self.diagram_type else None,
            "description": self.description,
            "mermaid_code": self.mermaid_code,
            "has_svg": bool(self.svg_content),
            "png_path": self.png_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CodeWikiAgentContext(Base):
    """
    CodeWiki context prepared for agents.

    Pre-computed context from CodeWiki analysis
    optimized for agent consumption.
    """
    __tablename__ = "codewiki_agent_contexts"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("codewiki_analyses.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)  # felix, miguel, quinn, diana

    # Context type
    context_type = Column(String(50), nullable=False)  # architecture, dependencies, security, docs

    # Prepared context
    context_summary = Column(Text)  # Concise summary for agent
    context_details = Column(JSON)  # Structured data for agent

    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "agent_name": self.agent_name,
            "context_type": self.context_type,
            "context_summary": self.context_summary,
            "times_used": self.times_used,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
