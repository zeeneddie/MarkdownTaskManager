"""
Unit Tests for Gradual Rollout Service

Week 53: Continuous Evolution - Gradual Rollout System
Tests for safe deployment with automatic rollback.

Author: Claude Code (Week 53 Day 4)
Date: 2025-11-25
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.gradual_rollout_service import (
    GradualRolloutService,
    RolloutConfig,
    RolloutStatus,
    StageStatus,
    RollbackTrigger,
    HealthCheckResult,
    RolloutStatusReport
)
from app.models.gradual_rollout import Rollout, RolloutStage, RolloutMetric
from app.services.evolution_dashboard_service import (
    AgentPerformanceMetrics,
    TimeRange,
    TrendDirection,
    PerformanceLevel
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def rollout_config():
    """Create default rollout configuration."""
    return RolloutConfig(
        stages=[5.0, 25.0, 50.0, 100.0],
        stage_duration_minutes=60,
        max_performance_drop=10.0,
        max_error_rate=5.0,
        min_requests_per_stage=100,
        auto_advance=True,
        auto_rollback=True
    )


@pytest.fixture
def rollout_service(mock_db_session, rollout_config):
    """Create Gradual Rollout Service with mocked dependencies."""
    service = GradualRolloutService(mock_db_session, rollout_config)
    service.dashboard_service = AsyncMock()
    return service


@pytest.fixture
def sample_rollout():
    """Create sample rollout."""
    return Rollout(
        id=uuid4(),
        experiment_id=uuid4(),
        variant_id=uuid4(),
        agent_id="felix",
        feature_name="enhanced_validation",
        current_stage=0,
        current_percentage=5.0,
        status=RolloutStatus.ACTIVE.value,
        started_at=datetime.utcnow() - timedelta(hours=2),
        metadata={"config": {}}
    )


@pytest.fixture
def sample_stage():
    """Create sample rollout stage."""
    return RolloutStage(
        id=uuid4(),
        rollout_id=uuid4(),
        stage_number=0,
        traffic_percentage=5.0,
        status=StageStatus.ACTIVE.value,
        started_at=datetime.utcnow() - timedelta(hours=1),
        baseline_success_rate=80.0,
        total_requests=150,
        successful_requests=135,
        failed_requests=15
    )


@pytest.fixture
def sample_agent_metrics():
    """Create sample agent metrics."""
    return AgentPerformanceMetrics(
        agent_id="felix",
        agent_role="Feature Architect",
        total_tasks=100,
        successful_tasks=80,
        failed_tasks=20,
        success_rate=80.0,
        trend_direction=TrendDirection.STABLE,
        improvement_rate=0.0,
        learning_velocity=1.0,
        experiments_participated=5,
        experiments_won=3,
        win_rate=60.0,
        performance_level=PerformanceLevel.GOOD,
        avg_code_quality=85.0,
        avg_estimation_accuracy=80.0,
        daily_success_rates=[],
        time_range=TimeRange.SEVEN_DAYS
    )


# ============================================================================
# TESTS: ROLLOUT INITIATION
# ============================================================================

@pytest.mark.asyncio
async def test_start_rollout(rollout_service):
    """Test starting a new rollout."""
    # Mock database operations
    rollout_service.db.add = Mock()
    rollout_service.db.flush = AsyncMock()
    rollout_service.db.commit = AsyncMock()
    rollout_service.db.refresh = AsyncMock()

    # Mock dashboard service
    rollout_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=Mock(success_rate=80.0)
    )

    # Mock _start_stage
    with patch.object(rollout_service, '_start_stage', new=AsyncMock()) as mock_start:
        rollout = await rollout_service.start_rollout(
            experiment_id=uuid4(),
            variant_id=uuid4(),
            agent_id="felix",
            feature_name="enhanced_validation"
        )

        assert rollout_service.db.add.called
        assert rollout_service.db.commit.called
        assert mock_start.called


@pytest.mark.asyncio
async def test_start_rollout_creates_stages(rollout_service, rollout_config):
    """Test that starting rollout creates all stages."""
    rollout_service.db.add = Mock()
    rollout_service.db.flush = AsyncMock()
    rollout_service.db.commit = AsyncMock()
    rollout_service.db.refresh = AsyncMock()

    rollout_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=Mock(success_rate=80.0)
    )

    with patch.object(rollout_service, '_start_stage', new=AsyncMock()):
        await rollout_service.start_rollout(
            experiment_id=uuid4(),
            variant_id=uuid4(),
            agent_id="felix",
            feature_name="test"
        )

        # Should create rollout + 4 stages (5 total calls to db.add)
        assert rollout_service.db.add.call_count == 5  # 1 rollout + 4 stages


# ============================================================================
# TESTS: STAGE ADVANCEMENT
# ============================================================================

@pytest.mark.asyncio
async def test_advance_to_next_stage_healthy(rollout_service, sample_rollout):
    """Test advancing to next stage when current stage is healthy."""
    # Mock database queries
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=sample_rollout)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)
    rollout_service.db.commit = AsyncMock()

    # Mock health check (healthy)
    health = HealthCheckResult(
        stage_id=uuid4(),
        is_healthy=True,
        success_rate=82.0,
        baseline_success_rate=80.0,
        performance_drop=0.0,
        error_rate=2.0,
        total_requests=150,
        recommendations=[],
        should_rollback=False,
        rollback_reason=None
    )

    with patch.object(rollout_service, 'check_rollout_health', return_value=health), \
         patch.object(rollout_service, '_start_stage', new=AsyncMock()) as mock_start:

        next_stage = await rollout_service.advance_to_next_stage(sample_rollout.id)

        assert mock_start.called
        assert rollout_service.db.commit.called


@pytest.mark.asyncio
async def test_advance_to_next_stage_unhealthy(rollout_service, sample_rollout):
    """Test that unhealthy stage prevents advancement."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=Mock(status=StageStatus.ACTIVE.value))
    rollout_service.db.execute = AsyncMock(return_value=mock_result)

    # Mock health check (unhealthy)
    health = HealthCheckResult(
        stage_id=uuid4(),
        is_healthy=False,
        success_rate=65.0,
        baseline_success_rate=80.0,
        performance_drop=15.0,
        error_rate=8.0,
        total_requests=150,
        recommendations=["Performance dropped"],
        should_rollback=False,
        rollback_reason=None
    )

    with patch.object(rollout_service, 'check_rollout_health', return_value=health):
        next_stage = await rollout_service.advance_to_next_stage(sample_rollout.id)

        assert next_stage is None


