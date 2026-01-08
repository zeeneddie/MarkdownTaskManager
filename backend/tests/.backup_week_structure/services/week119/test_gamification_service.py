# backend/tests/services/week119/test_gamification_service.py
"""
Tests for GamificationService - Week 119

Tests badge earning, points awarding, level progression, and streaks.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gamification_service import GamificationService
from app.models.engagement import (
    UserLevel,
    BadgeDefinition,
    UserBadge,
    UserPointsHistory,
    ActionType,
    BadgeCategory,
    BadgeTier,
    CriteriaType,
    LEVEL_DEFINITIONS,
    POINT_VALUES,
)


class TestGamificationService:
    """Test suite for GamificationService."""

    @pytest.fixture
    async def service(self, db_session: AsyncSession):
        """Create service instance."""
        return GamificationService(db_session)

    @pytest.fixture
    async def test_badge(self, db_session: AsyncSession):
        """Create a test badge."""
        badge = BadgeDefinition(
            id=uuid4(),
            name="test_badge",
            display_name="Test Badge",
            description="A test badge",
            category=BadgeCategory.ENGAGEMENT.value,
            tier=BadgeTier.BRONZE.value,
            criteria_type=CriteriaType.COUNT.value,
            criteria_target="features_requested",
            criteria_value=1,
            points_awarded=50,
            icon="test",
        )
        db_session.add(badge)
        await db_session.commit()
        return badge

    # ============== User Level Tests ==============

    @pytest.mark.asyncio
    async def test_get_or_create_user_level_new_user(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test creating user level for new user."""
        customer_id = "new_user_123"

        user_level = await service.get_or_create_user_level(customer_id)

        assert user_level is not None
        assert user_level.customer_id == customer_id
        assert user_level.current_level == 1
        assert user_level.level_name == "Newcomer"
        assert user_level.total_points == 0

    @pytest.mark.asyncio
    async def test_get_or_create_user_level_existing_user(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test getting existing user level."""
        customer_id = "existing_user_123"

        # Create first
        user_level1 = await service.get_or_create_user_level(customer_id)

        # Get again
        user_level2 = await service.get_or_create_user_level(customer_id)

        assert user_level1.id == user_level2.id

    @pytest.mark.asyncio
    async def test_get_user_profile(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test getting complete user profile."""
        customer_id = "profile_user_123"

        profile = await service.get_user_profile(customer_id)

        assert profile["customer_id"] == customer_id
        assert "level" in profile
        assert "stats" in profile
        assert "streak" in profile
        assert "badges" in profile
        assert "recent_points" in profile
        assert profile["level"]["current"] == 1
        assert profile["level"]["name"] == "Newcomer"

    # ============== Points Tests ==============

    @pytest.mark.asyncio
    async def test_award_points_basic(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test awarding points for an action."""
        customer_id = "points_user_123"

        result = await service.award_points(
            customer_id=customer_id,
            action_type=ActionType.FEATURE_REQUEST.value,
            reason="Created feature request",
        )

        assert result["success"] is True
        assert result["points_awarded"] == POINT_VALUES[ActionType.FEATURE_REQUEST.value]
        assert result["total_points"] > 0

    @pytest.mark.asyncio
    async def test_award_points_with_custom_amount(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test awarding custom point amount."""
        customer_id = "custom_points_user"

        result = await service.award_points(
            customer_id=customer_id,
            action_type=ActionType.BONUS.value,
            points=100,
            reason="Special bonus",
        )

        assert result["points_awarded"] == 100
        assert result["total_points"] == 100

    @pytest.mark.asyncio
    async def test_award_points_updates_stats(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test that awarding points updates user stats."""
        customer_id = "stats_user_123"

        # Award for feature request
        await service.award_points(
            customer_id=customer_id,
            action_type=ActionType.FEATURE_REQUEST.value,
        )

        # Check stats updated
        user_level = await service.get_or_create_user_level(customer_id)
        assert user_level.features_requested == 1

    @pytest.mark.asyncio
    async def test_award_points_triggers_badge(
        self, service: GamificationService, db_session: AsyncSession, test_badge
    ):
        """Test that awarding points triggers badge check."""
        customer_id = "badge_trigger_user"

        result = await service.award_points(
            customer_id=customer_id,
            action_type=ActionType.FEATURE_REQUEST.value,
        )

        # Should have earned test_badge
        assert len(result["new_badges"]) > 0

    @pytest.mark.asyncio
    async def test_get_points_history(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test getting points history."""
        customer_id = "history_user_123"

        # Award some points
        await service.award_points(
            customer_id=customer_id,
            action_type=ActionType.VOTE.value,
        )
        await service.award_points(
            customer_id=customer_id,
            action_type=ActionType.COMMENT.value,
        )

        history = await service.get_points_history(customer_id)

        assert len(history) >= 2

    # ============== Level Tests ==============

    @pytest.mark.asyncio
    async def test_level_up_on_points(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test leveling up when reaching point threshold."""
        customer_id = "level_up_user"

        # Award enough points to level up (100 points for level 2)
        result = await service.award_points(
            customer_id=customer_id,
            action_type=ActionType.BONUS.value,
            points=150,
            reason="Level up bonus",
        )

        # Should be level 2 now
        assert result["current_level"] == 2
        assert result["level_name"] == "Contributor"
        assert result["leveled_up"] is True

    # ============== Badge Tests ==============

    @pytest.mark.asyncio
    async def test_initialize_default_badges(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test initializing default badges."""
        count = await service.initialize_default_badges()

        # Should have initialized some badges
        assert count > 0

    @pytest.mark.asyncio
    async def test_get_all_badges(
        self, service: GamificationService, db_session: AsyncSession, test_badge
    ):
        """Test getting all badges."""
        badges = await service.get_all_badges()

        assert len(badges) >= 1
        badge_names = [b["name"] for b in badges]
        assert "test_badge" in badge_names

    @pytest.mark.asyncio
    async def test_get_user_badges(
        self, service: GamificationService, db_session: AsyncSession, test_badge
    ):
        """Test getting user badges."""
        customer_id = "badge_user_123"

        # Award badge
        await service.award_badge_manually(customer_id, test_badge.name)

        badges = await service.get_user_badges(customer_id)

        assert len(badges) == 1
        assert badges[0]["name"] == "test_badge"

    @pytest.mark.asyncio
    async def test_award_badge_manually(
        self, service: GamificationService, db_session: AsyncSession, test_badge
    ):
        """Test manually awarding a badge."""
        customer_id = "manual_badge_user"

        result = await service.award_badge_manually(
            customer_id=customer_id,
            badge_name="test_badge",
            reason="Manual award for testing",
        )

        assert result["success"] is True
        assert result["badge"]["name"] == "test_badge"
        assert result["badge"]["points_awarded"] == 50

    @pytest.mark.asyncio
    async def test_award_badge_duplicate(
        self, service: GamificationService, db_session: AsyncSession, test_badge
    ):
        """Test that duplicate badge award fails."""
        customer_id = "duplicate_badge_user"

        # Award first time
        await service.award_badge_manually(customer_id, "test_badge")

        # Try to award again
        result = await service.award_badge_manually(customer_id, "test_badge")

        assert result["success"] is False
        assert "already has" in result["error"]

    @pytest.mark.asyncio
    async def test_check_and_award_badges(
        self, service: GamificationService, db_session: AsyncSession, test_badge
    ):
        """Test automatic badge checking."""
        customer_id = "auto_badge_user"

        # Setup: increment features_requested
        user_level = await service.get_or_create_user_level(customer_id)
        user_level.features_requested = 5
        await db_session.commit()

        new_badges = await service.check_and_award_badges(customer_id)

        # Should have earned test_badge
        badge_names = [b["name"] for b in new_badges]
        assert "test_badge" in badge_names

    # ============== Leaderboard Tests ==============

    @pytest.mark.asyncio
    async def test_get_leaderboard(
        self, service: GamificationService, db_session: AsyncSession
    ):
        """Test getting leaderboard."""
        # Create some users with points
        await service.award_points("user_a", ActionType.BONUS.value, points=100)
        await service.award_points("user_b", ActionType.BONUS.value, points=200)
        await service.award_points("user_c", ActionType.BONUS.value, points=50)

        leaderboard = await service.get_leaderboard(limit=10)

        assert len(leaderboard) == 3
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[0]["customer_id"] == "user_b"  # Highest points
        assert leaderboard[0]["total_points"] == 200

    # ============== Statistics Tests ==============

    @pytest.mark.asyncio
    async def test_get_gamification_statistics(
        self, service: GamificationService, db_session: AsyncSession, test_badge
    ):
        """Test getting gamification statistics."""
        # Create some data
        await service.award_points("stat_user_1", ActionType.FEATURE_REQUEST.value)
        await service.award_points("stat_user_2", ActionType.FEEDBACK.value)

        stats = await service.get_gamification_statistics()

        assert stats["total_users"] >= 2
        assert stats["total_points_awarded"] > 0
        assert "level_distribution" in stats
        assert "level_definitions" in stats


class TestUserLevelModel:
    """Test UserLevel model methods."""

    def test_add_points(self):
        """Test adding points to user level."""
        user_level = UserLevel(
            id=uuid4(),
            customer_id="test",
            current_level=1,
            level_name="Newcomer",
            total_points=0,
            points_to_next_level=100,
        )

        leveled_up = user_level.add_points(50)

        assert user_level.total_points == 50
        assert leveled_up is False

    def test_level_up_on_threshold(self):
        """Test leveling up when crossing threshold."""
        user_level = UserLevel(
            id=uuid4(),
            customer_id="test",
            current_level=1,
            level_name="Newcomer",
            total_points=90,
            points_to_next_level=10,
        )

        leveled_up = user_level.add_points(20)  # Total = 110, above level 2 threshold

        assert leveled_up is True
        assert user_level.current_level == 2
        assert user_level.level_name == "Contributor"

    def test_update_streak_new_user(self):
        """Test streak update for new user."""
        user_level = UserLevel(
            id=uuid4(),
            customer_id="test",
            current_level=1,
            level_name="Newcomer",
            total_points=0,
            points_to_next_level=100,
            current_streak_days=0,
            longest_streak_days=0,
            last_activity_date=None,
        )

        user_level.update_streak()

        assert user_level.current_streak_days == 1
        assert user_level.last_activity_date == date.today()

    def test_update_streak_consecutive_day(self):
        """Test streak continues on consecutive day."""
        yesterday = date.today() - timedelta(days=1)
        user_level = UserLevel(
            id=uuid4(),
            customer_id="test",
            current_level=1,
            level_name="Newcomer",
            total_points=0,
            points_to_next_level=100,
            current_streak_days=5,
            longest_streak_days=5,
            last_activity_date=yesterday,
        )

        user_level.update_streak()

        assert user_level.current_streak_days == 6
        assert user_level.longest_streak_days == 6

    def test_update_streak_broken(self):
        """Test streak resets after gap."""
        two_days_ago = date.today() - timedelta(days=2)
        user_level = UserLevel(
            id=uuid4(),
            customer_id="test",
            current_level=1,
            level_name="Newcomer",
            total_points=0,
            points_to_next_level=100,
            current_streak_days=10,
            longest_streak_days=10,
            last_activity_date=two_days_ago,
        )

        user_level.update_streak()

        assert user_level.current_streak_days == 1  # Reset
        assert user_level.longest_streak_days == 10  # Preserved

    def test_get_stats(self):
        """Test getting user stats dictionary."""
        user_level = UserLevel(
            id=uuid4(),
            customer_id="test",
            current_level=3,
            level_name="Active Member",
            total_points=300,
            points_to_next_level=200,
            features_requested=5,
            feedback_given=3,
            votes_cast=10,
            comments_made=2,
            features_delivered=1,
            current_streak_days=7,
            longest_streak_days=14,
        )

        stats = user_level.get_stats()

        assert stats["features_requested"] == 5
        assert stats["feedback_given"] == 3
        assert stats["votes_cast"] == 10
        assert stats["current_streak_days"] == 7
        assert stats["total_points"] == 300


class TestBadgeDefinitionModel:
    """Test BadgeDefinition model methods."""

    def test_check_criteria_count(self):
        """Test count criteria checking."""
        badge = BadgeDefinition(
            id=uuid4(),
            name="test",
            display_name="Test",
            criteria_type=CriteriaType.COUNT.value,
            criteria_target="features_requested",
            criteria_value=5,
            points_awarded=10,
        )

        # Not enough
        assert badge.check_criteria({"features_requested": 3}) is False

        # Exactly enough
        assert badge.check_criteria({"features_requested": 5}) is True

        # More than enough
        assert badge.check_criteria({"features_requested": 10}) is True

    def test_check_criteria_streak(self):
        """Test streak criteria checking."""
        badge = BadgeDefinition(
            id=uuid4(),
            name="test",
            display_name="Test",
            criteria_type=CriteriaType.STREAK.value,
            criteria_target="current_streak_days",
            criteria_value=7,
            points_awarded=10,
        )

        assert badge.check_criteria({"current_streak_days": 5}) is False
        assert badge.check_criteria({"current_streak_days": 7}) is True
        assert badge.check_criteria({"current_streak_days": 30}) is True
