"""
Unit tests for CheckpointService (Fase 24.6 - Restartable Workflows).

Tests cover:
- Checkpoint creation and updates
- Loading checkpoints
- Error recording
- Resume preparation
- Status transitions
- Checkpoint listing

Author: Claude Code (Week 158)
Date: 2026-01-20
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.models.workflow_checkpoint import (
    WorkflowCheckpoint,
    CheckpointStatus,
    CheckpointStatusResponse,
)
from app.services.checkpoint_service import (
    CheckpointService,
    get_checkpoint_service,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh CheckpointService instance."""
    return CheckpointService()


@pytest.fixture
def sample_checkpoint():
    """Create a sample WorkflowCheckpoint."""
    now = datetime.now(timezone.utc)
    checkpoint = MagicMock(spec=WorkflowCheckpoint)
    checkpoint.id = str(uuid.uuid4())
    checkpoint.session_id = "session-123"
    checkpoint.workflow_type = "brown_paper"
    checkpoint.workflow_id = "workflow-abc"
    checkpoint.current_stage = "stage_2"
    checkpoint.completed_stages = ["stage_1", "stage_2"]
    checkpoint.stage_results = {
        "stage_1": {"output": "result_1"},
        "stage_2": {"output": "result_2"},
    }
    checkpoint.shared_data = {"key": "value"}
    checkpoint.input_data = {"input_key": "input_value"}
    checkpoint.checkpoint_metadata = {"meta": "data"}
    checkpoint.last_error = None
    checkpoint.error_stage = None
    checkpoint.error_context = None
    checkpoint.retry_count = 0
    checkpoint.checkpoint_version = 2
    checkpoint.status = CheckpointStatus.RUNNING.value
    checkpoint.created_at = now
    checkpoint.updated_at = now
    checkpoint.started_at = now
    checkpoint.last_checkpoint_at = now
    checkpoint.can_resume = True
    checkpoint.resume_stage = "stage_3"
    checkpoint.stages_completed_count = 2
    checkpoint.has_error = False
    return checkpoint


@pytest.fixture
def failed_checkpoint():
    """Create a failed WorkflowCheckpoint."""
    now = datetime.now(timezone.utc)
    checkpoint = MagicMock(spec=WorkflowCheckpoint)
    checkpoint.id = str(uuid.uuid4())
    checkpoint.session_id = "session-456"
    checkpoint.workflow_type = "migration"
    checkpoint.workflow_id = "workflow-def"
    checkpoint.current_stage = "stage_3"
    checkpoint.completed_stages = ["stage_1", "stage_2"]
    checkpoint.stage_results = {
        "stage_1": {"output": "result_1"},
        "stage_2": {"output": "result_2"},
    }
    checkpoint.shared_data = {"key": "value"}
    checkpoint.input_data = {}
    checkpoint.metadata = {}
    checkpoint.last_error = "Connection timeout"
    checkpoint.error_stage = "stage_3"
    checkpoint.error_context = {"timeout": 30}
    checkpoint.retry_count = 2
    checkpoint.checkpoint_version = 3
    checkpoint.status = CheckpointStatus.FAILED.value
    checkpoint.created_at = now
    checkpoint.updated_at = now
    checkpoint.started_at = now
    checkpoint.last_checkpoint_at = now
    checkpoint.can_resume = True
    checkpoint.resume_stage = "stage_3"
    checkpoint.stages_completed_count = 2
    checkpoint.has_error = True
    return checkpoint


# ==================== Model Property Tests ====================

