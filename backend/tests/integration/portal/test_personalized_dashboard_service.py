# backend/tests/services/week119/test_personalized_dashboard_service.py
"""
Tests for PersonalizedDashboardService - Week 119

Tests dashboard preferences, recommendations, and personalization.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.personalized_dashboard_service import PersonalizedDashboardService
from app.models.engagement import (
    DashboardPreferences,
    FeatureRecommendation,
    RecommendationType,
    RecommendationStatus,
)


class TestPersonalizedDashboardService:
    """Test suite for PersonalizedDashboardService."""

    @pytest.fixture
    async def service(self, db_session: AsyncSession):
        """Create service instance."""
        return PersonalizedDashboardService(db_session)

    # ============== Preferences Tests ==============

    @pytest.mark.asyncio
    async def test_get_or_create_preferences_new_user(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test creating preferences for new user."""
        customer_id = "new_dashboard_user"

        prefs = await service.get_or_create_preferences(customer_id)

        assert prefs is not None
        assert prefs.customer_id == customer_id
        assert prefs.layout == "default"
        assert prefs.widgets_order == service.DEFAULT_WIDGETS
        assert prefs.show_recommendations is True

    @pytest.mark.asyncio
    async def test_get_or_create_preferences_existing_user(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test getting existing preferences."""
        customer_id = "existing_dashboard_user"

        # Create first
        prefs1 = await service.get_or_create_preferences(customer_id)

        # Get again
        prefs2 = await service.get_or_create_preferences(customer_id)

        assert prefs1.id == prefs2.id

    @pytest.mark.asyncio
    async def test_get_preferences(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test getting preferences as dictionary."""
        customer_id = "prefs_dict_user"

        prefs = await service.get_preferences(customer_id)

        assert prefs["customer_id"] == customer_id
        assert "layout" in prefs
        assert "widgets" in prefs
        assert "content" in prefs
        assert "notifications" in prefs
        assert "interests" in prefs

    @pytest.mark.asyncio
    async def test_update_preferences_layout(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test updating layout preference."""
        customer_id = "layout_update_user"

        result = await service.update_preferences(
            customer_id=customer_id,
            layout="compact",
        )

        assert result["success"] is True

        # Verify updated
        prefs = await service.get_preferences(customer_id)
        assert prefs["layout"] == "compact"

    @pytest.mark.asyncio
    async def test_update_preferences_widgets(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test updating widget preferences."""
        customer_id = "widget_update_user"

        new_order = ["badges", "stats", "recommendations"]
        hidden = ["activity_feed"]

        result = await service.update_preferences(
            customer_id=customer_id,
            widgets_order=new_order,
            hidden_widgets=hidden,
        )

        assert result["success"] is True

        prefs = await service.get_preferences(customer_id)
        assert prefs["widgets"]["order"] == new_order
        assert prefs["widgets"]["hidden"] == hidden

    @pytest.mark.asyncio
    async def test_update_preferences_notifications(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test updating notification preferences."""
        customer_id = "notif_update_user"

        result = await service.update_preferences(
            customer_id=customer_id,
            email_digest="daily",
            notify_new_badges=False,
        )

        assert result["success"] is True

        prefs = await service.get_preferences(customer_id)
        assert prefs["notifications"]["email_digest"] == "daily"
        assert prefs["notifications"]["new_badges"] is False

    @pytest.mark.asyncio
    async def test_update_preferences_interests(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test updating interest tags."""
        customer_id = "interest_update_user"

        result = await service.update_preferences(
            customer_id=customer_id,
            interest_tags=["api", "performance", "security"],
        )

        assert result["success"] is True

        prefs = await service.get_preferences(customer_id)
        assert "api" in prefs["interests"]["tags"]

    # ============== Watched Features Tests ==============

    @pytest.mark.asyncio
    async def test_watch_feature(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test adding feature to watch list."""
        customer_id = "watch_user"
        feature_id = 123

        result = await service.watch_feature(customer_id, feature_id)

        assert result["success"] is True
        assert result["feature_id"] == feature_id
        assert result["total_watched"] == 1

    @pytest.mark.asyncio
    async def test_watch_feature_duplicate(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test that watching same feature twice doesn't duplicate."""
        customer_id = "dup_watch_user"
        feature_id = 456

        await service.watch_feature(customer_id, feature_id)
        result = await service.watch_feature(customer_id, feature_id)

        assert result["total_watched"] == 1

    @pytest.mark.asyncio
    async def test_watch_multiple_features(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test watching multiple features."""
        customer_id = "multi_watch_user"

        await service.watch_feature(customer_id, 1)
        await service.watch_feature(customer_id, 2)
        result = await service.watch_feature(customer_id, 3)

        assert result["total_watched"] == 3

    @pytest.mark.asyncio
    async def test_unwatch_feature(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test removing feature from watch list."""
        customer_id = "unwatch_user"
        feature_id = 789

        # Watch first
        await service.watch_feature(customer_id, feature_id)

        # Unwatch
        result = await service.unwatch_feature(customer_id, feature_id)

        assert result["success"] is True
        assert result["total_watched"] == 0

    @pytest.mark.asyncio
    async def test_unwatch_feature_not_watched(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test unwatching a feature that's not watched."""
        customer_id = "unwatch_empty_user"

        result = await service.unwatch_feature(customer_id, 999)

        assert result["success"] is True
        assert result["total_watched"] == 0

    # ============== Recommendations Tests ==============

    @pytest.mark.asyncio
    async def test_generate_recommendations(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test generating recommendations."""
        customer_id = "rec_gen_user"

        recs = await service.generate_recommendations(customer_id, limit=10)

        # Should return list (may be empty if no features)
        assert isinstance(recs, list)

    @pytest.mark.asyncio
    async def test_get_recommendations(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test getting active recommendations."""
        customer_id = "rec_get_user"

        # Create a recommendation directly
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id=customer_id,
            feature_request_id=1,
            recommendation_type=RecommendationType.TRENDING.value,
            score=0.8,
            reason="Trending feature",
            status=RecommendationStatus.ACTIVE.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(rec)
        await db_session.commit()

        recs = await service.get_recommendations(customer_id)

        assert len(recs) == 1
        assert recs[0]["feature_request_id"] == 1
        assert recs[0]["type"] == RecommendationType.TRENDING.value

    @pytest.mark.asyncio
    async def test_get_recommendations_excludes_expired(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test that expired recommendations are excluded."""
        customer_id = "rec_expired_user"

        # Create expired recommendation
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id=customer_id,
            feature_request_id=1,
            recommendation_type=RecommendationType.NEW.value,
            score=0.5,
            reason="Old feature",
            status=RecommendationStatus.ACTIVE.value,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        )
        db_session.add(rec)
        await db_session.commit()

        recs = await service.get_recommendations(customer_id)

        assert len(recs) == 0

    @pytest.mark.asyncio
    async def test_dismiss_recommendation(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test dismissing a recommendation."""
        customer_id = "rec_dismiss_user"

        # Create recommendation
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id=customer_id,
            feature_request_id=1,
            recommendation_type=RecommendationType.POPULAR.value,
            score=0.6,
            reason="Popular feature",
            status=RecommendationStatus.ACTIVE.value,
        )
        db_session.add(rec)
        await db_session.commit()

        # Dismiss it
        result = await service.dismiss_recommendation(customer_id, rec.id)

        assert result["success"] is True

        # Verify status changed
        db_rec = await db_session.execute(
            select(FeatureRecommendation).where(FeatureRecommendation.id == rec.id)
        )
        updated_rec = db_rec.scalar_one()
        assert updated_rec.status == RecommendationStatus.DISMISSED.value

    @pytest.mark.asyncio
    async def test_dismiss_recommendation_not_found(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test dismissing non-existent recommendation."""
        result = await service.dismiss_recommendation("user", uuid4())

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_dismiss_recommendation_wrong_user(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test that user can't dismiss another user's recommendation."""
        # Create recommendation for user_a
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id="user_a",
            feature_request_id=1,
            recommendation_type=RecommendationType.NEW.value,
            score=0.5,
            reason="Test",
            status=RecommendationStatus.ACTIVE.value,
        )
        db_session.add(rec)
        await db_session.commit()

        # Try to dismiss as user_b
        result = await service.dismiss_recommendation("user_b", rec.id)

        assert result["success"] is False

    # ============== Dashboard Data Tests ==============

    @pytest.mark.asyncio
    async def test_get_dashboard_data(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test getting complete dashboard data."""
        customer_id = "dashboard_data_user"

        data = await service.get_dashboard_data(customer_id)

        assert "preferences" in data
        assert "widgets" in data
        assert data["preferences"]["customer_id"] == customer_id

    @pytest.mark.asyncio
    async def test_get_dashboard_data_respects_preferences(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test that dashboard data respects user preferences."""
        customer_id = "pref_respect_user"

        # Disable recommendations
        await service.update_preferences(
            customer_id=customer_id,
            show_recommendations=False,
        )

        data = await service.get_dashboard_data(customer_id)

        # Recommendations should not be in widgets
        assert "recommendations" not in data["widgets"]

    @pytest.mark.asyncio
    async def test_get_dashboard_data_includes_watched(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test that dashboard includes watched features."""
        customer_id = "watched_data_user"

        # Watch some features
        await service.watch_feature(customer_id, 1)
        await service.watch_feature(customer_id, 2)

        data = await service.get_dashboard_data(customer_id)

        assert "watched" in data["widgets"]
        assert data["widgets"]["watched"]["count"] == 2

    # ============== Statistics Tests ==============

    @pytest.mark.asyncio
    async def test_get_recommendation_statistics(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test getting recommendation statistics."""
        # Create some recommendations
        for i in range(3):
            rec = FeatureRecommendation(
                id=uuid4(),
                customer_id=f"stat_user_{i}",
                feature_request_id=i,
                recommendation_type=RecommendationType.TRENDING.value,
                score=0.5 + (i * 0.1),
                reason="Test",
                status=RecommendationStatus.ACTIVE.value,
            )
            db_session.add(rec)
        await db_session.commit()

        stats = await service.get_recommendation_statistics()

        assert stats["total"] >= 3
        assert "by_type" in stats
        assert "by_status" in stats
        assert "average_score" in stats

    @pytest.mark.asyncio
    async def test_get_recommendation_statistics_empty(
        self, service: PersonalizedDashboardService, db_session: AsyncSession
    ):
        """Test statistics with no recommendations."""
        stats = await service.get_recommendation_statistics()

        assert stats["total"] == 0


class TestDashboardPreferencesModel:
    """Test DashboardPreferences model."""

    def test_default_values(self):
        """Test default preference values."""
        prefs = DashboardPreferences(
            id=uuid4(),
            customer_id="test",
        )

        assert prefs.layout == "default"
        assert prefs.show_recommendations is True
        assert prefs.show_trending is True
        assert prefs.show_activity_feed is True
        assert prefs.show_badges is True
        assert prefs.show_stats is True
        assert prefs.email_digest == "weekly"


class TestFeatureRecommendationModel:
    """Test FeatureRecommendation model methods."""

    def test_is_expired_no_date(self):
        """Test is_expired with no expiration date."""
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id="test",
            feature_request_id=1,
            recommendation_type=RecommendationType.NEW.value,
            score=0.5,
            expires_at=None,
        )

        assert rec.is_expired() is False

    def test_is_expired_future(self):
        """Test is_expired with future date."""
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id="test",
            feature_request_id=1,
            recommendation_type=RecommendationType.NEW.value,
            score=0.5,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        assert rec.is_expired() is False

    def test_is_expired_past(self):
        """Test is_expired with past date."""
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id="test",
            feature_request_id=1,
            recommendation_type=RecommendationType.NEW.value,
            score=0.5,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        assert rec.is_expired() is True
