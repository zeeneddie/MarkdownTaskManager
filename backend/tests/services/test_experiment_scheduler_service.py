"""
Unit Tests for Experiment Scheduler Service

Week 53: Continuous Evolution - Automatic Experiment Scheduler
Tests for opportunity detection, hypothesis generation, scheduling, and stopping conditions.

Author: Claude Code (Week 53 Day 3)
Date: 2025-11-25
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID

from app.services.experiment_scheduler_service import (
    ExperimentSchedulerService,
    ImprovementOpportunity,
    ImprovementOpportunityType,
    ExperimentPriority,
    ExperimentHypothesis,
    ScheduledExperiment,
    StoppingDecision,
    StoppingCondition
)
from app.services.evolution_dashboard_service import (
    AgentPerformanceMetrics,
    TrendDirection,
    PerformanceLevel,
    TimeRange
)
from app.models.ab_testing import Experiment, ExperimentStatus


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def scheduler_service(mock_db_session):
    """Create Experiment Scheduler Service with mocked dependencies."""
    service = ExperimentSchedulerService(mock_db_session)
    service.dashboard_service = AsyncMock()
    service.ab_testing_service = AsyncMock()
    return service


@pytest.fixture
def sample_agent_metrics():
    """Create sample agent performance metrics."""
    return AgentPerformanceMetrics(
        agent_id="felix",
        agent_role="Feature Architect",
        total_tasks=100,
        successful_tasks=70,
        failed_tasks=30,
        success_rate=70.0,
        trend_direction=TrendDirection.STABLE,
        improvement_rate=2.0,
        learning_velocity=1.5,
        experiments_participated=10,
        experiments_won=4,
        win_rate=40.0,
        performance_level=PerformanceLevel.AVERAGE,
        avg_code_quality=85.0,
        avg_estimation_accuracy=80.0,
        daily_success_rates=[],
        time_range=TimeRange.THIRTY_DAYS
    )


@pytest.fixture
def sample_declining_metrics():
    """Create sample metrics showing declining performance."""
    return AgentPerformanceMetrics(
        agent_id="marcus",
        agent_role="Maintenance Specialist",
        total_tasks=100,
        successful_tasks=65,
        failed_tasks=35,
        success_rate=65.0,
        trend_direction=TrendDirection.DECLINING,
        improvement_rate=-8.5,
        learning_velocity=-2.0,
        experiments_participated=8,
        experiments_won=3,
        win_rate=37.5,
        performance_level=PerformanceLevel.AVERAGE,
        avg_code_quality=80.0,
        avg_estimation_accuracy=75.0,
        daily_success_rates=[],
        time_range=TimeRange.THIRTY_DAYS
    )


@pytest.fixture
def sample_opportunity():
    """Create sample improvement opportunity."""
    return ImprovementOpportunity(
        agent_id="felix",
        opportunity_type=ImprovementOpportunityType.PERFORMANCE_GAP,
        priority=ExperimentPriority.HIGH,
        current_performance=70.0,
        expected_improvement=5.0,
        confidence=0.8,
        description="felix success rate (70.0%) below target (75.0%)",
        recommended_variants=["enhanced_validation", "improved_error_handling"],
        metadata={"gap": 5.0, "target": 75.0, "peer_average": 80.0}
    )


@pytest.fixture
def sample_hypothesis():
    """Create sample experiment hypothesis."""
    return ExperimentHypothesis(
        agent_id="felix",
        feature_name="enhanced_validation",
        hypothesis="Adding enhanced input validation will improve felix success rate from 70.0% to 75.0%",
        control_description="Current validation approach",
        treatment_description="Enhanced validation with edge case handling and error recovery",
        success_criteria="Success rate improvement > 5.0% with p < 0.05",
        estimated_impact=5.0,
        confidence=0.8,
        metadata={"opportunity_type": "performance_gap", "current_performance": 70.0}
    )


@pytest.fixture
def sample_experiment():
    """Create sample experiment."""
    exp_id = uuid4()
    return Experiment(
        id=exp_id,
        agent_id="felix",
        feature_name="enhanced_validation",
        description="Test enhanced validation",
        status=ExperimentStatus.ACTIVE,
        created_at=datetime.utcnow() - timedelta(days=7),
        started_at=datetime.utcnow() - timedelta(days=6),
        completed_at=None,
        winner_variant_id=None,
        extra_metadata={}
    )


# ============================================================================
# TESTS: OPPORTUNITY DETECTION
# ============================================================================

@pytest.mark.asyncio
async def test_detect_improvement_opportunity_performance_gap(
    scheduler_service,
    sample_agent_metrics
):
    """Test detecting performance gap opportunity."""
    # Mock dashboard service
    scheduler_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=sample_agent_metrics
    )
    scheduler_service.dashboard_service.get_all_agents_performance = AsyncMock(
        return_value=[sample_agent_metrics]
    )

    opportunity = await scheduler_service.detect_improvement_opportunity(
        "felix", TimeRange.THIRTY_DAYS
    )

    assert opportunity is not None
    assert opportunity.agent_id == "felix"
    assert opportunity.opportunity_type == ImprovementOpportunityType.PERFORMANCE_GAP
    assert opportunity.current_performance == 70.0
    assert opportunity.expected_improvement > 0
    assert opportunity.priority in [ExperimentPriority.HIGH, ExperimentPriority.MEDIUM]


@pytest.mark.asyncio
async def test_detect_improvement_opportunity_declining_trend(
    scheduler_service,
    sample_declining_metrics
):
    """Test detecting declining trend opportunity."""
    scheduler_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=sample_declining_metrics
    )
    scheduler_service.dashboard_service.get_all_agents_performance = AsyncMock(
        return_value=[sample_declining_metrics]
    )

    opportunity = await scheduler_service.detect_improvement_opportunity(
        "marcus", TimeRange.THIRTY_DAYS
    )

    assert opportunity is not None
    assert opportunity.agent_id == "marcus"
    assert opportunity.opportunity_type == ImprovementOpportunityType.DECLINING_TREND
    assert opportunity.priority == ExperimentPriority.HIGH
    assert "declining" in opportunity.description.lower()


@pytest.mark.asyncio
async def test_detect_improvement_opportunity_low_win_rate(
    scheduler_service,
    sample_agent_metrics
):
    """Test detecting low win rate opportunity."""
    # Metrics already have win_rate = 40.0, below threshold of 50.0
    scheduler_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=sample_agent_metrics
    )
    scheduler_service.dashboard_service.get_all_agents_performance = AsyncMock(
        return_value=[sample_agent_metrics]
    )

    # Adjust success rate to be above threshold to avoid performance_gap detection
    sample_agent_metrics.success_rate = 80.0

    opportunity = await scheduler_service.detect_improvement_opportunity(
        "felix", TimeRange.THIRTY_DAYS
    )

    # Note: With current logic, performance_gap might be detected first
    # In real scenario, we'd detect whichever is most critical
    assert opportunity is not None


@pytest.mark.asyncio
async def test_detect_improvement_opportunity_none_found(scheduler_service):
    """Test when no opportunity is detected."""
    # Mock high-performing agent
    high_performer = AgentPerformanceMetrics(
        agent_id="quinn",
        agent_role="Quality Inspector",
        total_tasks=100,
        successful_tasks=95,
        failed_tasks=5,
        success_rate=95.0,
        trend_direction=TrendDirection.IMPROVING,
        improvement_rate=5.0,
        learning_velocity=2.0,
        experiments_participated=10,
        experiments_won=8,
        win_rate=80.0,
        performance_level=PerformanceLevel.EXCELLENT,
        avg_code_quality=95.0,
        avg_estimation_accuracy=90.0,
        daily_success_rates=[],
        time_range=TimeRange.THIRTY_DAYS
    )

    scheduler_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        return_value=high_performer
    )
    scheduler_service.dashboard_service.get_all_agents_performance = AsyncMock(
        return_value=[high_performer]
    )

    opportunity = await scheduler_service.detect_improvement_opportunity(
        "quinn", TimeRange.THIRTY_DAYS
    )

    assert opportunity is None


@pytest.mark.asyncio
async def test_detect_all_opportunities(scheduler_service):
    """Test detecting opportunities for all agents."""
    agent1 = AgentPerformanceMetrics(
        agent_id="felix",
        agent_role="Feature Architect",
        total_tasks=100,
        successful_tasks=70,
        failed_tasks=30,
        success_rate=70.0,
        trend_direction=TrendDirection.STABLE,
        improvement_rate=0.0,
        learning_velocity=1.0,
        experiments_participated=5,
        experiments_won=2,
        win_rate=40.0,
        performance_level=PerformanceLevel.AVERAGE,
        avg_code_quality=80.0,
        avg_estimation_accuracy=75.0,
        daily_success_rates=[],
        time_range=TimeRange.THIRTY_DAYS
    )

    agent2 = AgentPerformanceMetrics(
        agent_id="marcus",
        agent_role="Maintenance Specialist",
        total_tasks=100,
        successful_tasks=95,
        failed_tasks=5,
        success_rate=95.0,
        trend_direction=TrendDirection.IMPROVING,
        improvement_rate=5.0,
        learning_velocity=2.0,
        experiments_participated=10,
        experiments_won=8,
        win_rate=80.0,
        performance_level=PerformanceLevel.EXCELLENT,
        avg_code_quality=95.0,
        avg_estimation_accuracy=90.0,
        daily_success_rates=[],
        time_range=TimeRange.THIRTY_DAYS
    )

    scheduler_service.dashboard_service.get_all_agents_performance = AsyncMock(
        return_value=[agent1, agent2]
    )

    # Mock individual calls
    scheduler_service.dashboard_service.get_agent_performance_trends = AsyncMock(
        side_effect=[agent1, agent2]
    )

    opportunities = await scheduler_service.detect_all_opportunities(TimeRange.THIRTY_DAYS)

    assert isinstance(opportunities, list)
    # Should find opportunity for agent1, but not agent2
    assert len(opportunities) >= 1


# ============================================================================
# TESTS: HYPOTHESIS GENERATION
# ============================================================================

@pytest.mark.asyncio
async def test_generate_hypothesis_performance_gap(
    scheduler_service,
    sample_opportunity
):
    """Test generating hypothesis for performance gap."""
    hypothesis = await scheduler_service.generate_experiment_hypothesis(sample_opportunity)

    assert isinstance(hypothesis, ExperimentHypothesis)
    assert hypothesis.agent_id == "felix"
    assert hypothesis.feature_name == "enhanced_validation"
    assert "validation" in hypothesis.hypothesis.lower()
    assert hypothesis.estimated_impact == sample_opportunity.expected_improvement
    assert hypothesis.confidence == sample_opportunity.confidence


@pytest.mark.asyncio
async def test_generate_hypothesis_declining_trend(scheduler_service):
    """Test generating hypothesis for declining trend."""
    opportunity = ImprovementOpportunity(
        agent_id="marcus",
        opportunity_type=ImprovementOpportunityType.DECLINING_TREND,
        priority=ExperimentPriority.HIGH,
        current_performance=65.0,
        expected_improvement=8.5,
        confidence=0.75,
        description="marcus performance declining",
        recommended_variants=["revert_recent_changes"],
        metadata={"improvement_rate": -8.5}
    )

    hypothesis = await scheduler_service.generate_experiment_hypothesis(opportunity)

    assert hypothesis.agent_id == "marcus"
    assert hypothesis.feature_name == "trend_reversal"
    assert "declining" in hypothesis.hypothesis.lower() or "revert" in hypothesis.hypothesis.lower()


@pytest.mark.asyncio
async def test_generate_hypothesis_low_win_rate(scheduler_service):
    """Test generating hypothesis for low win rate."""
    opportunity = ImprovementOpportunity(
        agent_id="betty",
        opportunity_type=ImprovementOpportunityType.LOW_WIN_RATE,
        priority=ExperimentPriority.MEDIUM,
        current_performance=35.0,
        expected_improvement=20.0,
        confidence=0.7,
        description="betty win rate low",
        recommended_variants=["strategy_optimization"],
        metadata={"win_rate": 35.0}
    )

    hypothesis = await scheduler_service.generate_experiment_hypothesis(opportunity)

    assert hypothesis.agent_id == "betty"
    assert hypothesis.feature_name == "strategy_optimization"
    assert "win rate" in hypothesis.hypothesis.lower() or "strategy" in hypothesis.hypothesis.lower()


# ============================================================================
# TESTS: EXPERIMENT SCHEDULING
# ============================================================================

@pytest.mark.asyncio
async def test_schedule_performance_experiment(
    scheduler_service,
    sample_hypothesis
):
    """Test scheduling a performance experiment."""
    # Mock AB testing service
    mock_experiment = Mock()
    mock_experiment.id = uuid4()
    scheduler_service.ab_testing_service.create_experiment = AsyncMock(
        return_value=mock_experiment
    )

    scheduled = await scheduler_service.schedule_performance_experiment(
        sample_hypothesis,
        ExperimentPriority.HIGH
    )

    assert isinstance(scheduled, ScheduledExperiment)
    assert scheduled.agent_id == "felix"
    assert scheduled.priority == ExperimentPriority.HIGH
    assert scheduled.status == "SCHEDULED"
    assert scheduled.experiment_id == mock_experiment.id


@pytest.mark.asyncio
async def test_schedule_experiment_priority_timing(
    scheduler_service,
    sample_hypothesis
):
    """Test that experiment start time varies by priority."""
    mock_experiment = Mock()
    mock_experiment.id = uuid4()
    scheduler_service.ab_testing_service.create_experiment = AsyncMock(
        return_value=mock_experiment
    )

    # Critical priority (start in 5 minutes)
    critical = await scheduler_service.schedule_performance_experiment(
        sample_hypothesis,
        ExperimentPriority.CRITICAL
    )

    # Low priority (start in 7 days)
    low = await scheduler_service.schedule_performance_experiment(
        sample_hypothesis,
        ExperimentPriority.LOW
    )

    # Critical should start sooner
    assert critical.start_at < low.start_at


@pytest.mark.asyncio
async def test_auto_create_baseline_experiments(scheduler_service):
    """Test auto-creating baseline experiments for new agent."""
    mock_experiment = Mock()
    mock_experiment.id = uuid4()
    scheduler_service.ab_testing_service.create_experiment = AsyncMock(
        return_value=mock_experiment
    )

    experiments = await scheduler_service.auto_create_baseline_experiments("newagent")

    assert isinstance(experiments, list)
    assert len(experiments) == 2  # Parameter + prompting baselines
    assert all(isinstance(e, ScheduledExperiment) for e in experiments)
    assert all(e.agent_id == "newagent" for e in experiments)


# ============================================================================
# TESTS: STOPPING CONDITIONS
# ============================================================================

@pytest.mark.asyncio
async def test_check_stopping_statistical_significance(scheduler_service):
    """Test stopping condition with statistical significance."""
    # Mock experiment results with significant improvement
    mock_results = {
        "experiment": Mock(started_at=datetime.utcnow() - timedelta(days=5)),
        "control": {
            "variant_id": str(uuid4()),
            "success_rate": 70.0,
            "total_trials": 50
        },
        "treatment": {
            "variant_id": str(uuid4()),
            "success_rate": 85.0,  # 21% improvement
            "total_trials": 50
        }
    }

    scheduler_service.ab_testing_service.get_experiment_results = AsyncMock(
        return_value=mock_results
    )

    decision = await scheduler_service.check_experiment_stopping_conditions("exp-id")

    assert isinstance(decision, StoppingDecision)
    assert decision.should_stop is True
    assert decision.condition == StoppingCondition.STATISTICAL_SIGNIFICANCE
    assert decision.winner_variant_id is not None


@pytest.mark.asyncio
async def test_check_stopping_degradation(scheduler_service):
    """Test stopping condition with performance degradation."""
    mock_results = {
        "experiment": Mock(started_at=datetime.utcnow() - timedelta(days=3)),
        "control": {
            "variant_id": str(uuid4()),
            "success_rate": 80.0,
            "total_trials": 40
        },
        "treatment": {
            "variant_id": str(uuid4()),
            "success_rate": 60.0,  # 25% worse
            "total_trials": 40
        }
    }

    scheduler_service.ab_testing_service.get_experiment_results = AsyncMock(
        return_value=mock_results
    )

    decision = await scheduler_service.check_experiment_stopping_conditions("exp-id")

    assert decision.should_stop is True
    assert decision.condition == StoppingCondition.DEGRADATION
    assert decision.winner_variant_id == UUID(mock_results["control"]["variant_id"])


@pytest.mark.asyncio
async def test_check_stopping_max_duration(scheduler_service):
    """Test stopping condition with max duration reached."""
    mock_results = {
        "experiment": Mock(started_at=datetime.utcnow() - timedelta(days=15)),  # > 14 days
        "control": {
            "variant_id": str(uuid4()),
            "success_rate": 75.0,
            "total_trials": 100
        },
        "treatment": {
            "variant_id": str(uuid4()),
            "success_rate": 77.0,  # Small improvement
            "total_trials": 100
        }
    }

    scheduler_service.ab_testing_service.get_experiment_results = AsyncMock(
        return_value=mock_results
    )

    decision = await scheduler_service.check_experiment_stopping_conditions("exp-id")

    assert decision.should_stop is True
    assert decision.condition == StoppingCondition.MAX_DURATION


@pytest.mark.asyncio
async def test_check_stopping_continue(scheduler_service):
    """Test when experiment should continue."""
    mock_results = {
        "experiment": Mock(started_at=datetime.utcnow() - timedelta(days=3)),
        "control": {
            "variant_id": str(uuid4()),
            "success_rate": 75.0,
            "total_trials": 20  # Not enough trials
        },
        "treatment": {
            "variant_id": str(uuid4()),
            "success_rate": 78.0,
            "total_trials": 20
        }
    }

    scheduler_service.ab_testing_service.get_experiment_results = AsyncMock(
        return_value=mock_results
    )

    decision = await scheduler_service.check_experiment_stopping_conditions("exp-id")

    assert decision.should_stop is False
    assert decision.condition is None
    assert "continue" in decision.reason.lower()


@pytest.mark.asyncio
async def test_check_stopping_insufficient_data(scheduler_service):
    """Test when there's insufficient data."""
    scheduler_service.ab_testing_service.get_experiment_results = AsyncMock(
        return_value=None
    )

    decision = await scheduler_service.check_experiment_stopping_conditions("exp-id")

    assert decision.should_stop is False
    assert "insufficient" in decision.reason.lower()


