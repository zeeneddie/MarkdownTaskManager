"""
Week 132-133: Dead Code & Runtime Analysis Models

SQLAlchemy models and dataclasses for dead code detection,
runtime analysis, and code coverage mapping.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================================
# Enums
# ============================================================================

class DeadCodeItemType(str, Enum):
    """Types of dead code items."""
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    FILE = "file"
    BRANCH = "branch"
    PARAMETER = "parameter"
    PROPERTY = "property"


class DetectionMethod(str, Enum):
    """How the dead code was detected."""
    STATIC = "static"
    RUNTIME = "runtime"
    BOTH = "both"
    HEURISTIC = "heuristic"


class RemovalRisk(str, Enum):
    """Risk level for removing dead code."""
    SAFE = "safe"          # 100% confident, no references
    LOW = "low"            # Very likely safe, minimal references
    MEDIUM = "medium"      # Might have side effects
    HIGH = "high"          # Potential breaking changes
    CRITICAL = "critical"  # Don't remove without review


class SuggestedAction(str, Enum):
    """Recommended action for dead code."""
    REMOVE = "remove"
    REVIEW = "review"
    KEEP = "keep"
    REFACTOR = "refactor"
    DEPRECATE = "deprecate"


class AnalysisType(str, Enum):
    """Type of dead code analysis."""
    STATIC = "static"
    RUNTIME = "runtime"
    COMBINED = "combined"


class APMProvider(str, Enum):
    """Supported APM providers."""
    NEW_RELIC = "new_relic"
    DATADOG = "datadog"
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    APP_DYNAMICS = "app_dynamics"
    CUSTOM = "custom"
    NONE = "none"


class CoverageSource(str, Enum):
    """Source of coverage data."""
    JEST = "jest"
    PYTEST = "pytest"
    PYTEST_COV = "pytest_cov"
    DOTCOVER = "dotcover"
    COVERLET = "coverlet"
    ISTANBUL = "istanbul"
    JACOCO = "jacoco"
    RUNTIME = "runtime"
    MANUAL = "manual"


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class DeadCodeAnalysisModel(Base):
    """Main dead code analysis session."""
    __tablename__ = "dead_code_analyses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    project_path = Column(String(1024), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    languages_detected = Column(JSONB, nullable=True)
    total_files_scanned = Column(Integer, default=0)
    total_lines_scanned = Column(Integer, default=0)
    dead_code_count = Column(Integer, default=0)
    dead_lines_count = Column(Integer, default=0)
    dead_code_percentage = Column(Float, default=0.0)
    safe_removal_count = Column(Integer, default=0)
    risky_removal_count = Column(Integer, default=0)
    estimated_cleanup_hours = Column(Float, default=0.0)
    tools_used = Column(JSONB, nullable=True)
    configuration = Column(JSONB, nullable=True)
    summary = Column(JSONB, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    errors = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    items = relationship("DeadCodeItemModel", back_populates="analysis", cascade="all, delete-orphan")


class DeadCodeItemModel(Base):
    """Individual dead code finding."""
    __tablename__ = "dead_code_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("dead_code_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)
    name = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    lines_count = Column(Integer, default=1)
    language = Column(String(50), nullable=True)
    detection_method = Column(String(50), nullable=False)
    detection_tool = Column(String(100), nullable=True)
    confidence = Column(Float, default=0.7)
    removal_risk = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    references = Column(JSONB, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, nullable=True)
    call_count = Column(Integer, nullable=True)
    suggested_action = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    analysis = relationship("DeadCodeAnalysisModel", back_populates="items")

    __table_args__ = (
        Index("ix_dead_code_items_file_path", "file_path"),
        Index("ix_dead_code_items_item_type", "item_type"),
        Index("ix_dead_code_items_removal_risk", "removal_risk"),
    )


class RuntimeAnalysisModel(Base):
    """Runtime/APM analysis results."""
    __tablename__ = "runtime_analyses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    project_path = Column(String(1024), nullable=False)
    apm_provider = Column(String(100), nullable=True)
    analysis_period_start = Column(DateTime, nullable=True)
    analysis_period_end = Column(DateTime, nullable=True)
    total_endpoints = Column(Integer, default=0)
    active_endpoints = Column(Integer, default=0)
    inactive_endpoints = Column(Integer, default=0)
    total_functions = Column(Integer, default=0)
    called_functions = Column(Integer, default=0)
    uncalled_functions = Column(Integer, default=0)
    hot_paths = Column(JSONB, nullable=True)
    cold_paths = Column(JSONB, nullable=True)
    execution_traces = Column(JSONB, nullable=True)
    performance_metrics = Column(JSONB, nullable=True)
    coverage_percentage = Column(Float, default=0.0)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    errors = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())


class CodeCoverageAnalysisModel(Base):
    """Code coverage analysis results."""
    __tablename__ = "code_coverage_analyses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    project_path = Column(String(1024), nullable=False)
    coverage_source = Column(String(100), nullable=False)
    total_lines = Column(Integer, default=0)
    covered_lines = Column(Integer, default=0)
    uncovered_lines = Column(Integer, default=0)
    line_coverage_percentage = Column(Float, default=0.0)
    total_branches = Column(Integer, default=0)
    covered_branches = Column(Integer, default=0)
    branch_coverage_percentage = Column(Float, default=0.0)
    total_functions = Column(Integer, default=0)
    covered_functions = Column(Integer, default=0)
    function_coverage_percentage = Column(Float, default=0.0)
    file_coverage = Column(JSONB, nullable=True)
    uncovered_files = Column(JSONB, nullable=True)
    critical_uncovered = Column(JSONB, nullable=True)
    coverage_trends = Column(JSONB, nullable=True)
    test_suites = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    errors = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())


# ============================================================================
# Dataclasses for Service Layer
# ============================================================================

@dataclass
class DeadCodeItem:
    """Individual dead code finding."""
    item_type: DeadCodeItemType
    name: str
    file_path: str
    detection_method: DetectionMethod
    removal_risk: RemovalRisk
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    lines_count: int = 1
    language: Optional[str] = None
    detection_tool: Optional[str] = None
    confidence: float = 0.7
    reason: Optional[str] = None
    references: List[str] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    call_count: Optional[int] = None
    suggested_action: SuggestedAction = SuggestedAction.REVIEW

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_type": self.item_type.value if isinstance(self.item_type, Enum) else self.item_type,
            "name": self.name,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "lines_count": self.lines_count,
            "language": self.language,
            "detection_method": self.detection_method.value if isinstance(self.detection_method, Enum) else self.detection_method,
            "detection_tool": self.detection_tool,
            "confidence": self.confidence,
            "removal_risk": self.removal_risk.value if isinstance(self.removal_risk, Enum) else self.removal_risk,
            "reason": self.reason,
            "references": self.references,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "call_count": self.call_count,
            "suggested_action": self.suggested_action.value if isinstance(self.suggested_action, Enum) else self.suggested_action,
        }


@dataclass
class DeadCodeAnalysisResult:
    """Result of dead code analysis."""
    project_path: str
    analysis_type: AnalysisType
    items: List[DeadCodeItem] = field(default_factory=list)
    languages_detected: List[str] = field(default_factory=list)
    total_files_scanned: int = 0
    total_lines_scanned: int = 0
    dead_code_count: int = 0
    dead_lines_count: int = 0
    dead_code_percentage: float = 0.0
    safe_removal_count: int = 0
    risky_removal_count: int = 0
    estimated_cleanup_hours: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "analysis_type": self.analysis_type.value if isinstance(self.analysis_type, Enum) else self.analysis_type,
            "items": [item.to_dict() for item in self.items],
            "languages_detected": self.languages_detected,
            "total_files_scanned": self.total_files_scanned,
            "total_lines_scanned": self.total_lines_scanned,
            "dead_code_count": self.dead_code_count,
            "dead_lines_count": self.dead_lines_count,
            "dead_code_percentage": self.dead_code_percentage,
            "safe_removal_count": self.safe_removal_count,
            "risky_removal_count": self.risky_removal_count,
            "estimated_cleanup_hours": self.estimated_cleanup_hours,
            "tools_used": self.tools_used,
            "recommendations": self.recommendations,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "errors": self.errors,
        }


@dataclass
class RuntimeAnalysisResult:
    """Result of runtime/APM analysis."""
    project_path: str
    apm_provider: APMProvider = APMProvider.NONE
    analysis_period_start: Optional[datetime] = None
    analysis_period_end: Optional[datetime] = None
    total_endpoints: int = 0
    active_endpoints: int = 0
    inactive_endpoints: int = 0
    total_functions: int = 0
    called_functions: int = 0
    uncalled_functions: int = 0
    hot_paths: List[Dict[str, Any]] = field(default_factory=list)
    cold_paths: List[Dict[str, Any]] = field(default_factory=list)
    execution_traces: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    coverage_percentage: float = 0.0
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "apm_provider": self.apm_provider.value if isinstance(self.apm_provider, Enum) else self.apm_provider,
            "analysis_period_start": self.analysis_period_start.isoformat() if self.analysis_period_start else None,
            "analysis_period_end": self.analysis_period_end.isoformat() if self.analysis_period_end else None,
            "total_endpoints": self.total_endpoints,
            "active_endpoints": self.active_endpoints,
            "inactive_endpoints": self.inactive_endpoints,
            "total_functions": self.total_functions,
            "called_functions": self.called_functions,
            "uncalled_functions": self.uncalled_functions,
            "hot_paths": self.hot_paths,
            "cold_paths": self.cold_paths,
            "execution_traces": self.execution_traces,
            "performance_metrics": self.performance_metrics,
            "coverage_percentage": self.coverage_percentage,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "errors": self.errors,
        }


@dataclass
class FileCoverage:
    """Coverage data for a single file."""
    file_path: str
    total_lines: int = 0
    covered_lines: int = 0
    uncovered_lines: int = 0
    line_coverage: float = 0.0
    total_branches: int = 0
    covered_branches: int = 0
    branch_coverage: float = 0.0
    total_functions: int = 0
    covered_functions: int = 0
    function_coverage: float = 0.0
    uncovered_line_numbers: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "total_lines": self.total_lines,
            "covered_lines": self.covered_lines,
            "uncovered_lines": self.uncovered_lines,
            "line_coverage": self.line_coverage,
            "total_branches": self.total_branches,
            "covered_branches": self.covered_branches,
            "branch_coverage": self.branch_coverage,
            "total_functions": self.total_functions,
            "covered_functions": self.covered_functions,
            "function_coverage": self.function_coverage,
            "uncovered_line_numbers": self.uncovered_line_numbers,
        }


@dataclass
class CodeCoverageResult:
    """Result of code coverage analysis."""
    project_path: str
    coverage_source: CoverageSource
    total_lines: int = 0
    covered_lines: int = 0
    uncovered_lines: int = 0
    line_coverage_percentage: float = 0.0
    total_branches: int = 0
    covered_branches: int = 0
    branch_coverage_percentage: float = 0.0
    total_functions: int = 0
    covered_functions: int = 0
    function_coverage_percentage: float = 0.0
    file_coverage: List[FileCoverage] = field(default_factory=list)
    uncovered_files: List[str] = field(default_factory=list)
    critical_uncovered: List[Dict[str, Any]] = field(default_factory=list)
    coverage_trends: List[Dict[str, Any]] = field(default_factory=list)
    test_suites: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "coverage_source": self.coverage_source.value if isinstance(self.coverage_source, Enum) else self.coverage_source,
            "total_lines": self.total_lines,
            "covered_lines": self.covered_lines,
            "uncovered_lines": self.uncovered_lines,
            "line_coverage_percentage": self.line_coverage_percentage,
            "total_branches": self.total_branches,
            "covered_branches": self.covered_branches,
            "branch_coverage_percentage": self.branch_coverage_percentage,
            "total_functions": self.total_functions,
            "covered_functions": self.covered_functions,
            "function_coverage_percentage": self.function_coverage_percentage,
            "file_coverage": [fc.to_dict() for fc in self.file_coverage],
            "uncovered_files": self.uncovered_files,
            "critical_uncovered": self.critical_uncovered,
            "coverage_trends": self.coverage_trends,
            "test_suites": self.test_suites,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "errors": self.errors,
        }


# ============================================================================
# Language Detection Patterns
# ============================================================================

LANGUAGE_EXTENSIONS = {
    "typescript": [".ts", ".tsx"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "python": [".py", ".pyw"],
    "csharp": [".cs"],
    "vbnet": [".vb"],
    "java": [".java"],
    "go": [".go"],
    "rust": [".rs"],
    "php": [".php"],
    "ruby": [".rb"],
    "kotlin": [".kt", ".kts"],
    "scala": [".scala"],
    "swift": [".swift"],
}

# Confidence levels per language/tool combination
TOOL_CONFIDENCE = {
    "ts-prune": {"typescript": 0.85, "javascript": 0.80},
    "vulture": {"python": 0.70},
    "roslyn": {"csharp": 0.85},
    "custom_vb": {"vbnet": 0.65},
    "sonarqube": {"java": 0.80, "csharp": 0.80, "typescript": 0.75},
    "eslint": {"typescript": 0.70, "javascript": 0.70},
    "pylint": {"python": 0.65},
}