@pytest.mark.asyncio
async def test_advance_triggers_rollback_on_failure(rollout_service, sample_rollout):
    """Test that critical failure triggers rollback."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=Mock(status=StageStatus.ACTIVE.value))
    rollout_service.db.execute = AsyncMock(return_value=mock_result)

    # Mock health check (should rollback)
    health = HealthCheckResult(
        stage_id=uuid4(),
        is_healthy=False,
        success_rate=60.0,
        baseline_success_rate=80.0,
        performance_drop=20.0,
        error_rate=12.0,
        total_requests=150,
        recommendations=["Critical failure"],
        should_rollback=True,
        rollback_reason="Performance drop: 20.0%"
    )

    with patch.object(rollout_service, 'check_rollout_health', return_value=health), \
         patch.object(rollout_service, 'trigger_rollback', new=AsyncMock()) as mock_rollback:

        next_stage = await rollout_service.advance_to_next_stage(sample_rollout.id)

        assert mock_rollback.called
        assert next_stage is None


# ============================================================================
# TESTS: HEALTH MONITORING
# ============================================================================

@pytest.mark.asyncio
async def test_check_rollout_health_healthy(rollout_service, sample_rollout, sample_stage, sample_agent_metrics):
    """Test health check with healthy stage."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=sample_stage)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)
    rollout_service.db.commit = AsyncMock()

    # Mock current metrics (healthy - 82% success)
    healthy_metrics = Mock(spec=AgentPerformanceMetrics)
    healthy_metrics.success_rate = 82.0
    rollout_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=healthy_metrics
    )

    health = await rollout_service.check_rollout_health(sample_rollout.id)

    assert isinstance(health, HealthCheckResult)
    assert health.is_healthy is True
    assert health.should_rollback is False
    assert health.performance_drop < 10.0  # Within threshold