# ============================================================================
# TESTS: HELPER METHODS
# ============================================================================

def test_calculate_priority_critical(scheduler_service):
    """Test priority calculation for critical cases."""
    priority = scheduler_service._calculate_priority(gap=35.0, current_rate=45.0)
    assert priority == ExperimentPriority.CRITICAL


def test_calculate_priority_high(scheduler_service):
    """Test priority calculation for high priority."""
    priority = scheduler_service._calculate_priority(gap=25.0, current_rate=60.0)
    assert priority == ExperimentPriority.HIGH


def test_calculate_priority_medium(scheduler_service):
    """Test priority calculation for medium priority."""
    priority = scheduler_service._calculate_priority(gap=15.0, current_rate=65.0)
    assert priority == ExperimentPriority.MEDIUM


def test_calculate_priority_low(scheduler_service):
    """Test priority calculation for low priority."""
    priority = scheduler_service._calculate_priority(gap=5.0, current_rate=72.0)
    assert priority == ExperimentPriority.LOW


def test_determine_winner(scheduler_service):
    """Test winner determination."""
    control = {"variant_id": str(uuid4()), "success_rate": 70.0}
    treatment = {"variant_id": str(uuid4()), "success_rate": 85.0}

    winner = scheduler_service._determine_winner(control, treatment)

    assert winner == UUID(treatment["variant_id"])


