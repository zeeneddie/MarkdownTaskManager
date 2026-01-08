"""
Week 131 Research Models - Background Jobs, Load Estimation, Documentation Rules

SQLAlchemy models and dataclasses for the three Week 131 research services:
1. BackgroundJobDetectorService - Detect scheduled tasks and batch jobs
2. LoadEstimationService - Connection pool and capacity analysis
3. DocumentationRuleExtractorService - Extract business rules from documentation

Author: Claude (AI Agent)
Created: 2025-12-31
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ============================================================================
# Enums
# ============================================================================

class JobType(str, Enum):
    """Background job schedule types."""
    NIGHTLY = "nightly"
    HOURLY = "hourly"
    ON_DEMAND = "on_demand"
    CRON = "cron"
    INTERVAL = "interval"
    EVENT_DRIVEN = "event_driven"
    STARTUP = "startup"
    DAEMON = "daemon"


class TriggerType(str, Enum):
    """Background job trigger mechanisms."""
    TIMER = "timer"
    SQL_AGENT = "sql_agent"
    QUARTZ = "quartz"
    HANGFIRE = "hangfire"
    WINDOWS_SCHEDULER = "windows_scheduler"
    WINDOWS_SERVICE = "windows_service"
    WEBMETHOD = "webmethod"
    PAGE_LOAD = "page_load"
    MANUAL = "manual"
    HTTP = "http"
    FILE_WATCHER = "file_watcher"
    EVENT_BUS = "event_bus"
    STARTUP = "startup"
    SERVICE = "service"
    MESSAGE_QUEUE = "message_queue"


class DetectionMethod(str, Enum):
    """How the job was detected."""
    NAMING = "naming"
    DIRECTORY = "directory"
    CODE_PATTERN = "code_pattern"
    CONFIG = "config"
    TABLE_SUFFIX = "table_suffix"
    COMBINED = "combined"


class ResourceIntensity(str, Enum):
    """Resource usage level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionMode(str, Enum):
    """ASP.NET session state modes."""
    IN_PROC = "InProc"
    STATE_SERVER = "StateServer"
    SQL_SERVER = "SQLServer"
    CUSTOM = "Custom"
    OFF = "Off"


class CapacityBottleneck(str, Enum):
    """Types of capacity bottlenecks."""
    CONNECTION_POOL = "connection_pool"
    SESSION_STATE = "session_state"
    QUERY_COMPLEXITY = "query_complexity"
    MEMORY = "memory"
    CPU = "cpu"
    DISK_IO = "disk_io"
    NONE = "none"


class RuleType(str, Enum):
    """Types of business rules extracted from documentation."""
    VALIDATION = "validation"
    RECOMMENDATION = "recommendation"
    OPTIONAL = "optional"
    CONDITION = "condition"
    AUTHORIZATION = "authorization"
    CALCULATION = "calculation"
    CONSTRAINT = "constraint"
    DEFAULT = "default"
    WORKFLOW = "workflow"
    NOTIFICATION = "notification"
    GENERAL = "general"


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class BackgroundJobModel(Base):
    """SQLAlchemy model for detected background jobs."""
    __tablename__ = 'background_jobs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    job_id = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    job_type = Column(String(50), nullable=False)
    schedule = Column(String(100), nullable=True)
    source_file = Column(String(500), nullable=False)
    source_line_start = Column(Integer, nullable=True)
    source_line_end = Column(Integer, nullable=True)
    entry_point = Column(String(200), nullable=True)
    trigger_type = Column(String(50), nullable=True)
    detection_method = Column(String(50), nullable=True)
    confidence = Column(Float, default=0.0)
    database_dependencies = Column(JSONB, default=[])
    file_dependencies = Column(JSONB, default=[])
    service_dependencies = Column(JSONB, default=[])
    has_error_handling = Column(Boolean, default=False)
    error_handling_pattern = Column(String(100), nullable=True)
    has_logging = Column(Boolean, default=False)
    estimated_duration = Column(String(50), nullable=True)
    resource_intensity = Column(String(20), default='medium')
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    project = relationship("Project", back_populates="background_jobs")


class LoadEstimationModel(Base):
    """SQLAlchemy model for load estimation results."""
    __tablename__ = 'load_estimations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    connection_pools = Column(JSONB, default=[])
    total_sql_connections = Column(Integer, default=0)
    using_block_count = Column(Integer, default=0)
    open_close_ratio = Column(Float, default=0.0)
    session_config = Column(JSONB, nullable=True)
    session_access_count = Column(Integer, default=0)
    session_variable_count = Column(Integer, default=0)
    query_metrics = Column(JSONB, nullable=True)
    estimated_concurrent_users = Column(Integer, default=0)
    capacity_bottleneck = Column(String(100), nullable=True)
    bottleneck_details = Column(Text, nullable=True)
    recommendations = Column(JSONB, default=[])
    analysis_path = Column(String(500), nullable=True)
    files_analyzed = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    errors = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    project = relationship("Project", back_populates="load_estimations")


