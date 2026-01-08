"""
Migration Enhanced Service Tests - Week 130

Tests for the 7-phase migration execution workflow.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.migration_enhanced_service import MigrationEnhancedService
from app.models.migration_enhanced import (
    MigrationEnhancedRequest,
    MigrationEnhancedSession,
    MigrationPhase,
    MigrationStatus,
    PhaseStatus,
    Phase1Result,
    Phase2Result,
    Phase3Result,
    Phase4Result,
    Phase5Result,
    Phase6Result,
    Phase7Result,
    TestStrategy,
    TestStrategyDecision,
    TargetTechnology,
    TargetDatabase,
    MigrationStrategy,
    DeploymentStrategy,
    can_start_phase_5,
    can_start_phase_6,
    can_start_phase_7,
    PHASE_DEPENDENCIES,
    PHASE_AGENTS,
)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def service(mock_db):
    """Create service instance with mock DB."""
    return MigrationEnhancedService(mock_db)


@pytest.fixture
def sample_request():
    """Create sample migration request."""
    return MigrationEnhancedRequest(
        brown_paper_session_id="bp-12345",
        target_technology=TargetTechnology.DOTNET8,
        target_database=TargetDatabase.POSTGRESQL,
        migration_strategy=MigrationStrategy.STRANGLER_FIG,
        deployment_strategy=DeploymentStrategy.BLUE_GREEN,
        team_size=5,
        parallel_execution=True,
        test_strategy=TestStrategy.AUTO,
    )


class TestMigrationEnhancedModels:
    """Test model definitions."""

    def test_migration_phase_enum(self):
        """Test MigrationPhase enum values."""
        assert MigrationPhase.PREPARATION.value == "preparation"
        assert MigrationPhase.CODE_TRANSFORMATION.value == "code_transformation"
        assert MigrationPhase.DATA_MIGRATION.value == "data_migration"
        assert MigrationPhase.TESTING.value == "testing"
        assert MigrationPhase.VALIDATION.value == "validation"
        assert MigrationPhase.ACCEPTANCE.value == "acceptance"
        assert MigrationPhase.DEPLOYMENT.value == "deployment"

    def test_migration_status_enum(self):
        """Test MigrationStatus enum values."""
        assert MigrationStatus.NOT_STARTED.value == "not_started"
        assert MigrationStatus.IN_PROGRESS.value == "in_progress"
        assert MigrationStatus.COMPLETED.value == "completed"
        assert MigrationStatus.FAILED.value == "failed"

    def test_phase_status_enum(self):
        """Test PhaseStatus enum values."""
        assert PhaseStatus.PENDING.value == "pending"
        assert PhaseStatus.IN_PROGRESS.value == "in_progress"
        assert PhaseStatus.COMPLETED.value == "completed"
        assert PhaseStatus.FAILED.value == "failed"
        assert PhaseStatus.SKIPPED.value == "skipped"

    def test_target_technology_enum(self):
        """Test TargetTechnology enum values."""
        assert TargetTechnology.DOTNET8.value == "dotnet8"
        assert TargetTechnology.PYTHON_FASTAPI.value == "python_fastapi"
        assert TargetTechnology.NODEJS_NESTJS.value == "nodejs_nestjs"

    def test_migration_enhanced_request(self, sample_request):
        """Test MigrationEnhancedRequest creation."""
        assert sample_request.brown_paper_session_id == "bp-12345"
        assert sample_request.target_technology == TargetTechnology.DOTNET8
        assert sample_request.team_size == 5
        assert sample_request.parallel_execution is True

    def test_phase_dependencies(self):
        """Test phase dependency mapping."""
        assert PHASE_DEPENDENCIES[1] == []  # Preparation has no deps
        assert PHASE_DEPENDENCIES[2] == [1]  # Code Transformation needs Prep
        assert PHASE_DEPENDENCIES[3] == [1]  # Data Migration needs Prep
        assert PHASE_DEPENDENCIES[4] == [1]  # Testing needs Prep
        assert PHASE_DEPENDENCIES[5] == [2, 3, 4]  # Validation needs parallel phases
        assert PHASE_DEPENDENCIES[6] == [5]  # Acceptance needs Validation
        assert PHASE_DEPENDENCIES[7] == [6]  # Deployment needs Acceptance

    def test_phase_agents(self):
        """Test agent assignments per phase."""
        assert "Miguel" in PHASE_AGENTS[1]  # Preparation
        assert "Paul" in PHASE_AGENTS[1]
        assert "Miguel" in PHASE_AGENTS[2]  # Code Transformation
        assert "Felix" in PHASE_AGENTS[2]
        assert "Tessa" in PHASE_AGENTS[4]  # Testing
        assert "Quinn" in PHASE_AGENTS[4]


class TestGateChecks:
    """Test gate check functions."""

    def test_can_start_phase_5_success(self):
        """Test Phase 5 gate when all prerequisites met."""
        session = MigrationEnhancedSession(
            session_id="test-123",
            brown_paper_session_id="bp-123",
            phase_2_status=PhaseStatus.COMPLETED,
            phase_3_status=PhaseStatus.COMPLETED,
            phase_4_status=PhaseStatus.COMPLETED,
            phase_4_result=Phase4Result(
                tests_failing=0,
                coverage_achieved=0.85
            )
        )

        can_start, reason = can_start_phase_5(session)
        assert can_start is True
        assert "Ready" in reason

    def test_can_start_phase_5_phase2_incomplete(self):
        """Test Phase 5 gate when Phase 2 not complete."""
        session = MigrationEnhancedSession(
            session_id="test-123",
            brown_paper_session_id="bp-123",
            phase_2_status=PhaseStatus.IN_PROGRESS,
            phase_3_status=PhaseStatus.COMPLETED,
            phase_4_status=PhaseStatus.COMPLETED,
        )

        can_start, reason = can_start_phase_5(session)
        assert can_start is False
        assert "Phase 2" in reason

    def test_can_start_phase_5_tests_failing(self):
        """Test Phase 5 gate when tests are failing."""
        session = MigrationEnhancedSession(
            session_id="test-123",
            brown_paper_session_id="bp-123",
            phase_2_status=PhaseStatus.COMPLETED,
            phase_3_status=PhaseStatus.COMPLETED,
            phase_4_status=PhaseStatus.COMPLETED,
            phase_4_result=Phase4Result(
                tests_failing=5,
                coverage_achieved=0.85
            )
        )

        can_start, reason = can_start_phase_5(session)
        assert can_start is False
        assert "failing tests" in reason

    def test_can_start_phase_5_low_coverage(self):
        """Test Phase 5 gate when coverage is too low."""
        session = MigrationEnhancedSession(
            session_id="test-123",
            brown_paper_session_id="bp-123",
            phase_2_status=PhaseStatus.COMPLETED,
            phase_3_status=PhaseStatus.COMPLETED,
            phase_4_status=PhaseStatus.COMPLETED,
            phase_4_result=Phase4Result(
                tests_failing=0,
                coverage_achieved=0.65  # Below 80%
            )
        )

        can_start, reason = can_start_phase_5(session)
        assert can_start is False
        assert "coverage" in reason

    def test_can_start_phase_6_success(self):
        """Test Phase 6 gate when prerequisites met."""
        session = MigrationEnhancedSession(
            session_id="test-123",
            brown_paper_session_id="bp-123",
            phase_5_status=PhaseStatus.COMPLETED,
            phase_5_result=Phase5Result()
        )

        can_start, reason = can_start_phase_6(session)
        assert can_start is True

    def test_can_start_phase_7_success(self):
        """Test Phase 7 gate when prerequisites met."""
        session = MigrationEnhancedSession(
            session_id="test-123",
            brown_paper_session_id="bp-123",
            phase_6_status=PhaseStatus.COMPLETED,
            phase_6_result=Phase6Result(go_decision=True)
        )

        can_start, reason = can_start_phase_7(session)
        assert can_start is True

    def test_can_start_phase_7_no_go(self):
        """Test Phase 7 gate when GO decision is not True."""
        session = MigrationEnhancedSession(
            session_id="test-123",
            brown_paper_session_id="bp-123",
            phase_6_status=PhaseStatus.COMPLETED,
            phase_6_result=Phase6Result(go_decision=False)
        )

        can_start, reason = can_start_phase_7(session)
        assert can_start is False
        assert "GO decision" in reason


class TestMigrationEnhancedService:
    """Test service methods."""

    @pytest.mark.asyncio
    async def test_start_migration(self, service, sample_request):
        """Test starting a new migration."""
        response = await service.start_migration(sample_request)

        assert response.session_id is not None
        assert response.status == MigrationStatus.NOT_STARTED
        assert len(response.phases_completed) == 0
        assert response.progress_percent == 0.0

    @pytest.mark.asyncio
    async def test_start_migration_stores_session(self, service, sample_request):
        """Test that start_migration stores session in memory."""
        response = await service.start_migration(sample_request)
        session = await service.get_session(response.session_id)

        assert session is not None
        assert session.brown_paper_session_id == "bp-12345"
        assert session.target_technology == TargetTechnology.DOTNET8

    @pytest.mark.asyncio
    async def test_run_preparation_phase(self, service, sample_request):
        """Test Phase 1: Preparation."""
        # Start migration
        response = await service.start_migration(sample_request)
        session_id = response.session_id

        # Run Phase 1
        result = await service.run_preparation_phase(session_id)

        assert result.success is True
        assert result.environment_ready is True
        assert result.brown_paper_loaded is True
        assert len(result.tools_configured) > 0
        assert "lead" in result.team_assignments

    @pytest.mark.asyncio
    async def test_run_code_transformation_phase(self, service, sample_request):
        """Test Phase 2: Code Transformation."""
        # Start and complete Phase 1
        response = await service.start_migration(sample_request)
        session_id = response.session_id
        await service.run_preparation_phase(session_id)

        # Run Phase 2
        result = await service.run_code_transformation_phase(session_id)

        assert result.success is True
        assert result.components_total > 0
        assert result.components_transformed > 0
        assert len(result.patterns_mapped) > 0

    @pytest.mark.asyncio
    async def test_run_code_transformation_requires_phase1(self, service, sample_request):
        """Test Phase 2 requires Phase 1 completion."""
        # Start migration but don't run Phase 1
        response = await service.start_migration(sample_request)
        session_id = response.session_id

        # Try to run Phase 2
        result = await service.run_code_transformation_phase(session_id)

        assert result.success is False
        assert "Phase 1" in result.errors[0]

    @pytest.mark.asyncio
    async def test_run_data_migration_phase(self, service, sample_request):
        """Test Phase 3: Data Migration."""
        # Start and complete Phase 1
        response = await service.start_migration(sample_request)
        session_id = response.session_id
        await service.run_preparation_phase(session_id)

        # Run Phase 3
        result = await service.run_data_migration_phase(session_id, dry_run=False)

        assert result.success is True
        assert result.tables_total > 0
        assert result.tables_migrated > 0

    @pytest.mark.asyncio
    async def test_run_testing_phase_auto_strategy(self, service, sample_request):
        """Test Phase 4: Testing with AUTO strategy."""
        # Start and complete Phase 1
        response = await service.start_migration(sample_request)
        session_id = response.session_id
        await service.run_preparation_phase(session_id)

        # Run Phase 4
        result = await service.run_testing_phase(session_id)

        assert result.success is True
        assert result.strategy_decision is not None
        assert result.strategy_decision.strategy in [TestStrategy.MIGRATE, TestStrategy.GENERATE]
        assert result.tests_total > 0
        assert result.coverage_achieved > 0

    @pytest.mark.asyncio
    async def test_run_testing_phase_forced_generate(self, service, sample_request):
        """Test Phase 4: Testing with forced GENERATE strategy."""
        # Start and complete Phase 1
        response = await service.start_migration(sample_request)
        session_id = response.session_id
        await service.run_preparation_phase(session_id)

        # Run Phase 4 with forced strategy
        result = await service.run_testing_phase(session_id, force_strategy=TestStrategy.GENERATE)

        assert result.success is True
        assert result.strategy_decision.strategy == TestStrategy.GENERATE

    @pytest.mark.asyncio
    async def test_full_workflow(self, service, sample_request):
        """Test complete 7-phase workflow."""
        # Start migration
        response = await service.start_migration(sample_request)
        session_id = response.session_id

        # Phase 1: Preparation
        p1 = await service.run_preparation_phase(session_id)
        assert p1.success is True

        # Phases 2, 3, 4: Parallel phases
        p2 = await service.run_code_transformation_phase(session_id)
        p3 = await service.run_data_migration_phase(session_id, dry_run=False)
        p4 = await service.run_testing_phase(session_id)

        assert p2.success is True
        assert p3.success is True
        assert p4.success is True

        # Phase 5: Validation (gate)
        p5 = await service.run_validation_phase(session_id)
        assert p5.success is True
        assert p5.functional_equivalence is not None
        assert p5.data_integrity is not None
        assert p5.security_audit is not None

        # Phase 6: Acceptance
        p6 = await service.run_acceptance_phase(session_id)
        assert p6.success is True
        assert p6.go_decision is True

        # Phase 7: Deployment to staging
        p7_staging = await service.run_deployment_phase(session_id, "staging")
        assert p7_staging.success is True
        assert p7_staging.staging_deployed is True

        # Phase 7: Deployment to production
        p7_prod = await service.run_deployment_phase(session_id, "production")
        assert p7_prod.success is True
        assert p7_prod.production_deployed is True

        # Check final status
        session = await service.get_session(session_id)
        assert session.status == MigrationStatus.COMPLETED


class TestReporting:
    """Test reporting methods."""

    @pytest.mark.asyncio
    async def test_get_full_report(self, service, sample_request):
        """Test full report generation."""
        # Start and complete some phases
        response = await service.start_migration(sample_request)
        session_id = response.session_id
        await service.run_preparation_phase(session_id)

        # Get report
        report = await service.get_full_report(session_id)

        assert report["session_id"] == session_id
        assert "configuration" in report
        assert "phases" in report
        assert len(report["phases"]) == 7

    @pytest.mark.asyncio
    async def test_get_testing_report(self, service, sample_request):
        """Test testing report generation."""
        # Start and complete Phase 4
        response = await service.start_migration(sample_request)
        session_id = response.session_id
        await service.run_preparation_phase(session_id)
        await service.run_testing_phase(session_id)

        # Get testing report
        report = await service.get_testing_report(session_id)

        assert "strategy" in report
        assert "tests" in report
        assert "breakdown" in report
        assert "coverage" in report

    @pytest.mark.asyncio
    async def test_get_validation_report(self, service, sample_request):
        """Test validation report generation."""
        # Complete through Phase 5
        response = await service.start_migration(sample_request)
        session_id = response.session_id
        await service.run_preparation_phase(session_id)
        await service.run_code_transformation_phase(session_id)
        await service.run_data_migration_phase(session_id, dry_run=False)
        await service.run_testing_phase(session_id)
        await service.run_validation_phase(session_id)

        # Get validation report
        report = await service.get_validation_report(session_id)

        assert "functional_equivalence" in report
        assert "data_integrity" in report
        assert "performance_baseline" in report
        assert "security_audit" in report


class TestRollback:
    """Test rollback functionality."""

    @pytest.mark.asyncio
    async def test_rollback(self, service, sample_request):
        """Test rollback after deployment."""
        # Complete full workflow
        response = await service.start_migration(sample_request)
        session_id = response.session_id

        await service.run_preparation_phase(session_id)
        await service.run_code_transformation_phase(session_id)
        await service.run_data_migration_phase(session_id, dry_run=False)
        await service.run_testing_phase(session_id)
        await service.run_validation_phase(session_id)
        await service.run_acceptance_phase(session_id)
        await service.run_deployment_phase(session_id, "staging")

        # Rollback
        result = await service.rollback(session_id)

        assert result.legacy_standby is True
        assert result.production_deployed is False

        # Check session status
        session = await service.get_session(session_id)
        assert session.status == MigrationStatus.FAILED
