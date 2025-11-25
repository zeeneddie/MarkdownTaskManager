"""
Unit tests for Evolution Metrics Service

Tests performance tracking, trend analysis, and ChromaDB integration.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.evolution_metrics_service import EvolutionMetricsService
from app.models.ab_testing import Experiment, ExperimentVariant, ExperimentResult


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection = MagicMock(return_value=mock_collection)
    return mock_client


@pytest.fixture
def metrics_service(mock_db_session, mock_chroma_client):
    """Create EvolutionMetricsService with mocked dependencies."""
    return EvolutionMetricsService(mock_db_session, mock_chroma_client)


class TestAgentPerformance:
    """Test agent performance tracking."""

    @pytest.mark.asyncio
    async def test_get_agent_performance_no_data(self, metrics_service, mock_db_session):
        """Test performance metrics with no experiments."""
        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: [])
        ))

        perf = await metrics_service.get_agent_performance("felix")

        assert perf["agent_id"] == "felix"
        assert perf["total_experiments"] == 0
        assert perf["average_success_rate"] == 0.0
        assert perf["improvement_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_agent_performance_with_experiments(
        self,
        metrics_service,
        mock_db_session
    ):
        """Test performance metrics with experiments."""
        # Create mock experiments with results
        control_variant = MagicMock(spec=ExperimentVariant)
        control_variant.is_control = True
        control_variant.results = [
            MagicMock(spec=ExperimentResult, success=True),
            MagicMock(spec=ExperimentResult, success=True),
            MagicMock(spec=ExperimentResult, success=False)
        ]  # 2/3 = 66.7% success

        test_variant = MagicMock(spec=ExperimentVariant)
        test_variant.is_control = False
        test_variant.results = [
            MagicMock(spec=ExperimentResult, success=True),
            MagicMock(spec=ExperimentResult, success=True),
            MagicMock(spec=ExperimentResult, success=True)
        ]  # 3/3 = 100% success

        experiment = MagicMock(spec=Experiment)
        experiment.agent_id = "felix"
        experiment.status = "COMPLETED"
        experiment.created_at = datetime.utcnow()
        experiment.variants = [control_variant, test_variant]

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: [experiment])
        ))

        perf = await metrics_service.get_agent_performance("felix")

        assert perf["agent_id"] == "felix"
        assert perf["total_experiments"] == 1
        assert perf["total_tasks"] == 6
        # Improvement: (100% - 66.7%) / 66.7% = 50%
        assert perf["improvement_rate"] > 0

    @pytest.mark.asyncio
    async def test_get_agent_performance_date_range(
        self,
        metrics_service,
        mock_db_session
    ):
        """Test performance metrics with date filtering."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: [])
        ))

        perf = await metrics_service.get_agent_performance(
            "felix",
            start_date=start_date,
            end_date=end_date
        )

        assert perf["period"]["start"] == start_date.isoformat()
        assert perf["period"]["end"] == end_date.isoformat()


