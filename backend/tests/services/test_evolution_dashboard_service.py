"""
Unit Tests for Evolution Dashboard Service

Week 53: Continuous Evolution - Evolution Dashboard
Tests for performance metrics, trends, and experiment summaries.

Author: Claude Code (Week 53 Day 1)
Date: 2025-11-25
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.evolution_dashboard_service import (
    EvolutionDashboardService,
    DashboardOverview,
    AgentPerformanceMetrics,
    ExperimentSummary,
    TimeRange,
    TrendDirection,
    PerformanceLevel
)
from app.models.ab_testing import Experiment, ExperimentVariant, ExperimentResult
from app.services.experience_store_service import Experience, Outcome, AgentRole, WorkType


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_experience_store():
    """Mock experience store service."""
    with patch('app.services.evolution_dashboard_service.ExperienceStoreService') as mock:
        instance = mock.return_value
        instance.get_agent_experiences = AsyncMock(return_value=[])
        instance.count_experiences = AsyncMock(return_value=1000)
        instance.count_successful_patterns = AsyncMock(return_value=50)
        instance.count_failure_analyses = AsyncMock(return_value=20)
        yield instance


@pytest.fixture
def evolution_service(mock_db_session, mock_experience_store):
    """Create Evolution Dashboard Service with mocked dependencies."""
    service = EvolutionDashboardService(mock_db_session)
    service.experience_store = mock_experience_store
    return service


@pytest.fixture
def sample_experiences():
    """Create sample experience data."""
    now = datetime.utcnow()
    experiences = []

    for i in range(100):
        exp = Experience(
            id=str(uuid4()),
            agent_id="felix",
            agent_role=AgentRole.FEATURE_ARCHITECT,
            work_type=WorkType.NEW_FEATURE,
            task_description=f"Task {i}",
            approach="Approach",
            outcome=Outcome.SUCCESS if i < 85 else Outcome.FAILURE,  # 85% success
            duration_seconds=300,
            timestamp=now - timedelta(days=i // 3),  # Spread over ~30 days
            key_decisions=[],
            learnings=[],
            patterns_used=[],
            complexity="medium",
            confidence=0.85
        )
        experiences.append(exp)

    return experiences


@pytest.fixture
def sample_experiment():
    """Create sample experiment."""
    exp_id = uuid4()
    now = datetime.utcnow()

    experiment = Experiment(
        id=exp_id,
        agent_id="felix",
        feature_name="enhanced_validation",
        description="Testing enhanced validation approach",
        status="COMPLETED",
        created_at=now - timedelta(days=10),
        started_at=now - timedelta(days=9),
        completed_at=now - timedelta(days=2),
        winner_variant_id=uuid4(),
        extra_metadata={}
    )

    # Create control variant
    control_variant = ExperimentVariant(
        id=uuid4(),
        experiment_id=exp_id,
        variant_name="control",
        description="Baseline approach",
        traffic_percentage=50.0,
        config_json={"timeout": 30},
        is_control=True
    )

    # Create treatment variant
    treatment_variant = ExperimentVariant(
        id=uuid4(),
        experiment_id=exp_id,
        variant_name="enhanced",
        description="Enhanced validation",
        traffic_percentage=50.0,
        config_json={"timeout": 30, "enhanced": True},
        is_control=False
    )

    experiment.variants = [control_variant, treatment_variant]
    experiment.winner_variant_id = treatment_variant.id

    return experiment


# ============================================================================
# TESTS: DASHBOARD OVERVIEW
# ============================================================================

@pytest.mark.asyncio
async def test_get_dashboard_overview_success(evolution_service, mock_db_session):
    """Test getting dashboard overview successfully."""
    # Mock experiment counts
    mock_db_session.execute = AsyncMock()
    mock_result = Mock()
    mock_result.scalar = Mock(side_effect=[25, 5, 18])  # total, active, completed
    mock_db_session.execute.return_value = mock_result

    # Mock agent metrics
    with patch.object(evolution_service, '_get_all_agent_metrics') as mock_agents:
        mock_agents.return_value = [
            Mock(
                success_rate=90.0,
                improvement_rate=12.0,
                trend_direction=TrendDirection.IMPROVING,
                agent_id="felix"
            ),
            Mock(
                success_rate=85.0,
                improvement_rate=5.0,
                trend_direction=TrendDirection.STABLE,
                agent_id="marcus"
            )
        ]

        overview = await evolution_service.get_dashboard_overview(TimeRange.THIRTY_DAYS)

        assert isinstance(overview, DashboardOverview)
        assert overview.total_experiments == 25
        assert overview.active_experiments == 5
        assert overview.completed_experiments == 18
        assert overview.total_agents == 2
        assert overview.improving_agents == 1
        assert overview.stable_agents == 1
        assert overview.avg_success_rate == 87.5
        assert overview.top_performer == "felix"


@pytest.mark.asyncio
async def test_get_dashboard_overview_no_experiments(evolution_service, mock_db_session):
    """Test dashboard overview with no experiments."""
    # Mock zero experiments
    mock_db_session.execute = AsyncMock()
    mock_result = Mock()
    mock_result.scalar = Mock(return_value=0)
    mock_db_session.execute.return_value = mock_result

    with patch.object(evolution_service, '_get_all_agent_metrics', return_value=[]):
        overview = await evolution_service.get_dashboard_overview(TimeRange.SEVEN_DAYS)

        assert overview.total_experiments == 0
        assert overview.active_experiments == 0
        assert overview.completed_experiments == 0
        assert overview.total_agents == 0
        assert overview.avg_success_rate == 0.0


# ============================================================================
# TESTS: AGENT PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_get_agent_performance_trends(evolution_service, sample_experiences):
    """Test getting performance trends for a specific agent."""
    # Mock experience store
    evolution_service.experience_store.get_agent_experiences = AsyncMock(
        return_value=sample_experiences
    )

    # Mock experiment counts
    with patch.object(evolution_service, '_count_agent_experiments', return_value=5), \
         patch.object(evolution_service, '_count_agent_wins', return_value=3), \
         patch.object(evolution_service, '_get_avg_quality_metric', return_value=88.5), \
         patch.object(evolution_service, '_calculate_trend', return_value=(TrendDirection.IMPROVING, 12.5)), \
         patch.object(evolution_service, '_calculate_learning_velocity', return_value=2.3), \
         patch.object(evolution_service, '_get_daily_success_rates', return_value=[("2025-11-25", 90.0)]):

        metrics = await evolution_service.get_agent_performance_trends("felix", TimeRange.THIRTY_DAYS)

        assert isinstance(metrics, AgentPerformanceMetrics)
        assert metrics.agent_id == "felix"
        assert metrics.agent_role == "Feature Architect"
        assert metrics.total_tasks == 100
        assert metrics.successful_tasks == 85
        assert metrics.failed_tasks == 15
        assert metrics.success_rate == 85.0
        assert metrics.trend_direction == TrendDirection.IMPROVING
        assert metrics.improvement_rate == 12.5
        assert metrics.learning_velocity == 2.3
        assert metrics.experiments_participated == 5
        assert metrics.experiments_won == 3
        assert metrics.win_rate == 60.0
        assert metrics.performance_level == PerformanceLevel.GOOD


@pytest.mark.asyncio
async def test_get_agent_performance_no_data(evolution_service):
    """Test agent performance with no data."""
    evolution_service.experience_store.get_agent_experiences = AsyncMock(return_value=[])

    with patch.object(evolution_service, '_count_agent_experiments', return_value=0), \
         patch.object(evolution_service, '_count_agent_wins', return_value=0), \
         patch.object(evolution_service, '_get_avg_quality_metric', return_value=None), \
         patch.object(evolution_service, '_calculate_trend', return_value=(TrendDirection.INSUFFICIENT_DATA, 0.0)), \
         patch.object(evolution_service, '_calculate_learning_velocity', return_value=0.0), \
         patch.object(evolution_service, '_get_daily_success_rates', return_value=[]):

        metrics = await evolution_service.get_agent_performance_trends("marcus", TimeRange.THIRTY_DAYS)

        assert metrics.total_tasks == 0
        assert metrics.success_rate == 0.0
        assert metrics.trend_direction == TrendDirection.INSUFFICIENT_DATA
        assert metrics.performance_level == PerformanceLevel.CRITICAL


# ============================================================================
# TESTS: EXPERIMENT SUMMARIES
# ============================================================================

@pytest.mark.asyncio
async def test_get_experiment_summary(evolution_service, sample_experiment, mock_db_session):
    """Test getting experiment summary."""
    # Mock database query
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_experiment)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with patch.object(evolution_service, '_count_experiment_trials', return_value=200), \
         patch.object(evolution_service, '_get_variant_success_rate', side_effect=[80.0, 92.0]), \
         patch.object(evolution_service, '_calculate_experiment_improvement', return_value=15.0):

        summary = await evolution_service.get_experiment_summary(str(sample_experiment.id))

        assert isinstance(summary, ExperimentSummary)
        assert summary.agent_id == "felix"
        assert summary.feature_name == "enhanced_validation"
        assert summary.status == "COMPLETED"
        assert summary.variant_count == 2
        assert summary.control_variant == "control"
        assert summary.winner_variant == "enhanced"
        assert summary.total_trials == 200
        assert summary.control_success_rate == 80.0
        assert summary.treatment_success_rate == 92.0
        assert summary.improvement_percentage == 15.0


@pytest.mark.asyncio
async def test_get_experiment_summary_not_found(evolution_service, mock_db_session):
    """Test getting experiment summary for non-existent experiment."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    summary = await evolution_service.get_experiment_summary("non-existent-id")

    assert summary is None


