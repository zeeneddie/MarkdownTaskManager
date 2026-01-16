"""
Tests for Confucius Workflow Orchestrators.

Tests cover:
- WorkflowOrchestrator base functionality
- BrownPaperOrchestrator stages
- MigrationOrchestrator stages
- GreenPaperOrchestrator stages
- QualityOrchestrator stages
- Quality gate integration
- SSE streaming
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.confucius.workflows import (
    WorkflowOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    BrownPaperOrchestrator,
    MigrationOrchestrator,
    GreenPaperOrchestrator,
    QualityOrchestrator,
)
from app.confucius.workflows.base import StageResult


# =============================================================================
# BASE WORKFLOW TESTS
# =============================================================================


class TestWorkflowStage:
    """Tests for WorkflowStage dataclass."""

    def test_stage_creation(self):
        """Test creating a workflow stage."""
        stage = WorkflowStage(
            name="test_stage",
            description="Test stage description",
            agents=["Felix", "Quinn"],
            required=True,
            parallel_agents=True,
        )

        assert stage.name == "test_stage"
        assert stage.agents == ["Felix", "Quinn"]
        assert stage.required is True
        assert stage.parallel_agents is True
        assert stage.quality_threshold == 0.85  # Default

    def test_stage_to_dict(self):
        """Test stage serialization."""
        stage = WorkflowStage(
            name="analyze",
            description="Analyze code",
            agents=["Miguel"],
            depends_on=["scan"],
        )

        result = stage.to_dict()

        assert result["name"] == "analyze"
        assert result["agents"] == ["Miguel"]
        assert result["depends_on"] == ["scan"]


class TestWorkflowContext:
    """Tests for WorkflowContext."""

    def test_context_creation(self):
        """Test creating workflow context."""
        ctx = WorkflowContext(
            workflow_id="wf-123",
            workflow_type="brown_paper",
            session_id="sess-456",
        )

        assert ctx.workflow_id == "wf-123"
        assert ctx.current_stage is None
        assert len(ctx.completed_stages) == 0

    def test_add_stage_result(self):
        """Test adding stage results."""
        ctx = WorkflowContext(
            workflow_id="wf-123",
            workflow_type="test",
            session_id="sess-456",
        )

        result = StageResult(
            stage_name="analyze",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            quality_score=0.90,
        )

        ctx.add_stage_result(result)

        assert "analyze" in ctx.stage_results
        assert "analyze" in ctx.completed_stages

    def test_get_stage_output(self):
        """Test getting stage output."""
        ctx = WorkflowContext(
            workflow_id="wf-123",
            workflow_type="test",
            session_id="sess-456",
        )

        result = StageResult(
            stage_name="scan",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            agent_results={"files_scanned": 100},
        )
        ctx.add_stage_result(result)

        output = ctx.get_stage_output("scan")
        assert output == {"files_scanned": 100}

        # Non-existent stage
        assert ctx.get_stage_output("missing") is None


class TestWorkflowResult:
    """Tests for WorkflowResult."""

    def test_result_success(self):
        """Test successful workflow result."""
        result = WorkflowResult(
            workflow_id="wf-123",
            workflow_type="brown_paper",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            stages_completed=6,
            stages_total=6,
        )

        assert result.success is True
        assert result.duration_seconds is not None

    def test_result_failure(self):
        """Test failed workflow result."""
        result = WorkflowResult(
            workflow_id="wf-456",
            workflow_type="migration",
            status=WorkflowStatus.FAILED,
            started_at=datetime.now(timezone.utc),
            error="Stage 3 failed",
        )

        assert result.success is False

    def test_result_to_dict(self):
        """Test result serialization."""
        result = WorkflowResult(
            workflow_id="wf-789",
            workflow_type="quality",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            stages_completed=5,
            stages_total=5,
            overall_quality_score=0.92,
        )

        data = result.to_dict()

        assert data["workflow_id"] == "wf-789"
        assert data["success"] is True
        assert data["overall_quality_score"] == 0.92


# =============================================================================
# BROWN PAPER ORCHESTRATOR TESTS
# =============================================================================


class TestBrownPaperOrchestrator:
    """Tests for Brown Paper workflow orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create Brown Paper orchestrator."""
        return BrownPaperOrchestrator()

    def test_workflow_type(self, orchestrator):
        """Test workflow type."""
        assert orchestrator.workflow_type == "brown_paper"

    def test_get_stages(self, orchestrator):
        """Test getting workflow stages."""
        stages = orchestrator.get_stages()

        assert len(stages) == 6
        stage_names = [s.name for s in stages]
        assert "code_understanding" in stage_names
        assert "domain_extraction" in stage_names
        assert "story_extraction" in stage_names
        assert "deep_extraction" in stage_names
        assert "estimation" in stage_names
        assert "output_consolidation" in stage_names

    def test_stage_dependencies(self, orchestrator):
        """Test stage dependencies."""
        stages = orchestrator.get_stages()
        stage_map = {s.name: s for s in stages}

        # Domain extraction depends on code understanding
        assert "code_understanding" in stage_map["domain_extraction"].depends_on

        # Estimation depends on story extraction
        assert "story_extraction" in stage_map["estimation"].depends_on

    def test_stage_agents(self, orchestrator):
        """Test stage agent assignments."""
        stages = orchestrator.get_stages()
        stage_map = {s.name: s for s in stages}

        assert "Miguel" in stage_map["code_understanding"].agents
        assert "Peter" in stage_map["domain_extraction"].agents
        assert "Eliza" in stage_map["estimation"].agents
        assert "Diana" in stage_map["output_consolidation"].agents

    @pytest.mark.asyncio
    async def test_run_workflow(self, orchestrator):
        """Test running workflow (mocked)."""
        # Mock agent extensions
        with patch.object(orchestrator, "get_agents_for_stage") as mock_agents:
            mock_ext = MagicMock()
            mock_ext.name = "Miguel"
            mock_ext.run_full_lifecycle = AsyncMock(
                return_value=MagicMock(
                    success=True,
                    output={"metrics": {"files_scanned": 100}},
                )
            )
            mock_agents.return_value = [mock_ext]

            result = await orchestrator.run(
                session_id="test-bp",
                input_data={
                    "application_id": "legacy-app",
                    "scan_path": "/tmp/code",
                    "tech_stack": ["python"],
                },
            )

            assert result.workflow_type == "brown_paper"
            assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]


# =============================================================================
# MIGRATION ORCHESTRATOR TESTS
# =============================================================================


class TestMigrationOrchestrator:
    """Tests for Migration workflow orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create Migration orchestrator."""
        return MigrationOrchestrator()

    def test_workflow_type(self, orchestrator):
        """Test workflow type."""
        assert orchestrator.workflow_type == "migration"

    def test_get_stages(self, orchestrator):
        """Test getting workflow stages."""
        stages = orchestrator.get_stages()

        assert len(stages) == 7  # Fase 37: Added security_analysis stage
        stage_names = [s.name for s in stages]
        assert "validate_answers" in stage_names
        assert "technical_analysis" in stage_names
        assert "security_analysis" in stage_names  # Fase 37
        assert "generate_specification" in stage_names
        assert "generate_tasks" in stage_names
        assert "estimate_effort" in stage_names
        assert "quality_review" in stage_names

    def test_get_questions(self, orchestrator):
        """Test getting migration questions."""
        questions = orchestrator.get_questions()

        assert len(questions) == 8
        question_ids = [q["id"] for q in questions]
        assert "q1_legacy_system" in question_ids
        assert "q8_timeline" in question_ids

    def test_stage_agents(self, orchestrator):
        """Test stage agent assignments."""
        stages = orchestrator.get_stages()
        stage_map = {s.name: s for s in stages}

        assert "Miguel" in stage_map["technical_analysis"].agents
        assert "Peter" in stage_map["generate_specification"].agents
        assert "Felix" in stage_map["generate_tasks"].agents
        assert "Quinn" in stage_map["quality_review"].agents

    @pytest.mark.asyncio
    async def test_validate_answers_missing(self, orchestrator):
        """Test validation with missing answers."""
        ctx = WorkflowContext(
            workflow_id="test",
            workflow_type="migration",
            session_id="test-mig",
            shared_data={"answers": {"q1_legacy_system": "Legacy ASP"}},
        )

        stage = WorkflowStage("validate_answers", "", [])

        result = await orchestrator.execute_stage(stage, ctx)

        assert result.status == WorkflowStatus.FAILED
        assert "Missing answers" in result.error


# =============================================================================
# GREEN PAPER ORCHESTRATOR TESTS
# =============================================================================


class TestGreenPaperOrchestrator:
    """Tests for Green Paper workflow orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create Green Paper orchestrator."""
        return GreenPaperOrchestrator()

    def test_workflow_type(self, orchestrator):
        """Test workflow type."""
        assert orchestrator.workflow_type == "green_paper"

    def test_get_stages(self, orchestrator):
        """Test getting workflow stages."""
        stages = orchestrator.get_stages()

        assert len(stages) == 7  # Fase 37: Added security_requirements stage
        stage_names = [s.name for s in stages]
        assert "validate_vision" in stage_names
        assert "requirements_constitution" in stage_names
        assert "ux_design" in stage_names
        assert "architecture_design" in stage_names
        assert "security_requirements" in stage_names  # Fase 37
        assert "implementation_planning" in stage_names
        assert "quality_review" in stage_names

    def test_get_questions(self, orchestrator):
        """Test getting green paper questions."""
        questions = orchestrator.get_questions()

        assert len(questions) == 6
        question_ids = [q["id"] for q in questions]
        assert "vision" in question_ids
        assert "users" in question_ids
        assert "features" in question_ids

    def test_stage_agents(self, orchestrator):
        """Test stage agent assignments."""
        stages = orchestrator.get_stages()
        stage_map = {s.name: s for s in stages}

        assert "Peter" in stage_map["requirements_constitution"].agents
        assert "Vicky" in stage_map["ux_design"].agents
        assert "Felix" in stage_map["architecture_design"].agents
        assert "Paul" in stage_map["implementation_planning"].agents

    @pytest.mark.asyncio
    async def test_validate_vision_missing_name(self, orchestrator):
        """Test validation with missing project name."""
        ctx = WorkflowContext(
            workflow_id="test",
            workflow_type="green_paper",
            session_id="test-gp",
            shared_data={
                "answers": {"vision": "A great app"},
                "project_name": "",  # Missing
            },
        )

        stage = WorkflowStage("validate_vision", "", [])

        result = await orchestrator.execute_stage(stage, ctx)

        assert result.status == WorkflowStatus.FAILED
        assert "Project name is required" in result.error


# =============================================================================
# QUALITY ORCHESTRATOR TESTS
# =============================================================================


class TestQualityOrchestrator:
    """Tests for Quality workflow orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create Quality orchestrator."""
        return QualityOrchestrator()

    def test_workflow_type(self, orchestrator):
        """Test workflow type."""
        assert orchestrator.workflow_type == "quality"

    def test_get_stages(self, orchestrator):
        """Test getting workflow stages."""
        stages = orchestrator.get_stages()

        assert len(stages) == 5
        stage_names = [s.name for s in stages]
        assert "scan_execution" in stage_names
        assert "metrics_analysis" in stage_names
        assert "quality_review" in stage_names
        assert "remediation_planning" in stage_names
        assert "test_validation" in stage_names

    def test_optional_stages(self, orchestrator):
        """Test optional stage flags."""
        stages = orchestrator.get_stages()
        stage_map = {s.name: s for s in stages}

        # Remediation and validation are optional
        assert stage_map["remediation_planning"].required is False
        assert stage_map["test_validation"].required is False

        # Scan and review are required
        assert stage_map["scan_execution"].required is True
        assert stage_map["quality_review"].required is True

    def test_stage_agents(self, orchestrator):
        """Test stage agent assignments."""
        stages = orchestrator.get_stages()
        stage_map = {s.name: s for s in stages}

        assert "Miguel" in stage_map["scan_execution"].agents
        assert "Quinn" in stage_map["quality_review"].agents
        assert "Marcus" in stage_map["remediation_planning"].agents
        assert "Tessa" in stage_map["test_validation"].agents

    @pytest.mark.asyncio
    async def test_run_quality_workflow(self, orchestrator):
        """Test running quality workflow (mocked)."""
        with patch.object(orchestrator, "get_agents_for_stage") as mock_agents:
            mock_ext = MagicMock()
            mock_ext.name = "Miguel"
            mock_ext.run_full_lifecycle = AsyncMock(
                return_value=MagicMock(
                    success=True,
                    output={"results": {}, "files_scanned": 50},
                )
            )
            mock_agents.return_value = [mock_ext]

            result = await orchestrator.run(
                session_id="test-qa",
                input_data={
                    "project_path": "/tmp/project",
                    "tech_stack": ["python"],
                    "scanners": ["complexity"],
                },
            )

            assert result.workflow_type == "quality"


# =============================================================================
# WORKFLOW INTEGRATION TESTS
# =============================================================================


class TestWorkflowIntegration:
    """Integration tests for workflow orchestration."""

    @pytest.mark.asyncio
    async def test_stage_dependency_checking(self):
        """Test that stage dependencies are checked."""
        orchestrator = BrownPaperOrchestrator()
        stages = orchestrator.get_stages()

        ctx = WorkflowContext(
            workflow_id="test",
            workflow_type="brown_paper",
            session_id="test-deps",
        )

        # Domain extraction depends on code_understanding
        domain_stage = next(s for s in stages if s.name == "domain_extraction")

        # Dependencies not met
        result = orchestrator._check_dependencies(domain_stage, ctx)
        assert result is False

        # Mark dependency as complete
        ctx.completed_stages.append("code_understanding")
        result = orchestrator._check_dependencies(domain_stage, ctx)
        assert result is True

    def test_domain_detection(self):
        """Test domain detection for quality gates."""
        orchestrator = BrownPaperOrchestrator()

        # Miguel -> metrics
        stage = WorkflowStage("test", "", ["Miguel"])
        assert orchestrator._get_domain_for_stage(stage) == "metrics"

        # Felix -> architecture
        stage = WorkflowStage("test", "", ["Felix"])
        assert orchestrator._get_domain_for_stage(stage) == "architecture"

        # Empty -> general
        stage = WorkflowStage("test", "", [])
        assert orchestrator._get_domain_for_stage(stage) == "general"

    def test_all_orchestrators_have_stages(self):
        """Test all orchestrators define stages."""
        orchestrators = [
            BrownPaperOrchestrator(),
            MigrationOrchestrator(),
            GreenPaperOrchestrator(),
            QualityOrchestrator(),
        ]

        for orch in orchestrators:
            stages = orch.get_stages()
            assert len(stages) > 0, f"{orch.workflow_type} has no stages"
            for stage in stages:
                assert stage.name, "Stage must have name"
                assert stage.description, "Stage must have description"

    def test_all_workflow_types_unique(self):
        """Test all workflow types are unique."""
        orchestrators = [
            BrownPaperOrchestrator(),
            MigrationOrchestrator(),
            GreenPaperOrchestrator(),
            QualityOrchestrator(),
        ]

        types = [o.workflow_type for o in orchestrators]
        assert len(types) == len(set(types)), "Workflow types must be unique"