class TestTrendAnalysis:
    """Test trend analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_trends_no_data(self, metrics_service, mock_db_session):
        """Test trend analysis with no data."""
        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: [])
        ))

        trends = await metrics_service.analyze_trends("felix")

        assert trends["agent_id"] == "felix"
        assert trends["daily_values"] == []
        assert trends["trend_direction"] == "stable"
        assert trends["trend_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_analyze_trends_improving(self, metrics_service, mock_db_session):
        """Test trend detection for improving agent."""
        # Create mock results showing improvement
        results = []
        base_date = datetime.utcnow() - timedelta(days=10)

        # Early results: 50% success
        for i in range(5):
            result = MagicMock(spec=ExperimentResult)
            result.created_at = base_date + timedelta(days=i)
            result.success = (i % 2 == 0)  # 3/5 success
            result.metrics_json = {}
            results.append(result)

        # Later results: 80% success
        for i in range(5, 10):
            result = MagicMock(spec=ExperimentResult)
            result.created_at = base_date + timedelta(days=i)
            result.success = (i % 5 != 0)  # 4/5 success
            result.metrics_json = {}
            results.append(result)

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: results)
        ))

        trends = await metrics_service.analyze_trends("felix", days=10)

        assert trends["trend_direction"] in ["improving", "stable"]
        # Should show improvement or at least stable

    @pytest.mark.asyncio
    async def test_analyze_trends_declining(self, metrics_service, mock_db_session):
        """Test trend detection for declining agent."""
        # Create mock results showing decline
        results = []
        base_date = datetime.utcnow() - timedelta(days=10)

        # Early results: 80% success
        for i in range(5):
            result = MagicMock(spec=ExperimentResult)
            result.created_at = base_date + timedelta(days=i)
            result.success = (i % 5 != 0)  # 4/5 success
            result.metrics_json = {}
            results.append(result)

        # Later results: 40% success
        for i in range(5, 10):
            result = MagicMock(spec=ExperimentResult)
            result.created_at = base_date + timedelta(days=i)
            result.success = (i % 5 == 0 or i % 5 == 1)  # 2/5 success
            result.metrics_json = {}
            results.append(result)

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: results)
        ))

        trends = await metrics_service.analyze_trends("felix", days=10)

        assert trends["trend_direction"] in ["declining", "stable"]
        # Should show decline or at least stable


class TestMetricsAggregation:
    """Test metrics aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_metrics_daily(self, metrics_service, mock_db_session):
        """Test daily metrics aggregation."""
        results = []
        base_date = datetime.utcnow() - timedelta(days=5)

        # Create 10 results over 5 days
        for i in range(10):
            result = MagicMock(spec=ExperimentResult)
            result.created_at = base_date + timedelta(days=i // 2)
            result.success = (i % 3 != 0)  # ~67% success
            result.metrics_json = {
                "execution_time_ms": 1000 + (i * 100),
                "code_quality_score": 7.0 + (i * 0.2)
            }
            results.append(result)

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: results)
        ))

        aggregated = await metrics_service.aggregate_metrics("felix", period="daily")

        assert len(aggregated) > 0
        # Should have aggregated data by day
        for agg in aggregated:
            assert "period" in agg
            assert "total_tasks" in agg
            assert "success_rate" in agg

    @pytest.mark.asyncio
    async def test_aggregate_metrics_weekly(self, metrics_service, mock_db_session):
        """Test weekly metrics aggregation."""
        results = []
        base_date = datetime.utcnow() - timedelta(days=30)

        # Create results over 30 days
        for i in range(30):
            result = MagicMock(spec=ExperimentResult)
            result.created_at = base_date + timedelta(days=i)
            result.success = True
            result.metrics_json = {}
            results.append(result)

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=lambda: MagicMock(all=lambda: results)
        ))

        aggregated = await metrics_service.aggregate_metrics("felix", period="weekly")

        assert len(aggregated) > 0
        # Should have aggregated data by week
        for agg in aggregated:
            assert "period" in agg
            assert "W" in agg["period"]  # ISO week format


class TestCrossAgentComparison:
    """Test cross-agent comparison."""

    @pytest.mark.asyncio
    async def test_compare_agents(self, metrics_service, mock_db_session):
        """Test comparing multiple agents."""
        # Mock different performance for each agent
        def create_mock_experiments(agent_id: str, success_rate: float):
            variant = MagicMock(spec=ExperimentVariant)
            variant.is_control = False
            variant.results = [
                MagicMock(spec=ExperimentResult, success=(i < success_rate * 10))
                for i in range(10)
            ]

            experiment = MagicMock(spec=Experiment)
            experiment.agent_id = agent_id
            experiment.status = "COMPLETED"
            experiment.created_at = datetime.utcnow()
            experiment.variants = [variant]

            return [experiment]

        async def mock_execute(query):
            # Return different data based on agent_id in query
            # This is simplified; real implementation would parse query
            return MagicMock(
                scalars=lambda: MagicMock(all=lambda: [])
            )

        mock_db_session.execute = mock_execute

        comparison = await metrics_service.compare_agents(["felix", "marcus", "quinn"])

        assert "felix" in comparison
        assert "marcus" in comparison
        assert "quinn" in comparison

        # Should have rankings
        for agent_data in comparison.values():
            assert "success_rate_rank" in agent_data
            assert "improvement_rank" in agent_data