# ============================================================================
# TESTS: TREND CALCULATION
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_trend_improving(evolution_service, sample_experiences):
    """Test trend calculation showing improvement."""
    # Mock experiences showing improvement over time
    now = datetime.utcnow()
    recent_experiences = [
        Mock(outcome=Outcome.SUCCESS) for _ in range(9)
    ] + [Mock(outcome=Outcome.FAILURE)]  # 90% success

    earlier_experiences = [
        Mock(outcome=Outcome.SUCCESS) for _ in range(8)
    ] + [Mock(outcome=Outcome.FAILURE) for _ in range(2)]  # 80% success

    evolution_service.experience_store.get_agent_experiences = AsyncMock(
        side_effect=[recent_experiences, earlier_experiences]
    )

    trend, improvement = await evolution_service._calculate_trend("felix", now - timedelta(days=30))

    assert trend == TrendDirection.IMPROVING
    assert improvement > 0


@pytest.mark.asyncio
async def test_calculate_trend_insufficient_data(evolution_service):
    """Test trend calculation with insufficient data."""
    evolution_service.experience_store.get_agent_experiences = AsyncMock(
        return_value=[Mock(outcome=Outcome.SUCCESS) for _ in range(3)]  # Too few
    )

    trend, improvement = await evolution_service._calculate_trend(
        "felix",
        datetime.utcnow() - timedelta(days=30)
    )

    assert trend == TrendDirection.INSUFFICIENT_DATA
    assert improvement == 0.0