class DocumentationRuleModel(Base):
    """SQLAlchemy model for documentation-extracted business rules."""
    __tablename__ = 'documentation_rules'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    rule_id = Column(String(50), nullable=False)
    rule_type = Column(String(50), nullable=False)
    condition = Column(Text, nullable=True)
    action = Column(Text, nullable=True)
    natural_language = Column(Text, nullable=True)
    source_file = Column(String(500), nullable=False)
    source_section = Column(String(500), nullable=True)
    source_line = Column(Integer, nullable=True)
    extraction_pattern = Column(String(50), nullable=True)
    confidence = Column(Float, default=0.0)
    related_code_rules = Column(JSONB, default=[])
    conflicts = Column(JSONB, default=[])
    is_validated = Column(Boolean, default=False)
    validated_by = Column(String(100), nullable=True)
    validation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    project = relationship("Project", back_populates="documentation_rules")


# ============================================================================
# Dataclasses for Service Results
# ============================================================================

@dataclass
class BackgroundJob:
    """A detected background job or scheduled task."""
    job_id: str
    name: str
    job_type: JobType
    source_file: str
    confidence: float
    trigger_type: TriggerType = TriggerType.MANUAL
    schedule: Optional[str] = None
    source_lines: Tuple[int, int] = (0, 0)
    entry_point: str = ""
    detection_method: DetectionMethod = DetectionMethod.NAMING
    database_dependencies: List[str] = field(default_factory=list)
    file_dependencies: List[str] = field(default_factory=list)
    service_dependencies: List[str] = field(default_factory=list)
    has_error_handling: bool = False
    error_handling_pattern: Optional[str] = None
    has_logging: bool = False
    estimated_duration: Optional[str] = None
    resource_intensity: ResourceIntensity = ResourceIntensity.MEDIUM
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "job_type": self.job_type.value if isinstance(self.job_type, Enum) else self.job_type,
            "schedule": self.schedule,
            "source_file": self.source_file,
            "source_lines": list(self.source_lines),
            "entry_point": self.entry_point,
            "trigger_type": self.trigger_type.value if isinstance(self.trigger_type, Enum) else self.trigger_type,
            "detection_method": self.detection_method.value if isinstance(self.detection_method, Enum) else self.detection_method,
            "confidence": self.confidence,
            "database_dependencies": self.database_dependencies,
            "file_dependencies": self.file_dependencies,
            "service_dependencies": self.service_dependencies,
            "has_error_handling": self.has_error_handling,
            "error_handling_pattern": self.error_handling_pattern,
            "has_logging": self.has_logging,
            "estimated_duration": self.estimated_duration,
            "resource_intensity": self.resource_intensity.value if isinstance(self.resource_intensity, Enum) else self.resource_intensity,
            "description": self.description,
        }


