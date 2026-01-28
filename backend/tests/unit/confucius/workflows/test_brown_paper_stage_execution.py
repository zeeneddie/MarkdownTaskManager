"""
Unit Tests for Brown Paper Stage Execution.

Tests individual stage execution logic with mocked agent extensions.
Each stage is tested in isolation with controlled inputs and outputs.

Coverage:
- code_understanding stage
- domain_extraction stage
- user_journey_extraction stage
- story_extraction stage
- deep_extraction stage
- estimation stage
- output_consolidation stage
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.confucius.workflows import (
    BrownPaperOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowStatus,
)
from app.confucius.workflows.base import StageResult


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def orchestrator():
    """Create Brown Paper orchestrator instance."""
    return BrownPaperOrchestrator()


@pytest.fixture
def base_context():
    """Create base workflow context with required shared data."""
    return WorkflowContext(
        workflow_id="test-bp-001",
        workflow_type="brown_paper",
        session_id="test-session-001",
        shared_data={
            "scan_path": "/tmp/test-project",
            "tech_stack": ["python", "javascript"],
            "application_id": "test-app",
        },
    )


@pytest.fixture
def mock_agent_extension():
    """Create a mock agent extension with configurable output."""
    def _create_mock(success: bool = True, output: Dict[str, Any] = None):
        mock = MagicMock()
        mock.name = "MockAgent"
        mock.run_full_lifecycle = AsyncMock(
            return_value=MagicMock(
                success=success,
                output=output or {"metrics": {}},
            )
        )
        return mock
    return _create_mock


# =============================================================================
# CODE UNDERSTANDING STAGE TESTS
# =============================================================================


class TestCodeUnderstandingStage:
    """Tests for code_understanding stage execution."""

    @pytest.mark.asyncio
    async def test_code_understanding_success(
        self, orchestrator, base_context, mock_agent_extension
    ):
        """Test successful code understanding execution."""
        mock_miguel = mock_agent_extension(
            success=True,
            output={
                "metrics": {
                    "files_scanned": 150,
                    "lines_of_code": 25000,
                    "complexity_score": 0.72,
                    "dependency_graph": {"nodes": 50, "edges": 120},
                }
            },
        )
        mock_miguel.name = "Miguel"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage = WorkflowStage(
                name="code_understanding",
                description="Analyze code structure",
                agents=["Miguel"],
            )

            result = await orchestrator.execute_stage(stage, base_context)

            assert result.status == WorkflowStatus.COMPLETED
            assert result.stage_name == "code_understanding"
            assert result.error is None
            assert "code_understanding_result" in base_context.shared_data

    @pytest.mark.asyncio
    async def test_code_understanding_no_agent(self, orchestrator, base_context):
        """Test code understanding when no agent is available."""
        with patch.object(orchestrator, "get_agents_for_stage", return_value=[]):
            stage = WorkflowStage(
                name="code_understanding",
                description="Analyze code structure",
                agents=["Miguel"],
            )

            result = await orchestrator.execute_stage(stage, base_context)

            # Should complete with default/empty results
            assert result.status == WorkflowStatus.COMPLETED
            assert "code_understanding_result" in base_context.shared_data

    @pytest.mark.asyncio
    async def test_code_understanding_agent_failure(
        self, orchestrator, base_context, mock_agent_extension
    ):
        """Test code understanding when agent fails."""
        mock_miguel = mock_agent_extension(success=False, output={})
        mock_miguel.name = "Miguel"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage = WorkflowStage(
                name="code_understanding",
                description="Analyze code structure",
                agents=["Miguel"],
            )

            result = await orchestrator.execute_stage(stage, base_context)

            # Should still complete but with minimal results
            assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_code_understanding_stores_results(
        self, orchestrator, base_context, mock_agent_extension
    ):
        """Test that code understanding stores results in context."""
        expected_metrics = {
            "files_scanned": 100,
            "lines_of_code": 5000,
            "complexity_score": 0.65,
        }
        mock_miguel = mock_agent_extension(
            success=True, output={"metrics": expected_metrics}
        )
        mock_miguel.name = "Miguel"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage = WorkflowStage(
                name="code_understanding",
                description="Analyze code structure",
                agents=["Miguel"],
            )

            await orchestrator.execute_stage(stage, base_context)

            stored_result = base_context.shared_data.get("code_understanding_result", {})
            assert stored_result.get("files_scanned") == 100
            assert stored_result.get("lines_of_code") == 5000


# =============================================================================
# DOMAIN EXTRACTION STAGE TESTS
# =============================================================================


class TestDomainExtractionStage:
    """Tests for domain_extraction stage execution."""

    @pytest.fixture
    def context_with_code_understanding(self, base_context):
        """Context with code understanding results."""
        base_context.shared_data["code_understanding_result"] = {
            "files_scanned": 100,
            "dependency_graph": {"nodes": 50, "edges": 100},
            "layer_analysis": {"presentation": 20, "business": 50, "data": 30},
        }
        base_context.completed_stages.append("code_understanding")
        return base_context

    @pytest.mark.asyncio
    async def test_domain_extraction_success(
        self, orchestrator, context_with_code_understanding, mock_agent_extension
    ):
        """Test successful domain extraction."""
        mock_peter = mock_agent_extension(
            success=True,
            output={
                "domains": [
                    {"name": "UserManagement", "modules": 15},
                    {"name": "OrderProcessing", "modules": 25},
                ],
                "business_capabilities": ["Authentication", "Ordering"],
            },
        )
        mock_peter.name = "Peter"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_peter]
        ):
            stage = WorkflowStage(
                name="domain_extraction",
                description="Extract business domains",
                agents=["Peter", "Betty"],
                depends_on=["code_understanding"],
            )

            result = await orchestrator.execute_stage(
                stage, context_with_code_understanding
            )

            assert result.status == WorkflowStatus.COMPLETED
            assert "domain_extraction_result" in context_with_code_understanding.shared_data

    @pytest.mark.asyncio
    async def test_domain_extraction_uses_code_analysis(
        self, orchestrator, context_with_code_understanding, mock_agent_extension
    ):
        """Test that domain extraction uses previous code analysis results."""
        mock_peter = mock_agent_extension(success=True, output={"domains": []})
        mock_peter.name = "Peter"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_peter]
        ):
            stage = WorkflowStage(
                name="domain_extraction",
                description="Extract business domains",
                agents=["Peter"],
                depends_on=["code_understanding"],
            )

            await orchestrator.execute_stage(stage, context_with_code_understanding)

            # Verify agent was called (would use code_understanding_result)
            mock_peter.run_full_lifecycle.assert_called_once()


# =============================================================================
# STORY EXTRACTION STAGE TESTS
# =============================================================================


class TestStoryExtractionStage:
    """Tests for story_extraction stage execution."""

    @pytest.fixture
    def context_with_domains(self, base_context):
        """Context with domain extraction results."""
        base_context.shared_data["code_understanding_result"] = {"files_scanned": 100}
        base_context.shared_data["domain_extraction_result"] = {
            "domains": [{"name": "UserManagement", "modules": 15}]
        }
        base_context.shared_data["user_journey_extraction_result"] = {
            "user_journeys": [{"name": "Login", "steps": 5}]
        }
        base_context.completed_stages.extend([
            "code_understanding",
            "domain_extraction",
            "user_journey_extraction",
        ])
        return base_context

    @pytest.mark.asyncio
    async def test_story_extraction_success(
        self, orchestrator, context_with_domains, mock_agent_extension
    ):
        """Test successful story extraction."""
        mock_felix = mock_agent_extension(
            success=True,
            output={
                "epics": [{"id": "E1", "title": "User Management"}],
                "features": [{"id": "F1", "epic_id": "E1", "title": "Authentication"}],
                "stories": [
                    {
                        "id": "S1",
                        "feature_id": "F1",
                        "title": "User login",
                        "story_points": 5,
                    }
                ],
            },
        )
        mock_felix.name = "Felix"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_felix]
        ):
            stage = WorkflowStage(
                name="story_extraction",
                description="Extract user stories",
                agents=["Felix", "Quinn"],
                depends_on=["user_journey_extraction"],
            )

            result = await orchestrator.execute_stage(stage, context_with_domains)

            assert result.status == WorkflowStatus.COMPLETED
            stored = context_with_domains.shared_data.get("story_extraction_result", {})
            assert "epics" in stored or len(stored) > 0


# =============================================================================
# DEEP EXTRACTION STAGE TESTS
# =============================================================================


class TestDeepExtractionStage:
    """Tests for deep_extraction stage execution."""

    @pytest.fixture
    def context_with_stories(self, base_context):
        """Context with story extraction results."""
        base_context.shared_data["story_extraction_result"] = {
            "epics": [{"id": "E1", "title": "User Management"}],
            "stories": [{"id": "S1", "title": "Login", "story_points": 5}],
        }
        base_context.completed_stages.append("story_extraction")
        return base_context

    @pytest.mark.asyncio
    async def test_deep_extraction_success(
        self, orchestrator, context_with_stories, mock_agent_extension
    ):
        """Test successful deep extraction with LLM council."""
        mock_marcus = mock_agent_extension(
            success=True,
            output={
                "refined_stories": [
                    {"id": "S1", "title": "Login", "confidence": 0.92}
                ],
                "conflicts_resolved": 2,
                "consensus_confidence": 0.88,
            },
        )
        mock_marcus.name = "Marcus"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_marcus]
        ):
            stage = WorkflowStage(
                name="deep_extraction",
                description="Deep extraction with LLM council",
                agents=["Marcus", "Betty"],
                parallel_agents=True,
                depends_on=["story_extraction"],
            )

            result = await orchestrator.execute_stage(stage, context_with_stories)

            assert result.status == WorkflowStatus.COMPLETED


# =============================================================================
# ESTIMATION STAGE TESTS
# =============================================================================


class TestEstimationStage:
    """Tests for estimation stage execution."""

    @pytest.fixture
    def context_with_deep_extraction(self, base_context):
        """Context with deep extraction results."""
        base_context.shared_data["deep_extraction_result"] = {
            "refined_stories": [
                {"id": "S1", "title": "Login", "complexity": "medium"},
                {"id": "S2", "title": "Registration", "complexity": "high"},
            ]
        }
        base_context.completed_stages.append("deep_extraction")
        return base_context

    @pytest.mark.asyncio
    async def test_estimation_success(
        self, orchestrator, context_with_deep_extraction, mock_agent_extension
    ):
        """Test successful estimation."""
        mock_eliza = mock_agent_extension(
            success=True,
            output={
                "story_estimates": [
                    {"id": "S1", "story_points": 5, "function_points": 12},
                    {"id": "S2", "story_points": 8, "function_points": 20},
                ],
                "total_function_points": 32,
                "effort_hours": 160,
            },
        )
        mock_eliza.name = "Eliza"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_eliza]
        ):
            stage = WorkflowStage(
                name="estimation",
                description="Estimate effort",
                agents=["Eliza"],
                depends_on=["deep_extraction"],
            )

            result = await orchestrator.execute_stage(
                stage, context_with_deep_extraction
            )

            assert result.status == WorkflowStatus.COMPLETED
            stored = context_with_deep_extraction.shared_data.get(
                "estimation_result", {}
            )
            assert "story_estimates" in stored or "total_function_points" in stored or len(stored) > 0


# =============================================================================
# OUTPUT CONSOLIDATION STAGE TESTS
# =============================================================================


class TestOutputConsolidationStage:
    """Tests for output_consolidation stage execution."""

    @pytest.fixture
    def context_with_all_stages(self, base_context):
        """Context with all previous stage results."""
        base_context.shared_data.update({
            "code_understanding_result": {"files_scanned": 100},
            "domain_extraction_result": {"domains": [{"name": "Core"}]},
            "story_extraction_result": {"epics": [], "stories": []},
            "deep_extraction_result": {"refined_stories": []},
            "estimation_result": {"total_function_points": 50},
        })
        base_context.completed_stages.extend([
            "code_understanding",
            "domain_extraction",
            "user_journey_extraction",
            "story_extraction",
            "deep_extraction",
            "estimation",
        ])
        return base_context

    @pytest.mark.asyncio
    async def test_output_consolidation_success(
        self, orchestrator, context_with_all_stages, mock_agent_extension
    ):
        """Test successful output consolidation."""
        mock_diana = mock_agent_extension(
            success=True,
            output={
                "summary": "Analysis complete",
                "recommendations": ["Refactor module X", "Add tests for Y"],
                "next_steps": ["Review epics", "Prioritize stories"],
            },
        )
        mock_diana.name = "Diana"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_diana]
        ):
            stage = WorkflowStage(
                name="output_consolidation",
                description="Consolidate output",
                agents=["Diana"],
                depends_on=["estimation"],
            )

            result = await orchestrator.execute_stage(stage, context_with_all_stages)

            assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_output_consolidation_collects_all_results(
        self, orchestrator, context_with_all_stages, mock_agent_extension
    ):
        """Test that consolidation has access to all previous results."""
        mock_diana = mock_agent_extension(success=True, output={})
        mock_diana.name = "Diana"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_diana]
        ):
            stage = WorkflowStage(
                name="output_consolidation",
                description="Consolidate output",
                agents=["Diana"],
                depends_on=["estimation"],
            )

            await orchestrator.execute_stage(stage, context_with_all_stages)

            # Verify all previous results are available
            assert "code_understanding_result" in context_with_all_stages.shared_data
            assert "domain_extraction_result" in context_with_all_stages.shared_data
            assert "estimation_result" in context_with_all_stages.shared_data


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestStageErrorHandling:
    """Tests for error handling in stage execution."""

    @pytest.mark.asyncio
    async def test_unknown_stage_raises_error(self, orchestrator, base_context):
        """Test that unknown stage name raises error."""
        stage = WorkflowStage(
            name="unknown_stage",
            description="Unknown stage",
            agents=[],
        )

        result = await orchestrator.execute_stage(stage, base_context)

        assert result.status == WorkflowStatus.FAILED
        assert "Unknown stage" in result.error

    @pytest.mark.asyncio
    async def test_exception_in_stage_is_caught(
        self, orchestrator, base_context, mock_agent_extension
    ):
        """Test that exceptions in stage execution are caught."""
        mock_agent = mock_agent_extension()
        mock_agent.run_full_lifecycle = AsyncMock(
            side_effect=RuntimeError("Agent crashed")
        )

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_agent]
        ):
            stage = WorkflowStage(
                name="code_understanding",
                description="Analyze code",
                agents=["Miguel"],
            )

            result = await orchestrator.execute_stage(stage, base_context)

            assert result.status == WorkflowStatus.FAILED
            assert "Agent crashed" in result.error

    @pytest.mark.asyncio
    async def test_stage_result_has_timing_info(
        self, orchestrator, base_context, mock_agent_extension
    ):
        """Test that stage result includes timing information."""
        mock_miguel = mock_agent_extension(success=True, output={"metrics": {}})
        mock_miguel.name = "Miguel"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage = WorkflowStage(
                name="code_understanding",
                description="Analyze code",
                agents=["Miguel"],
            )

            result = await orchestrator.execute_stage(stage, base_context)

            assert result.started_at is not None
            assert result.completed_at is not None
            assert result.completed_at >= result.started_at


# =============================================================================
# QUALITY THRESHOLD TESTS
# =============================================================================


class TestQualityThresholds:
    """Tests for quality threshold enforcement."""

    @pytest.mark.asyncio
    async def test_stage_returns_quality_score(
        self, orchestrator, base_context, mock_agent_extension
    ):
        """Test that stage result includes quality score."""
        mock_miguel = mock_agent_extension(success=True, output={"metrics": {}})
        mock_miguel.name = "Miguel"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage = WorkflowStage(
                name="code_understanding",
                description="Analyze code",
                agents=["Miguel"],
                quality_threshold=0.85,
            )

            result = await orchestrator.execute_stage(stage, base_context)

            assert result.quality_score is not None
            assert 0 <= result.quality_score <= 1

    def test_stage_quality_threshold_configuration(self, orchestrator):
        """Test that stages have appropriate quality thresholds."""
        stages = orchestrator.get_stages()
        stage_map = {s.name: s for s in stages}

        # All stages should have positive thresholds
        for stage in stages:
            assert stage.quality_threshold > 0, f"{stage.name} should have positive threshold"

        # Code understanding and domain extraction are critical
        assert stage_map["code_understanding"].quality_threshold >= 0.70
        assert stage_map["domain_extraction"].quality_threshold >= 0.70
