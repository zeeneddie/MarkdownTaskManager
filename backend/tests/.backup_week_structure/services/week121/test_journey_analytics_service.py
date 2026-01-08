# backend/tests/services/week121/test_journey_analytics_service.py
"""
Tests for Journey Analytics Service - Week 121

Tests customer journey tracking and funnel analysis.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.chatbot_journey import (
    JourneyEvent, JourneyFunnel, JourneyFunnelSnapshot,
    EventCategory, EVENT_TYPES
)
from app.services.journey_analytics_service import JourneyAnalyticsService


class TestEventTracking:
    """Test event tracking functionality."""

    @pytest.mark.asyncio
    async def test_track_portal_visit_event(self, mock_db_session):
        """Test tracking a portal visit event."""
        service = JourneyAnalyticsService(mock_db_session)

        event = await service.track_event(
            customer_id="customer-123",
            event_type="portal_visit",
            session_id="session-abc",
        )

        assert event.customer_id == "customer-123"
        assert event.event_type == "portal_visit"
        assert event.event_category == EventCategory.NAVIGATION.value
        assert event.session_id == "session-abc"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_feature_view_event(self, mock_db_session):
        """Test tracking a feature view event."""
        service = JourneyAnalyticsService(mock_db_session)

        event = await service.track_event(
            customer_id="customer-123",
            event_type="feature_view",
            feature_id=456,
            feature_status="in_progress",
        )

        assert event.event_type == "feature_view"
        assert event.event_category == EventCategory.INTERACTION.value
        assert event.feature_id == 456
        assert event.feature_status == "in_progress"

    @pytest.mark.asyncio
    async def test_track_conversion_event(self, mock_db_session):
        """Test tracking a conversion event."""
        service = JourneyAnalyticsService(mock_db_session)

        event = await service.track_event(
            customer_id="customer-123",
            event_type="feature_create_submit",
            event_data={"feature_title": "Dark Mode"},
        )

        assert event.event_type == "feature_create_submit"
        assert event.event_category == EventCategory.CONVERSION.value
        assert event.event_data["feature_title"] == "Dark Mode"

    @pytest.mark.asyncio
    async def test_track_milestone_event(self, mock_db_session):
        """Test tracking a milestone event."""
        service = JourneyAnalyticsService(mock_db_session)

        event = await service.track_event(
            customer_id="customer-123",
            event_type="feature_released",
            feature_id=789,
        )

        assert event.event_type == "feature_released"
        assert event.event_category == EventCategory.MILESTONE.value

    @pytest.mark.asyncio
    async def test_track_feature_event_helper(self, mock_db_session):
        """Test track_feature_event helper method."""
        service = JourneyAnalyticsService(mock_db_session)

        event = await service.track_feature_event(
            customer_id="customer-123",
            feature_id=123,
            event_type="feature_testing",
            feature_status="testing",
            event_data={"tests_passed": 10, "tests_total": 15},
        )

        assert event.feature_id == 123
        assert event.event_type == "feature_testing"
        assert event.feature_status == "testing"
        assert event.event_data["tests_passed"] == 10

    @pytest.mark.asyncio
    async def test_track_chatbot_event_helper(self, mock_db_session):
        """Test track_chatbot_event helper method."""
        service = JourneyAnalyticsService(mock_db_session)

        event = await service.track_chatbot_event(
            customer_id="customer-123",
            event_type="chatbot_message_sent",
            session_id="chat-session-xyz",
            event_data={"intent": "status_query"},
        )

        assert event.event_type == "chatbot_message_sent"
        assert event.session_id == "chat-session-xyz"
        assert event.event_data["intent"] == "status_query"


class TestEventTypes:
    """Test event type definitions."""

    def test_all_event_types_have_category(self):
        """Test all event types have a category defined."""
        for event_type, info in EVENT_TYPES.items():
            assert "category" in info, f"Missing category for {event_type}"
            assert info["category"] in [c.value for c in EventCategory], \
                f"Invalid category for {event_type}"

    def test_all_event_types_have_description(self):
        """Test all event types have a description."""
        for event_type, info in EVENT_TYPES.items():
            assert "description" in info, f"Missing description for {event_type}"
            assert len(info["description"]) > 0

    def test_navigation_events(self):
        """Test navigation event types."""
        nav_events = ["portal_visit", "page_view", "dashboard_view", "session_start", "session_end"]
        for event in nav_events:
            assert EVENT_TYPES[event]["category"] == EventCategory.NAVIGATION.value

    def test_conversion_events(self):
        """Test conversion event types."""
        conv_events = ["feature_create_submit", "feedback_submitted"]
        for event in conv_events:
            assert EVENT_TYPES[event]["category"] == EventCategory.CONVERSION.value

    def test_milestone_events(self):
        """Test milestone event types."""
        milestone_events = ["feature_released", "badge_earned", "level_up"]
        for event in milestone_events:
            assert EVENT_TYPES[event]["category"] == EventCategory.MILESTONE.value


class TestFunnelInsights:
    """Test funnel insight generation."""

    def test_generate_bottleneck_insight(self, mock_db_session):
        """Test bottleneck insight generation."""
        service = JourneyAnalyticsService(mock_db_session)

        step_counts = {"visit": 100, "view": 70, "create": 20, "submit": 10}
        conversion_rates = {"visit": 100.0, "view": 70.0, "create": 28.6, "submit": 50.0}
        drop_off_rates = {"visit": 0.0, "view": 30.0, "create": 71.4, "submit": 50.0}

        insights = service._generate_funnel_insights(
            step_counts, conversion_rates, drop_off_rates, "create"
        )

        assert len(insights) > 0
        assert insights[0]["type"] == "warning"
        assert "create" in insights[0]["title"]

    def test_generate_low_conversion_insight(self, mock_db_session):
        """Test low overall conversion insight."""
        service = JourneyAnalyticsService(mock_db_session)

        step_counts = {"step1": 1000, "step2": 100, "step3": 5}
        conversion_rates = {"step1": 100.0, "step2": 10.0, "step3": 5.0}
        drop_off_rates = {"step1": 0.0, "step2": 90.0, "step3": 95.0}

        insights = service._generate_funnel_insights(
            step_counts, conversion_rates, drop_off_rates, "step2"
        )

        critical_insights = [i for i in insights if i["type"] == "critical"]
        assert len(critical_insights) > 0

    def test_generate_no_data_insight(self, mock_db_session):
        """Test no data insight generation."""
        service = JourneyAnalyticsService(mock_db_session)

        step_counts = {"step1": 0, "step2": 0, "step3": 0}
        conversion_rates = {}
        drop_off_rates = {}

        insights = service._generate_funnel_insights(
            step_counts, conversion_rates, drop_off_rates, None
        )

        info_insights = [i for i in insights if i["type"] == "info"]
        assert len(info_insights) > 0
        assert "No data" in info_insights[0]["title"]


class TestJourneyEventModel:
    """Test JourneyEvent model methods."""

    def test_is_conversion_event(self):
        """Test is_conversion_event method."""
        event = JourneyEvent(
            id=uuid4(),
            customer_id="test",
            event_type="feature_create_submit",
            event_category=EventCategory.CONVERSION.value,
        )
        assert event.is_conversion_event()

    def test_is_not_conversion_event(self):
        """Test is_conversion_event for non-conversion."""
        event = JourneyEvent(
            id=uuid4(),
            customer_id="test",
            event_type="page_view",
            event_category=EventCategory.NAVIGATION.value,
        )
        assert not event.is_conversion_event()

    def test_is_milestone(self):
        """Test is_milestone method."""
        event = JourneyEvent(
            id=uuid4(),
            customer_id="test",
            event_type="feature_released",
            event_category=EventCategory.MILESTONE.value,
        )
        assert event.is_milestone()


class TestJourneyFunnelModel:
    """Test JourneyFunnel model methods."""

    def test_get_step_count(self):
        """Test get_step_count method."""
        funnel = JourneyFunnel(
            id=uuid4(),
            name="test_funnel",
            steps=[
                {"name": "step1", "event_type": "event1"},
                {"name": "step2", "event_type": "event2"},
                {"name": "step3", "event_type": "event3"},
            ],
            goal_event="event3",
        )
        assert funnel.get_step_count() == 3

    def test_get_step_names(self):
        """Test get_step_names method."""
        funnel = JourneyFunnel(
            id=uuid4(),
            name="test_funnel",
            steps=[
                {"name": "visit", "event_type": "portal_visit"},
                {"name": "view", "event_type": "feature_view"},
                {"name": "submit", "event_type": "feature_create_submit"},
            ],
            goal_event="feature_create_submit",
        )
        assert funnel.get_step_names() == ["visit", "view", "submit"]

    def test_get_step_count_empty(self):
        """Test get_step_count with no steps."""
        funnel = JourneyFunnel(
            id=uuid4(),
            name="empty_funnel",
            steps=None,
            goal_event="goal",
        )
        assert funnel.get_step_count() == 0


class TestJourneyFunnelSnapshotModel:
    """Test JourneyFunnelSnapshot model methods."""

    def test_get_biggest_drop(self):
        """Test get_biggest_drop method."""
        snapshot = JourneyFunnelSnapshot(
            id=uuid4(),
            funnel_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            step_counts={},
            conversion_rates={},
            drop_off_rates={"step1": 10.0, "step2": 50.0, "step3": 30.0},
            overall_conversion=10.0,
        )
        assert snapshot.get_biggest_drop() == "step2"

    def test_get_biggest_drop_empty(self):
        """Test get_biggest_drop with no drop-offs."""
        snapshot = JourneyFunnelSnapshot(
            id=uuid4(),
            funnel_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            step_counts={},
            conversion_rates={},
            drop_off_rates={},
            overall_conversion=100.0,
        )
        assert snapshot.get_biggest_drop() is None


class TestCustomerJourneySummary:
    """Test customer journey summary generation."""

    @pytest.mark.asyncio
    async def test_get_customer_journey_summary_empty(self, mock_db_session):
        """Test journey summary for customer with no events."""
        # Mock empty results
        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=0),
            scalar_one_or_none=MagicMock(return_value=None),
            all=MagicMock(return_value=[]),
        ))

        service = JourneyAnalyticsService(mock_db_session)
        summary = await service.get_customer_journey_summary("customer-123")

        assert summary["customer_id"] == "customer-123"
        assert summary["total_events"] == 0
        assert summary["journey_duration_days"] == 0


class TestEventStats:
    """Test aggregate event statistics."""

    @pytest.mark.asyncio
    async def test_get_event_stats_empty(self, mock_db_session):
        """Test stats with no events."""
        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=0),
            all=MagicMock(return_value=[]),
        ))

        service = JourneyAnalyticsService(mock_db_session)
        stats = await service.get_event_stats()

        assert stats["total_events"] == 0
        assert stats["unique_customers"] == 0
        assert stats["avg_events_per_customer"] == 0


# ============== FIXTURES ==============

@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session
