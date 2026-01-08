"""
Tests for MigrationPlanningOrchestrator (Week 69)

Tests cover:
- Orchestrator initialization (with/without LLM)
- Planning start and run workflows
- FP estimation phase (IFPUG)
- Target architecture phase
- Migration strategy selection
- Report generation
- Plan approval/rejection
- Error handling
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.migration_planning_orchestrator import (
    MigrationPlanningOrchestrator,
    PhaseResult,
    TARGET_TECHNOLOGIES,
    MIGRATION_STRATEGIES,
    GSC_FACTORS,
    run_migration_planning,
)
from app.models.project_assessment import ProjectAssessment, MigrationPlan, AssessmentPhase


class TestMigrationPlanningOrchestratorInit:
    """Test orchestrator initialization"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    def test_init_without_llm(self, mock_db):
        """Test initialization without LLM"""
        orchestrator = MigrationPlanningOrchestrator(mock_db, use_llm=False)

        assert orchestrator.db == mock_db
        assert orchestrator.use_llm == False
        assert orchestrator.llm_provider is None

    def test_init_with_llm_unavailable(self, mock_db):
        """Test initialization with LLM requested but unavailable"""
        orchestrator = MigrationPlanningOrchestrator(mock_db, use_llm=True)

        # Should not crash even if LLM unavailable
        assert orchestrator.db == mock_db


class TestTargetTechnologies:
    """Test target technology configurations"""

    def test_all_technologies_have_required_fields(self):
        """Test that all target technologies have required configuration"""
        required_fields = ["name", "patterns", "default_database", "default_frontend"]

        for tech_key, tech_config in TARGET_TECHNOLOGIES.items():
            for field in required_fields:
                assert field in tech_config, f"{tech_key} missing field: {field}"

    def test_technologies_exist(self):
        """Test expected technologies are defined"""
        expected = ["python_fastapi", "dotnet8", "nodejs_nestjs", "java_spring", "go_fiber"]

        for tech in expected:
            assert tech in TARGET_TECHNOLOGIES


class TestMigrationStrategies:
    """Test migration strategy configurations"""

    def test_all_strategies_have_required_fields(self):
        """Test that all strategies have required configuration"""
        required_fields = ["name", "description", "best_for", "timeline_multiplier", "risk_level"]

        for strategy_key, strategy_config in MIGRATION_STRATEGIES.items():
            for field in required_fields:
                assert field in strategy_config, f"{strategy_key} missing field: {field}"

    def test_strategies_exist(self):
        """Test expected strategies are defined"""
        expected = ["strangler_fig", "big_bang", "parallel_run", "incremental", "phased", "blue_green"]

        for strategy in expected:
            assert strategy in MIGRATION_STRATEGIES

    def test_timeline_multipliers_valid(self):
        """Test that timeline multipliers are reasonable"""
        for strategy_key, strategy_config in MIGRATION_STRATEGIES.items():
            multiplier = strategy_config["timeline_multiplier"]
            assert 0.5 <= multiplier <= 2.0, f"{strategy_key} has invalid multiplier: {multiplier}"


class TestGSCFactors:
    """Test GSC factor configuration"""

    def test_gsc_factors_count(self):
        """Test that all 14 GSC factors are defined (IFPUG standard)"""
        assert len(GSC_FACTORS) == 14

    def test_expected_factors_exist(self):
        """Test that key GSC factors are present"""
        expected = ["data_communications", "performance", "complex_processing", "reusability"]

        for factor in expected:
            assert factor in GSC_FACTORS


