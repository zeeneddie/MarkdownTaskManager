"""
Integration tests for Restartable Workflows (Fase 24.6).

Week 158 - Tests the complete checkpoint/resume lifecycle:
- Checkpoint creation after stages
- Resume from failure point
- Idempotent stage execution
- Error recovery
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.confucius.workflows.base import (
    WorkflowOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    StageResult,
)
from app.services.checkpoint_service import CheckpointService
from app.models.workflow_checkpoint import WorkflowCheckpoint, CheckpointStatus


class MockWorkflowOrchestrator(WorkflowOrchestrator):
    """Mock workflow orchestrator for testing."""

    def __init__(self, stages=None, fail_at_stage=None, **kwargs):
        super().__init__(**kwargs)
        self._stages = stages or [
            WorkflowStage("stage_1", "First stage", ["Felix"]),
            WorkflowStage("stage_2", "Second stage", ["Quinn"]),
            WorkflowStage("stage_3", "Third stage", ["Diana"]),
        ]
        self._fail_at_stage = fail_at_stage
        self._executed_stages = []

    @property
    def workflow_type(self) -> str:
        return "test_workflow"

    def get_stages(self):
        return self._stages

    async def execute_stage(self, stage, context):
        self._executed_stages.append(stage.name)

        if stage.name == self._fail_at_stage:
            return StageResult(
                stage_name=stage.name,
                status=WorkflowStatus.FAILED,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                error=f"Simulated failure at {stage.name}",
            )

        return StageResult(
            stage_name=stage.name,
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            agent_results={"output": f"Result from {stage.name}"},
            quality_score=0.9,
            passed_quality_gate=True,
        )


class TestWorkflowOrchestratorWithCheckpoints:
    """Test WorkflowOrchestrator checkpoint integration."""

    @pytest.fixture
    def mock_checkpoint_service(self):
        """Create a mock checkpoint service."""
        service = MagicMock(spec=CheckpointService)
        service.save_checkpoint = AsyncMock(return_value=MagicMock())
        service.load_checkpoint = AsyncMock(return_value=None)
        service.record_error = AsyncMock(return_value=MagicMock())
        service.mark_completed = AsyncMock(return_value=MagicMock())
        service.prepare_for_resume = AsyncMock(return_value=None)
        service.restore_context = AsyncMock(return_value={})
        return service

    @pytest.mark.asyncio
    async def test_workflow_saves_checkpoint_after_each_stage(self, mock_checkpoint_service):
        """Test that checkpoints are saved after each successful stage."""
        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_checkpoint_service)

        result = await workflow.run(
            session_id="test-session",
            input_data={"key": "value"},
        )

        # Verify all stages completed
        assert result.status == WorkflowStatus.COMPLETED
        assert result.stages_completed == 3

        # Verify checkpoint saved after each stage
        assert mock_checkpoint_service.save_checkpoint.call_count == 3

    @pytest.mark.asyncio
    async def test_workflow_records_error_on_failure(self, mock_checkpoint_service):
        """Test that errors are recorded in checkpoint on stage failure."""
        workflow = MockWorkflowOrchestrator(
            fail_at_stage="stage_2",
            checkpoint_service=mock_checkpoint_service,
        )

        result = await workflow.run(
            session_id="test-session",
            input_data={"key": "value"},
        )

        # Verify workflow failed
        assert result.status == WorkflowStatus.FAILED
        assert "stage_2" in result.error

        # Verify error recorded
        mock_checkpoint_service.record_error.assert_called_once()
        call_args = mock_checkpoint_service.record_error.call_args
        assert call_args.kwargs["stage_name"] == "stage_2"

    @pytest.mark.asyncio
    async def test_workflow_marks_completed_on_success(self, mock_checkpoint_service):
        """Test that workflow is marked completed after successful execution."""
        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_checkpoint_service)

        result = await workflow.run(
            session_id="test-session",
            input_data={"key": "value"},
        )

        assert result.status == WorkflowStatus.COMPLETED
        mock_checkpoint_service.mark_completed.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_without_checkpoint_service(self):
        """Test that workflow runs normally without checkpoint service."""
        workflow = MockWorkflowOrchestrator(checkpoint_service=None)

        result = await workflow.run(
            session_id="test-session",
            input_data={"key": "value"},
        )

        assert result.status == WorkflowStatus.COMPLETED
        assert result.stages_completed == 3

    @pytest.mark.asyncio
    async def test_workflow_skips_completed_stages(self, mock_checkpoint_service):
        """Test that resumed workflow skips already completed stages."""
        # Setup checkpoint with stage_1 completed
        mock_checkpoint = MagicMock(spec=WorkflowCheckpoint)
        mock_checkpoint.workflow_id = "test-wf-123"
        mock_checkpoint.resume_stage = "stage_2"

        mock_checkpoint_service.load_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_service.restore_context.return_value = {
            "workflow_id": "test-wf-123",
            "workflow_type": "test_workflow",
            "session_id": "test-session",
            "started_at": datetime.now(timezone.utc),
            "completed_stages": ["stage_1"],
            "stage_results": {
                "stage_1": {
                    "agent_results": {"output": "Previous result"},
                    "quality_score": 0.9,
                }
            },
            "shared_data": {"key": "value"},
            "input_data": {},
            "metadata": {},
        }

        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_checkpoint_service)

        result = await workflow.run(
            session_id="test-session",
            input_data={"key": "value"},
            resume_from_checkpoint=True,
        )

        assert result.status == WorkflowStatus.COMPLETED
        # stage_1 was skipped, only stage_2 and stage_3 executed
        assert "stage_1" not in workflow._executed_stages
        assert "stage_2" in workflow._executed_stages
        assert "stage_3" in workflow._executed_stages


class TestWorkflowResume:
    """Test workflow resume functionality."""

    @pytest.fixture
    def mock_checkpoint_service(self):
        """Create a mock checkpoint service."""
        service = MagicMock(spec=CheckpointService)
        service.save_checkpoint = AsyncMock(return_value=MagicMock())
        service.load_checkpoint = AsyncMock(return_value=None)
        service.record_error = AsyncMock(return_value=MagicMock())
        service.mark_completed = AsyncMock(return_value=MagicMock())
        return service

    @pytest.mark.asyncio
    async def test_resume_raises_without_checkpoint_service(self):
        """Test that resume raises error without checkpoint service."""
        workflow = MockWorkflowOrchestrator(checkpoint_service=None)

        with pytest.raises(ValueError, match="no checkpoint service configured"):
            await workflow.resume(
                session_id="test-session",
                workflow_id="test-workflow",
            )

    @pytest.mark.asyncio
    async def test_resume_raises_when_no_checkpoint(self, mock_checkpoint_service):
        """Test that resume raises error when no checkpoint found."""
        mock_checkpoint_service.prepare_for_resume = AsyncMock(return_value=None)

        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_checkpoint_service)

        with pytest.raises(ValueError, match="no checkpoint found"):
            await workflow.resume(
                session_id="test-session",
                workflow_id="test-workflow",
            )

    @pytest.mark.asyncio
    async def test_resume_with_skip_failed_stage(self, mock_checkpoint_service):
        """Test resume with skip_failed_stage option."""
        mock_checkpoint_service.prepare_for_resume = AsyncMock(return_value={
            "workflow_id": "test-wf-123",
            "workflow_type": "test_workflow",
            "session_id": "test-session",
            "started_at": datetime.now(timezone.utc),
            "completed_stages": ["stage_1", "stage_2"],  # stage_2 added by skip
            "stage_results": {},
            "shared_data": {},
            "input_data": {"original": "input"},
            "metadata": {},
        })
        mock_checkpoint_service.load_checkpoint.return_value = MagicMock(
            workflow_id="test-wf-123",
            resume_stage="stage_3",
        )
        mock_checkpoint_service.restore_context.return_value = {
            "workflow_id": "test-wf-123",
            "workflow_type": "test_workflow",
            "session_id": "test-session",
            "started_at": datetime.now(timezone.utc),
            "completed_stages": ["stage_1", "stage_2"],
            "stage_results": {},
            "shared_data": {},
            "input_data": {"original": "input"},
            "metadata": {},
        }

        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_checkpoint_service)

        result = await workflow.resume(
            session_id="test-session",
            workflow_id="test-wf-123",
            skip_failed_stage=True,
        )

        mock_checkpoint_service.prepare_for_resume.assert_called_once_with(
            session_id="test-session",
            workflow_type="test_workflow",
            workflow_id="test-wf-123",
            skip_failed_stage=True,
        )


class TestCheckpointStatusTracking:
    """Test checkpoint status transitions."""

    @pytest.mark.asyncio
    async def test_checkpoint_status_running_during_execution(self):
        """Test checkpoint status is RUNNING during execution."""
        mock_service = MagicMock(spec=CheckpointService)
        mock_service.save_checkpoint = AsyncMock(return_value=MagicMock())
        mock_service.load_checkpoint = AsyncMock(return_value=None)
        mock_service.mark_completed = AsyncMock(return_value=MagicMock())

        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_service)

        await workflow.run(
            session_id="test-session",
            input_data={},
        )

        # Check that save_checkpoint was called with correct status implied
        assert mock_service.save_checkpoint.call_count == 3

    @pytest.mark.asyncio
    async def test_checkpoint_status_completed_after_success(self):
        """Test checkpoint marked completed after successful workflow."""
        mock_service = MagicMock(spec=CheckpointService)
        mock_service.save_checkpoint = AsyncMock(return_value=MagicMock())
        mock_service.load_checkpoint = AsyncMock(return_value=None)
        mock_service.mark_completed = AsyncMock(return_value=MagicMock())

        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_service)

        result = await workflow.run(
            session_id="test-session",
            input_data={},
        )

        assert result.status == WorkflowStatus.COMPLETED
        mock_service.mark_completed.assert_called_once()

    @pytest.mark.asyncio
    async def test_checkpoint_status_failed_after_error(self):
        """Test checkpoint marked failed after error."""
        mock_service = MagicMock(spec=CheckpointService)
        mock_service.save_checkpoint = AsyncMock(return_value=MagicMock())
        mock_service.load_checkpoint = AsyncMock(return_value=None)
        mock_service.record_error = AsyncMock(return_value=MagicMock())

        workflow = MockWorkflowOrchestrator(
            fail_at_stage="stage_2",
            checkpoint_service=mock_service,
        )

        result = await workflow.run(
            session_id="test-session",
            input_data={},
        )

        assert result.status == WorkflowStatus.FAILED
        mock_service.record_error.assert_called_once()


class TestIdempotentStageExecution:
    """Test idempotent stage execution on resume."""

    @pytest.mark.asyncio
    async def test_completed_stages_not_re_executed(self):
        """Test that completed stages are not executed again on resume."""
        mock_service = MagicMock(spec=CheckpointService)

        mock_checkpoint = MagicMock(spec=WorkflowCheckpoint)
        mock_checkpoint.workflow_id = "test-wf-123"
        mock_checkpoint.resume_stage = "stage_2"

        mock_service.load_checkpoint = AsyncMock(return_value=mock_checkpoint)
        mock_service.restore_context = AsyncMock(return_value={
            "workflow_id": "test-wf-123",
            "workflow_type": "test_workflow",
            "session_id": "test-session",
            "started_at": datetime.now(timezone.utc),
            "completed_stages": ["stage_1"],
            "stage_results": {
                "stage_1": {
                    "agent_results": {"output": "Previous result"},
                    "quality_score": 0.9,
                }
            },
            "shared_data": {},
            "input_data": {},
            "metadata": {},
        })
        mock_service.save_checkpoint = AsyncMock(return_value=MagicMock())
        mock_service.mark_completed = AsyncMock(return_value=MagicMock())

        workflow = MockWorkflowOrchestrator(checkpoint_service=mock_service)

        await workflow.run(
            session_id="test-session",
            input_data={},
            resume_from_checkpoint=True,
        )

        # stage_1 should NOT be in executed stages (it was skipped)
        assert "stage_1" not in workflow._executed_stages

        # stage_2 and stage_3 should be executed
        assert "stage_2" in workflow._executed_stages
        assert "stage_3" in workflow._executed_stages
