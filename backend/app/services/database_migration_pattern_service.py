"""
Database Migration Pattern Service - Central Pattern Catalog

Fase 24 GAP Item D4: Database Migration Patterns
Week 159 - Centralized pattern catalog for database migration strategies.

This service provides a comprehensive catalog of database migration patterns,
including recommendations based on project scenarios and risk assessments.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MigrationPatternType(str, Enum):
    """Supported database migration pattern types."""

    DUAL_WRITE = "dual_write"
    CDC_SYNC = "cdc_sync"
    BULK_LOAD = "bulk_load"
    SHADOW_TABLE = "shadow_table"
    BLUE_GREEN = "blue_green"
    TRICKLE_MIGRATION = "trickle_migration"
    STRANGLER_FIG = "strangler_fig"
    EXPAND_CONTRACT = "expand_contract"


class RiskLevel(str, Enum):
    """Risk level classification for migration patterns."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataVolumeCategory(str, Enum):
    """Data volume categories for pattern selection."""

    SMALL = "small"          # < 1GB
    MEDIUM = "medium"        # 1GB - 100GB
    LARGE = "large"          # 100GB - 1TB
    VERY_LARGE = "very_large"  # > 1TB


class DowntimeRequirement(str, Enum):
    """Downtime tolerance categories."""

    ZERO = "zero"            # No downtime allowed
    MINIMAL = "minimal"      # < 5 minutes
    SHORT = "short"          # 5-60 minutes
    EXTENDED = "extended"    # Hours acceptable


@dataclass
class PatternPrerequisite:
    """Prerequisite for using a migration pattern."""

    name: str
    description: str
    is_required: bool = True
    verification_query: Optional[str] = None


@dataclass
class PatternRisk:
    """Risk associated with a migration pattern."""

    name: str
    description: str
    level: RiskLevel
    mitigation: str


@dataclass
class PatternPhase:
    """Phase in executing a migration pattern."""

    order: int
    name: str
    description: str
    estimated_effort_hours: float
    rollback_possible: bool = True


@dataclass
class MigrationPattern:
    """Complete definition of a database migration pattern."""

    pattern_type: MigrationPatternType
    name: str
    description: str

    # Suitability criteria
    suitable_data_volumes: List[DataVolumeCategory]
    suitable_downtime_requirements: List[DowntimeRequirement]
    suitable_scenarios: List[str]

    # Implementation details
    prerequisites: List[PatternPrerequisite]
    phases: List[PatternPhase]
    risks: List[PatternRisk]

    # Metrics
    complexity_score: int  # 1-10
    recommended_team_size: int
    typical_duration_weeks: float

    # Additional metadata
    related_patterns: List[MigrationPatternType] = field(default_factory=list)
    tools_supported: List[str] = field(default_factory=list)
    database_types_supported: List[str] = field(default_factory=list)

    # Documentation
    documentation_url: Optional[str] = None
    example_projects: List[str] = field(default_factory=list)


@dataclass
class PatternRecommendation:
    """Recommendation result for a migration scenario."""

    pattern: MigrationPattern
    score: float  # 0-100
    reasons: List[str]
    warnings: List[str] = field(default_factory=list)
    alternatives: List[MigrationPatternType] = field(default_factory=list)