class TestStartPlanning:
    """Test planning start workflow"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        async def mock_refresh(obj):
            obj.id = uuid4()
        db.refresh = mock_refresh

        return db

    @pytest.fixture
    def completed_assessment(self):
        """Create a completed assessment for testing"""
        return ProjectAssessment(
            id=uuid4(),
            project_name="TestProject",
            directory_path="/tmp/test",
            status="completed",
            primary_stack="python",
            file_count=500,
            line_count=25000,
            architecture_score=70,
            security_grade="B",
            quality_grade="B",
            overall_grade="B",
            blockers=[]  # No blockers
        )

    @pytest.mark.asyncio
    async def test_start_planning_creates_plan(self, mock_db, completed_assessment):
        """Test that start_planning creates a migration plan"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = completed_assessment
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        plan = await orchestrator.start_planning(
            assessment_id=completed_assessment.id,
            target_technology="python_fastapi"
        )

        assert plan.target_technology == "python_fastapi"
        assert plan.target_database == "postgresql"  # Default
        assert plan.target_frontend == "react"  # Default
        assert plan.status == "draft"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_planning_with_custom_options(self, mock_db, completed_assessment):
        """Test start_planning with custom database and frontend"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = completed_assessment
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        plan = await orchestrator.start_planning(
            assessment_id=completed_assessment.id,
            target_technology="python_fastapi",
            target_database="mysql",
            target_frontend="vue"
        )

        assert plan.target_database == "mysql"
        assert plan.target_frontend == "vue"

    @pytest.mark.asyncio
    async def test_start_planning_assessment_not_found(self, mock_db):
        """Test start_planning with nonexistent assessment"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_planning(
                assessment_id=uuid4(),
                target_technology="python_fastapi"
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_planning_assessment_not_completed(self, mock_db):
        """Test start_planning with incomplete assessment"""
        incomplete_assessment = ProjectAssessment(
            id=uuid4(),
            project_name="TestProject",
            status="running"  # Not completed
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = incomplete_assessment
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_planning(
                assessment_id=incomplete_assessment.id,
                target_technology="python_fastapi"
            )

        assert "must be completed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_planning_with_blockers(self, mock_db):
        """Test start_planning with assessment that has blockers"""
        blocked_assessment = ProjectAssessment(
            id=uuid4(),
            project_name="BlockedProject",
            status="completed",
            blockers=[{"type": "security", "title": "Critical vulnerabilities"}]
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = blocked_assessment
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_planning(
                assessment_id=blocked_assessment.id,
                target_technology="python_fastapi"
            )

        assert "blockers" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_planning_unknown_technology(self, mock_db, completed_assessment):
        """Test start_planning with unknown target technology"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = completed_assessment
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_planning(
                assessment_id=completed_assessment.id,
                target_technology="unknown_tech"
            )

        assert "Unknown target technology" in str(exc_info.value)


class TestFPEstimationPhase:
    """Test FP estimation phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return MigrationPlanningOrchestrator(db)

    @pytest.fixture
    def assessment(self):
        return ProjectAssessment(
            project_name="TestProject",
            directory_path="/tmp/test",
            file_count=500,
            line_count=25000,
            primary_stack="python",
            architecture_components=[
                {"name": "UserController", "type": "controller"},
                {"name": "UserService", "type": "service"},
                {"name": "UserRepository", "type": "repository"},
            ] * 10,  # 30 components
            security_critical_count=0
        )

    @pytest.fixture
    def plan(self):
        return MigrationPlan(
            target_technology="python_fastapi",
            target_database="postgresql"
        )

    @pytest.mark.asyncio
    async def test_fp_estimation_calculates_fp(self, orchestrator, plan, assessment):
        """Test that FP estimation calculates function points"""
        result = await orchestrator._run_fp_estimation_phase(plan, assessment)

        assert result.success == True
        assert result.phase_name == "estimation"
        assert "unadjusted_fp" in result.data
        assert "adjusted_fp" in result.data
        assert result.data["adjusted_fp"] > 0

    @pytest.mark.asyncio
    async def test_fp_estimation_updates_plan(self, orchestrator, plan, assessment):
        """Test that FP estimation updates the plan object"""
        await orchestrator._run_fp_estimation_phase(plan, assessment)

        assert plan.unadjusted_fp > 0
        assert plan.adjusted_fp > 0
        assert plan.vaf is not None
        assert plan.total_hours > 0
        assert plan.total_weeks > 0
        assert plan.team_size_recommended >= 2

    @pytest.mark.asyncio
    async def test_fp_estimation_gsc_factors(self, orchestrator, plan, assessment):
        """Test that GSC factors are calculated"""
        await orchestrator._run_fp_estimation_phase(plan, assessment)

        assert plan.gsc_factors is not None
        assert len(plan.gsc_factors) == 14  # All GSC factors

    @pytest.mark.asyncio
    async def test_fp_estimation_phase_breakdown(self, orchestrator, plan, assessment):
        """Test that phase breakdown is calculated"""
        await orchestrator._run_fp_estimation_phase(plan, assessment)

        assert plan.phase_breakdown is not None
        assert len(plan.phase_breakdown) == 4  # Requirements, Dev, Test, Deploy

        # Check percentages sum to 100
        total_percentage = sum(p.get("percentage", 0) for p in plan.phase_breakdown)
        assert total_percentage == 100

    @pytest.mark.asyncio
    async def test_fp_estimation_team_composition(self, orchestrator, plan, assessment):
        """Test that team composition is calculated"""
        await orchestrator._run_fp_estimation_phase(plan, assessment)

        assert plan.team_composition is not None
        assert "senior_developers" in plan.team_composition
        assert "mid_developers" in plan.team_composition
        assert "qa_engineers" in plan.team_composition
        assert "devops" in plan.team_composition

    @pytest.mark.asyncio
    async def test_fp_estimation_security_impacts_gsc(self, orchestrator, plan):
        """Test that security issues impact GSC scores"""
        assessment_with_security = ProjectAssessment(
            project_name="SecureProject",
            directory_path="/tmp/test",
            file_count=100,
            line_count=5000,
            architecture_components=[{"name": "Service", "type": "service"}] * 10,
            security_critical_count=5  # Has security issues
        )

        await orchestrator._run_fp_estimation_phase(plan, assessment_with_security)

        # GSC base score should be higher due to security issues
        avg_gsc = sum(plan.gsc_factors.values()) / len(plan.gsc_factors)
        assert avg_gsc >= 3  # Base is 3, with +1 for security


class TestArchitecturePhase:
    """Test target architecture phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return MigrationPlanningOrchestrator(db)

    @pytest.fixture
    def assessment(self):
        return ProjectAssessment(
            project_name="TestProject",
            architecture_pattern="layered",
            architecture_components=[
                {"name": "UserController", "type": "controller"},
                {"name": "UserService", "type": "service"},
                {"name": "UserRepository", "type": "repository"},
                {"name": "User", "type": "model"},
            ]
        )

    @pytest.fixture
    def plan(self):
        return MigrationPlan(
            target_technology="python_fastapi",
            target_database="postgresql",
            target_frontend="react"
        )

    @pytest.mark.asyncio
    async def test_architecture_phase_success(self, orchestrator, plan, assessment):
        """Test architecture phase completes successfully"""
        result = await orchestrator._run_architecture_phase(plan, assessment)

        assert result.success == True
        assert result.phase_name == "architecture"
        assert "pattern" in result.data
        assert "components_mapped" in result.data

    @pytest.mark.asyncio
    async def test_architecture_phase_defines_layers(self, orchestrator, plan, assessment):
        """Test architecture phase defines target layers"""
        await orchestrator._run_architecture_phase(plan, assessment)

        assert plan.architecture_layers is not None
        assert len(plan.architecture_layers) == 4  # API, Application, Domain, Infrastructure

        layer_names = [l.get("name") for l in plan.architecture_layers]
        assert "API" in layer_names
        assert "Domain" in layer_names

    @pytest.mark.asyncio
    async def test_architecture_phase_maps_components(self, orchestrator, plan, assessment):
        """Test architecture phase maps source to target components"""
        await orchestrator._run_architecture_phase(plan, assessment)

        assert plan.component_mapping is not None
        assert len(plan.component_mapping) > 0

        for mapping in plan.component_mapping:
            assert "legacy_name" in mapping
            assert "target_name" in mapping
            assert "target_layer" in mapping
            assert "effort_hours" in mapping

    @pytest.mark.asyncio
    async def test_architecture_phase_creates_adrs(self, orchestrator, plan, assessment):
        """Test architecture phase creates ADRs"""
        await orchestrator._run_architecture_phase(plan, assessment)

        assert plan.architecture_decisions is not None
        assert len(plan.architecture_decisions) >= 2

        for adr in plan.architecture_decisions:
            assert "id" in adr
            assert "title" in adr
            assert "decision" in adr

    @pytest.mark.asyncio
    async def test_architecture_phase_api_contracts(self, orchestrator, plan, assessment):
        """Test architecture phase defines API contracts"""
        await orchestrator._run_architecture_phase(plan, assessment)

        assert plan.api_contracts is not None
        assert len(plan.api_contracts) >= 5  # Basic CRUD + health

    @pytest.mark.asyncio
    async def test_architecture_phase_data_migration(self, orchestrator, plan, assessment):
        """Test architecture phase defines data migration plan"""
        await orchestrator._run_architecture_phase(plan, assessment)

        assert plan.data_migration_plan is not None
        assert len(plan.data_migration_plan) >= 5  # 5 steps


class TestComponentMapping:
    """Test component type and layer mapping"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return MigrationPlanningOrchestrator(db)

    def test_map_controller(self, orchestrator):
        """Test controller mapping"""
        result = orchestrator._map_component_type("controller", "python_fastapi")
        assert result == "Controller"

    def test_map_service(self, orchestrator):
        """Test service mapping"""
        result = orchestrator._map_component_type("service", "python_fastapi")
        assert result == "Service"

    def test_map_unknown_type(self, orchestrator):
        """Test unknown type mapping"""
        result = orchestrator._map_component_type("unknown", "python_fastapi")
        assert result == "Component"

    def test_get_layer_for_controller(self, orchestrator):
        """Test layer assignment for controller"""
        layer = orchestrator._get_layer_for_component("Controller")
        assert layer == "API"

    def test_get_layer_for_service(self, orchestrator):
        """Test layer assignment for service"""
        layer = orchestrator._get_layer_for_component("Service")
        assert layer == "Application"

    def test_get_layer_for_entity(self, orchestrator):
        """Test layer assignment for entity"""
        layer = orchestrator._get_layer_for_component("Entity")
        assert layer == "Domain"

    def test_get_layer_for_repository(self, orchestrator):
        """Test layer assignment for repository"""
        layer = orchestrator._get_layer_for_component("Repository")
        assert layer == "Infrastructure"

    def test_estimate_effort_service(self, orchestrator):
        """Test effort estimation for service"""
        hours = orchestrator._estimate_component_effort("service")
        assert hours == 16

    def test_estimate_effort_model(self, orchestrator):
        """Test effort estimation for model"""
        hours = orchestrator._estimate_component_effort("model")
        assert hours == 4


class TestStrategyPhase:
    """Test migration strategy phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return MigrationPlanningOrchestrator(db)

    @pytest.fixture
    def plan(self):
        return MigrationPlan(
            target_technology="python_fastapi",
            total_weeks=20
        )

    @pytest.mark.asyncio
    async def test_strategy_phase_success(self, orchestrator, plan):
        """Test strategy phase completes successfully"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            file_count=500,
            security_critical_count=0,
            overall_grade="B"
        )

        result = await orchestrator._run_strategy_phase(plan, assessment)

        assert result.success == True
        assert result.phase_name == "strategy"
        assert "strategy" in result.data

    @pytest.mark.asyncio
    async def test_strategy_strangler_fig_for_large_project(self, orchestrator, plan):
        """Test strangler fig is selected for large projects"""
        assessment = ProjectAssessment(
            project_name="LargeProject",
            file_count=2000,  # Large project
            security_critical_count=0,
            overall_grade="B"
        )

        await orchestrator._run_strategy_phase(plan, assessment)

        assert plan.migration_strategy == "strangler_fig"

    @pytest.mark.asyncio
    async def test_strategy_strangler_fig_for_security_issues(self, orchestrator, plan):
        """Test strangler fig is selected for security-critical projects"""
        assessment = ProjectAssessment(
            project_name="SecureProject",
            file_count=500,
            security_critical_count=10,  # Many security issues
            overall_grade="C"
        )

        await orchestrator._run_strategy_phase(plan, assessment)

        assert plan.migration_strategy == "strangler_fig"

    @pytest.mark.asyncio
    async def test_strategy_big_bang_for_small_project(self, orchestrator, plan):
        """Test big bang is selected for small projects"""
        assessment = ProjectAssessment(
            project_name="SmallProject",
            file_count=50,  # Small project
            security_critical_count=0,
            overall_grade="A"
        )

        await orchestrator._run_strategy_phase(plan, assessment)

        assert plan.migration_strategy == "big_bang"

    @pytest.mark.asyncio
    async def test_strategy_incremental_for_good_quality(self, orchestrator, plan):
        """Test incremental is selected for good quality projects"""
        assessment = ProjectAssessment(
            project_name="GoodProject",
            file_count=500,  # Medium size
            security_critical_count=0,
            overall_grade="A"  # High quality
        )

        await orchestrator._run_strategy_phase(plan, assessment)

        assert plan.migration_strategy == "incremental"

    @pytest.mark.asyncio
    async def test_strategy_defines_phases(self, orchestrator, plan):
        """Test strategy defines migration phases"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            file_count=500,
            security_critical_count=0,
            overall_grade="B"
        )

        await orchestrator._run_strategy_phase(plan, assessment)

        assert plan.migration_phases is not None
        assert len(plan.migration_phases) >= 3

        for phase in plan.migration_phases:
            assert "name" in phase
            assert "duration_weeks" in phase
            assert "deliverables" in phase

    @pytest.mark.asyncio
    async def test_strategy_defines_milestones(self, orchestrator, plan):
        """Test strategy defines milestones"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            file_count=500,
            security_critical_count=0,
            overall_grade="B"
        )

        await orchestrator._run_strategy_phase(plan, assessment)

        assert plan.milestones is not None
        assert len(plan.milestones) >= 4

    @pytest.mark.asyncio
    async def test_strategy_identifies_risks(self, orchestrator, plan):
        """Test strategy identifies risks"""
        assessment = ProjectAssessment(
            project_name="RiskyProject",
            file_count=500,
            security_critical_count=3,  # Some security issues
            tech_debt_hours=200,  # High tech debt
            overall_grade="C"
        )

        await orchestrator._run_strategy_phase(plan, assessment)

        assert plan.risks is not None
        assert len(plan.risks) >= 1

        # Should identify both security and tech debt risks
        risk_titles = [r.get("title", "") for r in plan.risks]
        assert any("security" in t.lower() for t in risk_titles)
        assert any("debt" in t.lower() for t in risk_titles)


