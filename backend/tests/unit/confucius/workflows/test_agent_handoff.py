"""
Unit Tests for Agent-to-Agent Handoff.

Tests data transfer and context sharing between agents during workflow execution.
Validates that outputs from one stage are correctly passed as inputs to the next.

Coverage:
- Context data propagation
- Stage result storage and retrieval
- Cross-stage data dependencies
- Agent output format validation
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.confucius.workflows import (
    BrownPaperOrchestrator,
    MigrationOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowStatus,
)
from app.confucius.workflows.base import StageResult


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def brown_paper_orchestrator():
    """Create Brown Paper orchestrator."""
    return BrownPaperOrchestrator()


@pytest.fixture
def migration_orchestrator():
    """Create Migration orchestrator."""
    return MigrationOrchestrator()


@pytest.fixture
def workflow_context():
    """Create a workflow context for testing."""
    return WorkflowContext(
        workflow_id="test-handoff-001",
        workflow_type="brown_paper",
        session_id="test-session",
        shared_data={
            "scan_path": "/tmp/test",
            "tech_stack": ["python"],
        },
    )


def create_mock_agent(name: str, output: Dict[str, Any]):
    """Create a mock agent extension with specific output."""
    mock = MagicMock()
    mock.name = name
    mock.run_full_lifecycle = AsyncMock(
        return_value=MagicMock(success=True, output=output)
    )
    return mock


# =============================================================================
# CONTEXT DATA PROPAGATION TESTS
# =============================================================================


class TestContextDataPropagation:
    """Tests for data propagation through workflow context."""

    def test_stage_result_stored_in_context(self, workflow_context):
        """Test that stage results are stored in shared_data."""
        result_data = {"files_scanned": 100, "complexity": 0.75}
        workflow_context.shared_data["code_understanding_result"] = result_data

        assert "code_understanding_result" in workflow_context.shared_data
        assert workflow_context.shared_data["code_understanding_result"]["files_scanned"] == 100

    def test_multiple_stage_results_coexist(self, workflow_context):
        """Test that multiple stage results can coexist."""
        workflow_context.shared_data["stage_1_result"] = {"data": "a"}
        workflow_context.shared_data["stage_2_result"] = {"data": "b"}
        workflow_context.shared_data["stage_3_result"] = {"data": "c"}

        assert len([k for k in workflow_context.shared_data if k.endswith("_result")]) == 3

    def test_context_preserves_input_data(self, workflow_context):
        """Test that input data is preserved through stages."""
        original_path = workflow_context.shared_data["scan_path"]

        # Simulate adding stage results
        workflow_context.shared_data["stage_result"] = {"new_data": "value"}

        # Original data should still be present
        assert workflow_context.shared_data["scan_path"] == original_path

    def test_get_stage_output_returns_correct_data(self, workflow_context):
        """Test StageResult retrieval from context."""
        stage_result = StageResult(
            stage_name="test_stage",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            agent_results={"metric_a": 100},
        )
        workflow_context.add_stage_result(stage_result)

        output = workflow_context.get_stage_output("test_stage")
        assert output == {"metric_a": 100}


# =============================================================================
# BROWN PAPER HANDOFF CHAIN TESTS
# =============================================================================


class TestBrownPaperHandoffChain:
    """Tests for Brown Paper workflow stage handoffs."""

    @pytest.mark.asyncio
    async def test_code_understanding_to_domain_extraction(
        self, brown_paper_orchestrator, workflow_context
    ):
        """Test handoff from code_understanding to domain_extraction."""
        # Stage 1: Code understanding produces output
        code_output = {
            "files_scanned": 150,
            "dependency_graph": {"nodes": 50, "edges": 100},
            "layer_analysis": {"presentation": 20, "business": 50, "data": 30},
        }

        mock_miguel = create_mock_agent("Miguel", {"metrics": code_output})

        with patch.object(
            brown_paper_orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage1 = WorkflowStage("code_understanding", "", ["Miguel"])
            await brown_paper_orchestrator.execute_stage(stage1, workflow_context)

        # Verify data is stored
        assert "code_understanding_result" in workflow_context.shared_data

        # Stage 2: Domain extraction should have access to code understanding data
        workflow_context.completed_stages.append("code_understanding")

        mock_peter = create_mock_agent("Peter", {"domains": [{"name": "Core"}]})

        with patch.object(
            brown_paper_orchestrator, "get_agents_for_stage", return_value=[mock_peter]
        ):
            stage2 = WorkflowStage(
                "domain_extraction", "", ["Peter"], depends_on=["code_understanding"]
            )
            result = await brown_paper_orchestrator.execute_stage(stage2, workflow_context)

        assert result.status == WorkflowStatus.COMPLETED
        # Both results should be in context
        assert "code_understanding_result" in workflow_context.shared_data
        assert "domain_extraction_result" in workflow_context.shared_data

    @pytest.mark.asyncio
    async def test_story_extraction_receives_domain_data(
        self, brown_paper_orchestrator, workflow_context
    ):
        """Test that story extraction receives domain extraction data."""
        # Setup: Add prior stage results
        workflow_context.shared_data["code_understanding_result"] = {
            "files_scanned": 100
        }
        workflow_context.shared_data["domain_extraction_result"] = {
            "domains": [
                {"name": "UserManagement", "modules": 15},
                {"name": "OrderProcessing", "modules": 25},
            ],
            "business_capabilities": ["Authentication", "Ordering"],
        }
        workflow_context.shared_data["user_journey_extraction_result"] = {
            "user_journeys": [{"name": "Login"}]
        }
        workflow_context.completed_stages.extend([
            "code_understanding",
            "domain_extraction",
            "user_journey_extraction",
        ])

        # Execute story extraction
        mock_felix = create_mock_agent(
            "Felix",
            {
                "epics": [{"id": "E1", "title": "UserManagement"}],
                "stories": [{"id": "S1", "title": "Login"}],
            },
        )

        with patch.object(
            brown_paper_orchestrator, "get_agents_for_stage", return_value=[mock_felix]
        ):
            stage = WorkflowStage(
                "story_extraction",
                "",
                ["Felix"],
                depends_on=["user_journey_extraction"],
            )
            result = await brown_paper_orchestrator.execute_stage(stage, workflow_context)

        assert result.status == WorkflowStatus.COMPLETED
        # Story extraction should be added while preserving previous data
        assert "domain_extraction_result" in workflow_context.shared_data
        assert "story_extraction_result" in workflow_context.shared_data

    @pytest.mark.asyncio
    async def test_estimation_receives_all_prior_data(
        self, brown_paper_orchestrator, workflow_context
    ):
        """Test that estimation stage has access to all prior stage data."""
        # Setup all prior stages
        prior_stages = {
            "code_understanding_result": {"files_scanned": 100},
            "domain_extraction_result": {"domains": []},
            "user_journey_extraction_result": {"user_journeys": []},
            "story_extraction_result": {
                "epics": [{"id": "E1"}],
                "stories": [{"id": "S1", "complexity": "medium"}],
            },
            "deep_extraction_result": {"refined_stories": []},
        }
        workflow_context.shared_data.update(prior_stages)
        workflow_context.completed_stages.extend([
            "code_understanding",
            "domain_extraction",
            "user_journey_extraction",
            "story_extraction",
            "deep_extraction",
        ])

        mock_eliza = create_mock_agent(
            "Eliza",
            {"story_estimates": [], "total_function_points": 100},
        )

        with patch.object(
            brown_paper_orchestrator, "get_agents_for_stage", return_value=[mock_eliza]
        ):
            stage = WorkflowStage(
                "estimation", "", ["Eliza"], depends_on=["deep_extraction"]
            )
            await brown_paper_orchestrator.execute_stage(stage, workflow_context)

        # All prior data should still be accessible
        for key in prior_stages:
            assert key in workflow_context.shared_data


# =============================================================================
# MIGRATION HANDOFF CHAIN TESTS
# =============================================================================


class TestMigrationHandoffChain:
    """Tests for Migration workflow stage handoffs."""

    @pytest.fixture
    def migration_context(self):
        """Create migration workflow context."""
        ctx = WorkflowContext(
            workflow_id="test-mig-handoff",
            workflow_type="migration",
            session_id="test-session",
            shared_data={
                "source_path": "/opt/legacy",
                "answers": {
                    "q1_legacy_system": "Classic ASP",
                    "q2_migration_target": ".NET 8",
                    "q3_migration_strategy": "Strangler",
                    "q4_data_migration": "SQL to PostgreSQL",
                    "q5_problem_statement": "Legacy unmaintainable",
                    "q6_stakeholders": "Dev team",
                    "q7_success_criteria": "Zero data loss",
                    "q8_timeline": "6 months",
                },
            },
        )
        # Add input_data required by security_analysis stage
        ctx.input_data = {"source_path": "/opt/legacy"}
        return ctx

    @pytest.mark.asyncio
    async def test_technical_to_security_handoff(
        self, migration_orchestrator, migration_context
    ):
        """Test handoff from technical_analysis to security_analysis."""
        # Setup: Add validation result
        migration_context.shared_data["validate_answers_result"] = {
            "valid": True,
            "answers_count": 8,
        }
        migration_context.completed_stages.append("validate_answers")

        # Execute technical analysis
        tech_output = {
            "tech_stack_detected": ["classic_asp", "vbscript"],
            "complexity_score": 0.8,
            "legacy_findings": [{"type": "sql_injection", "count": 15}],
        }
        mock_miguel = create_mock_agent("Miguel", tech_output)

        with patch.object(
            migration_orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage1 = WorkflowStage(
                "technical_analysis", "", ["Miguel"], depends_on=["validate_answers"]
            )
            await migration_orchestrator.execute_stage(stage1, migration_context)

        migration_context.completed_stages.append("technical_analysis")

        # Execute security analysis - should have access to tech stack info
        mock_quinn = create_mock_agent(
            "Quinn",
            {
                "findings": [],
                "cwe_top_25_coverage": 0.5,
            },
        )

        with patch.object(
            migration_orchestrator, "get_agents_for_stage", return_value=[mock_quinn]
        ):
            stage2 = WorkflowStage(
                "security_analysis", "", ["Quinn"], depends_on=["technical_analysis"]
            )
            result = await migration_orchestrator.execute_stage(stage2, migration_context)

        assert result.status == WorkflowStatus.COMPLETED
        # Both results should be present
        assert "technical_analysis_result" in migration_context.shared_data
        assert "security_analysis_result" in migration_context.shared_data

    @pytest.mark.asyncio
    async def test_specification_to_tasks_handoff(
        self, migration_orchestrator, migration_context
    ):
        """Test handoff from generate_specification to generate_tasks."""
        # Setup specification result
        migration_context.shared_data["generate_specification_result"] = {
            "specification": {
                "problem_statement": "Migrate ASP to .NET",
                "stakeholders": ["Dev Team"],
                "architecture_decisions": [{"decision": "Use microservices"}],
            },
        }
        migration_context.completed_stages.extend([
            "validate_answers",
            "technical_analysis",
            "security_analysis",
            "generate_specification",
        ])

        # Execute task generation
        mock_felix = create_mock_agent(
            "Felix",
            {
                "epics": [{"id": "E1", "title": "Data Migration"}],
                "migration_waves": [{"wave": 1, "epic_ids": ["E1"]}],
            },
        )

        with patch.object(
            migration_orchestrator, "get_agents_for_stage", return_value=[mock_felix]
        ):
            stage = WorkflowStage(
                "generate_tasks",
                "",
                ["Felix"],
                depends_on=["generate_specification"],
            )
            result = await migration_orchestrator.execute_stage(stage, migration_context)

        assert result.status == WorkflowStatus.COMPLETED
        # Spec should still be accessible
        assert "generate_specification_result" in migration_context.shared_data


# =============================================================================
# DATA FORMAT VALIDATION TESTS
# =============================================================================


class TestDataFormatValidation:
    """Tests for validating data formats in handoffs."""

    def test_epic_format_in_handoff(self, workflow_context):
        """Test that epics have required fields for downstream stages."""
        epic = {
            "id": "E1",
            "title": "User Management Epic",
            "description": "All user management features",
        }
        workflow_context.shared_data["story_extraction_result"] = {"epics": [epic]}

        stored_epics = workflow_context.shared_data["story_extraction_result"]["epics"]
        assert len(stored_epics) == 1
        assert "id" in stored_epics[0]
        assert "title" in stored_epics[0]

    def test_story_format_in_handoff(self, workflow_context):
        """Test that stories have required fields for estimation."""
        story = {
            "id": "S1",
            "title": "User login",
            "feature_id": "F1",
            "complexity": "medium",
        }
        workflow_context.shared_data["story_extraction_result"] = {"stories": [story]}

        stored_stories = workflow_context.shared_data["story_extraction_result"]["stories"]
        assert "id" in stored_stories[0]
        assert "title" in stored_stories[0]

    def test_domain_format_in_handoff(self, workflow_context):
        """Test that domains have required fields."""
        domain = {
            "name": "UserManagement",
            "modules": 15,
            "description": "User-related functionality",
        }
        workflow_context.shared_data["domain_extraction_result"] = {"domains": [domain]}

        stored_domains = workflow_context.shared_data["domain_extraction_result"]["domains"]
        assert "name" in stored_domains[0]


# =============================================================================
# PARALLEL AGENT HANDOFF TESTS
# =============================================================================


class TestParallelAgentHandoff:
    """Tests for parallel agent execution and result merging."""

    @pytest.mark.asyncio
    async def test_parallel_agents_results_merged(
        self, brown_paper_orchestrator, workflow_context
    ):
        """Test that parallel agents' results are merged correctly."""
        # Setup for deep extraction (parallel agents)
        workflow_context.shared_data["story_extraction_result"] = {
            "stories": [{"id": "S1"}]
        }
        workflow_context.completed_stages.append("story_extraction")

        # Mock two parallel agents
        mock_marcus = create_mock_agent(
            "Marcus", {"refined_stories": [{"id": "S1", "validated": True}]}
        )
        mock_betty = create_mock_agent(
            "Betty", {"business_rules": [{"id": "BR1"}]}
        )

        with patch.object(
            brown_paper_orchestrator,
            "get_agents_for_stage",
            return_value=[mock_marcus, mock_betty],
        ):
            stage = WorkflowStage(
                "deep_extraction",
                "",
                ["Marcus", "Betty"],
                parallel_agents=True,
                depends_on=["story_extraction"],
            )
            result = await brown_paper_orchestrator.execute_stage(stage, workflow_context)

        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_single_agent_failure_in_parallel(
        self, brown_paper_orchestrator, workflow_context
    ):
        """Test handling when one parallel agent fails."""
        workflow_context.shared_data["story_extraction_result"] = {
            "stories": [{"id": "S1"}]
        }
        workflow_context.completed_stages.append("story_extraction")

        mock_marcus = create_mock_agent("Marcus", {"refined_stories": []})
        mock_betty = MagicMock()
        mock_betty.name = "Betty"
        mock_betty.run_full_lifecycle = AsyncMock(
            return_value=MagicMock(success=False, output={})
        )

        with patch.object(
            brown_paper_orchestrator,
            "get_agents_for_stage",
            return_value=[mock_marcus, mock_betty],
        ):
            stage = WorkflowStage(
                "deep_extraction",
                "",
                ["Marcus", "Betty"],
                parallel_agents=True,
            )
            # Should still complete with partial results
            result = await brown_paper_orchestrator.execute_stage(stage, workflow_context)

        # Stage may complete with degraded output
        assert result is not None


# =============================================================================
# ERROR PROPAGATION TESTS
# =============================================================================


class TestErrorPropagation:
    """Tests for error handling in handoffs."""

    def test_missing_dependency_data_handled(self, workflow_context):
        """Test handling when expected dependency data is missing."""
        # Don't add code_understanding_result
        output = workflow_context.shared_data.get("code_understanding_result")
        assert output is None

    @pytest.mark.asyncio
    async def test_stage_failure_recorded(
        self, brown_paper_orchestrator, workflow_context
    ):
        """Test that stage failures are recorded in context."""
        mock_agent = MagicMock()
        mock_agent.name = "Miguel"
        mock_agent.run_full_lifecycle = AsyncMock(
            side_effect=RuntimeError("Agent error")
        )

        with patch.object(
            brown_paper_orchestrator, "get_agents_for_stage", return_value=[mock_agent]
        ):
            stage = WorkflowStage("code_understanding", "", ["Miguel"])
            result = await brown_paper_orchestrator.execute_stage(stage, workflow_context)

        assert result.status == WorkflowStatus.FAILED
        assert result.error is not None
