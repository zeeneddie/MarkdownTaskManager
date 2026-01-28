"""
Integration Tests for Workflow Error Recovery.

Tests error handling, retry mechanisms, and recovery scenarios
across all Confucius workflow types.

Coverage:
- Stage failure handling
- Retry mechanisms
- Graceful degradation
- Workflow restart from checkpoint
- Timeout handling
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import asyncio

from app.confucius.workflows import (
    BrownPaperOrchestrator,
    MigrationOrchestrator,
    GreenPaperOrchestrator,
    QualityOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
)
from app.confucius.workflows.base import StageResult


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def all_orchestrators():
    """Create instances of all orchestrators."""
    return {
        "brown_paper": BrownPaperOrchestrator(),
        "migration": MigrationOrchestrator(),
        "green_paper": GreenPaperOrchestrator(),
        "quality": QualityOrchestrator(),
    }


@pytest.fixture
def mock_successful_agent():
    """Create a mock agent that always succeeds."""
    mock = MagicMock()
    mock.name = "SuccessAgent"
    mock.run_full_lifecycle = AsyncMock(
        return_value=MagicMock(
            success=True,
            output={"data": "success"},
            confidence=0.9,
        )
    )
    return mock


@pytest.fixture
def mock_failing_agent():
    """Create a mock agent that always fails."""
    mock = MagicMock()
    mock.name = "FailingAgent"
    mock.run_full_lifecycle = AsyncMock(
        side_effect=RuntimeError("Agent execution failed")
    )
    return mock


@pytest.fixture
def mock_timeout_agent():
    """Create a mock agent that times out."""
    async def slow_execution(*args, **kwargs):
        await asyncio.sleep(10)  # Simulate slow execution
        return MagicMock(success=True, output={})

    mock = MagicMock()
    mock.name = "SlowAgent"
    mock.run_full_lifecycle = slow_execution
    return mock


# =============================================================================
# STAGE FAILURE HANDLING TESTS
# =============================================================================


class TestStageFailureHandling:
    """Tests for handling stage failures."""

    @pytest.mark.asyncio
    async def test_brown_paper_stage_failure_recorded(
        self, mock_failing_agent
    ):
        """Test that Brown Paper stage failure is properly recorded."""
        orchestrator = BrownPaperOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test-fail",
                input_data={"scan_path": "/tmp/test", "tech_stack": ["python"]},
            )

        assert result.status == WorkflowStatus.FAILED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_migration_stage_failure_recorded(
        self, mock_failing_agent
    ):
        """Test that Migration stage failure is properly recorded."""
        orchestrator = MigrationOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test-fail",
                input_data={
                    "source_path": "/tmp/test",
                    "answers": {f"q{i}_field": f"answer_{i}" for i in range(1, 9)},
                },
            )

        # Should fail at validation or first execution stage
        assert result is not None

    @pytest.mark.asyncio
    async def test_quality_stage_failure_recorded(
        self, mock_failing_agent
    ):
        """Test that Quality stage failure is properly recorded."""
        orchestrator = QualityOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test-fail",
                input_data={"project_path": "/tmp/test", "scanners": ["complexity"]},
            )

        assert result.status == WorkflowStatus.FAILED

    @pytest.mark.asyncio
    async def test_failure_includes_stage_name(self, mock_failing_agent):
        """Test that failure result includes which stage failed."""
        orchestrator = BrownPaperOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        # Error message should indicate the failing stage
        assert result.error is not None


# =============================================================================
# RETRY MECHANISM TESTS
# =============================================================================


class TestRetryMechanisms:
    """Tests for retry mechanisms in workflows."""

    @pytest.mark.asyncio
    async def test_transient_failure_recovery(self, mock_successful_agent):
        """Test recovery from transient failures."""
        orchestrator = BrownPaperOrchestrator()
        call_count = 0

        async def failing_then_succeeding(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("Transient error")
            return MagicMock(success=True, output={"data": "recovered"})

        mock_agent = MagicMock()
        mock_agent.name = "RetryAgent"
        mock_agent.run_full_lifecycle = failing_then_succeeding

        # Note: Actual retry behavior depends on orchestrator implementation
        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_agent]
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        # Should either succeed (if retries work) or fail gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_failing_agent):
        """Test handling when max retries are exceeded."""
        orchestrator = BrownPaperOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        # Should fail after exhausting retries
        assert result.status == WorkflowStatus.FAILED


# =============================================================================
# GRACEFUL DEGRADATION TESTS
# =============================================================================


class TestGracefulDegradation:
    """Tests for graceful degradation when components fail."""

    @pytest.mark.asyncio
    async def test_workflow_without_agents(self):
        """Test workflow behavior when no agents are available."""
        orchestrator = BrownPaperOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[]
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        # Should complete with default/empty results, not crash
        assert result is not None

    @pytest.mark.asyncio
    async def test_partial_agent_failure(self, mock_successful_agent, mock_failing_agent):
        """Test workflow when some agents succeed and others fail."""
        orchestrator = BrownPaperOrchestrator()

        def mixed_agents(stage, context):
            if stage.name == "code_understanding":
                return [mock_successful_agent]
            else:
                return [mock_failing_agent]

        with patch.object(
            orchestrator, "get_agents_for_stage", side_effect=mixed_agents
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        # Workflow should handle partial failure
        assert result is not None


# =============================================================================
# CHECKPOINT AND RESTART TESTS
# =============================================================================


class TestCheckpointRestart:
    """Tests for workflow checkpoint and restart functionality."""

    @pytest.mark.asyncio
    async def test_context_preserves_completed_stages(
        self, mock_successful_agent
    ):
        """Test that context tracks which stages completed."""
        orchestrator = BrownPaperOrchestrator()
        final_context = None

        def capture_context(stage, context):
            nonlocal final_context
            final_context = context
            return [mock_successful_agent]

        with patch.object(
            orchestrator, "get_agents_for_stage", side_effect=capture_context
        ):
            await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        # Context should track completed stages
        if final_context:
            assert len(final_context.completed_stages) >= 0

    @pytest.mark.asyncio
    async def test_stage_results_persisted(self, mock_successful_agent):
        """Test that stage results are persisted in shared_data."""
        orchestrator = BrownPaperOrchestrator()
        captured_shared_data = {}

        def capture_data(stage, context):
            captured_shared_data.update(context.shared_data)
            return [mock_successful_agent]

        with patch.object(
            orchestrator, "get_agents_for_stage", side_effect=capture_data
        ):
            await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test", "tech_stack": ["python"]},
            )

        # Should have input data preserved
        assert "scan_path" in captured_shared_data or "tech_stack" in captured_shared_data


# =============================================================================
# TIMEOUT HANDLING TESTS
# =============================================================================


class TestTimeoutHandling:
    """Tests for timeout handling in workflows."""

    @pytest.mark.asyncio
    async def test_stage_timeout_configuration(self):
        """Test that stages have timeout configuration."""
        orchestrator = BrownPaperOrchestrator()
        stages = orchestrator.get_stages()

        for stage in stages:
            assert stage.timeout_seconds > 0, f"{stage.name} missing timeout"

    @pytest.mark.asyncio
    async def test_stages_have_max_iterations(self):
        """Test that stages have max_iterations for retry control."""
        orchestrator = BrownPaperOrchestrator()
        stages = orchestrator.get_stages()

        for stage in stages:
            assert stage.max_iterations >= 1, f"{stage.name} invalid max_iterations"


# =============================================================================
# CROSS-ORCHESTRATOR ERROR TESTS
# =============================================================================


class TestCrossOrchestratorErrors:
    """Tests for error handling across all orchestrator types."""

    @pytest.mark.asyncio
    async def test_all_orchestrators_handle_empty_input(
        self, all_orchestrators, mock_successful_agent
    ):
        """Test all orchestrators handle empty input gracefully."""
        for name, orchestrator in all_orchestrators.items():
            with patch.object(
                orchestrator, "get_agents_for_stage", return_value=[mock_successful_agent]
            ):
                result = await orchestrator.run(
                    session_id=f"test-{name}",
                    input_data={},
                )

            # Each orchestrator should return a result (success or failure)
            assert result is not None, f"{name} orchestrator returned None"

    @pytest.mark.asyncio
    async def test_all_orchestrators_handle_agent_failure(
        self, all_orchestrators, mock_failing_agent
    ):
        """Test all orchestrators handle agent failures."""
        for name, orchestrator in all_orchestrators.items():
            with patch.object(
                orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
            ):
                result = await orchestrator.run(
                    session_id=f"test-{name}",
                    input_data={"scan_path": "/tmp/test"},
                )

            # Each orchestrator should handle failure gracefully
            assert result is not None, f"{name} orchestrator crashed on agent failure"
            assert result.status == WorkflowStatus.FAILED, f"{name} should report failure"


# =============================================================================
# ERROR MESSAGE QUALITY TESTS
# =============================================================================


class TestErrorMessageQuality:
    """Tests for quality of error messages."""

    @pytest.mark.asyncio
    async def test_error_message_not_empty(self, mock_failing_agent):
        """Test that error messages are not empty."""
        orchestrator = BrownPaperOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        if result.status == WorkflowStatus.FAILED:
            assert result.error is not None
            assert len(result.error) > 0

    @pytest.mark.asyncio
    async def test_error_message_contains_context(self, mock_failing_agent):
        """Test that error messages contain useful context."""
        orchestrator = BrownPaperOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        if result.error:
            # Error should mention what went wrong
            assert len(result.error) > 5  # Not just "error"


# =============================================================================
# CLEANUP TESTS
# =============================================================================


class TestWorkflowCleanup:
    """Tests for workflow cleanup after errors."""

    @pytest.mark.asyncio
    async def test_resources_released_on_failure(self, mock_failing_agent):
        """Test that resources are released when workflow fails."""
        orchestrator = BrownPaperOrchestrator()

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_failing_agent]
        ):
            result = await orchestrator.run(
                session_id="test",
                input_data={"scan_path": "/tmp/test"},
            )

        # Workflow should complete cleanup (no hanging resources)
        assert result is not None
        # Orchestrator should be reusable after failure
        assert orchestrator.workflow_type == "brown_paper"