@dataclass
class PatternRiskAssessment:
    """Risk assessment for applying a pattern to a specific scenario."""

    pattern_type: MigrationPatternType
    overall_risk_level: RiskLevel
    risk_score: int  # 1-100
    identified_risks: List[PatternRisk]
    mitigations_required: List[str]
    go_no_go_recommendation: str  # "GO", "GO_WITH_CAUTION", "NO_GO"
    assessment_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DatabaseMigrationPatternService:
    """
    Central service for database migration pattern management.

    Provides pattern catalog, recommendations, and risk assessments
    for database migration strategies.
    """

    def __init__(self):
        """Initialize the pattern service with the complete catalog."""
        self._patterns: Dict[MigrationPatternType, MigrationPattern] = {}
        self._initialize_pattern_catalog()
        logger.info(
            f"DatabaseMigrationPatternService initialized with "
            f"{len(self._patterns)} patterns"
        )

    def _initialize_pattern_catalog(self) -> None:
        """Initialize all migration patterns in the catalog."""

        # Pattern 1: Dual Write
        self._patterns[MigrationPatternType.DUAL_WRITE] = MigrationPattern(
            pattern_type=MigrationPatternType.DUAL_WRITE,
            name="Dual Write Pattern",
            description=(
                "Write data to both legacy and new database simultaneously. "
                "Enables gradual migration with real-time data consistency "
                "validation between systems."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.SMALL,
                DataVolumeCategory.MEDIUM
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.ZERO,
                DowntimeRequirement.MINIMAL
            ],
            suitable_scenarios=[
                "Real-time data synchronization required",
                "Gradual migration with rollback capability",
                "High availability systems",
                "Financial transaction systems"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="Application code access",
                    description="Ability to modify application write logic",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Network connectivity",
                    description="Both databases accessible from application",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Schema compatibility",
                    description="Target schema can accept source data format",
                    is_required=True
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="Setup",
                    description="Configure dual write infrastructure",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=2,
                    name="Shadow writes",
                    description="Enable writes to new DB (async, non-blocking)",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=3,
                    name="Validation",
                    description="Compare data consistency between databases",
                    estimated_effort_hours=24.0
                ),
                PatternPhase(
                    order=4,
                    name="Cutover",
                    description="Switch primary reads to new database",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=5,
                    name="Decommission",
                    description="Remove legacy database writes",
                    estimated_effort_hours=4.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Data inconsistency",
                    description="Writes may succeed in one DB but fail in other",
                    level=RiskLevel.HIGH,
                    mitigation="Implement transaction coordinator or eventual consistency checks"
                ),
                PatternRisk(
                    name="Performance impact",
                    description="Double write latency affects application performance",
                    level=RiskLevel.MEDIUM,
                    mitigation="Use async writes to secondary database"
                ),
                PatternRisk(
                    name="Complexity",
                    description="Application code becomes more complex",
                    level=RiskLevel.MEDIUM,
                    mitigation="Use abstraction layer for database operations"
                )
            ],
            complexity_score=7,
            recommended_team_size=3,
            typical_duration_weeks=4,
            related_patterns=[
                MigrationPatternType.CDC_SYNC,
                MigrationPatternType.SHADOW_TABLE
            ],
            tools_supported=["Debezium", "Custom middleware", "Database triggers"],
            database_types_supported=["PostgreSQL", "MySQL", "SQL Server", "Oracle"]
        )

        # Pattern 2: CDC Sync
        self._patterns[MigrationPatternType.CDC_SYNC] = MigrationPattern(
            pattern_type=MigrationPatternType.CDC_SYNC,
            name="Change Data Capture Synchronization",
            description=(
                "Capture database changes at the log level and replicate to "
                "target database. Provides near real-time sync without "
                "application code changes."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.MEDIUM,
                DataVolumeCategory.LARGE,
                DataVolumeCategory.VERY_LARGE
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.ZERO,
                DowntimeRequirement.MINIMAL
            ],
            suitable_scenarios=[
                "Large data volumes with continuous changes",
                "Cannot modify application code",
                "Real-time analytics pipelines",
                "Data warehouse synchronization"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="Database log access",
                    description="Access to transaction logs (binlog, WAL, redo logs)",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="CDC tool",
                    description="Debezium, Oracle GoldenGate, or similar",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Message queue",
                    description="Kafka or similar for change event streaming",
                    is_required=False
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="CDC Setup",
                    description="Install and configure CDC connector",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=2,
                    name="Initial snapshot",
                    description="Full database snapshot to target",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=3,
                    name="Stream changes",
                    description="Enable continuous change streaming",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=4,
                    name="Validation",
                    description="Verify data consistency and lag",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=5,
                    name="Cutover",
                    description="Switch application to new database",
                    estimated_effort_hours=4.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Replication lag",
                    description="Changes may take time to propagate",
                    level=RiskLevel.MEDIUM,
                    mitigation="Monitor lag metrics, size infrastructure appropriately"
                ),
                PatternRisk(
                    name="Schema changes",
                    description="DDL changes may break replication",
                    level=RiskLevel.HIGH,
                    mitigation="Coordinate schema changes, use schema registry"
                ),
                PatternRisk(
                    name="Log retention",
                    description="Logs may be purged before capture",
                    level=RiskLevel.MEDIUM,
                    mitigation="Configure adequate log retention period"
                )
            ],
            complexity_score=6,
            recommended_team_size=2,
            typical_duration_weeks=3,
            related_patterns=[
                MigrationPatternType.DUAL_WRITE,
                MigrationPatternType.TRICKLE_MIGRATION
            ],
            tools_supported=[
                "Debezium", "Oracle GoldenGate", "AWS DMS",
                "Azure Data Factory", "Striim", "Attunity"
            ],
            database_types_supported=[
                "PostgreSQL", "MySQL", "SQL Server", "Oracle",
                "MongoDB", "Cassandra"
            ]
        )

        # Pattern 3: Bulk Load
        self._patterns[MigrationPatternType.BULK_LOAD] = MigrationPattern(
            pattern_type=MigrationPatternType.BULK_LOAD,
            name="Bulk Load Migration",
            description=(
                "Export data from source, transform as needed, and bulk import "
                "to target. Simple approach suitable for maintenance windows."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.SMALL,
                DataVolumeCategory.MEDIUM,
                DataVolumeCategory.LARGE
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.SHORT,
                DowntimeRequirement.EXTENDED
            ],
            suitable_scenarios=[
                "Scheduled maintenance window available",
                "One-time migration without continuous sync",
                "Data archival projects",
                "Development/test environment refresh"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="Downtime window",
                    description="Planned maintenance window for migration",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Storage capacity",
                    description="Sufficient disk space for export files",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="ETL tooling",
                    description="Tools for data extraction and loading",
                    is_required=False
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="Preparation",
                    description="Plan export/import scripts, validate schemas",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=2,
                    name="Export",
                    description="Extract data from source database",
                    estimated_effort_hours=4.0,
                    rollback_possible=True
                ),
                PatternPhase(
                    order=3,
                    name="Transform",
                    description="Apply data transformations if needed",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=4,
                    name="Load",
                    description="Import data to target database",
                    estimated_effort_hours=4.0
                ),
                PatternPhase(
                    order=5,
                    name="Validation",
                    description="Verify row counts and data integrity",
                    estimated_effort_hours=4.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Downtime required",
                    description="Application must be offline during migration",
                    level=RiskLevel.MEDIUM,
                    mitigation="Schedule during low-traffic periods"
                ),
                PatternRisk(
                    name="Data staleness",
                    description="Changes during migration may be lost",
                    level=RiskLevel.HIGH,
                    mitigation="Implement freeze period or delta sync"
                ),
                PatternRisk(
                    name="Load failures",
                    description="Import may fail partway through",
                    level=RiskLevel.MEDIUM,
                    mitigation="Use transactional loads, implement checkpoints"
                )
            ],
            complexity_score=3,
            recommended_team_size=2,
            typical_duration_weeks=1,
            related_patterns=[
                MigrationPatternType.TRICKLE_MIGRATION
            ],
            tools_supported=[
                "pg_dump/pg_restore", "mysqldump", "bcp",
                "Oracle Data Pump", "AWS DMS", "Talend"
            ],
            database_types_supported=[
                "PostgreSQL", "MySQL", "SQL Server", "Oracle",
                "SQLite", "MariaDB"
            ]
        )

        # Pattern 4: Shadow Table
        self._patterns[MigrationPatternType.SHADOW_TABLE] = MigrationPattern(
            pattern_type=MigrationPatternType.SHADOW_TABLE,
            name="Shadow Table Migration",
            description=(
                "Create parallel 'shadow' tables in the same database with new "
                "schema. Migrate data incrementally while old tables remain active."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.SMALL,
                DataVolumeCategory.MEDIUM
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.ZERO,
                DowntimeRequirement.MINIMAL
            ],
            suitable_scenarios=[
                "Schema evolution within same database",
                "Column type changes",
                "Table restructuring",
                "Index optimization"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="Database space",
                    description="Sufficient space for duplicate tables",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Trigger support",
                    description="Database supports triggers for sync",
                    is_required=False
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="Create shadows",
                    description="Create shadow tables with new schema",
                    estimated_effort_hours=4.0
                ),
                PatternPhase(
                    order=2,
                    name="Setup sync",
                    description="Configure triggers or dual-write for sync",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=3,
                    name="Backfill",
                    description="Copy existing data to shadow tables",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=4,
                    name="Verify",
                    description="Validate data consistency",
                    estimated_effort_hours=4.0
                ),
                PatternPhase(
                    order=5,
                    name="Rename",
                    description="Atomic rename to swap tables",
                    estimated_effort_hours=2.0
                ),
                PatternPhase(
                    order=6,
                    name="Cleanup",
                    description="Drop old tables and triggers",
                    estimated_effort_hours=2.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Space exhaustion",
                    description="Duplicate tables consume significant space",
                    level=RiskLevel.MEDIUM,
                    mitigation="Monitor disk usage, clean up promptly"
                ),
                PatternRisk(
                    name="Sync complexity",
                    description="Keeping shadow tables in sync is error-prone",
                    level=RiskLevel.MEDIUM,
                    mitigation="Use proven trigger patterns or CDC"
                ),
                PatternRisk(
                    name="Performance impact",
                    description="Triggers add write overhead",
                    level=RiskLevel.LOW,
                    mitigation="Optimize triggers, consider async sync"
                )
            ],
            complexity_score=5,
            recommended_team_size=2,
            typical_duration_weeks=2,
            related_patterns=[
                MigrationPatternType.EXPAND_CONTRACT,
                MigrationPatternType.DUAL_WRITE
            ],
            tools_supported=[
                "pt-online-schema-change", "gh-ost",
                "pg_repack", "Database triggers"
            ],
            database_types_supported=["PostgreSQL", "MySQL", "MariaDB"]
        )

        # Pattern 5: Blue-Green
        self._patterns[MigrationPatternType.BLUE_GREEN] = MigrationPattern(
            pattern_type=MigrationPatternType.BLUE_GREEN,
            name="Blue-Green Database Migration",
            description=(
                "Maintain two complete database environments (blue and green). "
                "Sync data, then switch traffic atomically between environments."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.SMALL,
                DataVolumeCategory.MEDIUM,
                DataVolumeCategory.LARGE
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.ZERO,
                DowntimeRequirement.MINIMAL
            ],
            suitable_scenarios=[
                "Complete platform migrations",
                "Cloud-to-cloud migrations",
                "Major version upgrades",
                "Multi-region deployments"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="Duplicate infrastructure",
                    description="Resources for complete second environment",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Traffic management",
                    description="Load balancer or DNS for traffic switching",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Data sync mechanism",
                    description="CDC or replication between environments",
                    is_required=True
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="Green setup",
                    description="Provision and configure green environment",
                    estimated_effort_hours=24.0
                ),
                PatternPhase(
                    order=2,
                    name="Data sync",
                    description="Establish data replication blue -> green",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=3,
                    name="Application deploy",
                    description="Deploy application to green environment",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=4,
                    name="Testing",
                    description="Validate green environment functionality",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=5,
                    name="Cutover",
                    description="Switch traffic from blue to green",
                    estimated_effort_hours=2.0
                ),
                PatternPhase(
                    order=6,
                    name="Monitoring",
                    description="Monitor green environment, keep blue as fallback",
                    estimated_effort_hours=8.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Cost",
                    description="Running duplicate environments is expensive",
                    level=RiskLevel.MEDIUM,
                    mitigation="Plan for quick decommission of blue environment"
                ),
                PatternRisk(
                    name="Data drift",
                    description="Data may diverge during cutover",
                    level=RiskLevel.HIGH,
                    mitigation="Implement bidirectional sync or freeze writes"
                ),
                PatternRisk(
                    name="Configuration drift",
                    description="Environments may not be identical",
                    level=RiskLevel.MEDIUM,
                    mitigation="Use infrastructure as code"
                )
            ],
            complexity_score=8,
            recommended_team_size=4,
            typical_duration_weeks=6,
            related_patterns=[
                MigrationPatternType.CDC_SYNC,
                MigrationPatternType.STRANGLER_FIG
            ],
            tools_supported=[
                "Kubernetes", "AWS RDS", "Azure SQL",
                "Terraform", "Database replication"
            ],
            database_types_supported=[
                "PostgreSQL", "MySQL", "SQL Server", "Oracle",
                "Cloud-managed databases"
            ]
        )

        # Pattern 6: Trickle Migration
        self._patterns[MigrationPatternType.TRICKLE_MIGRATION] = MigrationPattern(
            pattern_type=MigrationPatternType.TRICKLE_MIGRATION,
            name="Trickle Migration",
            description=(
                "Migrate data in small batches over time during low-traffic periods. "
                "Minimizes impact on production while gradually moving data."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.LARGE,
                DataVolumeCategory.VERY_LARGE
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.ZERO,
                DowntimeRequirement.MINIMAL
            ],
            suitable_scenarios=[
                "Very large datasets",
                "Cannot afford extended downtime",
                "Limited network bandwidth",
                "Historical data archival"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="Partitionable data",
                    description="Data can be divided into independent batches",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Batch tracking",
                    description="Mechanism to track migrated batches",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Scheduling",
                    description="Job scheduler for automated batches",
                    is_required=False
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="Planning",
                    description="Define batch criteria and schedule",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=2,
                    name="Batch scripts",
                    description="Develop batch migration scripts",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=3,
                    name="Pilot batch",
                    description="Migrate first batch, validate",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=4,
                    name="Automated migration",
                    description="Run scheduled batch migrations",
                    estimated_effort_hours=40.0
                ),
                PatternPhase(
                    order=5,
                    name="Verification",
                    description="Validate all data migrated correctly",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=6,
                    name="Cutover",
                    description="Final sync and application switch",
                    estimated_effort_hours=4.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Long duration",
                    description="Migration takes extended period",
                    level=RiskLevel.LOW,
                    mitigation="Acceptable trade-off for zero downtime"
                ),
                PatternRisk(
                    name="Data consistency",
                    description="Partial migration state is complex",
                    level=RiskLevel.HIGH,
                    mitigation="Use clear batch boundaries, implement routing"
                ),
                PatternRisk(
                    name="Batch failures",
                    description="Individual batches may fail",
                    level=RiskLevel.MEDIUM,
                    mitigation="Implement retry logic and monitoring"
                )
            ],
            complexity_score=6,
            recommended_team_size=2,
            typical_duration_weeks=8,
            related_patterns=[
                MigrationPatternType.BULK_LOAD,
                MigrationPatternType.CDC_SYNC
            ],
            tools_supported=[
                "Custom scripts", "Apache Airflow", "AWS Glue",
                "Informatica", "Talend"
            ],
            database_types_supported=[
                "PostgreSQL", "MySQL", "SQL Server", "Oracle",
                "BigQuery", "Snowflake"
            ]
        )

        # Pattern 7: Strangler Fig
        self._patterns[MigrationPatternType.STRANGLER_FIG] = MigrationPattern(
            pattern_type=MigrationPatternType.STRANGLER_FIG,
            name="Strangler Fig Pattern",
            description=(
                "Gradually replace legacy database access with new database "
                "by routing specific operations to the new system while "
                "legacy handles remaining operations."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.MEDIUM,
                DataVolumeCategory.LARGE,
                DataVolumeCategory.VERY_LARGE
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.ZERO
            ],
            suitable_scenarios=[
                "Legacy system modernization",
                "Microservices decomposition",
                "Gradual feature migration",
                "Risk-averse organizations"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="API layer",
                    description="Ability to route requests at API/service level",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Feature flags",
                    description="System for controlling feature routing",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Monitoring",
                    description="Comprehensive observability for both systems",
                    is_required=True
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="Facade",
                    description="Create abstraction layer over legacy",
                    estimated_effort_hours=24.0
                ),
                PatternPhase(
                    order=2,
                    name="New implementation",
                    description="Build new database and service layer",
                    estimated_effort_hours=40.0
                ),
                PatternPhase(
                    order=3,
                    name="Feature routing",
                    description="Route first features to new system",
                    estimated_effort_hours=16.0
                ),
                PatternPhase(
                    order=4,
                    name="Incremental migration",
                    description="Gradually migrate remaining features",
                    estimated_effort_hours=80.0
                ),
                PatternPhase(
                    order=5,
                    name="Decommission",
                    description="Remove legacy system when fully migrated",
                    estimated_effort_hours=16.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Extended timeline",
                    description="Full migration takes months or years",
                    level=RiskLevel.MEDIUM,
                    mitigation="Define clear milestones and deadlines"
                ),
                PatternRisk(
                    name="Dual maintenance",
                    description="Must maintain both systems during migration",
                    level=RiskLevel.HIGH,
                    mitigation="Minimize changes to legacy, prioritize migration"
                ),
                PatternRisk(
                    name="Complexity",
                    description="Routing logic becomes complex",
                    level=RiskLevel.MEDIUM,
                    mitigation="Use well-tested routing patterns"
                )
            ],
            complexity_score=9,
            recommended_team_size=5,
            typical_duration_weeks=24,
            related_patterns=[
                MigrationPatternType.BLUE_GREEN,
                MigrationPatternType.DUAL_WRITE
            ],
            tools_supported=[
                "API Gateway", "Service Mesh", "Feature flags",
                "Kong", "Istio", "LaunchDarkly"
            ],
            database_types_supported=[
                "Any - pattern is database agnostic"
            ]
        )

        # Pattern 8: Expand-Contract
        self._patterns[MigrationPatternType.EXPAND_CONTRACT] = MigrationPattern(
            pattern_type=MigrationPatternType.EXPAND_CONTRACT,
            name="Expand-Contract Migration",
            description=(
                "Three-phase schema migration: Expand (add new structure), "
                "Migrate (move data and update code), Contract (remove old structure). "
                "Enables safe, reversible schema changes."
            ),
            suitable_data_volumes=[
                DataVolumeCategory.SMALL,
                DataVolumeCategory.MEDIUM,
                DataVolumeCategory.LARGE
            ],
            suitable_downtime_requirements=[
                DowntimeRequirement.ZERO,
                DowntimeRequirement.MINIMAL
            ],
            suitable_scenarios=[
                "Column renames or type changes",
                "Table splits or merges",
                "Backward-compatible API changes",
                "Continuous deployment environments"
            ],
            prerequisites=[
                PatternPrerequisite(
                    name="Version control",
                    description="Schema versioning and migration tooling",
                    is_required=True
                ),
                PatternPrerequisite(
                    name="Deployment pipeline",
                    description="Ability to deploy in multiple phases",
                    is_required=True
                )
            ],
            phases=[
                PatternPhase(
                    order=1,
                    name="Expand",
                    description="Add new columns/tables alongside old",
                    estimated_effort_hours=4.0
                ),
                PatternPhase(
                    order=2,
                    name="Code update",
                    description="Update application to write to both",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=3,
                    name="Data migration",
                    description="Copy/transform existing data to new structure",
                    estimated_effort_hours=8.0
                ),
                PatternPhase(
                    order=4,
                    name="Read switch",
                    description="Update application to read from new structure",
                    estimated_effort_hours=4.0
                ),
                PatternPhase(
                    order=5,
                    name="Contract",
                    description="Remove old structure when no longer needed",
                    estimated_effort_hours=4.0
                )
            ],
            risks=[
                PatternRisk(
                    name="Forgotten cleanup",
                    description="Old structures may never be removed",
                    level=RiskLevel.LOW,
                    mitigation="Track migrations, set deadlines for contract phase"
                ),
                PatternRisk(
                    name="Code complexity",
                    description="Dual-structure code during migration",
                    level=RiskLevel.LOW,
                    mitigation="Keep migration window short"
                )
            ],
            complexity_score=4,
            recommended_team_size=2,
            typical_duration_weeks=2,
            related_patterns=[
                MigrationPatternType.SHADOW_TABLE
            ],
            tools_supported=[
                "Flyway", "Liquibase", "Alembic",
                "Rails migrations", "Django migrations"
            ],
            database_types_supported=[
                "PostgreSQL", "MySQL", "SQL Server", "Oracle",
                "SQLite", "Any SQL database"
            ]
        )

    # =========================================================================
    # Public API Methods
    # =========================================================================

    def get_pattern(
        self,
        pattern_type: MigrationPatternType
    ) -> Optional[MigrationPattern]:
        """
        Get a specific migration pattern by type.

        Args:
            pattern_type: The pattern type to retrieve

        Returns:
            The migration pattern or None if not found
        """
        return self._patterns.get(pattern_type)

    def list_patterns(self) -> List[MigrationPattern]:
        """
        List all available migration patterns.

        Returns:
            List of all migration patterns in the catalog
        """
        return list(self._patterns.values())

    def get_patterns_for_scenario(
        self,
        data_volume: DataVolumeCategory,
        downtime_requirement: DowntimeRequirement,
        scenario_keywords: Optional[List[str]] = None
    ) -> List[MigrationPattern]:
        """
        Get patterns suitable for a specific migration scenario.

        Args:
            data_volume: The data volume category
            downtime_requirement: The downtime tolerance
            scenario_keywords: Optional keywords to match against scenarios

        Returns:
            List of suitable patterns, ordered by relevance
        """
        suitable = []

        for pattern in self._patterns.values():
            # Check data volume suitability
            if data_volume not in pattern.suitable_data_volumes:
                continue

            # Check downtime requirement
            if downtime_requirement not in pattern.suitable_downtime_requirements:
                continue

            # If keywords provided, check scenario match
            if scenario_keywords:
                scenario_text = " ".join(pattern.suitable_scenarios).lower()
                keyword_matches = sum(
                    1 for kw in scenario_keywords
                    if kw.lower() in scenario_text
                )
                if keyword_matches == 0:
                    continue

            suitable.append(pattern)

        # Sort by complexity (lower is better for most cases)
        suitable.sort(key=lambda p: p.complexity_score)

        return suitable

    def recommend_pattern(
        self,
        data_volume: DataVolumeCategory,
        downtime_requirement: DowntimeRequirement,
        scenario_description: str,
        source_db_type: Optional[str] = None,
        target_db_type: Optional[str] = None,
        team_size: Optional[int] = None,
        max_duration_weeks: Optional[float] = None
    ) -> List[PatternRecommendation]:
        """
        Get pattern recommendations for a migration scenario.

        Args:
            data_volume: The data volume category
            downtime_requirement: The downtime tolerance
            scenario_description: Free-text description of the migration
            source_db_type: Source database type (e.g., "Oracle", "SQL Server")
            target_db_type: Target database type (e.g., "PostgreSQL")
            team_size: Available team size
            max_duration_weeks: Maximum acceptable duration in weeks

        Returns:
            List of recommendations ordered by score (highest first)
        """
        recommendations = []
        scenario_words = scenario_description.lower().split()

        for pattern in self._patterns.values():
            score = 0.0
            reasons = []
            warnings = []

            # Score based on data volume match (25 points)
            if data_volume in pattern.suitable_data_volumes:
                score += 25
                reasons.append(
                    f"Suitable for {data_volume.value} data volumes"
                )
            else:
                score -= 20
                warnings.append(
                    f"Pattern not ideal for {data_volume.value} data volumes"
                )

            # Score based on downtime match (25 points)
            if downtime_requirement in pattern.suitable_downtime_requirements:
                score += 25
                reasons.append(
                    f"Meets {downtime_requirement.value} downtime requirement"
                )
            else:
                score -= 30
                warnings.append(
                    f"May not meet {downtime_requirement.value} downtime requirement"
                )

            # Score based on scenario keyword matches (20 points max)
            scenario_text = " ".join(pattern.suitable_scenarios).lower()
            keyword_matches = sum(
                1 for word in scenario_words
                if word in scenario_text and len(word) > 3
            )
            keyword_score = min(keyword_matches * 5, 20)
            score += keyword_score
            if keyword_matches > 0:
                reasons.append(
                    f"Scenario matches {keyword_matches} keywords"
                )

            # Score based on database support (10 points)
            if source_db_type or target_db_type:
                db_supported = True
                if source_db_type:
                    if not any(
                        source_db_type.lower() in db.lower()
                        for db in pattern.database_types_supported
                    ):
                        db_supported = False
                if target_db_type:
                    if not any(
                        target_db_type.lower() in db.lower()
                        for db in pattern.database_types_supported
                    ):
                        db_supported = False

                if db_supported:
                    score += 10
                    reasons.append("Supports required database types")
                else:
                    score -= 10
                    warnings.append(
                        "May not fully support required database types"
                    )

            # Score based on team size (10 points)
            if team_size:
                if team_size >= pattern.recommended_team_size:
                    score += 10
                    reasons.append(
                        f"Team size ({team_size}) meets recommendation "
                        f"({pattern.recommended_team_size})"
                    )
                else:
                    score += 5
                    warnings.append(
                        f"Team size ({team_size}) below recommendation "
                        f"({pattern.recommended_team_size})"
                    )

            # Score based on duration (10 points)
            if max_duration_weeks:
                if pattern.typical_duration_weeks <= max_duration_weeks:
                    score += 10
                    reasons.append(
                        f"Typical duration ({pattern.typical_duration_weeks}w) "
                        f"within limit ({max_duration_weeks}w)"
                    )
                else:
                    score -= 5
                    warnings.append(
                        f"Typical duration ({pattern.typical_duration_weeks}w) "
                        f"exceeds limit ({max_duration_weeks}w)"
                    )

            # Normalize score to 0-100
            score = max(0, min(100, score))

            # Get alternative patterns
            alternatives = [
                alt for alt in pattern.related_patterns
                if alt != pattern.pattern_type
            ]

            recommendations.append(PatternRecommendation(
                pattern=pattern,
                score=score,
                reasons=reasons,
                warnings=warnings,
                alternatives=alternatives
            ))

        # Sort by score descending
        recommendations.sort(key=lambda r: r.score, reverse=True)

        return recommendations

    def assess_pattern_risk(
        self,
        pattern_type: MigrationPatternType,
        data_volume: DataVolumeCategory,
        has_downtime_window: bool,
        team_experience_level: str,  # "junior", "mid", "senior", "expert"
        critical_data: bool = False,
        regulatory_requirements: bool = False
    ) -> Optional[PatternRiskAssessment]:
        """
        Assess the risk of applying a pattern to a specific scenario.

        Args:
            pattern_type: The pattern to assess
            data_volume: The data volume category
            has_downtime_window: Whether a downtime window is available
            team_experience_level: Team's experience level
            critical_data: Whether data is business-critical
            regulatory_requirements: Whether there are compliance requirements

        Returns:
            Risk assessment or None if pattern not found
        """
        pattern = self._patterns.get(pattern_type)
        if not pattern:
            return None

        identified_risks = list(pattern.risks)
        mitigations_required = []
        risk_score = 0

        # Base risk from pattern complexity
        risk_score += pattern.complexity_score * 5

        # Risk from data volume
        if data_volume == DataVolumeCategory.VERY_LARGE:
            risk_score += 20
            mitigations_required.append(
                "Implement comprehensive monitoring for large data volumes"
            )
        elif data_volume == DataVolumeCategory.LARGE:
            risk_score += 10

        # Risk from downtime availability
        if not has_downtime_window:
            if DowntimeRequirement.ZERO not in pattern.suitable_downtime_requirements:
                risk_score += 25
                mitigations_required.append(
                    "Consider alternative pattern or negotiate maintenance window"
                )

        # Risk from team experience
        experience_risk = {
            "junior": 25,
            "mid": 15,
            "senior": 5,
            "expert": 0
        }
        risk_score += experience_risk.get(team_experience_level, 15)
        if team_experience_level in ["junior", "mid"]:
            mitigations_required.append(
                "Pair with experienced database migration specialist"
            )

        # Risk from critical data
        if critical_data:
            risk_score += 15
            mitigations_required.append(
                "Implement comprehensive backup and rollback procedures"
            )
            mitigations_required.append(
                "Conduct thorough dry-run in staging environment"
            )

        # Risk from regulatory requirements
        if regulatory_requirements:
            risk_score += 10
            mitigations_required.append(
                "Document all migration steps for audit trail"
            )
            mitigations_required.append(
                "Obtain compliance team sign-off before execution"
            )

        # Determine overall risk level
        if risk_score >= 75:
            overall_risk = RiskLevel.CRITICAL
        elif risk_score >= 50:
            overall_risk = RiskLevel.HIGH
        elif risk_score >= 25:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        # Determine go/no-go recommendation
        if risk_score >= 80:
            recommendation = "NO_GO"
        elif risk_score >= 50:
            recommendation = "GO_WITH_CAUTION"
        else:
            recommendation = "GO"

        return PatternRiskAssessment(
            pattern_type=pattern_type,
            overall_risk_level=overall_risk,
            risk_score=min(100, risk_score),
            identified_risks=identified_risks,
            mitigations_required=mitigations_required,
            go_no_go_recommendation=recommendation
        )

    def get_pattern_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all patterns in the catalog.

        Returns:
            Dictionary with pattern summaries and statistics
        """
        summaries = []
        for pattern in self._patterns.values():
            summaries.append({
                "type": pattern.pattern_type.value,
                "name": pattern.name,
                "complexity": pattern.complexity_score,
                "typical_weeks": pattern.typical_duration_weeks,
                "team_size": pattern.recommended_team_size,
                "zero_downtime": DowntimeRequirement.ZERO in pattern.suitable_downtime_requirements,
                "risk_count": len(pattern.risks)
            })

        return {
            "total_patterns": len(self._patterns),
            "patterns": summaries,
            "complexity_range": {
                "min": min(p.complexity_score for p in self._patterns.values()),
                "max": max(p.complexity_score for p in self._patterns.values()),
                "avg": sum(p.complexity_score for p in self._patterns.values()) / len(self._patterns)
            },
            "zero_downtime_patterns": sum(
                1 for p in self._patterns.values()
                if DowntimeRequirement.ZERO in p.suitable_downtime_requirements
            )
        }
