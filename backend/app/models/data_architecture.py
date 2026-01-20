"""
Fase 24: Data Architecture Models

Dataclasses and SQLAlchemy models for:
- DataLineageService: Track data flow from specs to code
- ERDGeneratorService: Generate target architecture ERD
- CDCIntegrationService: Change Data Capture for dual-system sync
- JourneyComparisonService: E2E journey comparison between legacy and new

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


# ============================================
# Enums
# ============================================

class LineageNodeType(str, Enum):
    """Types of nodes in data lineage graph."""
    BROWN_PAPER_SESSION = "brown_paper_session"
    DOMAIN = "domain"
    ENTITY = "entity"
    FIELD = "field"
    EPIC = "epic"
    FEATURE = "feature"
    USER_STORY = "user_story"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    TEST_CASE = "test_case"
    CODE_FILE = "code_file"
    CODE_CLASS = "code_class"
    CODE_METHOD = "code_method"
    DATABASE_TABLE = "database_table"
    DATABASE_COLUMN = "database_column"
    API_ENDPOINT = "api_endpoint"


class LineageEdgeType(str, Enum):
    """Types of relationships in data lineage."""
    EXTRACTED_FROM = "extracted_from"        # spec extracted from code
    DEFINES = "defines"                       # story defines acceptance criteria
    IMPLEMENTED_BY = "implemented_by"         # story implemented by code
    TESTED_BY = "tested_by"                   # story tested by test case
    MAPS_TO = "maps_to"                       # legacy field maps to new field
    TRANSFORMS_TO = "transforms_to"           # field transformation
    DEPENDS_ON = "depends_on"                 # dependency relationship
    VALIDATES = "validates"                   # test validates code


class TransformationType(str, Enum):
    """Types of data transformations."""
    DIRECT_COPY = "direct_copy"              # 1:1 mapping
    RENAME = "rename"                         # field renamed
    TYPE_CHANGE = "type_change"              # data type changed
    SPLIT = "split"                          # one field becomes multiple
    MERGE = "merge"                          # multiple fields become one
    CALCULATION = "calculation"              # derived value
    LOOKUP = "lookup"                        # FK lookup
    DEFAULT = "default"                      # default value added
    NULLABLE_CHANGE = "nullable_change"      # nullable constraint changed
    FORMAT_CHANGE = "format_change"          # format changed (date, etc.)


class ERDOutputFormat(str, Enum):
    """Output formats for ERD generation."""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    DBML = "dbml"
    JSON = "json"
    DOT = "dot"  # Graphviz


class CDCEventType(str, Enum):
    """Types of CDC events."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    TRUNCATE = "truncate"
    SCHEMA_CHANGE = "schema_change"


class CDCMode(str, Enum):
    """CDC operation modes."""
    SHADOW = "shadow"          # Receive only, no writes
    MIRROR = "mirror"          # Full sync, writes allowed
    SELECTIVE = "selective"    # Only specified tables
    PAUSED = "paused"          # Temporarily stopped


class JourneyStepType(str, Enum):
    """Types of steps in a user journey."""
    NAVIGATION = "navigation"
    CLICK = "click"
    INPUT = "input"
    SUBMIT = "submit"
    WAIT = "wait"
    ASSERTION = "assertion"
    API_CALL = "api_call"
    SCREENSHOT = "screenshot"


class JourneyMatchStatus(str, Enum):
    """Status of journey step comparison."""
    MATCH = "match"
    MISMATCH = "mismatch"
    OVERRIDE_APPROVED = "override_approved"
    OVERRIDE_PENDING = "override_pending"
    SKIPPED = "skipped"


# ============================================
# Data Lineage Dataclasses
# ============================================