class TestCheckpointModel:
    """Tests for WorkflowCheckpoint model properties."""

    def test_can_resume_running(self):
        """Test can_resume is True for running status."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.status = CheckpointStatus.RUNNING.value
        assert checkpoint.can_resume is True

    def test_can_resume_failed(self):
        """Test can_resume is True for failed status."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.status = CheckpointStatus.FAILED.value
        assert checkpoint.can_resume is True

    def test_can_resume_completed(self):
        """Test can_resume is False for completed status."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.status = CheckpointStatus.COMPLETED.value
        assert checkpoint.can_resume is False

    def test_can_resume_cancelled(self):
        """Test can_resume is False for cancelled status."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.status = CheckpointStatus.CANCELLED.value
        assert checkpoint.can_resume is False

    def test_resume_stage_from_error(self):
        """Test resume_stage returns error_stage when failed."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.status = CheckpointStatus.FAILED.value
        checkpoint.error_stage = "failed_stage"
        checkpoint.current_stage = "some_stage"
        assert checkpoint.resume_stage == "failed_stage"

    def test_resume_stage_from_current(self):
        """Test resume_stage returns current_stage when not failed."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.status = CheckpointStatus.RUNNING.value
        checkpoint.current_stage = "current_stage"
        assert checkpoint.resume_stage == "current_stage"

    def test_stages_completed_count(self):
        """Test stages_completed_count returns correct count."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.completed_stages = ["stage_1", "stage_2", "stage_3"]
        assert checkpoint.stages_completed_count == 3

    def test_stages_completed_count_empty(self):
        """Test stages_completed_count returns 0 for empty list."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.completed_stages = []
        assert checkpoint.stages_completed_count == 0

    def test_stages_completed_count_none(self):
        """Test stages_completed_count returns 0 for None."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.completed_stages = None
        assert checkpoint.stages_completed_count == 0

    def test_has_error_true(self):
        """Test has_error returns True when error exists."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.last_error = "Some error"
        assert checkpoint.has_error is True

    def test_has_error_false(self):
        """Test has_error returns False when no error."""
        checkpoint = WorkflowCheckpoint()
        checkpoint.last_error = None
        assert checkpoint.has_error is False

    def test_to_dict(self):
        """Test to_dict returns correct dictionary."""
        now = datetime.now(timezone.utc)
        checkpoint = WorkflowCheckpoint()
        checkpoint.id = "test-id"
        checkpoint.session_id = "session-id"
        checkpoint.workflow_type = "brown_paper"
        checkpoint.workflow_id = "workflow-id"
        checkpoint.current_stage = "stage_1"
        checkpoint.completed_stages = ["stage_1"]
        checkpoint.stage_results = {"stage_1": {"data": "value"}}
        checkpoint.shared_data = {"shared": "data"}
        checkpoint.input_data = {"input": "data"}
        checkpoint.checkpoint_metadata = {"meta": "data"}
        checkpoint.last_error = None
        checkpoint.error_stage = None
        checkpoint.error_context = None
        checkpoint.retry_count = 0
        checkpoint.checkpoint_version = 1
        checkpoint.status = CheckpointStatus.RUNNING.value
        checkpoint.created_at = now
        checkpoint.updated_at = now
        checkpoint.started_at = now
        checkpoint.last_checkpoint_at = now

        result = checkpoint.to_dict()

        assert result["id"] == "test-id"
        assert result["session_id"] == "session-id"
        assert result["workflow_type"] == "brown_paper"
        assert result["can_resume"] is True
        assert result["stages_completed_count"] == 1
        assert result["has_error"] is False


# ==================== Service Tests ====================

class TestCheckpointService:
    """Tests for CheckpointService methods."""

    @pytest.mark.asyncio
    async def test_restore_context(self, service, sample_checkpoint):
        """Test restore_context returns correct context dictionary."""
        context = await service.restore_context(sample_checkpoint)

        assert context["workflow_id"] == sample_checkpoint.workflow_id
        assert context["workflow_type"] == sample_checkpoint.workflow_type
        assert context["session_id"] == sample_checkpoint.session_id
        assert context["current_stage"] == sample_checkpoint.current_stage
        assert context["completed_stages"] == sample_checkpoint.completed_stages
        assert context["stage_results"] == sample_checkpoint.stage_results
        assert context["shared_data"] == sample_checkpoint.shared_data
        assert context["input_data"] == sample_checkpoint.input_data
        assert context["metadata"] == sample_checkpoint.checkpoint_metadata

    @pytest.mark.asyncio
    async def test_restore_context_with_none_values(self, service):
        """Test restore_context handles None values gracefully."""
        checkpoint = MagicMock(spec=WorkflowCheckpoint)
        checkpoint.workflow_id = "wf-123"
        checkpoint.workflow_type = "test"
        checkpoint.session_id = "session-123"
        checkpoint.started_at = datetime.now(timezone.utc)
        checkpoint.current_stage = None
        checkpoint.completed_stages = None
        checkpoint.stage_results = None
        checkpoint.shared_data = None
        checkpoint.input_data = None
        checkpoint.checkpoint_metadata = None

        context = await service.restore_context(checkpoint)

        assert context["completed_stages"] == []
        assert context["stage_results"] == {}
        assert context["shared_data"] == {}
        assert context["input_data"] == {}
        assert context["metadata"] == {}


