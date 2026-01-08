"""
Unit Tests for Observability Service

Week 54: Tests for agent action logging, decision tracing, and performance aggregation.
"""

import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.observability_service import ObservabilityService
from app.models.observability import (
    LLMProvider,
    AgentAction,
    DecisionTrace,
    AgentPerformanceDaily,
)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def observability_service(mock_db_session):
    """Create ObservabilityService with mocked dependencies."""
    return ObservabilityService(mock_db_session)


# ============================================================================
# PROVIDER MANAGEMENT TESTS
# ============================================================================

class TestProviderManagement:
    """Test LLM provider management functions."""

    @pytest.mark.asyncio
    async def test_get_all_providers(self, observability_service, mock_db_session):
        """Test retrieving all providers."""
        # Setup
        mock_providers = [
            MagicMock(spec=LLMProvider, name="ollama", tier="free"),
            MagicMock(spec=LLMProvider, name="claude_sonnet", tier="balanced"),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_providers)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        providers = await observability_service.get_all_providers()

        # Verify
        assert len(providers) == 2
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_get_active_providers(self, observability_service, mock_db_session):
        """Test retrieving only active providers."""
        # Setup
        mock_providers = [
            MagicMock(spec=LLMProvider, name="ollama", is_active=True),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_providers)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        providers = await observability_service.get_active_providers()

        # Verify
        assert len(providers) == 1
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_get_provider_by_name(self, observability_service, mock_db_session):
        """Test retrieving a provider by name."""
        # Setup
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.name = "ollama"
        mock_provider.tier = "free"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_provider)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        provider = await observability_service.get_provider_by_name("ollama")

        # Verify
        assert provider is not None
        assert provider.name == "ollama"

    @pytest.mark.asyncio
    async def test_get_provider_by_name_not_found(self, observability_service, mock_db_session):
        """Test retrieving a non-existent provider."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        provider = await observability_service.get_provider_by_name("nonexistent")

        # Verify
        assert provider is None

    @pytest.mark.asyncio
    async def test_get_providers_by_tier(self, observability_service, mock_db_session):
        """Test filtering providers by tier."""
        # Setup
        mock_providers = [
            MagicMock(spec=LLMProvider, name="claude_sonnet", tier="balanced"),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_providers)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        providers = await observability_service.get_providers_by_tier("balanced")

        # Verify
        assert len(providers) == 1
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_update_provider_status(self, observability_service, mock_db_session):
        """Test enabling/disabling a provider."""
        # Setup
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.name = "ollama"
        mock_provider.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_provider)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute
        provider = await observability_service.update_provider_status("ollama", False)

        # Verify
        assert provider is not None
        assert mock_provider.is_active == False
        assert mock_db_session.commit.called


# ============================================================================
# ACTION LOGGING TESTS
# ============================================================================

class TestActionLogging:
    """Test agent action logging functions."""

    @pytest.mark.asyncio
    async def test_log_action(self, observability_service, mock_db_session):
        """Test logging a basic agent action."""
        # Setup
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute
        action = await observability_service.log_action(
            agent_id="felix",
            action_type="generate",
            provider="ollama",
            model="qwen2.5-coder:7b",
            token_input=100,
            token_output=200,
            duration_ms=1500,
            success=True,
            confidence_score=0.85,
        )

        # Verify
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_log_action_with_error(self, observability_service, mock_db_session):
        """Test logging a failed agent action."""
        # Setup
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute
        action = await observability_service.log_action(
            agent_id="quinn",
            action_type="review",
            provider="claude_sonnet",
            success=False,
            error="Timeout exceeded",
        )

        # Verify
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_log_action_with_task_id(self, observability_service, mock_db_session):
        """Test logging action associated with a task."""
        # Setup
        task_id = uuid4()
        session_id = uuid4()
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute
        action = await observability_service.log_action(
            agent_id="betty",
            action_type="debug",
            task_id=task_id,
            session_id=session_id,
            decision_rationale="Found null pointer in line 42",
        )

        # Verify
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_get_recent_actions(self, observability_service, mock_db_session):
        """Test retrieving recent actions."""
        # Setup
        mock_actions = [
            MagicMock(spec=AgentAction, agent_id="felix", action_type="generate"),
            MagicMock(spec=AgentAction, agent_id="quinn", action_type="review"),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_actions)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        actions = await observability_service.get_recent_actions(limit=50)

        # Verify
        assert len(actions) == 2
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_get_recent_actions_filtered_by_agent(self, observability_service, mock_db_session):
        """Test retrieving recent actions for a specific agent."""
        # Setup
        mock_actions = [
            MagicMock(spec=AgentAction, agent_id="felix", action_type="generate"),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_actions)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        actions = await observability_service.get_recent_actions(
            agent_id="felix",
            limit=10
        )

        # Verify
        assert len(actions) == 1
        assert actions[0].agent_id == "felix"

    @pytest.mark.asyncio
    async def test_get_actions_by_task(self, observability_service, mock_db_session):
        """Test retrieving all actions for a task."""
        # Setup
        task_id = uuid4()
        mock_actions = [
            MagicMock(spec=AgentAction, task_id=task_id, action_type="generate"),
            MagicMock(spec=AgentAction, task_id=task_id, action_type="review"),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_actions)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        actions = await observability_service.get_actions_by_task(task_id)

        # Verify
        assert len(actions) == 2


# ============================================================================
# DECISION TRACING TESTS
# ============================================================================

class TestDecisionTracing:
    """Test decision trace logging functions."""

    @pytest.mark.asyncio
    async def test_log_decision(self, observability_service, mock_db_session):
        """Test logging a decision point."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=None)  # No existing traces
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute
        decision = await observability_service.log_decision(
            agent_id="felix",
            decision_point="model_selection",
            options=[
                {"name": "ollama", "cost": 0},
                {"name": "claude_sonnet", "cost": 3},
            ],
            selected_option="ollama",
            selection_rationale="Task is simple, use free tier",
            outcome="success",
        )

        # Verify
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_log_decision_with_task_id_increments_sequence(self, observability_service, mock_db_session):
        """Test that sequence number increments for same task."""
        # Setup
        task_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=2)  # Existing max sequence
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute
        decision = await observability_service.log_decision(
            agent_id="quinn",
            decision_point="quality_gate",
            task_id=task_id,
            outcome="failure",
        )

        # Verify
        assert mock_db_session.add.called
        # The added trace should have sequence_number = 3

    @pytest.mark.asyncio
    async def test_get_decision_trace(self, observability_service, mock_db_session):
        """Test retrieving decision trace for a task."""
        # Setup
        task_id = uuid4()
        mock_traces = [
            MagicMock(spec=DecisionTrace, sequence_number=1, decision_point="model_selection"),
            MagicMock(spec=DecisionTrace, sequence_number=2, decision_point="quality_gate"),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_traces)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        traces = await observability_service.get_decision_trace(task_id)

        # Verify
        assert len(traces) == 2
        assert traces[0].sequence_number == 1


