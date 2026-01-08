"""
Integration Tests for Continuous Learning API

Week 25-26: AgentEvolver Integration - Continuous Learning Tests

Author: Claude Code (Week 26 Day 5)
Date: 2025-11-22
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Import the service and types
from app.services.continuous_learning_service import (
    ContinuousLearningService,
    LearningSession,
    LearningStatus,
    OptimizationType,
    ThresholdUpdate,
    WeightUpdate,
    SessionResult,
    RetrainingCheck,
    LearningMetrics
)
from app.services.experience_store_service import WorkType, AgentRole, Outcome


class TestContinuousLearningService:
    """Tests for ContinuousLearningService"""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance"""
        return ContinuousLearningService()

    @pytest.fixture
    def mock_experience_store(self):
        """Create mock experience store"""
        mock = AsyncMock()
        mock.get_experiences.return_value = []
        mock.get_successful_patterns.return_value = []
        return mock

    # -------------------------------------------------------------------------
    # THRESHOLD OPTIMIZATION TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_optimize_thresholds_no_experiences(self, service):
        """Test threshold optimization with no experiences"""
        with patch.object(service, '_get_experience_store') as mock_store:
            mock_store.return_value.get_experiences = AsyncMock(return_value=[])

            result = await service.optimize_validation_thresholds("felix")

            assert isinstance(result, ThresholdUpdate)
            assert result.agent_id == "felix"
            assert result.confidence == 0.0
            assert "No experiences" in result.reasoning

    @pytest.mark.asyncio
    async def test_optimize_thresholds_high_success(self, service):
        """Test threshold optimization with high success rate"""
        # Create mock experiences with high success rate
        mock_experiences = [
            MagicMock(
                quality_score=85,
                outcome=Outcome.SUCCESS
            ) for _ in range(10)
        ]

        with patch.object(service, '_get_experience_store') as mock_store:
            mock_store.return_value.get_experiences = AsyncMock(
                return_value=mock_experiences
            )

            result = await service.optimize_validation_thresholds("felix")

            assert result.agent_id == "felix"
            assert "High success rate" in result.reasoning or "selectivity" in result.reasoning

    # -------------------------------------------------------------------------
    # LEARNING RATE TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_adjust_learning_rate_improving(self, service):
        """Test learning rate adjustment when performance is improving"""
        # Set up improving trajectory
        service._learning_metrics["felix"] = LearningMetrics(
            agent_id="felix",
            agent_role=AgentRole.FEATURE_ARCHITECT,
            performance_trajectory=[0.6, 0.65, 0.70, 0.75, 0.80]
        )

        mock_performance = MagicMock(success_rate=0.8)

        new_rate = await service.adjust_learning_rate("felix", mock_performance)

        # Should decrease rate when improving (fine-tuning)
        assert new_rate <= 0.1

    @pytest.mark.asyncio
    async def test_adjust_learning_rate_declining(self, service):
        """Test learning rate adjustment when performance is declining"""
        service._learning_metrics["marcus"] = LearningMetrics(
            agent_id="marcus",
            agent_role=AgentRole.MAINTENANCE_SPECIALIST,
            performance_trajectory=[0.80, 0.75, 0.70, 0.65, 0.60]
        )

        mock_performance = MagicMock(success_rate=0.5)

        new_rate = await service.adjust_learning_rate("marcus", mock_performance)

        # Should increase rate when declining
        assert new_rate >= 0.1

    # -------------------------------------------------------------------------
    # PATTERN WEIGHT TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_pattern_weights_no_patterns(self, service):
        """Test pattern weight update with no patterns"""
        with patch.object(service, '_get_experience_store') as mock_store:
            mock_store.return_value.get_successful_patterns = AsyncMock(
                return_value=[]
            )

            updates = await service.update_pattern_weights("quinn")

            assert isinstance(updates, list)
            assert len(updates) == 0

    @pytest.mark.asyncio
    async def test_update_pattern_weights_high_success(self, service):
        """Test pattern weight update for high success patterns"""
        mock_pattern = MagicMock(
            id="pattern-1",
            name="Test Pattern",
            success_count=18,
            failure_count=2
        )

        with patch.object(service, '_get_experience_store') as mock_store:
            mock_store.return_value.get_successful_patterns = AsyncMock(
                return_value=[mock_pattern]
            )

            updates = await service.update_pattern_weights("betty")

            assert len(updates) == 1
            assert updates[0].success_rate == 0.9
            assert "High success rate" in updates[0].reasoning

    # -------------------------------------------------------------------------
    # RETRAINING CHECK TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_check_retraining_needed_no_drop(self, service):
        """Test retraining check when no performance drop"""
        with patch.object(service, '_get_evolution_service') as mock_evo:
            mock_metrics = MagicMock(
                success_rate=0.8,
                average_quality_score=80
            )
            mock_evo.return_value.get_performance_metrics = AsyncMock(
                return_value=mock_metrics
            )

            with patch.object(service, '_get_experience_store') as mock_store:
                mock_store.return_value.get_successful_patterns = AsyncMock(
                    return_value=[]
                )

                result = await service.check_retraining_needed("eliza")

                assert isinstance(result, RetrainingCheck)
                # No significant drop, so no retraining needed
                assert result.urgency == "low"

    # -------------------------------------------------------------------------
    # SESSION MANAGEMENT TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_start_learning_session(self, service):
        """Test starting a learning session"""
        with patch.object(service, '_get_evolution_service') as mock_evo:
            mock_evo.return_value.get_performance_metrics = AsyncMock(
                return_value=MagicMock(success_rate=0.7)
            )

            with patch.object(service, '_get_experience_store') as mock_store:
                mock_store.return_value.get_experiences = AsyncMock(
                    return_value=[]
                )
                mock_store.return_value.get_successful_patterns = AsyncMock(
                    return_value=[]
                )

                session = await service.start_learning_session(
                    agent_id="tessa",
                    max_iterations=3
                )

                assert isinstance(session, LearningSession)
                assert session.agent_id == "tessa"
                assert session.status == LearningStatus.COMPLETED
                assert session.max_iterations == 3

    @pytest.mark.asyncio
    async def test_complete_learning_session(self, service):
        """Test completing a learning session"""
        # First start a session
        with patch.object(service, '_get_evolution_service') as mock_evo:
            mock_evo.return_value.get_performance_metrics = AsyncMock(
                return_value=MagicMock(success_rate=0.75)
            )

            with patch.object(service, '_get_experience_store') as mock_store:
                mock_store.return_value.get_experiences = AsyncMock(
                    return_value=[]
                )
                mock_store.return_value.get_successful_patterns = AsyncMock(
                    return_value=[]
                )

                session = await service.start_learning_session("miguel")
                result = await service.complete_learning_session(
                    session.id,
                    {"test": True}
                )

                assert isinstance(result, SessionResult)
                assert result.agent_id == "miguel"
                assert result.session_id == session.id

    @pytest.mark.asyncio
    async def test_complete_session_not_found(self, service):
        """Test completing non-existent session raises error"""
        with pytest.raises(ValueError):
            await service.complete_learning_session("invalid-id", {})

    # -------------------------------------------------------------------------
    # METRICS TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_learning_metrics(self, service):
        """Test getting learning metrics"""
        metrics = await service.get_learning_metrics("diana")

        assert isinstance(metrics, LearningMetrics)
        assert metrics.agent_id == "diana"
        assert metrics.agent_role == AgentRole.DOCUMENTATION_WRITER

    @pytest.mark.asyncio
    async def test_get_all_learning_metrics(self, service):
        """Test getting all learning metrics"""
        # Initialize some metrics
        await service.get_learning_metrics("felix")
        await service.get_learning_metrics("marcus")

        all_metrics = await service.get_all_learning_metrics()

        assert isinstance(all_metrics, list)
        assert len(all_metrics) >= 2

    # -------------------------------------------------------------------------
    # AUTO-TUNE TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_auto_tune_all_agents(self, service):
        """Test auto-tuning all agents"""
        with patch.object(service, '_get_evolution_service') as mock_evo:
            mock_evo.return_value.get_performance_metrics = AsyncMock(
                return_value=MagicMock(success_rate=0.7, average_quality_score=75)
            )

            with patch.object(service, '_get_experience_store') as mock_store:
                mock_store.return_value.get_experiences = AsyncMock(
                    return_value=[]
                )
                mock_store.return_value.get_successful_patterns = AsyncMock(
                    return_value=[]
                )

                results = await service.auto_tune_all_agents()

                assert isinstance(results, dict)
                assert "felix" in results
                assert "marcus" in results
                assert len(results) == 10  # All 10 agents