@dataclass
class BackgroundJobDetectionResult:
    """Result of background job detection scan."""
    success: bool = True
    jobs: List[BackgroundJob] = field(default_factory=list)
    job_tables: List[str] = field(default_factory=list)
    batch_directories: List[str] = field(default_factory=list)
    config_sources: List[str] = field(default_factory=list)
    detection_stats: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def total_jobs(self) -> int:
        """Total number of detected jobs."""
        return len(self.jobs)

    @property
    def files_scanned(self) -> int:
        """Number of files scanned."""
        return self.detection_stats.get("files_scanned", 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "jobs": [j.to_dict() for j in self.jobs],
            "job_tables": self.job_tables,
            "batch_directories": self.batch_directories,
            "config_sources": self.config_sources,
            "detection_stats": self.detection_stats,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_ms": self.duration_ms,
            "summary": {
                "total_jobs": len(self.jobs),
                "by_type": self._count_by_type(),
                "by_trigger": self._count_by_trigger(),
                "high_confidence": sum(1 for j in self.jobs if j.confidence >= 0.8),
            }
        }

    def _count_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for job in self.jobs:
            key = job.job_type.value if isinstance(job.job_type, Enum) else job.job_type
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_by_trigger(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for job in self.jobs:
            key = job.trigger_type.value if isinstance(job.trigger_type, Enum) else job.trigger_type
            counts[key] = counts.get(key, 0) + 1
        return counts


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration from web.config."""
    connection_string_name: str
    min_pool_size: int = 0
    max_pool_size: int = 100
    connection_timeout: int = 15
    pooling_enabled: bool = True
    source_file: str = ""
    raw_connection_string: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_string_name": self.connection_string_name,
            "min_pool_size": self.min_pool_size,
            "max_pool_size": self.max_pool_size,
            "connection_timeout": self.connection_timeout,
            "pooling_enabled": self.pooling_enabled,
            "source_file": self.source_file,
        }


@dataclass
class SessionStateConfig:
    """ASP.NET session state configuration."""
    mode: SessionMode = SessionMode.IN_PROC
    timeout_minutes: int = 20
    cookieless: bool = False
    custom_provider: Optional[str] = None
    sql_connection_string: Optional[str] = None
    state_server_address: Optional[str] = None
    source_file: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value if isinstance(self.mode, Enum) else self.mode,
            "timeout_minutes": self.timeout_minutes,
            "cookieless": self.cookieless,
            "custom_provider": self.custom_provider,
            "source_file": self.source_file,
        }


@dataclass
class QueryComplexityMetrics:
    """Query complexity analysis metrics."""
    total_queries: int = 0
    simple_queries: int = 0
    complex_queries: int = 0
    very_complex_queries: int = 0
    has_n_plus_one: bool = False
    uses_transactions: bool = False
    uses_locks: bool = False
    lock_patterns: List[str] = field(default_factory=list)
    avg_join_count: float = 0.0
    max_join_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "simple_queries": self.simple_queries,
            "complex_queries": self.complex_queries,
            "very_complex_queries": self.very_complex_queries,
            "has_n_plus_one": self.has_n_plus_one,
            "uses_transactions": self.uses_transactions,
            "uses_locks": self.uses_locks,
            "lock_patterns": self.lock_patterns,
            "avg_join_count": self.avg_join_count,
            "max_join_count": self.max_join_count,
            "complexity_rating": self._get_complexity_rating(),
        }

    def _get_complexity_rating(self) -> str:
        if self.very_complex_queries > 10 or self.has_n_plus_one:
            return "critical"
        if self.very_complex_queries > 5 or self.complex_queries > 20:
            return "high"
        if self.complex_queries > 10:
            return "medium"
        return "low"


@dataclass
class LoadEstimationResult:
    """Result of load estimation analysis."""
    success: bool = True
    connection_pools: List[ConnectionPoolConfig] = field(default_factory=list)
    total_sql_connections: int = 0
    using_block_count: int = 0
    open_close_ratio: float = 0.0
    session_config: Optional[SessionStateConfig] = None
    session_access_count: int = 0
    session_variable_count: int = 0
    query_metrics: Optional[QueryComplexityMetrics] = None
    estimated_concurrent_users: int = 0
    capacity_bottleneck: CapacityBottleneck = CapacityBottleneck.NONE
    bottleneck_details: str = ""
    recommendations: List[str] = field(default_factory=list)
    files_analyzed: int = 0
    errors: List[str] = field(default_factory=list)
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "connection_pools": [cp.to_dict() for cp in self.connection_pools],
            "total_sql_connections": self.total_sql_connections,
            "using_block_count": self.using_block_count,
            "open_close_ratio": self.open_close_ratio,
            "session_config": self.session_config.to_dict() if self.session_config else None,
            "session_access_count": self.session_access_count,
            "session_variable_count": self.session_variable_count,
            "query_metrics": self.query_metrics.to_dict() if self.query_metrics else None,
            "estimated_concurrent_users": self.estimated_concurrent_users,
            "capacity_bottleneck": self.capacity_bottleneck.value if isinstance(self.capacity_bottleneck, Enum) else self.capacity_bottleneck,
            "bottleneck_details": self.bottleneck_details,
            "recommendations": self.recommendations,
            "files_analyzed": self.files_analyzed,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
        }


@dataclass
class DocumentationRule:
    """A business rule extracted from documentation."""
    rule_id: str
    rule_type: str
    natural_language: str
    source_file: str
    confidence: float
    condition: str = ""
    action: str = ""
    source_section: str = ""
    source_line: int = 0
    extraction_pattern: str = ""
    related_code_rules: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "condition": self.condition,
            "action": self.action,
            "natural_language": self.natural_language,
            "source_file": self.source_file,
            "source_section": self.source_section,
            "source_line": self.source_line,
            "extraction_pattern": self.extraction_pattern,
            "confidence": self.confidence,
            "related_code_rules": self.related_code_rules,
            "conflicts": self.conflicts,
        }


@dataclass
class DocumentationExtractionResult:
    """Result of documentation rule extraction."""
    success: bool = True
    rules: List[DocumentationRule] = field(default_factory=list)
    files_processed: List[str] = field(default_factory=list)
    files_by_type: Dict[str, int] = field(default_factory=dict)
    total_sections_scanned: int = 0
    rules_by_pattern: Dict[str, int] = field(default_factory=dict)
    rules_by_type: Dict[str, int] = field(default_factory=dict)
    code_rule_matches: int = 0
    conflicts_detected: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def total_rules(self) -> int:
        """Total number of extracted rules."""
        return len(self.rules)

    @property
    def files_scanned(self) -> int:
        """Number of files scanned."""
        return len(self.files_processed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "rules": [r.to_dict() for r in self.rules],
            "files_processed": self.files_processed,
            "files_by_type": self.files_by_type,
            "total_sections_scanned": self.total_sections_scanned,
            "rules_by_pattern": self.rules_by_pattern,
            "rules_by_type": self.rules_by_type,
            "code_rule_matches": self.code_rule_matches,
            "conflicts_detected": self.conflicts_detected,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_ms": self.duration_ms,
            "summary": {
                "total_rules": self.total_rules,
                "high_confidence": sum(1 for r in self.rules if r.confidence >= 0.8),
                "with_conflicts": sum(1 for r in self.rules if r.conflicts),
                "linked_to_code": sum(1 for r in self.rules if r.related_code_rules),
            }
        }