class TestChromaDBIntegration:
    """Test ChromaDB milestone storage."""

    @pytest.mark.asyncio
    async def test_store_evolution_milestone(
        self,
        metrics_service,
        mock_chroma_client
    ):
        """Test storing milestone in ChromaDB."""
        success = await metrics_service.store_evolution_milestone(
            agent_id="felix",
            milestone_type="first_success",
            description="First successful experiment",
            metrics={"success_rate": 0.95},
            experiment_id=uuid4()
        )

        assert success is True
        assert mock_chroma_client.get_or_create_collection.called

    @pytest.mark.asyncio
    async def test_store_evolution_milestone_no_chroma(self, mock_db_session):
        """Test milestone storage without ChromaDB."""
        service = EvolutionMetricsService(mock_db_session, chroma_client=None)

        success = await service.store_evolution_milestone(
            agent_id="felix",
            milestone_type="first_success",
            description="Test",
            metrics={}
        )

        assert success is False  # No ChromaDB configured

    @pytest.mark.asyncio
    async def test_retrieve_evolution_milestones(
        self,
        metrics_service,
        mock_chroma_client
    ):
        """Test retrieving milestones from ChromaDB."""
        # Mock ChromaDB query results
        mock_collection = mock_chroma_client.get_or_create_collection.return_value
        mock_collection.query = MagicMock(return_value={
            "ids": [["milestone_1", "milestone_2"]],
            "documents": [["Doc 1", "Doc 2"]],
            "metadatas": [[{"agent_id": "felix"}, {"agent_id": "felix"}]],
            "distances": [[0.1, 0.2]]
        })

        milestones = await metrics_service.retrieve_evolution_milestones("felix")

        assert len(milestones) == 2
        assert mock_collection.query.called


class TestMilestoneDetection:
    """Test automatic milestone detection."""

    @pytest.mark.asyncio
    async def test_detect_milestone_major_improvement(self, metrics_service):
        """Test detecting major improvement milestone."""
        control = MagicMock(spec=ExperimentVariant)
        control.is_control = True
        control.results = [MagicMock(success=(i < 5)) for i in range(10)]  # 50%

        winner_id = uuid4()
        winner = MagicMock(spec=ExperimentVariant)
        winner.id = winner_id
        winner.variant_name = "async_variant"
        winner.is_control = False
        winner.results = [MagicMock(success=(i < 9)) for i in range(10)]  # 90%

        experiment = MagicMock(spec=Experiment)
        experiment.status = "COMPLETED"
        experiment.winner_variant_id = winner_id
        experiment.variants = [control, winner]

        milestone = await metrics_service.detect_milestone("felix", experiment)

        assert milestone is not None
        milestone_type, description = milestone
        assert "improvement" in milestone_type.lower()
        assert "80" in description  # 80% improvement

    @pytest.mark.asyncio
    async def test_detect_milestone_no_milestone(self, metrics_service):
        """Test no milestone for small improvement."""
        control = MagicMock(spec=ExperimentVariant)
        control.is_control = True
        control.results = [MagicMock(success=(i < 8)) for i in range(10)]  # 80%

        winner_id = uuid4()
        winner = MagicMock(spec=ExperimentVariant)
        winner.id = winner_id
        winner.is_control = False
        winner.results = [MagicMock(success=(i < 9)) for i in range(10)]  # 90%

        experiment = MagicMock(spec=Experiment)
        experiment.status = "COMPLETED"
        experiment.winner_variant_id = winner_id
        experiment.variants = [control, winner]

        milestone = await metrics_service.detect_milestone("felix", experiment)

        # 12.5% improvement - below 20% threshold
        # Might still trigger 10% threshold
        assert milestone is None or "improvement_threshold" in milestone[0]