@dataclass
class LineageNode:
    """A node in the data lineage graph."""
    id: str
    node_type: LineageNodeType
    name: str
    description: Optional[str] = None
    source_path: Optional[str] = None  # file path or URL
    source_line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LineageEdge:
    """An edge connecting two nodes in data lineage."""
    id: str
    source_node_id: str
    target_node_id: str
    edge_type: LineageEdgeType
    transformation: Optional[TransformationType] = None
    transformation_rule: Optional[str] = None  # e.g., "UPPER(legacy_name)"
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldMapping:
    """Mapping between legacy and new field."""
    legacy_table: str
    legacy_field: str
    legacy_type: str
    new_table: str
    new_field: str
    new_type: str
    transformation: TransformationType
    transformation_rule: Optional[str] = None
    nullable_legacy: bool = True
    nullable_new: bool = True
    default_value: Optional[str] = None
    validation_rule: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ImpactAnalysisResult:
    """Result of analyzing impact of a change."""
    changed_node_id: str
    changed_node_name: str
    affected_nodes: List[LineageNode]
    affected_edges: List[LineageEdge]
    test_cases_affected: List[str]
    code_files_affected: List[str]
    stories_affected: List[str]
    risk_level: str  # low, medium, high, critical
    recommendations: List[str]


@dataclass
class LineageGraph:
    """Complete data lineage graph."""
    session_id: str
    project_id: str
    nodes: List[LineageNode] = field(default_factory=list)
    edges: List[LineageEdge] = field(default_factory=list)
    field_mappings: List[FieldMapping] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_node(self, node_id: str) -> Optional[LineageNode]:
        """Get node by ID."""
        return next((n for n in self.nodes if n.id == node_id), None)

    def get_downstream(self, node_id: str) -> List[LineageNode]:
        """Get all nodes downstream of given node."""
        downstream_ids = {e.target_node_id for e in self.edges if e.source_node_id == node_id}
        return [n for n in self.nodes if n.id in downstream_ids]

    def get_upstream(self, node_id: str) -> List[LineageNode]:
        """Get all nodes upstream of given node."""
        upstream_ids = {e.source_node_id for e in self.edges if e.target_node_id == node_id}
        return [n for n in self.nodes if n.id in upstream_ids]


# ============================================
# ERD Generator Dataclasses
# ============================================

@dataclass
class ERDColumn:
    """Column definition for ERD."""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None  # "table.column"
    unique: bool = False
    default: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ERDTable:
    """Table definition for ERD."""
    name: str
    schema: Optional[str] = None
    columns: List[ERDColumn] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    description: Optional[str] = None
    is_aggregate_root: bool = False  # DDD concept
    bounded_context: Optional[str] = None


@dataclass
class ERDRelationship:
    """Relationship between tables."""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str  # "one-to-one", "one-to-many", "many-to-many"
    on_delete: str = "NO ACTION"
    on_update: str = "NO ACTION"


@dataclass
class ERDDiagram:
    """Complete ERD diagram."""
    name: str
    tables: List[ERDTable] = field(default_factory=list)
    relationships: List[ERDRelationship] = field(default_factory=list)
    bounded_contexts: Dict[str, List[str]] = field(default_factory=dict)  # context -> table names
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mermaid(self) -> str:
        """Generate Mermaid ERD syntax."""
        lines = ["erDiagram"]

        # Add tables
        for table in self.tables:
            lines.append(f"    {table.name} {{")
            for col in table.columns:
                pk = " PK" if col.primary_key else ""
                fk = " FK" if col.foreign_key else ""
                lines.append(f"        {col.data_type} {col.name}{pk}{fk}")
            lines.append("    }")

        # Add relationships
        for rel in self.relationships:
            if rel.relationship_type == "one-to-one":
                symbol = "||--||"
            elif rel.relationship_type == "one-to-many":
                symbol = "||--o{"
            else:  # many-to-many
                symbol = "}o--o{"
            lines.append(f"    {rel.from_table} {symbol} {rel.to_table} : \"{rel.from_column}\"")

        return "\n".join(lines)

    def to_plantuml(self) -> str:
        """Generate PlantUML ERD syntax."""
        lines = ["@startuml", "!define TABLE(name) entity name << (T,#FFAAAA) >>"]

        for table in self.tables:
            lines.append(f"TABLE({table.name}) {{")
            for col in table.columns:
                pk = " <<PK>>" if col.primary_key else ""
                fk = " <<FK>>" if col.foreign_key else ""
                lines.append(f"  {col.name} : {col.data_type}{pk}{fk}")
            lines.append("}")

        for rel in self.relationships:
            if rel.relationship_type == "one-to-one":
                symbol = "||--||"
            elif rel.relationship_type == "one-to-many":
                symbol = "||--o{"
            else:
                symbol = "}o--o{"
            lines.append(f"{rel.from_table} {symbol} {rel.to_table}")

        lines.append("@enduml")
        return "\n".join(lines)


