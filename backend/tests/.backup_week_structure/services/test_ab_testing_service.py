"""
Unit tests for A/B Testing Service

Tests experiment lifecycle, traffic allocation, and statistical analysis.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.ab_testing_service import ABTestingService
from app.models.ab_testing import Experiment, ExperimentVariant, ExperimentResult


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def ab_service(mock_db_session):
    """Create ABTestingService instance with mocked DB."""
    return ABTestingService(mock_db_session)


class TestExperimentCreation:
    """Test experiment creation and validation."""

    @pytest.mark.asyncio
    async def test_create_experiment_success(self, ab_service, mock_db_session):
        """Test successful experiment creation."""
        # Mock experiment creation
        experiment_id = uuid4()
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.agent_id = "felix"
        mock_experiment.feature_name = "test_feature"
        mock_experiment.status = "DRAFT"
        mock_experiment.variants = []

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one=lambda: mock_experiment
        ))

        variants = [
            {
                "variant_name": "control",
                "traffic_percentage": 50.0,
                "config_json": {"mode": "sync"},
                "is_control": True
            },
            {
                "variant_name": "async_variant",
                "traffic_percentage": 50.0,
                "config_json": {"mode": "async"},
                "is_control": False
            }
        ]

        experiment = await ab_service.create_experiment(
            agent_id="felix",
            feature_name="test_feature",
            description="Test experiment",
            variants=variants
        )

        assert experiment is not None
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_create_experiment_invalid_traffic(self, ab_service):
        """Test experiment creation fails with invalid traffic allocation."""
        variants = [
            {
                "variant_name": "control",
                "traffic_percentage": 40.0,  # Only 90% total
                "config_json": {},
                "is_control": True
            },
            {
                "variant_name": "variant_a",
                "traffic_percentage": 50.0,
                "config_json": {},
                "is_control": False
            }
        ]

        with pytest.raises(ValueError, match="must sum to 100"):
            await ab_service.create_experiment(
                agent_id="felix",
                feature_name="test",
                description=None,
                variants=variants
            )

    @pytest.mark.asyncio
    async def test_create_experiment_no_control(self, ab_service):
        """Test experiment creation fails without control variant."""
        variants = [
            {
                "variant_name": "variant_a",
                "traffic_percentage": 50.0,
                "config_json": {},
                "is_control": False
            },
            {
                "variant_name": "variant_b",
                "traffic_percentage": 50.0,
                "config_json": {},
                "is_control": False
            }
        ]

        with pytest.raises(ValueError, match="Exactly one control variant required"):
            await ab_service.create_experiment(
                agent_id="felix",
                feature_name="test",
                description=None,
                variants=variants
            )

    @pytest.mark.asyncio
    async def test_create_experiment_multiple_controls(self, ab_service):
        """Test experiment creation fails with multiple control variants."""
        variants = [
            {
                "variant_name": "control_a",
                "traffic_percentage": 50.0,
                "config_json": {},
                "is_control": True
            },
            {
                "variant_name": "control_b",
                "traffic_percentage": 50.0,
                "config_json": {},
                "is_control": True
            }
        ]

        with pytest.raises(ValueError, match="Exactly one control variant required"):
            await ab_service.create_experiment(
                agent_id="felix",
                feature_name="test",
                description=None,
                variants=variants
            )


class TestExperimentLifecycle:
    """Test experiment status transitions."""

    @pytest.mark.asyncio
    async def test_start_experiment(self, ab_service, mock_db_session):
        """Test starting an experiment."""
        experiment_id = uuid4()
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.status = "DRAFT"

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=lambda: mock_experiment
        ))

        experiment = await ab_service.start_experiment(experiment_id)

        assert mock_experiment.status == "ACTIVE"
        assert mock_experiment.started_at is not None
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_start_experiment_invalid_status(self, ab_service, mock_db_session):
        """Test starting non-DRAFT experiment fails."""
        experiment_id = uuid4()
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.status = "ACTIVE"  # Already active

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=lambda: mock_experiment
        ))

        with pytest.raises(ValueError, match="Can only start DRAFT experiments"):
            await ab_service.start_experiment(experiment_id)

    @pytest.mark.asyncio
    async def test_pause_experiment(self, ab_service, mock_db_session):
        """Test pausing an active experiment."""
        experiment_id = uuid4()
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.status = "ACTIVE"

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=lambda: mock_experiment
        ))

        experiment = await ab_service.pause_experiment(experiment_id)

        assert mock_experiment.status == "PAUSED"
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_complete_experiment(self, ab_service, mock_db_session):
        """Test completing an experiment with winner."""
        experiment_id = uuid4()
        winner_variant_id = uuid4()

        mock_variant = MagicMock(spec=ExperimentVariant)
        mock_variant.id = winner_variant_id

        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.status = "ACTIVE"
        mock_experiment.variants = [mock_variant]

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=lambda: mock_experiment
        ))

        experiment = await ab_service.complete_experiment(
            experiment_id=experiment_id,
            winner_variant_id=winner_variant_id
        )

        assert mock_experiment.status == "COMPLETED"
        assert mock_experiment.completed_at is not None
        assert mock_experiment.winner_variant_id == winner_variant_id
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_complete_experiment_invalid_winner(self, ab_service, mock_db_session):
        """Test completing experiment with invalid winner fails."""
        experiment_id = uuid4()
        winner_variant_id = uuid4()
        other_variant_id = uuid4()

        mock_variant = MagicMock(spec=ExperimentVariant)
        mock_variant.id = other_variant_id  # Different ID

        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.status = "ACTIVE"
        mock_experiment.variants = [mock_variant]

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=lambda: mock_experiment
        ))

        with pytest.raises(ValueError, match="Winner variant .* not in experiment"):
            await ab_service.complete_experiment(
                experiment_id=experiment_id,
                winner_variant_id=winner_variant_id
            )


class TestTrafficAllocation:
    """Test traffic allocation logic."""

    @pytest.mark.asyncio
    async def test_allocate_traffic_sticky_assignment(self, ab_service, mock_db_session):
        """Test that same task always gets same variant."""
        experiment_id = uuid4()
        task_id = "task_12345"

        variant_a = MagicMock(spec=ExperimentVariant)
        variant_a.id = uuid4()
        variant_a.variant_name = "control"
        variant_a.traffic_percentage = 50.0

        variant_b = MagicMock(spec=ExperimentVariant)
        variant_b.id = uuid4()
        variant_b.variant_name = "variant_a"
        variant_b.traffic_percentage = 50.0

        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.status = "ACTIVE"
        mock_experiment.variants = [variant_a, variant_b]

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=lambda: mock_experiment
        ))

        # Allocate same task multiple times
        variant_1 = await ab_service.allocate_traffic(experiment_id, task_id)
        variant_2 = await ab_service.allocate_traffic(experiment_id, task_id)
        variant_3 = await ab_service.allocate_traffic(experiment_id, task_id)

        # Should always get same variant (sticky)
        assert variant_1.id == variant_2.id
        assert variant_2.id == variant_3.id

    @pytest.mark.asyncio
    async def test_allocate_traffic_distribution(self, ab_service, mock_db_session):
        """Test traffic allocation respects percentages (roughly)."""
        experiment_id = uuid4()

        variant_a = MagicMock(spec=ExperimentVariant)
        variant_a.id = uuid4()
        variant_a.variant_name = "control"
        variant_a.traffic_percentage = 30.0

        variant_b = MagicMock(spec=ExperimentVariant)
        variant_b.id = uuid4()
        variant_b.variant_name = "variant_a"
        variant_b.traffic_percentage = 70.0

        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = experiment_id
        mock_experiment.status = "ACTIVE"
        mock_experiment.variants = [variant_a, variant_b]

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=lambda: mock_experiment
        ))

        # Allocate 100 different tasks
        allocations = {}
        for i in range(100):
            task_id = f"task_{i}"
            variant = await ab_service.allocate_traffic(experiment_id, task_id)
            variant_name = variant.variant_name
            allocations[variant_name] = allocations.get(variant_name, 0) + 1

        # Should be roughly 30/70 split (allow ±15% variance)
        control_pct = (allocations.get("control", 0) / 100) * 100
        variant_pct = (allocations.get("variant_a", 0) / 100) * 100

        assert 15 <= control_pct <= 45  # 30% ± 15%
        assert 55 <= variant_pct <= 85  # 70% ± 15%


class TestStatisticalAnalysis:
    """Test statistical analysis methods."""

    def test_confidence_interval_calculation(self, ab_service):
        """Test confidence interval calculation."""
        # 50% success rate, 100 samples
        lower, upper = ab_service._calculate_confidence_interval(0.5, 100, 0.95)

        # Should be roughly 0.5 ± 0.098
        assert 0.40 <= lower <= 0.45
        assert 0.55 <= upper <= 0.60

    def test_confidence_interval_high_success(self, ab_service):
        """Test confidence interval with high success rate."""
        # 95% success rate, 100 samples
        lower, upper = ab_service._calculate_confidence_interval(0.95, 100, 0.95)

        assert 0.90 <= lower <= 0.95
        assert upper <= 1.0

    def test_p_value_calculation_significant(self, ab_service):
        """Test p-value calculation with significant difference."""
        # Control: 50% success (n=100)
        # Variant: 70% success (n=100)
        p_value = ab_service._calculate_p_value(0.5, 100, 0.7, 100)

        # Should be significant (p < 0.05)
        assert p_value < 0.05

    def test_p_value_calculation_not_significant(self, ab_service):
        """Test p-value calculation with no significant difference."""
        # Control: 50% success (n=100)
        # Variant: 52% success (n=100)
        p_value = ab_service._calculate_p_value(0.5, 100, 0.52, 100)

        # Should not be significant (p > 0.05)
        assert p_value > 0.05

    def test_normal_cdf(self, ab_service):
        """Test normal CDF approximation."""
        # Test known values
        assert abs(ab_service._normal_cdf(0) - 0.5) < 0.01
        assert abs(ab_service._normal_cdf(1.96) - 0.975) < 0.01
        assert abs(ab_service._normal_cdf(-1.96) - 0.025) < 0.01


class TestResultLogging:
    """Test result logging functionality."""

    @pytest.mark.asyncio
    async def test_log_result_success(self, ab_service, mock_db_session):
        """Test logging successful result."""
        variant_id = uuid4()
        task_id = "task_123"
        metrics = {
            "success_rate": 0.95,
            "execution_time_ms": 1500,
            "code_quality_score": 8.5
        }

        result = await ab_service.log_result(
            variant_id=variant_id,
            task_id=task_id,
            success=True,
            metrics=metrics,
            work_type="NEW_FEATURE"
        )

        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_log_result_failure(self, ab_service, mock_db_session):
        """Test logging failed result with error."""
        variant_id = uuid4()
        task_id = "task_456"
        metrics = {"retry_count": 3}
        error_message = "Connection timeout"

        result = await ab_service.log_result(
            variant_id=variant_id,
            task_id=task_id,
            success=False,
            metrics=metrics,
            error_message=error_message
        )

        assert mock_db_session.add.called
        assert mock_db_session.commit.called