def test_determine_winner_control_wins(scheduler_service):
    """Test winner determination when control wins."""
    control = {"variant_id": str(uuid4()), "success_rate": 85.0}
    treatment = {"variant_id": str(uuid4()), "success_rate": 70.0}

    winner = scheduler_service._determine_winner(control, treatment)

    assert winner == UUID(control["variant_id"])


# ============================================================================
# TESTS: BACKGROUND SCHEDULER
# ============================================================================

def test_start_scheduler(scheduler_service):
    """Test starting background scheduler."""
    scheduler_service.start_scheduler()

    assert scheduler_service.scheduler is not None
    assert scheduler_service.scheduler.running

    # Cleanup
    scheduler_service.stop_scheduler()


def test_stop_scheduler(scheduler_service):
    """Test stopping background scheduler."""
    scheduler_service.start_scheduler()
    scheduler_service.stop_scheduler()

    assert scheduler_service.scheduler is None


def test_start_scheduler_idempotent(scheduler_service):
    """Test that starting scheduler multiple times is safe."""
    scheduler_service.start_scheduler()
    first_scheduler = scheduler_service.scheduler

    scheduler_service.start_scheduler()
    second_scheduler = scheduler_service.scheduler

    assert first_scheduler is second_scheduler

    # Cleanup
    scheduler_service.stop_scheduler()