# ============================================
# CDC Integration Dataclasses
# ============================================

@dataclass
class CDCEvent:
    """A single CDC event."""
    id: str
    event_type: CDCEventType
    source_table: str
    source_schema: Optional[str] = None
    primary_key_values: Dict[str, Any] = field(default_factory=dict)
    before_values: Optional[Dict[str, Any]] = None
    after_values: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_id: Optional[str] = None
    sequence_number: int = 0


@dataclass
class CDCTableConfig:
    """Configuration for CDC on a specific table."""
    source_table: str
    target_table: str
    source_schema: Optional[str] = None
    target_schema: Optional[str] = None
    enabled: bool = True
    mode: CDCMode = CDCMode.SHADOW
    field_mappings: List[FieldMapping] = field(default_factory=list)
    filter_condition: Optional[str] = None  # SQL WHERE clause
    transform_function: Optional[str] = None  # Python function name


@dataclass
class CDCSession:
    """CDC synchronization session."""
    id: str
    source_connection: str  # connection string or name
    target_connection: str
    tables: List[CDCTableConfig] = field(default_factory=list)
    mode: CDCMode = CDCMode.SHADOW
    started_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    events_processed: int = 0
    events_failed: int = 0
    status: str = "initialized"  # initialized, running, paused, stopped, error


@dataclass
class CDCSyncStats:
    """Statistics for CDC synchronization."""
    session_id: str
    table_name: str
    inserts: int = 0
    updates: int = 0
    deletes: int = 0
    errors: int = 0
    last_event_at: Optional[datetime] = None
    avg_latency_ms: float = 0.0


# ============================================
# Journey Comparison Dataclasses
# ============================================

@dataclass
class JourneyStep:
    """A single step in a user journey."""
    step_number: int
    step_type: JourneyStepType
    selector: Optional[str] = None  # CSS selector or XPath
    action: Optional[str] = None  # click, type, etc.
    value: Optional[str] = None  # input value
    expected_result: Optional[str] = None
    screenshot_path: Optional[str] = None
    api_request: Optional[Dict[str, Any]] = None
    api_response: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: int = 0


@dataclass
class JourneyRecording:
    """A recorded user journey."""
    id: str
    name: str
    system: str  # "legacy" or "new"
    base_url: str
    description: Optional[str] = None
    steps: List[JourneyStep] = field(default_factory=list)
    total_duration_ms: int = 0
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recorded_by: Optional[str] = None


@dataclass
class JourneyStepComparison:
    """Comparison of a single step between legacy and new."""
    step_number: int
    legacy_step: JourneyStep
    new_step: JourneyStep
    status: JourneyMatchStatus
    visual_diff_path: Optional[str] = None
    visual_diff_score: float = 0.0  # 0.0 = identical, 1.0 = completely different
    data_diff: Optional[Dict[str, Any]] = None
    override_reason: Optional[str] = None
    override_approved_by: Optional[str] = None
    override_approved_at: Optional[datetime] = None


@dataclass
class JourneyOverrideRule:
    """Rule for overriding journey comparison differences."""
    id: str
    journey_name: str
    override_type: str  # "improved_ux", "intentional_change", "known_difference"
    legacy_behavior: str
    new_behavior: str
    reason: str
    approved_by: str
    step_number: Optional[int] = None  # None = applies to all steps
    approved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    active: bool = True


@dataclass
class JourneyComparisonResult:
    """Result of comparing a journey between legacy and new systems."""
    id: str
    journey_name: str
    legacy_recording_id: str
    new_recording_id: str
    step_comparisons: List[JourneyStepComparison] = field(default_factory=list)
    total_steps: int = 0
    matching_steps: int = 0
    mismatching_steps: int = 0
    overridden_steps: int = 0
    overall_match_percentage: float = 0.0
    visual_match_percentage: float = 0.0
    data_match_percentage: float = 0.0
    compared_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, passed, failed, needs_review