# ============================================================================
# TESTS: PERFORMANCE CLASSIFICATION
# ============================================================================

def test_classify_performance_excellent(evolution_service):
    """Test performance classification for excellent performance."""
    level = evolution_service._classify_performance(95.0)
    assert level == PerformanceLevel.EXCELLENT


def test_classify_performance_good(evolution_service):
    """Test performance classification for good performance."""
    level = evolution_service._classify_performance(80.0)
    assert level == PerformanceLevel.GOOD


def test_classify_performance_average(evolution_service):
    """Test performance classification for average performance."""
    level = evolution_service._classify_performance(65.0)
    assert level == PerformanceLevel.AVERAGE


def test_classify_performance_poor(evolution_service):
    """Test performance classification for poor performance."""
    level = evolution_service._classify_performance(50.0)
    assert level == PerformanceLevel.POOR


def test_classify_performance_critical(evolution_service):
    """Test performance classification for critical performance."""
    level = evolution_service._classify_performance(30.0)
    assert level == PerformanceLevel.CRITICAL


# ============================================================================
# TESTS: HELPER METHODS
# ============================================================================

def test_get_cutoff_date_seven_days(evolution_service):
    """Test cutoff date calculation for 7 days."""
    cutoff = evolution_service._get_cutoff_date(TimeRange.SEVEN_DAYS)
    now = datetime.utcnow()
    expected = now - timedelta(days=7)

    assert abs((cutoff - expected).total_seconds()) < 5  # Within 5 seconds


def test_get_cutoff_date_all_time(evolution_service):
    """Test cutoff date calculation for all time."""
    cutoff = evolution_service._get_cutoff_date(TimeRange.ALL_TIME)

    assert cutoff.year == 2020


def test_get_agent_role(evolution_service):
    """Test agent role mapping."""
    assert evolution_service._get_agent_role("felix") == "Feature Architect"
    assert evolution_service._get_agent_role("marcus") == "Maintenance Specialist"
    assert evolution_service._get_agent_role("quinn") == "Quality Inspector"
    assert evolution_service._get_agent_role("unknown") == "unknown"