@pytest.mark.asyncio
async def test_check_rollout_health_performance_drop(rollout_service, sample_rollout, sample_stage):
    """Test health check with performance degradation."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=sample_stage)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)
    rollout_service.db.commit = AsyncMock()

    # Mock degraded metrics (65% success, down from 80%)
    degraded_metrics = Mock(spec=AgentPerformanceMetrics)
    degraded_metrics.success_rate = 65.0
    rollout_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=degraded_metrics
    )

    health = await rollout_service.check_rollout_health(sample_rollout.id)

    assert health.is_healthy is False
    assert health.should_rollback is True
    assert health.performance_drop == 15.0  # 80 - 65
    assert "Performance drop" in health.rollback_reason


@pytest.mark.asyncio
async def test_check_rollout_health_error_spike(rollout_service, sample_rollout):
    """Test health check with high error rate."""
    # Create stage with high error rate
    bad_stage = RolloutStage(
        id=uuid4(),
        rollout_id=sample_rollout.id,
        stage_number=0,
        traffic_percentage=5.0,
        status=StageStatus.ACTIVE.value,
        started_at=datetime.utcnow() - timedelta(hours=1),
        baseline_success_rate=80.0,
        total_requests=200,
        successful_requests=180,
        failed_requests=20  # 10% error rate
    )

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=bad_stage)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)
    rollout_service.db.commit = AsyncMock()

    rollout_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=Mock(success_rate=78.0)
    )

    health = await rollout_service.check_rollout_health(sample_rollout.id)

    assert health.should_rollback is True
    assert "Error rate" in health.rollback_reason
    assert health.error_rate == 10.0


# ============================================================================
# TESTS: ROLLBACK
# ============================================================================

@pytest.mark.asyncio
async def test_trigger_rollback(rollout_service, sample_rollout, sample_stage):
    """Test triggering manual rollback."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=sample_stage)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)
    rollout_service.db.commit = AsyncMock()
    rollout_service.db.refresh = AsyncMock()

    rollout = await rollout_service.trigger_rollback(
        sample_rollout.id,
        "Manual rollback for testing",
        RollbackTrigger.MANUAL
    )

    assert rollout.status == RolloutStatus.ROLLED_BACK.value
    assert rollout.rolled_back_at is not None
    assert rollout.current_percentage == 0.0
    assert "manual" in rollout.rollback_reason.lower()