# ============================================
# SQLAlchemy Models
# ============================================

class DataLineageSession(Base):
    """Database model for data lineage sessions."""
    __tablename__ = "data_lineage_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=True)
    brown_paper_session_id = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    field_mapping_count = Column(Integer, default=0)
    graph_data = Column(JSON, nullable=True)  # Full LineageGraph as JSON
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DataLineageFieldMapping(Base):
    """Database model for field mappings."""
    __tablename__ = "data_lineage_field_mappings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("data_lineage_sessions.id"), nullable=False)
    legacy_table = Column(String(255), nullable=False)
    legacy_field = Column(String(255), nullable=False)
    legacy_type = Column(String(100), nullable=False)
    new_table = Column(String(255), nullable=False)
    new_field = Column(String(255), nullable=False)
    new_type = Column(String(100), nullable=False)
    transformation_type = Column(String(50), nullable=False)
    transformation_rule = Column(Text, nullable=True)
    nullable_legacy = Column(Boolean, default=True)
    nullable_new = Column(Boolean, default=True)
    default_value = Column(String(255), nullable=True)
    validation_rule = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ERDDiagramModel(Base):
    """Database model for ERD diagrams."""
    __tablename__ = "erd_diagrams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=True)
    brown_paper_session_id = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    diagram_type = Column(String(50), default="target")  # legacy, target, comparison
    table_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    diagram_data = Column(JSON, nullable=True)  # Full ERDDiagram as JSON
    mermaid_output = Column(Text, nullable=True)
    plantuml_output = Column(Text, nullable=True)
    bounded_contexts = Column(JSON, nullable=True)
    normalization_level = Column(String(10), default="3NF")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CDCSessionModel(Base):
    """Database model for CDC sessions."""
    __tablename__ = "cdc_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    source_connection_name = Column(String(255), nullable=False)
    target_connection_name = Column(String(255), nullable=False)
    mode = Column(String(50), default="shadow")
    status = Column(String(50), default="initialized")
    table_count = Column(Integer, default=0)
    events_processed = Column(Integer, default=0)
    events_failed = Column(Integer, default=0)
    last_sync_at = Column(DateTime, nullable=True)
    config = Column(JSON, nullable=True)  # Full CDC config
    stats = Column(JSON, nullable=True)  # Per-table stats
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class JourneyRecordingModel(Base):
    """Database model for journey recordings."""
    __tablename__ = "journey_recordings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system = Column(String(50), nullable=False)  # legacy, new
    base_url = Column(String(500), nullable=False)
    step_count = Column(Integer, default=0)
    total_duration_ms = Column(Integer, default=0)
    steps_data = Column(JSON, nullable=True)  # List of JourneyStep
    recorded_by = Column(String(255), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class JourneyComparisonModel(Base):
    """Database model for journey comparisons."""
    __tablename__ = "journey_comparisons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=True)
    journey_name = Column(String(255), nullable=False)
    legacy_recording_id = Column(String(36), ForeignKey("journey_recordings.id"), nullable=False)
    new_recording_id = Column(String(36), ForeignKey("journey_recordings.id"), nullable=False)
    total_steps = Column(Integer, default=0)
    matching_steps = Column(Integer, default=0)
    mismatching_steps = Column(Integer, default=0)
    overridden_steps = Column(Integer, default=0)
    overall_match_percentage = Column(Float, default=0.0)
    visual_match_percentage = Column(Float, default=0.0)
    data_match_percentage = Column(Float, default=0.0)
    status = Column(String(50), default="pending")
    comparison_data = Column(JSON, nullable=True)  # Full comparison result
    compared_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class JourneyOverrideRuleModel(Base):
    """Database model for journey override rules."""
    __tablename__ = "journey_override_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=True)
    journey_name = Column(String(255), nullable=False)
    step_number = Column(Integer, nullable=True)  # None = all steps
    override_type = Column(String(100), nullable=False)
    legacy_behavior = Column(Text, nullable=False)
    new_behavior = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    approved_by = Column(String(255), nullable=False)
    approved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