class TestReportPhase:
    """Test report generation phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return MigrationPlanningOrchestrator(db)

    @pytest.fixture
    def plan(self):
        return MigrationPlan(
            target_technology="python_fastapi",
            target_database="postgresql",
            unadjusted_fp=200,
            adjusted_fp=180,
            vaf=Decimal("0.90"),
            total_hours=1440,
            total_days=180,
            total_weeks=36,
            migration_strategy="incremental",
            timeline_weeks=40,
            architecture_pattern="clean_architecture",
            architecture_layers=[
                {"name": "API", "responsibility": "HTTP endpoints"},
                {"name": "Domain", "responsibility": "Business logic"}
            ],
            phase_breakdown=[
                {"phase": "Development", "percentage": 40, "hours": 576}
            ],
            migration_phases=[
                {"name": "Phase 1", "duration_weeks": 10, "description": "Foundation"}
            ],
            risks=[
                {"title": "Risk 1", "probability": 3, "impact": 4, "mitigation": "Mitigate"}
            ],
            success_criteria=["All tests pass"],
            team_size_recommended=5
        )

    @pytest.fixture
    def assessment(self):
        return ProjectAssessment(
            id=uuid4(),
            project_name="TestProject",
            primary_stack="php",
            file_count=500,
            line_count=25000,
            architecture_score=70,
            security_grade="B",
            quality_grade="B",
            overall_grade="B"
        )

    @pytest.mark.asyncio
    async def test_report_phase_success(self, orchestrator, plan, assessment):
        """Test report phase completes successfully"""
        result = await orchestrator._run_report_phase(plan, assessment)

        assert result.success == True
        assert result.phase_name == "report"

    @pytest.mark.asyncio
    async def test_report_phase_generates_markdown(self, orchestrator, plan, assessment):
        """Test report phase generates markdown content"""
        await orchestrator._run_report_phase(plan, assessment)

        assert plan.report_content is not None
        assert "# Migration Plan" in plan.report_content
        assert "TestProject" in plan.report_content

    @pytest.mark.asyncio
    async def test_report_phase_includes_sections(self, orchestrator, plan, assessment):
        """Test report includes all required sections"""
        await orchestrator._run_report_phase(plan, assessment)

        content = plan.report_content
        assert "Executive Summary" in content
        assert "Source System Assessment" in content
        assert "Target Architecture" in content
        assert "Effort Estimation" in content
        assert "Migration Strategy" in content
        assert "Risks" in content
        assert "Success Criteria" in content

    @pytest.mark.asyncio
    async def test_report_phase_sets_metadata(self, orchestrator, plan, assessment):
        """Test report phase sets metadata"""
        await orchestrator._run_report_phase(plan, assessment)

        assert plan.report_type == "full_migration_plan"
        assert plan.report_metadata is not None
        assert "generated_at" in plan.report_metadata
        assert "sections" in plan.report_metadata
        assert "word_count" in plan.report_metadata


class TestPlanApproval:
    """Test plan approval and rejection"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_approve_plan(self, mock_db):
        """Test plan approval"""
        plan_id = uuid4()
        plan = MigrationPlan(
            id=plan_id,
            status="in_review"
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = plan
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        result = await orchestrator.approve_plan(
            plan_id=plan_id,
            reviewer="john.doe",
            notes="Approved after review"
        )

        assert result.status == "approved"
        assert result.reviewed_by == "john.doe"
        assert result.review_notes == "Approved after review"
        assert result.reviewed_at is not None

    @pytest.mark.asyncio
    async def test_approve_plan_not_in_review(self, mock_db):
        """Test approval fails if plan not in_review"""
        plan = MigrationPlan(
            id=uuid4(),
            status="draft"  # Not in_review
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = plan
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await orchestrator.approve_plan(
                plan_id=plan.id,
                reviewer="john.doe"
            )

        assert "must be in_review" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reject_plan(self, mock_db):
        """Test plan rejection"""
        plan_id = uuid4()
        plan = MigrationPlan(
            id=plan_id,
            status="in_review"
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = plan
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        result = await orchestrator.reject_plan(
            plan_id=plan_id,
            reviewer="jane.doe",
            notes="Need more details on risks"
        )

        assert result.status == "rejected"
        assert result.reviewed_by == "jane.doe"
        assert result.review_notes == "Need more details on risks"

    @pytest.mark.asyncio
    async def test_approve_plan_not_found(self, mock_db):
        """Test approval fails for nonexistent plan"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = MigrationPlanningOrchestrator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await orchestrator.approve_plan(
                plan_id=uuid4(),
                reviewer="john.doe"
            )

        assert "not found" in str(exc_info.value)


class TestAgentMapping:
    """Test agent mapping for phases"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return MigrationPlanningOrchestrator(db)

    def test_agent_mapping(self, orchestrator):
        """Test correct agent is assigned to each phase"""
        expected_agents = {
            "estimation": "eliza",
            "architecture": "felix",
            "strategy": "felix",
            "report": "diana"
        }

        for phase, expected_agent in expected_agents.items():
            agent = orchestrator._get_agent_for_phase(phase)
            assert agent == expected_agent, f"Phase {phase} should use agent {expected_agent}"

    def test_unknown_phase_returns_unknown(self, orchestrator):
        """Test unknown phase returns 'unknown'"""
        agent = orchestrator._get_agent_for_phase("nonexistent")
        assert agent == "unknown"


class TestPhaseResults:
    """Test PhaseResult dataclass"""

    def test_phase_result_success(self):
        """Test successful phase result"""
        result = PhaseResult(
            success=True,
            phase_name="estimation",
            data={"fp": 200},
            duration_seconds=10,
            items_processed=5,
            items_found=200
        )

        assert result.success == True
        assert result.phase_name == "estimation"
        assert result.data == {"fp": 200}
        assert result.error is None

    def test_phase_result_failure(self):
        """Test failed phase result"""
        result = PhaseResult(
            success=False,
            phase_name="architecture",
            data={},
            error="Architecture analysis failed"
        )

        assert result.success == False
        assert result.error == "Architecture analysis failed"


class TestConvenienceFunction:
    """Test convenience function"""

    @pytest.mark.asyncio
    async def test_run_migration_planning_function(self):
        """Test the run_migration_planning convenience function"""
        assessment_id = uuid4()

        # Create mock db
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # Create completed assessment
        assessment = ProjectAssessment(
            id=assessment_id,
            project_name="TestProject",
            directory_path="/tmp/test",
            status="completed",
            primary_stack="python",
            file_count=500,
            line_count=25000,
            architecture_score=70,
            architecture_components=[{"name": "Service", "type": "service"}] * 10,
            security_grade="B",
            security_critical_count=0,
            quality_grade="B",
            overall_grade="B",
            blockers=[],
            tech_debt_hours=50
        )

        plan_id = uuid4()
        plan = MigrationPlan(
            id=plan_id,
            assessment_id=assessment_id,
            target_technology="python_fastapi",
            target_database="postgresql",
            target_frontend="react",
            status="draft",
            current_phase="estimation",
            progress_percent=0,
            started_at=datetime.now(timezone.utc)
        )

        async def mock_refresh(obj):
            if isinstance(obj, MigrationPlan):
                obj.id = plan_id
        mock_db.refresh = mock_refresh

        # Setup execute to return assessment then plan
        call_count = [0]
        def get_mock_result():
            mock_result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_result.scalar_one_or_none.return_value = assessment
            else:
                mock_result.scalar_one_or_none.return_value = plan
            return mock_result

        mock_db.execute = AsyncMock(side_effect=lambda *args, **kwargs: get_mock_result())

        # Run convenience function
        result = await run_migration_planning(
            db=mock_db,
            assessment_id=assessment_id,
            target_technology="python_fastapi",
            use_llm=False
        )

        # Should complete with in_review status
        assert result.status == "in_review"