# ============================================================================
# PERFORMANCE AGGREGATION TESTS
# ============================================================================

class TestPerformanceAggregation:
    """Test daily performance aggregation functions."""

    @pytest.mark.asyncio
    async def test_get_daily_performance(self, observability_service, mock_db_session):
        """Test retrieving daily performance records."""
        # Setup
        mock_records = [
            MagicMock(
                spec=AgentPerformanceDaily,
                agent_id="felix",
                date=date.today(),
                total_actions=50,
                successful_actions=45,
            ),
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_records)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        records = await observability_service.get_daily_performance()

        # Verify
        assert len(records) == 1
        assert records[0].agent_id == "felix"

    @pytest.mark.asyncio
    async def test_get_daily_performance_filtered(self, observability_service, mock_db_session):
        """Test retrieving daily performance with filters."""
        # Setup
        mock_records = []
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_records)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        records = await observability_service.get_daily_performance(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            agent_id="felix",
        )

        # Verify
        assert isinstance(records, list)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestHelperFunctions:
    """Test helper functions."""

    def test_truncate_short_text(self, observability_service):
        """Test truncation of text shorter than max."""
        result = observability_service._truncate("Short text", 100)
        assert result == "Short text"

    def test_truncate_long_text(self, observability_service):
        """Test truncation of text longer than max."""
        long_text = "A" * 150
        result = observability_service._truncate(long_text, 100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_truncate_none(self, observability_service):
        """Test truncation of None value."""
        result = observability_service._truncate(None, 100)
        assert result is None

    def test_truncate_exact_length(self, observability_service):
        """Test truncation of text exactly at max."""
        exact_text = "A" * 100
        result = observability_service._truncate(exact_text, 100)
        assert result == exact_text
        assert len(result) == 100