class TestCheckpointServiceWithMockedDB:
    """Tests for CheckpointService methods that require database mocking."""

    @pytest.mark.asyncio
    async def test_save_checkpoint_creates_new(self, service):
        """Test save_checkpoint creates a new checkpoint when none exists."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            checkpoint = await service.save_checkpoint(
                session_id="session-123",
                workflow_type="brown_paper",
                workflow_id="workflow-abc",
                current_stage="stage_1",
                completed_stages=["stage_1"],
                stage_result={"output": "result"},
                shared_data={"key": "value"},
                input_data={"input": "data"},
            )

            # Verify add was called (new checkpoint)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_checkpoint_updates_existing(self, service, sample_checkpoint):
        """Test save_checkpoint updates an existing checkpoint."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            await service.save_checkpoint(
                session_id="session-123",
                workflow_type="brown_paper",
                workflow_id="workflow-abc",
                current_stage="stage_3",
                completed_stages=["stage_1", "stage_2", "stage_3"],
                stage_result={"output": "result_3"},
                shared_data={"key": "updated_value"},
            )

            # Verify add was NOT called (existing checkpoint)
            mock_session.add.assert_not_called()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_checkpoint_found(self, service, sample_checkpoint):
        """Test load_checkpoint returns checkpoint when found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.load_checkpoint(
                session_id="session-123",
                workflow_type="brown_paper",
            )

            assert result == sample_checkpoint

    @pytest.mark.asyncio
    async def test_load_checkpoint_not_found(self, service):
        """Test load_checkpoint returns None when not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.load_checkpoint(
                session_id="session-123",
                workflow_type="brown_paper",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_record_error(self, service, sample_checkpoint):
        """Test record_error updates checkpoint with error information."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.record_error(
                session_id="session-123",
                workflow_type="brown_paper",
                workflow_id="workflow-abc",
                stage_name="stage_3",
                error="Connection timeout",
                error_context={"timeout": 30},
            )

            assert result == sample_checkpoint
            assert sample_checkpoint.last_error == "Connection timeout"
            assert sample_checkpoint.error_stage == "stage_3"
            assert sample_checkpoint.error_context == {"timeout": 30}
            assert sample_checkpoint.status == CheckpointStatus.FAILED.value
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_error_no_checkpoint(self, service):
        """Test record_error returns None when no checkpoint exists."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.record_error(
                session_id="session-123",
                workflow_type="brown_paper",
                workflow_id="workflow-abc",
                stage_name="stage_3",
                error="Some error",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_mark_completed(self, service, sample_checkpoint):
        """Test mark_completed updates checkpoint status."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.mark_completed(
                session_id="session-123",
                workflow_type="brown_paper",
                workflow_id="workflow-abc",
            )

            assert result == sample_checkpoint
            assert sample_checkpoint.status == CheckpointStatus.COMPLETED.value
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_cancelled(self, service, sample_checkpoint):
        """Test mark_cancelled updates checkpoint status."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.mark_cancelled(
                session_id="session-123",
                workflow_type="brown_paper",
                workflow_id="workflow-abc",
                reason="User cancelled",
            )

            assert result == sample_checkpoint
            assert sample_checkpoint.status == CheckpointStatus.CANCELLED.value
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_checkpoints(self, service):
        """Test clear_checkpoints deletes checkpoints."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            count = await service.clear_checkpoints(
                session_id="session-123",
                workflow_type="brown_paper",
            )

            assert count == 3
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, service, sample_checkpoint):
        """Test list_checkpoints returns list of checkpoints."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_checkpoint]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.list_checkpoints(
                session_id="session-123",
                workflow_type="brown_paper",
            )

            assert len(result) == 1
            assert result[0] == sample_checkpoint

    @pytest.mark.asyncio
    async def test_get_checkpoint_status(self, service, sample_checkpoint):
        """Test get_checkpoint_status returns status response."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.get_checkpoint_status("workflow-abc")

            assert isinstance(result, CheckpointStatusResponse)
            assert result.workflow_id == sample_checkpoint.workflow_id
            assert result.workflow_type == sample_checkpoint.workflow_type
            assert result.status == sample_checkpoint.status
            assert result.can_resume == sample_checkpoint.can_resume

    @pytest.mark.asyncio
    async def test_prepare_for_resume(self, service, failed_checkpoint):
        """Test prepare_for_resume clears error state."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = failed_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.prepare_for_resume(
                session_id="session-456",
                workflow_type="migration",
                workflow_id="workflow-def",
                skip_failed_stage=False,
            )

            assert result is not None
            assert failed_checkpoint.last_error is None
            assert failed_checkpoint.error_stage is None
            assert failed_checkpoint.status == CheckpointStatus.RUNNING.value
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_prepare_for_resume_skip_failed(self, service, failed_checkpoint):
        """Test prepare_for_resume with skip_failed_stage."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = failed_checkpoint
        mock_session.execute.return_value = mock_result

        with patch("app.services.checkpoint_service.AsyncSessionLocal") as mock_db:
            mock_db.return_value.__aenter__.return_value = mock_session

            result = await service.prepare_for_resume(
                session_id="session-456",
                workflow_type="migration",
                workflow_id="workflow-def",
                skip_failed_stage=True,
            )

            assert result is not None
            # Check error_stage was added to completed_stages
            assert "stage_3" in failed_checkpoint.completed_stages


class TestCheckpointStatusEnum:
    """Tests for CheckpointStatus enum."""

    def test_all_statuses_defined(self):
        """Test all expected statuses are defined."""
        assert CheckpointStatus.RUNNING.value == "running"
        assert CheckpointStatus.PAUSED.value == "paused"
        assert CheckpointStatus.COMPLETED.value == "completed"
        assert CheckpointStatus.FAILED.value == "failed"
        assert CheckpointStatus.CANCELLED.value == "cancelled"


class TestGetCheckpointService:
    """Tests for singleton getter."""

    def test_get_checkpoint_service_singleton(self):
        """Test get_checkpoint_service returns same instance."""
        # Reset singleton
        import app.services.checkpoint_service as module
        module._checkpoint_service = None

        service1 = get_checkpoint_service()
        service2 = get_checkpoint_service()

        assert service1 is service2
        assert isinstance(service1, CheckpointService)