class TestContinuousLearningEdgeCases:
    """Edge case tests for Continuous Learning"""

    @pytest.fixture
    def service(self):
        return ContinuousLearningService()

    @pytest.mark.asyncio
    async def test_agent_role_mapping(self, service):
        """Test agent role mapping for all agents"""
        expected = {
            "felix": AgentRole.FEATURE_ARCHITECT,
            "marcus": AgentRole.MAINTENANCE_SPECIALIST,
            "quinn": AgentRole.QUALITY_INSPECTOR,
            "betty": AgentRole.BUG_HUNTER,
            "eliza": AgentRole.ESTIMATION_ENGINE,
            "tessa": AgentRole.TEST_ENGINEER,
            "miguel": AgentRole.MIGRATION_ARCHITECT,
            "diana": AgentRole.DOCUMENTATION_WRITER,
            "peter": AgentRole.PRODUCT_OWNER,
            "paul": AgentRole.PROJECT_LEAD
        }

        for agent_id, expected_role in expected.items():
            role = service._get_agent_role(agent_id)
            assert role == expected_role, f"Role mismatch for {agent_id}"

    @pytest.mark.asyncio
    async def test_learning_rate_boundaries(self, service):
        """Test learning rate stays within boundaries"""
        # Test minimum boundary
        config = service._get_agent_config("test")
        config.learning_rate = 0.01

        mock_performance = MagicMock(success_rate=0.1)  # Very low

        new_rate = await service.adjust_learning_rate("test", mock_performance)

        assert new_rate >= service.MIN_LEARNING_RATE
        assert new_rate <= service.MAX_LEARNING_RATE