@pytest.mark.asyncio
async def test_trigger_rollback_performance_drop(rollout_service, sample_rollout, sample_stage):
    """Test automatic rollback on performance drop."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    mock_result.scalar_one = Mock(return_value=sample_stage)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)
    rollout_service.db.commit = AsyncMock()
    rollout_service.db.refresh = AsyncMock()

    rollout = await rollout_service.trigger_rollback(
        sample_rollout.id,
        "Performance drop: 15.0%",
        RollbackTrigger.PERFORMANCE_DROP
    )

    assert rollout.status == RolloutStatus.ROLLED_BACK.value
    assert "performance_drop" in rollout.rollback_reason.lower()


# ============================================================================
# TESTS: STATUS & REPORTING
# ============================================================================

@pytest.mark.asyncio
async def test_get_rollout_status(rollout_service, sample_rollout):
    """Test getting comprehensive rollout status."""
    # Mock stages
    sample_rollout.stages = [
        Mock(status=StageStatus.COMPLETED.value),
        Mock(status=StageStatus.ACTIVE.value),
        Mock(status=StageStatus.PENDING.value),
        Mock(status=StageStatus.PENDING.value)
    ]

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_rollout)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)

    # Mock health check
    health = HealthCheckResult(
        stage_id=uuid4(),
        is_healthy=True,
        success_rate=82.0,
        baseline_success_rate=80.0,
        performance_drop=0.0,
        error_rate=2.0,
        total_requests=150,
        recommendations=[],
        should_rollback=False,
        rollback_reason=None
    )

    with patch.object(rollout_service, 'check_rollout_health', return_value=health):
        status = await rollout_service.get_rollout_status(sample_rollout.id)

        assert isinstance(status, RolloutStatusReport)
        assert status.rollout_id == sample_rollout.id
        assert status.status == RolloutStatus.ACTIVE
        assert status.total_stages == 4
        assert status.stages_completed == 1
        assert status.overall_health == "HEALTHY"
        assert status.can_advance is True


@pytest.mark.asyncio
async def test_get_rollout_status_completed(rollout_service):
    """Test status for completed rollout."""
    completed_rollout = Rollout(
        id=uuid4(),
        experiment_id=uuid4(),
        variant_id=uuid4(),
        agent_id="felix",
        feature_name="test",
        current_stage=3,
        current_percentage=100.0,
        status=RolloutStatus.COMPLETED.value,
        started_at=datetime.utcnow() - timedelta(hours=4),
        completed_at=datetime.utcnow(),
        metadata={}
    )

    completed_rollout.stages = [
        Mock(status=StageStatus.COMPLETED.value),
        Mock(status=StageStatus.COMPLETED.value),
        Mock(status=StageStatus.COMPLETED.value),
        Mock(status=StageStatus.COMPLETED.value)
    ]

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=completed_rollout)
    rollout_service.db.execute = AsyncMock(return_value=mock_result)

    status = await rollout_service.get_rollout_status(completed_rollout.id)

    assert status.status == RolloutStatus.COMPLETED
    assert status.overall_health == "COMPLETED"
    assert status.stages_completed == 4
    assert status.elapsed_time is not None


# ============================================================================
# TESTS: METRICS COLLECTION
# ============================================================================

@pytest.mark.asyncio
async def test_record_metric(rollout_service):
    """Test recording a rollout metric."""
    rollout_service.db.add = Mock()
    rollout_service.db.commit = AsyncMock()
    rollout_service.db.refresh = AsyncMock()

    stage_id = uuid4()
    metric = await rollout_service.record_metric(
        stage_id=stage_id,
        metric_name="success_rate",
        metric_value=85.0,
        threshold_value=75.0,
        metadata={"source": "health_check"}
    )

    assert rollout_service.db.add.called
    assert rollout_service.db.commit.called


@pytest.mark.asyncio
async def test_record_metric_threshold_breach(rollout_service):
    """Test recording metric with threshold breach."""
    rollout_service.db.add = Mock()
    rollout_service.db.commit = AsyncMock()
    rollout_service.db.refresh = AsyncMock()

    metric = await rollout_service.record_metric(
        stage_id=uuid4(),
        metric_name="error_rate",
        metric_value=8.0,
        threshold_value=5.0
    )

    # Check that threshold_breached was set correctly in the add() call
    added_metric = rollout_service.db.add.call_args[0][0]
    assert added_metric.threshold_breached is True


@pytest.mark.asyncio
async def test_get_stage_metrics(rollout_service):
    """Test getting metrics for a stage."""
    stage_id = uuid4()

    # Mock metrics
    mock_metrics = [
        Mock(metric_name="success_rate", metric_value=82.0),
        Mock(metric_name="error_rate", metric_value=3.0),
        Mock(metric_name="response_time", metric_value=150.0)
    ]

    mock_result = Mock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_metrics)))
    rollout_service.db.execute = AsyncMock(return_value=mock_result)

    metrics = await rollout_service.get_stage_metrics(stage_id)

    assert len(metrics) == 3
    assert metrics[0].metric_name == "success_rate"


# ============================================================================
# TESTS: CONFIGURATION
# ============================================================================

def test_rollout_config_defaults():
    """Test default rollout configuration."""
    config = RolloutConfig()

    assert config.stages == [5.0, 25.0, 50.0, 100.0]
    assert config.stage_duration_minutes == 60
    assert config.max_performance_drop == 10.0
    assert config.max_error_rate == 5.0
    assert config.auto_advance is True
    assert config.auto_rollback is True


def test_rollout_config_custom():
    """Test custom rollout configuration."""
    config = RolloutConfig(
        stages=[10.0, 50.0, 100.0],
        stage_duration_minutes=30,
        max_performance_drop=5.0,
        auto_advance=False
    )

    assert len(config.stages) == 3
    assert config.stage_duration_minutes == 30
    assert config.max_performance_drop == 5.0
    assert config.auto_advance is False


# ============================================================================
# TESTS: LIST OPERATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_list_active_rollouts(rollout_service):
    """Test listing active rollouts."""
    mock_rollouts = [
        Mock(id=uuid4(), agent_id="felix", status=RolloutStatus.ACTIVE.value),
        Mock(id=uuid4(), agent_id="marcus", status=RolloutStatus.ACTIVE.value)
    ]

    mock_result = Mock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_rollouts)))
    rollout_service.db.execute = AsyncMock(return_value=mock_result)

    rollouts = await rollout_service.list_active_rollouts()

    assert len(rollouts) == 2
    assert all(r.status == RolloutStatus.ACTIVE.value for r in rollouts)


@pytest.mark.asyncio
async def test_list_active_rollouts_filtered(rollout_service):
    """Test listing active rollouts filtered by agent."""
    mock_rollouts = [
        Mock(id=uuid4(), agent_id="felix", status=RolloutStatus.ACTIVE.value)
    ]

    mock_result = Mock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_rollouts)))
    rollout_service.db.execute = AsyncMock(return_value=mock_result)

    rollouts = await rollout_service.list_active_rollouts(agent_id="felix")

    assert len(rollouts) == 1
    assert rollouts[0].agent_id == "felix"
