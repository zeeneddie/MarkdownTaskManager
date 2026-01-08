"""
Migration Enhanced Models - Fase 21 (Week 129-130)

7-Phase migration execution workflow that takes Brown Paper Enhanced output as input.
INTEGRATION: Uses Brown Paper session data, orchestrates actual migration execution.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class MigrationPhase(str, Enum):
    """The 7 phases of migration execution."""
    PREPARATION = "preparation"           # Phase 1
    CODE_TRANSFORMATION = "code_transformation"  # Phase 2
    DATA_MIGRATION = "data_migration"     # Phase 3
    TESTING = "testing"                   # Phase 4
    VALIDATION = "validation"             # Phase 5
    ACCEPTANCE = "acceptance"             # Phase 6
    DEPLOYMENT = "deployment"             # Phase 7


class MigrationStatus(str, Enum):
    """Overall migration status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PhaseStatus(str, Enum):
    """Individual phase status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TargetTechnology(str, Enum):
    """Target technology stack options."""
    DOTNET8 = "dotnet8"
    PYTHON_FASTAPI = "python_fastapi"
    NODEJS_NESTJS = "nodejs_nestjs"
    JAVA_SPRING = "java_spring"
    GO_FIBER = "go_fiber"


class TargetDatabase(str, Enum):
    """Target database options."""
    POSTGRESQL = "postgresql"
    SQLSERVER = "sqlserver"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class MigrationStrategy(str, Enum):
    """Migration strategy options."""
    STRANGLER_FIG = "strangler_fig"  # Gradual replacement
    BIG_BANG = "big_bang"            # Complete cutover
    PHASED = "phased"                # Module by module
    PARALLEL_RUN = "parallel_run"    # Both systems live
    BLUE_GREEN = "blue_green"        # Two environments
    INCREMENTAL = "incremental"      # Feature by feature


class TestStrategy(str, Enum):
    """Test strategy for Phase 4."""
    AUTO = "auto"          # Decide based on legacy test quality
    MIGRATE = "migrate"    # Migrate existing tests
    GENERATE = "generate"  # Generate new tests from specs


class DeploymentStrategy(str, Enum):
    """Deployment strategy for Phase 7."""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    BIG_BANG = "big_bang"


# ============================================================================
# Request Models
# ============================================================================

@dataclass
class MigrationEnhancedRequest:
    """Request to start a migration execution."""
    brown_paper_session_id: str  # Required - link to analysis
    target_technology: TargetTechnology = TargetTechnology.DOTNET8
    target_database: TargetDatabase = TargetDatabase.POSTGRESQL
    migration_strategy: MigrationStrategy = MigrationStrategy.STRANGLER_FIG
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN
    team_size: int = 3

    # Optional configuration
    skip_phases: List[int] = field(default_factory=list)
    parallel_execution: bool = True
    test_strategy: TestStrategy = TestStrategy.AUTO
    test_coverage_target: float = 0.80
    performance_tolerance: float = 1.10  # 110% of legacy


# ============================================================================
# Phase Result Models
# ============================================================================

@dataclass
class Phase1Result:
    """Phase 1: Preparation results."""
    environment_ready: bool = False
    tools_configured: List[str] = field(default_factory=list)
    brown_paper_loaded: bool = False
    workspace_url: Optional[str] = None
    team_assignments: Dict[str, str] = field(default_factory=dict)
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class Phase2Result:
    """Phase 2: Code Transformation results."""
    components_total: int = 0
    components_transformed: int = 0
    patterns_mapped: Dict[str, str] = field(default_factory=dict)
    manual_fixes_required: int = 0
    manual_fixes_completed: int = 0
    code_review_passed: bool = False
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class Phase3Result:
    """Phase 3: Data Migration results."""
    tables_total: int = 0
    tables_migrated: int = 0
    records_total: int = 0
    records_migrated: int = 0
    stored_procedures_total: int = 0
    stored_procedures_migrated: int = 0
    data_validation_passed: bool = False
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class TestStrategyDecision:
    """Decision about test strategy for Phase 4."""
    strategy: TestStrategy
    legacy_test_count: int = 0
    legacy_test_coverage: float = 0.0
    legacy_test_quality_score: int = 0  # 0-100
    reason: str = ""


@dataclass
class Phase4Result:
    """Phase 4: Testing results."""
    strategy_decision: Optional[TestStrategyDecision] = None
    tests_total: int = 0
    tests_passing: int = 0
    tests_failing: int = 0
    coverage_achieved: float = 0.0
    ci_cd_pipeline_active: bool = False

    # Test breakdown
    unit_tests: int = 0
    integration_tests: int = 0
    e2e_tests: int = 0
    security_tests: int = 0
    performance_tests: int = 0

    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class FunctionalEquivalenceResult:
    """Functional equivalence check result."""
    method: str  # golden_master, parallel_run, sampling
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    equivalence_rate: float = 0.0
    documented_deviations: List[str] = field(default_factory=list)


@dataclass
class DataIntegrityResult:
    """Data integrity check result."""
    tables_checked: int = 0
    record_count_matches: bool = False
    checksum_matches: bool = False
    foreign_keys_valid: bool = False
    null_patterns_valid: bool = False
    issues: List[str] = field(default_factory=list)


@dataclass
class PerformanceBaselineResult:
    """Performance baseline comparison result."""
    response_time_p50_ratio: float = 0.0  # new/legacy
    response_time_p95_ratio: float = 0.0
    response_time_p99_ratio: float = 0.0
    throughput_ratio: float = 0.0
    memory_ratio: float = 0.0
    within_tolerance: bool = False


@dataclass
class SecurityAuditResult:
    """Security audit result."""
    owasp_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    passed: bool = False


@dataclass
class Phase5Result:
    """Phase 5: Validation results."""
    functional_equivalence: Optional[FunctionalEquivalenceResult] = None
    data_integrity: Optional[DataIntegrityResult] = None
    performance_baseline: Optional[PerformanceBaselineResult] = None
    security_audit: Optional[SecurityAuditResult] = None
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class AcceptanceChecklistItem:
    """Single item in acceptance checklist."""
    id: str
    description: str
    category: str  # business_rule, user_story, stakeholder
    status: str = "pending"  # pending, accepted, rejected
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: str = ""


@dataclass
class Phase6Result:
    """Phase 6: Acceptance results."""
    checklist_items: List[AcceptanceChecklistItem] = field(default_factory=list)
    business_rules_verified: int = 0
    business_rules_total: int = 0
    stories_accepted: int = 0
    stories_total: int = 0
    stakeholder_signoffs: Dict[str, datetime] = field(default_factory=dict)
    go_decision: Optional[bool] = None  # True=GO, False=NO-GO, None=Pending
    go_decision_notes: str = ""
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class Phase7Result:
    """Phase 7: Deployment results."""
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN
    staging_deployed: bool = False
    staging_smoke_tests_passed: bool = False
    production_deployed: bool = False
    production_smoke_tests_passed: bool = False
    error_rate: float = 0.0
    rollback_ready: bool = False
    legacy_standby: bool = False
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


# ============================================================================
# Session Model
# ============================================================================

@dataclass
class MigrationEnhancedSession:
    """Complete migration session state."""
    session_id: str
    brown_paper_session_id: str
    status: MigrationStatus = MigrationStatus.NOT_STARTED

    # Configuration
    target_technology: TargetTechnology = TargetTechnology.DOTNET8
    target_database: TargetDatabase = TargetDatabase.POSTGRESQL
    migration_strategy: MigrationStrategy = MigrationStrategy.STRANGLER_FIG
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN
    team_size: int = 3
    parallel_execution: bool = True
    test_strategy: TestStrategy = TestStrategy.AUTO

    # Phase statuses
    phase_1_status: PhaseStatus = PhaseStatus.PENDING
    phase_2_status: PhaseStatus = PhaseStatus.PENDING
    phase_3_status: PhaseStatus = PhaseStatus.PENDING
    phase_4_status: PhaseStatus = PhaseStatus.PENDING
    phase_5_status: PhaseStatus = PhaseStatus.PENDING
    phase_6_status: PhaseStatus = PhaseStatus.PENDING
    phase_7_status: PhaseStatus = PhaseStatus.PENDING

    # Phase results
    phase_1_result: Optional[Phase1Result] = None
    phase_2_result: Optional[Phase2Result] = None
    phase_3_result: Optional[Phase3Result] = None
    phase_4_result: Optional[Phase4Result] = None
    phase_5_result: Optional[Phase5Result] = None
    phase_6_result: Optional[Phase6Result] = None
    phase_7_result: Optional[Phase7Result] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_ms: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)


@dataclass
class MigrationEnhancedResponse:
    """Response for migration operations."""
    session_id: str
    status: MigrationStatus
    current_phase: Optional[MigrationPhase] = None
    phases_completed: List[int] = field(default_factory=list)
    progress_percent: float = 0.0

    # Summary metrics
    components_migrated: int = 0
    tables_migrated: int = 0
    tests_passing: int = 0
    test_coverage: float = 0.0

    # Links
    workspace_url: Optional[str] = None
    report_url: Optional[str] = None

    # Timing
    total_duration_ms: int = 0
    estimated_remaining_ms: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)


# ============================================================================
# Gate Checks
# ============================================================================

def can_start_phase_5(session: MigrationEnhancedSession) -> tuple[bool, str]:
    """
    Check if Phase 5 (Validation) can start.
    Requires Phase 2, 3, and 4 to be completed with passing tests.
    """
    if session.phase_2_status != PhaseStatus.COMPLETED:
        return False, "Phase 2 (Code Transformation) not completed"

    if session.phase_3_status != PhaseStatus.COMPLETED:
        return False, "Phase 3 (Data Migration) not completed"

    if session.phase_4_status != PhaseStatus.COMPLETED:
        return False, "Phase 4 (Testing) not completed"

    if session.phase_4_result:
        if session.phase_4_result.tests_failing > 0:
            return False, f"Phase 4 has {session.phase_4_result.tests_failing} failing tests"
        if session.phase_4_result.coverage_achieved < 0.80:
            return False, f"Phase 4 coverage {session.phase_4_result.coverage_achieved:.0%} < 80%"

    return True, "Ready for Phase 5"


def can_start_phase_6(session: MigrationEnhancedSession) -> tuple[bool, str]:
    """Check if Phase 6 (Acceptance) can start."""
    if session.phase_5_status != PhaseStatus.COMPLETED:
        return False, "Phase 5 (Validation) not completed"

    if session.phase_5_result:
        if session.phase_5_result.security_audit and session.phase_5_result.security_audit.critical_issues > 0:
            return False, f"Phase 5 has {session.phase_5_result.security_audit.critical_issues} critical security issues"

    return True, "Ready for Phase 6"


def can_start_phase_7(session: MigrationEnhancedSession) -> tuple[bool, str]:
    """Check if Phase 7 (Deployment) can start."""
    if session.phase_6_status != PhaseStatus.COMPLETED:
        return False, "Phase 6 (Acceptance) not completed"

    if session.phase_6_result:
        if session.phase_6_result.go_decision is not True:
            return False, "Phase 6 did not result in GO decision"

    return True, "Ready for Phase 7"


# ============================================================================
# Constants
# ============================================================================

# Phase dependencies for parallel execution
PHASE_DEPENDENCIES = {
    1: [],           # Preparation - no dependencies
    2: [1],          # Code Transformation - needs Preparation
    3: [1],          # Data Migration - needs Preparation (parallel with 2)
    4: [1],          # Testing - needs Preparation (parallel with 2, 3)
    5: [2, 3, 4],    # Validation - needs all parallel phases done
    6: [5],          # Acceptance - needs Validation
    7: [6],          # Deployment - needs Acceptance
}

# Agent assignments per phase
PHASE_AGENTS = {
    1: ["Miguel", "Paul"],
    2: ["Miguel", "Felix"],
    3: ["Miguel"],
    4: ["Tessa", "Quinn"],
    5: ["Quinn", "Tessa"],
    6: ["Peter", "Diana"],
    7: ["Paul", "Miguel"],
}

# Pattern mappings per target technology
PATTERN_MAPPINGS = {
    TargetTechnology.DOTNET8: {
        "vb6_form": "blazor_component",
        "asp_classic": "razor_page",
        "ado_recordset": "ef_core_dbset",
        "vbscript_class": "csharp_class",
        "stored_procedure": "ef_core_raw_sql",
    },
    TargetTechnology.PYTHON_FASTAPI: {
        "vb6_form": "react_component",
        "asp_classic": "jinja2_template",
        "ado_recordset": "sqlalchemy_model",
        "vbscript_class": "python_class",
        "stored_procedure": "sqlalchemy_text",
    },
    TargetTechnology.NODEJS_NESTJS: {
        "vb6_form": "angular_component",
        "asp_classic": "ejs_template",
        "ado_recordset": "typeorm_entity",
        "vbscript_class": "typescript_class",
        "stored_procedure": "raw_query",
    },
}

# Test framework mappings
TEST_FRAMEWORK_MAPPINGS = {
    TargetTechnology.DOTNET8: {
        "nunit": "xunit",
        "mstest": "xunit",
        "moq": "nsubstitute",
    },
    TargetTechnology.PYTHON_FASTAPI: {
        "junit": "pytest",
        "nunit": "pytest",
        "mockito": "pytest_mock",
    },
    TargetTechnology.NODEJS_NESTJS: {
        "mocha": "jest",
        "jasmine": "jest",
        "sinon": "jest_mock",
    },
}
